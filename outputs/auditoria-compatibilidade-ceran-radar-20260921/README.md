# Compatibilidade das entradas CERAN com o candidato Radar

Auditoria local dos arquivos já coletados, sem ajuste de modelos, emissão de previsão ou promoção. Referência analisada: **21/09/2026 às 21h, UTC−3 presumido**. Os arquivos foram efetivamente recebidos às 21h00min28s; esta reconstrução posterior não é uma emissão prospectiva às 21h.

## Comparação com o histórico

Os três HTMLs CERAN preservados têm 48 registros horários contínuos, de 19/09 às 21h a 21/09 às 20h. Os cabeçalhos declaram montante e jusante em metros; o texto original contém “Justante”. Seus hashes conferem com os recibos da coleta.

O CSV ONS preservado termina em 21/09 às 11h. Há **37 timestamps exatamente iguais por usina, totalizando 222 pares de nível: todos coincidem, com diferença zero**. As meias-noites CERAN não foram pareadas com os rótulos 23h59 ONS. As demais leituras sem correspondência continuam no CSV de comparação. Isso comprova concordância numérica nesse intervalo restrito, não identidade de sensores, datum, política de revisão ou fuso documentado.

## Disponibilidade e faixas do treino

A regra histórica foi aplicada literalmente: fonte mais recente até origem−60min, expiração após 90min adicionais, diferenças de 1h e inclinações de 3h/6h da série atrasada. O vetor das 21h tem **24/24 valores finitos**, reconstruídos também por cálculo independente com as leituras horárias exatas. A fonte mais recente usada é das 20h; as diferenças dependem de leituras anteriores. Recebê-las nesta coleta não comprova sua hora original de publicação.

**17 dos 24 campos estão fora dos mínimos/máximos usados no treino de cada um dos 12 modelos da fase test.** Nos 12 modelos da fase validation são 18 campos. As faixas são calculadas nas linhas efetivamente admitidas no treino de cada horizonte, não em todo o acervo ou no período de avaliação. Não houve recorte, normalização adaptativa ou alteração dos modelos.

Exemplos da fase test, iguais nos 12 horizontes:

| Campo | Valor reconstruído | Faixa de treino |
|---|---:|---:|
| Julho, nível jusante | 82,10 m | 66,75–80,11 m |
| Monte Claro, nível montante | 153,94 m | 146,80–152,44 m |
| Castro Alves, nível montante | 246,96 m | 236,97–243,94 m |
| Castro Alves, inclinação de montante em 6h | 0,5133 m/h | −0,1067–0,2200 m/h |

Isso sinaliza entradas fora do domínio empírico de treino, sem fornecer por si só uma medida de erro da previsão. Tampouco estar dentro dos limites garantiria boa previsão.

Todos os **24 conjuntos de treino têm zero linhas com ausências nas novas colunas**. O tratamento de NaN da biblioteca permite inferência, mas esse experimento não treinou com exemplos de ausência nesses campos. A cobertura desta coleta não resolve o desempenho em futuras falhas de fonte.

## Revisão observada

Entre os snapshots das 18h e 21h, foram comparados 270 pares de nível com timestamp exato. Uma leitura mudou: **Castro Alves, montante de 21/09 às 17h, de 246,22 para 246,17 m (−0,05 m)**. O jusante correspondente permaneceu 156,18 m. Essa leitura está depois do fim do CSV ONS; não contradiz os 222 pares idênticos. As duas versões e horários de recebimento permanecem em `snapshot-revisions.csv`. A auditoria não infere a causa da revisão nem a usa para substituir fontes antigas.

## Resultado e reprodução

O mapeamento nominal e a cobertura da coleta são compatíveis com uma futura avaliação local do candidato, mas as entradas fora das faixas, revisões, ausências não representadas e referências ainda não certificadas precisam acompanhar qualquer avaliação. **Nenhum candidato foi promovido ou emitido e a meta de 98% não foi demonstrada.**

`audit.py` reproduz a comparação, confirma hashes de fontes/modelo, recompõe o vetor de 24 campos, reconstrói os 24 memberships e confere suas contagens com o experimento congelado. Ele não chama treinamento nem executa HGE. Executar na raiz do projeto:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python outputs/auditoria-compatibilidade-ceran-radar-20260921/audit.py
```

O nome histórico do ambiente virtual não muda o escopo somente Radar. `audit.json` registra hashes das entradas; `artifact-hashes.json` registra os artefatos desta auditoria. A revisão independente do agente confirmou os 222 pares, a revisão de 5 cm, o vetor reconstruído diretamente dos HTMLs e todos os 576 registros de limites. Confirmou também zero linhas com faltas nos 24 conjuntos de treino. Na fase test são 16 campos acima do máximo e um abaixo do mínimo; na validation, 17 acima e um abaixo. Nenhum arquivo foi alterado pelo agente.
