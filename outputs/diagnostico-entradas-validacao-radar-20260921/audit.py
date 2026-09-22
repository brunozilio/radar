"""Descriptive input/membership/weight audit; no models loaded, fitted or inferred."""
import csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];E=ROOT/'outputs/experimento-radar-historico-2023-20260921';sources={};TZ=timezone(timedelta(hours=-3))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def ep(s):return datetime.fromisoformat(s).timestamp()
def iso(t):return datetime.fromtimestamp(t,TZ).isoformat()
def save(name,rs):
 with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def future(a,h):return np.r_[a[h:],np.full(h,np.nan)]
def stat(a):
 v=a[np.isfinite(a)];return dict(n=len(a),finite=len(v),missing=int((~np.isfinite(a)).sum()),minimum=float(v.min()) if len(v) else None,median=float(np.median(v)) if len(v) else None,p90=float(np.quantile(v,.9)) if len(v) else None,maximum=float(v.max()) if len(v) else None)
old=dict(np.load(use(ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921/features.npz')));new=dict(np.load(use(ROOT/'outputs/radar-matriz-observada-2023-20260921/features.npz')));masks=dict(np.load(use(E/'training-masks.npz')));pred=list(csv.DictReader(use(E/'predictions.csv').open()));train=list(csv.DictReader(use(E/'training.csv').open()));meta=json.loads(use(E/'experiment.json').read_text());use(E/'protocol.json');use(E/'code/hydro_radar_2023_augmentation.py')
for path in list(sources):
 absolute=str(ROOT/path)
 if absolute in meta['input_sha256']:assert sha(ROOT/path)==meta['input_sha256'][absolute]
F=old['features'][:,:120];NF=new['features'];names=[];units=[]
for code in ['86510000','86472000','86472600','86500000']:
 names.append(code+':H');units.append('m')
 for h in [.5,1,2,4,8]:names.append(code+':dH'+str(h));units.append('m/h')
for plant in ['julho','monte','castro']:
 names.extend([plant+':Q06',plant+':Q',plant+':I']);units.extend(['(1000m3/s)^0.6','1000m3/s','1000m3/s'])
 for h in [1,2,4,8]:names.append(plant+':dQ'+str(h));units.append('(1000m3/s)^0.6/h')
for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
 for h in [1,3,6,12,24,48]:names.extend([group+':P'+str(h),group+':C'+str(h)]);units.extend(['mm','fraction'])
 for h in [3,6,12]:names.append(group+':P3lag'+str(h));units.append('mm')
assert len(names)==120
blocks=[('Muçum',0,6),('Linha José Júlio',6,12),('Santa Tereza',12,18),('Carreiro nível',18,24),('Julho Q/I',24,31),('Monte Q/I',31,38),('Castro Q/I',38,45)]+[(g,45+15*i,60+15*i) for i,g in enumerate(['Baixo Antas chuva','Carreiro chuva','Prata-Turvo chuva','Alto Antas chuva','Tainhas chuva'])]
weightrows=[];stats=[];coverage=[];validation=[];dates={};lookup={iso(t):i for i,t in enumerate(old['times'])};weightdetail=[]
for h in range(1,13):
 y=future(old['truth'],h);dy=y-old['base'];ny=future(new['truth'],h);nd=ny-new['base'];nm=masks['new_h'+str(h)];assert nm.sum()==503-2*(h-1);nw=1+2*(abs(nd[nm])>=1)+2*(ny[nm]>=9)
 for phase in ['validation','test']:
  om=masks[f'{phase}_original_h{h}'];ow=1+2*(abs(dy[om])>=1)+2*(y[om]>=9);info=next(r for r in train if r['phase']==phase and int(r['horizon_h'])==h);assert om.sum()==int(info['original_n']) and nm.sum()==int(info['added_n'])
  r=dict(phase=phase,horizon_h=h,original_n=int(om.sum()),added_n=int(nm.sum()),row_fraction_2023=float(nm.sum()/(om.sum()+nm.sum())),original_weight=int(ow.sum()),added_weight=int(nw.sum()),weight_fraction_2023=float(nw.sum()/(ow.sum()+nw.sum())),original_ge7=int((y[om]>=7).sum()),added_ge7=int((ny[nm]>=7).sum()),original_ge9=int((y[om]>=9).sum()),added_ge9=int((ny[nm]>=9).sum()),added_abs_response_ge1=int((abs(nd[nm])>=1).sum()),original_ge7_weight=int(ow[y[om]>=7].sum()),added_ge7_weight=int(nw[ny[nm]>=7].sum()))
  weightrows.append(r)
 for i,w in zip(np.where(nm)[0],nw):weightdetail.append(dict(horizon_h=h,origin=iso(new['times'][i]),target_time=iso(new['times'][i]+h*3600),base_m=float(new['base'][i]),target_m=float(ny[i]),response_m=float(nd[i]),weight=int(w)))
 rs=[r for r in pred if r['phase']=='validation' and int(r['nominal_lead_h'])==h and r['actual_m'] and float(r['actual_m'])>=7];assert len(rs)==28;vi=np.array([lookup[r['origin']] for r in rs]);dates[h]=sorted({r['target_time'] for r in rs})
 for r,i in zip(rs,vi):
  assert float(r['actual_m'])==y[i];item=dict(horizon_h=h,origin=r['origin'],target_time=r['target_time'],base_m=float(r['base_m']),target_m=float(r['actual_m']))
  for j,name in enumerate(names):item[name]=float(F[i,j]) if np.isfinite(F[i,j]) else None
  validation.append(item)
 populations={'validation_high':F[vi],'original_validation_train':F[masks[f'validation_original_h{h}']],'added2023_all':NF[nm],'added2023_high':NF[nm&(ny>=7)]}
 for label,x in populations.items():
  for j,name in enumerate(names):stats.append(dict(horizon_h=h,population=label,column=j,feature=name,unit=units[j],**stat(x[:,j])))
  for labelb,start,end in blocks:
   nan=~np.isfinite(x[:,start:end]);coverage.append(dict(horizon_h=h,population=label,block=labelb,rows=len(x),rows_any_missing=int(nan.any(1).sum()),rows_all_missing=int(nan.all(1).sum()),missing_cells=int(nan.sum()),cells=nan.size))
assert all(dates[h]==dates[1] for h in dates)
report=dict(passed=True,validation_distinct_targets=dates[1],target_count=28,horizons=12,validation_rows=336,weights_formula='1 + 2*(abs(target-base)>=1m) + 2*(target>=9m)',weights=weightrows,coverage=coverage,limits=['The same28target timestamps occur in all12h; these are not336independent flood targets.','Descriptive distribution comparison does not establish model attribution or physical cause.','2023peak is unobserved and not interpolated; added2023high means admitted labels only.','2023ANA datum/timezone/publication and pre-2024plant regime comparability uncertified.','Weights are actual per-row sample_weight sums, not influence measurements in fitted trees.','No models read, fitted or inferred; no queries or operational changes.'])
save('validation-inputs.csv',validation);save('training-weights.csv',weightrows);save('added-row-weights.csv',weightdetail);save('feature-distributions.csv',stats);save('block-coverage.csv',coverage);(OUT/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n')
print('TARGETS',dates[1]);print('WEIGHTS',json.dumps([r for r in weightrows if r['horizon_h'] in [1,6,12]],indent=2));print('COVERAGE H12',json.dumps([r for r in coverage if r['horizon_h']==12 and r['population'] in ['validation_high','added2023_all']],indent=2));print('KEY FEATURE H12',json.dumps([r for r in stats if r['horizon_h']==12 and r['population'] in ['validation_high','added2023_all'] and (r['feature'].endswith((':Q',':I',':P24',':C24',':H')))],indent=2))
# Additional descriptive range comparison, not a support/eligibility gate.
range_rows=[]
for h in [1,6,12]:
 vi=np.array([lookup[r['origin']] for r in pred if r['phase']=='validation' and int(r['nominal_lead_h'])==h and r['actual_m'] and float(r['actual_m'])>=7]);nm=masks[f'new_h{h}']
 for j in range(120):
  v=NF[nm,j];v=v[np.isfinite(v)];x=F[vi,j]
  range_rows.append(dict(horizon_h=h,column=j,feature=names[j],new_finite=len(v),validation_finite=int(np.isfinite(x).sum()),validation_below_new_min=int((x<v.min()).sum()) if len(v) else None,validation_above_new_max=int((x>v.max()).sum()) if len(v) else None))
save('validation-versus-added-range.csv',range_rows)
assert not any(r['missing_cells'] for r in coverage if r['population']=='validation_high')
h12labels=[r for r in weightdetail if r['horizon_h']==12 and r['target_m']>=7]
report['h12_added_high_targets']=[r['target_time'] for r in h12labels]
report['validation_input_all_finite']=True
report['h12_added_high_weight']=sum(r['weight'] for r in h12labels)
(OUT/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['# Diagnóstico de entradas e pesos: Radar observado com 2023','',
'Os 28 alvos ≥7 m da validação são horas consecutivas de **08/11/2025 08h até 09/11/2025 11h (UTC−3 presumido)**. Reaparecem nos 12 horizontes: 336 linhas de previsão, mas somente 28 alvos distintos. As origens conjuntas vão de 07/11 20h a 09/11 10h. Não atribuí um nome/certificação externa ao episódio.','',
'**Todas as 120 entradas estão finitas nas 336 linhas de validação de cheia.** Em contraste, todas as amostras adicionadas de 2023 têm os 12 campos de Santa Tereza e Carreiro ausentes, em todos os horizontes. Portanto, o prejuízo da validação não é explicado simplesmente por entradas ausentes nessas origens; a distribuição do conjunto adicionado é diferente. Isso não prova causa ou influência particular no modelo.','',
'No horizonte 12h, as 481 amostras novas têm ausência de algum campo em: Muçum 8; Linha José Júlio 0; Q/I de cada usina 12 (3 com os 7 campos ausentes); chuva Baixo Antas 408, Carreiro 404, Prata-Turvo 0, Alto Antas 2, Tainhas 1. Chuva P24 Baixo Antas e Carreiro é ausente em 404/481; as colunas de cobertura continuam finitas, logo chuva ausente não equivale a zero.','',
'| Campo h12 | Validação cheia: mediana / máximo | 2023 admitido: mediana / máximo |','|---|---:|---:|']
for name in ['julho:Q','julho:I','monte:Q','monte:I','castro:Q','castro:I','Baixo Antas:P24','Carreiro:P24','Prata-Turvo:P24','Alto Antas:P24','Tainhas:P24']:
 a=next(r for r in stats if r['horizon_h']==12 and r['population']=='validation_high' and r['feature']==name);b=next(r for r in stats if r['horizon_h']==12 and r['population']=='added2023_all' and r['feature']==name);factor=1000 if name.endswith((':Q',':I')) else 1;unit='m³/s' if factor==1000 else 'mm'
 lines.append(f"| {name} ({unit}) | {a['median']*factor:.2f} / {a['maximum']*factor:.2f} | {b['median']*factor:.2f} / {b['maximum']*factor:.2f} |")
lines+=['','Medianas/máximos usam apenas valores finitos, portanto chuva ausente em grande parte de 2023 torna essa comparação condicional. Os 120 campos completos, cobertura por bloco e diferenças de faixa estão nos CSVs; exceder a faixa das amostras novas não significa exceder o treino original nem um limite físico.','',
'A cobertura P24 mediana Baixo Antas/Carreiro é 0,988/0,948 na validação contra 0,329/0,051 no conjunto adicionado. Os pesos espaciais não foram renormalizados. Q/I são entradas atrasadas dos CSVs ONS; estes números não certificam equivalência de regime operacional, datum ou disponibilidade entre 2023 e 2025.','',
'## Peso efetivamente passado ao ajuste','',
'Fórmula congelada: `1 + 2*(|alvo−base|≥1 m) + 2*(alvo≥9 m)`. A fronteira de cheia descritiva (7 m) não é a mesma fronteira de peso (9 m). Não houve reponderação ad hoc nesta auditoria.','',
'| Fase | h | Linhas 2023 / total | Peso 2023 / total | Fração do peso | Alvos 2023 ≥7 / ≥9 |','|---|---:|---:|---:|---:|---:|']
for r in weightrows:
 if r['horizon_h'] in (1,6,12):lines.append(f"| {r['phase']} | {r['horizon_h']} | {r['added_n']} / {r['added_n']+r['original_n']} | {r['added_weight']} / {r['added_weight']+r['original_weight']} | {100*r['weight_fraction_2023']:.3f}% | {r['added_ge7']} / {r['added_ge9']} |")
lines+=['',
'Em h12, dos 663 pontos de peso adicionados, 101 vêm de 45 alvos ≥7 m; apenas cinco alvos são ≥9 m. O restante não representa o pico ausente de setembro de 2023. Cada linha/peso admitido está listado em added-row-weights.csv; não foi preenchido o pico. Soma de pesos mede a contribuição nominal à função de ajuste, não a influência causal de exemplos ou variáveis nas árvores.','',
'## Escopo e integridade','',
'Leitura local das duas matrizes congeladas, máscaras, treino e previsões; nenhum modelo foi carregado ou executado. Foram conferidos hashes publicados dos insumos disponíveis em experiment.json e membership contra training.csv. Ausências preservadas, sem coleta, alteração operacional, treino, HGE ou promoção. Datums, fuso/publicação históricos e regimes físicos permanecem não certificados. Script e manifestos permitem reprodução; fonte de entradas é a matriz congelada, não uma nova auditoria de sensores/XML.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n')
(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ['artifact-hashes.json','console.txt']],indent=2)+'\n')
