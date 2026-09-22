"""Independent reconstruction only; never imports model/preparation helpers."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json
import numpy as np

P = Path(__file__).resolve().parent
R = P.parents[1]
B = R / 'outputs/experimento-radar-mistura-atrasos-20260922'
S = {'A': 'mucum-hourly-20260922T000704-0300', 'B': 'mucum-hourly-20260922T010016-0300'}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def reconstruct():
    paths = [B/'prepared-inputs.npz', R/'scripts/hydro_latency_forecast.py', R/'scripts/hydro_model.py', R/'scripts/hydro_routing_fit.py']
    z = dict(np.load(paths[0])); origins = z['times']; result = {}; summaries = []
    for profile, folder in S.items():
        folder = R/'outputs'/folder
        history = folder/'history/ana-86510000.npz'; agefile = folder/'idades-fontes.csv'
        paths += [history, agefile]
        h = dict(np.load(history))
        delay = float(next(r for r in csv.DictReader(agefile.open()) if r['source']=='86510000')['delay_minutes'])*60
        assert np.all(np.diff(h['times']) > 0)
        # Separate chronological cursors select each literal predecessor, including
        # an invalid newest record; no search backwards for a finite value.
        values = {}; stamps = {}
        for offset in (0, 1, 2):
            v = np.full(len(origins), np.nan); ts = np.full(len(origins), np.nan); cursor = -1
            for i, origin in enumerate(origins):
                query = origin - offset*3600 - delay
                while cursor+1 < len(h['times']) and h['times'][cursor+1] <= query:
                    cursor += 1
                if cursor >= 0 and query-h['times'][cursor] <= 900:
                    ts[i] = h['times'][cursor]; v[i] = h['level'][cursor]
            values[offset] = v; stamps[offset] = ts
        np.testing.assert_array_equal(values[0], z['base_'+profile])
        for hours, column in ((1, 2), (2, 3)):
            derived = (values[0]-values[hours])/hours
            # The generator shifts within its finite grid, so the first hours
            # cannot use an earlier source outside that grid.
            derived[:hours] = np.nan
            np.testing.assert_array_equal(derived, z['features_'+profile][:,column])
            finite = np.isfinite(derived); elapsed = (stamps[0]-stamps[hours])/3600
            result[profile+'_column'+str(column)] = derived
            summaries.append(dict(profile=profile, column=column, name=f'86510000:dH{hours}',
                units='m/hour_nominal', nominal_hours=hours, delay_minutes=delay/60,
                rows=len(origins), finite=int(finite.sum()), missing=int((~finite).sum()),
                finite_with_non_nominal_measurement_interval=int((finite & (elapsed != hours)).sum()),
                measurement_interval_hours=sorted(set(elapsed[finite].tolist()))))
    result['times'] = origins
    return result, summaries, {str(p.relative_to(R)):sha(p) for p in paths}

if __name__ == '__main__':
    result, summaries, hashes = reconstruct()
    np.savez_compressed(P/'reconstructed-trends.npz', **result)
    (P/'contract-verification.json').write_text(json.dumps(dict(passed=True,
        verified_at_utc=datetime.now(timezone.utc).isoformat(), columns=summaries,
        input_sha256=hashes, diagnostic_outputs_not_yet_audited=True), indent=2)+'\n')
