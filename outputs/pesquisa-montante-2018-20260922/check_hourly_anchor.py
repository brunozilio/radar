"""Independent raw-XML check; does not import the coordinator's builder."""
from pathlib import Path
from collections import defaultdict
import csv,json,math,hashlib,datetime as dt,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent;W=R.parents[1];D=W/'outputs/diagnostico-ancora-horaria-2018-20260922';S=W/'outputs/pesquisa-janelas-ineditas-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvread(name):return list(csv.DictReader((D/name).open()))
def iso(t):return t.isoformat()
checks=[]
def ck(name,v):checks.append({'check':name,'passed':bool(v)})
def same(v,expected):return v=='' if expected is None else (v==str(expected) if isinstance(expected,(str,bool)) else abs(float(v)-expected)<1e-12)
series={}
for p in sorted((S/'raw').glob('ana-*.xml')):
 data={}
 for e in ET.fromstring(p.read_bytes()).iter('DadosHidrometereologicos'):
  x={c.tag:c.text or '' for c in e};t=dt.datetime.fromisoformat(x['DataHora']);v=float(x['NivelFinal'])
  data[t]=v/100 if math.isfinite(v) and v>=0 and x['CQ_NivelFinal']=='Dado aprovado' else None
 series[min(data).date().isoformat()]=data
frows=csvread('features.csv');traces=csvread('lookup-traces.csv');targets=csvread('targets.csv');metrics=csvread('coverage.csv')
featuremap={};targetmap=defaultdict(list)
for r in frows:
 d=series[r['window']];o=dt.datetime.fromisoformat(r['origin_literal']);a=o-dt.timedelta(hours=1);base=d.get(a)
 ck('base '+r['origin_literal'],r['anchor_literal']==iso(a) and same(r['level_m'],base))
 slopes={lag:None if base is None or d.get(a-dt.timedelta(hours=lag)) is None else (base-d[a-dt.timedelta(hours=lag)])/lag for lag in [.5,1,2,4,8]}
 ck('slopes '+r['origin_literal'],all(same(r[f'dH{lag}_m_per_h'],v) for lag,v in slopes.items()))
 q=o-dt.timedelta(minutes=15);old=max((t for t in d if t<=q),default=None);age=(q-old).total_seconds()/60 if old else None
 ck('current expiry '+r['origin_literal'],r['current_contract_last_literal']==(iso(old) if old else '') and same(r['current_contract_age_minutes'],age) and r['current_contract_base_m']=='' and (age is None or age==45))
 featuremap[(r['window'],o)]=(base,slopes)
for r in traces:
 o=dt.datetime.fromisoformat(r['origin_literal']);a=o-dt.timedelta(hours=1);lag=float(r['lag_h']);p=a-dt.timedelta(hours=lag);d=series[r['window']];base,slopes=featuremap[(r['window'],o)]
 ck('lookup '+r['origin_literal']+' '+str(lag),p<a<o and r['anchor_literal']==iso(a) and r['past_literal']==iso(p) and same(r['anchor_m'],base) and same(r['past_m'],d.get(p)) and same(r['value_m_per_h'],slopes[lag]))
seen=set()
for r in targets:
 o=dt.datetime.fromisoformat(r['origin_literal']);h=int(r['horizon_h']);t=o+dt.timedelta(hours=h);d=series[r['window']];base,slopes=featuremap[(r['window'],o)];truth=d.get(t);complete=base is not None and all(slopes[k] is not None for k in [1,2,4,8])
 key=(r['window'],o,h);ck('target '+str(key),key not in seen and t in d and r['target_literal']==iso(t) and same(r['actual_m'],truth) and same(r['base_m'],base) and same(r['complete_hourly_features'],complete) and r['current_contract_base_m']=='');seen.add(key)
 targetmap[(r['window'],h)].append((base,truth,complete))
expectedkeys={(win,o,h) for win,d in series.items() for o in d for h in range(1,13) if o+dt.timedelta(hours=h) in d}
ck('all keys no temporal bridge',seen==expectedkeys)
six=[]
for r in metrics:
 win=r['window'];h=int(r['horizon_h']);pop=targetmap[(win,h)];observed=[(b,t,c) for b,t,c in pop if t is not None and (r['subset']=='all' or t>=7)];pairs=[(b,t,c) for b,t,c in observed if b is not None]
 exp={'scheduled_rows':168-h,'boundary_exclusions':h,'missing_truth':sum(t is None for b,t,c in pop),'observed_targets':len(observed),'anchor_target_pairs':len(pairs),'missing_anchor_on_observed_target':len(observed)-len(pairs),'complete_hourly_pairs':sum(c for b,t,c in pairs),'complete_six_field_pairs':0,'current_contract_pairs':0}
 ck('coverage '+win+' '+str(h)+' '+r['subset'],all(int(r[k])==v for k,v in exp.items()))
 if h in [1,6,12] and r['subset']=='all':six.append({'window':win,'horizon_h':h,**exp})
m=json.loads((D/'manifest.json').read_text());hashes={}
for item in m['files']:
 p=D/item['file'];ck('artifact hash '+item['file'],sha(p)==item['sha256']);hashes[str(p.relative_to(W))]=sha(p)
for name,digest in m['source_sha256'].items():ck('input hash '+name,sha(W/name)==digest);hashes[name]=sha(W/name)
ck('sizes',len(frows)==336 and len(traces)==1680 and len(targets)==3876 and len(metrics)==48)
out={'passed':all(c['passed'] for c in checks),'check_count':len(checks),'origins':len(frows),'traces':len(traces),'scheduled_targets':len(targets),'coverage_groups':len(metrics),'all_boundary_exclusions':2*sum(range(1,13)),'six_all_groups':six,'checks':checks,'sha256':hashes,'limits':['Structural coverage only, no fit or inference','Exact O-1h is a declared measurement-lag assumption, not certified publication latency','dH0.5 absent throughout; six local fields do not establish full Radar admissibility','Nonapproved target rows remain missing; no cross-window shift','Current operational contract is unchanged']}
(R/'hourly-anchor-independent-check.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:out[k] for k in ['passed','check_count','six_all_groups']},indent=2))
if not out['passed']:raise SystemExit(1)
