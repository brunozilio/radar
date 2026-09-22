"""Rating experiment report, separating forecast and algebraic diagnostics."""
import csv,json,shutil
from pathlib import Path
OUT=Path(__file__).resolve().parent
read=lambda name:list(csv.DictReader((OUT/name).open()))
e=read('evaluation.csv');c=read('curve-fit-evaluation.csv');t=read('training.csv');parts=read('component-metrics.csv')
changes=[]
for h in range(1,13):
    pair={f:next(x for x in e if x['horizon_h']==str(h) and x['family']==f and x['subset']=='high' and x['population']=='common') for f in ('reference','candidate')}
    changes.append(dict(horizon_h=h,n=int(pair['reference']['n']),reference_hits=int(pair['reference']['hits']),candidate_hits=int(pair['candidate']['hits']),reference_mae_m=float(pair['reference']['mae_m']),candidate_mae_m=float(pair['candidate']['mae_m'])))
lines=['# Curva de vazão–nível ajustada somente com pares H/Q válidos','',
       'A nova curva não trouxe ganho consistente na previsão e não foi promovida. Foram preservados os modelos operacionais, a tolerância de 0,50 m e a população de alvos.','',
       '## Mudança isolada','',
       'A curva anterior havia sido ajustada somente nas linhas com toda a matriz de roteamento completa. Chuva ou vazão de outra estação ausente excluía um par H/Q válido de Muçum. O candidato usa os pares finitos H/Q, mantendo a mesma forma de potência, inicialização, limites, objetivo soft_l1 e cortes de treino. Nenhum hiperparâmetro foi procurado.','',
       '|Fase|Amostra|Pares de treino|Treino com nível ≥7 m|','|---|---|---:|---:|']
for r in t:lines.append(f"|{r['phase']}|{r['family']}|{r['training_n']}|{r['training_high_n']}|")
lines+=['','## Conversão usando vazão reportada conhecida','',
        'Este quadro mede somente a aproximação H(Q), usando Q reportada no mesmo horário. Não mede capacidade de prever vazão, nível futuro ou independência física entre as medições.','',
        '|Período|Amostra|Recorte|N|MAE da conversão (m)|','|---|---|---|---:|---:|']
for r in c:lines.append(f"|{r['phase']}|{r['family']}|{r['subset']}|{r['n']}|{float(r['mae_m']):.4f}|")
lines+=['','A curva ampliada reduziu o MAE de conversão na cheia da validação (0,206→0,139 m), mas piorou na cheia do teste (0,252→0,259 m). Os pares H/Q do teste não entraram no ajuste. Os períodos, porém, já foram examinados durante o desenvolvimento, portanto não são novos testes independentes.','',
        '## Aplicação às previsões com os demais componentes fixos','',
        'A vazão calculada pelo HGE foi preservada; mudou apenas a curva e o offset calculado com a mesma âncora. Chuva, roteamento, estados, parâmetros, estimativas de montante e correção residual de vazão permaneceram iguais. Parâmetros HGE antes ajustados com a curva antiga podem incorporar compensações; isto é um teste isolado de conversão, não recalibração hidráulica completa.','',
        '|Prazo|N na cheia|Acertos anteriores|Acertos novos|MAE anterior (m)|MAE novo (m)|','|---|---:|---:|---:|---:|---:|']
for r in changes:
    lines.append(f"|{r['horizon_h']} h|{r['n']}|{r['reference_hits']}|{r['candidate_hits']}|{r['reference_mae_m']:.4f}|{r['candidate_mae_m']:.4f}|")
lines+=['','## Decomposição algébrica da referência','',
        'Com Q do alvo disponível, o erro de nível é a soma exata de: diferença de nível associada às vazões pela curva adotada; e diferença entre o resíduo H–Q da âncora e o do alvo. Os termos podem se compensar; seus erros absolutos médios não são parcelas aditivas do erro total.','',
        '|Prazo|Pares de cheia com Q do alvo|MAE total (m)|MAE associado às vazões (m)|MAE da diferença de resíduos H–Q (m)|','|---|---:|---:|---:|---:|']
for h in (1,6,12):
    rr={r['component']:r for r in parts if r['horizon_h']==str(h) and r['subset']=='high'}
    names=('total_error_m','flow_conversion_error_m','anchor_curve_error_m')
    values=[float(rr[n]['mae_m']) for n in names]
    lines.append(f"|{h} h|{rr[names[0]]['n']}|{values[0]:.4f}|{values[1]:.4f}|{values[2]:.4f}|")
lines+=['','A decomposição tem 23.091 pares: perdeu 12 linhas relativas ao alvo de 22/07 às 17h, nível 18,95 m, por falta de Q do alvo na grade. Essas linhas permanecem na comparação das previsões; apenas o diagnóstico algébrico fica indisponível. O alvo de cheia ausente deve impedir interpretar a decomposição como amostra completa.','',
        'VazaoFinal é a vazão reportada pela ANA. O acervo não prova que seja medição independente de nível nem documenta sua derivação operacional em 2025–2026. Logo os termos não são erros físicos puros. O primeiro reúne efeitos de vazão prevista, propagação e escoamento local; o segundo pode refletir curva, referência, revisão ou dependência H/Q.','',
        'Este diagnóstico não elimina incerteza de referência vertical, fuso e revisões. O próximo trabalho deve priorizar os termos que geram a vazão de Muçum e sua correção temporal, preservando o controle atual. Não cabe trocar a curva só pelo ganho pontual de um prazo.','']
(OUT/'report.md').write_text('\n'.join(lines))
(OUT/'decision.json').write_text(json.dumps({'promoted':False,'live_issuance':False,'goal_achieved':False,'high_level_horizon_comparison':changes,'reason':'Inconsistent conversion performance across periods and forecast hit changes across horizons; no independent promotion evidence.','reported_q_is_certified_independent_measurement':False,'decomposition_missing_target_q_rows':12},indent=2)+'\n')
shutil.copyfile('/tmp/radar-rating-paired-tests.log',OUT/'tests.log');shutil.copyfile('/tmp/radar-rating-paired.log',OUT/'execution.log')
print(json.dumps({'high_horizons':changes,'decision':'not promoted'},indent=2))
