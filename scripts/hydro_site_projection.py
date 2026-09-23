"""Server-only 15-minute refresh of the hourly experimental Muçum model.

Uses its own history and ledger, separate from the local research automation.
The clock checks availability; inference requires complete same-hour inputs.
"""
import argparse
import fcntl
import io
import json
import os
import shutil
import signal
import tarfile
import tempfile
import urllib.request
import urllib.error
import uuid
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from hydro_hourly_collect import collect, ROOT, TZ, dump
from hydro_hourly_forecast import PREV, epoch, iso, CUTOFF
from threadpoolctl import threadpool_limits
import hydro_history
from hydro_input_readiness import (InputsNotReady, require_ready, require_features,
                                  select_latest_ready, MAX_REFERENCE_AGE_HOURS, LEVELS, PLANTS)
from hydro_feature_contract import build_snapshot, current_nwp_features, NWP_MODELS
from hydro_short_term_candidate import build_shadow
from hydro_projection_archive import enqueue_attempt
from hydro_propagation_live import run_shadow as run_propagation_shadow
from hydro_propagation_public import public_forecast, MODEL_VERSION, MODEL_ID, MODEL_SHA256

LEGACY_MODEL_VERSION = 'forecast-6h-v1-complete-hour-v3-mucum-only'


def future_model_points(reference, points, issued):
    """Keep only original nominal targets that remain in the actual future."""
    age = (issued-reference).total_seconds()
    if not 0 <= age <= MAX_REFERENCE_AGE_HOURS * 3600:
        raise InputsNotReady({'status':'waiting_for_data', 'referenceAt':reference.isoformat(),
            'missing':['Complete observation reference is older than three hours at issuance']})
    result = [point for point in points if epoch(point['timestamp']) > issued.timestamp()]
    leads = [(epoch(point['timestamp'])-reference.timestamp())/3600 for point in result]
    first_lead = int(age // 3600) + 1
    if not leads or leads != list(range(first_lead, 7)) or not 1 <= leads[0] <= 4:
        raise ValueError('Expected the strictly future suffix of original H+1 through H+6 targets')
    return result


def calculate_model(out, reference):
    """Frozen statistical model; inference only, never retrain in the cron."""
    require_ready(out, reference, PREV / 'chuva-pesos.json')
    if not 0 <= (datetime.now(TZ)-reference).total_seconds() <= MAX_REFERENCE_AGE_HOURS*3600:
        raise InputsNotReady({'status':'waiting_for_data', 'referenceAt':reference.isoformat(),
            'missing':['Complete observation reference is older than three hours before inference']})
    os.environ.update(HYDRO_OUTPUT_DIR=str(out), HYDRO_ORIGIN=reference.isoformat(), HYDRO_HORIZON='6', HYDRO_REQUIRE_COMPLETE='1')
    from hydro_latency_forecast import prepare_current, telemetry_features
    t, raw, delayed, ages = prepare_current()
    times, X, H, _truth, _phase, _ = telemetry_features(t, raw, delayed)
    if times[-1] != reference.timestamp() or not np.isfinite(H[-1]):
        raise ValueError('Invalid model reference or Muçum anchor')
    last = next(a for a in ages if a['source'] == '86510000')
    if any(a['delay_minutes'] != 0 for a in ages if a['source'] in ['86510000','86472000','86472600','86500000','julho','monte','castro']):
        raise InputsNotReady({'status':'waiting_for_data','missing':['Model source timestamp does not match reference hour']})
    weather = current_nwp_features({model: json.loads((out / 'raw' / f'weather-{model}.json').read_text()) for model in NWP_MODELS}, reference.isoformat())
    features = np.array([np.r_[X[-1], weather]])
    require_features(features[-1])
    dump(out / 'current-features.json', features[-1].tolist())
    frozen = ROOT / 'model-artifacts/forecast-6h-v1'
    specification = json.loads((frozen / 'model.json').read_text())
    modeldir = out / 'models'
    modeldir.mkdir()
    points = []
    for lead in range(1, 7):
        artifact = frozen / f'forecast-{lead}.joblib'
        if hydro_history.sha(artifact) != specification['artifacts'][artifact.name]:
            raise ValueError('Model artifact integrity failure')
        model = joblib.load(artifact)
        value = float(model.predict(features[-1:])[0] + H[-1])
        if not np.isfinite(value):
            raise ValueError('Non-finite prediction')
        shutil.copyfile(artifact, modeldir / artifact.name)
        points.append({'timestamp': iso(times[-1] + lead * 3600), 'level': value})
        print(f'Modelo de previsão: {lead}h', flush=True)
    points = future_model_points(reference, points, datetime.now(TZ))
    dump(out / 'model-metadata.json', {'trainingCutoff': CUTOFF, 'model': specification, 'sourceAges': ages, 'runtimeManifest': json.loads((ROOT / 'manifest.json').read_text()) if (ROOT / 'manifest.json').exists() else None, 'trainingFeatureContract': 'legacy-mixed-nwp-unverified'})
    return last, points


def restore_history(archive, destination):
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
        for member in tar.getmembers():
            if not member.isfile() or Path(member.name).name != member.name or member.size > 50_000_000:
                raise ValueError('Invalid history archive')
            stream = tar.extractfile(member)
            (destination / member.name).write_bytes(stream.read())
    hydro_history.verify(destination)


def record_features_and_shadow(out, reference, generated, observation, points):
    manifest = json.loads((out / 'collection-manifest.json').read_text())
    by_file = {row['file']: row for row in manifest}
    sources = []
    for identity in (*LEVELS, *PLANTS, *NWP_MODELS):
        kind = 'nwp' if identity in NWP_MODELS else 'observed'
        filename = (f'weather-{identity}.json' if kind == 'nwp' else
                    f'ana-{identity}-fresh.xml' if identity in LEVELS else f'ceran-{identity}-fresh.html')
        row = by_file[filename]
        source = dict(kind=kind, id=identity, available_at=row['collected_at'], sha256=row['sha256'])
        if kind == 'nwp':
            source.update(product='current_forecast', field='precipitation')
            if row.get('issued_at'):
                source['forecast_reference_at'] = row['issued_at']
        else:
            source['observed_through'] = reference.isoformat()
        sources.append(source)
    metadata = json.loads((out / 'model-metadata.json').read_text())
    metadata['collectionManifestSha256'] = hydro_history.sha(out / 'collection-manifest.json')
    if (out / 'reference-selection.json').exists():
        metadata['referenceSelection'] = json.loads((out / 'reference-selection.json').read_text())
    snapshot = build_snapshot(reference_at=reference.isoformat(), issued_at=generated,
        station_id='86510000', datum_id='ANA:86510000:reference-unverified',
        feature_values=json.loads((out / 'current-features.json').read_text()), sources=sources,
        input_readiness=json.loads((out / 'input-readiness.json').read_text()), model_metadata=metadata)
    dump(out / 'feature-snapshot.json', snapshot)
    row = by_file['ana-86510000-fresh.xml']
    observations, _ = hydro_history.ana_rows(out / 'raw' / row['file'], '86510000',
        epoch(row['collected_at']), strict_quality=True)
    def measured(when, value):
        return dict(station='86510000', timestamp=iso(when), level=float(value),
                    received_at=row['collected_at'], quality='approved', evidence_id=row['sha256'])
    history = [measured(when, values[0]) for when, values in observations.items()
               if when == reference.timestamp() - 3600 and np.isfinite(values[0])]
    shadow = build_shadow(reference_at=reference.isoformat(), issued_at=generated,
        anchor=measured(reference.timestamp(), observation['value']), received_history=history,
        baseline_points=points)
    dump(out / 'short-term-shadow.json', shadow)


def perform_attempt(args, out, checked_reference):
    """The public primary uses only its measured level/flow feature contract."""
    if args.source:
        shutil.copytree(args.source / 'raw', out / 'raw')
        shutil.copyfile(args.source / 'collection-manifest.json', out / 'collection-manifest.json')
    else:
        collect(out, datetime.now(TZ), hydrometric_only=True)
    shadow = run_propagation_shadow(out, ROOT, checked_reference)
    selection = dict(checkedReferenceAt=checked_reference.isoformat(),
                     modelVersion=MODEL_VERSION, rainRequired=False,
                     candidates=shadow.get('candidates', []))
    if shadow.get('status') == 'calculated':
        reference = datetime.fromisoformat(shadow['referenceAt'].replace('Z', '+00:00'))
        args.selected_reference = reference
        selection.update(referenceAt=reference.isoformat(),
                         referenceAgeSeconds=shadow['referenceAgeSeconds'])
    dump(out / 'reference-selection.json', selection)
    try:
        payload = public_forecast(shadow, checked_reference=checked_reference,
            attempt_id=args.attempt_id, now=datetime.now(TZ),
            after_reference=getattr(args, 'after_reference', None))
    except InputsNotReady as exc:
        dump(out / 'input-readiness.json', exc.report)
        raise
    readiness = dict(status='ready', modelVersion=MODEL_VERSION, rainRequired=False,
                     referenceAt=payload['referenceAt'], missing=[],
                     sources=shadow['sources'])
    payload.update(referenceSelection=selection, inputReadiness=readiness)
    dump(out / 'input-readiness.json', readiness)
    dump(out / 'model-metadata.json', dict(modelVersion=MODEL_VERSION,
        modelSha256=payload['modelSha256'], featureContract=payload['featureContract'],
        sources=shadow['sources'], experimental=True, goal98PercentDemonstrated=False,
        publication='User-authorized experimental hydrometric primary',
        runtimeManifest=json.loads((ROOT / 'manifest.json').read_text()) if (ROOT / 'manifest.json').exists() else None))
    dump(out / 'forecast.json', payload)
    return payload


def perform_legacy_attempt(args, out, checked_reference):
    # Collection happens even when inference cannot proceed. The caller archives
    # its raw evidence in finally, before this temporary directory disappears.
    if args.source:
        shutil.copytree(args.source / 'raw', out / 'raw')
        shutil.copyfile(args.source / 'collection-manifest.json', out / 'collection-manifest.json')
    else:
        collect(out, datetime.now(TZ))
    # Preserve an independent hydrometric experiment even when rain blocks
    # the public baseline. Shadow output cannot satisfy or bypass that gate.
    run_propagation_shadow(out, ROOT, checked_reference)
    reference, _ = select_latest_ready(out, checked_reference, PREV / 'chuva-pesos.json',
                                      after_reference=getattr(args, 'after_reference', None))
    args.selected_reference = reference
    remote = os.environ.get('OBJECT_STORAGE_URL', '').rstrip('/')
    checkpoint = args.state / 'history.tar.gz'
    if remote:
        try:
            with urllib.request.urlopen(remote + '/projection/history.tar.gz', timeout=30) as response:
                checkpoint.write_bytes(response.read())
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
    index = out / 'history-index'
    index.mkdir()
    if checkpoint.exists():
        seed = out / 'previous-history'
        restore_history(checkpoint.read_bytes(), seed)
        dump(index / 'current.json', {'directory': str(seed), 'manifest_sha256': hydro_history.sha(seed / 'manifest.json')})
    os.environ['HYDRO_REQUIRE_COMPLETE'] = '1'
    history = hydro_history.build(out, index, PREV, allow_missing_rain=True)
    os.environ['HYDRO_HISTORY_DIR'] = str(history)
    with threadpool_limits(limits=2):
        observation, points = calculate_model(out, reference)
    generated = datetime.now(TZ).isoformat()
    points = future_model_points(reference, points, datetime.fromisoformat(generated))
    record_features_and_shadow(out, reference, generated, observation, points)
    payload = {
        'schema': 1, 'station': 'mucum', 'generatedAt': generated, 'referenceAt': reference.isoformat(),
        'experimental': True, 'intervalMinutes': 15,
        'modelVersion': LEGACY_MODEL_VERSION, 'horizonHours': 6,
        'forecastStartLeadHours': int((epoch(points[0]['timestamp'])-reference.timestamp())/3600),
        'referenceAgeSeconds': (datetime.fromisoformat(generated)-reference).total_seconds(),
        'checkedReferenceAt': checked_reference.isoformat(),
        'referenceSelection': json.loads((out / 'reference-selection.json').read_text()),
        'inputReadiness': json.loads((out / 'input-readiness.json').read_text()),
        'archiveReceiptKey': f'projection/receipts/{args.attempt_id}.json',
        'observation': {'timestamp': observation['last_time'], 'level': observation['value']},
        'models': [{'id': 'radar_arvores_live_candidate', 'label': 'Modelo de previsão', 'points': points}],
    }
    dump(out / 'forecast.json', payload)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for path in sorted(history.iterdir()):
            tar.add(path, arcname=path.name)
    (args.state / 'history.pending.tar.gz').write_bytes(buffer.getvalue())
    os.replace(args.state / 'history.pending.tar.gz', checkpoint)
    # Compatibility checkpoint. Permanent evidence lives in immutable objects.
    with tarfile.open(args.state / 'audit.tar.gz', 'w:gz') as tar:
        for name in ['collection-manifest.json', 'input-readiness.json', 'model-metadata.json',
                     'feature-snapshot.json', 'short-term-shadow.json', 'reference-selection.json', 'raw']:
            tar.add(out / name, arcname=name)
    return payload


def shadow_refresh_status(out, archive_receipt_key):
    """Expose only metadata from the shadow file included in this attempt archive.

    The Node caller still has to flush and confirm this receipt before publishing
    refresh state. Local outbox creation alone is not a durable remote receipt.
    """
    source = out / 'propagation-shadow.json'
    try:
        if not source.is_file():
            return None
        value = json.loads(source.read_text())
    except (OSError, ValueError):
        return None
    if (not isinstance(value, dict) or value.get('schema') != 'radar-propagation-shadow/v1' or
            value.get('mode') != 'shadow' or value.get('publishable') is not False or
            value.get('station') != '86510000' or value.get('status') not in ('calculated', 'unavailable')):
        return None
    if value['status'] == 'calculated' and value.get('modelVersion') != 'mucum-hydrometry-shadow-v1':
        return None
    result = dict(status=value['status'], generatedAt=value.get('generatedAt'),
                  archiveReceiptKey=archive_receipt_key, modelVersion='mucum-hydrometry-shadow-v1')
    if value.get('referenceAt') is not None:
        result['referenceAt'] = value['referenceAt']
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', type=Path, required=True)
    ap.add_argument('--source', type=Path, help='Local collected fixture; never used by the public endpoint')
    ap.add_argument('--attempt-id', default=None)
    ap.add_argument('--reference', help='Exact polling hour; complete observed reference is selected after collection')
    ap.add_argument('--after-reference', help='Only select an observation hour newer than this published reference')
    args = ap.parse_args()
    args.attempt_id = args.attempt_id or str(uuid.uuid4())
    args.after_reference = datetime.fromisoformat(args.after_reference.replace('Z', '+00:00')) if args.after_reference else None
    args.state.mkdir(parents=True, exist_ok=True)
    def interrupted(signum, _frame):
        raise TimeoutError(f'Calculation interrupted by signal {signum}; preserving collected evidence')
    signal.signal(signal.SIGTERM, interrupted)
    with (args.state / 'calculation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        reference = datetime.fromisoformat(args.reference.replace('Z', '+00:00')) if args.reference else datetime.now(TZ).replace(minute=0, second=0, microsecond=0)
        status = dict(status='checking', attemptId=args.attempt_id, referenceAt=reference.isoformat(),
                      checkedReferenceAt=reference.isoformat())
        dump(args.state / 'refresh-status.json', status)
        saved = args.state / 'result.json'
        if saved.exists():
            previous = json.loads(saved.read_text())
            saved_reference = datetime.fromisoformat(previous['referenceAt'].replace('Z', '+00:00'))
            now = datetime.now(TZ)
            saved_points = [point for model in previous.get('models', []) for point in model.get('points', [])]
            if (saved_reference <= reference and 0 <= (now-saved_reference).total_seconds() <= MAX_REFERENCE_AGE_HOURS*3600 and
                    (args.after_reference is None or saved_reference > args.after_reference) and
                    saved_points and all(epoch(point['timestamp']) > now.timestamp() for point in saved_points) and
                    previous.get('archiveReceiptKey') and previous.get('modelVersion') == MODEL_VERSION and
                    previous.get('modelSha256') == MODEL_SHA256 and
                    len(previous.get('models', [])) == 1 and previous['models'][0].get('id') == MODEL_ID):
                dump(args.state / 'refresh-status.json', {**status, 'status': 'calculated',
                    'referenceAt':previous['referenceAt'], 'generatedAt': previous['generatedAt'],
                    'archiveReceiptKey': previous['archiveReceiptKey']})
                return
        with tempfile.TemporaryDirectory(prefix='site-', dir=args.state) as temp:
            out = Path(temp)
            payload = None
            try:
                payload = perform_attempt(args, out, reference)
                status.update(status='calculated', generatedAt=payload['generatedAt'], referenceAt=payload['referenceAt'])
            except InputsNotReady as exc:
                status.update(exc.report)
                status['referenceAt'] = getattr(args, 'selected_reference', reference).isoformat()
            except Exception as exc:
                status.update(status='failed', error=f'{type(exc).__name__}: {exc}')
                raise
            finally:
                selected_reference = getattr(args, 'selected_reference', reference)
                status['referenceAt'] = selected_reference.isoformat()
                status['checkedReferenceAt'] = reference.isoformat()
                if (out / 'reference-selection.json').exists():
                    status['referenceSelection'] = json.loads((out / 'reference-selection.json').read_text())
                status['archiveReceiptKey'] = enqueue_attempt(args.state, out, ROOT,
                    attempt_id=args.attempt_id, reference_at=selected_reference.isoformat(), status=status['status'],
                    generated_at=status.get('generatedAt'), missing=status.get('missing'), error=status.get('error'))
                shadow = shadow_refresh_status(out, status['archiveReceiptKey'])
                if shadow is not None:
                    status['shadow'] = shadow
                dump(args.state / 'refresh-status.json', status)
            if payload is not None:
                dump(args.state / 'result.pending.json', payload)
                os.replace(args.state / 'result.pending.json', saved)
            print(json.dumps(status), flush=True)


if __name__ == '__main__':
    main()
