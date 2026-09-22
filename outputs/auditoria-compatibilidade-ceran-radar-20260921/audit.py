"""Local, read-only input audit. Does not fit or issue any forecast."""
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from hydro_hourly_forecast import epoch, iso
from hydro_reservoir_level_experiment import prepare_levels, PLANTS, FIELDS
from hydro_radar_native_missing import training_masks
from hydro_routing_fit import shift

OUT = Path(__file__).resolve().parent
CYCLE = ROOT / 'outputs/mucum-hourly-20260921T210023-0300'
MODEL = ROOT / 'outputs/experimento-radar-niveis-reservatorios-20260921'
ONS = ROOT / 'outputs/mucum-propagacao-2026-09-21/raw/DADOS_HIDROLOGICOS_HO_2026_09-ceran.csv'
TZ = timezone(timedelta(hours=-3))  # Assumption retained from historical protocol.


class Table(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.cell = None
        self.row = []
        self.rows = []
        self.headers = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table' and dict(attrs).get('id') == 'customers':
            assert not self.inside
            self.inside = True
        if not self.inside:
            return
        if tag == 'tr':
            self.row = []
        elif tag in ('td', 'th'):
            self.cell = []
        elif tag == 'br' and self.cell is not None:
            self.cell.append(' ')

    def handle_data(self, data):
        if self.inside and self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if not self.inside:
            return
        if tag in ('td', 'th'):
            text = ' '.join(''.join(self.cell).split())
            self.row.append(text)
            if tag == 'th':
                self.headers.append(text)
            self.cell = None
        elif tag == 'tr' and self.row:
            self.rows.append(self.row)
        elif tag == 'table':
            self.inside = False


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, rows):
    with (OUT / name).open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def verify_artifact(folder, name):
    manifest = json.loads((folder / 'artifact-hashes.json').read_text())
    expected = next(r['sha256'] for r in manifest if r['file'] == name)
    assert sha(folder / name) == expected


