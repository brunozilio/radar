# Histórico de cheias de Muçum — auditoria

Dados oficiais ANA preservados em XML. Níveis aprovados convertidos de cm para m; suspeitos separados. Nenhuma interpolação, treino ou divisão treino/teste executada.

| Janela | Registros | Níveis aprovados | Suspeitos | Sem registro na grade de 15 min | Nível ausente/outro QC |
|---|---:|---:|---:|---:|---:|
| 2020-jun-jul | 4800 | 4686 | 91 | 0 | 23 |
| 2024-mar-mai | 8832 | 8832 | 0 | 0 | 0 |

Os horários originais não informam fuso. A coluna UTC usa hipótese explícita UTC−03, ainda não verificada; não integrar com outras fontes até confirmar. O datum, zero da régua, relocação, curvas-chave válidas e seções transversais continuam pendentes. Dado aprovado pela fonte não demonstra datum consistente entre anos.

As janelas são lotes para auditoria, sem atribuição a treino ou teste. Os primeiros meses permitem investigar aquecimento, mas nenhuma adequação ao treino foi concluída. A grade de 15 min é nominal para medir cobertura; ausências não são zeros.

Cada pasta contém summary.json (variável/QC), levels-approved.csv, levels-suspect.csv, levels-unavailable_or_other_qc.csv, gaps-15min.csv e rows-all-qc.jsonl. Os manifestos individuais registram URL, instante, resposta, bytes e hash SHA-256.

Próxima fonte em caso de falha/lacuna: [Hidroweb da estação](https://www.snirh.gov.br/hidroweb/serieshistoricas?codigoEstacao=86510000). Para curvas e perfis: [API ANA oficial](https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html), com acesso autorizado. Não foi contornada autenticação. O endpoint legado tem aviso de descontinuação; manter os dados baixados imutáveis.

Reprodução sem rede: `python3 scripts/hydro_collect_flood_history.py --offline`. A execução padrão reutiliza apenas cache com URL e hash verificados.
