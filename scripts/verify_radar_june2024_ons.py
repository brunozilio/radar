"""Independently reconstruct literal source extraction and every lag lookup."""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'outputs/auditoria-qi-radar-junho2024-20260922'
OUT = ROOT / 'outputs/verificacao-qi-radar-junho2024-20260922'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    checks = 0
    for item in json.loads((SRC/'artifact-hashes.json').read_text()):
        assert sha(SRC/item['file']) == item['sha256']; checks += 1
    raw = SRC/'raw/ons-2024-06.csv'
    extracted = list(csv.DictReader((SRC/'ceran-2024-06-source-values.csv').open()))
    expected = []
    codes = ['JIUHQJ', 'JIUHMC', 'JIUHCA']
    with raw.open(encoding='utf-8-sig') as f:
        for i, r in enumerate(csv.DictReader(f, delimiter=';')):
            if r['id_reservatorio'] in codes:
                expected.append(dict(r, source_file=str(raw.relative_to(ROOT)), source_record_index=str(i)))
    assert expected == extracted; checks += len(expected)
    index = {(r['id_reservatorio'], datetime.fromisoformat(r['din_instante'])): r for r in extracted}
    assert len(index) == len(extracted); checks += 1
    per_plant = {c: sorted(t for plant,t in index if plant == c) for c in codes}
    expected_times = [datetime(2024,6,day,hour) for day in range(1,31) for hour in range(1,24)]
    expected_times += [datetime(2024,6,day,23,59) for day in range(1,31)]
    for c in codes:
        assert per_plant[c] == sorted(expected_times); checks += 1
    traces = list(csv.DictReader((SRC/'lag-source-trace.csv').open()))
    identities = set()
    for r in traces:
        origin = datetime.fromisoformat(r['origin_literal'])
        query = origin-timedelta(hours=1+int(r['back_hours']))
        assert query == datetime.fromisoformat(r['query_literal']); checks += 1
        c = r['plant']; t = max(t for t in per_plant[c] if t <= query)
        source = index[(c,t)]
        field = 'val_vazaodefluente' if r['variable']=='Q' else 'val_vazaoafluente'
        assert r['source_literal']==source['din_instante']; checks += 1
        assert float(r['value_m3s']) == float(source[field]); checks += 1
        assert float(r['age_seconds']) == (query-t).total_seconds() <= 5400; checks += 1
        assert r['source_record_index'] == source['source_record_index']; checks += 1
        identities.add((origin,c,r['variable'],int(r['back_hours'])))
    assert len(identities)==len(traces)==168*18; checks += 1
    summary = []
    for scope,start in [('month','2024-06-01'),('warmup','2024-06-12'),('central','2024-06-15')]:
        stop = '2024-07-01' if scope=='month' else '2024-06-22'
        for c in codes:
            rr=[r for r in extracted if r['id_reservatorio']==c and start<=r['din_instante']<stop]
            differences=[float(r['val_vazaodefluente'])-sum(float(r[k]) for k in
                         ['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']) for r in rr]
            summary.append({'scope':scope,'plant':c,'n':len(rr),
                'q_equals_i':sum(float(r['val_vazaodefluente'])==float(r['val_vazaoafluente']) for r in rr),
                'turbine_zero':sum(float(r['val_vazaoturbinada'])==0 for r in rr),
                'component_residual_gt1':sum(abs(x)>1 for x in differences),
                'residual_min':min(differences),'residual_max':max(differences)})
    shared = sum(index[('JIUHQJ',t)]['val_vazaodefluente']==index[('JIUHMC',t)]['val_vazaodefluente']
                 for t in per_plant['JIUHQJ'])
    result={'passed':True,'checks':checks,'rows':len(extracted),'lookups':len(traces),
            'summary':summary,'julho_monte_equal_Q':shared,
            'source_artifact_manifest_sha256':sha(SRC/'artifact-hashes.json'),
            'source_script_sha256':sha(ROOT/'scripts/hydro_radar_june2024_ons.py'),
            'source_index_convention':'Zero-based data-row index, header excluded.',
            'fits':0,'inferences':0,'goal_achieved':False}
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (OUT/'verify.py').write_bytes(Path(__file__).read_bytes())
    (OUT/'manifest.json').write_text(json.dumps([{'file':p.name,'sha256':sha(p)} for p in sorted(OUT.iterdir())],indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
