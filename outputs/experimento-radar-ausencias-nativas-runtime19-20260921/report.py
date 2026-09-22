import csv,json
from pathlib import Path

p=Path(__file__).resolve().parent
metrics=list(csv.DictReader((p/'evaluation.csv').open()))
rows=list(csv.DictReader((p/'predictions.csv').open()))
training=list(csv.DictReader((p/'training.csv').open()))
differences=list(csv.DictReader((p/'runtime-comparison.csv').open()))
lines=['# Radar: treino com entradas ausentes e avaliação completa','',
       'Referência e candidato foram ajustados no mesmo ambiente operacional atual, com os mesmos parâmetros, fontes e cortes. A única mudança no candidato foi permitir campos de níveis e variações ausentes no treino, usando o tratamento nativo das árvores. Isso inclui variações passadas de Muçum; o nível-base e o alvo de treino continuam obrigatórios.','',
       'A avaliação inclui todos os alvos agendados. A amostra antiga, que exigia os primeiros 24 campos preenchidos, e sua parte excluída são apresentadas separadamente.','',
       '## Todos os pares calculáveis, sem excluir ausência auxiliar','',
       '|Fase|Prazo|Recorte|Modelo|Pares|Acertos ≤0,50 m|MAE (m)|Falhas com alvo|',
       '|---|---|---|---|---|---|---|---|']
for phase in ('validation','test'):
    for h in ('1','6','12'):
        for subset in ('all','level_ge_7m'):
            for family in ('baseline','candidate'):
                r=next(r for r in metrics if (r['phase'],r['horizon_h'],r['subset'],r['population'],r['family'])==(phase,h,subset,'full_schedule',family))
                lines.append(f"|{phase}|{h}|{subset}|{family}|{r['n']}|{r['hits']} ({100*float(r['hit_fraction']):.2f}%)|{float(r['mae_m']):.4f}|{r['failures']}|")
lines+=['','## Efeito da exclusão antiga no teste','',
        '|Prazo|Recorte|População|N|MAE referência|MAE candidato|Acertos referência|Acertos candidato|',
        '|---|---|---|---|---|---|---|---|']
for h in ('1','6','12'):
    for subset in ('all','level_ge_7m'):
        for population in ('complete24','missing24'):
            rs={r['family']:r for r in metrics if (r['phase'],r['horizon_h'],r['subset'],r['population'])==('test',h,subset,population)}
            a,b=rs['baseline'],rs['candidate']
            lines.append(f"|{h}|{subset}|{population}|{a['n']}|{float(a['mae_m']):.4f}|{float(b['mae_m']):.4f}|{a['hits']}|{b['hits']}|")
lines+=['','## Reprodução e limites','',
        'O primeiro ensaio foi interrompido ao detectar diferença com a previsão histórica arquivada. O ambiente antigo preservado (NumPy 2.0.2, scikit-learn 1.6.1) reproduziu exatamente as 1.350 previsões de uma hora; o atual (NumPy 2.5.3, scikit-learn 1.9.1) apresentou diferença máxima de 0,0908 m nesse horizonte. Variar 1/2/4 threads não alterou nenhum resultado dentro de cada ambiente. As acumulações meteorológicas construídas pelos dois procedimentos foram idênticas.','',
        'A nova comparação foi registrada após esse diagnóstico e antes de avaliar o candidato no teste. A referência atual é um novo ajuste, não a previsão arquivada. runtime-comparison.csv preserva todas as diferenças nos 16.113 pares antigos, por prazo; a diferença máxima ao longo dos 12 horizontes foi 1,1784 m. O ensaio interrompido e seus modelos parciais não foram substituídos.','',
        'As árvores mantêm os parâmetros por horizonte escolhidos anteriormente; portanto a fase chamada validation já participou da escolha e não é validação independente. O período test também foi previamente inspecionado. Nenhum resultado desta rodada certifica 98% prospectivos.','',
        'Os cortes originais foram preservados, inclusive a pequena exclusão de alvos que atravessam a fronteira de outubro no treino histórico. O runner operacional usa um corte único posterior. Não houve modificação do runner, emissão de nova previsão, mudança da automação, implantação ou promoção.','',
        'As faltas dos primeiros 24 campos incluem níveis e variações passadas de Muçum, Linha José Júlio, Linha Colombo e Passo Carreiro. Permitir NaNs não inventa observações e não recupera um nível-base ausente. Os atrasos e a disponibilidade das fontes históricas continuam hipóteses não certificadas.','']
(p/'report.md').write_text('\n'.join(lines))
decision=dict(promoted=False,goal_achieved=False,live_issuance=False,
              decision='Do not promote: historical hit-rate gains are mixed across horizons; flood6h worsens154to147hits while flood12h improves75to86. Independent prospective validation remains absent.',
              historical_exact_replay_claim=False,
              runtime_difference_comparisons=len(differences),
              maximum_archived_to_current_difference_m=max(float(r['abs_difference_m']) for r in differences),
              identical_candidate_baseline_availability=all(bool(r['baseline_m'])==bool(r['candidate_m']) for r in rows),
              scope='Fixed Radar-only native-missing training experiment; descriptive historical development.')
(p/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
print(json.dumps(decision,indent=2))
