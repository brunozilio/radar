"""Offline independent reconciliation of all selected raw ONS fields and delay lookups."""
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter,defaultdict
import csv,hashlib,json,math
P=Path(__file__).resolve().parent;ROOT=P.parents[1];D=ROOT/'outputs/ons-reserva-2021-2022-20260922'
IDS={'JIUHQJ','JIUHMC','JIUHCA'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def number(x):
    try:v=float(x)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
hh=json.loads((D/'artifact-hashes.json').read_text())
for x in hh:assert sha(D/x['file'])==x['sha256']
plan=json.loads((D/'collection-plan.json').read_text());manifest=json.loads((D/'source-manifest.json').read_text());refs=json.loads((D/'ons-references.json').read_text())
allrows={};compared=0;physical=0;lookup=defaultdict(dict);duplicate_keys=set()
for m,ref in zip(manifest,refs):
    assert m['month']==ref['month'] and plan['registered_at_utc']<m['requested_at_utc']
    raw=D/m['file'];assert m['http_status']==200 and sha(raw)==m['sha256']==ref['raw_source_sha256']
    extracted=ROOT/ref['literal_csv'];assert sha(extracted)==ref['csv_sha256']
    selected=list(csv.DictReader(extracted.open()));by_index={int(r['source_record_index']):r for r in selected};assert len(by_index)==len(selected)
    with raw.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter=';');columns=reader.fieldnames;seen=set()
        for i,row in enumerate(reader,1):
            physical+=1
            if row['id_reservatorio'] not in IDS:continue
            actual=by_index[i];seen.add(i)
            assert {k:actual[k] for k in columns}==row
            assert actual['source_file']==str(raw.relative_to(ROOT)) and actual['source_sha256']==m['sha256']
            assert int(actual['source_csv_line'])==reader.line_num
            key=(actual['source_file'],i);assert key not in allrows;allrows[key]=row
            station=row['id_reservatorio'];t=datetime.fromisoformat(row['din_instante'])
            assert t not in lookup[station];lookup[station][t]=row
            compared+=1
        assert seen==set(by_index)
following={}
for station,rr in lookup.items():
    tt=sorted(rr)
    for i,t in enumerate(tt):following[station,t]=tt[i+1] if i+1<len(tt) else None
trace=list(csv.DictReader((D/'lag-source-trace.csv').open()));origins=defaultdict(list)
for tr in trace:
    origin=datetime.fromisoformat(tr['origin']);assert origin.utcoffset()==timedelta(hours=-3)
    query=origin.replace(tzinfo=None)-timedelta(hours=1+int(tr['back_hours']))
    assert datetime.fromisoformat(tr['query_naive'])==query
    row=allrows[tr['source_file'],int(tr['source_record_index'])]
    source_time=datetime.fromisoformat(row['din_instante']);assert tr['source_time_naive']==row['din_instante']
    assert row['id_reservatorio']==tr['plant'] and source_time<=query
    following_time=following[tr['plant'],source_time];assert following_time is None or following_time>query
    age=(query-source_time).total_seconds();assert float(tr['age_seconds'])==age
    value=number(row['val_vazaodefluente' if tr['variable']=='Q' else 'val_vazaoafluente'])
    usable=age<=5400 and value is not None;assert (tr['usable']=='True')==usable
    assert number(tr['value_m3s'])==(value if usable else None)
    assert (tr['zero']=='True')==(usable and value==0)
    assert (tr['negative']=='True')==(usable and value<0)
    q=number(row['val_vazaodefluente']);components=[number(row[k]) for k in ('val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas')]
    total=sum(components) if all(x is not None for x in components) else None
    zero_components=bool(usable and tr['variable']=='Q' and q==0 and total is not None and total>1)
    residual=bool(usable and tr['variable']=='Q' and q is not None and total is not None and abs(q-total)>1)
    assert (tr['Q_zero_positive_components']=='True')==zero_components
    assert (tr['Q_balance_residual_gt1']=='True')==residual
    origins[tr['origin']].append(tr)
for rr in origins.values():
    assert len(rr)==18 and len({(r['plant'],r['variable'],r['back_hours']) for r in rr})==18
audit=json.loads((D/'audit.json').read_text());assert audit['rows']==compared and audit['lag_queries']==len(trace)
for s in audit['origin_coverage']:
    rr=[v for k,v in origins.items() if k.startswith(str(s['year']))];assert len(rr)==s['origins']
    assert sum(all(r['usable']=='True' for r in o) for o in rr)==s['all_18_lookups_available']
    for key,col in [('uses_any_zero','zero'),('uses_any_negative','negative'),('uses_Q_zero_positive_components','Q_zero_positive_components'),('uses_Q_balance_residual_gt1','Q_balance_residual_gt1')]:
        assert sum(any(r[col]=='True' for r in o) for o in rr)==s[key]
result=dict(passed=True,artifact_hashes_verified=len(hh),raw_csv_responses=5,raw_rows_scanned=physical,all_fields_reconciled_rows=compared,
    all_asof_queries_reconciled=len(trace),all_origins_reconciled=len(origins),source_timestamps_modified=False,model_access=False,
    no_claim_of_physical_QI_validity=True,origin_coverage=audit['origin_coverage'])
dump(P/'verification.json',result)
dump(P/'artifact-hashes.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps(result,indent=2))
