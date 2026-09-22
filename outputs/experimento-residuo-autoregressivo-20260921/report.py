import csv
import json
from collections import Counter
from pathlib import Path

p=Path(__file__).resolve().parent
metrics=list(csv.DictReader((p/'evaluation.csv').open()))
rows=list(csv.DictReader((p/'predictions.csv').open()))
counts={family:dict(Counter(r[family+'_status'] for r in rows)) for family in ('reference','julho_levels')}
decision=dict(status_counts=counts,promoted=False,goal_achieved=False,
              conclusion='Some historical improvements, but mixed hit rates and three new negative-flow failures per family. No operational promotion.',
              next_research='Separate reconstruction-residual prediction from upstream forecast errors; any physical constraint requires a new preregistered experiment, not hiding the three failures.')
(p/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
lines=['# Correção autorregressiva do resíduo de vazão','',
       '12 modelos ridge com alpha 1000 fixo, quatro resíduos anteriores à origem e alvos de treino estritamente anteriores a julho/2026. Avaliação histórica de desenvolvimento já inspecionada. Nenhuma promoção.','',
       '|Prazo|Recorte|Modelo|N|Acertos ≤0,50 m|MAE (m)|Falhas com alvo|',
       '|---|---|---|---|---|---|---|']
for h in ('1','6','12'):
    for subset in ('all','level_ge_7m'):
        for model in ('baseline','candidate'):
            r=next(r for r in metrics if r['horizon_h']==h and r['subset']==subset and r['model']==model and r['family']=='julho_levels' and r['population']=='individual')
            lines.append(f"|{h}|{subset}|{model}|{r['n']}|{r['hits']} ({100*float(r['hit_fraction']):.2f}%)|{float(r['mae_m']):.4f}|{r['failures']}|")
lines+=['','As métricas acima usam a amostra individual: no horizonte de 12 horas o candidato perde duas previsões por vazão negativa. evaluation.csv também preserva a comparação na amostra comum, sem eliminar as falhas da cobertura.','',
        f'Contagens por família: {counts}.','',
        'O alvo aprendido é Q reportada menos uma reconstrução com chuva e montante posteriormente conhecidos. Ele não é o erro completo da previsão emitida. Ao aplicar a correção a vazões previstas, os erros de montante e chuva permanecem.','',
        'Os componentes congelados foram ajustados no período anterior a julho e os resíduos de treino são internos a esse ajuste, não previsões fora de amostra. O teste posterior não entra no ajuste ridge, mas já havia sido examinado em outras experiências.','',
        '“Finalizado” indica uma reconstrução retrospectiva, não dados exclusivamente observados: a chuva inclui preenchimento da área sem cobertura com previous_day1, e o montante usa a grade histórica existente e proxy regional Carreiro para lacunas. Esses efeitos também entram nos estados anteriores. A ressalva pós-revisão está preservada em documentation-clarification.json; protocolo e código executados permanecem intactos.','',
        'Três vazões corrigidas negativas por família foram mantidas como falhas (11 horas: uma; 12 horas: duas). Não houve corte em zero nem fallback escolhido pelo sinal. Entradas residuais ausentes retornam exclusivamente à correção original; entradas-base ausentes permanecem ausentes.','',
        'A âncora foi reproduzida com diferença zero em todas as linhas comparáveis. 126 testes passaram, incluindo exclusão de labels no corte, invariância a resíduos futuros e preservação do fallback/falha. Esses testes não comprovam 98% prospectivos.','']
(p/'report.md').write_text('\n'.join(lines))
print(json.dumps(decision,indent=2))
