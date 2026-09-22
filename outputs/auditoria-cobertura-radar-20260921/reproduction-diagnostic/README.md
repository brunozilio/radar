# Discrepância do controle Radar — diagnóstico sem novo treino

O controle interrompeu em 1h na origem **23/07/2026 20:00 UTC−3**, com diferença de **0,001403385642978705 m** em relação à previsão histórica preservada. Isso continua sendo falha de reprodução; nenhuma tolerância foi relaxada e nenhum candidato de teste foi aceito. O log original foi copiado para `sources/radar-native-missing.log`.

## Hipóteses verificadas

**Membership e ordem descartados como causa neste snapshot.** A expressão histórica `np.r_[tr,va]` e o `training_masks` novo produzem exatamente os mesmos índices, na mesma ordem, nos 12 horizontes. Em 1h há 9.524 linhas: 3.633 de treino inicial e 5.891 de validação. Os pesos são 9.417 amostras com peso 1, 104 com peso 3 e 3 com peso 5. Índices, deltas e pesos têm hashes em `membership-verification.json`.

**Há diferença concreta de implementação do estimador entre os runtimes.** Os diretórios citados pelo relatório histórico local (`hydro_12h_report.py:125`; também `hydro_model.py:2`) ainda existem e contêm:

| Biblioteca | Diretórios históricos citados | Ambiente novo |
|---|---|---|
| Python importado nesta auditoria | 3.9.6 | 3.12.14 |
| scikit-learn | 1.6.1 | 1.9.1 |
| NumPy | 2.0.2 | 2.5.3 |
| SciPy | 1.13.1 | 1.18.1 |
| joblib | 1.5.3 | 1.6.0 |

O construtor de HistGradientBoostingRegressor tem os mesmos defaults nas duas versões inspecionadas. Porém:

- Na **1.6.1**, o HGB chama `_bin_mapper.fit_transform(X)` sem pesos, e `_find_binning_thresholds` usa percentis `method="midpoint"`.
- Na **1.9.1**, chama `_bin_mapper.fit_transform(X, sample_weight=sample_weight)`; os limites usam percentis ponderados quando há pesos. O caso não ponderado também passa a usar `averaged_inverted_cdf`.

Como o Radar fornece pesos não uniformes, igualdade de dados, seed e hiperparâmetros não implica o mesmo ajuste entre essas versões. É uma causa concreta plausível, mais específica que ruído numérico genérico; **esta auditoria não demonstra que ela explica integralmente os 0,001403 m**, pois não executou ajuste em nenhum ambiente. O teste com runtime antigo fica com o responsável pelo experimento.

O ambiente antigo pôde ser importado com `PYTHONPATH=/tmp/radar-hydro-libs:/tmp/radar-plot-libs /usr/bin/python3`. Isso não certifica sozinho qual processo executou o lote das 15h: não foi localizado recibo original de runtime desse lote. A documentação local é um apontador de procedência, não prova de execução. Também há diferença de threads: a leitura atual sem limite mostra 18 no ambiente antigo, enquanto o novo script limita a 2; o número histórico efetivo não foi determinado.

## Preservação e limites

`sources/` guarda cópias do código relevante, das duas implementações de binning/HGB e dos logs/documentos citados. `binning-source-evidence.json` identifica linhas e hashes. `runtime-older-libs.json` e `runtime-new.json` registram importações atuais, versões e threadpools. `constructor-defaults.json` conserva a comparação de defaults. `verify_runtime.py` reconstrói apenas features e máscaras com funções puras extraídas por AST; não importa módulos operacionais nem treina modelos.

A comparação dos 60 preditores meteorológicos versus o algoritmo histórico está sendo feita separadamente pelo responsável. Nenhum dado original, modelo ou script operacional foi alterado. Nenhum HGE foi executado. Os dois modelos parciais de validação não certificam a reprodução do modelo de teste que falhou antes de ser salvo.
