"""Independent column/array audit, no pipeline imports or model execution."""
import ast,csv,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def save(n,r):
 with (OUT/n).open('w') as f:w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
def lag(a,n):return np.r_[np.full(n,np.nan),a[:-n]]
oldbase=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921';newbase=ROOT/'outputs/radar-matriz-observada-2023-20260921';old=dict(np.load(use(oldbase/'features.npz')));new=dict(np.load(use(newbase/'features.npz')))
files=[oldbase/'code/hydro_latency_forecast.py',newbase/'code/hydro_latency_forecast.py',ROOT/'scripts/hydro_latency_forecast.py'];asts=[]
for p in files:
 tree=ast.parse(use(p).read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='telemetry_features');asts.append(ast.dump(node,include_attributes=False))
assert asts[0]==asts[1]==asts[2]
core=np.r_[np.arange(12),np.arange(24,45)];names=[]
for code,label in [('86510000','Muçum'),('86472000','Linha José Júlio')]:
 start=0 if code=='86510000' else 6
 names.append(dict(original_column=start,feature=code+':H',physical_source=label,unit='m',formula='H delayed',source_field='ANA NivelFinal/100',delay_minutes=15 if start==0 else 30,query_expiry_minutes=15))
 for k,h in enumerate([.5,1,2,4,8],1):names.append(dict(original_column=start+k,feature=code+f':dH{h:g}',physical_source=label,unit='m/h',formula=f'(H(O)-H(O-{h:g}h))/{h:g}',source_field='ANA NivelFinal/100',delay_minutes=15 if start==0 else 30,query_expiry_minutes=15))
for start,plant,label,code in [(24,'julho','14 de Julho','JIUHQJ'),(31,'monte','Monte Claro','JIUHMC'),(38,'castro','Castro Alves','JIUHCA')]:
 for k,name,unit,formula,field in [(0,'Q06','(1000m3/s)^0.6','maximum(Q/1000,0)**0.6','val_vazaodefluente'),(1,'Q','1000m3/s','Q/1000','val_vazaodefluente'),(2,'I','1000m3/s','I/1000','val_vazaoafluente')]+[(i+3,'dQ'+str(h),'(1000m3/s)^0.6/h',f'(Q06(O)-Q06(O-{h}h))/{h}','val_vazaodefluente') for i,h in enumerate([1,2,4,8])]:
  names.append(dict(original_column=start+k,feature=plant+':'+name,physical_source=label+' '+code,unit=unit,formula=formula,source_field='ONS '+field+'; original recent CERAN HTML merged',delay_minutes=60,query_expiry_minutes=90))
for i,r in enumerate(names):r['core_column']=i
assert [r['original_column'] for r in names]==list(core)
ages=list(csv.DictReader(use(ROOT/'outputs/mucum-atualizacao-15h-2026-09-21/idades-fontes.csv').open()))
for code,delay in [('86510000',15),('86472000',30),('julho',60),('monte',60),('castro',60)]:assert float(next(r['delay_minutes'] for r in ages if r['source']==code))==delay
checks=[];coverage=[]
for label,data,path in [('original2025_26',old,ROOT/'outputs/mucum-atualizacao-15h-2026-09-21/telemetria-latencia.npz'),('added2023',new,newbase/'quarter-hour.npz')]:
 q=dict(np.load(use(path)));ix=np.searchsorted(q['times'],data['times']);assert np.array_equal(q['times'][ix],data['times']);columns=[]
 for code in ['86510000','86472000']:
  v=q[code+':H'];columns.append(v[ix])
  for h in [.5,1,2,4,8]:columns.append(((v-lag(v,int(h*4)))/h)[ix])
 for plant in ['julho','monte','castro']:
  v=q[plant+':Q']/1000;power=np.maximum(v,0)**.6;columns.extend([power[ix],v[ix],q[plant+':I'][ix]/1000])
  for h in [1,2,4,8]:columns.append(((power-lag(power,h*4))/h)[ix])
 x=np.column_stack(columns);np.testing.assert_array_equal(x,data['features'][:,core]);checks.append(dict(dataset=label,shape=list(x.shape),cells=x.size,max_difference=0,nan_cells=int(np.isnan(x).sum()),rows_all33_finite=int(np.isfinite(x).all(1).sum()),rows_any_missing=int((~np.isfinite(x)).any(1).sum()),finite_base=int(np.isfinite(data['base']).sum())))
 for j,r in enumerate(names):coverage.append(dict(dataset=label,**r,rows=len(x),finite=int(np.isfinite(x[:,j]).sum()),missing=int((~np.isfinite(x[:,j])).sum())))
 # Descriptive admitted training rows, not a new membership filter.
 for h in [1,6,12]:
  y=np.r_[data['truth'][h:],np.full(h,np.nan)];eligible=np.isfinite(y)&np.isfinite(data['base']);checks.append(dict(dataset=label,horizon_h=h,finite_base_target=int(eligible.sum()),among_eligible_all33_finite=int((eligible&np.isfinite(x).all(1)).sum()),among_eligible_any33_missing=int((eligible&(~np.isfinite(x)).any(1)).sum())))
protocol=ROOT/'docs/radar-core33-compatibility-protocol.json';p=json.loads(use(protocol).read_text()) if protocol.exists() else None
if p is not None:
 assert p['columns_zero_based']==core.tolist()
 assert p['promoted'] is False and p['goal_achieved'] is False
 assert 'No complete-input restriction' in p['training']
 use(ROOT/'scripts/hydro_radar_core33.py')
