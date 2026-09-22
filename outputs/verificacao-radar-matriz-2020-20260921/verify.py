"""Read-only independent reconstruction of 2020 Radar matrix; writes this audit only."""
import csv,json,hashlib,bisect
from pathlib import Path
from datetime import datetime,timezone,timedelta
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
M=ROOT/'outputs/radar-matriz-observada-2020-20260921'; S=ROOT/'outputs/radar-insumos-observados-2020-20260921'
QI=ROOT/'outputs/auditoria-qi-radar-2020-20260921'
TZ=timezone(timedelta(hours=-3)); checks=[]; sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def ep(v):
 d=datetime.fromisoformat(v);return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()
def iso(v):return datetime.fromtimestamp(v,TZ).isoformat()
def check(name,a,b,tol=0):
 a=np.asarray(a);b=np.asarray(b);assert a.shape==b.shape,name
 np.testing.assert_allclose(a,b,atol=tol,rtol=0,equal_nan=True,err_msg=name)
 checks.append(dict(name=name,cells=a.size,max_abs=float(np.nanmax(abs(a-b))) if np.isfinite(a-b).any() else 0))
def lag(a,n):return np.r_[np.full(n,np.nan),a[:-n]] if n else a.copy()
def val(r,field):
 try:v=float(r.get(field))
 except (ValueError,TypeError):return np.nan
 if not np.isfinite(v) or v<0 or r.get('CQ_'+field) not in ('Dado aprovado',None):return np.nan
 if field=='ChuvaFinal' and v>150:return np.nan
 return v/100 if field=='NivelFinal' else v
def select(ts,v,queries,age):
 out=[];ix=[]
 for q in queries:
  j=bisect.bisect_right(ts,q)-1;ix.append(j)
  out.append(v[j] if j>=0 and q-ts[j]<=age else np.nan)
 return np.array(out),ix
for folder in (M,S,QI,ROOT/'outputs/auditoria-latencias-chuva-20260921'):
 manifest=json.loads(use(folder/'artifact-hashes.json').read_text())
 entries=manifest['files'].items() if isinstance(manifest,dict) else [(r['file'],r['sha256']) for r in manifest]
 for f,h in entries:assert sha(folder/f)==h,(folder,f)
prep=json.loads(use(M/'preparation.json').read_text())
for f,h in prep['input_sha256'].items():assert sha(ROOT/f)==h,f
D=dict(np.load(use(M/'features.npz'))); Q=dict(np.load(use(M/'quarter-hour.npz')))
times=D['times'];grid=Q['times'];assert len(times)==480 and D['features'].shape==(480,120)
check('hourly_times',times,np.arange(ep('2020-07-01'),ep('2020-07-21'),3600)); indices=np.searchsorted(grid,times)
levels={'86510000':900,'86472000':1800,'86472600':900,'86500000':1800};delayed={};raw={};cols=[];traces=[];rows_by={};ons_by={}
for code in levels:
 rows=[json.loads(s) for s in use(S/'stations'/f'ana-{code}-all-qc.jsonl').read_text().splitlines()];rows_by[code]=rows
 ts=[ep(r['DataHora']) for r in rows];v=[val(r,'NivelFinal') for r in rows];assert all(a<b for a,b in zip(ts,ts[1:]))
 raw[code],_=select(ts,v,grid,0);delayed[code],_=select(ts,v,grid-levels[code],900)
 check(code+' raw exact',raw[code],Q['raw:'+code+':H']);check(code+' delayed',delayed[code],Q[code+':H'])
 hv,ix=select(ts,v,times-levels[code],900)
 for t,x,j in zip(times,hv,ix):traces.append(dict(station=code,origin=iso(t),query=iso(t-levels[code]),source_time=iso(ts[j]) if j>=0 else '',value_m=x,usable=np.isfinite(x)))
 cols.append(delayed[code][indices])
 for hours in (.5,1,2,4,8):cols.append(((delayed[code]-lag(delayed[code],int(hours*4)))/hours)[indices])
