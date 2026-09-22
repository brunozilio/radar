"""Independent full rerun of six origins; no fitting and no delta-level inversion."""
import argparse,csv,datetime,hashlib,importlib.util,json,shutil
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
ROOT=Path('/Users/brunozilio/Documents/radar')
OUT=ROOT/'outputs/verificacao-integral-chuva-mucum-20260921'
BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
FLOW=ROOT/'outputs/experimento-niveis-reservatorios-20260921'
RAIN=ROOT/'outputs/experimento-chuva-prevista-montante-20260921'
PROXY=ROOT/'outputs/experimento-proxy-carreiro-20260921'
NEW=ROOT/'outputs/experimento-chuva-ate-mucum-20260921'
TZ=datetime.timezone(datetime.timedelta(hours=-3))
ORIGINS=['2026-07-01T00:00','2026-07-02T21:00','2026-07-22T08:00','2026-07-22T09:00','2026-07-22T11:00','2026-08-13T09:00']
def epoch(s):
 d=datetime.datetime.fromisoformat(s);return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()
def iso(t):return datetime.datetime.fromtimestamp(float(t),TZ).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def save(p,rs):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def shift(v,n):
 r=np.full(v.shape,np.nan);r[n:]=v[:-n];return r
def predict(m,x):
 med,mean,scale,beta=[np.asarray(m[k]) for k in ['median','mean','scale','beta']]
 u=np.column_stack([np.where(np.isfinite(x),x,med),~np.isfinite(x)])
 return ((u-mean)/scale)@beta+m['intercept']
def route(history,future,weights,index,h):
 # Deliberately standalone implementation; exactly-zero weights need no input.
 values=[]
 for lag,w in weights:
  if w==0:continue
  k=h-lag
  v=future[k] if k>=0 else history[index+k]
  if not np.isfinite(v):return np.nan
  values.append(w*v)
 return sum(values)
