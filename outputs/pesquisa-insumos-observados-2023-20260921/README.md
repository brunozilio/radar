# Insumos observados de 29/08 a 04/09/2023 — levantamento Radar

**Existe chuva observada nos cinco postos de maior peso, mas o lote é parcial: Santa Tereza e Passo Carreiro retornaram ausência explícita, e duas estações importantes de chuva param durante 04/09.** Não foi montada matriz nem treinado modelo.

Foram feitas exatamente **8 requisições GET**, todas HTTP200, entre 22/09/2026 01:40:28 e 01:40:32 UTC (21/09 à noite em UTC−3). Respostas completas totalizam 1.584.250 bytes. O endpoint público é DadosHidrometeorologicosGerais da ANA; parâmetros e URL integral estão nos sidecars e source-manifest.json. Nenhuma consulta de Muçum, ONS ou meteorologia foi repetida.

## Seleção e reaproveitamento

Lidos primeiro os relatórios existentes de setembro/2023 e de viabilidade histórica. O inventário de XMLs dos oito postos e dos caches normalizados não encontrou registros da janela solicitada reutilizáveis; os oito caches têm zero timestamps nessa janela. O acervo Muçum/ONS existente continua referenciado, sem download ou alteração. Arquivos e hashes consultados constam de collection-plan.json e prior-evidence.json.

Seleção deduplicada: três níveis auxiliares mais o maior peso de cada região, obtido de chuva-pesos.json; nenhum peso foi modificado.

| Uso | Estação | Peso original na região | Registros | Chuva aprovada | Cadência predominante |
|---|---|---:|---:|---:|---|
| Alto Antas | 86060010 | 0,170250 | 168 | 168 | 1 hora |
| Prata-Turvo | 86125050 | 0,303838 | 168 | 168 | 1 hora |
| Tainhas | 86160000 | 0,609290 | 636 | 631 | 15 minutos |
| Baixo Antas | 86450000 | 0,286127 | 147 | 147 | 1 hora |
| Carreiro | 86479000 | 0,517941 | 154 | 154 | 1 hora |
| Nível Linha José Júlio | 86472000 | — | 672 | 672 | 15 minutos |
| Nível Santa Tereza | 86472600 | — | 0 | 0 | Sem dados |
| Nível Passo Carreiro | 86500000 | — | 0 | 0 | Sem dados |

Chuva aprovada significa valor numérico com CQ Dado aprovado; não equivale a uma nova certificação física. Nenhuma chuva negativa, suspeita ou acima do limite de 150 mm do parser atual foi encontrada nos registros presentes. Valores brutos permanecem nos XMLs/JSONL; nenhuma ausência foi convertida em chuva zero.

## Níveis auxiliares e QC

- **86472000:** 672/672 níveis aprovados de 15 minutos, sem vazios ou suspeitos; máximo reportado 2.773 cm. São valores reportados, sem nova validação de referência vertical.
- **86472600 e 86500000:** XML com Error: Sem dados para esta estação no período solicitado. HTTP200, não falha de transporte nem descarte do parser. Não há linhas de nível ou chuva para normalizar.
- Na estação de chuva **86160000**, os níveis incidentais têm 621 aprovados, 11 suspeitos e quatro vazios. Suspeitos de 04/09 13h30–16h, preservados; essa estação não substitui automaticamente nenhum nível auxiliar.
- Na estação de chuva **86479000**, existe nível reportado **−222 cm, CQ Dado aprovado, em 04/09 09h**. Preservado como achado; o parser atual que exige nível não negativo rejeitaria esse valor. Não é motivo para inventar correção ou invalidar automaticamente a chuva simultânea.
- Em **86060010**, NivelFinal está vazio nos 168 registros apesar de CQ Dado aprovado. A chuva, por sua vez, tem 168 valores numéricos aprovados. QC sozinho não comprova disponibilidade do campo.

## Cadências e lacunas de chuva

- **86060010 e 86125050:** 168/168 timestamps horários completos, de 29/08 00h a 04/09 23h. Não comparar suas contagens com 672 slots de 15 minutos.
- **86160000:** faltam 36 registros de 15 minutos, de 29/08 00h a 08h45. A série inicia às 09h. Nos 636 registros presentes, cinco chuvas vazias de 29/08 11h a 12h. Depois há chuva aprovada até 04/09 23h45.
- **86450000:** falta 01/09 16h e, no dia do evento, **04/09 04h–23h**. Última chuva às 03h. São 21 timestamps ausentes em uma grade horária de 168.
- **86479000:** faltam **04/09 10h–23h**, 14 timestamps horários. Última chuva às 09h.
- **86472000:** chuva e timestamps completos, 672/672.

Não há timestamps duplicados nem registros fora da janela nos dados presentes. As distribuições de intervalos, fases de relógio e listas de lacunas estão em coverage.json. A cadência modal é diagnóstico do arquivo, não contrato documental do intervalo acumulado de ChuvaFinal; o integrador exige revisão de cobertura temporal antes de qualquer uso futuro.

## Consequência para um eventual candidato de 120 campos

Há dados observados úteis para continuar a pesquisa, mas **este levantamento não cobre as 27 estações de chuva**. Mesmo se todas as amostras presentes tivessem cobertura temporal completa, seus pesos somados atingiriam apenas 0,367052 em Baixo Antas, 0,318763 em Prata-Turvo e 0,278327 em Alto Antas, abaixo do limiar regional atual de 0,5. Carreiro poderia atingir 0,527301 e Tainhas 0,841530 antes das perdas de cobertura. Esses números são tetos espaciais da amostra, não acumulados ou coberturas observadas de janelas.

Portanto, não é válido tratar a coleta das maiores estações como chuva regional completa, renormalizar pesos silenciosamente ou imputar a chuva ausente. O próximo lote, se autorizado, precisaria das demais estações com pesos positivos, reaproveitando os oito arquivos atuais e mantendo lacunas; só depois caberia reconstruir janelas observadas e avaliar cobertura. Um modelo de 120 campos seria uma família distinta do Radar de 180 campos com NWP, exigindo controle comparável e protocolo próprios.

O filtro original complete24 não admitiria essas origens com Santa Tereza e Carreiro totalmente ausentes; um eventual tratamento nativo de faltas precisaria permanecer explícito. A disponibilidade de níveis aprovados de Muçum no pico não mudou: conforme acervo anterior, o último aprovado antes da interrupção é 04/09 19h30. Não foi inserida a marca retrospectiva nem tratada como alvo horário.

## Limites e integridade

Datas/horas originais sem fuso são preservadas. UTC−3, latência histórica, continuidade de régua e comparabilidade entre regimes permanecem hipóteses ou pendências; o lote não certifica emissão prospectiva. O evento já foi inspecionado e não constitui holdout novo. Não foram coletadas nem substituídas previsões meteorológicas; reanálise e chuva futura não entram neste levantamento.

collect.py limita-se aos oito pedidos, com sidecar anterior impedindo repetição automática; audit.py apenas lê as respostas e gera inventário. raw/ contém XMLs integrais e sidecars URL/headers/coleta/hash; stations/ contém todos os registros/QC sem preenchimento. source-manifest.json, coverage.json, prior-evidence.json e artifact-hashes.json registram procedência e integridade.

Nenhum arquivo anterior, modelo ou pipeline foi alterado; nenhum treino, execução HGE/ARNO, promoção ou mensagem externa ocorreu.
