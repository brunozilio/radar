import csv,hashlib,json,shutil
from pathlib import Path

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def rows(path):
    with path.open() as f:return list(csv.DictReader(f))

evaluation=rows(OUT/'evaluation.csv');current=rows(OUT/'current.csv');training=rows(OUT/'training-residuals.csv')
families=['reference_delta','weighted_delta','reference_absolute','weighted_absolute']
digests={f:hashlib.sha256() for f in families};counts={f:0 for f in families}
with (OUT/'predictions.csv').open() as f:
    for r in csv.DictReader(f):
        identity=[r[k] for k in ['source','phase','lead_h','origin','target_time','actual_m3_s','high_flow']]
        digests[r['family']].update((json.dumps(identity)+'\n').encode());counts[r['family']]+=1
assert len({d.hexdigest() for d in digests.values()})==1
prior={(r['source'],r['phase'],r['lead_h'],r['subset']):r for r in rows(ROOT/'outputs/experimento-vazao-arvores-20260921/evaluation.csv') if r['family']=='ridge_reference'}
for r in evaluation:
    if r['family']=='reference_delta':
        old=prior[r['source'],r['phase'],r['lead_h'],r['subset']]
        assert r['n']==old['n']
        for field in ['mae_m3_s','bias_m3_s','p90_absolute_m3_s']:assert abs(float(r[field])-float(old[field]))<1e-8
max_weighted_bias=max(abs(float(r['weighted_mean_residual_m3_s_before_clipping'])) for r in training if r['family'].startswith('weighted_'))
assert max_weighted_bias<1e-5
for name,sha in json.loads((OUT/'experiment.json').read_text())['source_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==sha
summary=[]
for source in ['julho','carreiro']:
    for family in families:
        item={'source':source,'family':family}
        for phase in ['validation','test']:
            for subset in ['all','high_flow']:
                group=[r for r in evaluation if r['source']==source and r['family']==family and r['phase']==phase and r['subset']==subset];n=sum(int(r['n']) for r in group)
                item[phase+'_'+subset+'_mae_m3_s']=sum(int(r['n'])*float(r['mae_m3_s']) for r in group)/n
        item['current_11h_m3_s']=next(float(r['forecast_m3_s']) for r in current if r['source']==source and r['family']==family and r['lead_h']=='11')
        item['max_weighted_training_bias_m3_s']=max(abs(float(r['weighted_mean_residual_m3_s_before_clipping'])) for r in training if r['source']==source and r['family']==family)
        summary.append(item)
decision={'status':'NOT_PROMOTED','reason':'Joint weighted centering corrects a fitting property but does not improve validation high-flow MAE of the current delta model, and does not solve extrapolation. Absolute-response variant improves its own biased baseline but remains worse than the current delta reference in validation floods.','max_weighted_training_bias_m3_s':max_weighted_bias,'paired_target_sha256':next(iter(digests.values())).hexdigest(),'paired_target_counts':counts,'summary':summary,'promoted':False,'live_issuance':False,'goal_achieved':False}
(OUT/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
lines=['# Centralização ponderada no ajuste de vazões','','Decisão: candidato não promovido. Ajustar corretamente o intercepto junto dos coeficientes eliminou o resíduo médio ponderado do treinamento, mas não trouxe ganho consistente que justifique mudar o modelo em acompanhamento.','','| Fonte | Família | Validação geral | Validação vazões altas | Desenvolvimento geral | Desenvolvimento vazões altas | Diagnóstico atual11h |','|---|---|---:|---:|---:|---:|---:|']
for r in summary:lines.append(f"| {r['source']} | {r['family']} | {r['validation_all_mae_m3_s']:.3f} | {r['validation_high_flow_mae_m3_s']:.3f} | {r['test_all_mae_m3_s']:.3f} | {r['test_high_flow_mae_m3_s']:.3f} | {r['current_11h_m3_s']:.2f} |")
lines+=['','Erros e vazões em m³/s. MAE ponderado pelo número de pares, nos prazos0–11h. Mantidos limiares de vazão alta por fonte, todos os alvos e os mesmos53preditores. O diagnóstico atual usa o snapshot18h e histórico congelado das15h; não reproduz necessariamente o ajuste horário ativo.','','## O que foi isolado','','O ajuste anterior padronizava as entradas pela média não ponderada e fixava o intercepto na média ponderada do alvo. Quando pesos e entradas estão associados, isso não equivale ao ótimo conjunto de coeficientes e intercepto livre. O candidato usa a média ponderada das entradas, mantendo medianas, desvios-padrão, penalidade1000 e pesos originais. Essa mudança foi testada separadamente para resposta de variação e resposta de vazão absoluta.','','O candidato foi conferido contra uma formulação independente de mínimos quadrados aumentados, com intercepto sem penalidade, além das equações normais e do resíduo médio ponderado. Pesos uniformes reproduzem a referência; Carreiro não teve diferença relevante pois os pesos desse treino são uniformes. A suíte local passou71testes.','','Em14deJulho, o resíduo médio ponderado máximo no treinamento da referência de variação era17,70m³/s; o candidato o removeu numericamente. Na versão de resposta absoluta, o valor era148,83m³/s. Isso não garante menor erro fora do ajuste: a validação de vazões altas do modelo de variação praticamente não mudou e o desenvolvimento piorou ligeiramente. A variante absoluta ponderada melhorou sua própria referência, mas ficou pior que o modelo de variação nas vazões altas da validação.','','A comparação conservou96modelos finais, código, hashes, resíduos de treino e previsões pareadas. Os períodos já foram examinados em desenvolvimento e não representam validação independente nova. Nenhuma emissão foi substituída. A discrepância de centralização não explica a extrapolação atual, e a meta98% permanece não demonstrada.']
(OUT/'report.md').write_text('\n'.join(lines)+'\n')
log=Path('/tmp/radar-weighted-centering.log')
if log.exists():shutil.move(log,OUT/'execution.log')
print(json.dumps({'decision':decision['status'],'max_weighted_training_bias_m3_s':max_weighted_bias,'pairs':counts}))
