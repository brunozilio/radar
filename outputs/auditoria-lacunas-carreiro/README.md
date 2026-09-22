# Auditoria das lacunas de vazão — Passo Carreiro 86500000

Auditoria local de 21/09/2026, sem downloads, preenchimento ou alterações no pipeline. Convenção temporal UTC−03 mantida do parser congelado; não constitui nova verificação do contrato histórico da ANA. Nível bruto em cm, normalizado em m; vazão em m³/s.

## Conclusão

As 4.122 falhas em 344 origens são explicadas por 512 instantes distintos de entradas ausentes do Carreiro: 425 sem registro exato e 87 com vazão vazia na fonte. Todas as falhas têm ao menos uma dessas dependências. Não encontramos perda de vazão aprovada causada pelo parser no período avaliado, nem uma versão preservada que repare essas lacunas.

Na grade de 15min de 01/07/2026 00:00 até 21/09/2026 00:00 exclusivo há 1.031 slots sem vazão: 855 sem registro exato e 176 com campo VazaoFinal vazio. Esses slots não são o número de previsões falhadas: kernels, âncora, base atrasada e múltiplos horizontes propagam cada ausência. São 25 intervalos contíguos, discriminados em missing-intervals.csv. O prefixo de 25h acrescenta 98 slots, chegando a 1.129.

## Coocorrência nível/vazão

- 23/07/2026 10:45–19:00: 34 registros de 15 minutos com nível aprovado e vazão vazia; CQ_VazaoFinal também vazio. Nível entre 4,648 e 5,172m. São 17 instantes usados como dependências ausentes do experimento (grade horária e base de meia hora). A existência de nível não autoriza gerar vazão por curva não documentada.
- 14/08/2026 12:45–17:15: 19 slots sem vazão; 16 têm nível bruto marcado Dado suspeito e 3 não têm nível numérico. Não são níveis aprovados descartados indevidamente.
- Dos 176 registros com vazão vazia, 126 também têm nível vazio, 34 têm nível aprovado e 16 nível suspeito. Nenhum deles tem uma vazão numérica aprovada escondida no campo original.

## Intervalos e cadência

- 01–08/07: em cada dia faltam 94 dos 96 slots; o arquivo preserva registros pontuais de vazão às 07h e 17h. Não é justificável transformar essa cadência em telemetria contínua por preenchimento.
- 09/07: 37 slots sem registro e 57 registros de vazão vazia.
- 10/07 até 16:30: 66 registros de vazão vazia; as leituras pontuais aprovadas permanecem.
- 15/07 16:45 até 16/07 09:30: 66 slots sem registro exato, entrecortados pelas leituras pontuais existentes.
- Restantes: o intervalo de 23/07 e o de 14/08 acima.

## Parser e versões

A reconstrução independente da ordem ana-86500000-2025.xml → ana-86500000.xml → ana-86500000-latest.xml reproduziu exatamente normalized-86500000.npz. A aplicação posterior do fresh do snapshot15h reproduziu exatamente raw:86500000:Q no telemetria-latencia.npz. Nenhuma dessas leituras chamou o parser original que pode gravar cache.

Em toda a grade congelada, incluindo treino e o fim de 21/09, há 2.183 slots sem Q: 1.966 sem registro, 207 com campo vazio e 10 rejeitados por CQ=Dado suspeito. Estes dez são anteriores a julho/2026 e estão listados com valor/horário/linha em missing-quarter-hours.csv. Não há rejeição por número negativo ou inválido entre as lacunas examinadas.

Não há diferença de valores ou CQ de nível/vazão nos timestamps compartilhados dos XML examinados. Os arquivos normalizados posteriores só recuperam dois slots do frozen15h: 21/09 14:45 e 15:00, fora da avaliação. Isso reflete ampliação da cobertura temporal e não correção das lacunas de julho/agosto.

Limite do código existente: load_ana mantém o último valor finito aprovado quando uma versão posterior no lote vier vazia/suspeita; o merge fresh substitui inclusive por ausência. Não apareceu conflito desse tipo nas versões preservadas desta estação. Não alteramos a política.

## Evidências e próximo passo

- summary.json: contagens, comparação dos arquivos normalizados posteriores e manifesto SHA-256 de cada entrada consultada.
- missing-quarter-hours.csv: todos os slots ausentes do frozen, classificação, H/Q e QC brutos, caminho e linha inicial do registro XML.
- missing-intervals.csv: intervalos na grade completa, na avaliação e com prefixo.
- missing-input-dependencies.csv: 512 instantes ausentes que efetivamente afetam o experimento, contagem de pares/origens e causas sobrepostas.
- audit.py: receita local reprodutível; grava somente nesta pasta.

Próximo lote possível: solicitar/obter do operador ANA/SGB registros originais de vazão ou curva-chave oficial de Passo Carreiro com vigência específica de julho/2026, pontos de medição, referência da régua e domínio válido. Esta auditoria não procurou nem ajustou curva; usar nível como preditor separado é uma hipótese nova, que exigiria protocolo e avaliação próprios. A correção matemática dos pesos zero não recupera observações faltantes.