check('base',D['base'],delayed['86510000'][indices]);check('truth exact',D['truth'],raw['86510000'][indices])
stored={(r['station'],r['origin']):r for r in csv.DictReader(use(M/'level-source-trace.csv').open())}
for t in traces:
 r=stored[t['station'],t['origin']]
 assert r['query']==t['query'] and r['source_time']==t['source_time'] and (r['usable']=='True')==t['usable']
 if t['usable']:assert float(r['value_m'])==t['value_m']
ons=[];ref=json.loads(use(QI/'ons-references.json').read_text())
for r in ref:
 p=use(ROOT/r['literal_csv']);assert sha(p)==r['csv_sha256'];assert sha(ROOT/r['raw_source_path'])==r['raw_source_sha256']
 ons.extend(v for v in csv.DictReader(p.open()) if v['din_instante'].startswith(r['month']))
onsmeta=[]
for plant,code in [('julho','JIUHQJ'),('monte','JIUHMC'),('castro','JIUHCA')]:
 rs=sorted((r for r in ons if r['id_reservatorio'].strip()==code),key=lambda r:r['din_instante']);ts=[ep(r['din_instante']) for r in rs];ons_by[code]=(ts,rs);assert len(ts)==len(set(ts))
 for field,key in [('val_vazaodefluente','Q'),('val_vazaoafluente','I')]:
  v=[float(r[field]) if r[field] else np.nan for r in rs]
  rv,_=select(ts,v,grid,5400);dv,_=select(ts,v,grid-3600,5400);check(plant+key+' raw',rv,Q['raw:'+plant+':'+key]);check(plant+key+' delayed',dv,Q[plant+':'+key]);delayed[plant+key]=dv
  picked,ix=select(ts,v,times-3600,5400)
  onsmeta.append(dict(plant=plant,field=key,finite_hourly=int(np.isfinite(picked).sum()),literal_2359_selected=sum(j>=0 and rs[j]['din_instante'][11:16]=='23:59' and times[k]-3600-ts[j]<=5400 for k,j in enumerate(ix))))
 q=delayed[plant+'Q']/1000;power=np.maximum(q,0)**.6;cols.extend([power[indices],q[indices],delayed[plant+'I'][indices]/1000])
 for h in (1,2,4,8):cols.append(((power-lag(power,h*4))/h)[indices])
