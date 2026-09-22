"""Post-run reporting; preregistered gate unchanged, no model selection."""
import csv,hashlib,json,math
from pathlib import Path
import numpy as np
ROOT=Path('/Users/brunozilio/Documents/radar');OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,rows):
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def metric(values):
    a=np.array(values);e=abs(a)
    return dict(n=len(a),mae_m3_s=float(e.mean()),bias_m3_s=float(a.mean()),
                rmse_m3_s=float(np.sqrt((a*a).mean())),p90_absolute_m3_s=float(np.quantile(e,.9)),
                p98_absolute_m3_s=float(np.quantile(e,.98)),max_absolute_m3_s=float(e.max()))
p=OUT/'predictions.csv';before=sha(p);rows=list(csv.DictReader(p.open()))
families=['level_and_slopes','without_monte'];maps={f:{} for f in families}
for r in rows:
    key=r['phase'],int(r['lead_h']),r['origin'],r['target_time']
    assert key not in maps[r['family']]
    assert math.isfinite(float(r['forecast_m3_s'])) and math.isfinite(float(r['actual_m3_s']))
    maps[r['family']][key]=r
assert maps[families[0]].keys()==maps[families[1]].keys()
for k,r in maps[families[0]].items():
    other=maps[families[1]][k]
    assert r['actual_m3_s']==other['actual_m3_s'] and r['high_flow']==other['high_flow']
evaluations=[];aggregate=[];daily=[];concentration=[]
for phase in ('validation','test'):
    for subset in ('all','high_flow'):
        for family in families:
            selected=[r for r in rows if r['phase']==phase and r['family']==family and (subset=='all' or r['high_flow']=='True')]
            aggregate.append(dict(phase=phase,subset=subset,family=family,**metric([float(r['forecast_m3_s'])-float(r['actual_m3_s']) for r in selected])))
            for lead in range(12):
                rs=[r for r in selected if int(r['lead_h'])==lead]
                evaluations.append(dict(phase=phase,subset=subset,family=family,lead_h=lead,**metric([float(r['forecast_m3_s'])-float(r['actual_m3_s']) for r in rs])))
            if phase=='test':
                for day in sorted({r['origin'][:10] for r in selected}):
                    rs=[r for r in selected if r['origin'][:10]==day]
                    daily.append(dict(phase=phase,subset=subset,family=family,origin_local_date=day,**metric([float(r['forecast_m3_s'])-float(r['actual_m3_s']) for r in rs])))
                for group in ('july22_origins','other_origins'):
                    rs=[r for r in selected if (r['origin'][:10]=='2026-07-22')==(group=='july22_origins')]
                    concentration.append(dict(subset=subset,family=family,diagnostic_group=group,**metric([float(r['forecast_m3_s'])-float(r['actual_m3_s']) for r in rs])))
save('evaluation-extended.csv',evaluations);save('aggregate.csv',aggregate);save('daily-diagnostic.csv',daily)
save('july22-diagnostic.csv',concentration)
original=list(csv.DictReader((OUT/'evaluation.csv').open()));maxdiff=0
for r in original:
    match=next(x for x in evaluations if all(str(x[k])==r[k] for k in ('phase','subset','family','lead_h')))
    for k in ('n','mae_m3_s','bias_m3_s','p90_absolute_m3_s'):
        d=abs(match[k]-float(r[k]));maxdiff=max(maxdiff,d);assert d<1e-8
gate=[]
for phase in ('validation','test'):
    for subset in ('all','high_flow'):
        pair={r['family']:r for r in aggregate if r['phase']==phase and r['subset']==subset}
        old=pair[families[0]]['mae_m3_s'];new=pair[families[1]]['mae_m3_s']
        gate.append(dict(phase=phase,subset=subset,reference_mae_m3_s=old,candidate_mae_m3_s=new,
                         change_percent=(new/old-1)*100,passed=new<old,n=pair[families[0]]['n']))
decision=dict(gate=gate,proceed_to_downstream_evaluation=all(x['passed'] for x in gate),
              promoted=False,goal_achieved=False,live_issuance=False,
              identical_source_target_pairs=len(maps[families[0]]),prediction_failures_in_evaluation=0,
              reference_metrics_reproduction_max_difference=maxdiff,
              caveats=['All periods are previously inspected development; no independent or prospective gain.',
                       'Pooled rows overlap horizons and events and are not independent sample size.',
                       'July22 vs remainder is post-hoc diagnosis, not a replacement gate.',
                       'No claim about source correctness or physical importance of Monte Claro.',
                       'Same baseline exclusions for missing target or known origin flow remain.'],
              input_sha256={str(p):before,str(OUT/'protocol.json'):sha(OUT/'protocol.json')})
(OUT/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
lines=['# Retirada de Monte Claro dos preditores de vazão de 14 de Julho','',
       'A mudança não passou pelo critério pré-especificado para avançar à avaliação do nível de Muçum. Nenhuma previsão operacional foi alterada.','',
       'Foram retiradas 16 entradas de vazão, afluência e níveis/variações de Monte Claro. Os 61 preditores restantes, os alvos, cortes temporais, pesos e regularização mantiveram as regras anteriores. Os valores originais continuam preservados.','',
       '|Período|Recorte|Pares somados nos 12 prazos|MAE anterior (m³/s)|Sem Monte (m³/s)|Mudança|',
       '|---|---|---:|---:|---:|---:|']
for r in gate:
    lines.append(f"|{r['phase']}|{r['subset']}|{r['n']}|{r['reference_mae_m3_s']:.2f}|{r['candidate_mae_m3_s']:.2f}|{r['change_percent']:+.2f}%|")
lines+=['','A soma dos pares pondera os erros pelos respectivos tamanhos; não representa observações independentes. O recorte de vazão alta usa o percentil 95 anterior a outubro de 2025, sem mudança de limiar.','',
        'O ganho em julho–setembro não se repetiu na validação anterior. Retirar a fonte inteira perde informação útil; este experimento não justifica descartar a fonte, declarar erro oficial ou trocar o modelo.','',
        '## Diagnóstico posterior da concentração do erro','',
        'As origens de 22/07 são separadas apenas para entender a sensibilidade já observada. Não são um recorte de seleção nem um evento independente certificado.','',
        '|Recorte|Grupo de origens|Família|N|MAE (m³/s)|Máximo (m³/s)|','|---|---|---|---:|---:|---:|']
for r in concentration:
    lines.append(f"|{r['subset']}|{r['diagnostic_group']}|{r['family']}|{r['n']}|{r['mae_m3_s']:.2f}|{r['max_absolute_m3_s']:.2f}|")
lines+=['','evaluation-extended.csv contém MAE, viés, RMSE, P90, P98 e máximo por prazo/período; daily-diagnostic.csv preserva o diagnóstico por data.','',
        f"Referência reproduzida sem alteração nas previsões; {len(maps[families[0]])} pares idênticos por família, nenhuma previsão não finita nesse conjunto. Excluídos por alvo ou vazão conhecida ausentes continuam fora, como no controle; não equivalem a cobertura completa da série.",'',
        'Arquivos históricos revistos e hipóteses de disponibilidade impedem tratar estes resultados como precisão prospectiva. Nenhuma conclusão de 98% decorre desta ablação.','']
(OUT/'report.md').write_text('\n'.join(lines))
assert sha(p)==before
print(json.dumps(decision,indent=2))
