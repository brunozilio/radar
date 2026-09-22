# Semântica e proposta de QC das vazões ONS/CERAN

Pesquisa delimitada em21/09/2026. Acervo primário reutilizado com verificação de hashes; nenhum download anual ou nova coleta de série. Nenhum script, dado, modelo ou teste foi alterado. As fontes copiadas em `sources/`, URLs, datas conhecidas de coleta e SHA-256 estão em `source-manifest.json`. A pesquisa adicional pública não localizou contrato CERAN de fechamento nem significado especial para9999.

## Evidência primária confirmada

A [rotina ONS RO-AO.BR.02, revisão08](https://www.ons.org.br/%2FMPO%2FDocumento%20Normativo%2F4.%20Rotinas%20Operacionais%20-%20SM%205.13%2F4.3.%20Rotinas%20P%C3%B3s-Opera%C3%A7%C3%A3o%2F4.3.2.%20Apura%C3%A7%C3%A3o%20de%20Dados%2FRO-AO.BR.02_Rev.08.pdf), vigência02/07/2024, pp.3–5, define:

- `Qdef = Qtur + Qvert + Qoutras`, vazões em m³/s.
- Qoutras reúne restituições por caminhos distintos das turbinas/vertedouro. Transferência entre reservatórios é contabilizada separadamente.
- Vazão vertida não turbinável é parcela do vertimento: não somá-la novamente à defluência.
- Afluência resulta de balanço com defluência, transferência e variação de armazenamento. Não exigir `I=Q`, nem `I≥Q`.
- Horário oficial de Brasília; disponibilização após fechar a hora. A rotina descreve consistência em etapas e remete à NT076/2005R2; não fornece aqui tolerância numérica geral para o fechamento.

O [catálogo horário ONS](https://dados.ons.org.br/dataset/dados_hidrologicos_ho) distingue essa exportação dos produtos consistidos: dados dos agentes, sujeitos a lacunas e revisões, sem validação ONS assegurada. “Consolidados” no título descritivo do PDF do dicionário não elimina essa ressalva do catálogo. A atualização periódica do portal não prova quando cada registro foi originalmente disponibilizado.

O [dicionário de06/06/2024](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/dados_hidrologicos_ho/DicionarioDados_DadosHidrologicosHorarios.pdf), pp.1–2, admite:

| Campo | Nulo | Zero | Negativo |
|---|---|---|---|
| Afluente | sim | sim | sim |
| Defluente | sim | sim | não |
| Turbinada | sim | sim | não |
| Vertida | sim | sim | não |
| Outras estruturas | sim | sim | não |
| Transferida | sim | sim | sim |
| Vertida não turbinável | sim | sim | não |

Consequências: **zero não significa ausência**; não converter nulo em zero; afluência negativa não pode ser rejeitada alegando proibição no esquema ONS. O dicionário define hora-fim (01h representa a hora precedente), sem especificar tratamento do23:59 no exportador.

## CERAN: evidência empírica não equivale a contrato

As tabelas públicas de [Castro Alves](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php), [Monte Claro](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHMC.php) e [14deJulho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php) nomeiam afluente, turbinada, vertida, remanescente e defluência, em m³/s. Não foi localizado dicionário público que fixe partições, arredondamento, média versus instante, flags ou sentinelas.

Na amostra local já auditada, a defluência CERAN coincide com turbinada+vertida, enquanto remanescente aparece separada. ExemploCastro21/09/2026 11h: CERAN Q=1205,20,T=152,V=1053,20,R=21,22; ONS Q=1205,T=152,V=1032,O=21. ONS fecha incluindo outras; somar novamenteR no HTML gera dupla contagem neste exemplo. **Não aplicar automaticamente a fórmula ONS às colunas CERAN.** A equivalência por instantes apoia uma interpretação, não comprova que o mesmo contrato vale para toda usina/período. Detalhes da comparação permanecem em `outputs/auditoria-qualidade-treino-ceran/ceran-ons-overlaps.csv`.

## Valor9999

**Não foi encontrada evidência primária de que9999 seja código de ausência, teto do exportador, limite do equipamento ou medição física validada para Monte Claro.** O dicionário declara FLOAT sem enumerar sentinelas. A rotina não menciona9999; o anexo13 usa campos posicionais de sete caracteres para afluência/defluência, portanto a máscara ilustrativa de quatro letras não demonstra teto9999. O histórico local tem um caso afluente9999, preservado com linha/hash em `9999-local-evidence.json`.

Resultados de busca sobre9999 em formatos de modelos energéticos, equipamentos não identificados ou outros domínios não estabelecem sua semântica nesta série. Manter9999 como valor original com significado especial **não verificado**; não convertê-lo automaticamente em nulo, saturado ou “acima da capacidade”.

## Proposta geral de QC — ainda não implementada

1. **Identidade antes da conta:** estação/usina, versão da fonte, unidades, intervalo, fuso, método de agregação e partição de componentes devem coincidir. Caso contrário, marcar `SEMANTICS_UNVERIFIED` e não comparar como se fossem equivalentes.
2. **Ausência separada:** campo ausente/não finito é `MISSING`; não vira zero. Verificar limites de sinal por campo e fonte, conservando bruto e razão. Não aplicar um filtro único `valor≥0` à afluência ONS.
3. **Fechamento ONS:** com campos finitos e partição confirmada, registrar `r=Q−T−V−O`. Q=0 com componente positiva é candidato a `COMPONENT_CONFLICT`, inclusive quando outras componentes não negativas estejam ausentes; uma igualdade completa só é testável com todas presentes. O conflito não revela qual campo está errado.
4. **Tolerância anterior ao modelo:** deriva de precisão, arredondamento, erros instrumentais e sincronismo documentados. Se arredondamento ao mais próximo e passos de quantização forem conhecidos, o limite de arredondamento da soma é `(passoQ+passoT+passoV+passoO)/2`. Isso é derivação matemática, não tolerância oficial ONS. Sem metadados, guardar residual e sinalização para revisão; não inventar limiar de reprovação física nem escolhê-lo pelo erro do modelo.
5. **CERAN:** até confirmar contrato, testar somas somente como diagnóstico identificado por fonte. Não somar remanescente ou parcela não turbinável duas vezes; não corrigir a defluência para forçar igualdade.
6. **Extremos e saltos:** `EXTREME_REVIEW` ou `POSSIBLE_OUTAGE` são avisos independentes. Pico acima do histórico,9999,zero isolado,I<Q ou subida rápida não bastam para invalidar. Procurar estados operacionais, sensores independentes e revisão do agente, preservando o evento.
7. **Consumo pelo modelo separado:** manter bruto+flags+evidência. Decidir tratamento em um candidato com política congelada e avaliação temporal independente, preservando avaliações anteriores; jamais limpar amostras em função dos erros do teste. Esta pesquisa apenas especifica diagnóstico, não autoriza substituir/interpolar entradas.

## O que ainda falta

Não localizados: contrato CERAN de componentes/instantes e flags; lista de sentinelas e limites do instrumento de Monte Claro; precisão/quantização oficial e tolerância do balanço; NT076/2005R2 integral; documentação do mapeamento23:59↔24h e continuidade temporal do exportador; versão posterior à revisão08 confirmada como vigente. A ausência na busca não prova inexistência.

Canais públicos apropriados para esclarecimento: ONS `relacionamento.agentes@ons.org.br` (catálogo); CERAN `ceran@ceran.com.br` (site institucional). Solicitar dicionário/versionamento, parcelas incluídas na vertida/remanescente, qualidade/sentinelas, arredondamento e tratamento de falhas. Nenhuma mensagem externa enviada.
