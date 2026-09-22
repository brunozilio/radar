"""Independent local audit: no model/operational helper imports, no fit, no network."""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'outputs/diagnostico-variacao-treino-horario-20260922'
A=R/'outputs/mucum-hourly-20260922T000704-0300';B=R/'outputs/mucum-hourly-20260922T010016-0300'
S=[R/'outputs/auditoria-suporte-radar-live-00h-20260922-v2',R/'outputs/auditoria-suporte-radar-live-01h-20260922']
cut=datetime.fromisoformat('2026-09-21T00:00:00-03:00').timestamp();checks=[];inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def track(p):inputs[str(p.relative_to(R))]=sha(p);return p
def load(p):return dict(np.load(track(p)))
def js(p):return json.loads(track(p).read_text())
def csvrows(p):return list(csv.DictReader(track(p).open()))
def check(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
def same(a,b):return a.shape==b.shape and np.array_equal(a,b,equal_nan=True)
def changes(a,b):return int(np.sum(~((a==b)|(np.isnan(a)&np.isnan(b)))))
def dump(name,x):(P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def save(name,x):
 with (P/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(x[0]));w.writeheader();w.writerows(x)
def asof(t,v,q,expiry):
 ix=np.searchsorted(t,q,side='right')-1;good=ix>=0;safe=np.maximum(ix,0);good&=(q-t[safe]<=expiry);out=np.full(len(q),np.nan);out[good]=v[ix[good]];return out
root=js(D/'comparison.json')
for path,h in root['input_sha256'].items():check('root input hash:'+path,sha(track(Path(path)))==h)
for x in js(D/'artifact-hashes.json'):check('root artifact:'+x['file'],sha(track(D/x['file']))==x['sha256'])
q=[load(p/'telemetria-latencia.npz') for p in (A,B)];f=[load(p/'radar-features.npz') for p in (A,B)]
for x in q:check('quarter grid900',np.all(np.diff(x['times'])==900))
for x in f:check('hour grid3600',np.all(np.diff(x['times'])==3600))
qi=[x['times']<cut for x in q];fi=[x['times']<cut for x in f]
check('same quarter historical timestamps',same(q[0]['times'][qi[0]],q[1]['times'][qi[1]]));check('same hourly historical timestamps',same(f[0]['times'][fi[0]],f[1]['times'][fi[1]]))
history=[]
for pa in sorted((A/'history').glob('*.npz')):
 aa=load(pa);bb=load(B/'history'/pa.name);ia=aa['times']<cut;ib=bb['times']<cut;check(pa.name+' history timeline',same(aa['times'][ia],bb['times'][ib]))
 for k in aa:
  if k!='times':history.append({'source':pa.name,'field':k,'rows':int(ia.sum()),'changed':changes(aa[k][ia],bb[k][ib])})
check('114 unchanged normalized history fields',len(history)==114 and sum(x['changed'] for x in history)==0)
raw=[{'field':k,'changed':changes(q[0][k][qi[0]],q[1][k][qi[1]])} for k in q[0] if k.startswith('raw:')]
check('raw grid fields unchanged',all(x['changed']==0 for x in raw))
fc=[{'column':j,'changed':changes(f[0]['features'][fi[0],j],f[1]['features'][fi[1],j])} for j in range(180)]
check('94columns 538204cells',sum(x['changed']>0 for x in fc)==94 and sum(x['changed'] for x in fc)==538204)
rootfc=csvrows(D/'feature-changes-before-cutoff.csv');check('all feature table counts',all(int(x['changed'])==fc[int(x['column'])]['changed'] for x in rootfc))
ages=[{x['source']:x for x in csvrows(p/'idades-fontes.csv')} for p in (A,B)];shiftresults=[]
for code,oldmin,newmin,key in [('86510000',15,30,'H'),('86472600',15,75,'H'),('castro',0,60,'Q')]:
 check(code+' ages',float(ages[0][code]['delay_minutes'])==oldmin and float(ages[1][code]['delay_minutes'])==newmin)
 steps=int((newmin-oldmin)/15);qt=q[1]['times'];sel=(qt<cut)&(qt>=q[0]['times'][0]+steps*900);oldix=np.searchsorted(q[0]['times'],qt[sel]-steps*900)
 old=q[0][code+':'+key][oldix];new=q[1][code+':'+key][sel];check(code+' direct shift exact',same(old,new))
 # Independent source lookup also checks the leading grid positions excluded from shift.
 for p,z,lag in zip((A,B),q,(oldmin,newmin)):
  h=load(p/'history'/('ana-'+code+'.npz' if key=='H' else 'ceran-'+code+'.npz'))
  valid=(h['times']<=z['times'][-1])&np.isfinite(h['level' if key=='H' else key]);latest=h['times'][valid][-1]
  check(code+p.name+' latest age',z['times'][-1]-latest==lag*60)
  mask=z['times']<cut;re=asof(h['times'],h['level' if key=='H' else key],z['times'][mask]-lag*60,900 if key=='H' else 5400)
  check(code+p.name+' full source asof exact',same(re,z[code+':'+key][mask]))
 shiftresults.append({'source':code,'field':key,'old_delay_minutes':oldmin,'new_delay_minutes':newmin,'extra_shift_quarters':steps,'direct_shift_positions':int(sel.sum()),'finite_pairs':int(np.isfinite(old).sum()),'nan_pairs':int(np.isnan(old).sum()),'changed_after_shift':changes(old,new),'leading_positions_excluded_from_shift':steps,'leading_positions_checked_by_independent_asof':True})
# Independently reconstruct original operational masks from hourly truth and complete24.
mi=[load(p/'training-indices.npz') for p in S];members=[]
for lead in range(1,15):
 tr=[]
 for k in range(2):
  x=f[k];target=np.full(len(x['times']),np.nan);target[:-lead]=x['truth'][lead:]
  valid=np.isfinite(x['base'])&np.isfinite(target)&np.isfinite(x['features'][:,:24]).all(axis=1)&(x['times']+lead*3600<cut)
  ix=np.flatnonzero(valid);check(f'mask{k}h{lead}',same(ix,mi[k][f'h{lead}']));tr.append(set(x['times'][ix]))
 a,b=tr;common=np.array(sorted(a&b));ai=np.searchsorted(f[0]['times'],common);bi=np.searchsorted(f[1]['times'],common)
 members.append({'nominal_lead_h':lead,'before':len(a),'after':len(b),'added':len(b-a),'removed':len(a-b),'common':len(common),'common_base_changed':changes(f[0]['base'][ai],f[1]['base'][bi]),'common_target_changed':changes(f[0]['truth'][ai+lead],f[1]['truth'][bi+lead])})
rootm=csvrows(D/'membership.csv');check('all14 membership table values',all(all(int(rr[k])==r[k] for k in r) for rr,r in zip(rootm,members)));check('h1membership claim',members[0]['before']==10875 and members[0]['after']==10899 and members[0]['added']==258 and members[0]['removed']==234)
save('independent-history.csv',history);save('independent-feature-changes.csv',fc);save('independent-membership.csv',members);save('direct-shift-checks.csv',shiftresults)
dump('input-hashes.json',inputs)
dump('verification.json',{'passed':all(x['passed'] for x in checks),'checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks_count':len(checks),'checks':checks,'cutoff_exclusive':datetime.fromtimestamp(cut,timezone.utc).isoformat(),'normalized_history_fields':len(history),'raw_grid_fields':len(raw),'changed_feature_columns':94,'changed_feature_cells':538204,'direct_shifts':shiftresults,'h1_membership':members[0],'historical_grid_rows_quarter':int(qi[0].sum()),'historical_grid_rows_hourly':int(fi[0].sum()),'no_fit_no_network':True,'limits':['No claim of XML/QC revisions outside retained numeric history fields or after cutoff.','Current delays reused over historical grid are a preparation assumption, not historical publication latency.','Direct shifts verify H of Muçum/Santa and Q of Castro, not a full causal decomposition of every rain/weather cell.','No inference or attribution of forecast error; fixed training cutoff does not freeze input matrix, membership, weights or models.','98percent accuracy goal is not established by this audit.']})
print('PASS',len(checks),'checks',shiftresults)
