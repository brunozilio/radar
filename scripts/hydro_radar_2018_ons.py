"""Collect three catalog-listed ONS resources and audit literal CERAN fields."""
import bisect
import csv
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/auditoria-qi-radar-2018-20260922'
CATALOG = ROOT / 'outputs/historico-vazoes-ceran/raw/catalog.json'
IDS = {'JIUHQJ': '14 DE JULHO', 'JIUHMC': 'MONTE CLARO', 'JIUHCA': 'CASTRO ALVES'}
FIELDS = ['val_vazaodefluente', 'val_vazaoafluente', 'val_vazaoturbinada',
          'val_vazaovertida', 'val_vazaooutrasestruturas']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def save(path, rows, fields=None):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def num(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def flags(row):
    q, i, t, v, o = [num(row[k]) for k in FIELDS]
    component_sum = t + v + o if all(x is not None for x in (t, v, o)) else None
    return {'Q_zero': q == 0, 'I_zero': i == 0,
            'Q_negative': q is not None and q < 0, 'I_negative': i is not None and i < 0,
            'Q_missing': q is None, 'I_missing': i is None,
            'Q_zero_positive_components': q == 0 and component_sum is not None and component_sum > 1,
            'balance_residual_gt1': q is not None and component_sum is not None and abs(q - component_sum) > 1}


def run():
    OUT.mkdir(exist_ok=False)
    (OUT / 'raw').mkdir()
    catalog = json.loads(CATALOG.read_text())
    resources = catalog.get('result', catalog)['resources']
    jobs = []
    for month in ('2018-08', '2018-09', '2018-10'):
        resource = next(r for r in resources if r['url'].endswith(month.replace('-', '_') + '.csv'))
        jobs.append({'month': month, 'resource_id': resource['id'], 'url': resource['url']})
    dump(OUT / 'collection-plan.json', {
        'created_at_utc': datetime.now(timezone.utc).isoformat(), 'jobs': jobs,
        'catalog_path': str(CATALOG.relative_to(ROOT)), 'catalog_sha256': sha(CATALOG),
        'script_sha256': sha(Path(__file__)), 'maximum_gets': 3, 'maximum_bytes_each': 32 * 1024 * 1024,
        'no_retries': True, 'stations': IDS, 'purpose': 'Literal source audit, no fit, inference or operational changes.',
        'windows_including_warmup': [['2018-08-27', '2018-09-05'], ['2018-09-27', '2018-10-06']],
        'time_policy': 'Preserve literal timestamps, including23:59; no timezone or publication certification.',
        'diagnostic_policy': 'Keep zeros, negatives and missing fields; flag, never repair or certify. A residual>1m3/s is a diagnostic, not an official QC flag.',
        'lookup_policy': 'For each hourly origin in the central7days, Q current/back1/2/4/8h and I current use a declared60min lag with maximum age90min after query. Publication latency not verified.'})
    receipts = []
    for job in jobs:
        destination = OUT / 'raw' / ('ons-' + job['month'] + '.csv')
        side = destination.with_suffix('.receipt.json')
        meta = {**job, 'requested_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'request_started'}
        dump(side, meta)
        try:
            try:
                with urlopen(Request(job['url'], headers={'User-Agent': 'Radar-public-history/1.0'}), timeout=60) as response:
                    body = response.read(32 * 1024 * 1024 + 1)
                    meta.update(http_status=response.status, headers=dict(response.headers), final_url=response.url)
            except HTTPError as exc:
                body = exc.read(32 * 1024 * 1024 + 1)
                meta.update(http_status=exc.code, headers=dict(exc.headers))
            if len(body) > 32 * 1024 * 1024:
                raise ValueError('Response exceeded bound')
            destination.write_bytes(body)
            meta.update(status='response_preserved', file=str(destination.relative_to(OUT)),
                        sha256=sha(destination), bytes=len(body))
        except Exception as exc:
            meta.update(status='request_failed', error=str(exc))
        meta['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        dump(side, meta)
        receipts.append(meta)
        print(job['month'], meta['status'], meta.get('http_status'), flush=True)
    dump(OUT / 'source-manifest.json', receipts)
    if any(r['status'] != 'response_preserved' or r['http_status'] != 200 for r in receipts):
        raise RuntimeError('Incomplete acquisition preserved; inspect before further work')
    all_rows, summaries, references = [], [], []
    for receipt in receipts:
        path = OUT / receipt['file']
        assert sha(path) == receipt['sha256']
        with path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream, delimiter=';')
            fields = reader.fieldnames
            rows = [dict(r, source_file=str(path.relative_to(ROOT)), source_record_index=index)
                    for index, r in enumerate(reader) if r['id_reservatorio'].strip() in IDS]
        assert rows and all(r['nom_reservatorio'] == IDS[r['id_reservatorio'].strip()] for r in rows)
        assert all(r['din_instante'].startswith(receipt['month']) for r in rows)
        literal = OUT / ('ceran-' + receipt['month'] + '-source-values.csv')
        save(literal, rows, fields + ['source_file', 'source_record_index'])
        all_rows.extend(rows)
        references.append({'month': receipt['month'], 'literal_csv': str(literal.relative_to(ROOT)),
                           'csv_sha256': sha(literal), 'raw_source_path': str(path.relative_to(ROOT)),
                           'raw_source_sha256': sha(path), 'raw_source_url': receipt['url']})
        for code in IDS:
            rr = [r for r in rows if r['id_reservatorio'].strip() == code]
            summaries.append({'month': receipt['month'], 'plant': code, 'rows': len(rr),
                              'literal_2359': sum(r['din_instante'][11:16] == '23:59' for r in rr),
                              **{key: sum(flags(r)[key] for r in rr) for key in flags(rr[0])}})
    assert len({(r['id_reservatorio'], r['din_instante']) for r in all_rows}) == len(all_rows)
    save(OUT / 'source-summary.csv', summaries)
    save(OUT / 'source-diagnostics.csv', [dict(r, **flags(r)) for r in all_rows if any(flags(r).values())],
         list(all_rows[0]) + list(flags(all_rows[0])))
    dump(OUT / 'ons-references.json', references)
    indices = {code: sorted([r for r in all_rows if r['id_reservatorio'].strip() == code], key=lambda r: r['din_instante']) for code in IDS}
    times = {code: [datetime.fromisoformat(r['din_instante']) for r in rr] for code, rr in indices.items()}
    traces, origins = [], []
    for start in ('2018-08-30', '2018-09-30'):
        for hour in range(168):
            origin = datetime.fromisoformat(start) + timedelta(hours=hour)
            current = []
            for code in IDS:
                for variable, back in [('Q', 0), ('Q', 1), ('Q', 2), ('Q', 4), ('Q', 8), ('I', 0)]:
                    query = origin - timedelta(hours=1 + back)
                    index = bisect.bisect_right(times[code], query) - 1
                    row = indices[code][index] if index >= 0 else None
                    age = (query - times[code][index]).total_seconds() if row else None
                    value = num(row[FIELDS[0 if variable == 'Q' else 1]]) if row else None
                    usable = row is not None and age <= 5400 and value is not None
                    diagnostic = flags(row) if row else {}
                    entry = {'window': start, 'origin_literal': origin.isoformat(), 'plant': code,
                             'variable': variable, 'back_hours': back, 'query_literal': query.isoformat(),
                             'source_literal': row['din_instante'] if row else None, 'age_seconds': age,
                             'value_m3s': value if usable else None, 'usable': usable,
                             'uses_zero': usable and value == 0,
                             'Q_zero_positive_components': bool(usable and variable == 'Q' and diagnostic.get('Q_zero_positive_components')),
                             'Q_balance_residual_gt1': bool(usable and variable == 'Q' and diagnostic.get('balance_residual_gt1')),
                             'source_file': row['source_file'] if row else None,
                             'source_record_index': row['source_record_index'] if row else None}
                    assert row is None or datetime.fromisoformat(row['din_instante']) <= query < origin
                    traces.append(entry)
                    current.append(entry)
            origins.append({'window': start, 'origin_literal': origin.isoformat(),
                            'all_18_lookups_available': all(r['usable'] for r in current),
                            **{key: any(r[key] for r in current) for key in ('uses_zero', 'Q_zero_positive_components', 'Q_balance_residual_gt1')}})
    save(OUT / 'lag-source-trace.csv', traces)
    save(OUT / 'origin-diagnostics.csv', origins)
    audit = {'source_rows': len(all_rows), 'origins': len(origins), 'lookups': len(traces),
             'all_lookups_available': sum(r['all_18_lookups_available'] for r in origins),
             **{key: sum(r[key] for r in origins) for key in ('uses_zero', 'Q_zero_positive_components', 'Q_balance_residual_gt1')},
             'fits': 0, 'inferences': 0, 'operational_changes': 0, 'goal_achieved': False}
    dump(OUT / 'audit.json', audit)
    dump(OUT / 'artifact-hashes.json', [{'file': str(p.relative_to(OUT)), 'sha256': sha(p)}
                                      for p in sorted(OUT.rglob('*')) if p.is_file()])
    print(json.dumps(audit), flush=True)


if __name__ == '__main__':
    run()
