"""Audit ablation indices and source-feature availability under frozen masks."""
import ast,csv,hashlib,json
from pathlib import Path
from datetime import datetime
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def save(name,rows):
 with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def shifted(a,h):return np.r_[a[h:],np.full(h,np.nan)]
O=dict(np.load(use(ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921/features.npz')));N=dict(np.load(use(ROOT/'outputs/radar-matriz-observada-2023-20260921/features.npz')));M=dict(np.load(use(ROOT/'outputs/experimento-radar-core33-20260921/training-masks.npz')));prev=dict(np.load(use(ROOT/'outputs/experimento-radar-historico-2023-20260921/training-masks.npz')));pred=list(csv.DictReader(use(ROOT/'outputs/experimento-radar-core33-20260921/predictions.csv').open()));F=O['features'][:,:120];NF=N['features'];assert all(np.array_equal(v,prev[k]) for k,v in M.items())
# Static source inspection plus independent list construction, no execution/import.
asts=[]
for p in [ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921/code/hydro_latency_forecast.py',ROOT/'outputs/radar-matriz-observada-2023-20260921/code/hydro_latency_forecast.py']:
 tree=ast.parse(use(p).read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='telemetry_features');asts.append(ast.dump(node,include_attributes=False))
assert asts[0]==asts[1]
names=[]
for code in ['86510000','86472000','86472600','86500000']:
 names.append(code+':H');names.extend(code+f':dH{h}' for h in [.5,1,2,4,8])
for plant in ['julho','monte','castro']:names.extend([plant+':Q06',plant+':Q',plant+':I']+[plant+f':dQ06{h}' for h in [1,2,4,8]])
regions=['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas'];P=[];C=[]
for region in regions:
 for h in [1,3,6,12,24,48]:P.append(len(names));names.append(region+':P'+str(h));C.append(len(names));names.append(region+':C'+str(h))
 for lag in [3,6,12]:P.append(len(names));names.append(region+':P3lag'+str(lag))
assert len(names)==120 and len(P)==45 and len(C)==30
A=np.arange(12,24);R=np.arange(45,120);idx45=np.arange(45);idx108=np.r_[np.arange(12),np.arange(24,120)];core33=np.r_[np.arange(12),np.arange(24,45)]
assert np.array_equal(np.setdiff1d(np.arange(120),idx45),R);assert np.array_equal(np.setdiff1d(np.arange(120),idx108),A);assert np.array_equal(np.intersect1d(idx45,idx108),core33);assert np.array_equal(np.union1d(idx45,idx108),np.arange(120));assert np.isnan(NF[:,A]).all()
columns=[dict(original_index=j,feature=names[j],in_45=j in idx45,in_108=j in idx108,in_core33=j in core33,block='auxiliary_levels' if j in A else 'rain_amount' if j in P else 'rain_coverage' if j in C else 'retained_core') for j in range(120)]
blocks={'auxiliary12':A,'SantaTereza6':np.arange(12,18),'Carreiro6':np.arange(18,24),'rain75':R,'rain_amount45':np.array(P),'rain_coverage30':np.array(C),'retained45':idx45,'retained108':idx108}
rows=[];byregion=[];cooccur=[]
def examine(phase,h,population,x):
 for name,idx in blocks.items():
  z=x[:,idx];finite=np.isfinite(z);rec=dict(phase=phase,horizon_h=h,population=population,block=name,rows=len(x),columns=len(idx),cells=z.size,finite_cells=int(finite.sum()),missing_cells=int((~finite).sum()),rows_complete=int(finite.all(1).sum()),rows_any_missing=int((~finite).any(1).sum()),rows_all_missing=int((~finite).all(1).sum()),zero_finite_cells=int(((z==0)&finite).sum()))
  rows.append(rec)
 for k,region in enumerate(regions):
  pis=[j for j in P if 45+15*k<=j<60+15*k];cis=[j for j in C if 45+15*k<=j<60+15*k];z=x[:,pis];c=x[:,cis];v=c[np.isfinite(c)]
  byregion.append(dict(phase=phase,horizon_h=h,population=population,region=region,rows=len(x),amount_cells=z.size,amount_missing=int((~np.isfinite(z)).sum()),amount_finite_zero=int((z==0).sum()),rows_amount_all_missing=int((~np.isfinite(z)).all(1).sum()),coverage_cells=c.size,coverage_missing=int((~np.isfinite(c)).sum()),coverage_below_half=int((c<.5).sum()),coverage_min=float(v.min()) if len(v) else None,coverage_median=float(np.median(v)) if len(v) else None,coverage_max=float(v.max()) if len(v) else None))
 am=(~np.isfinite(x[:,A])).any(1);rm=(~np.isfinite(x[:,P])).any(1)
 cooccur.append(dict(phase=phase,horizon_h=h,population=population,rows=len(x),both_aux_and_rain_amount_complete=int((~am&~rm).sum()),aux_missing_only=int((am&~rm).sum()),rain_amount_missing_only=int((~am&rm).sum()),both_missing=int((am&rm).sum())))
index={t:i for i,t in enumerate(O['times'])};evalrows=[]
for phase in ['validation','test']:
 for h in range(1,13):
  om=M[f'{phase}_original_h{h}'];nm=M[f'new_h{h}'];assert len(om)==len(F) and len(nm)==len(NF)
  examine(phase,h,'original_training',F[om]);examine(phase,h,'added2023_training',NF[nm]);examine(phase,h,'combined_training',np.vstack([NF[nm],F[om]]))
  records=[r for r in pred if r['phase']==phase and int(r['nominal_lead_h'])==h and r['actual_m'] and float(r['actual_m'])>=7];assert len(records)==(28 if phase=='validation' else 237);ii=[index[datetime.fromisoformat(r['origin']).timestamp()] for r in records];examine(phase,h,'evaluation_high_full_schedule',F[ii])
  for r,i in zip(records,ii):evalrows.append(dict(phase=phase,horizon_h=h,origin=r['origin'],target_time=r['target_time'],actual_m=r['actual_m'],base_m=r['base_m'],aux_missing=int((~np.isfinite(F[i,A])).sum()),rain_amount_missing=int((~np.isfinite(F[i,P])).sum()),rain_coverage_missing=int((~np.isfinite(F[i,C])).sum()),missing45=int((~np.isfinite(F[i,idx45])).sum()),missing108=int((~np.isfinite(F[i,idx108])).sum())))
report=dict(passed=True,columns45=idx45.tolist(),columns108=idx108.tolist(),removed_by45=R.tolist(),removed_by108=A.tolist(),source_feature_AST_identical=True,all2023_auxiliary_nan=dict(rows=720,columns=12,cells=8640,all_nan=True),rain_block=dict(total=75,amount_or_lagged_amount=45,coverage=30),coverage=rows,rain_by_region=byregion,joint_coverage=cooccur,limits=['Availability means frozen derived feature is finite, not independent confirmation of raw receipt/publication or meteorological truth.','45 removes all75rain fields including30coverage columns;108 removes only12auxiliary level/slopes.','Finite zero rain is counted separately from missing; regional amounts are not renormalized and missingness is preserved.','Frozen hyperparameters were selected for another feature representation; comparison measures this frozen learning procedure, not optimal models or hydrologic causation.','Identical masks retained despite remaining gaps; no complete-input gate.','Full_schedule high counts all237testtargets, including one missing-base forecast perhorizon.','Original2025/26 and2023 publication/datum/plant-regime compatibility remains uncertified.','No models loaded, fitted or inferred, no network or operational edits.'],source_sha256=sources)
save('columns.csv',columns);save('coverage.csv',rows);save('rain-by-region.csv',byregion);save('joint-coverage.csv',cooccur);save('evaluation-high-inputs.csv',evalrows);(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,coverage_h12=[r for r in rows if r['horizon_h']==12 and r['block'] in ['auxiliary12','rain_amount45','rain_coverage30'] and r['population']!='combined_training']),indent=2))
protocolpath=ROOT/'docs/radar-factorial-blocks-protocol.json';protocol=json.loads(use(protocolpath).read_text());assert protocol['new_columns_zero_based']['levels45']==idx45.tolist();assert protocol['new_columns_zero_based']['rain108']==idx108.tolist();assert 'No completeness filter' in protocol['training'];assert protocol['promoted'] is False
report['protocol']=protocol;report['source_sha256']=sources;(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['# Auditoria dos blocos de entradas Radar: 45 e108 campos','',
'Os índices do protocolo foram conferidos contra a função de features congelada, idêntica nas duas matrizes. **45=0..44** conserva os24 campos dos quatro postos de nível e21 campos Q/I das três usinas; remove45..119. **108=0..11+24..119** conserva core33 e chuva; remove12..23 (SantaTereza e Carreiro). A interseção dos conjuntos é core33 e a união é120, sem duplicação de colunas.','',
'O bloco de chuva contém **75 campos:45 de acumulados/defasagens e30 de cobertura**. Remover chuva retira ambos, inclusive a informação de disponibilidade. O CSV columns.csv lista cada posição e participação. A designação levels45 também inclui Q/I, não apenas níveis.','',
'Confirmação2023: as12 colunas auxiliares são NaN em **720/720 origens e8.640/8.640 células**, antes de qualquer máscara. Essa ausência permanece em todos os conjuntos admitidos por horizonte. O corte108 remove esses campos, mas não preenche medições.','',
'## Cobertura h12 nas mesmas máscaras','',
'| Fase/população | Linhas | Linhas com auxiliares faltantes | Linhas com chuva acumulada faltante | Células chuva ausentes | Células cobertura ausentes |','|---|---:|---:|---:|---:|---:|']
for phase in ['validation','test']:
 for pop in ['original_training','added2023_training','combined_training','evaluation_high_full_schedule']:
  rr={r['block']:r for r in rows if r['phase']==phase and r['horizon_h']==12 and r['population']==pop};a=rr['auxiliary12'];b=rr['rain_amount45'];c=rr['rain_coverage30'];lines.append(f"| {phase}/{pop} | {a['rows']} | {a['rows_any_missing']} | {b['rows_any_missing']} | {b['missing_cells']} | {c['missing_cells']} |")
lines+=['',
'No treino2023 h12, há14.366 células de chuva acumulada finitas, das quais5.377 são zeros;7.279 estão ausentes. Apenas73/481 linhas têm todos45 acumulados finitos. As14.430 células de cobertura são finitas; isso não significa que exista chuva medida para todas as regiões e janelas. Não tratar NaN como zero. As contagens para todos12horizontes, duas fases, treino original/adicionado/combinado e avaliação estão nos CSVs.','',
'Os28 alvos de cheia da validação têm ambos os blocos completos em todos os horizontes. No teste h12 há97/237 origens com alguma falta auxiliar e1/237 com chuva acumulada ausente. O denominador237 preserva o alvo de cheia com base Muçum ausente; não foi filtrado pelo sucesso da previsão.','',
'## Limites da comparação','',
'O experimento45/108 mantém parâmetros e máscaras do algoritmo congelado. Isso mede o efeito de remover grupos de entradas nesse procedimento específico, sem novo ajuste de hiperparâmetros; não estabelece a relevância causal hidrológica de chuva ou estações, nem o melhor modelo possível para cada conjunto.','',
'Disponibilidade nesta auditoria significa campo derivado finito da matriz preservada. Não é uma nova validação de sensores, publicação histórica, datum, fuso ou regime das usinas. A remoção de75 campos também remove30 indicadores de cobertura e pode mudar o comportamento do algoritmo por esse motivo. Não presumir equivalência física entre2023 e2025/26.','',
'Nenhuma máscara mudou e nenhum requisito de completude foi acrescentado; faltas remanescentes continuam NaN. Nenhum modelo foi lido, treinado ou executado, nenhuma consulta externa ou alteração operacional. Script, índices, distribuição por região e rastros das origens de avaliação estão preservados com hashes.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n');(OUT/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n');(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
