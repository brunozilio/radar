"""Offline comparison of the saved 22h issue; no collection or publication."""
from pathlib import Path
from datetime import datetime, timedelta
import json, hashlib, csv
import numpy as np
import joblib
from sklearn.base import clone
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TRAIN = ROOT / 'outputs/mucum-hourly-20260921T220010-0300/radar-features.npz'
CURRENT = ROOT / 'outputs/mucum-hourly-20260921T220010-0300/radar-features.npz'
a = dict(np.load(TRAIN)); b = dict(np.load(CURRENT))
# telemetry_features has 24 level, 21 flow and 75 observed-rain features.
# weather_features appends 60 future meteorological forecast columns.
assert a['features'].shape[1] == b['features'].shape[1] == 180
assert np.all(np.diff(a['times']) == 3600)
cutoff = datetime.fromisoformat('2026-09-21T00:00:00-03:00').timestamp()
reference = datetime.fromisoformat('2026-09-21T22:00:00-03:00')
assert b['times'][-1] == reference.timestamp()
results = []
with threadpool_limits(limits=2):
 for lead in range(1, 7):
  frozen = joblib.load(ROOT / f'outputs/mucum-hourly-20260921T220010-0300/models/radar-{lead}.joblib')
  site = joblib.load(ROOT / f'model-artifacts/forecast-6h-v1/forecast-{lead}.joblib')
  target = np.r_[a['truth'][lead:], np.full(lead, np.nan)]
  delta = target - a['base']
  valid = np.isfinite(a['base']) & np.isfinite(target) & np.isfinite(a['features'][:, :24]).all(axis=1)
  train = np.where(valid & (a['times'] + lead * 3600 < cutoff))[0]
  assert len(train) > 1000 and np.max(a['times'][train] + lead * 3600) < cutoff
  weights = (1 + 2 * (abs(delta) >= 1) + 2 * (target >= 9))[train]
  baseline = float(frozen.predict(b['features'][-1:])[0] + b['base'][-1])
  full = clone(frozen).fit(a['features'][train], delta[train], sample_weight=weights)
  full_result = float(full.predict(b['features'][-1:])[0] + b['base'][-1])
  assert abs(full_result - baseline) < 1e-9, 'Local baseline must reproduce before comparison'
  observed = clone(frozen).fit(a['features'][train, :120], delta[train], sample_weight=weights)
  value = float(observed.predict(b['features'][-1:, :120])[0] + b['base'][-1])
  assert observed.n_features_in_ == 120 and np.isfinite(value)
  joblib.dump(observed, OUT / f'observed-only-{lead}.joblib')
  row = {'target': (reference + timedelta(hours=lead)).isoformat(), 'site_m': float(site.predict(b['features'][-1:])[0] + b['base'][-1]), 'local_with_forecast_m': baseline,
         'retrained_with_forecast_m': full_result, 'observed_only_m': value,
         'paired_difference_m': value - full_result, 'baseline_reproduction_error_m': full_result - baseline,
         'training_rows': len(train)}
  results.append(row)
  print(json.dumps(row), flush=True)
result = {'reference_at': reference.isoformat(), 'computed_at': datetime.now().astimezone().isoformat(),
          'observation': {'time': '2026-09-21T21:30:00-03:00', 'level_m': float(b['base'][-1])},
          'status': 'offline retrospective diagnostic; not a prospectively issued forecast',
          'training_cutoff': '2026-09-21T00:00:00-03:00', 'features_retained': 120, 'future_rain_features_removed': 60,
          'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [TRAIN, CURRENT]},
          'points': results}
(OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
with (OUT / 'comparison.csv').open('w') as f:
 w = csv.DictWriter(f, fieldnames=results[0]); w.writeheader(); w.writerows(results)