def run():
    paths = [Path(__file__), ONS, CYCLE/'collection-manifest.json', CYCLE/'run.json',
             MODEL/'features.npz', MODEL/'training.csv',
             ROOT/'scripts/hydro_reservoir_level_experiment.py',
             ROOT/'scripts/hydro_radar_native_missing.py', ROOT/'scripts/hydro_routing_fit.py',
             ROOT/'scripts/hydro_hourly_forecast.py']
    for name in ('features.npz', 'training.csv'):
        verify_artifact(MODEL, name)
    collection = {r['file']: r for r in json.loads(paths[2].read_text())}
    origin = epoch(json.loads(paths[3].read_text())['reference_time'])
    source = []
    source_meta = []
    for plant, identifier in PLANTS.items():
        path = CYCLE/'raw'/f'ceran-{plant}-fresh.html'
        paths.append(path)
        receipt = collection[path.name]
        assert receipt['sha256'] == sha(path) and receipt['status'] == 200
        table = Table()
        table.feed(path.read_text())
        assert table.headers[:3] == ['Data / Hora', 'Nível Montante (m)', 'Nível Justante (m)']
        stamps = []
        for row in table.rows[1:]:
            assert len(row) == 8
            at = datetime.strptime(row[0], '%d/%m/%Y %H:%M:%S').replace(tzinfo=TZ)
            stamps.append(at.timestamp())
            # Fail on malformed tokens; empty cells remain missing, never filled.
            levels = [float(v) if v.strip() else float('nan') for v in row[1:3]]
            source.append(dict(id_reservatorio=identifier, din_instante=at.isoformat(),
                               val_nivelmontante=levels[0], val_niveljusante=levels[1]))
        assert len(stamps) == len(set(stamps)) and len(stamps) > 6
        source_meta.append(dict(plant=plant, rows=len(stamps), earliest=iso(min(stamps)),
                                latest=iso(max(stamps)), headers=table.headers,
                                collected_at=receipt['collected_at'], url=receipt['url'],
                                latest_age_at_reference_min=(origin-max(stamps))/60,
                                sha256=receipt['sha256']))
    historical = list(csv.DictReader(ONS.open(), delimiter=';'))
    index = {}
    for row in historical:
        key = (row['id_reservatorio'].strip(), epoch(row['din_instante']))
        assert key not in index
        index[key] = row
    comparisons = []
    for row in source:
        at = epoch(row['din_instante'])
        other = index.get((row['id_reservatorio'], at))
        for field in FIELDS:
            current = row[field]
            previous = float(other[field]) if other and other[field] else float('nan')
            both = bool(np.isfinite(current) and np.isfinite(previous))
            comparisons.append(dict(plant=row['id_reservatorio'], time=iso(at), field=field,
                                    ceran_m=current if np.isfinite(current) else None,
                                    ons_m=previous if np.isfinite(previous) else None,
                                    timestamp_overlap=other is not None,
                                    delta_m=current-previous if both else None))
    times = np.arange(origin-7*3600, origin+1, 3600)
    values, names, trace = prepare_levels(source, times)
    now = values[-1]
    assert len(names) == 24 and values.shape == (8, 24)
    # Independent exact-hour reconstruction for this complete live snapshot.
    live_index = {(r['id_reservatorio'], epoch(r['din_instante'])): r for r in source}
    earlier = ROOT/'outputs/mucum-hourly-20260921T180020-0300'
    paths.append(earlier/'collection-manifest.json')
    prior_receipts = {r['file']: r for r in json.loads(paths[-1].read_text())}
    revisions = []
    for plant, identifier in PLANTS.items():
        path = earlier/'raw'/f'ceran-{plant}-fresh.html'
        paths.append(path)
        assert sha(path) == prior_receipts[path.name]['sha256']
        table = Table()
        table.feed(path.read_text())
        assert table.headers[:3] == ['Data / Hora', 'Nível Montante (m)', 'Nível Justante (m)']
        for row in table.rows[1:]:
            at = datetime.strptime(row[0], '%d/%m/%Y %H:%M:%S').replace(tzinfo=TZ).timestamp()
            other = live_index.get((identifier, at))
            if other is None:
                continue
            for j, field in enumerate(FIELDS, 1):
                previous, current = float(row[j]), other[field]
                revisions.append(dict(plant=identifier, time=iso(at), field=field,
                                      earlier_m=previous, later_m=current,
                                      delta_m=current-previous,
                                      earlier_collected_at=prior_receipts[path.name]['collected_at'],
                                      later_collected_at=collection[path.name]['collected_at']))
    manual = []
    for identifier in PLANTS.values():
        for field in FIELDS:
            samples = [live_index[(identifier, origin-(1+h)*3600)][field] for h in (0, 1, 3, 6)]
            manual += [samples[0], samples[0]-samples[1], (samples[0]-samples[2])/3, (samples[0]-samples[3])/6]
    np.testing.assert_array_equal(now, manual)
    frozen = dict(np.load(MODEL/'features.npz'))
    training = {(r['phase'], int(r['horizon_h'])): r for r in csv.DictReader((MODEL/'training.csv').open())}
    bounds = []
    missing_training = []
    for h in range(1, 13):
        target = shift(frozen['truth'], -h)
        masks = training_masks(frozen['times'], frozen['base'], target, frozen['complete24'], h,
                               epoch('2025-10-01T00:00:00-03:00'), epoch('2026-07-01T00:00:00-03:00'))
        for phase in ('validation', 'test'):
            selected = frozen['features'][masks[phase, 'baseline'], 180:]
            meta = training[phase, h]
            assert len(selected) == int(meta['training_n'])
            missing = int((~np.isfinite(selected).all(axis=1)).sum())
            assert missing == int(meta['training_with_missing_reservoir_input'])
            missing_training.append(dict(phase=phase, horizon_h=h, training_rows=len(selected),
                                         with_missing_reservoir_features=missing))
            for j, name in enumerate(names):
                low, high = float(np.nanmin(selected[:, j])), float(np.nanmax(selected[:, j]))
                bounds.append(dict(phase=phase, horizon_h=h, column=180+j, name=name,
                                   current_value=float(now[j]), training_min=low, training_max=high,
                                   outside=bool(now[j] < low or now[j] > high)))
    summaries = []
    for identifier in PLANTS.values():
        for field in FIELDS:
            group = [r for r in comparisons if r['plant'] == identifier and r['field'] == field]
            delta = np.array([r['delta_m'] for r in group if r['delta_m'] is not None])
            summaries.append(dict(plant=identifier, field=field, live_rows=len(group), paired=len(delta),
                                  equal_within_1e_9m=int((abs(delta) <= 1e-9).sum()),
                                  max_abs_difference_m=float(abs(delta).max()),
                                  median_abs_difference_m=float(np.median(abs(delta)))))
    summary = dict(reference=iso(origin), sources=source_meta, comparisons=summaries,
                   cross_snapshot_pairs=len(revisions),
                   cross_snapshot_revisions=[r for r in revisions if abs(r['delta_m']) > 1e-9],
                   live_features_finite=int(np.isfinite(now).sum()), live_features_total=24,
                   training_sets_with_missing_reservoir_features=sum(r['with_missing_reservoir_features'] > 0 for r in missing_training),
                   training_sets=len(missing_training),
                   outside_names_by_phase={phase: sorted(set(r['name'] for r in bounds if r['phase'] == phase and r['outside'])) for phase in ('validation', 'test')},
                   utc_minus_3_assumed=True, same_datum_certified=False,
                   historical_publication_latency_certified=False, candidate_issued=False, model_promoted=False,
                   input_sha256={str(p.relative_to(ROOT)): sha(p) for p in paths})
    save('source-comparison.csv', comparisons)
    save('snapshot-revisions.csv', revisions)
    save('feature-source-trace.csv', trace)
    save('training-bounds.csv', bounds)
    save('training-missingness.csv', missing_training)
    save('live-features.csv', [dict(column=180+i, name=n, value=float(now[i])) for i,n in enumerate(names)])
    (OUT/'audit.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('input_sha256', 'sources')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