result=dict(passed=True,selected_original_columns=core.tolist(),feature_function_AST_identical=True,columns=names,coverage=checks,protocol_available=p is not None,protocol=p,semantic_conclusion='Same ordered mathematical feature definitions, named source identities, units and configured delays. Semantic correspondence is sufficient for the declared descriptive factorial experiment; it does not establish sensor datum, physical regime or historical source-availability equivalence.',limits=['Original quarter-hour ONS/CERAN preparation merges previously gridded history and recent HTML;2023 preparation selects literal monthly ONS rows. Equal formulas do not certify interchangeable source versions or identical timestamp preprocessing.','2023 literal23:59 preserved; original source-level preprocessing was not rebuilt here.','Q/I retained as reported, no mass balance, sum-of-components correction, storage calculation or official validity certification.','dQ is rate of transformed defluence, not raw m3/s/h. Q06 clips negatives only in power transform; raw Q/I columns are not clipped.','Historical delays are presumed availability, not issue/receipt logs. Datum/regime changes between2023and2025/26remain unverified.','No new completeness gate: missing selected inputs remain missing. Core33 drops all rain and both SantaTereza/Carreiro level blocks.','No models loaded, trained or run.'],source_sha256=sources)
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');save('columns.csv',names);save('coverage.csv',coverage)
print(json.dumps({k:v for k,v in result.items() if k in ['passed','coverage','protocol_available']},indent=2))
lines=['# Auditoria das colunas Radar core33','',
'As mesmas 33 posições têm a mesma definição matemática, identidade nominal de fonte e unidades nas matrizes original e 2023. A função telemetry_features é idêntica por AST nas duas cópias congeladas e no código atual. A reconstrução independente a partir das grades de 15 minutos coincide exatamente em **450.384 células** (426.624 originais e 23.760 de 2023), incluindo NaNs.','',
'| Posições na matriz120 | Posições core33 | Fonte e conteúdo |','|---|---|---|','| 0–5 | 0–5 | Muçum 86510000: H e dH0,5/1/2/4/8 |','| 6–11 | 6–11 | Linha José Júlio 86472000: H e dH0,5/1/2/4/8 |','| 24–30 | 12–18 | 14 de Julho JIUHQJ: Q06, Q, I, dQ06 1/2/4/8 |','| 31–37 | 19–25 | Monte Claro JIUHMC: mesmos sete campos |','| 38–44 | 26–32 | Castro Alves JIUHCA: mesmos sete campos |','',
'`H` está em metros, derivadas de H em m/h. Q e I estão divididas por 1.000 (não valores em m³/s sem escala). `Q06=max(Q/1000,0)^0,6`; **dQ06 é a derivada dessa potência por hora**, não derivada da vazão bruta. O clipping pertence apenas à potência; Q/I preservam seus valores. Aflluência I e defluência Q são de cada usina individual, não somas na cascata. O CSV columns.csv registra todas as 33 posições, fórmulas e unidades.','',
'Os atrasos congelados são Muçum 15 min, Linha José Júlio 30 min, com expiração de 15 min após a consulta; Q/I 60 min, expiração de 90 min. idades-fontes.csv confirma os valores do snapshot original, e o builder2023 declara os mesmos. Comparação matemática não certifica disponibilidade histórica real.','',
'## Cobertura','',
'| Matriz | Origens | Linhas com todos33 finitos | Linhas com alguma falta | Células ausentes |','|---|---:|---:|---:|---:|']
for r in checks:
 if 'shape' in r:lines.append(f"| {r['dataset']} | {r['shape'][0]} | {r['rows_all33_finite']} | {r['rows_any_missing']} | {r['nan_cells']} |")
lines+=['',
'No lote2023, entre pares base/alvo finitos h1/h6/h12, são 503/493/481 pares; 483/473/461 têm todos33 finitos e **20 em cada horizonte continuam com alguma falta**. A seleção core33 não deve acrescentar um filtro de completude: as máscaras originais do experimento devem permanecer. Contagens da matriz original cobrem toda a grade preservada, não equivalem às máscaras temporais de treino de uma fase.','',
'## Correspondência e limites','',
'A correspondência de colunas é consistente para o experimento fatorial declarado. Isso é distinto de certificar equivalência física das medições: datum, manutenção dos sensores, validade de Q reportada, fuso/publicação e regime operacional entre 2023 e 2025/26 continuam sem certificação.','',
'O preparo original mescla história já em grade e HTML CERAN recente; o de2023 consulta CSVs ONS mensais com timestamps literais, inclusive23:59. Esta auditoria recompõe derivados das grades preservadas, não reconstrói a cadeia original de ingestão ONS/CERAN nem declara versões de fonte intercambiáveis. A auditoria anterior da matriz2023 verificou a consulta literal diretamente; nenhuma nova consulta foi feita aqui.','',
'Core33 elimina os12 campos Santa Tereza/Carreiro e todos75 campos de chuva do conjunto120. Manter mesma ordem não demonstra que esse corte melhorará previsões. Nenhum modelo foi lido, treinado ou executado; nenhum dado ou código operacional foi modificado.','',
f"Protocolo disponível e preservado nesta execução: {'sim' if p is not None else 'ainda não; auditoria numérica concluída, leitura do protocolo pendente'}. O conteúdo integral e o hash, quando disponível, ficam em verification.json."
]
(OUT/'README.md').write_text('\n'.join(lines).replace('Aflluência','Afluência')+'\n')
(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=q.name,sha256=sha(q)) for q in sorted(OUT.iterdir()) if q.is_file() and q.name!='artifact-hashes.json'],indent=2)+'\n')
