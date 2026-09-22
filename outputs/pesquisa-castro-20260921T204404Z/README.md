# Castro Alves: obras e interpretação operacional

Pesquisa delimitada em 21/09/2026, com três fontes primárias novas preservadas. Este lote é documentação candidata, fora do treino, das previsões e do placar. Nenhuma alteração de modelo foi feita.

## Evidência nova

A [nota CERAN de 06/07/2026](https://ceran.com.br/news/obras-na-barragem-da-uhe-castro-alves-ultrapassam-80-de-execucao/) informa avanço superior a 80%, com principais intervenções estruturais concluídas e atividades complementares ainda em andamento. É atualização posterior aos 50% de maio já arquivados. Descreve situação na publicação; não confirma conclusão total ou regime de setembro.

A [nota CERAN de 01/10/2025](https://ceran.com.br/news/ceran-realiza-obra-na-barragem-da-uhe-castro-alves/) previa execução na estiagem, preservação da vazão remanescente e ausência de impacto esperado nas vazões/geração. Trata-se de expectativa anterior às obras, não medição do efeito realizado.

A [LPIA FEPAM 00424/2025, hospedada pela CERAN](https://ceran.com.br/wp-content/uploads/2025/09/Licenca-Previa-e-de-Instalacao-para-Alteracao-no-424-2025.pdf), folhas 1–3, registra:

- Reforço sem alteração permanente da cota da soleira e níveis operacionais; adequação da superfície hidráulica do vertedouro e ombreiras até 250 m.
- Deplecionamento temporário de até 3 m durante a obra, com cota mínima de até 237 m relativa ao nível do mar e comando remoto (item 1.4.5.5).
- Conduto temporário de aproximadamente 260 m para vazão remanescente e ensecadeira a jusante. Vazão remanescente cadastrada: 17 m³/s, a manter integralmente.
- Vazão de projeto de 12.043 m³/s para TR 10.000 anos: parâmetro de projeto, não teto físico nem intervalo de confiança.
- Validade impressa 12/09/2025–12/09/2026. Renovação não verificada; não inferir irregularidade ou situação vigente a partir desta cópia.

A folha 2 foi renderizada e conferida visualmente, inclusive item 1.4.5.5. O endereço `/storage/` retornou 404; o link `/wp-content/uploads/` da página pública de licenciamento funcionou. Ambos constam do manifesto, sem esconder a falha.

## Implicação diagnóstica e limites

É hipótese, não resultado: mudanças temporárias de armazenamento podem alterar a relação entre afluência e defluência; alterações hidráulicas podem exigir curvas e metadados por período. O acervo prévio ONS define afluência por balanço, e não necessariamente por sensor direto. Juntar essa semântica à licença justifica investigar o regime operacional; não prova que as obras causaram a subida atual ou o viés/extrapolação do modelo.

Nenhuma fonte localizada nesta busca delimitada identifica manobra, cota efetivamente praticada, curva de descarga vigente ou boletim específico de 21/09/2026. A consulta direcionada ao ONS não retornou documento novo pertinente. Não há base para corrigir vazões, subtrair 3 m das séries ou mudar PET/tau. Não foi coletada nova série observada.

Próximo passo útil de pesquisa: buscar relatório de conclusão/atualização de licença, datas efetivas de deplecionamento e recomposição e curvas de descarga/volume por vigência. Depois cruzar, fora do ajuste, níveis, afluência e defluência com esses regimes; manter previsões sinalizadas e erradas no placar.

## Metadados e qualidade

- URLs, coleta UTC real, status HTTP, cabeçalhos relevantes, bytes e SHA-256: `source-manifest.json`.
- Unidades: m, m³/s, percentual de execução e datas civis conforme cada fonte. Não há série horária neste lote nem transformação de fuso. Horário impresso na licença não informa offset; permanece literal.
- Datum: SIRGAS 2000 explicitado para coordenadas geográficas da licença. Isso não identifica datum altimétrico da cota; a expressão nível do mar não basta para conciliar a régua ANA Muçum. Nenhum zero de régua foi inferido.
- Qualidade: notícias são declarações da operadora; licença é documento de projeto/autorização, não registro da execução; assinatura digital não foi validada criptograficamente nesta rodada. Metadados de observação, revisão e incerteza quantitativa não aplicáveis às notícias e ausentes para efeitos operacionais.
- Acesso: fontes públicas, sem credenciais. Notícias exibem copyright CERAN; não foi identificada licença aberta de reutilização. PDF é documento público emitido pela FEPAM hospedado pela operadora; licença específica de redistribuição não identificada. Preservação local para auditoria, sem republicação.
- Lacunas: execução real das condições; conclusão/renovação; curva hidráulica por período; timestamps de manobras; medições ou estimativas afetadas. Nenhuma interpolação ou preenchimento foi realizado.

Busca para não duplicar: `site:ceran.com.br "Castro Alves" "2026" obras comportas`, `site:ons.org.br "Castro Alves" "2026" "obras"`, `site:ceran.com.br "Castro Alves" "setembro" "2026"`. Lidos antes: `outputs/historico-vazoes-ceran/README.md`, `operational-context.md`, `source-manifest.json`.
