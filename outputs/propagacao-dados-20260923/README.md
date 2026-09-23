# Dados observados para o modelo complementar de propagação

Foi preparado um conjunto separado, sem chuva, para o modelo experimental de nível de Muçum a partir dos níveis a montante e das vazões das três usinas. Este preparo não treinou modelos nem alterou produção.

`exact-hour-level-flow.npz` contém **12.969 horas**, de **01/04/2025 00h** a **23/09/2026 08h BRT**, com **11.236 origens** em que as dez variáveis da hora estão presentes. A última origem com todas elas é **23/09/2026 07h BRT**: falta nível exato de Santa Tereza às 08h no recibo utilizado.

As fontes são os arquivos brutos ANA e ONS de `outputs/mucum-propagacao-2026-09-21/raw` e o recibo recente `outputs/mucum-hourly-20260923T084211-0300`. Foram lidos **33 arquivos**. Os hashes originais e os recibos de aquisição puderam ser verificados para **20**; os outros arquivos históricos receberam um hash de conteúdo atual, sem inventar recibo antigo.

## Contrato

- `times`: segundos Unix UTC em grade horária estrita, crescente, com passo de 3.600 segundos.
- Níveis em metros: `86510000:H` (Muçum), `86472000:H` (Linha José Júlio), `86472600:H` (Santa Tereza), `86500000:H` (Passo Carreiro). Cada estação mantém a sua própria régua.
- Vazões em m³/s: `julho:Q`, `julho:I`, `monte:Q`, `monte:I`, `castro:Q`, `castro:I`; `Q` é defluência, `I` afluência. Usinas em série não são somadas como contribuições independentes.
- `received_at:<chave>`: instante real de recebimento do arquivo selecionado, quando conhecido. Não representa o momento de publicação inicial da observação. `NaN` indica recibo desconhecido.
- `source_index:<chave>`: índice em `manifest.json.sources`; `-1` indica ausência.

Os dados são alinhados somente pelo timestamp exato da fonte. Não há interpolação, reaproveitamento da última leitura, preenchimento de faltas ou deslocamento de horário. A API Python `load_dataset(baseline, collections)` devolve `(times, data, metadata)`; em `data`, apenas as dez chaves de nível/vazão são preditores. As demais chaves servem à auditoria.

## Qualidade e restrições verificadas

Foram excluídos níveis cujo indicador ANA não fosse `Dado aprovado`, valores negativos/não finitos e observações posteriores ao seu recibo. Foram rejeitadas **488 observações horárias de nível por qualidade**. Três registros de defluência zero em Monte Claro, contraditos pelos componentes positivos da própria linha ONS, tornaram-se ausentes; não foram substituídos pela soma dos componentes. Demais zeros válidos foram mantidos.

O ONS registra a última observação de cada dia às **23:59**, além das horas 01h a 23h. Esses registros foram preservados nos arquivos brutos e omitidos da matriz de horas exatas; **não foram renomeados para 00h**. Consequentemente, exigir todas as 25 defasagens de 0 a 24h de todas as variáveis simultaneamente deixa zero exemplos históricos elegíveis. O modelo deve comparar defasagens usando pares observados válidos e construir um conjunto esparso de defasagens; preencher a meia-noite alteraria o contrato.

Dados recentes com recibo conhecido substituem revisões anteriores, inclusive quando uma observação antes válida é reprovada. Há 18 alterações de valor nas sobreposições recentes. O ONS apresenta agregados horários/fim de intervalo, enquanto CERAN pode representar uma leitura instantânea. Essa equivalência e a estabilidade das referências verticais não estão certificadas.

Os dados antigos foram baixados retroativamente e podem ter sido revisados depois do instante-alvo. Logo, permitem avaliação retrospectiva por cortes temporais, mas **não comprovam disponibilidade operacional histórica**. Os intervalos de treino/seleção/teste em `availability-audit.json` são uma proposta de inventário; precisam ser congelados antes da seleção do novo modelo. O episódio de 21–23/setembro/2026 fica fora do ajuste. O histórico já foi examinado em experimentos anteriores e não equivale a um teste independente jamais visto.

## Reprodução e testes

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python scripts/hydro_propagation_data.py \
  --baseline outputs/mucum-propagacao-2026-09-21 \
  --collection outputs/mucum-hourly-20260923T084211-0300 \
  --out /tmp/radar-propagation-reproduction

PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python -m unittest discover \
  -s scripts -p 'test_hydro_propagation_data.py' -v
```

A suíte verifica horas exatas, ausência de preenchimento, referência de estação, conversão cm→m, fuso, rejeição de qualidade, zeros contraditórios, 23:59, identidade ONS, duplicatas conflitantes, recebimentos desconhecidos, revisão inválida, integridade do arquivo e exclusão de observações futuras. **14 testes passaram.**