def compute():
 OUT.mkdir(parents=True,exist_ok=True)
 paths=[BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',FLOW/'additional-features.npz',
  FLOW/'frozen-models.json',RAIN/'frozen-models.json',RAIN/'forecast-rain-features.npz',
  PROXY/'modeled-carreiro-inputs.npz',PROXY/'proxy-models.json',PROXY/'protocol.json',
  PROXY/'predictions.csv',BASE/'conferencia-balanco.json',BASE/'roteamento-vazao-pesos.csv',
  ROOT/'outputs/mucum-hge-experimental-2026-09-21/parametros.json',
  ROOT/'experiments/hge-water-balance/run.py',ROOT/'experiments/hge-water-balance/vendor/hydrological_model.py',
  PROXY/'code/hydro_reservoir_mucum_experiment.py']
 weatherpaths=[ROOT/'outputs/mucum-propagacao-2026-09-21/raw'/('chuva-previsao-historica-'+m+'.json') for m in ['gfs_seamless','ecmwf_ifs025']]+[BASE/'nwp-historical-icon.json']
 paths+=weatherpaths
 initial={str(p):sha(p) for p in paths}
 # Match preserved provenance wherever these experiment manifests cover an input.
 checks=[]
 for folder in [PROXY,RAIN]:
  metadata=json.loads((folder/'experiment.json').read_text())['input_sha256']
  for p in paths:
   if str(p) in metadata:
    assert initial[str(p)]==metadata[str(p)],str(p)
    checks.append({'experiment':str(folder),'input':str(p),'sha256':initial[str(p)]})
 code=OUT/'code';(code/'vendor').mkdir(parents=True,exist_ok=True)
 for p in paths[13:16]:
  dest=code/'vendor'/p.name if p.name=='hydrological_model.py' else code/p.name
  shutil.copyfile(p,dest)
 spec=importlib.util.spec_from_file_location('independent_hge',code/'run.py');hge=importlib.util.module_from_spec(spec);spec.loader.exec_module(hge)
 d=dict(np.load(paths[0]));z=dict(np.load(paths[1]));extras=dict(np.load(paths[2]));rf=dict(np.load(paths[5]));proxy=dict(np.load(paths[6]))
 t=d['times']
 for obj in [extras,rf,proxy]:np.testing.assert_array_equal(t,obj['times'])
 ids=np.array([np.searchsorted(t,epoch(o)) for o in ORIGINS]);np.testing.assert_array_equal(t[ids],[epoch(o) for o in ORIGINS])
 ix=np.searchsorted(z['times'],t);np.testing.assert_array_equal(z['times'][ix],t)
 cols=[]
 for key in ['julho:Q','julho:I','monte:Q','monte:I','castro:Q','castro:I','86500000:Q']:
  a=z[key][ix]/1000;cols.extend([a,a-shift(a,1),(a-shift(a,3))/3,(a-shift(a,6))/6])
 for g in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
  for w in [3,6,12,24,48]:cols.append(z[g+':P'+str(w)][ix]/100)
 F=np.column_stack(cols);F77=np.column_stack([F,extras['levels_and_slopes']]);F97=np.column_stack([F77,rf['values']])
 assert F.shape[1]==53 and F77.shape[1]==77 and F97.shape[1]==97
 models=json.loads(paths[4].read_text());old=json.loads(paths[3].read_text())
 knownj=z['julho:Q'][ix[ids]]/1000;knownc=z['86500000:Q'][ix[ids]]/1000
 fj={}
 for fam,feat in [('level_and_slopes',F77),('levels_forecast_rain',F97)]:
  fj[fam]=np.column_stack([np.maximum(knownj+predict(models[f'julho:{k}:test:{fam}'],feat[ids]),0)*1000 for k in range(12)])
  if fam=='level_and_slopes':
   for k in range(12):assert models[f'julho:{k}:test:{fam}']==old[f'julho:{k}:test:{fam}']
 fc=np.column_stack([np.maximum(knownc+predict(old[f'carreiro:{k}:test:reference'],F[ids]),0)*1000 for k in range(12)])
 fc=np.where(np.isfinite(fc),fc,proxy['estimated_q_m3_s'][ids])
 hj=d['julho']*1000;hc=np.where(np.isfinite(d['carreiro']),d['carreiro']*1000,proxy['estimated_q_m3_s'][:,0])
 members=[]
 for p in weatherpaths:
  item=json.loads(p.read_text())[0]
  assert item['utc_offset_seconds']==-10800 and item['hourly_units']['precipitation_previous_day1']=='mm'
  lookup={epoch(x):v for x,v in zip(item['hourly']['time'],item['hourly']['precipitation_previous_day1'])}
  members.append(np.array([lookup.get(x,np.nan) for x in t],dtype=float))
 members=np.array(members);count=np.isfinite(members).sum(axis=0);assert np.all(count>0)
 mean=np.nansum(members,axis=0)/count
 rain=d['amount']+np.maximum(1-d['coverage'],0)*mean
 pars=next(v['parameters'] for v in json.loads(paths[12].read_text()) if v['pet_mm_day_hypothesis']==3)
 pars=np.array([pars[k] for k in hge.NAMES]);area=float(d['area'])
 # End at final origin minus one hour; no future observations enter state simulation.
 states,err=hge.simulate(rain[:int(ids.max())],3.,pars,area,hge.initial_state(pars));maxbalance=float(abs(err).max())
 rating=json.loads(paths[10].read_text())['rating_parameters'];a,b,c=rating
 kernels=list(csv.DictReader(paths[11].open()))
 wj=[(int(r['lag_h']),float(r['weight'])) for r in kernels if r['source']=='14 de Julho']
 wc=[(int(r['lag_h']),float(r['weight'])) for r in kernels if r['source']=='Passo Carreiro']
 assert min(lag for lag,w in wj if w)!=0
 rows=[];inputrows=[]
 for n,i in enumerate(ids):
  ai=int(np.searchsorted(z['times'],t[i]-900));assert z['times'][ai]==t[i]-900
  ah=z['raw:86510000:H'][ai];aq=z['raw:86510000:Q'][ai]
  local,e=hge.simulate(mean[i:i+13],3.,pars,area,states[i-1].copy());maxbalance=max(maxbalance,float(abs(e).max()))
  # Future arrays cannot affect these two anchor reconstructions.
  pastq=route(hj,fj['level_and_slopes'][n],wj,i,-1)+route(hc,fc[n],wc,i,-1)+states[i-1,-1]
  nowq=route(hj,fj['level_and_slopes'][n],wj,i,0)+route(hc,fc[n],wc,i,0)+local[0,-1]
  residual=aq-(.25*pastq+.75*nowq);offset=ah-(a*max(aq/1000,0)**b+c)
  for k in range(12):inputrows.append({'origin':iso(t[i]),'relative_lead_h':k,'julho77_m3_s':fj['level_and_slopes'][n,k],'julho97_m3_s':fj['levels_forecast_rain'][n,k],'carreiro_m3_s':fc[n,k]})
  for h in range(1,13):
   jr={fam:route(hj,arr[n],wj,i,h) for fam,arr in fj.items()}
   cr=route(hc,fc[n],wc,i,h);decay=residual*np.exp(-(h+.25)/6)
   total={fam:q+cr+local[h,-1]+decay for fam,q in jr.items()}
   levels={fam:float(a*(q/1000)**b+c+offset) if np.isfinite(q) and q>=0 else None for fam,q in total.items()}
   rows.append({'origin':iso(t[i]),'target_time':iso(t[i]+h*3600),'nominal_lead_h':h,'baseline_m':levels['level_and_slopes'],'candidate_m':levels['levels_forecast_rain'],'anchor_h_m':ah,'anchor_q_m3_s':aq,'anchor_offset_m':offset,'past_reconstructed_q_m3_s':pastq,'origin_reconstructed_q_m3_s':nowq,'residual_anchor_m3_s':residual,'decayed_residual_m3_s':decay,'julho77_routed_m3_s':jr['level_and_slopes'],'julho97_routed_m3_s':jr['levels_forecast_rain'],'carreiro_routed_m3_s':cr,'local_q_m3_s':local[h,-1],'baseline_total_q_m3_s':total['level_and_slopes'],'candidate_total_q_m3_s':total['levels_forecast_rain']})
 assert len(rows)==72 and maxbalance<1e-8
 for p in paths:assert sha(p)==initial[str(p)]
 save(OUT/'recomputed-levels.csv',rows);save(OUT/'recomputed-upstream.csv',inputrows)
 dump(OUT/'computation.json',{'origins':ORIGINS,'rows':72,'fit_performed':False,'method':'Full independent routing and HGE state/future simulation; no inversion of saved levels and no delta update','max_numerical_water_balance_error_mm':maxbalance,'input_sha256':initial,'prior_provenance_checks':checks,'rating':rating,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 print('Recomputed 72 rows',flush=True)
def compare():
 data=list(csv.DictReader((OUT/'recomputed-levels.csv').open()))
 old={(r['origin'],int(r['nominal_lead_h'])):r for r in csv.DictReader((PROXY/'predictions.csv').open())}
 if not (NEW/'predictions.csv').exists():
  print('WAITING_CANDIDATE_FILE',flush=True);return
 new={(r['origin'],int(r['nominal_lead_h'])):r for r in csv.DictReader((NEW/'predictions.csv').open())}
 print('Candidate columns:',list(next(iter(new.values()))),flush=True)
 # Explicit field selection is supplied after inspecting the produced artifact.
 field=ARGS.candidate_field
 if not field:raise ValueError('Candidate field must be explicitly supplied after inspecting CSV header')
 results=[]
 for r in data:
  key=r['origin'],int(r['nominal_lead_h'])
  for family,want,got in [('baseline',old[key]['julho_levels_m'],r['baseline_m']),('candidate',new[key][field],r['candidate_m'])]:
   same_missing=not want and not got
   delta=float(got)-float(want) if want and got else None
   results.append({'origin':key[0],'nominal_lead_h':key[1],'family':family,'saved_m':want,'recomputed_m':got,'difference_m':delta,'passed':same_missing or delta is not None and abs(delta)<=1e-8})
 save(OUT/'comparison.csv',results)
 summary={'tolerance_m':1e-8,'rows_per_family':72,'passed':all(r['passed'] for r in results),'families':{fam:{'max_absolute_difference_m':max(abs(r['difference_m']) for r in results if r['family']==fam and r['difference_m'] is not None),'failed':sum(not r['passed'] for r in results if r['family']==fam)} for fam in ['baseline','candidate']},'comparison_inputs_sha256':{str(p):sha(p) for p in [PROXY/'predictions.csv',NEW/'predictions.csv',OUT/'recomputed-levels.csv']},'candidate_column':field}
 dump(OUT/'verification.json',summary);print(json.dumps(summary,indent=2),flush=True)
 assert summary['passed'],'Numerical regression exceeds 1e-8m'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--compare-only',action='store_true');p.add_argument('--candidate-field');ARGS=p.parse_args()
 with threadpool_limits(limits=2):
  if not ARGS.compare_only:compute()
  compare()

