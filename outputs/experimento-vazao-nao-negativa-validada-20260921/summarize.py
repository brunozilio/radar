import csv,hashlib,json,shutil
from pathlib import Path

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def rows(path):
    with path.open() as f:return list(csv.DictReader(f))

e=rows(OUT/'evaluation.csv');c=rows(OUT/'current.csv');diag=rows(OUT/'solver-diagnostics.csv')
assert len(diag)==36 and all(r['success']=='True' and float(r['kkt_relative'])<1e-7 for r in diag)
families=['reference_delta_full','level_ridge_unconstrained','level_ridge_nonnegative']
digests={f:hashlib.sha256() for f in families};counts={f:0 for f in families}
with (OUT/'predictions.csv').open() as f:
    for r in csv.DictReader(f):
        keys=[r[k] for k in ['phase','lead_h','origin','target_time','actual_m3_s','high_flow']]
        digests[r['family']].update((json.dumps(keys)+'\n').encode());counts[r['family']]+=1
assert len({h.hexdigest() for h in digests.values()})==1
prior={(r['phase'],r['lead_h'],r['subset']):r for r in rows(ROOT/'outputs/experimento-vazao-2023-20260921/evaluation.csv') if r['family']=='reference_full'}
for r in e:
    if r['family']=='reference_delta_full':
        old=prior[r['phase'],r['lead_h'],r['subset']]
        assert r['n']==old['n'] and abs(float(r['mae_m3_s'])-float(old['mae_m3_s']))<1e-8
for file,sha in json.loads((OUT/'experiment.json').read_text())['source_sha256'].items():
    assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==sha
summary=[]
for phase in ['validation','test']:
    for family in families:
        item={'phase':phase,'family':family}
        for subset in ['all','high_flow']:
            group=[r for r in e if r['phase']==phase and r['family']==family and r['subset']==subset]
            n=sum(int(r['n']) for r in group);item[subset+'_n']=n
            for field in ['mae_m3_s','bias_m3_s']:item[subset+'_'+field]=sum(int(r['n'])*float(r[field]) for r in group)/n
        summary.append(item)
decision={'status':'NOT_PROMOTED','reason':'Nonnegative level regression reduced current extrapolation and development-test high-flow MAE but worsened validation high-flow MAE and general errors. No independent gain demonstrated.','max_relative_kkt_residual':max(float(r['kkt_relative']) for r in diag),'paired_target_sha256':next(iter(digests.values())).hexdigest(),'paired_target_counts':counts,'summary':summary,'invalid_predecessor':'../experimento-vazao-nao-negativa-20260921/invalidation.json','promoted':False,'goal_achieved':False}
(OUT/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
lines=['# Regressão de vazões com coeficientes não negativos','','Resultado: candidato não promovido. Este é o experimento numericamente validado. O primeiro resultado, em experimento-vazao-nao-negativa-20260921, foi invalidado por falha na construção da matriz e não deve ser usado para conclusões.','','| Período | Família | MAE geral | MAE vazões altas | Viés vazões altas |','|---|---|---:|---:|---:|']
for r in summary:lines.append(f"| {r['phase']} | {r['family']} | {r['all_mae_m3_s']:.2f} | {r['high_flow_mae_m3_s']:.2f} | {r['high_flow_bias_m3_s']:.2f} |")
lines+=['','Unidades:m³/s. Agregados ponderados pelo número de pares em0–11h. Vazões altas usam o mesmo percentil95 histórico de14deJulho da referência, não a cota de cheia deMuçum. Todos os candidatos usam exatamente os mesmos alvos de avaliação.','','A restrição reduz o diagnóstico atual de14deJulho em11h de19.341,99 para12.623,36m³/s. Isso não prova maior precisão. Na validação anterior, o erro de vazões altas piora de285,24 para417,48m³/s; no desenvolvimento seguinte, melhora437,99→421,84, acompanhada de piora geral169,23→175,64. O período seguinte já foi examinado, portanto não é evidência independente que possa substituir a validação anterior.','','O modelo intermediário sem restrição também foi testado para separar a mudança de variáveis/objetivo da restrição de sinal. Os dois modelos de nível usam vazões defasadas em vez de diferenças, resposta absoluta e os mesmos25preditores de chuva. O intercepto permanece fixado à média ponderada do alvo, como no ajustador de referência; não foi otimizado separadamente neste protocolo.','','## Verificação numérica','','O primeiro otimizador declarou sucesso, mas uma conferência independente encontrou resíduo relativoKKT0,0375 em um ajuste. Valores da parte não utilizada do fator triangular entravam na matriz transposta. A implementação passou a extrair explicitamente o triângulo inferior, verificar a reconstrução da matriz original e exigir KKTrelativo<=1e-7. Um teste injeta valores espúrios no triângulo oposto para garantir que não afetem o problema.','','Na repetição validada,36ajustes restritos convergiram, com resíduo relativo máximo2,94e-15. A referência reproduz a avaliação anterior; hashes e identidade dos alvos foram conferidos. Os36modelos finais e cópias de código foram preservados. A suíte local passou68testes.','','As restrições tornam a resposta monotônica nas variáveis numéricas, mantendo os demais valores e indicadores de ausência fixos. Não impõem conservação de água, soma unitária dos coeficientes ou teto físico ao rio. Nenhuma previsão ativa foi modificada ou emitida por este experimento. A meta98% permanece não demonstrada.']
(OUT/'report.md').write_text('\n'.join(lines)+'\n')
log=Path('/tmp/radar-nonnegative-validated.log')
if log.exists():shutil.move(log,OUT/'execution.log')
print(json.dumps({'decision':decision['status'],'KKT':decision['max_relative_kkt_residual'],'pairs_per_family':counts}))