check('all45 level and ONS fields',np.column_stack(cols),D['features'][:,:45])
weights=json.loads(use(ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json').read_text());lags=json.loads(use(ROOT/'outputs/auditoria-latencias-chuva-20260921/latencies.json').read_text())['stations'];requests=[(w,0) for w in (1,3,6,12,24,48)]+[(3,h) for h in (3,6,12)];rain={};rainmeta=[]
for s in lags:
 code=s['station'];delay=s['shift_steps_15min']*900;assert int(s['delay_seconds']/900)==s['shift_steps_15min']
 rs=[json.loads(line) for line in use(S/'stations'/f'ana-{code}-all-qc.jsonl').read_text().splitlines()]
 end=np.array([ep(r['DataHora']) for r in rs]);dt=np.r_[0,np.diff(end)] if len(end) else np.array([]);v=np.array([val(r,'ChuvaFinal') for r in rs]);good=np.isfinite(v)&(dt>0)&(dt<=5400);right=end[good];duration=dt[good];left=right-duration;rv=v[good]
 rainmeta.append(dict(station=code,rows=len(rs),valid_intervals=int(good.sum()),effective_delay_seconds=delay))
 for w,l in requests:
  queries=times-delay-l*3600;amount=[];cover=[]
  for k in range(0,len(queries),128):
   query=queries[k:k+128,None];overlap=np.maximum(0,right[None,:]-np.maximum(left[None,:],query-w*3600));overlap*=right[None,:]<=query
   amount.extend((overlap/duration[None,:]*rv[None,:]).sum(1));cover.extend(overlap.sum(1)/(w*3600))
  rain[code,w,l]=np.array(amount),np.clip(cover,0,1)
raincols=[]
for g in weights:
 group={}
 for w,l in requests:
  p=sum(weight*rain[c,w,l][0] for c,weight in g['weights'].items());cov=sum(weight*rain[c,w,l][1] for c,weight in g['weights'].items());group[w,l]=np.where(cov>=.5,p,np.nan),cov
 for w in (1,3,6,12,24,48):raincols.extend(group[w,0])
 for l in (3,6,12):raincols.append(group[3,l][0])
check('36000 rain cells independently integrated',np.column_stack(raincols),D['features'][:,45:120],2e-10)
check('all120 columns',np.column_stack(cols+raincols),D['features'],2e-10)
assert np.isnan(D['features']).sum()==13634 and np.isfinite(D['base']).sum()==453 and np.isfinite(D['truth']).sum()==454 and not D['complete24'].any()
targetrows=list(csv.DictReader(use(M/'target-coverage.csv').open()));targetstats=[]
for h in range(1,13):
 y=np.r_[D['truth'][h:],np.full(h,np.nan)];valid=np.isfinite(y)&np.isfinite(D['base']);record=targetrows[h-1];assert int(record['valid_pairs'])==valid.sum();assert int(record['finite_target'])==np.isfinite(y).sum()
 for i in np.where(np.isfinite(y))[0]:assert times[i]+h*3600==times[i+h]
 targetstats.append(dict(horizon_h=h,valid_pairs=int(valid.sum()),finite_targets=int(np.isfinite(y).sum())))
 if h==12:current={iso(t) for t in times[valid]}
# Independently verify every pre-existing Q/I trace; source is literal CSV, flags do not enter values.
stored_qi=list(csv.DictReader(use(QI/'lag-source-trace.csv').open()));assert len(stored_qi)==8640
trace_index={};qidiag=[]
for r in stored_qi:
 origin=ep(r['origin']);back=int(r['back_hours']);query=origin-3600*(back+1);assert ep(r['query_naive'])==query
 ts,rs=ons_by[r['plant']];j=bisect.bisect_right(ts,query)-1;src=rs[j] if j>=0 else None
 field='val_vazaodefluente' if r['variable']=='Q' else 'val_vazaoafluente';v=float(src[field]) if src and src[field] else np.nan;usable=j>=0 and query-ts[j]<=5400 and np.isfinite(v)
 assert r['usable']==str(bool(usable));assert ep(r['source_time_naive'])==ts[j];assert float(r['age_seconds'])==query-ts[j]
 if usable:assert float(r['value_m3s'])==v
 trace_index[r['origin'],r['plant'],r['variable'],back]=v if usable else np.nan
 components=[float(src[f]) if src[f] else np.nan for f in ['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']]
 contradiction=bool(usable and r['variable']=='Q' and v==0 and np.isfinite(components).all() and sum(components)>1)
 assert (r['Q_zero_positive_components']=='True')==contradiction
 if v==0 and usable:qidiag.append(dict(origin=r['origin'],plant=r['plant'],variable=r['variable'],back_hours=back,source_time=r['source_time_naive'],value=0,contradictory_components=contradiction))
tracecols=[]
for code in ['JIUHQJ','JIUHMC','JIUHCA']:
 currentq=np.array([trace_index[iso(t),code,'Q',0] for t in times])/1000;currenti=np.array([trace_index[iso(t),code,'I',0] for t in times])/1000;power=np.maximum(currentq,0)**.6;tracecols.extend([power,currentq,currenti])
 for h in [1,2,4,8]:oldq=np.array([trace_index[iso(t),code,'Q',h] for t in times])/1000;tracecols.append((power-np.maximum(oldq,0)**.6)/h)
check('8640 QI traces mapped to10080 matrix cells',np.column_stack(tracecols),D['features'][:,24:45])
assert sha(M/'qi-diagnostics.json')==sha(use(QI/'audit.json'));assert sha(M/'qi-origin-diagnostics.csv')==sha(use(QI/'origin-diagnostics.csv'))
# Separate missing contemporaneous truth from delayed base. No gap filling on either.
mucum=rows_by['86510000'];bytime={ep(r['DataHora']):r for r in mucum};base_details=[];missing_details=[]
for i,t in enumerate(times):
 query=t-900;ordered=sorted(bytime);j=bisect.bisect_right(ordered,query)-1;stamp=ordered[j] if j>=0 else None;br=bytime.get(stamp,{});yr=bytime.get(t,{})
 bv=val(br,'NivelFinal') if stamp is not None and query-stamp<=900 else np.nan;yv=val(yr,'NivelFinal');assert (np.isnan(bv) and np.isnan(D['base'][i])) or bv==D['base'][i];assert (np.isnan(yv) and np.isnan(D['truth'][i])) or yv==D['truth'][i]
 detail=dict(origin=iso(t),base_query=iso(query),base_source=iso(stamp) if stamp else None,base_age_after_query_seconds=query-stamp if stamp else None,base_raw_cm=br.get('NivelFinal'),base_qc=br.get('CQ_NivelFinal'),base_finite=bool(np.isfinite(bv)),truth_source=iso(t) if yr else None,truth_raw_cm=yr.get('NivelFinal'),truth_qc=yr.get('CQ_NivelFinal'),truth_finite=bool(np.isfinite(yv)),base_source_file=br.get('source_file'),base_record_index=br.get('source_record_index'),truth_source_file=yr.get('source_file'),truth_record_index=yr.get('source_record_index'));base_details.append(detail)
 if not detail['base_finite'] or not detail['truth_finite']:missing_details.append(detail)
from collections import Counter
bstats=dict(origins=480,base_missing=int((~np.isfinite(D['base'])).sum()),truth_current_missing=int((~np.isfinite(D['truth'])).sum()),both_missing=int((~np.isfinite(D['base'])&~np.isfinite(D['truth'])).sum()),base_finite_truth_missing=int((np.isfinite(D['base'])&~np.isfinite(D['truth'])).sum()),base_missing_truth_finite=int((~np.isfinite(D['base'])&np.isfinite(D['truth'])).sum()),base_source_exact_query=sum(r['base_age_after_query_seconds']==0 for r in base_details),base_source_carried_after_query=sum(r['base_age_after_query_seconds']>0 for r in base_details if r['base_age_after_query_seconds'] is not None),base_missing_qc=dict(Counter(str(r['base_qc']) for r in base_details if not r['base_finite'])),truth_missing_qc=dict(Counter(str(r['truth_qc']) for r in base_details if not r['truth_finite'])))
for h in range(1,13):
 y=np.r_[D['truth'][h:],np.full(h,np.nan)];valid=np.isfinite(D['base'])&np.isfinite(y);expected=targetrows[h-1];delta=y-D['base'];assert int(expected['high_targets'])==((y>=7)&valid).sum();assert float(expected['minimum_response_m'])==delta[valid].min();assert float(expected['maximum_response_m'])==delta[valid].max()
 record=targetstats[h-1];record.update(target_missing_within_grid=int((~np.isfinite(y[:-h])).sum()),target_beyond_window=h,base_missing_target_finite=int((~np.isfinite(D['base'])&np.isfinite(y)).sum()),base_finite_target_missing=int((np.isfinite(D['base'])&~np.isfinite(y)).sum()),maximum_response_m=float(delta[valid].max()))
for name,records in [('base-truth-source-audit.csv',base_details),('base-truth-missing.csv',missing_details),('zero-qi-traces.csv',qidiag),('target-coverage.csv',targetstats)]:
 with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
report=dict(passed=True,checks=checks,shape=[480,120],nan_cells=13634,finite_base=453,finite_truth=454,level_trace_rows=len(traces),ons=onsmeta,rain_stations=rainmeta,target_coverage=targetstats,base_vs_truth=bstats,qi_trace_count=len(stored_qi),zero_qi_trace_count=len(qidiag),origins_with_zero_qi=len({r['origin'] for r in qidiag}),origins_with_contradictory_components=len({r['origin'] for r in qidiag if r['contradictory_components']}),qi_flags_did_not_modify_values=True,limits=['All-QC normalization previously compared fieldwise against raw XML; this audit verifies hashes and reconstructs source selection/integration.','Monthly ONS normalized source CSVs used verbatim and raw hashes verified; JulyParquet not independently redecoded here.','Presumed2026availability lags applied to2020; not certified issue/receipt logs, timezone, gauge datum or plant regime.','No training, new queries, interpolation, rounding, promotion or changes to2021/22.'],source_sha256=sources)
(OUT/'verification.json').write_text(json.dumps(report,indent=2,default=lambda v:v.item())+'\n')
lines=['# Verificação independente: matriz observada Radar2020','',
'As57.600 células(480×120) foram reconstruídas independentemente:11.520níveis,10.080Q/I e36.000chuva. Níveis eQ/I coincidem exatamente; chuva por sobreposição de intervalos completos coincide até2e-10mm, com máscarasNaN idênticas. Nenhum helper de features, chuva ou seleção operacional foi executado.','',
f"Diferença máxima chuva: {checks[-3]['max_abs']:.3g}mm. As13.634células ausentes,453bases e454níveis contemporâneos conferem, assim como os1.920rastrosANA. Hashes dos manifestos e insumos conferem.",'',
'## Base atrasada versus alvo exato','',
f"Das480origens, {bstats['base_missing']} têm base indisponível e{bstats['truth_current_missing']} têm nível contemporâneo indisponível;{bstats['both_missing']} coincidem. Há{bstats['base_finite_truth_missing']}origens com base finita/H(O)ausente e{bstats['base_missing_truth_finite']}com base ausente/H(O)finito. Isso reflete timestamps distintos: a base consultaO−15min e o alvo contemporâneo exigeO exato.",
f"Em todas{bstats['base_source_exact_query']}origens existe linha exatamente na consultaO−15min; nenhuma base usa carry-forward adicional após consulta. Base ausente porQC:{bstats['base_missing_qc']}; H(O)ausente porQC:{bstats['truth_missing_qc']}. Linha mais antiga aprovada não substitui a mais nova rejeitada/vazia. source/índice/valores estão nosCSVs.",'',
'Os pares h1/h6/h12 são447/437/426. Alvos são deslocados dentro deste bloco, sem cruzar anos ou prolongar além20/07; os últimos h alvos ficam indisponíveis. O máximo de resposta h12 é11,53m, sem inserir marca retrospectiva do pico.','',
'## Q/I literal e diagnósticos','',
'Todas8.640consultas Q/I foram conferidas por busca independente noCSVliteral: atraso60min, idade≤90min após consulta,23:59mantido. Reconstituem exatamente os21campos da matriz, incluindo transformações e diferenças1/2/4/8h. Nenhum flag participa do valor; JSON/CSV de diagnósticos são cópias exatas da auditoria anterior.',
f"{report['origins_with_zero_qi']}origens usam algum zero e{report['origins_with_contradictory_components']}usamQzero com componentes positivos. Estes zeros persistem nos campos correspondentes, sem substituição porNaN, componentes ou estimativas. Sinalização aritmética não é certificação oficial de erro.",'',
'## Chuva e limites','',
'Os27postos foram reconstruídos diretamente das sériesALL-QC com intervalo finalizado, duração≤90min, QC/limites congelados, atrasos truncados em15min e pesos fixos. Não houve renormalização regional, chuva futura observada ou interpretação de ausência como mediçãozero; cobertura mínima0,5 regula os acumulados. Faltas/coberturas concordam nos75campos.','',
'O acervoANA foi conferido campo por campo comXML na etapa anterior; aqui conferimoshashes, seleção, integração e rastros. JulhoONS parte doCSVnormalizado já auditado ehashParquet; não foi redecodificado. Esta igualdade numérica não certifica disponibilidade histórica, fuso, datum ou regime físico. Nenhum treino, rede, operação ou acesso aos anos2021/2022.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n');(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
print(json.dumps(dict(passed=True,checks=len(checks),base_vs_truth=bstats,qi_trace_count=8640,origins_with_zero_qi=report['origins_with_zero_qi'],origins_with_contradictory_components=report['origins_with_contradictory_components'],target_coverage=targetstats),indent=2,default=lambda v:v.item()))
