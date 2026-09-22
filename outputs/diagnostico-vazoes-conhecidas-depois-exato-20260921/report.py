"""NON-FORECAST sensitivity report; no operational or goal score updates."""
import csv,json,hashlib,shutil
from pathlib import Path
from collections import Counter
OUT=Path(__file__).resolve().parent
e=list(csv.DictReader((OUT/'evaluation-diagnostic-only.csv').open()))
r=list(csv.DictReader((OUT/'reconstructions-not-forecasts.csv').open()))
audit=list(csv.DictReader((OUT/'julho-exact-observation-audit.csv').open()))
counts=Counter(x['status'] for x in audit)
status={f:dict(Counter(x[f+'_status'] for x in r)) for f in ('reference','observed_julho','observed_carreiro','observed_both')}
lines=['# Diagnóstico com vazões conhecidas depois — não é previsão','',
       '**Estes resultados usam informações indisponíveis na emissão e não contam para a meta de 98%.** Servem somente para investigar a sensibilidade das previsões às estimativas de vazão de montante.','',
       'Mantivemos o nível de referência, alvos, âncoras, chuva, Carreiro histórico/proxies, estados HGE, roteamento e curva. Substituímos apenas os termos de vazão estimada com tempo relativo não negativo: Julho, Carreiro ou ambos. Inclusive o termo relativo zero pode estar indisponível na emissão por atraso de publicação.','',
       '## Contrato de observação e cobertura','',
       f"Nos {len(audit)} horários de julho–setembro, a conferência de Julho encontrou {counts['missing_exact_ons_record']} sem timestamp ONS exato e {counts['baseline_disagreement']} com valor diferente da grade de referência. Esses pontos ficaram indisponíveis para o diagnóstico; não receberam valores anteriores nem aproximação temporal.",'',
       'A primeira execução usava a grade com retenção de leitura anterior e foi preservada como preliminar/superada em ../diagnostico-vazoes-conhecidas-depois-20260921/invalidation.json. Não sustenta uma conclusão sobre observações exatas.','',
       'A exigência de dados disponíveis em todos os quatro cenários reduz a amostra. Comparamos cada cenário com a referência na mesma interseção, sem apresentar a redução como ganho de cobertura. Métricas individuais e exclusões permanecem no CSV.','',
       '## Níveis de cheia — interseção dos quatro cenários','',
       '|Prazo|Cenário|N comum|Acertos ≤0,50 m|MAE (m)|Máximo (m)|','|---|---|---:|---:|---:|---:|']
labels={'reference':'Referência causal','observed_julho':'Julho conhecido depois','observed_carreiro':'Carreiro conhecido depois','observed_both':'Ambos conhecidos depois'}
for h in (1,6,12):
    for family in labels:
        x=next(x for x in e if x['horizon_h']==str(h) and x['subset']=='high' and x['population']=='common_four' and x['family']==family)
        lines.append(f"|{h} h|{labels[family]}|{x['n']}|{x['hits']} ({100*float(x['hit_fraction']):.2f}%)|{float(x['mae_m']):.4f}|{float(x['max_abs_m']):.4f}|")
lines+=['','## O que o diagnóstico muda','',
        'Na interseção de 12 h/cheia (81 pares), trocar só a vazão de Julho reduz MAE de 1,722 para 1,027 m; trocar só Carreiro reduz para 1,651 m; ambos chegam a 0,992 m. Ainda sobram erros relevantes, apesar da informação extra. Portanto, aperfeiçoar apenas a estimativa de montante não basta neste recorte: também é necessário investigar a resposta que converte as vazões em nível, incluindo correção da âncora, curva, runoff local e entradas históricas.','',
        'A contribuição de cada fonte não é aditiva, e erros podem se compensar. No prazo de 6 h, usar o Carreiro conhecido depois piora o MAE de 0,896 para 0,916 m. Isso não prova defeito na medição nem que uma previsão pior de Carreiro é desejável.','',
        'Não é um limite superior teórico de precisão, modelo candidato, treino, teste independente ou previsão prospectiva. A interseção tem forte seleção por lacunas; 81 pares de prazos sobrepostos não representam 81 cheias independentes. Fuso, revisões e validade física das medições continuam sujeitos às ressalvas do acervo.','',
        'O próximo diagnóstico deve separar os termos de resposta do modelo sobre os casos em que há entradas completas, mantendo a comparação também nos dados operacionais. A meta e a tolerância de 0,50 m permanecem iguais.','',
        '## Verificação matemática','',
        'Foram recompostos roteamentos completos de Julho/Carreiro em seis origens e quatro cenários usando componentes HGE/residual de replay independente anterior: 288 comparações, 228 valores finitos e 60 ausências concordantes; diferença máxima 1,07e-14 m. A checagem não inverteu os níveis de referência. Não houve nova simulação HGE dos 23.538 casos. A suíte passou 119 testes.','']
(OUT/'report.md').write_text('\n'.join(lines))
(OUT/'status-counts.json').write_text(json.dumps(status,indent=2)+'\n')
(OUT/'decision.json').write_text(json.dumps({'valid_operational_forecast':False,'eligible_for_goal':False,'models_fitted':0,'promoted':False,'goal_achieved':False,'exact_julho_audit':dict(counts),'retained_origin_target_rows':len(r),'next_focus':'Investigate level response and anchor/routing/local runoff jointly; upstream forecast errors alone do not explain the residual diagnostic error.','limitations':['Intersection selection by exact-source availability','Historical reconstruction with unavailable information','Compensating errors; not an accuracy ceiling','Overlapping horizons and events are not independent evidence']},indent=2)+'\n')
shutil.copyfile('/tmp/radar-future-flow-exact.log',OUT/'execution.log')
shutil.copyfile('/tmp/radar-future-flow-exact-tests.log',OUT/'tests.log')
print(json.dumps({'exact_audit':dict(counts),'status_counts':status},indent=2))
