"""Rebuild recent120quarterhour predictors from audited strict-QC station archives."""
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from hydro_hourly_forecast import ROOT, epoch
from hydro_latency_forecast import telemetry_features
from hydro_model import asof
from hydro_rain_windows import observed_rain_windows
from hydro_routing_fit import shift

OUT = ROOT / 'outputs/radar-matriz-recente-ancora-15min-20260922'
PROTOCOL = ROOT / 'docs/radar-june2024-observed-features-protocol.json'
SNAPSHOT = ROOT / 'outputs/mucum-atualizacao-15h-2026-09-21/telemetria-latencia.npz'
WEIGHTS = ROOT / 'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json'
DELAYS = ROOT / 'outputs/auditoria-latencias-chuva-20260921/latencies.json'
LEVELS = {'86510000': (900, 900), '86472000': (1800, 900), '86472600': (900, 900), '86500000': (1800, 900)}


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def run(strict_dir, audit_manifest):
    assert strict_dir.is_dir() and audit_manifest.is_file()
    weights = json.loads(WEIGHTS.read_text())
    delays = {r['station']: r for r in json.loads(DELAYS.read_text())['stations']}
    station_paths = {c: strict_dir / f'ana-{c}.npz' for c in delays}
    assert all(p.is_file() for p in station_paths.values())
    paths = [PROTOCOL, Path(__file__), SNAPSHOT, WEIGHTS, DELAYS, audit_manifest, *station_paths.values()]
    paths += [ROOT / 'scripts' / name for name in ('hydro_hourly_forecast.py','hydro_latency_forecast.py','hydro_model.py','hydro_rain_windows.py','hydro_routing_fit.py')]
    hashes = {str(p.resolve()): sha(p) for p in paths}
    OUT.mkdir(exist_ok=False)
    dump(OUT / 'preparation-plan.json', {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'protocol': json.loads(PROTOCOL.read_text()), 'input_sha256': hashes})
    original = dict(np.load(SNAPSHOT, allow_pickle=False))
    grid = original['times']
    assert np.all(np.diff(grid) == 900)
    raw, delayed, rain = {}, {}, {}
    for code, path in station_paths.items():
        d = dict(np.load(path, allow_pickle=False))
        t, h, r = d['times'], d['level'], d['rain']
        assert t.shape == h.shape == r.shape and np.all(np.diff(t) > 0)
        assert not np.isinf(h).any() and not np.isinf(r).any()
        rw = observed_rain_windows(t, r, grid) if len(t) else {w: (np.zeros(len(grid)),np.zeros(len(grid))) for w in (1,3,6,12,24,48)}
        steps = int(delays[code]['shift_steps_15min'])
        assert steps == int(delays[code]['delay_seconds'] / 900)
        rain[code] = {w: (shift(v[0],steps),shift(v[1],steps)) for w,v in rw.items()}
        if code in LEVELS:
            raw[code + ':H'] = asof(t,h,grid,max_age=0)
            lag, age = LEVELS[code]
            delayed[code + ':H'] = asof(t,h,grid-lag,max_age=age)
    for plant in ('julho','monte','castro'):
        for key in ('Q','I'):
            raw[plant + ':' + key] = original['raw:' + plant + ':' + key].copy()
            delayed[plant + ':' + key] = original[plant + ':' + key].copy()
    for group in weights:
        for w in (1,3,6,12,24,48):
            amount = sum(weight*np.nan_to_num(rain[c][w][0],nan=0) for c,weight in group['weights'].items())
            cover = sum(weight*np.nan_to_num(rain[c][w][1],nan=0) for c,weight in group['weights'].items())
            delayed[group['group']+f':P{w}'] = np.where(cover>=.5,amount,np.nan)
            delayed[group['group']+f':C{w}'] = cover
    times,X,base,truth,phase,_ = telemetry_features(grid,raw,delayed)
    keep = times < epoch('2026-09-21T00:00:00-03:00')
    times,X,base,truth = times[keep],X[keep],base[keep],truth[phase][keep]
    assert X.shape == (12912,120)
    assert np.all(np.diff(times)==3600) and not np.isinf(X).any()
    np.savez_compressed(OUT/'features.npz',times=times,features=X,base=base,truth=truth,complete24=np.isfinite(X[:,:24]).all(axis=1))
    np.savez_compressed(OUT/'quarter-hour.npz',times=grid,**{'raw:'+k:v for k,v in raw.items()},**delayed)
    summary = {'origins':len(times),'features':120,'finite_base':int(np.isfinite(base).sum()),'finite_truth':int(np.isfinite(truth).sum()),'missing_cells':int(np.isnan(X).sum()),'complete24':int(np.isfinite(X[:,:24]).all(axis=1).sum()),'fits':0,'inferences':0,'operational_changes':0,'goal_achieved':False}
    for name,digest in hashes.items(): assert sha(Path(name))==digest
    dump(OUT/'preparation.json',{**summary,'input_sha256':hashes})
    with (OUT/'feature-coverage.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['column','finite','missing']);w.writeheader()
        w.writerows({'column':j,'finite':int(np.isfinite(X[:,j]).sum()),'missing':int(np.isnan(X[:,j]).sum())} for j in range(120))
    dump(OUT/'artifact-hashes.json',[{'file':p.name,'sha256':sha(p)} for p in sorted(OUT.iterdir())])
    print(json.dumps(summary),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--strict-dir',type=Path,required=True)
    parser.add_argument('--audit-manifest',type=Path,required=True)
    args=parser.parse_args()
    run(args.strict_dir,args.audit_manifest)
