"""Audit the fixed experiment and record its non-promotion decision."""
import csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent

def rows(path):
    with path.open() as f:return list(csv.DictReader(f))

evaluation=rows(OUT/'evaluation.csv');current=rows(OUT/'current.csv')
prior={(r['phase'],r['lead_h'],r['subset']):r for r in rows(ROOT/'outputs/experimento-vazao-arvores-20260921/evaluation.csv') if r['source']=='julho' and r['family']=='ridge_reference'}
reference_error=0.
for r in evaluation:
    if r['family']=='reference_full':
        old=prior[r['phase'],r['lead_h'],r['subset']]
        assert r['n']==old['n']
        for key in ['mae_m3_s','bias_m3_s','p90_absolute_m3_s']:
            reference_error=max(reference_error,abs(float(r[key])-float(old[key])))
assert reference_error<1e-8
families=['reference_full','reference_ceran_only','augmented_ceran_2023']
digests={f:hashlib.sha256() for f in families};counts={f:0 for f in families}
with (OUT/'predictions.csv').open() as f:
    for r in csv.DictReader(f):
        identity=[r[k] for k in ['phase','lead_h','origin','target_time','actual_m3_s','high_flow']]
        digests[r['family']].update((json.dumps(identity)+'\n').encode());counts[r['family']]+=1
assert len({v.hexdigest() for v in digests.values()})==1
assert len(set(counts.values()))==1
manifest=json.loads((OUT/'experiment.json').read_text())
for name,sha in manifest['input_sha256'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==sha,name
summary=[]
for phase in ['validation','test']:
    for family in families:
        item={'phase':phase,'family':family}
        for subset in ['all','high_flow']:
            group=[r for r in evaluation if r['phase']==phase and r['family']==family and r['subset']==subset]
            n=sum(int(r['n']) for r in group)
            item[subset+'_n']=n
            for metric in ['mae_m3_s','bias_m3_s']:
                item[subset+'_'+metric]=sum(float(r[metric])*int(r['n']) for r in group)/n
        summary.append(item)
decision={'status':'NOT_PROMOTED','reason':'Added2023 CERAN-only ridge worsened validation high-flow MAE against both baselines; current extrapolation also increased. No hyperparameter retuning after observing this result.','historical_reference_reproduction_max_error_m3_s':reference_error,'paired_target_membership_sha256':next(iter(digests.values())).hexdigest(),'paired_target_counts':counts,'input_hashes_verified':len(manifest['input_sha256']),'summary':summary,'live_issuance':False,'goal_achieved':False}
(OUT/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
lines=['# Treinamento experimental com a cheia de2023','','Decisão: candidato não promovido. Parâmetros e avaliação seguiram o protocolo definido antes do ajuste. Os dados de2023 permanecem preservados; nenhum resultado alterou os modelos em acompanhamento.','','| Período | Família | MAE geral | MAE vazões altas | Viés nas vazões altas |','|---|---|---:|---:|---:|']
for r in summary:lines.append(f"| {r['phase']} | {r['family']} | {r['all_mae_m3_s']:.2f} | {r['high_flow_mae_m3_s']:.2f} | {r['high_flow_bias_m3_s']:.2f} |")
lines+=['','Vazões e erros em m³/s. Média ponderada pela quantidade de pares, nos prazos0–11h. O recorte de vazões altas usa o percentil95 de14deJulho anterior a01/10/2025, preservado da referência; não é a definição de cheia de Muçum. Os336pares de validação e3.252de desenvolvimento são correlacionados e não equivalem a eventos independentes.','','A referência completa teve MAE285,24m³/s nas vazões altas da validação; retirar chuva/tributário elevou para324,89. Adicionar2023 ao modelo reduzido elevou novamente para406,71. No desenvolvimento posterior, acrescentar2023 melhorou o modelo reduzido, mas o resultado454,72 continuou pior que437,99 da referência completa. Não há ganho sustentado que justifique substituição.','','## Diagnóstico atual, origem18h de21/09','','| Família | Vazão estimada0h | +5h | +11h |','|---|---:|---:|---:|']
for family in families:
    values={int(r['lead_h']):float(r['forecast_m3_s']) for r in current if r['family']==family}
    lines.append(f"| {family} | {values[0]:.2f} | {values[5]:.2f} | {values[11]:.2f} |")
lines+=['','Os modelos desta comparação usam o histórico de latência congelado das15h e a entrada atual do snapshot18h; não são reprodução do ajuste horário ativo. A leitura mais recente de14deJulho era17h, portanto o valor0h é estimativa, não observação. Nenhum destes diagnósticos foi emitido como previsão adicional.','','## Auditoria e limitações','','Foram acrescentadas669–681origens de2023 por antecedência; o máximo alvo adicional é15.114m³/s. Os alvos são exclusivamente vazões publicadas em horas exatas. Registros23:59 podem ser entradas após o atraso presumido, mas não foram deslocados para criar alvos à meia-noite. Não se usou pico de nível Muçum, precipitação inventada ou vazão futura como entrada.','','A referência reproduziu os resultados históricos anteriores até tolerância1e-8m³/s. Os três candidatos têm exatamente os mesmos alvos/recortes de avaliação, confirmados por hash. Os dados brutos, política, código,36modelos finais, entradas e escolhas foram preservados. A suíte local passou64testes, incluindo vazamento temporal, expiração de leitura carregada, sinais por campo e não conversão23:59→00h.','','Disponibilidade original, fuso histórico e regime operacional pré-avarias2024 seguem limitações. O evento2023 e o período de desenvolvimento posterior já foram examinados; nenhum deles representa teste independente novo. Os resultados não provam98% de acerto de nível. A simples adição de uma cheia maior, nesta representação linear, foi insuficiente. O próximo candidato deve tratar a dinâmica e a extrapolação mantendo essas avaliações como desenvolvimento.']
(OUT/'report.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'decision':decision['status'],'reference_error':reference_error,'paired_counts':counts,'inputs_verified':decision['input_hashes_verified']}))
