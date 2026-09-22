"""Separate raw revisions, current latency changes and training membership drift."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
A=ROOT/'outputs/mucum-hourly-20260922T000704-0300'
B=ROOT/'outputs/mucum-hourly-20260922T010016-0300'
SA=ROOT/'outputs/auditoria-suporte-radar-live-00h-20260922-v2'
SB=ROOT/'outputs/auditoria-suporte-radar-live-01h-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def compare(a,b):
    eq=(a==b)|(np.isnan(a)&np.isnan(b));finite=np.isfinite(a)&np.isfinite(b)
    return dict(rows=len(a),changed=int((~eq).sum()),availability_changes=int((np.isfinite(a)!=np.isfinite(b)).sum()),
                max_finite_difference=float(np.max(abs(a[finite]-b[finite]))) if finite.any() else None)
def main():
    qa,qb=[dict(np.load(p/'telemetria-latencia.npz')) for p in (A,B)]
    da,db=[dict(np.load(p/'radar-features.npz')) for p in (A,B)]
    cut=1790046000-86400 # 2026-09-21T00:00:00-03:00, independently fixed
    qta,qtb=[q['times']<cut for q in (qa,qb)];ta,tb=[d['times']<cut for d in (da,db)]
    np.testing.assert_array_equal(qa['times'][qta],qb['times'][qtb]);np.testing.assert_array_equal(da['times'][ta],db['times'][tb])
    raw=[dict(field=k,**compare(qa[k][qta],qb[k][qtb])) for k in sorted(qa) if k.startswith('raw:')]
    history=[];history_paths=[]
    for pa in sorted((A/'history').glob('*.npz')):
        pb=B/'history'/pa.name;aa,bb=dict(np.load(pa)),dict(np.load(pb));history_paths.extend((pa,pb))
        ia,ib=aa['times']<cut,bb['times']<cut
        np.testing.assert_array_equal(aa['times'][ia],bb['times'][ib])
        for field in sorted(aa):
            if field!='times':history.append(dict(source=pa.name,field=field,**compare(aa[field][ia],bb[field][ib])))
    feature=[dict(column=j,**compare(da['features'][ta,j],db['features'][tb,j])) for j in range(180)]
    ages=[{r['source']:r for r in csv.DictReader((p/'idades-fontes.csv').open())} for p in (A,B)]
    age_rows=[dict(source=s,lag_before_minutes=float(ages[0][s]['delay_minutes']),lag_after_minutes=float(ages[1][s]['delay_minutes']),
                   before_last=ages[0][s]['last_time'],after_last=ages[1][s]['last_time']) for s in sorted(ages[0])]
    ma,mb=[dict(np.load(p/'training-indices.npz')) for p in (SA,SB)]
    membership=[]
    for h in range(1,15):
        a=set(da['times'][ma[f'h{h}']]);b=set(db['times'][mb[f'h{h}']]);both=sorted(a&b)
        ai=np.searchsorted(da['times'],both);bi=np.searchsorted(db['times'],both)
        membership.append(dict(nominal_lead_h=h,before=len(a),after=len(b),added=len(b-a),removed=len(a-b),common=len(both),
            common_base_changed=compare(da['base'][ai],db['base'][bi])['changed'],
            common_target_changed=compare(da['truth'][ai+h],db['truth'][bi+h])['changed']))
    paths=[Path(__file__),ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_hourly_forecast.py']
    paths += [p/name for p in (A,B) for name in ('radar-features.npz','telemetria-latencia.npz','idades-fontes.csv','run-result.json','history/manifest.json')]
    paths += [p/'training-indices.npz' for p in (SA,SB)]
    paths += history_paths
    save('raw-revisions-before-cutoff.csv',raw);save('feature-changes-before-cutoff.csv',feature);save('source-ages.csv',age_rows);save('membership.csv',membership)
    save('history-revisions-before-cutoff.csv',history)
    summary=dict(cutoff_exclusive='2026-09-21T00:00:00-03:00',raw_fields_changed=[r for r in raw if r['changed']],
        history_fields_checked=len(history),history_fields_changed=[r for r in history if r['changed']],
        feature_columns_changed=sum(r['changed']>0 for r in feature),feature_cells_changed=sum(r['changed'] for r in feature),
        source_delay_changes=[r for r in age_rows if r['lag_before_minutes']!=r['lag_after_minutes']],
        horizons=len(membership),input_sha256={str(p):sha(p) for p in paths},fit_performed=False,operational_change=False,
        limitation='Contemporaneous source lag is applied to the historical grid by prepare_current. This audit decomposes changes; it does not certify historical publication times or prove causality of forecast error.')
    (OUT/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='input_sha256'}))
if __name__=='__main__':main()
