"""Literal ONS extraction and frozen-delay availability audit; never model inference."""
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter
import csv,json,hashlib,math,bisect
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
IDS={'JIUHQJ':'14 DE JULHO','JIUHMC':'MONTE CLARO','JIUHCA':'CASTRO ALVES'}
FIELDS=['val_vazaodefluente','val_vazaoafluente','val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def num(s):
    try:v=float(s)
    except (ValueError,TypeError):return None
    return v if math.isfinite(v) else None
def dump(name,v):(P/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(name,rows,fields=None):
    with (P/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def flags(r):
    q,i,t,v,o=[num(r[k]) for k in FIELDS];cs=t+v+o if all(x is not None for x in (t,v,o)) else None
    return dict(q_zero=q==0,i_zero=i==0,q_negative=q is not None and q<0,i_negative=i is not None and i<0,
        q_zero_positive_components=q==0 and cs is not None and cs>1,
        balance_residual_gt1=q is not None and cs is not None and abs(q-cs)>1,
        component_sum_m3s=cs,balance_residual_m3s=q-cs if q is not None and cs is not None else None)

manifest=json.loads((P/'source-manifest.json').read_text());refs=[];source=[];summaries=[];conflicts=[]
assert len(manifest)==5
for m in manifest:
    assert m['status']=='preserved' and m['http_status']==200,m
    path=P/m['file'];assert sha(path)==m['sha256']
    rr=[]
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter=';');fields=reader.fieldnames
        for index,r in enumerate(reader,1):
            if r['id_reservatorio'] in IDS:
                assert r['nom_reservatorio']==IDS[r['id_reservatorio']]
                assert r['din_instante'].startswith(m['month'])
                assert datetime.fromisoformat(r['din_instante']).tzinfo is None
                rr.append(dict(r,source_file=str(path.relative_to(ROOT)),source_sha256=m['sha256'],source_record_index=index,source_csv_line=reader.line_num))
    assert rr
    name=f"ceran-{m['month']}-source-values.csv";save(name,rr,fields+['source_file','source_sha256','source_record_index','source_csv_line'])
    source.extend(rr);refs.append(dict(month=m['month'],literal_csv=str((P/name).relative_to(ROOT)),csv_sha256=sha(P/name),
        raw_source_path=str(path.relative_to(ROOT)),raw_source_sha256=m['sha256'],raw_source_url=m['url']))
    for code in IDS:
        plant=[r for r in rr if r['id_reservatorio']==code]
        counts=Counter(r['din_instante'] for r in plant)
        conflicts.extend(dict(month=m['month'],plant=code,time=t,rows=[r for r in plant if r['din_instante']==t]) for t,n in counts.items() if n>1)
        summaries.append(dict(month=m['month'],plant=code,rows=len(plant),unique_timestamps=len(counts),
            literal_2359=sum(r['din_instante'][11:16]=='23:59' for r in plant),
            Q_finite=sum(num(r[FIELDS[0]]) is not None for r in plant),I_finite=sum(num(r[FIELDS[1]]) is not None for r in plant),
            **{k:sum(flags(r)[k] for r in plant) for k in ('q_zero','i_zero','q_negative','i_negative','q_zero_positive_components','balance_residual_gt1')}))
dump('duplicate-or-conflict.json',conflicts)
assert not conflicts,'Do not resolve duplicated source timestamps automatically.'
save('source-summary.csv',summaries)
flagrows=[dict(r,**flags(r)) for r in source if any(flags(r)[k] for k in ('q_zero','i_zero','q_negative','i_negative','q_zero_positive_components','balance_residual_gt1'))]
save('source-diagnostics.csv',flagrows,list(source[0])+list(flags(source[0])))
index={code:sorted([r for r in source if r['id_reservatorio']==code],key=lambda r:r['din_instante']) for code in IDS}
times={code:[datetime.fromisoformat(r['din_instante']) for r in rr] for code,rr in index.items()}
origins=[datetime(2021,5,1)+timedelta(hours=h) for h in range(744)]+[datetime(2022,5,1)+timedelta(hours=h) for h in range(1464)]
trace=[];originrows=[]
for origin in origins:
    current=[]
    for code in IDS:
        for kind,back in [('Q',0),('Q',1),('Q',2),('Q',4),('Q',8),('I',0)]:
            query=origin-timedelta(hours=1+back);j=bisect.bisect_right(times[code],query)-1
            r=index[code][j] if j>=0 else None;age=(query-times[code][j]).total_seconds() if r else None
            value=num(r['val_vazaodefluente' if kind=='Q' else 'val_vazaoafluente']) if r else None
            usable=r is not None and age<=5400 and value is not None
            f=flags(r) if r else {}
            row=dict(year=origin.year,origin=origin.isoformat()+'-03:00',plant=code,variable=kind,back_hours=back,
                query_naive=query.isoformat(),source_time_naive=r['din_instante'] if r else None,age_seconds=age,
                value_m3s=value if usable else None,usable=usable,zero=usable and value==0,negative=usable and value<0,
                Q_zero_positive_components=bool(usable and kind=='Q' and f.get('q_zero_positive_components')),
                Q_balance_residual_gt1=bool(usable and kind=='Q' and f.get('balance_residual_gt1')),
                source_file=r['source_file'] if r else None,source_record_index=r['source_record_index'] if r else None)
            trace.append(row);current.append(row)
    originrows.append(dict(year=origin.year,origin=origin.isoformat()+'-03:00',all_18_lookups_available=all(r['usable'] for r in current),
        uses_any_zero=any(r['zero'] for r in current),uses_any_negative=any(r['negative'] for r in current),
        uses_Q_zero_positive_components=any(r['Q_zero_positive_components'] for r in current),
        uses_Q_balance_residual_gt1=any(r['Q_balance_residual_gt1'] for r in current)))
save('lag-source-trace.csv',trace);save('origin-diagnostics.csv',originrows);dump('ons-references.json',refs)
years=[]
for year in (2021,2022):
    rr=[r for r in originrows if r['year']==year]
    years.append(dict(year=year,origins=len(rr),**{k:sum(r[k] for r in rr) for k in ('all_18_lookups_available','uses_any_zero','uses_any_negative','uses_Q_zero_positive_components','uses_Q_balance_residual_gt1')}))
result=dict(rows=len(source),months=summaries,origin_coverage=years,lag_queries=len(trace),flagged_source_rows=len(flagrows),
    source_publication_time_certified=False,timezone_certified=False,model_inference=False,training=False,
    flag_policy='Diagnostic only, not official QC. Preserve reported zeros/negatives and timestamps including23:59; no repair, rejection mask or component replacement.',
    bounds='60min assumed delay and90min maximum age after query, unchanged frozen contract.',goal_achieved=False)
dump('audit.json',result)
dump('artifact-hashes.json',[dict(file=str(p.relative_to(P)),sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps({k:v for k,v in result.items() if k!='months'},indent=2))
