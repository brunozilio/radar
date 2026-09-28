# Diagnóstico e melhoria experimental do modelo de Muçum — 28/09/2026

## Situação

O modelo público continua `mucum-hydrometry-public-v1`, SHA-256 `8adc838b20fba1ec3edd63db53e4575b0b8df59c22a777ada434ed773fb58c97`. Não foi retreinado nem substituído. A meta de 98% dentro de ±0,50 m por horizonte, inclusive em cheias, permanece não demonstrada.

Os arquivos brutos e os pares da avaliação estão em `outputs/diagnostico-modelo-20260928-evidencias.tar.gz` (SHA-256 `8cc628d6dacea5a80985f3aca7e72e30264e4b7ff984060f6246fed31437ce51`).

Foram capturadas 125 rodadas da API pública e o CSV de nível de Muçum do SGB em `outputs/auditoria-modelo-publico-20260928/`. Dessas, 100 usam o modelo hidrométrico atual. A API expõe chaves de recibo, mas esta captura não verificou a existência dos recibos remotos. O CSV atual não comprova quando cada leitura estava publicada nem se houve revisão ou aprovação ANA na hora da previsão. Os resultados abaixo são diagnóstico retrospectivo, com horas e alvos sobrepostos.

| Horizonte nominal | Pares exatos | MAE | Acertos ±0,50 m | Maior erro |
|---|---:|---:|---:|---:|
| H+2 | 97 | 0,049 m | 97/97 | 0,342 m |
| H+3 | 96 | 0,087 m | 95/96 | 0,599 m |
| H+4 | 95 | 0,134 m | 95/95 | 0,468 m |
| H+5 | 94 | 0,177 m | 89/94 | 0,743 m |
| H+6 | 94 | 0,228 m | 84/94 | 0,816 m |

H+1 não aparece nas rodadas públicas atuais porque o cálculo costuma sair cerca de uma hora depois da referência; o alvo H+1 já venceu. O viés agregado é negativo em todos os horizontes, mas há erros importantes dos dois sinais. O maior erro H+6 da captura foi uma subestimativa de 0,816 m para 28/09 às 13h BRT. Esses dados não satisfazem a exigência de 1.000 previsões por horizonte e dez cheias independentes.

## Experimentos

1. **Correção pelo erro da rodada anterior:** piorou o MAE tanto na parte inicial quanto na parte final da captura. Descartada.
2. **Média dos modelos com e sem defasagens:** diminuiu alguns MAEs, mas piorou o acerto ±0,50 m em partes do episódio recente e não resolveu H+6. Não promovida.
3. **Modelo com duas réguas e eventos de 2024:** receita registrada antes da execução em `docs/candidato-hidrometrico-2026-09-28.md`; avaliação em `outputs/candidato-duas-estacoes-20260928/`. Na comparação pareada do teste, H+6 piorou de 0,213 m para 0,311 m de MAE; no episódio recente, de 0,753 m para 1,014 m. Descartado para os prazos longos. A maior cobertura natural não compensa essa regressão.
4. **Atualização pela leitura local mais recente:** receita congelada em `docs/nowcast-shadow-2026-09-28.md`. O replay em `outputs/avaliacao-nowcast-20260928/` assumiu atraso de 45 minutos do CSV SGB e comparou 451 pares nos mesmos alvos. O MAE caiu de 0,050→0,043 m em H+2; 0,089→0,080 em H+3; 0,136→0,128 em H+4; 0,181→0,176 em H+5; 0,235→0,232 em H+6. Em H+6, os acertos ±0,50 m permaneceram 79/89 e o maior erro subiu levemente de 0,816 para 0,817 m. Só quatro pares tinham alvo ≥7 m em cada horizonte. **Isto não é validação prospectiva.**

## Execução paralela implementada

`scripts/hydro_propagation_live.py` grava `local-nowcast-shadow.json` com a leitura ANA aprovada mais recente, seu recibo, o valor esperado pelo modelo naquele instante e o ajuste limitado a ±0,50 m. A leitura deve ser posterior à referência, anterior à emissão e ter idade máxima de uma hora. Falha da candidata produz registro indisponível e não modifica a previsão pública. `scripts/hydro_projection_archive.py` inclui o documento no pacote imutável da tentativa.

Uma coleta local em 28/09 às 14h14 BRT (`outputs/nowcast-live-sample-20260928/`) recebeu as sete fontes exigidas, calculou o modelo e encontrou leitura ANA aprovada de 13h45, nível 5,39 m. A candidata aplicou +0,061 m. Esse ensaio prova a viabilidade técnica e o contrato de recibo nessa tentativa; não mede o erro futuro.

O código da candidata passou 31 testes Python focados em isolamento da previsão pública, qualidade/tempo da leitura, limite de ajuste, empacotamento e contrato de publicação. O radar passou 74 testes Node, lint e build; o build mantém o aviso anterior de rastreamento amplo de arquivos em `lib/projection-server.ts`.

## Publicação

Em 28/09/2026, a versão Cloudflare `129eab1d-b669-4006-b8da-4d6f6a662ae1` implantou a execução paralela, a remoção da seção de câmeras e as duas correções da auditoria geral. A página pública foi consultada após o contêiner ficar ativo: a seção de câmeras não apareceu e o painel de Muçum continuou presente. A API continuou identificando o mesmo modelo público e SHA-256. A existência de um primeiro arquivo *shadow* no armazenamento remoto após o agendamento ainda precisa de verificação.

## Próxima avaliação

Executar a candidata paralelamente em novas emissões, preservar os recibos de cada tentativa e avaliar por antecedência real, nível ≥7 m, subida, pico e recessão. Registrar indisponibilidade separadamente. Só considerar publicação quando houver ganho prospectivo sustentado em episódios independentes e sem regressão nos erros críticos. Até lá, a interface deve continuar identificando a previsão como experimental.
