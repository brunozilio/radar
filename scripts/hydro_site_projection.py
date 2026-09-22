"""Server-only 15-minute refresh of the existing hourly experimental models.

Uses its own history and ledger, separate from the local research automation.
The model reference remains hourly; collection and calculation run every 15 min.
"""
import argparse
import fcntl
import io
import json
import os
import shutil
import tarfile
import tempfile
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from hydro_hourly_collect import collect, ROOT, TZ, dump
from hydro_hourly_forecast import PREV, weather_features, epoch, iso, CUTOFF
from threadpoolctl import threadpool_limits
import hydro_history
import hydro_encantado


def calculate_model(out, reference):
    """Frozen statistical model; inference only, never retrain in the cron."""
    os.environ.update(HYDRO_OUTPUT_DIR=str(out), HYDRO_ORIGIN=reference.isoformat(), HYDRO_HORIZON='6')
    from hydro_latency_forecast import prepare_current, telemetry_features
    t, raw, delayed, ages = prepare_current()
    times, X, H, _truth, _phase, _ = telemetry_features(t, raw, delayed)
    if times[-1] != reference.timestamp() or not np.isfinite(H[-1]):
        raise ValueError('Invalid model reference or Muçum anchor')
    last = next(a for a in ages if a['source'] == '86510000')
    if last['delay_minutes'] > 90:
        raise ValueError('Muçum observation older than 90 minutes')
    features = np.column_stack([X, weather_features(times, out)])
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
    emission = datetime.now(TZ).timestamp()
    points = [p for p in points if epoch(p['timestamp']) > emission]
    if len(points) != 6:
        raise ValueError('One of the six hourly targets elapsed during calculation; recollect')
    dump(out / 'model-metadata.json', {'trainingCutoff': CUTOFF, 'model': specification, 'sourceAges': ages, 'runtimeManifest': json.loads((ROOT / 'manifest.json').read_text())})
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', type=Path, required=True)
    ap.add_argument('--source', type=Path, help='Local collected fixture; never used by the public endpoint')
    args = ap.parse_args()
    args.state.mkdir(parents=True, exist_ok=True)
    with (args.state / 'calculation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with tempfile.TemporaryDirectory(prefix='site-', dir=args.state) as temp:
            out = Path(temp)
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
            if args.source:
                shutil.copytree(args.source / 'raw', out / 'raw')
                shutil.copyfile(args.source / 'collection-manifest.json', out / 'collection-manifest.json')
            else:
                collect(out, datetime.now(TZ))
            manifest = json.loads((out / 'collection-manifest.json').read_text())
            required = [r for r in manifest if r['source'] in ['ANA', 'CERAN', 'Open-Meteo']]
            if not required or any('error' in r for r in required):
                raise ValueError('Required source unavailable')
            now = datetime.now(TZ)
            if any((now - datetime.fromisoformat(r['collected_at'])).total_seconds() > 3600 for r in required):
                raise ValueError('Collection is stale')
            history = hydro_history.build(out, index, PREV)
            os.environ['HYDRO_HISTORY_DIR'] = str(history)
            reference = now.replace(minute=0, second=0, microsecond=0)
            with threadpool_limits(limits=2):
                observation, points = calculate_model(out, reference)
                additional = {}
                for station in hydro_encantado.MODEL_CONFIGS:
                    try:
                        additional[station] = hydro_encantado.calculate(out, reference, station=station)
                    except Exception as exc:
                        # Each city preserves its own previous issue on failure.
                        additional[station] = None
                        print(f'{station} unavailable: {type(exc).__name__}: {exc}', flush=True)
            generated = datetime.now(TZ).isoformat()
            payload = {
                'schema': 1, 'generatedAt': generated, 'referenceAt': reference.isoformat(),
                'experimental': True, 'intervalMinutes': 15,
                'modelVersion': 'forecast-6h-v1', 'horizonHours': 6,
                'observation': {'timestamp': observation['last_time'], 'level': observation['value']},
                'models': [{'id': 'radar_arvores_live_candidate', 'label': 'Modelo de previsão', 'points': points}],
                **additional,
            }
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
                for p in sorted(history.iterdir()):
                    tar.add(p, arcname=p.name)
            (args.state / 'history.pending.tar.gz').write_bytes(buffer.getvalue())
            os.replace(args.state / 'history.pending.tar.gz', checkpoint)
            # Keep the most recent complete calculation locally for diagnosis.
            with tarfile.open(args.state / 'audit.tar.gz', 'w:gz') as tar:
                for name in ['models', 'collection-manifest.json', 'model-metadata.json', 'raw', 'history']:
                    tar.add(out / name, arcname=name)
            dump(args.state / 'result.pending.json', payload)
            os.replace(args.state / 'result.pending.json', args.state / 'result.json')
            print(json.dumps({'status': 'success', 'generatedAt': generated}), flush=True)


if __name__ == '__main__':
    main()
