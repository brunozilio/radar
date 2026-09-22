import csv,json
from pathlib import Path

p=Path(__file__).resolve().parent
metrics=list(csv.DictReader((p/'evaluation.csv').open()))
rows=list(csv.DictReader((p/'predictions.csv').open()))
lines=['# Radar com níveis de reservatórios','',
       '24 candidatos foram treinados com 204 preditores: os 180 originais mais os 24 níveis e variações de montante/jusante de 14 de Julho, Monte Claro e Castro Alves. A referência permaneceu congelada; o candidato manteve seus índices de treino, pesos e parâmetros. Não houve componente HGE.','',
       '|Fase|Prazo|Recorte|Modelo|N|Acertos ≤0,50 m|MAE (m)|Máximo (m)|',
       '|---|---|---|---|---|---|---|---|']
for phase in ('validation','test'):
    for h in ('1','6','12'):
        for subset in ('all','level_ge_7m'):
            for family in ('baseline','candidate'):
                r=next(r for r in metrics if (r['phase'],r['horizon_h'],r['subset'],r['population'],r['family'])==(phase,h,subset,'full_schedule',family))
                lines.append(f"|{phase}|{h}|{subset}|{family}|{r['n']}|{r['hits']} ({100*float(r['hit_fraction']):.2f}%)|{float(r['mae_m']):.4f}|{float(r['max_abs_m']):.4f}|")
changes=[]
for phase in ('validation','test'):
    for h in map(str,range(1,13)):
        for subset in ('all','level_ge_7m'):
            rs={r['family']:r for r in metrics if (r['phase'],r['horizon_h'],r['subset'],r['population'])==(phase,h,subset,'full_schedule')}
            a,b=rs['baseline'],rs['candidate']
            changes.append(dict(phase=phase,horizon_h=int(h),subset=subset,n=int(a['n']),
                                hit_change=int(b['hits'])-int(a['hits']),mae_change_m=float(b['mae_m'])-float(a['mae_m']),
                                maximum_error_change_m=float(b['max_abs_m'])-float(a['max_abs_m'])))
with (p/'changes.csv').open('w') as s:
    w=csv.DictWriter(s,fieldnames=list(changes[0]));w.writeheader();w.writerows(changes)
lines+=['','Todos os 102.084 agendamentos anteriores estão preservados. evaluation.csv contém cada prazo, as falhas de cobertura e os subconjuntos com/sem os primeiros 24 campos preenchidos; changes.csv contém todas as diferenças por horizonte.','',
        'Houve ganhos nos prazos longos nas duas fases, mas não em todos os recortes. No teste de cheia, 6 horas teve 154→158 acertos e 12 horas 75→84, em 236 pares por prazo; 2 horas perdeu três acertos. Na fase validation, a cheia de 12 horas passou 8→11/28 acertos, enquanto 4 horas perdeu um. Não houve seleção posterior de prazos para substituir partes da previsão operacional.','',
        'O treino continua com o filtro original dos primeiros 24 campos completos; a mudança de política de treino testada anteriormente não foi incorporada a este candidato. A inferência e a avaliação incluem as origens com campos ausentes, desde que haja nível-base de Muçum.','',
        'Os níveis dos reservatórios mantêm seus próprios referenciais. Não foram convertidos em volume, subtraídos entre estações ou tratados como estimativas de vazão física. Os registros anômalos documentados permanecem no acervo.','',
        'A disponibilidade é uma hipótese histórica: atraso de 60 minutos mais vencimento de 90 minutos após a consulta atrasada, sem reposicionar o registro de 23h59. Isso admite idade total de até 150 minutos na origem, não apenas 90; a maior idade efetivamente aceita foi 121 minutos. Ausência no registro mais novo permanece ausência. Não há comprovação de publicação do dado naquele instante.','',
        'São períodos de desenvolvimento já inspecionados; a fase validation também participou da escolha anterior dos parâmetros da referência. Não houve promoção, atualização do runner, emissão operacional, deploy ou alegação de 98% prospectivos.','']
(p/'report.md').write_text('\n'.join(lines))
decision=dict(promoted=False,live_issuance=False,goal_achieved=False,changes=changes,
              reason='Descriptive historical experiment. Promotion requires independent event validation and prospective evidence, regardless of aggregate improvements here.')
(p/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
print(json.dumps({'promoted':False,'changed_metric_groups':len(changes)}))
