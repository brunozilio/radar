"""Report conditional branch performance without selecting a new rule."""
import csv,json,hashlib,math
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent
def save(path,rows):
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def stats(error):
    e=np.array(error);a=abs(e)
    return dict(n=len(e),mae_m3_s=float(a.mean()),bias_m3_s=float(e.mean()),
                p90_abs_m3_s=float(np.quantile(a,.9)),p98_abs_m3_s=float(np.quantile(a,.98)),
                max_abs_m3_s=float(a.max()),rmse_m3_s=float(np.sqrt((e*e).mean()))) if len(e) else dict(n=0,mae_m3_s=None,bias_m3_s=None,p90_abs_m3_s=None,p98_abs_m3_s=None,max_abs_m3_s=None,rmse_m3_s=None)
p=OUT/'predictions.csv';sha=hashlib.sha256(p.read_bytes()).hexdigest();rows=list(csv.DictReader(p.open()))
evaluation=[];aggregate=[];branches=[];changed=[]
for phase in ('validation','test'):
    for subset in ('all','high_flow'):
        selected=[r for r in rows if r['phase']==phase and (subset=='all' or r['high_flow']=='True')]
        for name,column in [('reference','reference_m3_s'),('conditional','forecast_m3_s')]:
            aggregate.append(dict(phase=phase,subset=subset,family=name,**stats([float(r[column])-float(r['actual_m3_s']) for r in selected])))
            for h in range(12):
                evaluation.append(dict(phase=phase,subset=subset,family=name,lead_h=h,**stats([float(r[column])-float(r['actual_m3_s']) for r in selected if int(r['lead_h'])==h])))
            for branch in (False,True):
                branchrows=[r for r in selected if (r['fallback_selected']=='True')==branch]
                branches.append(dict(phase=phase,subset=subset,family=name,fallback_selected=branch,**stats([float(r[column])-float(r['actual_m3_s']) for r in branchrows])))
for r in rows:
    selected=r['fallback_selected']=='True'
    if not selected:assert r['forecast_m3_s']==r['reference_m3_s']
    else:
        actual=float(r['actual_m3_s']);old=float(r['reference_m3_s']);new=float(r['forecast_m3_s'])
        changed.append(dict(origin=r['origin'],target_time=r['target_time'],lead_h=r['lead_h'],
                            actual_m3_s=actual,reference_m3_s=old,conditional_m3_s=new,
                            reference_abs_error_m3_s=abs(old-actual),conditional_abs_error_m3_s=abs(new-actual),
                            error_change_m3_s=abs(new-actual)-abs(old-actual)))
save(OUT/'evaluation.csv',evaluation);save(OUT/'aggregate.csv',aggregate);save(OUT/'branch-metrics.csv',branches)
save(OUT/'affected-predictions.csv',changed)
decision=dict(promoted=False,goal_achieved=False,live_issuance=False,prediction_rows=len(rows),
              selected_rows=len(changed),unselected_values_preserved=len(rows)-len(changed),
              improved_selected_rows=sum(r['error_change_m3_s']<0 for r in changed),
              worsened_selected_rows=sum(r['error_change_m3_s']>0 for r in changed),
              validation_selected_rows=sum(r['phase']=='validation' and r['fallback_selected']=='True' for r in rows),
              status='Historical causal-dependency diagnostic, not promotion evidence',
              limitation='The conflict branch was chosen after source/model diagnostics and has no exercised validation cases or independent future event.',
              next_step='Assess full downstream sensitivity without promotion; establish independently verified comparable live source semantics before any operational use.',
              prediction_sha256=sha)
(OUT/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
lines=['# Modelo alternativo condicionado a conflito de componentes ONS','',
       'Diagnóstico histórico local. Nenhuma observação, emissão ou modelo operacional foi substituído.','',
       'A regra geral detectou três registros de Monte Claro: Q total zero com componentes completos somando 6 m³/s. Pela dependência dos preditores atuais e de 1/3/6 horas, eles afetam nove origens, 22/07 das 08h às 16h. Somente nessas origens usa-se a previsão congelada sem os 16 preditores Monte. Nenhuma data está codificada na seleção.','',
       '|Período|Recorte|Modelo|N|MAE (m³/s)|Máximo (m³/s)|','|---|---|---|---:|---:|---:|']
for r in aggregate:
    lines.append(f"|{r['phase']}|{r['subset']}|{r['family']}|{r['n']}|{r['mae_m3_s']:.2f}|{r['max_abs_m3_s']:.2f}|")
lines+=['',f"Foram selecionadas {len(changed)} previsões dos 12 prazos; {decision['improved_selected_rows']} melhoraram e {decision['worsened_selected_rows']} pioraram. As outras {len(rows)-len(changed)} ficaram exatamente iguais. A população de alvos foi preservada.",'',
        'O grupo selecionado está inteiro no teste já inspecionado. Não há caso de conflito exercitado na validação anterior, portanto a invariância dessa validação não prova que o ramo alternativo generaliza. Nove origens e 108 prazos sobrepostos não constituem nove eventos nem 108 amostras independentes.','',
        'O conflito não determina qual coluna está incorreta nem fornece uma vazão verdadeira de reposição. Campos ausentes permanecem desconhecidos. A fórmula ONS não foi transferida às páginas CERAN atuais, cujo contrato de componentes é diferente/não verificado.','',
        'Atraso de uma hora e expiração de 90 minutos reproduzem a hipótese dos preditores históricos. O arquivo revisado não informa quando cada revisão esteve disponível. A seleção usa tempos passados, mas disponibilidade histórica não está certificada.','',
        'A melhora de vazão deve ser investigada até o nível de Muçum; por si só não demonstra a meta de 98% e não autoriza promoção.','']
(OUT/'report.md').write_text('\n'.join(lines))
assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
print(json.dumps({'decision':decision,'aggregate':aggregate},indent=2))
