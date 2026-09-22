"""Freeze one existing RADAR family before reserved-window inference; never fit/predict."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, shutil
import numpy as np
import joblib

P=Path(__file__).resolve().parent; ROOT=P.parents[1]
C=ROOT/'outputs/experimento-radar-historico-2020-20260921'
B=ROOT/'outputs/experimento-radar-observado-120-20260921'
PROTO=ROOT/'docs/radar-reserved-2021-2022-challenge-protocol.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def verify(p):
    hh=json.loads((p/'artifact-hashes.json').read_text())
    for h in hh: assert sha(p/h['file'])==h['sha256'],str(p/h['file'])
    return len(hh)

assert not PROTO.exists() and not (P/'models').exists()
verified={str(p.relative_to(ROOT)):verify(p) for p in (B,C)}
original=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921/features.npz'
added=ROOT/'outputs/radar-matriz-observada-2020-20260921/features.npz'
old=np.load(original);new=np.load(added);masks=np.load(C/'training-masks.npz')
reservation=ROOT/'docs/radar-historical-evaluation-reservation.json'
for w in json.loads(reservation.read_text())['windows']:
    lo=datetime.fromisoformat(w['start_inclusive_local']).timestamp();hi=datetime.fromisoformat(w['stop_exclusive_local']).timestamp()
    assert not ((old['times']>=lo)&(old['times']<hi)).any()
    assert not ((new['times']>=lo)&(new['times']<hi)).any()
records=[];(P/'models').mkdir()
cm={int(r['horizon_h']):r for r in csv.DictReader((C/'training.csv').open()) if r['phase']=='test'}
bm={int(r['horizon_h']):r for r in csv.DictReader((B/'training.csv').open()) if r['phase']=='test'}
for h in range(1,13):
    assert int(masks[f'new_h{h}'].sum())==int(cm[h]['added_n'])
    assert int(masks[f'test_original_h{h}'].sum())==int(cm[h]['original_n'])==int(bm[h]['n'])
    for family,folder,info in [('control120',B,bm[h]),('candidate120_plus2020',C,cm[h])]:
        source=folder/f'models/test-{h}.joblib';model=joblib.load(source)
        assert model.n_features_in_==120
        params=model.get_params();assert params['max_leaf_nodes']==int(info['leaf_nodes']) and params['loss']==info['loss']
        dest=P/'models'/f'{family}-{h}.joblib';shutil.copyfile(source,dest);assert sha(dest)==sha(source)
        records.append(dict(family=family,horizon_h=h,source=str(source.relative_to(ROOT)),file=str(dest.relative_to(ROOT)),
            sha256=sha(dest),parameters=params,training=info))
refs=[reservation,original,added,C/'training-masks.npz',C/'training.csv',C/'experiment.json',B/'training.csv',B/'experiment.json',
      ROOT/'docs/radar-2020-augmentation-protocol.json',ROOT/'docs/radar-2020-observed-features-protocol.json',
      ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_model.py',ROOT/'scripts/hydro_rain_windows.py',
      ROOT/'scripts/hydro_radar_2024_features.py',ROOT/'scripts/hydro_routing_fit.py',ROOT/'scripts/hydro_hourly_forecast.py',
      ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json',ROOT/'outputs/auditoria-latencias-chuva-20260921/latencies.json']
protocol=dict(id='radar-reserved-2021-2022-challenge-v1',registered_at_utc=datetime.now(timezone.utc).isoformat(),
    scope='One retrospective reserved-event challenge, not prospective accuracy or a forward-only historical training simulation.',
    choice='Frozen test-phase120-column observed control versus same family plus all eligible July1..20/2020. Reuse24 models; no refit, no parameter search, no per-horizon mixing, no2023/2024 augmentation.',
    choice_reason='The pre-reservation development comparison showed high-water MAE gains at all12 horizons and hit gains at11; validation hit regressions and worse high-water maxima remain explicit. This is a fixed hypothesis to test, not a promoted winner.',
    prior_exposure='SGB dates/peak descriptions and ANA Muçum/Linha coverage/QC have been inspected. No model inference/errors on the reserved windows. Remaining ANA/ONS source collection is ongoing.',
    training_direction='Selected models end training targets before2026-07-01 and include later-than2021/2022 records. Results can assess retrospective transfer to reserved events, not predictions that could have been issued using only then-past training data.',
    windows=json.loads(reservation.read_text())['windows'],warmup='April28..30 of each respective year; do not concatenate year gaps.',
    features='Exact existing120 telemetry_features inputs, order, delays, weights and missingness contract from frozen references; no NWP/reanalysis, no filling missing upstream levels, no recalibration or changed rainfall threshold.',
    sources='27 ANA ALL-QC stations plus ONS literalCSV for JIUHQJ/JIUHMC/JIUHCA. Preserve23:59 timestamps and raw reported Q/I values; flag zeros, negatives, missingness and inconsistent component sums without creating new masks. Missing auxiliary inputs remainNaN.',
    target='Exact Muçum NivelFinal at target timestamp, finite/nonnegative and explicitly Dado aprovado. No NivelDisplay, peak marks, nearest-quarter substitution, interpolated truth or silent revisions. Source timezone assignment remains an assumption.',
    schedule='All hourly origins withinMay2021 andMayJune2022 with target inside the same reserved window, for each nominalh1..12. Report excluded boundary rows separately; predict only when frozen delayed base finite, preserving all schedule rows and failures. No certified real historical issuance is implied.',
    evaluation='Separate each year and pooled, all-target and observed>=7m subsets; perh1..12 all scheduled, complete24 and missing24 populations. Report observed targets, pairs, missing forecasts, missing truth, hits<=0.50m, pair fraction and observed-target inclusive hit fraction, MAE/bias/P98/max, and raw predictions. Missing forecasts count against observed-target fraction. Missing truth is unknown, never an acerto.',
    inference_gate='Before any inference, finish raw-source QC, verify frozen model/training/helper hashes, freeze prepared input matrix hashes and source receipts in a separate pre-inference manifest. If a source contract cannot be met, report the gap instead of changing the contract after seeing errors.',
    selection_and_promotion='No candidate changes from this challenge. If errors later guide modifications, these windows become development data, never a fresh holdout again. No automatic promotion from this retrospective challenge.',
    prospective_goal='Unchanged>=98% at<=0.50m separately real1..12h and high-water subset, >=1000 prospective verifiable forecasts/horizon and>=10 independently certified floods, with coverage/uncertainty; not fulfilled by this experiment.',
    model_records=records,reference_sha256={str(p.relative_to(ROOT)):sha(p) for p in refs},runtime=json.loads((C/'experiment.json').read_text())['runtime'],
    fitted=False,inference_performed=False,promoted=False,goal_achieved=False)
dump(PROTO,protocol);shutil.copyfile(PROTO,P/'protocol.json')
dump(P/'verification.json',dict(original_artifacts_verified=verified,frozen_models=24,models_features=120,reserved_training_exclusion_checked=True,membership_counts_checked=24,inference=False,protocol_sha256=sha(PROTO)))
dump(P/'artifact-hashes.json',[dict(file=str(p.relative_to(P)),sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps(dict(protocol=str(PROTO),frozen_models=24,protocol_sha256=sha(PROTO),inference=False),indent=2))
