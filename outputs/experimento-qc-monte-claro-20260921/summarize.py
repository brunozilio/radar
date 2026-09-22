"""Validate paired experiment invariants and produce its development report."""
import csv
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
TREE=HERE.parent/'experimento-vazao-arvores-20260921'

def read(path):
    with path.open() as f:return list(csv.DictReader(f))

evaluation=read(HERE/'evaluation.csv')
current=read(HERE/'current.csv')
predictions=read(HERE/'test-predictions.csv')
reference_current={(r['source'],r['lead_h']):float(r['forecast_m3_s']) for r in read(TREE/'current.csv') if r['family']=='ridge_reference'}
lookup={(r['source'],r['lead_h'],r['variant'],r['origin']):r for r in predictions}
base=[r for r in predictions if r['variant']=='original']
assert len(lookup)==len(predictions)==len(base)*3
max_unaffected_difference=0.
for r in base:
    for v in ['Q_missing','QI_missing']:
        pair=lookup[r['source'],r['lead_h'],v,r['origin']]
        assert pair['target_time']==r['target_time'] and pair['actual_m3_s']==r['actual_m3_s']
        if r['input_affected']=='False':
            max_unaffected_difference=max(max_unaffected_difference,abs(float(pair['forecast_m3_s'])-float(r['forecast_m3_s'])))
assert max_unaffected_difference<1e-8
ev={(r['source'],r['lead_h'],r['phase'],r['subset'],r['variant']):r for r in evaluation}
for r in evaluation:
    b=ev[r['source'],r['lead_h'],r['phase'],r['subset'],'original']
    assert r['n']==b['n']
    if r['phase']=='validation':assert abs(float(r['mae_m3_s'])-float(b['mae_m3_s']))<1e-8
max_reproduction=max(abs(float(r['forecast_m3_s'])-reference_current[r['source'],r['lead_h']]) for r in current if r['variant']=='original')
assert max_reproduction<1e-8
summary=[]
for station in ['julho','carreiro']:
    for variant in ['original','Q_missing','QI_missing']:
        item={'source':station,'variant':variant}
        for subset in ['all','high_flow']:
            rows=[r for r in evaluation if r['source']==station and r['variant']==variant and r['phase']=='test' and r['subset']==subset]
            n=sum(int(r['n']) for r in rows)
            item[subset+'_n']=n
            item[subset+'_mae_m3_s']=sum(int(r['n'])*float(r['mae_m3_s']) for r in rows)/n
        rows=[r for r in predictions if r['source']==station and r['variant']==variant and r['input_affected']=='True']
        item['affected_n']=len(rows)
        item['affected_mae_m3_s']=sum(abs(float(r['forecast_m3_s'])-float(r['actual_m3_s'])) for r in rows)/len(rows)
        item['current_11h_m3_s']=next(float(r['forecast_m3_s']) for r in current if r['source']==station and r['variant']==variant and r['lead_h']=='11')
        summary.append(item)
decision={'promoted':False,'goal_achieved':False,'next_step':'Define and validate a source-semantic input QC rule on independent periods, preserving raw readings. Do not deploy date-specific masks. Investigate extrapolation separately.','checks':{'paired_target_values_and_membership_identical':True,'validation_unchanged':True,'unaffected_test_max_prediction_difference_m3_s':max_unaffected_difference,'reference_current_reproduction_max_difference_m3_s':max_reproduction},'summary':summary,'report_inputs_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'evaluation.csv',HERE/'current.csv',HERE/'test-predictions.csv',HERE/'policy.json',Path(__file__)]}}
(HERE/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
lines=['# Sensibilidade aos zeros suspeitos de Monte Claro','','Apenas experimento retrospectivo: não houve promoção, nova emissão ou modificação do histórico original. A política foi registrada antes do cálculo em docs/monte-claro-input-qc-experiment.json.','','Foram comparadas a entrada original, somente Q ausente e Q/I ausentes nas janelas auditadas de22/07/2026. São12slots deQ e8deI; suas diferenças temporais afetam nove origens horárias. Valores ausentes recebem o tratamento já existente do ridge: mediana e indicadores calculados somente no treinamento. Nenhum valor real de substituição foi inventado.','','| Fonte | Variante | MAE geral | MAE vazões altas | MAE nas origens afetadas | Diagnóstico atual11h |','|---|---|---:|---:|---:|---:|']
for r in summary:lines.append(f"| {r['source']} | {r['variant']} | {r['all_mae_m3_s']:.2f} | {r['high_flow_mae_m3_s']:.2f} | {r['affected_mae_m3_s']:.2f} | {r['current_11h_m3_s']:.2f} |")
lines+=['','Valores em m³/s. MAE agregado nos prazos0–11h, ponderado pela quantidade de pares. Vazões altas usam o percentil95 da fonte anterior a01/10/2025; não são o critério de cheia de Muçum. Cada fonte tem108pares nas origens afetadas: nove origens ×12prazos, altamente correlacionados e pertencentes a um único episódio.','','Em14deJulho, a retirada dos zeros das entradas reduz bastante os erros nesse episódio. EmCarreiro, melhora nas nove origens afetadas convive com pequena piora no subconjunto de vazões altas. A limpeza também não resolve a extrapolação do diagnóstico atual:14deJulho em11h permanece acima de13mil m³/s.','','A validação anterior a01/07/2026 permanece idêntica, assim como todos os alvos e as previsões fora das origens afetadas no teste. O treinamento final, que inclui julho, muda seus coeficientes e por isso modifica também o diagnóstico atual. A referência original reproduz o experimento anterior com erro inferior a1e-8m³/s. Modelos finais, código, política e hashes foram preservados.','','Limitações: as datas anômalas foram identificadas retrospectivamente. Julho–setembro/2026 é um período de desenvolvimento já examinado. Os resultados medem sensibilidade a uma entrada suspeita; não demonstram melhoria prospectiva nem98% de acerto do nível do rio. A máscara por data não deve entrar na operação. É necessário definir uma regra geral a partir da semântica da fonte e avaliá-la em outros eventos, sem selecionar exclusões pelos erros dos modelos. A série atual deCastroAlves não foi invalidada por exceder os máximos históricos.']
(HERE/'report.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(decision['checks']))
