# Meta de precisão — nível do rio em Muçum

Criada em 21/09/2026. Estado: **ativa; 98% ainda não demonstrados**.

## Objetivo e medida

Alcançar pelo menos **98% de previsões com erro absoluto de até 0,50 m**,
separadamente para cada antecedência de 1 a 12 horas. A tolerância de 0,50 m
é a definição operacional inicial adotada para tornar o pedido de 98% mensurável;
não deve ser ampliada para fazer o modelo passar.

Acerto = `abs(nivel_previsto_m - nivel_observado_m) <= 0.50`.
Assertividade = `acertos / previsoes_verificaveis * 100`.

Exigir o mesmo percentual no recorte de cheias: nível observado >=7 m.
Esse é um recorte analítico do projeto, **não uma cota oficial de alerta**.
Apresentar ainda os resultados de subida rápida, pico e recessão separadamente.
Não agregar horizontes nem usar a frequência de rio baixo para esconder falhas
nos períodos críticos. Avaliar o Radar e o HGE/ARNO separadamente: não contar
como acerto simplesmente porque um dos dois modelos acertou.

## Evidência necessária para conclusão

- Previsões imutáveis, emitidas e registradas antes do instante previsto.
- No mínimo 1.000 previsões verificáveis por horizonte no total e observações
  de pelo menos 10 eventos independentes de cheia. Publicar também os tamanhos
  amostrais do recorte de cheias; poucos pontos não sustentam conclusão.
- Erro <=0,50 m em pelo menos 98% dos pares em cada horizonte e recorte.
- Quantificar incerteza considerando a dependência entre previsões consecutivas,
  por exemplo com reamostragem por evento. Os mínimos amostrais não constituem
  sozinhos garantia estatística ou garantia de desempenho futuro.
- Publicar MAE, viés, P90/P98 do erro absoluto, erro máximo, erros de pico e
  horário, disponibilidade das fontes e cobertura das previsões esperadas.
- Sem previsão ou sem observação válida: registrar a falta separadamente;
  nunca contar como acerto nem escondê-la do relatório de cobertura.
- Medição na mesma estação, unidade e referência vertical, com controle de
  qualidade. Registrar revisões dos dados e da curva-chave. Não transformar
  observação interpolada ou valor carregado em medição real no horário-alvo.
- Seleção de candidatos por avaliação temporal e por eventos reservados, seguida
  de execução prospectiva. Proibir dados futuros nos preditores e alterações
  retroativas nas previsões já emitidas.

## Ciclo horário

1. Atualizar dados e estados dos dois métodos no mesmo horário de referência.
2. Salvar previsões de 1 a 12h, instante real de emissão, validade, versões de
   código/modelo, parâmetros, fontes e respectivas idades.
3. Verificar as previsões anteriores que já tenham medição válida correspondente.
4. Atualizar o placar por modelo, antecedência e regime do rio. Calcular o prazo
   a partir da emissão efetiva: não chamar de 1h uma previsão emitida depois do
   horário de referência e com menos de 1h restante. Marcar atrasos explicitamente.
   O registro usa bandas de antecedência mínima h até menos de h+1 horas reais,
   sempre exibindo o prazo exato. Saídas com menos de 1h restante ficam fora das
   bandas; 12h exige pelo menos 12h efetivas. Ver `prospective-verification.md`.
5. Diagnosticar os maiores erros e testar uma melhoria local, em versão candidata,
   quando houver evidência e dados suficientes. Preservar o modelo de referência
   para comparação e não fazer ajustes apenas para aproximar os dois resultados.
6. Promover candidatos apenas com evidência de ganho, sem regressão em cheias e
   preservando os registros e o modelo anterior. Informar mudanças relevantes,
   falhas e necessidade de intervenção; manter silêncio nos demais casos.

## Ponto de partida

O experimento HGE/ARNO de 21/09/2026 é um componente simplificado da equipe HGE-IPH,
não o MGB-IPH completo. Na reconstrução histórica do cenário PET=3, apresentou
MAE de 0,411 m no geral e 0,888 m acima de 7 m, contra 0,426 m e 0,849 m do
roteamento anterior. **Esses números não são taxa de acerto prospectiva.**

Não há, até este registro, comprovação de 98% pelo protocolo acima. Atingir a meta
depende de dados e validação; ela não representa promessa de precisão.

Escopo autorizado: coleta pública, cálculos, testes e melhorias locais. Sem deploy,
alteração do produto em produção ou mensagens a terceiros. O recálculo horário
continua ativo nesta tarefa.

## Pesquisa e evolução autorizadas

O usuário autorizou em 21/09/2026 um agente para buscar séries históricas e
informações de treinamento, com evolução recorrente do modelo. A automação
horária inclui esse trabalho em lotes delimitados, sem impedir o recálculo.

- Inventário inicial: `outputs/pesquisa-hidrologica-2026-09-21/`.
- Placar retrospectivo inicial: `outputs/meta-precisao-2026-09-21/placar.md`.
- Primeiro novo candidato: ET0 horária de reanálise no modelo HGE/ARNO,
  em `outputs/mucum-hge-et0-candidato-2026-09-21/`.
- Cada nova fonte exige proveniência, licença/condições, unidades, datum,
  timestamps, dados válidos por variável e tratamento explícito de lacunas.
- Amostras com chuva, mas sem nível, não viram alvos de treinamento. Dados
  suspeitos devem ser segregados. Hindcasts e reanálises não são arquivos de
  previsões historicamente emitidas.
- Treinar versões candidatas separadas; registrar também resultados negativos.
  Manter modelo anterior quando a evidência não mostrar ganho em cheias.
- Não reutilizar eventos de teste repetidamente para selecionar hiperparâmetros
  e depois chamá-los de validação independente. Reservar novos eventos e verificar
  previsões reais após a emissão.

## Integração prospectiva de 21/09/2026

O runner `scripts/hydro_hourly_forecast.py` foi ligado ao agendamento horário.
Primeira execução completa: `outputs/mucum-hourly-20260921T165608-0300/`, com
133 respostas coletadas e duas emissões registradas às 17:01 BRT. A origem
nominal foi 16h; o alvo das 17h expirou durante o cálculo e não foi emitido.
Os alvos registrados vão de 18h até 06h do dia seguinte; o de 18h tem menos
de uma hora real e não comprova a banda de 1h. As horas nominais extras permitem
avaliar até a banda de 12h reais. O registro conserva essa diferença.

Essas versões são candidatas com meteorologia atual, sem promoção automática.
No alvo final, Radar calculou 16,64m e HGE 25,22m: divergência de 8,59m que
exige diagnóstico de extrapolação e verificação posterior, **não** evidência
de precisão. Nenhum valor foi publicado no produto. A primeira emissão usou
Muçum às16h (11,64m), último dado admissível até sua origem; a coleta também
continha observações posteriores, que não foram antecipadas para a origem.

O agente preservou nova documentação SGB sobre referências verticais e máximos
manual/telemetria em `outputs/historico-cheias-mucum/documentation/`.
Diferenças entre máximos em horários distintos não autorizam correção global.
Os metadados de vigência e contrato temporal ainda não foram inteiramente
confirmados. A meta de98% permanece ativa e não demonstrada.

## Auditoria de extrapolação de montante

`outputs/auditoria-vazao-montante-20260921/validated/` reproduziu numericamente
as24estimativas originais de vazão (2fontes ×12prazos) do snapshot17h e
decompôs suas contribuições. A estimativa máxima de14deJulho, aproximadamente
14.080m³/s, extrapola o máximo observado no treinamento (9.452m³/s).
Entradas ligadas à rápida subida de Castro Alves e à chuva também ultrapassam
as faixas do treino. Isso sinaliza incerteza; não prova um limite físico do rio.

Uma mistura com persistência, selecionada no período de validação anterior,
foi testada no período cronológico seguinte e não promovida: em14deJulho,
no prazo11h e nas vazões altas, MAE piorou de729,88 para984,95m³/s (+34,9%).
São erros de vazão, não percentuais de acerto do nível de Muçum. A avaliação
é de desenvolvimento e não um novo conjunto independente.

O cálculo horário passa a preservar `upstream-extrapolation.json`, com entradas
fora das faixas históricas, vazões previstas acima do máximo de treino e maiores
contribuições lineares. Previsões sinalizadas continuam na avaliação; não são
cortadas ou excluídas para melhorar a taxa de acerto. A faixa de sensibilidade
PET/chuva não representa a incerteza dessas vazões futuras.

O agente adicionou3.902registros ONS horários das três usinas de montante,
julho/2020 e maio/2024, em `outputs/historico-vazoes-ceran/`. A auditoria
encontrou apagão de87–88horas no pico de2024 e zeros suspeitos no pico de2020;
o lote permanece fora do treinamento. Fontes ONS/CERAN documentam avarias,
restauração e obras: esses períodos não serão tratados automaticamente como
um regime físico único. O horário de fechamento23:59 e vínculo do fuso com
o exportador histórico também permanecem explicitamente pendentes.

## Continuidade dos insumos

O runner foi ligado a snapshots cumulativos via `scripts/hydro_history.py`,
com índice ativo em `outputs/monitoramento-prospectivo/history-index/`.
Duas coletas reais foram consolidadas;181séries da emissão de referência17h
foram reproduzidas sem diferença até tolerância1e-10. A suíte local soma33testes,
incluindo retenção além de sete dias, revisões inválidas, rejeição de recibos
antigos e integridade dos arquivos. A validação não gerou outra previsão,
não retrodatou emissão e não altera a meta de precisão. Ela remove a perda
de histórico causada pelo deslocamento da janela de coleta; interrupções reais
sem aquisição continuam sendo lacunas, jamais observações inventadas.

## Cobertura e segunda emissão prospectiva

O protocolo de cobertura foi pré-registrado para janelas horárias a partir de
21/09/2026 às18h BRT. Exige entrega dos dois modelos no mesmo ciclo/referência,
com todas as bandas reais1–12h e conclusão antes do fim da janela. Ausências,
falhas, atrasos e pacotes incompletos não desaparecem do denominador. Antes de
encerrar a primeira janela, a taxa é não calculável; cobertura não é precisão.

Na execução17:27, uma inconsistência de grade meteorológica interrompeu o
cálculo. A correção do coletor já usava as coordenadas originais, compatíveis com
as grades dos arquivos de treinamento; a migração cumulativa foi registrada
com hashes exatos em `docs/weather-grid-transition-20260921.json`. O checkpoint
anterior e a falha foram preservados. A tentativa de recuperação emitiu ambos
os modelos às17:31 BRT e verificou os artefatos imutáveis e o vínculo ao ciclo.

A coletaANA das17:23 trouxe12,97m às17h. Na comparação diagnóstica das previsões
antigas das15h, Radar errou1,76m e HGE1,05m nesse alvo. Não são evidência de98%
nem importações retroativamente elegíveis. A nova emissão continua sinalizando
extrapolação no HGE; os resultados não foram promovidos nem publicados no produto.

## Árvores e qualidade das entradas de montante

O experimento em `outputs/experimento-vazao-arvores-20260921/` comparou ridge,
árvores de variação e árvores de nível em cortes cronológicos. A seleção pela
validação manteve ridge nas duas fontes; nenhuma família nova foi promovida.
Árvores de variação reduziram o MAE de14deJulho no teste de desenvolvimento,
mas pioraram a validação nas vazões altas e não repetiram a melhora emCarreiro.
Esse período de teste já foi examinado e não é validação independente nova.

A auditoria do agente em `outputs/auditoria-qualidade-treino-ceran/` reproduziu
as seis sériesQ/I de montante e encontrou zeros contraditórios emMonteClaro
em22/07/2026, propagados até o arquivo congelado de treinamento. Não há
evidência equivalente para invalidar a subida atual deCastroAlves: extrapolação
histórica não é prova de erro de medição.

A política `docs/monte-claro-input-qc-experiment.json` definiu antes do cálculo
duas máscaras experimentais: somenteQ eQ/I ausentes nas janelas auditadas.
`outputs/experimento-qc-monte-claro-20260921/` preserva os originais e todos os
alvos, recomputa tendências e mantém as mesmas amostras e parâmetros. Na
varianteQ/I, MAE de vazões altas de14deJulho cai437,99→322,73m³/s, masCarreiro
piora78,21→78,91m³/s. Nove origens de um mesmo episódio explicam as alterações
do teste;108pares por fonte não equivalem a108eventos independentes.

O diagnóstico atual11h de14deJulho permanece acima de13mil m³/s. A limpeza
retrospectiva não resolveu a extrapolação nem demonstrou precisão do nível.
Nenhuma máscara por data foi aplicada ao runner. Próximo passo: definir uma
regra de qualidade pela semântica de cada fonte, manter leitura bruta e
validar em outros eventos antes de promover um candidato. A suíte local
tem48testes aprovados, incluindo cortes temporais, proteção contra ancorar
leitura antiga e aplicação da máscara somente ao snapshot auditado.

## Inventário de eventos e semântica das fontes

O relatório prospectivo passou a incluir um inventário de episódios observados,
com política registrada no ledger em21/09. Leituras>=7m são agrupadas até haver
72h contínuas abaixo desse nível, com lacunas/qualidade inválida interrompendo
a comprovação da separação. A regra é diagnóstica: não certifica independência
hidrológica nem satisfaz automaticamente o mínimo de10cheias. A primeira
avaliação mostrou um episódio ainda aberto e nenhum evento completo. A leitura
mais recente então disponível era13,45m às17h30BRT. Metadados de fuso/datum
continuam pendentes; não há pares elegíveis à meta até essa verificação.

A avaliação agora usa um único corte de tempo para previsões, revisões de
observações, cobertura e eventos. Foram adicionados testes de múltiplos picos
no mesmo episódio, separação por recessão observada, lacunas, censura, datums
distintos e registros recebidos depois do corte;56testes locais passaram.

O agente preservou pesquisa primária em `outputs/pesquisa-qc-semantica-fontes/`.
ONS documenta Qdef=Qtur+Qvert+Qoutras; transferência não entra novamente e
vertimento não turbinável é parcela. O esquema aceita zero e até afluência
negativa. CERAN não tem contrato público de componentes confirmado e as amostras
indicam outra partição.9999 não foi identificado como sentinela ou limite.
O próximo diagnóstico deve preservar essas distinções, sinalizar conflitos e
não converter extremos, zeros ou afluências negativas automaticamente em falha.

## Ciclo18h e histórico extremo de2023

O ciclo `outputs/mucum-hourly-20260921T180020-0300/` concluiu às18h02BRT,
com as bandas reais1–12h e56artefatos verificados por pacote. A última leitura
admissível deMuçum era13,45m às17h30, atraso30min na origem18h. Em08h de22/09,
Radar estima17,07m eHGE30,67m;16estimativas de vazão do HGE ultrapassam os máximos
dos respectivos treinamentos. A grande divergência permanece explícita e não
é tratada como intervalo de confiança. A medição das18h ainda não estava
disponível: seis pares vencidos ficaram como ausência de observação exata.

O agente recuperou setembro2023 em `outputs/historico-cheia-setembro-2023/`.
Há714horas de cada CERAN, com seis horas ausentes por usina, sem lacuna no pico
de04–05/09. O máximo defluente de14deJulho é15.114m³/s. Muçum tem2.023níveis
aprovados, mas falta telemetria aprovada durante o pico: a marca retrospectiva
SGB não substitui essa série horária. O lote continua separado do treino ativo.

Foi definido antes do ajuste o protocolo `docs/upstream-2023-augmentation-protocol.json`:
comparar a referência completa, um ridge só comCERAN e o mesmo ridge acrescido
das linhas de2023. Isso permitirá separar o efeito de remover preditores do
efeito de adicionar uma cheia maior. Parâmetros/cortes ficam fixos, períodos
vistos continuam rotulados como desenvolvimento e nenhum candidato é promovido.
O protocolo ainda não foi executado nesta etapa. A suíte local soma60testes.

## Resultado do acréscimo de2023

O protocolo acima foi executado depois, em
`outputs/experimento-vazao-2023-20260921/`, sem modificar a definição anterior.
Foram treinados três grupos com os mesmos alvos de avaliação: referência
completa, somente24preditoresCERAN e estes24preditores acrescidos de2023.
O lote adicionou669–681origens por antecedência, respeitando atraso presumido
60min e expiração90min. Registros23:59 não viraram alvos de hora inteira.

O candidato não foi promovido: MAE de vazões altas na validação foi285,24m³/s
na referência completa,324,89no modeloCERAN e406,71com2023. No desenvolvimento
posterior, o acréscimo melhorou o modelo reduzido491,88→454,72, mas continuou
pior que437,99da referência completa. A extrapolação atual também cresceu;
o diagnóstico11h passa19.341,99→28.775,39m³/s nesta comparação congelada.

Os36modelos finais, alvos pareados, código e hashes foram preservados. O histórico
adicional é mantido para pesquisas futuras; nenhum valor foi descartado por
piorar o erro. A suíte local passou64testes. A meta de98% continua não demonstrada;
mais dados, sem representação adequada da dinâmica, não garantiram melhora.

## Regressão com restrição de sinal

O protocolo `docs/nonnegative-upstream-protocol.json` comparou a referência,
um ridge de vazão absoluta com variáveis defasadas e esse ridge com coeficientes
numéricos não negativos. O primeiro ajuste foi invalidado por falha numérica
na utilização do fator triangular, preservada em
`outputs/experimento-vazao-nao-negativa-20260921/invalidation.json`.
O candidato validado está em
`outputs/experimento-vazao-nao-negativa-validada-20260921/`.

Após corrigir e conferir independentemente as condiçõesKKT, os36ajustes
restritos tiveram resíduo relativo máximo2,94e-15. A extrapolação atual11h
de14deJulho diminuiu19.341,99→12.623,36m³/s, mas o MAE de vazões altas na
validação piorou285,24→417,48. A melhora no desenvolvimento seguinte
437,99→421,84não foi suficiente para promoção. Todos os alvos e versões
anteriores foram preservados.68testes locais passaram; isso verifica o
processamento, não comprova a meta98% nem conservação física por esse modelo.

## Centralização ponderada

`outputs/experimento-centralizacao-ponderada-20260921/` compara média ponderada
das entradas com a centralização anterior, mantendo escala, mediana, pesos,
penalidade e alvos. Uma formulação independente com intercepto livre confirmou
o ajuste candidato. O resíduo ponderado do treinamento desapareceu, mas o MAE
nas vazões altas da validação de14deJulho ficou285,24→285,31m³/s, e no período
seguinte437,99→438,42. Carreiro, com pesos uniformes, permaneceu equivalente.

Na resposta absoluta, a centralização ponderada reduziu bastante o viés de
treinamento e melhorou sua própria referência; ainda assim, o erro de vazões
altas da validação329,17ficou pior que285,24da referência de variação.
Nenhum candidato foi promovido.96modelos e todos os alvos pareados foram
preservados;71testes locais passaram. A extrapolação continua sem solução
demonstrada e os critérios prospectivos da meta permanecem não atendidos.

## Primeira comparação das emissões ao alvo18h

A coleta18h26 recebeu nível aprovado13,87m às18h de21/09. As emissões das17h01
previram13,431m(Radar) e13,929m(HGE), com erros0,439e0,059m. As emissões17h31
previram13,859m e14,016m, erros0,011e0,146m. Todas ficaram dentro de±0,50m
nesse alvo, mas com menos de1h real de antecedência: aproximadamente59min e29min.
Portanto não entram nas bandas1–12h da meta. Fuso/datum ainda pendentes também
permanecem explícitos. O relatório está em
`outputs/monitoramento-prospectivo/reports/20260921T212640476483Z/`.

As importações antigas da origem15h continuam separadas: para18h tiveram erros
2,369m(Radar) e0,791m(HGE). Não foram apagadas nem transformadas em emissões
prospectivas. Um único alvo de curto prazo não comprova98% ou elimina a
extrapolação preocupante do HGE nas horas seguintes.

## Evidência pública do horário e da unidade atuais

O agente concluiu a pesquisa em
`outputs/verificacao-contrato-temporal-mucum/README.md`. O portal ANA
`gerarGrafico.aspx` identifica a estação 86510000 Muçum, unidade cm e UTC−3.
Os 73 horários numéricos de 21/09 em comum com o serviço legado coincidem
exatamente; o mapa oficial também registra 1387 às 21:00Z, correspondente
às 18h UTC−3. Respostas, comparação e hashes estão preservados.

Essa evidência confirma a apresentação do portal atual e corrobora a
interpretação temporal das observações atuais do legado. O HTML público
não demonstra ligação ao backend SOAP, nem resolve continuidade física
da régua, revisões ou disponibilidade histórica. As flags anteriores de
elegibilidade permanecem inalteradas. Não houve treino ou promoção de
modelo a partir dessa pesquisa documental.

## Dependência do HGE das vazões previstas

`scripts/hydro_hge_dependencies.py` reproduziu os 14 pontos da emissão18h02
usando263 referências a blobs verificados, com erro máximo7,11e-15m e estado
hidrológico final idêntico dentro de1e-8. A análise está em
`outputs/diagnostico-dependencias-hge-18h-20260921/report.md`.

No alvo08h de22/09, dos20.049,67m³/s calculados,18.119,61m³/s vêm de vazões
futuras estimadas de14deJulho. Zerar somente a chuva incremental futura muda
30,669→30,635m; manter as vazões de montante constantes muda para16,306m.
São sensibilidades diagnósticas, não previsões substitutas ou limites físicos.
Persistência já falhou na comparação histórica anterior e não foi promovida.
A prioridade passa pela previsão de defluências da cascata e sua validação,
pois chuva local/PET não explicam a extrapolação predominante neste caso.
Os dois testes novos verificam a fronteira entre valores históricos e estimados;
a suíte hidrológica atual passou76testes. A meta prospectiva permanece aberta.

O agente concluiu `outputs/pesquisa-armazenamento-ceran/README.md`: o acervo
ONS já contém níveis horários de montante/jusante pareáveis com Q/I. O cadastro
atual publica volumes úteis4,600/1,450/4,710hm³ (Castro/Monte/Julho), mas há
divergências com Vmáx−Vmín nos dois primeiros e não há histórico desse cadastro.
Não foi recuperada curva cota-volume completa com vigência após as avarias.
Logo esses números não sustentam limite de vazão, retenção presumida ou
conversão automática dos percentuais históricos. Níveis podem ser examinados
como preditores, após conciliar contratos das fontes e atrasos, mantendo regimes
separados. Esta pesquisa não alterou treinamento ou previsões.

## Experimento com níveis dos reservatórios

O protocolo pré-especificado `docs/reservoir-level-features-protocol.json` foi
executado em `outputs/experimento-niveis-reservatorios-20260921/`. Acrescentar
níveis de montante/jusante e variações reduziu o MAE de vazões altas de14deJulho
285,24→266,58m³/s na validação e437,99→396,03no período posterior. Houve melhora
nas12antecedências nominais0–11h, mas o erro11h continua alto:601,77/687,95m³/s.
Carreiro piorou nas vazões altas da validação; não foi escolhido esse acréscimo
para sua previsão. Nenhum resultado comprova ainda ganho no nível deMuçum.

Foram preservados144modelos,197.206pares idênticos por família e o rastreio
das entradas. A referência anterior foi reproduzida exatamente em contagens,
MAE, viés eP90; hashes conferidos. Os níveis usam atraso presumido60min e
expiração90min, não disponibilidade histórica comprovada. A suíte passou79testes.

A auditoria `outputs/auditoria-niveis-reservatorios-ceran/` encontrou um salto
jusante deJulho68,74→168,74→68,75m em03/05/2025. O valor foi mantido no teste,
sem máscara criada após os resultados. Há240pares de níveis CERAN/ONS coincidentes
e unidades em metros explícitas, mas datum/fuso comum seguem pendentes.
O candidato fica preservado para avaliação da propagação atéMuçum e robustez
por eventos; modelos horários não foram alterados e98%continua não demonstrado.

## Propagação do candidato até Muçum

O protocolo `docs/reservoir-level-mucum-protocol.json` foi executado em
`outputs/experimento-niveis-ate-mucum-20260921/`, sem novo ajuste. Somente a
previsão de14deJulho foi trocada; Carreiro, HGE/PET3, roteamento, curva de nível
e tau6ficaram iguais. As chuvas observadas param em origem−1h; origem/futuro
usam arquivos meteorológicos. A âncora exige H/Q exatos em origem−15min.

No prazo nominal12h, MAE geral0,700→0,590m e MAE em nível≥7m1,746→1,663m.
Acertos±0,50m nas cheias14,8%→18,0%. Em6h, MAE geral piora0,370→0,385m.
Portanto o ganho é misto e o candidato não foi promovido. A contagem verificada
é18.981pares de23.538alvos,
com4.122falhas de entrada,288âncoras ausentes e147alvos ausentes (motivos
prioritários mutuamente exclusivos). Cobertura geral por prazo fica em torno
de81–82%entre alvos com medição, e menor no recorte de cheia. Os147alvos
sem verdade e com entradas válidas conservam ambas as previsões.

A revisão independente confirmou índices/unidades, igualdade de hashes,
reprodução de métricas e ausência de observações futuras na inferência.
Identificou uma limitação de cobertura: `route()` rejeita lacunas mesmo em
defasagens com peso exatamente zero. Carreiro tem sete desses pesos. Isso
afeta igualmente os pares das duas famílias, mas merece revisão separada
sem escolha por erro. A suíte passou82testes. O estudo continua histórico e
com disponibilidade presumida; adicionou zero evidência prospectiva à meta.

## Pesos exatamente zero e causa das falhas de cobertura

O experimento `outputs/experimento-niveis-ate-mucum-pesos-zero-20260921/`
ignora entradas apenas quando seu peso congelado é exatamente zero. Pesos
positivos arbitrariamente pequenos continuam exigindo dados. Os38.256valores
finitos anteriores permaneceram exatamente iguais; nenhum dos23.538alvos
mudou de situação. A cobertura deste acervo não melhorou com essa correção.

A auditoria das4.122falhas de entrada, em344origens, apontou PassoCarreiro
em todos os casos:4.056dependem de histórico ausente para a âncora,
3.750de histórico ausente no roteamento e2.214de base conhecida ausente.
Essas causas se sobrepõem. A investigação seguinte examina QC/versões e
níveis medidos da estação86500000. Nenhuma lacuna foi preenchida nem modelo
horário alterado. A suíte passou84testes; a meta permanece não demonstrada.

`outputs/auditoria-lacunas-carreiro/README.md` confirmou a origem das lacunas:
512instantes distintos afetam as4.122falhas (425sem registro exato e87com
vazão vazia). Na grade de15min do período avaliado há1.031slots sem vazão,
855sem registro e176com campo vazio. De01a08/07a fonte preservada tem leituras
pontuais às07h e17h; não representa telemetria contínua. Há34níveis aprovados
sem vazão em23/07,10h45–19h. Nenhuma vazão aprovada foi descartada pelo parser
nesse período e nenhuma versão preservada recupera as lacunas históricas.
Não foi ajustada curva de descarga nem imputado dado; novo tratamento dessas
entradas precisará de protocolo e validação próprios.

## Ciclo horário das19h

`outputs/mucum-hourly-20260921T190023-0300/` terminou às19h02min15s BRT,
com leitura14,25m de18h30. Cada pacote teve56artefatos e207recibos de entrada
verificados, cobrindo todas as bandas reais1–12h. Para20h, Radar15,447m e
HGE16,217m; para09h de22/09, Radar17,564m eHGE28,997m. A divergência longa
permanece explícita; os experimentos de níveis/pesoszero não foram incorporados.

A primeira janela fechada da política de cobertura,18h–19h, teve entrega
completa. É apenas uma janela de entrega, não prova de precisão. O relatório
`outputs/monitoramento-prospectivo/reports/20260921T220215980431Z/` mantém
zero pares elegíveis para a meta; a observação exata das19h ainda não estava
disponível. Recibos de revisão manual anteriores permanecem separados no
histórico e não foram apagados ou usados para reescrever emissões originais.

## Diagnóstico por tendência e episódio

`outputs/diagnostico-tendencias-eventos-reservatorios-20260921/` estratifica
as previsões preservadas pela variação líquida de3h conhecida na origem,
usando somente dois níveis exatos e explicitamente aprovados até origem−15min.
As categorias recompõem contagens eMAE com diferença máxima6,66e-16m.
Todos os alvos finitos conferem com as fontes brutas e têm QC aprovado.

Há quatro agrupamentos com alvos horários≥7m no período; nenhum foi certificado
independente e dois têm lacunas. A cheia iniciada02/07BRT tem35alvos de nível
por prazo e zero pares calculáveis. Na maior cheia, pico19,86m, MAE12h cai
2,253→2,163m, ainda muito acima da tolerância. Em12h há redução deMAEnas três
tendências conhecidas, mas a categoria estável fica com zero acertos em24pares.
Em6h, a taxa dentro de±0,50m piora nas subidas e descidas apesar doMAEmenor.
Não foi criada seleção de modelo por recorte favorável. A suíte passou87testes.

A pesquisa `outputs/pesquisa-curva-chave-carreiro/README.md` encontrou curva
oficial antiga com vigência até31/12/2013 e diferenças entre texto/anexo.
Não há curva admitida parajulho2026. O caminho atual ANA requer autenticação
e não foi acessado; as34vazões ausentes continuam ausentes. Nenhuma conversão,
promoção ou alteração do pipeline foi realizada a partir dessas descobertas.

## Experimento de entradas estimadas para o Carreiro

O experimento `outputs/experimento-proxy-carreiro-20260921/` ajustou 12 modelos
auxiliares com alvos anteriores a 01/07/2026, sem variáveis de vazão do próprio
Carreiro. As estimativas entram somente nas posições ausentes do cálculo e
ficam separadas das observações. Modelos principais e parâmetros HGE continuam
congelados. Nenhum arquivo de medição ou alvo foi preenchido.

Foram recuperados 4.122 pares, passando de 18.981 para 23.103 pares calculáveis.
Os 38.256 valores anteriormente finitos permaneceram idênticos, com diferença
máxima de 0 m. Restam 147 alvos exatos ausentes e 288 âncoras ausentes.
A verificação preservada confere as 22 entradas por hash e o corte de treino.

Em 12 h, o candidato com níveis das usinas tem cobertura de 99,02% no total e
99,16% nas cheias, mas acerta dentro de ±0,50 m em somente 60,55% e 30,21%,
respectivamente. Nos 52 novos pares de cheia de 12 h, o acerto é 73,08%; esse
recorte não substitui a avaliação completa. A mudança nas métricas agregadas
vem da população ampliada, sem mudança das previsões antigas.

Resultado mantido como candidato histórico de cobertura, sem promoção à rotina
horária. Disponibilidade histórica presumida e períodos já examinados impedem
usar esses números como prova prospectiva ou independente. A redação herdada
contraditória do protocolo foi esclarecida após a execução; original e código
executado continuam preservados, com adendo e hashes, sem alteração numérica.
A suíte passou 89 testes; a meta de 98% permanece ativa e não demonstrada.

## Proxy por cheia e atribuição das maiores oscilações

`outputs/diagnostico-eventos-proxy-carreiro-20260921/` conserva as mesmas regras
de tendência e agrupamento, com contagens e MAE recompostos até 4,44e-16 m.
Todos os alvos finitos conferem com fontes aprovadas; quatro agrupamentos
continuam sem certificação de independência. A cheia de início de julho passa
de zero para 35 pares por prazo: 35/35 acertos em 6 h, mas 26/35 em 12 h.
Na maior cheia, o candidato tem apenas 18/133 acertos em 12 h, MAE de 2,006 m
e erro máximo de 9,038 m. A suíte local passou 90 testes.

`outputs/diagnostico-erros-julho-20260921/` reproduz e decompõe as vazões
congeladas nos três maiores erros de nível. A sequência bruta de Monte Claro
em 22/07 (9.907 m³/s às 06h, zero às 07h–09h, 9.907 m³/s às 10h) provoca
parcelas estatísticas de aproximadamente −5,8 mil e +5,8 mil m³/s na previsão
propagada de Julho. Isso localiza uma causa matemática importante da oscilação,
sem provar a vazão real ausente ou substituir observações. Vazões futuras
observadas foram usadas exclusivamente na comparação diagnóstica.

A próxima melhoria deve tratar entradas inconsistentes de forma causal e geral,
com validação anterior ao episódio, sem selecionar somente erros conhecidos.
Nenhuma previsão original, fonte bruta ou versão horária foi alterada.

O agente ampliou a pesquisa pré-avarias em
`outputs/pesquisa-ceran-2023-extensao-20260921/`: janeiro e junho de 2023,
4.371 registros das três usinas, fontes ONS integrais e hashes conferidos.
A janela 15–17/06 tem Q/I completos nas três usinas, com máximo de Julho de
2.850 m³/s. Outros seis meses estão catalogados, sem auditoria de cobertura.
Esses dados não entraram no treino. Hora-fim/fuso do exportador, latência
histórica e comparabilidade do regime anterior às avarias de 2024 continuam
explícitos; nenhuma lacuna foi preenchida.

## Teste de limites estatísticos nas variações de vazão

`outputs/experimento-limites-variacao-vazao-20260921/` ajustou 48 modelos
novos, reutilizando 48 referências congeladas. O candidato limita somente as
21 variáveis de mudança de vazão aos percentis 0,5 e 99,5 de cada treino.
Os limites usam apenas alvos anteriores ao corte; nenhuma vazão conhecida,
medição, ausência ou alvo foi substituído. Não são limites físicos ou QC oficial.
As referências foram reproduzidas sem diferença, em 197.206 pares por família.

Para Julho, MAE em vazões altas melhora de 396,03 para 315,62 m³/s no teste,
mas piora de 266,58 para 277,63 m³/s na validação anterior. Para Carreiro,
melhora na validação (79,18 para 73,66 m³/s) mas piora no teste (77,33 para
81,84 m³/s). Candidato não promovido por falta de ganho consistente nos dois
períodos; nenhum ganho de nível de Muçum foi inferido desses erros de vazão.
Foram preservados protocolo, limites, modelos, todas as previsões e hashes.
A suíte passou 93 testes. Os períodos já examinados continuam desenvolvimento.

A auditoria paralela `outputs/auditoria-consistencia-componentes-ceran-20260921/`
aplicou regra geral a 38.764 linhas ONS: Qdef=0 com componentes finitos somando
mais de 1 m³/s. Encontrou exatamente as três linhas de Monte Claro de 22/07,
07h–09h; nenhuma antes de julho. A identidade documentada sinaliza um conflito,
mas não determina qual coluna está errada nem uma substituição válida.
Ausência de casos positivos pré-julho impede afirmar validação independente
do tratamento desses conflitos. Fontes brutas continuam intactas.

A captura ANA de 19h26min19s BRT gerou novo recibo e relatório em
`outputs/monitoramento-prospectivo/reports/20260921T222619142289Z/`.
Continuam 10 pares diagnósticos observados e zero elegíveis à meta; a medição
exata das 19h ainda não entrou nos pares. Não foram repetidas emissões horárias,
criadas observações por interpolação ou alteradas as pendências de metadados.

## Chuva prevista nos preditores de vazão

`outputs/experimento-chuva-prevista-montante-20260921/` acrescentou 20 variáveis
à referência de 77: acumulados previstos de 3, 6, 9 e 12 h nos cinco pontos
históricos, usando média apenas de membros meteorológicos com janela completa.
Não há substituição por chuva observada futura ou zero quando falta previsão.
Foram preservados 197.206 pares por família, 48 modelos novos e 48 referências;
a reprodução da referência teve diferença máxima zero. Os 97 testes passaram.

Para Julho, MAE em vazões altas cai de 266,58 para 241,57 m³/s na validação e
de 396,03 para 389,60 m³/s no teste. Há melhoria em 8/12 e 11/12 prazos,
respectivamente; os demais prazos permanecem publicados. Para Carreiro, os
erros agregados pioram nos dois períodos. Somente Julho avança para comparação
local da propagação até Muçum. Nenhuma melhoria de nível ou promoção foi alegada.

A documentação de previous_day1 indica previsão com antecedência nominal de
24 h em relação a cada tempo válido. Para origem+1…+12 h, as referências de
inicialização ficam antes da origem, mas não há prova por registro de emissão
ou publicação. Diferentes tempos válidos podem usar diferentes rodadas; o
arquivo histórico não equivale à previsão operacional mais recente. Essa
limitação permanece explícita, inclusive nos testes anteriores que usam o
mesmo arquivo. A compatibilidade com operação precisa de avaliação separada.

A captura ANA de 19h32min13s BRT preservou a última leitura aprovada disponível:
14,44 m às 18h45. O relatório `20260921T223213231031Z` ainda tem 10 pares
diagnósticos e zero elegíveis à meta; não apareceu observação exata das 19h.
Não houve interpolação, repetição da emissão horária ou alteração de metadados.

O agente concluiu a revisão documental em
`outputs/pesquisa-contrato-chuva-prevista-20260921/`, compatível somente com uso
histórico sob disponibilidade presumida. O original da requisição ICON não
foi localizado; sua identidade está na configuração local. Há 77 horas ausentes
por ponto em abril de 2026; o candidato registra composição de 2 ou 3 membros
completos por variável. A revisão posterior está anexada ao experimento sem
mudança numérica. Produtos antigos Single Runs/HRES com hindcasts não foram
confundidos ou substituídos pelo IFS025 utilizado neste teste.

## Efeito da chuva prevista no nível de Muçum

`outputs/experimento-chuva-ate-mucum-20260921/` alterou somente as previsões
futuras de vazão de Julho, mantendo todos os outros termos do candidato com
proxy Carreiro. As 23.538 linhas e os 23.250 valores anteriores finitos foram
preservados. Continuam 23.103 pares, 147 alvos ausentes e 288 âncoras ausentes;
os 147 casos sem alvo também receberam previsão, sem inventar observações.

Em 12 h nas cheias, MAE diminui de 1,375 para 1,359 m e erro máximo de 9,038
para 8,323 m. Entretanto, os acertos dentro de ±0,50 m caem de 71/235 para
67/235 (30,21% para 28,51%): seis acertos perdidos e dois novos. No conjunto
geral de 12 h, a taxa cai de 60,55% para 60,14%. A cobertura não muda. O
candidato não é promovido; ganho em vazão ou redução de MAE não substituem
a métrica definida na meta.

A atualização foi feita pela diferença exata de vazão propagada e curva fixa,
com domínio/inversão verificados. Uma execução integral independente em
`outputs/verificacao-integral-chuva-mucum-20260921/` repetiu HGE/roteamento,
sem inverter níveis, em seis origens e 12 horizontes: 144 comparações entre
as duas famílias, diferença máxima 7,11e-15 m. Os hashes e componentes foram
conferidos. A suíte passou 101 testes. Trata-se de correção numérica demonstrada,
não de validação independente da precisão ou alcance dos 98%.

## Primeira comparação disponível para o alvo das 19h

A captura ANA de 19h45min09s BRT recebeu nível aprovado de 14,61 m às 19h
e 14,80 m às 19h15. O relatório
`outputs/monitoramento-prospectivo/reports/20260921T224509857639Z/` tem agora
20 pares diagnósticos e 142 ainda não vencidos, sem alvos vencidos faltantes
nesse recorte. Zero pares continuam elegíveis à meta devido às pendências.

Para o alvo das 19h, as emissões reais de 17h01 e 17h31 ficam na banda de
1 a menos de 2 horas: erros Radar de 0,804 e 0,107 m; HGE de 0,509 e 0,510 m.
Os dois últimos permanecem erros acima da tolerância de 0,50 m, sem arredondar
para acerto. Esses quatro pares compartilham o mesmo alvo observado, não são
quatro eventos independentes. Emissões de 18h02/18h35 têm menos de 1 h real
e continuam fora do recorte mínimo da meta; a revisão manual segue separada.

## Calibração por erros anteriores já observáveis

`outputs/experimento-correcao-erros-passados-20260921/` avaliou uma regra fixa:
por horizonte, subtrair a mediana dos erros originais com alvo entre origem−24 h
e origem−15 min, exigindo seis pares finitos. Não houve busca de parâmetros,
seleção por cheia, realimentação com erro corrigido ou uso do alvo atual.
Partida sem histórico em julho; observação com atraso de 15 min é hipótese.

Os acertos de 1 h no total subiram de 97,57% para 98,40%, mas nas cheias
ficaram em 95,32% (antes 91,91%). Em 12 h nas cheias, caíram de 30,21% para
22,55%, e MAE subiu de 1,375 para 1,841 m. O erro máximo também aumentou.
O único recorte acima de 98% não satisfaz a meta: é histórico, não cobre cheias
nem os demais prazos, e não constitui prova prospectiva. Nenhuma escolha
retrospectiva do prazo favorável foi incorporada à operação.

Candidato não promovido. As 23.538 linhas e a cobertura ficaram preservadas;
22.979 previsões receberam correção e nenhuma ficou negativa. Uma verificação
independente por máscaras temporais diretas confirmou todas as correções sem
diferença, registrando os alvos inicial/final de cada janela. A suíte passou
105 testes. A adaptação usa observações anteriores do mesmo evento e não deve
ser apresentada como um modelo estático sem acesso sequencial ao período.

## Auditoria da disponibilidade efetiva das medições

`outputs/auditoria-latencia-observacoes-20260921/` verifica 20 recibos e seus
XMLs, até o recibo 2cd08ac3, com 19 coletas distintas. Há dez horários válidos
posteriores ao início da auditoria, entre 16h48 e 19h45 BRT. A primeira
recepção local desses pontos aconteceu 18,19–43,33 minutos após a medição,
mediana de 27,50 min; nenhum foi recebido em até 15 min. É limite superior
de detecção pelo nosso coletor, não medida exata da publicação do fornecedor;
cadência, cache e execução afetam esses intervalos.

Nos ciclos regulares de 18h e 19h, a leitura efetivamente usada tem 30 min na
referência e cerca de 32 min na emissão. A medição referência−15 min não está
nos recibos vinculados. Experimentos com esse atraso presumido continuam
históricos e não devem ser apresentados como reprodução certificada do vivo.
Idade na referência não substitui idade na emissão; revisões manuais ficaram
separadas. Nenhum relógio, ponto ou elegibilidade foi alterado. A suíte passou
107 testes. O próximo teste de sensibilidade deve explicitar a idade maior,
sem alterar a definição de sucesso ou os alvos observados.

O complemento `outputs/historico-ceran-2023-complemento-20260921/` preserva
seis novos CSVs ONS de fevereiro, março, abril, maio, julho e agosto de 2023,
sem repetir janeiro/junho/setembro. Foram conferidos os hashes e 13.058 linhas
das três usinas, sem timestamps duplicados; 13.053 valores de Q e de I finitos.
A cheia de 13/07 apresenta máximos defluentes de 2.630/4.343/4.568 m³/s em
Castro/Monte/Julho, com janelas de 73 h ao redor dos picos completas nas três
usinas para Q/I e níveis de montante/jusante. Esses dados são pré-avarias de
2024, com ressalvas de hora-fim, fonte revisável e regime; não entraram no
treino atual nem foram usados para completar lacunas ou alvos de Muçum.

No complemento de 2023, o agente também documentou Julho jusante em 13/02,
15h→16h→17h: 69,00→62,02→69,02 m, com Qdef/I constantes em 28/12 m³/s.
O salto foi preservado, sem máscara ou afirmação de erro oficial. Os hashes
finais do relatório, extrações, auditoria e seis arquivos integrais foram
conferidos após a conclusão.

## Ciclo regular das 20h e variação da disponibilidade

O ciclo `outputs/mucum-hourly-20260921T200235-0300/` concluiu às
20h04m38s BRT. A leitura aprovada usada foi 15,10 m às 19h45: idade de
15 min na referência e 19,64 min na emissão. A disponibilidade variou em
relação aos ciclos de 18h/19h; a auditoria anterior não estabelece atraso
fixo de 30 min. Sensibilidades devem representar essa variação.

Ambos os pacotes tiveram os 56 artefatos e 207 recibos de insumos conferidos
por hash e cobrem as bandas reais 1–12 h. Para o alvo das 21h, Radar prevê
15,809 m e HGE 16,841 m; para 22/09 às 10h, 18,135 e 27,453 m. Os 14
pontos de vazão futura sinalizados ultrapassam seus máximos de treino, e
28 modelos de vazão têm entradas fora das faixas históricas. As previsões
continuam experimentais, preservadas no placar, sem limite físico inferido
desses valores. Nenhum candidato novo foi promovido.

O relatório `20260921T230438769929Z` contém 190 pares registrados:
20 confrontados, 12 com alvo já vencido mas sem medição exata recebida e
158 ainda não vencidos. Zero pares são elegíveis à meta. As duas janelas
horárias encerradas tiveram entrega completa; a janela das 20h permanece
aberta nesse corte. Cobertura de entrega não mede assertividade.

## Sensibilidade controlada à idade da leitura de Muçum

`outputs/comparacao-idade-ancora-20260921/` compara as idades de 15, 30 e
45 min pré-especificadas nos protocolos docs/anchor-delay-*min-protocol.json.
A única mudança entre cenários é a âncora exata H/Q, com interpolação da vazão
reconstruída e decaimento pelo tempo desde essa âncora. Modelos, proxies,
chuva, parâmetros e alvos ficaram iguais; sem seleção do melhor atraso.

Cada cenário tem 23.538 linhas. Pares verificáveis: 23.103/23.115/23.115;
a interseção comum tem 23.079. Em cheias e horizonte 1 h, a mesma amostra de
235 alvos teve 216/204/189 acertos (91,91%/86,81%/80,43%), com MAE
0,2094/0,2431/0,2756 m. Em 12 h, também 235 alvos, MAE
1,3752/1,3816/1,3832 m e 71/71/72 acertos. O atraso tem impacto claro no
curto prazo, mas sozinho não explica os erros maiores de 12 h.

A verificação independente reproduziu os 46.500 valores finitos do cenário
15 min sem diferença contra o experimento anterior e preservou lacunas.
162 verificações passaram; 216 comparações dos termos de âncora em seis
origens tiveram diferença máxima 1,07e-14 m. 1.152 métricas individuais
conferidas sem diferença; suíte 110 testes. Nada foi promovido.

Este teste varia somente a idade da âncora. Outras latências seguem
presumidas; arquivos revistos não certificam disponibilidade histórica.
A comparação permanece desenvolvimento, sem elegibilidade prospectiva
nem conclusão de 98%. O modelo operacional deve usar a idade efetivamente
disponível, nunca escolher retroativamente um atraso pelo desempenho.

## Ablação da fonte Monte Claro na previsão de 14 de Julho

`outputs/experimento-sem-monte-20260921/` executou o protocolo fixo
`docs/monte-ablation-protocol.json`: retirar os 16 preditores diretos de
Monte (Q/I, níveis montante/jusante e respectivas variações), mantendo 61
colunas, alvos, cortes, ridge alpha1000 e pesos. Não houve edição dos valores
originais, ajuste de hiperparâmetros ou mudança operacional.

O gate definido antes da execução exigia menor MAE nos recortes total/alto
nos dois períodos para avançar ao teste de nível. Falhou na validação:
MAE total 70,50→75,38 m³/s; alto 266,58→277,15. No teste de desenvolvimento,
MAE total 142,36→130,89 e alto 396,03→301,96. Não foi promovido nem
propagado ao nível de Muçum como candidato aprovado.

O diagnóstico posterior por data concentra o ganho nas origens de 22/07:
MAE 1.849,60→484,63 m³/s em 288 pares de prazos sobrepostos. Fora desse
dia, MAE total do teste piorou 121,22→126,51 e alto 254,80→284,21.
Isso evidencia perda de informação útil na retirada integral, sem declarar
a fonte oficialmente errada ou transformar a data em evento independente.

São 204.216 linhas, 102.108 por família: 78.558 validação e 23.550 teste,
sem lacunas de alvo/vazão conhecida nos intervalos nem previsão não finita.
305 verificações independentes passaram; referência e inferência foram
reproduzidas com diferença máxima 0. Pré-processamento/cortes conferidos,
resíduo relativo da equação normal até 1,23e-15; suíte 112 testes. Todos
os resultados seguem desenvolvimento já inspecionado, sem prova de98%.

A coleta ANA de 20h16m07s BRT (recibo a9c1d5ce) ainda trazia como último
ponto aprovado 15,10 m às 19h45. Relatório 20260921T231607284138Z:
190 pares registrados, 20 confrontados, 12 sem observação exata do alvo já
vencido e 158 ainda não vencidos; nenhum elegível à meta. Não foi criada
observação substituta para avaliar o alvo das 20h.

## Modelo alternativo condicionado à consistência de componentes

O protocolo `docs/component-fallback-protocol.json` foi executado em
`outputs/experimento-fallback-componentes-20260921/`: regra ONS Qdef=0,
Qtur/Qvert/Qoutras todas finitas e soma>1 m³/s. Não há máscara por data
nem substituição de observação. Sobre 12.921 registros Monte, três acionam
a regra. Suas 12 dependências em valores/diferenças de 0/1/3/6 h afetam
nove origens, 22/07 08–16h BRT, com atraso presumido de1h e expiração90min.
Só aí são usadas as previsões congeladas do modelo sem Monte.

As 108 previsões de vazão selecionadas melhoraram; as outras 102.000 ficaram
exatamente iguais. MAE no teste: total 142,36→125,37 m³/s, alto
396,03→272,99. A validação ficou igual porque não tem casos que acionem
a regra, portanto não valida esse ramo. Todos os conflitos já eram conhecidos
retrospectivamente; não se afirma ganho independente ou erro oficial da fonte.

`outputs/experimento-fallback-ate-mucum-20260921/` propagou somente a
mudança de vazão futura de Julho, com curva, âncora, chuva, HGE, Carreiro e
correção residual fixos. Preservou 23.538 linhas, 23.103 pares, 147 alvos
ausentes e 288 âncoras ausentes. Na cheia em1h, acertos caíram216→214/235;
em6h subiram115→117; em12h ficaram71/235, embora MAE caísse
1,3752→1,1761 m e máximo9,0383→5,7441 m. Melhorar vazão/MAE não
satisfaz automaticamente o critério de acerto. Nada foi promovido.

85 verificações independentes conferiram a regra/proveniência e a seleção;
23.430 níveis não selecionados e seus estados ficaram exatos. Recomputação
de roteamento sobre componentes de replay independente verificou144valores
em6origens (3afetadas), máximo7,11e-15 m. Não é uma nova simulação
integral dos23.538casos. Suíte116testes.

O confronto global ONS versus série congelada encontrou175 diferenças de
dependências em45timestamps de19–21/09 UTC, fora dos conflitos; máximo
77,95 m³/s. A causa não foi inferida. As12dependências selecionadas
coincidem, mas transferência automática a outro snapshot/fonte ao vivo
exige nova auditoria. A regra ONS não foi aplicada às parcelas CERAN atuais.

Na coleta20h23m45s BRT, reciboe9a7e1cf, ANA ainda retornava como último
ponto aprovado19h45=15,10m. Relatório20260921T232345712676Z preserva
20pares confrontados,12semobservação exata já vencida,158aindanãovencidos,
zeroelegíveis. Não foram repetidas as emissões das20h nem inventados alvos.

## Separação diagnóstica entre vazão prevista e resposta de nível

`outputs/diagnostico-vazoes-conhecidas-depois-exato-20260921/` é uma
reconstrução NÃO-PREVISÃO: troca somente termos de vazão de montante que
eram estimados na origem pelas observações conhecidas depois. Cenários:
Julho, Carreiro, ambos, além da referência. Vazões passadas, proxies, chuva,
HGE, âncora, curva e correção residual permanecem fixos. Nenhum resultado
entra no placar prospectivo, e não se presume limite superior de precisão,
pois erros de componentes podem se compensar.

A primeira rodada em `outputs/diagnostico-vazoes-conhecidas-depois-20260921/`
foi preservada como preliminar/superada: a grade raw de Julho usa asof até
90min e não prova timestamp exato. Na janela de1.968horas, o confronto ONS
encontrou82horários semregistro exato e32valores divergentes. A nova rodada
exige registroexato, Qfinita e concordânciaaté1e-7m³/s com a referência;
1.854horários satisfazem. Sem isso, mantém lacuna; não transforma23:59
em00h ou estima observação ausente. Carreiro usa grade ANA raw exata.

Na amostra comum dos4cenários, 12h/cheia tem81pares: referênciaMAE1,7218m,
Julhoconhecido1,0265m, Carreiroconhecido1,6508m, ambos0,9919m. Acertos
respectivos22/26/24/29 de81. A amostra encolheu pelas lacunas e não pode
ser confundida com235pares completos anteriores. Em6h/cheia(133pares),
Carreiroconhecido piorou MAE0,8959→0,9159m; ambosreduzempara0,6896m.
Isso reforça a investigação conjunta da resposta de nível/âncora/roteamento,
sem atribuir todo resíduo a um único componente nem inferir erro oficial.

Todas23.538linhas/alvos/referências ficaram preservados. Ausência de vazão
necessária com base disponível: Julho6.540,Carreiro2.294,ambos8.127;
mais288basesausentes. 5.826casosCarreiro sem termo futuro ficam exatos.
Verificador independente reproduziu todos os deltas (máximo9,09e-13m³/s),
valores/status e joinONS. Checagem por roteamento completo sobre componentes
de replay anterior:288comparações em6origens,228finitas/60ausências
concordantes, máximo1,07e-14m. Suíte119testes. Nãohouve treino/promoção.

## Observação das20h finalmente recebida

Coleta20h34m08sBRT, recibof717c6e3: ANA aprovou20h=15,26m e20h15=15,41m.
O relatório20260921T233408730097Z agora tem32pares confrontados,158ainda
nãovencidos e nenhuma observação exata vencida ausente nesse corte. Ainda
zeroelegíveis àmeta pelas pendências de metadados/amostra.

Para o alvo20h, emissão regular18h02 tem1,964h de antecedência real:
Radar15,5051m(erro0,2451),HGE16,7157m(erro1,4557). Emissão19h02
temmenosde1h real e não conta nessa banda mínima: Radarerro0,1868m,
HGE0,9574m. Revisão manual18h35 ficou separada. São comparações sobre
um único alvo, não eventos independentes. Todas previsões originais seguem
preservadas; não houve nova emissão20h ou ajuste no evento atual.

## Amostra de calibração da curva vazão–nível

`outputs/experimento-curva-pares-hq-20260921/` executou o protocolo
`docs/rating-paired-only-protocol.json`: ajustar a mesma curva de potência
com pares H/Q finitos, sem exigir que todas as entradas da matriz de
roteamento estejam presentes. Forma, inicialização, bounds e soft_l1 ficaram
iguais. O treino pré-julho aumentou8.880→10.890pares e128→256pares
comnível≥7m; pré-outubro3.025→4.373 e100→228. Cortes estritos
foram mantidos, sem seleção de coeficientes por desempenho no teste.

A conversão H(Q) na cheia da validação (Qreportada conhecida, não previsão)
teve MAE0,2057→0,1391m; na cheia do teste, piorou0,2518→0,2590m.
No uso em previsões, preservando exatamente a vazão calculada, âncora e
todos os demais componentes, os acertos de cheia em1h foram216→217/235;
em6h115→114; em12h71→71, comMAE1,3752→1,3815m. Nãohouve
ganho consistente nem promoção. Os23.538alvos e falhas foram preservados.

A decomposição da referência separa diferença de nível associada às vazões
pela curva adotada e diferença entre resíduos H–Q da âncora e do alvo.
Na amostra234pares de cheia/horizonte, em12h os MAEs foram1,3697m total,
1,2575m no primeiro termo e0,1967m no segundo. São termos algébricos
que podem se compensar, não parcelas absolutas aditivas nem causas físicas
independentes. Isso orienta a prioridade para geração/propagação/correção
da vazão de Muçum, sem declarar que a curva é perfeita.

A decomposição cobre23.091linhas; 12linhas do alvo22/07 17h=18,95m
ficaram semdiagnóstico por falta deQreportada no alvo. Elas permanecem
na avaliação de previsões. O acervo não certifica VazaoFinal como medição
física independente deH nem sua derivação operacional2025/26: manter
o termo “vazão reportada pela ANA”. Documentos/ressalvas preservados em
reported-flow-provenance.json, sem nova aprovação da referência ou curva.

51verificações independentes passaram sem refit: Qprevista/aplicação da
curva idênticas, parâmetros decontrole até6,10e-11 dosoriginais, identidade
algébrica até7,11e-15m. Suíte121testes. Nenhuma emissão, tolerância,
fonte bruta ou elegibilidade prospectiva foi alterada.

## Duração da correção residual: 2, 6 e 12 horas

Os protocolos `docs/residual-tau-{2,6,12}h-protocol.json` foram registrados
antes dos três cálculos em `outputs/experimento-correcao-tau-*h-20260921/`.
Somente a constante de decaimento mudou; âncora de 15 minutos, chuva,
parâmetros HGE, roteamento, curva e modelos foram preservados. Os 12 proxies
Carreiro foram recalculados identicamente, com treino anterior a julho.
São dados históricos de desenvolvimento já inspecionados, sem validação
independente para selecionar a constante.

Cada cenário mantém 23.538 linhas, com 23.103 pares avaliáveis, 147 alvos
ausentes e 288 âncoras ausentes. Não houve vazão corrigida negativa neste
conjunto. Em `outputs/comparacao-correcao-tau-20260921/`, as métricas dos
dois modelos, todos os prazos e amostras individuais/comuns foram preservadas.

No modelo com níveis de reservatórios, prolongar a constante de 6 para
12 horas aumentou os acertos de cheia em todos os 12 prazos: em 1 hora,
216→224/235 (91,91%→95,32%); em 6 horas, 115→136/235
(48,94%→57,87%); em 12 horas, 71→85/235 (30,21%→36,17%).
O MAE de cheia em 12 horas caiu de 1,3752 para 1,2680 m. Porém os acertos
gerais em 6 horas caíram de 75,70% para 72,01%, e em 12 horas de
60,55% para 59,72%. O cenário de 2 horas piorou os acertos de cheia em
todos os prazos. Não houve promoção nem escolha de constante por prazo.

237 verificações independentes passaram: o controle de 6 horas reproduziu
exatamente a execução anterior e os componentes anteriores à correção
permaneceram iguais. Outra recombinação de componentes de um replay integral
anterior cobriu 216 valores em seis origens, com diferença máxima de
7,11e-15 m. Não foi uma nova simulação independente de todas as origens.
A suíte passou com 123 testes. A correção residual é estatística; o balanço
numérico do HGE não prova sua interpretação como fluxo físico.

A coleta ANA de 21/09/2026 às 20:54:53 BRT preservou a leitura aprovada
de 20:30, 15,56 m. O relatório prospectivo
`outputs/monitoramento-prospectivo/reports/20260921T235453699095Z/`
contém 32 pares comparáveis e 158 ainda não vencidos, sem pares elegíveis
à meta enquanto as referências de tempo e nível permanecem sem certificação.
O próximo passo é avaliar a persistência do resíduo em períodos e eventos
separados, sem escolher parâmetros a partir do nível futuro observado.

## Correção residual por grupos de cheia e tendência

`outputs/diagnostico-correcao-tau-eventos-20260921/` reutiliza exatamente os
quatro grupos e as tendências na origem já preservados no diagnóstico do
proxy Carreiro. Não seleciona limites de eventos a partir dos erros, não
ajusta modelos e não implementa troca de constante por grupo ou tendência.
Os três cenários continuam com os mesmos 23.538 alvos e falhas.

Na comparação tau6→tau12, em 12 horas, os acertos no modelo com níveis
de reservatórios foram: primeiro grupo de julho 26→28/35; grande grupo
de julho 18→27/133; meados de agosto 17→22/49; fim de agosto 10→8/18.
O MAE desse último grupo piorou 0,5620→0,6214 m. Dar peso igual aos
quatro grupos reduz o MAE médio 0,9032→0,8524 m e aumenta a média das
frações de acerto 44,52%→47,41%; essa média não substitui a meta original
nem transforma os grupos em eventos independentes certificados.

Em 6 horas, no conjunto geral, as perdas de acertos apareceram em todas
as tendências conhecidas: subida 368→361/455, descida 602→570/837,
estável 482→450/625. Portanto a tendência anterior à emissão, sozinha,
não justifica adotar automaticamente tau12 quando o rio sobe. O recorte
de cheia usa o nível observado no alvo e não pode ser um seletor operacional.

216 conferências confirmaram que as partições reproduzem contagens,
acertos e MAE ponderado do conjunto anterior em todos os prazos e modelos.
Dois grupos têm lacunas e todos permanecem sem certificação das referências.
Não houve promoção. A rodada anterior produziu evidência nova e constitui
progresso; a meta permanece ativa e não demonstrada.

## Emissão das 21 horas e contrato oficial legado

O ciclo `outputs/mucum-hourly-20260921T210023-0300/` terminou às
21:02:20 BRT de 21/09. A última leitura aprovada usada foi 15,56 m às
20:30, com idade real de 32,34 minutos na emissão. As duas séries
preservam 14 alvos nominais e cobrem as faixas reais de antecedência de
1 a 12 horas. Foram verificados, para cada emissão, 56 artefatos,
207 recibos de entrada, seus hashes e a conclusão do mesmo ciclo.

O Radar prevê 16,3449 m às 22h e 17,6471 m às 11h do dia seguinte;
o HGE experimental, 17,3344 m e 21,6935 m nesses mesmos alvos. Essas
previsões divergentes não são intervalo de confiança. O HGE tem 12
estimativas de vazão acima do máximo de treino e 28 modelos de vazão
com alguma entrada fora da faixa histórica, sinalizados sem corte artificial.
O relatório `20260922T000220562707Z` contém 218 comparações: 32
pareadas, 14 com horário vencido mas observação exata ainda ausente,
172 não vencidas. Nenhuma comparação é elegível à meta por enquanto.

A pesquisa `outputs/pesquisa-referencia-legacy-20260921/` preservou
três recursos oficiais novos: DISCO e duas URLs do WSDL, estas com
conteúdo idêntico. O contrato define a operação consultada, mas retorna
schema/diffgram genérico sem declaração de fuso de DataHora ou referência
de nível da estação. Não resolve a vigência do zero de régua em 2025–2026
nem a diferença documental entre 33,985 e 33,96 m. Nenhum contato externo,
flag de elegibilidade ou modelo foi alterado. A busca negativa é limitada
ao acervo e às três fontes consultadas, não prova que inexista documentação.

## Última rodada histórica HGE: resíduo autorregressivo

Antes da instrução de remoção do HGE, foi concluído e preservado o
experimento `outputs/experimento-residuo-autoregressivo-20260921/`.
Doze regressões ridge, alpha 1000 fixo, aprenderam resíduos de reconstrução
com quatro entradas anteriores à origem e labels estritamente anteriores
a 01/07/2026. A última data de alvo do treino é 30/06 às 23h; os tamanhos
de treino são 10.694 pares em 1 hora e 10.675 em 12 horas. Não houve
ajuste nos alvos julho–setembro, mas esse período já é desenvolvimento
inspecionado. Resíduos internos ao treino não constituem validação externa.

No modelo com níveis de reservatórios, em cheias os acertos em 12 horas
passaram de 71 para 89/235 (30,21%→37,87%) e o MAE de 1,3752 para
1,2436 m. Em 6 horas os acertos gerais pioraram 1458→1425/1926.
Por família, 23.019 previsões receberam a correção aprendida, 228 usaram
o fallback original por falta de entrada, 288 preservaram a ausência da
previsão-base, e três falharam por vazão corrigida negativa. Não foram
cortadas em zero nem ocultadas. Todas as 147 linhas sem alvo mantiveram
sua previsão. A avaliação preserva amostras individuais e comuns.

126 testes passaram. A âncora reproduzida tem diferença zero; o estado
HGE anterior à origem permaneceu idêntico após perturbar chuva futura
em três origens. “Reconstrução finalizada” inclui chuva estimada em área
sem cobertura e proxies/grade histórica de montante; não representa
forçantes exclusivamente medidas. A definição e os parênteses da fórmula
da âncora foram esclarecidos em documentation-clarification.json sem
reescrever o protocolo ou código usados na execução. Não houve promoção.

## Mudança de escopo: continuar somente com Radar

Em 21/09/2026, às 21h11 BRT aproximadamente, a tarefa coordenadora
`01a0c670-24dd-7fc3-ac9b-256c3d9b27e5` repassou a instrução expressa
do usuário: “REMOVA O HGE”. Esta orientação substitui a parte anterior
da meta que solicitava manter os dois modelos. Novas execuções e pesquisas
HGE/ARNO foram interrompidas; recibos, experimentos e falhas anteriores
continuam preservados como histórico auditável. A coordenadora cuida da
remoção do runner, relatórios ativos, site e automação, sem edição concorrente
desses arquivos por esta tarefa.

A meta de 98%, a tolerância de 0,50 m, a avaliação por antecedência real
de 1–12 horas e as exigências prospectivas por cheia permanecem iguais,
agora aplicadas somente ao Radar. O próximo trabalho deve partir das
previsões e erros do Radar, sem promover este candidato derivado do HGE.

## Radar: cobertura histórica e diferença entre ambientes

A auditoria `outputs/auditoria-cobertura-radar-20260921/` confirmou que
o filtro histórico de avaliação exigia os primeiros 24 campos de níveis
e variações preenchidos, enquanto a inferência operacional aceita ausências
nesses campos quando o nível-base de Muçum está presente. Em 1, 6 e 12
horas isso excluiu, respectivamente, 589/1.939, 584/1.927 e 578/1.915 pares
calculáveis. Nas cheias, excluiu 92/236, 96/236 e 96/236, incluindo o alvo
de 19,86 m. As exclusões não são apenas campos auxiliares: incluem também
algumas variações passadas de Muçum. Todos os pares de cheia excluídos
tinham alguma entrada de Passo Carreiro ausente. O subconjunto antigo foi
reproduzido exatamente; sua precisão não pode representar os casos excluídos.

O primeiro ensaio `outputs/experimento-radar-ausencias-nativas-20260921/`
parou antes de calcular o candidato de teste ao detectar diferença de
0,001403 m na primeira previsão antiga. Modelos parciais, protocolo, código
e motivo da interrupção foram preservados. Os dois procedimentos de
construção das 60 acumulações meteorológicas produziram os mesmos valores
e ausências; os índices de treino também eram idênticos.

O replay em `outputs/auditoria-reproducao-radar-legacy-20260921/`, usando
o ambiente antigo preservado (Python 3.9.6, NumPy 2.0.2, scikit-learn 1.6.1),
reproduziu exatamente as 1.350 previsões de uma hora. No ambiente atual
(Python 3.12.14, NumPy 2.5.3, scikit-learn 1.9.1), a diferença máxima foi
0,090797 m. Em cada ambiente, 1, 2 e 4 threads deram resultados idênticos.
A inspeção das bibliotecas encontrou mudança no binning ponderado das
árvores; o teste compara ambientes completos e não isola apenas essa
mudança interna como causa única. Isso não justifica alterar resultados
ou recibos antigos, que permanecem associados às suas versões.

Antes de olhar resultados do candidato de teste, foi registrado
`docs/radar-native-missing-runtime19-protocol.json`: referência e candidato
ajustados no mesmo ambiente atual, com diferenças contra o acervo antigo
explicitamente salvas. A referência desse ensaio é um novo ajuste;
não há reivindicação de reprodução numérica do modelo antigo nesse ambiente.

O experimento completo em
`outputs/experimento-radar-ausencias-nativas-runtime19-20260921/` ajustou
48 modelos Radar: referência/candidato, dois cortes temporais, 12 horizontes.
O candidato apenas retirou a exigência de todos os 24 primeiros campos
preenchidos no treino, mantendo o nível-base e alvo finitos. Ambos inferiram
as mesmas origens com nível-base disponível. Validação: 78.546 agendamentos,
77.664 pares. Teste: 23.538 agendamentos, 23.115 pares, dos quais 7.002 eram
excluídos pelo filtro de completude. As 147 previsões sem alvo foram mantidas.

Resultados do teste completo, sem selecionar pela presença de entradas:
em 1 hora, os acertos gerais foram 1933→1932/1939 e de cheia 230→230/236
(97,46% na cheia). Em 6 horas, gerais 1759→1745/1927 e cheia 154→147/236
(65,25%→62,29%). Em 12 horas, gerais 1296→1338/1915 e cheia 75→86/236
(31,78%→36,44%). O MAE de cheia em 12 horas caiu 1,3995→1,3408 m, mas
o maior erro aumentou 7,1202→7,9215 m. Não houve ganho consistente nem
promoção. Os percentuais acima são históricos de desenvolvimento, sem
equivalência com evidência prospectiva dos 98%.

751 verificações independentes confirmaram memberships/cutoffs, 180
preditores, inferência dos 48 modelos com diferença zero, cobertura e
comparação contra os 16.113 pares arquivados. O maior desvio entre ambiente
antigo e atual nesses 12 horizontes foi 1,1784 m, distinto da diferença
máxima de 0,0908 m documentada apenas em 1 hora. Duas verificações unitárias
focadas confirmaram tratamento de faltas e exclusão de labels no corte.

A captura ANA às 21:22:14 BRT preservou 15,85 m às 21h e 15,73 m às
20h45. O Radar emitido às 19h02 errou 0,1425 m no alvo de 21h, na faixa
real de 1–2 horas; o emitido às 18h02 errou 0,5558 m, na faixa real de
2–3 horas. O relatório ativo somente Radar
`outputs/monitoramento-prospectivo/reports/20260922T002214126619Z/`
tem 109 comparações, 23 pareadas e 86 não vencidas. Os registros HGE
continuam históricos; sua retirada da visão ativa não apaga recibos.
Nenhum par ainda satisfaz a certificação necessária à meta.

## Radar com níveis de reservatórios, mantendo o treino de referência

`outputs/experimento-radar-niveis-reservatorios-20260921/` acrescentou
24 preditores de nível/variação de montante e jusante das três usinas
CERAN aos 180 preditores do Radar. Reutilizou os 24 controles congelados
da rodada anterior, sem refit e com reprodução exata de suas previsões.
Treinou 24 candidatos nas mesmas linhas, parâmetros, pesos, cortes e
runtime. A política descartada de ampliar o treino com faltas não foi
incorporada; a única mudança aqui são as 24 colunas. Não houve HGE.

Os 102.084 agendamentos, alvos e disponibilidade de previsões permaneceram
idênticos. Na cheia do teste, 6 horas passou 154→158/236 acertos e MAE
0,6237→0,6076 m; 12 horas passou 75→84/236 e MAE 1,3995→1,3275 m,
com máximo 7,1202→6,8643 m. Em 2 horas houve perda de três acertos.
Na fase validation, cheia de 12 horas passou 8→11/28 acertos, mas 4 horas
perdeu um. Há ganhos nos prazos longos, não uma melhora uniforme; nenhum
prazo foi selecionado posteriormente para substituir parte da operação.
Não houve promoção, emissão do candidato ou mudança da automação.

A auditoria das entradas em
`outputs/auditoria-features-reservatorios-radar-20260921/` reconstruiu
as 24 colunas exatamente a partir de 38.764 linhas ONS/18 arquivos,
com 77.568 seleções rastreadas e 67 verificações aprovadas. O atraso
presumido é 60 minutos; o limite de 90 minutos é contado depois desse
atraso, permitindo até 150 minutos de idade na origem. O maior valor
efetivamente aceito foi 121 minutos. O registro 23h59 permaneceu literal
e a ausência mais recente não foi substituída por leitura anterior finita.
Cinco testes focados de corte/ausência/tempo passaram. A disponibilidade
de publicação continua assumida, não certificada. Os níveis não foram
convertidos em armazenamento ou misturados entre referenciais.

A verificação independente final em
`outputs/verificacao-radar-niveis-reservatorios-20260921/` passou 385
checks sem refit: 102.084 chaves/alvos/bases, composição exata dos 204
preditores, inferência dos 24 controles e 24 candidatos, índices e cortes
de treino, configuração/interceptos e cobertura. Todos os campos das
métricas da referência anterior foram preservados. Essas verificações
confirmam a execução e a comparação, não validação prospectiva nem
certificação dos 98%. A meta continua ativa somente para o Radar.

## Compatibilidade dos novos campos com a coleta CERAN das 21h

`outputs/auditoria-compatibilidade-ceran-radar-20260921/` comparou os três
HTMLs CERAN preservados às 21h com o CSV ONS usado nas entradas históricas.
São 48 horas por usina; 37 timestamps comuns por usina e dois campos
produzem 222 pares exatamente idênticos. Os registros 23h59 ONS não foram
deslocados para parear com 00h CERAN. Essa coincidência numérica limitada
não certifica datum, fuso, sensor ou disponibilidade histórica.

O vetor atrasado da origem 21h tem 24/24 campos finitos, com reconstrução
independente exata. Porém 17 campos estão fora das faixas efetivamente
usadas por cada um dos 12 modelos da fase test; na fase validation são
18 campos. Por exemplo, o montante Castro Alves é 246,96 m contra máximo
de treino test de 243,94 m. Todos os 24 conjuntos de treino tinham zero
linhas com faltas nessas novas colunas: aceitar NaN mecanicamente não
equivale a ter aprendido o regime de falhas dessas fontes.

Comparando snapshots das 18h e 21h, uma de 270 leituras comuns mudou:
montante Castro Alves de 21/09 às 17h, 246,22→246,17 m. Ambas as versões
foram preservadas. Essa leitura é posterior ao fim do CSV ONS e não está
entre os 222 pares comparados. A coleta das 21h foi recebida às 21h00min28s;
a reconstrução posterior não foi lançada como previsão prospectiva às
21h. Nenhum modelo foi ajustado, promovido ou emitido nesta auditoria.

## Combinação Radar: treino com faltas e níveis de reservatórios

O protocolo prévio `docs/radar-native-reservoir-protocol.json` fixou a
combinação das duas mudanças já testadas isoladamente: 204 preditores
e treino sem exigir completude nas 24 primeiras entradas de telemetria.
Mantiveram-se parâmetros, pesos, runtime, cortes cronológicos e exclusões
das fronteiras. `outputs/experimento-radar-ausencias-reservatorios-20260921/`
ajustou 24 modelos novos e reutilizou os três controles congelados, sem
refit. São os mesmos 102.084 agendamentos e disponibilidade de previsão.

Na cheia da fase test, a combinação manteve 230/236 acertos em 1h. Em 6h
teve 156/236 contra 154 da referência, 147 do treino com faltas e 158
dos níveis adicionais; MAE 0,5760 m contra 0,6237/0,6010/0,6076 m.
Em 12h teve 80/236 contra 75/86/84, MAE 1,3318 m e maior erro 7,6867 m,
superior aos 7,1202 m da referência e 6,8643 m dos níveis adicionais.
Na validation, 6h caiu de 24 para 23/28 acertos contra a referência;
12h ficou 8/28, com MAE 0,9060 m contra 0,7742 m. Não há dominância
consistente da combinação, seleção posterior de versões por horizonte
ou promoção. Todos os horizontes permanecem no relatório comparativo.

O treino ampliado inclui mais alvos altos (fase test: 255 alvos ≥7 m nos
horizontes 1/6/12h, contra 189/191/198), porém as 7/6/6 linhas com faltas
nos novos campos pertencem a um único dia de nível baixo. Além disso,
três campos agora parecem dentro da faixa porque o treino inclui o pico
suspeito de jusante Julho de 168,74 m e suas inclinações. A redução de
17 para 11 entradas fora da faixa não comprova cobertura física melhor.

`outputs/verificacao-radar-ausencias-reservatorios-20260921/` reproduziu
exatamente a inferência dos 24 novos modelos, conferiu memberships,
cortes, contagens, configuração e 84 hashes de entradas. As 432 linhas
de métricas dos controles coincidem integralmente com as rodadas
anteriores. Cinco testes focados passaram. Os ganhos/perdas são de
desenvolvimento histórico; não são evidência prospectiva dos 98%.

A revisão independente recalculou os 24 resultados de cheia da combinação.
Há 237 alvos altos observados por horizonte de test, dos quais 236 pares
e uma falha por falta do nível-base, igual nas quatro versões. Os acertos
citados sobre 236 não incluem essa falha no denominador: em 1h, 230/236
é 97,46%, enquanto 230/237 é 97,05%. Ambos ficam abaixo da meta.

## Diagnóstico dos extremos de julho, sem novo ajuste

`outputs/diagnostico-extremos-radar-20260921/` rastreou os maiores erros
das quatro versões. As 12 maiores falhas de 12h da combinação têm origem
em 21/07/2026 entre 12h e 23h, todas sem os seis campos de nível/variação
do Carreiro. No pior caso, origem 19h, base 3,42 m, alvo 16,50 m às 07h
e previsão 8,8133 m: erro −7,6867 m. A resposta alvo−base de 13,08 m
excede o máximo de treino de 8,09 m. Ampliar o membership com faltas não
mudou os extremos da resposta de treino em 1h, 6h ou 12h. A base tem
atraso imposto de 15min; a resposta não é uma diferença entre medições
exatamente separadas pelo horizonte nominal.

Em 12h na cheia test, acima do máximo de treino são 0/12 acertos e MAE
6,6862 m; abaixo do mínimo, 3/26 e 1,7242 m; dentro da faixa, 77/198 e
0,9558 m. A falha sem nível-base permanece fora desses 236 pares. Mesmo
dentro da faixa o desempenho é insuficiente, portanto ampliar amplitudes
ou corrigir uma estação isolada não demonstraria a meta. A estratificação
descreve associação e não prova causalidade. Todos os 192 grupos de
métricas foram reconciliados com os totais anteriores, e os vetores de
204 campos nas 12 origens foram preservados em 2.448 células rastreáveis.

O dia-alvo 22/07 representa 11,58% da soma de erros absolutos dos 1.915
pares de test em 12h; 23/07 acrescenta 5,35%. São dias civis diagnósticos,
não eventos independentes certificados. Os períodos foram escolhidos
depois de observar os erros e não viraram holdout nem foram retirados da
avaliação. Nenhum treino, promoção ou mudança operacional nesta análise.

A fonte original do Carreiro confirmou 47 registros de 15min entre
11h30 e 23h de 21/07, mas 46 níveis vazios e somente um aprovado às
17h (5,70 m). Com atraso imposto de 30min, esse ponto aparece às 17h30;
às 17h45 a seleção já encontra o registro das 17h15 vazio, preservado.
Não é apenas desalinhamento de grade nem rejeição de QC. O agente
reconstruiu exatamente os 24 primeiros campos: 72 células Carreiro
ausentes nas 12 origens, outros 18 campos sempre finitos. A leitura
antiga não foi propagada através das ausências para melhorar métricas.

## Ciclo regular Radar das 22h

`outputs/mucum-hourly-20260921T220010-0300/` concluiu a coleta de 133
fontes públicas sem erros e emitiu somente Radar às 22h02min08s BRT.
Última observação utilizada: 16,17 m às 21h30, com idade real aproximada
de 32min09s na emissão. Recibo
`bc57eee5908f2544692f44f1a34cd20c16db7fc77cbf34e5ca9942b2631400e3`.
Foram conferidos 22 artefatos, 202 recibos de entrada e a conclusão do
ciclo. Há uma única emissão regular Radar para essa hora, com cobertura
das bandas reais de 1 a 12h; os pontos nominais extras permanecem com
as limitações já registradas.

Previsão experimental: 17,1380 m para 23h; 18,3368 m para 02h; 17,2498 m
para 10h. Esses valores não são observações e não demonstram acurácia.
O relatório prospectivo está em
`outputs/monitoramento-prospectivo/reports/20260922T010208631083Z/`.
O novo ensaio combinado e o diagnóstico de julho não foram promovidos.

## Viabilidade de respostas extremas nos acervos antigos

`outputs/viabilidade-historico-antigo-radar-20260921/` examinou 49.302
origens/horizontes usando somente pares exatos aprovados: base O−15min,
alvo O+h. Em 12h, há 1.141 pares em junho–julho/2020, 480 em setembro/2023
e 2.195 em março–maio/2024. Respectivamente 9, 3 e 7 respostas excedem o
máximo atual de treino de 8,09 m, com máximos 11,53/12,59/9,35 m. São
potenciais exemplos, não matrizes completas prontas para treinar.

Os 19 pares extremos têm Q/I e níveis correntes das três usinas presentes
sob a regra temporal literal. Não foram auditados aqui todos os atrasos,
chuva ou estações auxiliares. As sete origens de 2024 ficam em 01/05 de
04h a 10h, antes da avaria documentada de 02/05; o apagão posterior não
foi preenchido. Referências, fuso, sensores e regime físico continuam
pendentes. Foram reproduzidos 13.518 níveis aprovados diretamente dos XMLs
de 2020/2024 e conferidos quatro derivados contra seus hashes congelados.

O agente preservou seis consultas ao campo exato precipitation_previous_day1
em `outputs/pesquisa-cobertura-meteorologica-antiga-20260921/`: um ponto,
três modelos, um dia por consulta. Amostras de 2020 e 2023 retornaram todos
os valores nulos; três dias amostrados em março/abril/maio de 2024 tiveram
todos os valores finitos. A documentação oficial situa o arquivo geral
desde 2024; produtos Historical Forecast/reanálise/hindcast não substituem
o campo usado. Não há certificação de publicação histórica ou cobertura
integral dos meses e cinco pontos.

Prioridade seguinte: completar os insumos para abril até 01/05/2024,
com aquecimento e alvos anteriores a 02/05, respeitando a fronteira
operacional documentada. Não houve treino, promoção ou nova alocação
de holdout; os períodos já foram inspecionados e seguem como pesquisa.

## Coleta completa dos insumos para abril–01/05/2024

O protocolo `docs/radar-inputs-2024-collection-protocol.json` foi registrado
antes da coleta. `outputs/radar-insumos-2024-hidrologia-20260921/` preservou
29.449 registros ANA (27 estações consultadas) e 6.060 linhas ONS das três
usinas. Foram 80 requisições novas e quatro fontes reutilizadas com hash.
As 10 respostas ANA “Sem dados” são HTTP200, não falhas de transporte:
três cada de 86493000, 86500000 e 86504900, e uma de 86479000 em 01/05.

No intervalo 29/03–01/05, Muçum tem 3.264 níveis aprovados; Linha José Júlio
3.175 aprovados/84 vazios/5 suspeitos; Santa Tereza 3.232/26/2, além de
quatro timestamps ausentes. Carreiro não tem registros nas três janelas.
A revisão independente dos 24 campos com os atrasos congelados confirmou
que complete24 admitiria zero das 744 origens novas. Os outros 18 campos
estariam completos em 683. Logo, testar o acréscimo exige contrastá-lo com
uma referência que já aceite faltas; não imputar Carreiro silenciosamente.

A chuva tem cadências horárias, de 30min e de 15min, incluindo segundos
:02 preservados. Não usar 3.264 slots como denominador de todas as fontes.
Duas estações trazem QC aprovado de chuva, mas valor sempre vazio, que
permanece ausente. A matriz de chuva por bacia ainda precisa ser montada.

`outputs/radar-insumos-2024-meteorologia-20260921/` fez três requisições
com os cinco pontos originais: 12.600 valores finitos e 44.640/44.640
janelas completas para as 744 origens. As 15 grades, unidades mm e offset
UTC−3 conferem. Não há certificação de publicação histórica/vintage.
Foram conferidos 84 hashes de fontes hidrológicas e 13 artefatos meteo;
o agente conferiu os 81 XMLs ANA. DuckDB temporário foi removido após
extrair os Parquets, sem alterar runtimes compartilhados. Nenhum treino
ou promoção foi realizado; os arquivos ainda são insumos para pesquisa.

A captura prospectiva às 22h17 preservou 16,32 m às 21h45, recibo
`113eccb5fd457173ce326501b977eb60473ee0f4eae7f638dfaf7f3a21b92b97`.
A leitura exata das 22h ainda não estava na resposta; não substituí-la
pelo valor das 21h45 na verificação. Relatório:
`outputs/monitoramento-prospectivo/reports/20260922T011700478388Z/`.

## Matriz auditada de abril–01/05/2024

`outputs/radar-matriz-2024-20260921/` tem 744 origens horárias e 180
campos, com 6.326 ausências entre 133.920 células. As seis colunas do
Carreiro continuam ausentes; nenhuma origem satisfaz complete24, mas
as outras 18 colunas de nível estão completas em 683 origens. Base e
nível observado no horário da origem estão presentes em todas as 744.
Os alvos futuros são deslocados separadamente por horizonte: 743 pares
em 1h, 738 em 6h e 732 em 12h, sempre antes de 02/05/2024.

As latências das 27 estações de chuva foram reconstruídas do snapshot
original das 15h, reproduzindo exatamente 60 campos regionais em 51.709
linhas de 15min. Foi preservado o arredondamento por truncamento da
referência: 181min em 86125000 viram 12 passos, ou 180min. Isso isola o
efeito do novo histórico; não certifica publicação histórica real.

O agente verificou 124 critérios em
`outputs/verificacao-radar-matriz-2024-20260921/`: 44.640 células de
previsão meteorológica, 2.976 seleções de nível e 15.624 células Q/I
conferem. As 186 seleções ONS de timestamps 23h59 foram mantidas
literalmente. Os 57 hashes de fontes conferem. A auditoria adicional
`outputs/auditoria-chuva-matriz-2024-20260921/` reconstruiu diretamente
dos intervalos ANA normalizados as 55.800 células dos 75 campos de
chuva, sem chamar os helpers originais: máscaras idênticas, diferença
máxima numérica de 2,28e-13. As fontes normalizadas já haviam sido
comparadas independentemente aos XMLs. Fuso, datum, publicação e
comparabilidade física continuam sem certificação.

## Ensaio de acréscimo de2024 à referência de180 campos

Protocolo anterior ao treino:
`docs/radar-2024-augmentation-protocol.json`. Resultado:
`outputs/experimento-radar-historico-2024-20260921/`. Foram treinados
24 modelos, mantendo parâmetros, pesos e pertencimento original ao
treino e acrescentando todo o intervalo elegível de2024. Não houve
seleção de exemplos extremos, preenchimento do Carreiro ou busca de
parâmetros. A referência congelada é a versão de180 campos que já
aceita ausências auxiliares; não confundir com a versão operacional
ou com o ensaio de204 campos. Os 24 controles não foram retreinados.

As 102.084 linhas de avaliação, alvos, bases e disponibilidade foram
preservadas. Em12h entram 732 exemplos, 41 deles com alvo>=7m. A maior
resposta de treino sobe de8,09m para9,35m; continua abaixo de respostas
observadas no período posterior. Não se atravessou o hiato entre2024
e2025 para construir alvos. Os últimos h exemplos de2024 permanecem
inelegíveis.

Na cheia de test, com236 pares e uma falha por horizonte, os resultados
referência→acréscimo foram:

- 1h: 230→231 acertos; MAE0,07749→0,06869m; máximo1,27599→1,00147m.
- 6h: 147→155 acertos; MAE0,60098→0,54344m; máximo5,64366→5,27045m.
- 12h: 86→88 acertos; MAE1,34076→1,28390m; máximo7,92153→8,08807m.

O resultado não domina a referência: em test8h perde14 acertos e em9h
perde8; na fase validation perde acertos de cheia em7 dos12 horizontes.
No recorte diagnóstico de12 respostas superiores a8,09m em12h, dez
erros diminuem e dois aumentam, mas nenhuma das versões acerta dentro
de0,50m. O MAE desse recorte cai de6,79519m para6,32155m. O maior erro
do candidato ocorre em21/07/2026 16h para22/07 04h: previsão6,40193m,
observado14,49m. Esse recorte foi examinado depois dos resultados e
continua diagnóstico, sem certificação de evento independente.

`outputs/verificacao-radar-historico-2024-20260921/` reproduziu os24
modelos exatamente, recalculou288 linhas de métricas e conferiu144
linhas do controle com a referência. Máscaras, cortes, parâmetros,
contagens por árvore,36 hashes de entrada e36 de artefatos conferem.
O agente também recalculou independentemente as métricas de cheia.
Oito testes focados de regras temporais, ausências e chuva passaram.
Sem promoção, sem mudança operacional e sem comprovação de98%.

Próximo trabalho: usar as regressões e o erro de resposta extrema para
orientar um protocolo novo, mantendo estas fases como desenvolvimento.
Não selecionar versões por horizonte nem ajustar na mesma cheia e
apresentar o resultado como validação independente.

## Observação exata das22h disponível

A captura às22h30min40s BRT preservou16,45m às22h, aprovado pela fonte,
recibo `28d4120d141be07622885737acce4d9c44b10027083196ec471e5775d4d25967`.
O relatório `outputs/monitoramento-prospectivo/reports/20260922T013040261556Z/`
agora contém31 pares previsão–observação e92 alvos ainda não vencidos; os oito
alvos das22h anteriormente sem observação puderam ser confrontados.
Continua com zero pares elegíveis para declarar a meta, devido às
pendências de metadados e demais requisitos. Nenhuma nova emissão
regular foi feita nesta captura; o ciclo das22h permanece único.

## Suporte dos exemplos extremos nas árvores congeladas

`outputs/diagnostico-suporte-extremos-radar-20260921/` examinou as duas
versões de12h sem retreinar. O roteamento manual de todas as amostras
reproduziu as contagens de todas as folhas nas360 árvores; a soma da
resposta inicial com as contribuições das180 árvores reproduziu as
previsões dos12 casos extremos exatamente.

Os sete exemplos acrescentados de2024 com resposta>8,09m começam com
Muçum entre13,70 e15,11m. Os12 casos posteriores difíceis começam entre
3,21 e10,42m. Restringindo descritivamente o treino a essa última faixa,
há2.285 pares originais com máximo8,09m e152 novos com máximo8,01m:
o máximo combinado nesse recorte permanece8,09m. A faixa foi escolhida
depois de examinar os erros; não virou filtro de treino ou avaliação.

No pior caso novo,21/07 às16h, a resposta real é11,22m e a prevista
3,13193m. Só46/180 árvores compartilham a folha desse caso com algum
dos sete exemplos extremos de2024. A fração média do peso desses
exemplos nas folhas é1,0645%, mas isso não é seu peso final na previsão:
as folhas do boosting aprendem correções residuais. A contagem dos
primeiros cortes divergentes também não constitui importância causal.
Esse diagnóstico mostra uma lacuna na combinação de nível inicial e
resposta, sem estabelecer uma causa única para o erro ou garantir que
mais dados a resolverão. Nenhuma entrada foi deslocada artificialmente.

## Levantamento observado delimitado de setembro2023

O agente realizou oitoGET ANA para29/08–04/09/2023, depois de conferir
reaproveitamento, em `outputs/pesquisa-insumos-observados-2023-20260921/`.
Linha José Júlio tem672/672 níveis aprovados; Santa Tereza e Passo
Carreiro retornam “Sem dados”, HTTP200. Os cinco postos de maior peso
regional têm chuva observada, mas Baixo Antas86450000 termina em04/09
03h e Carreiro86479000 em09h. Alto Antas e Prata têm168 horários
completos cada; Tainhas tem631 chuvas aprovadas em636 registros.

O lote de oito postos é somente levantamento: seus pesos conhecidos
ficam abaixo de0,5 em três regiões, portanto não constitui reconstrução
regional válida. Não houve renormalização dos pesos nem preenchimento.
Foram conferidos31 hashes e os1.945 registros normalizados reproduziram
integralmente os oitoXMLs. Muçum, ONS e NWP não foram consultados de novo.

Próximo passo autorizado de pesquisa: completar as estações observadas
necessárias, com janelas e margens pré-definidas, e preparar controle
histórico de120 campos sem previsão meteorológica antes de medir o
efeito de adicionar2023. Separar a remoção dos60 campos NWP do acréscimo
de novas amostras; não tratar a comparação pontual das22h em outro
artefato como validação histórica. A série de Muçum segue sem pico
aprovado; marcas retrospectivas não serão convertidas em alvos horários.
Nenhuma nova matriz, treino ou promoção foi realizada nesta etapa.

## Controle histórico de120campos observados

O protocolo `docs/radar-observed-only-protocol.json` foi registrado
antes do ajuste. `outputs/experimento-radar-observado-120-20260921/`
treinou24 modelos retirando apenas os60 campos de previsão meteorológica
da referência nativa de180campos. Não entrou dado novo de2023/2024,
não se impôs chuva futura igual a zero e não houve busca de parâmetros.
Os parâmetros permanecem os originalmente escolhidos para180campos:
é uma ablação sem otimização, não a melhor configuração possível de120.

As102.084 linhas de avaliação, alvos, bases, regras de ausência e amostras
de treino permaneceram idênticas. Os24 controles foram recarregados,
não retreinados, e reproduzidos exatamente. O ensaio de120campos fica
congelado como controle para eventual acréscimo de séries antigas sem
NWP, separando o efeito da mudança de entradas do efeito dos dados novos.

Na cheia de test, sempre236 pares e uma falha por horizonte:

- 1h:230→230 acertos; MAE0,077488→0,077472m; máximo1,27599→1,28483m.
- 6h:147→149 acertos; MAE0,60098→0,59927m; máximo5,64366→5,71730m.
- 12h:86→83 acertos; MAE1,34076→1,36181m; máximo7,92153→7,59000m.

O resultado é misto: perde acertos de cheia em test4h/7h/8h/10h/12h,
ganha em5h/6h/11h e empata nos demais. Na validation12h,8→7 acertos
entre28 pares. Retirar NWP não resolveu a subestimação das cheias e
não demonstrou vantagem geral. Nenhuma combinação por horizonte foi
montada a partir dos resultados.

`outputs/verificacao-radar-observado-120-20260921/` reproduziu os24
modelos de120campos exatamente e recalculou288 linhas de métricas.
As144 linhas do controle conferem com a referência, assim como máscaras,
cortes, parâmetros e contagens por árvore. Foram conferidos36 hashes
de artefatos e34 de entrada. Todas as fases continuam desenvolvimento
já inspecionado; sem promoção, emissão nova ou comprovação de98%.

## Acervo observado2023 ampliado para as27estações

`outputs/radar-insumos-observados-2023-20260921/` cobre a janela solicitada
29/08–30/09/2023, com margem de aquecimento anterior a setembro. O plano
foi registrado antes das27 novas requisições ANA, todasHTTP200. Foram
reutilizados11XMLs, incluindo os oito da sondagem e Muçum já coletado.
Das38 respostas,31 têm registros e sete são “Sem dados”. O conjunto
preserva19.265 linhas e17.083 chuvas numéricas aprovadas, em27JSONL e
27NPZ com qualidade e proveniência. Valores suspeitos, negativos e
ausentes não foram corrigidos nem automaticamente admitidos no treino.

Muçum tem2.652 registros,2.311 níveis aprovados,11 suspeitos e330 vazios;
a última linha é25/09 22h45. Linha José Júlio tem2.683 registros,
2.682 níveis aprovados e um vazio, terminando25/09 22h30. Santa Tereza
tem somente16 registros em30/09 20h–23h45, todos com nível e chuva
vazios. Carreiro não tem registros. As duas maiores estações de chuva
86450000/86479000 não voltam após suas interrupções de04/09. Nenhuma
dessas lacunas foi preenchida para tornar a matriz artificialmente
completa; a coleta do mês não significa disponibilidade durante todo ele.

Os CSVs ONS literais já preservados de agosto e setembro foram apenas
referenciados e conferidos por hash:744 e714 linhas por usina,
respectivamente. Não houve novas consultas ONS/NWP nem reinterpretação
de23h59. A marca retrospectiva do pico de Muçum continua separada.

O agente concluiu320 verificações do acervo. A reconciliação adicional
`outputs/verificacao-insumos-observados-2023-20260921/` conferiu118 hashes,
os38XMLs e todos os19.265 registros das27séries, campo a campo, incluindo
QC e origem. Arrays numéricos de quatro grandezas, QC, timestamps e
referências ONS também conferem. Isso verifica a normalização, sem
certificar disponibilidade histórica, datum ou comparabilidade física.

Próxima etapa: montar a matriz observada de120campos de setembro usando
as regras temporais congeladas, preservando todas as720origens horárias
e as ausências, e só então pré-registrar o acréscimo ao controle120.
Ainda não houve matriz ou treino com2023 nesta coleta.

A auditoria independente do ensaio120 em
`outputs/auditoria-independente-radar-observado-120-20260921/` concluiu122
verificações:48 linhas de métricas de cheia conferem até1e-12, com os
mesmos237 alvos/236 pares/uma falha em test e28/28 em validation.
A falha é a origem22/07/2026 às17h, preservada nas duas famílias.
Os resultados continuam mistos, sem promoção. Os sete artefatos dessa
auditoria e os118 do acervo2023 tiveram os hashes finais conferidos.

## Matriz observada2023 e ensaio de acréscimo

`outputs/radar-matriz-observada-2023-20260921/` mantém as720origens
horárias de setembro e120campos observados, sob o protocolo anterior
ao processamento `docs/radar-2023-observed-features-protocol.json`.
São506 bases finitas,505 níveis observados no horário da origem e
23.799 células ausentes. Santa Tereza e Carreiro ficam ausentes nas
12colunas correspondentes; nenhuma origem tem complete24.

Há503 pares elegíveis em1h,493 em6h e481 em12h, com56/51/45 alvos>=7m.
As máximas respostas respectivas são2,64/9,90/12,59m. O par de12h a
mais que a antiga análise de viabilidade vem da nova fonte de agosto:
base0,86m exatamente em31/08 23h45, origem01/09 00h e alvo1,43m às12h.
Não decorre de tolerância asof, interpolação ou preenchimento. Os
alvos continuam exatos, e a regra da base permanece igual à referência.

`docs/radar-2023-augmentation-protocol.json` foi registrado antes do
ajuste e esclarecido quanto ao par adicional antes de treinar.
`outputs/experimento-radar-historico-2023-20260921/` treinou24 modelos
de120campos com todos os pares elegíveis de setembro, sem acrescentar
2024, selecionar apenas extremos ou alterar pesos/parâmetros. Referência:
controle congelado de120campos, não o modelo de180campos. As102.084
linhas de avaliação e a disponibilidade foram preservadas.

Resultado de cheia test, controle120→acréscimo2023, com236 pares e uma
falha em cada horizonte:

- 1h:230→229 acertos; MAE0,07747→0,10057m; máximo1,28483→0,77670m.
- 6h:149→154 acertos; MAE0,59927→0,54572m; máximo5,71730→4,51347m.
- 12h:83→89 acertos; MAE1,36181→1,25671m; máximo7,59000→7,36283m.

Há regressão na validation: em6h,24→18 acertos e MAE0,25871→0,53129m;
em12h,7→3 acertos e MAE0,90849→1,21074m, entre28 pares. Esse resultado
não demonstra ganho sustentado nem autoriza promoção. Nenhuma versão
foi selecionada por horizonte após observar as métricas.

`outputs/verificacao-radar-historico-2023-20260921/` reproduziu os24
modelos exatamente, recalculou288 linhas de métricas e conferiu144
linhas do controle, máscaras, cortes, parâmetros e contagens das árvores.
Foram conferidos36 hashes de artefatos e36 de entrada. Permanece um
ensaio histórico de desenvolvimento, com limitações de metadados,
regime e publicação; sem comprovação de98%.

A auditoria independente da matriz em
`outputs/verificacao-radar-matriz-2023-20260921/` reconstruiu86.400
células dos120campos. Níveis, Q/I e2.880 seleções ANA conferem; as54.000
células de chuva foram reconstruídas por sobreposição de intervalos
medidos, com máscaras idênticas e diferença máxima1,99e-13mm. Os15
artefatos da matriz e três da auditoria tiveram seus hashes conferidos.

## Ciclo regular RADAR das23h

`outputs/mucum-hourly-20260921T230014-0300/` concluiu133 coletas públicas
sem erros e emitiu somente RADAR às23h02min10,864694s BRT. Última
observação utilizada:16,75m às22h30, idade real32min10,9s na emissão.
Recibo `cf0512133a9b6cac4f3e292c8f1dbfc4667e5546e25d8bee984b3bd55fc6ddbe`.

`verify_receipt.py` conferiu a cadeia do ledger, uma única emissão regular,
conclusão do ciclo,22 artefatos e202 recibos de entrada, tanto nos caminhos
de origem quanto nos blobs preservados. As14 inferências dos modelos
salvos foram reproduzidas exatamente. Há cobertura das bandas reais
1–12h; pontos nominais extras mantêm as limitações anteriores. O log foi
preservado em pipeline.log e a cópia temporária foi removida.

Previsões experimentais:17,5115m para00h,18,7081m para02h e17,5064m para11h.
Não são observações nem certificação do pico. Nenhum candidato120 ou
treino com2023/2024 foi promovido para essa emissão. O relatório
`outputs/monitoramento-prospectivo/reports/20260922T020210946249Z/` contém
31 pares confrontados, nove alvos sem observação exata disponível e97
ainda não vencidos; zero pares elegíveis para declarar a meta. As cinco
janelas horárias fechadas foram entregues, o que mede execução, não
assertividade. As pendências de metadados e eventos continuam explícitas.

A auditoria independente do acréscimo2023 em
`outputs/auditoria-independente-radar-historico-2023-20260921/` passou125
verificações e confirmou as48 métricas de cheia. Nesse recorte, a validation piora
MAE nos12 horizontes e não ganha acertos em nenhum; essa regressão
impede interpretar os ganhos de test como melhora geral. Nos12 casos
de test12h com resposta>8,09m,11 erros diminuem e um aumenta; o MAE
cai de6,770415m para5,777524m, ainda longe da tolerância de0,50m. O
caso que piora tem origem21/07/2026 às13h: erro7,347555→7,362831m.
O recorte é diagnóstico já inspecionado, não prova independente.
Sem promoção ou alteração das regras da meta.

## Diagnóstico da regressão e do suporte das entradas

`outputs/diagnostico-regressao-validacao-radar-20260921/` decompôs os
resultados sem alterar previsões. Os28 alvos de cheia da validation são
as mesmas28 observações consecutivas de08/11/2025 08h a09/11 11h em
todos os12 horizontes. São336 pares de previsão, não336 observações
independentes nem vários eventos certificados. A piora em todos os
12h se refere ao recorte de cheia; no conjunto geral o MAE de3h melhora.

Em12h, o viés positivo passa de0,6377m para1,1022m. O candidato elevou
as previsões em média0,4645m; seis casos melhoram e22 pioram. Em6h,
o viés passa de−0,0458m para+0,4812m, com cinco casos melhores e23
piores. Não há justificativa para subtrair esses vieses futuros na
operação: foram calculados depois dos alvos e usá-los seria vazamento.

Na validation12h com alvo>=7m, as15 respostas alvo−base>0,50m passam
deMAE0,9537m para1,4702m, com acertos6→2. As quatro respostas abaixo
de−0,50m e as nove dentro de±0,50m também pioram MAE. No test12h,
as104 respostas acima de0,50m melhoram MAE1,9941→1,7869m e acertos
23→26; as110 negativas melhoram0,8904→0,8508m e48→52. As22 próximas
dezero pioram0,7300→0,7799m. A classificação usa o alvo futuro apenas
para diagnóstico; não virou entrada ou filtro. As classes, incluindo
base indisponível, reconciliam96 grupos de contagens/acertos/erros.

O agente documentou entradas e pesos em
`outputs/diagnostico-entradas-validacao-radar-20260921/`. Todas as120
entradas das336 linhas de cheia da validation estão completas. Todas
as amostras novas de2023 têm os12 campos Santa Tereza/Carreiro ausentes.
Em12h, P24 Baixo Antas e Carreiro falta em404/481 novas amostras; as
coberturas medianas são0,329/0,051, contra0,988/0,948 na validation.
Logo, não é correto atribuir a regressão simplesmente à ausência de
sensores na validação. A distribuição do histórico adicionado difere,
mas essa comparação não identifica uma causa única.

O peso nominal acrescentado por2023 em12h é663:9,94% do ajuste da
validation e4,58% do test. Dos481 pares novos,45 têm alvo>=7m e
apenas cinco>=9m; o pico ausente não foi preenchido. Vazões da validação
excedem algumas faixas das amostras novas, o que não significa exceder
o treino original ou um limite físico. Foram conferidos seis hashes
do diagnóstico de erros e dez do diagnóstico de entradas/pesos.

Prioridade seguinte: testar uma hipótese explícita de compatibilidade
das entradas e de generalização antes de simplesmente acrescentar mais
anos ou mudar pesos para corrigir esse trecho já observado. Não houve
novo treino, promoção ou mudança operacional nesta etapa.

## Comparação fatorial de compatibilidade: 33 entradas e histórico de 2023

O protocolo `docs/radar-core33-compatibility-protocol.json` foi registrado
antes dos ajustes. `outputs/experimento-radar-core33-20260921/` compara
quatro famílias: 120 entradas originais, 120 com setembro de 2023,
33 originais e 33 com 2023. O subconjunto mantém os níveis e derivadas
de Muçum/Linha José Júlio e Q/I das três usinas. Retira os campos de
Santa Tereza/Carreiro e chuva; isso não significa irrelevância física
da chuva. Nenhum dado de 2024 entrou neste experimento.

Foram ajustados 48 modelos novos; os 48 controles congelados tiveram
suas inferências reproduzidas exatamente. Permaneceram idênticos os
parâmetros, pesos, máscaras, 102.084 linhas, bases, alvos e disponibilidade
de previsão. Os 20 pares admitidos de 2023 com alguma entrada ausente
nos horizontes 1/6/12 foram preservados. A auditoria de colunas em
`outputs/auditoria-colunas-core33-20260921/` reconstruiu 450.384 células
com diferença zero e conferiu cinco hashes. dQ corresponde à variação
da potência 0,6 da vazão normalizada, por hora; não é vazão bruta por hora.

Dentro da família de 33 entradas, acrescentar 2023 melhora o MAE de
cheia em nove dos 12 horizontes de validation e dez de test. Entretanto,
os acertos caem em um horizonte de validation e seis de test. A redução
120→33 sem acrescentar 2023 piora o MAE de cheia nos 12 horizontes de
validation. Portanto, o efeito favorável de adicionar o ano ao subconjunto
reduzido não equivale a superioridade da versão final.

Na validation de 6h, os acertos/28 alvos são 24 (120 original), 18
(120+2023), 18 (33 original) e 20 (33+2023). Em 12h são 7, 3, 8 e 9;
os MAE correspondentes são 0,9085, 1,2107, 1,0979 e 1,0936 m. Os
28 alvos continuam pertencendo ao mesmo trecho já inspecionado.

No test de 12h, os acertos/237 alvos são 83, 89, 83 e 79, nessa mesma
ordem. Há 236 pares e uma falha de base em todas as famílias. Os MAE
são 1,3618, 1,2567, 1,3703 e 1,2930 m; os maiores erros são 7,5900,
7,3628, 10,0287 e 9,4211 m. Comparado a 120+2023, 33+2023 piora o
MAE geral de test em todos os 12 horizontes. Não há domínio global.

Em 1h de cheia no test, 33+2023 tem 232 acertos/236 pares (98,31%),
mas 232/237 alvos incluindo a falha (97,89%). Esse resultado histórico
isolado não atinge a regra operacional nem comprova a meta prospectiva.
Não omitir a falha para apresentar um percentual acima de 98%.

`outputs/verificacao-radar-core33-20260921/` reproduziu os 48 modelos
novos exatamente, recalculou 576 linhas de métricas, reconciliou 288
linhas dos controles e conferiu 60 hashes de artefatos e 60 de entradas.
O arquivo effects.csv contém os quatro contrastes para todos os
horizontes e recortes. Não houve promoção, mistura de versões por
horizonte, alteração da emissão horária ou mudança dos critérios da meta.

A auditoria independente em
`outputs/auditoria-independente-radar-core33-20260921/` passou 263
verificações: 96 grupos de cheia, 36 máscaras, 48 combinações de
amostras/pesos e identidade das chaves, bases, alvos e controles.
Os oito hashes de artefatos foram conferidos também pelo coordenador.
A retirada simultânea de dois blocos não permite atribuir o resultado
separadamente à chuva ou às estações removidas; qualquer continuação
dessa hipótese precisa separar esses fatores em protocolo próprio.

Às 23:21:47 BRT, uma nova consulta ANA somente de leitura preservou
188 observações e o recibo
`fb3c7e41208e0f230b5dfa4a31d878a16891639ae467fdc44cfbd7d33d5c2297`.
Último nível retornado: 16,91 m às 22:45, marcado aprovado pela fonte,
com referência de régua/fuso ainda não certificados para a meta.
O alvo exato das 23h continuava ausente; não foi substituído por 22:45.
O relatório `outputs/monitoramento-prospectivo/reports/20260922T022147355519Z/`
mantém 31 pares confrontados, nove alvos sem observação exata e 97
ainda não vencidos; zero pares elegíveis para a meta. Cinco de cinco
janelas fechadas entregues. Cadeia de registros e hash do XML
conferidos. Não houve nova emissão ou repetição do ciclo das 23h.

## Separação dos efeitos de chuva, estações auxiliares e histórico de 2023

O protocolo `docs/radar-factorial-blocks-protocol.json`, registrado antes
do treino, completou a comparação de oito famílias. Aos conjuntos
120/33 foram acrescentados 45 campos (todos os níveis e Q/I, sem chuva)
e 108 (core33 mais chuva, sem Santa Tereza/Carreiro), cada um com e sem
2023. `outputs/experimento-radar-factorial-blocos-20260921/` contém 96
modelos novos; os 96 modelos anteriores foram reutilizados e reproduzidos
exatamente. Parâmetros, pesos, máscaras e 102.084 linhas permaneceram
iguais; nenhuma amostra de 2024 ou filtro de completude foi acrescentado.

A auditoria `outputs/auditoria-blocos-radar-20260921/` confirmou índices,
interseção core33 e união120; seus nove hashes foram conferidos. O bloco
de chuva contém 45 acumulados/defasagens e 30 coberturas. Portanto,
retirá-lo remove também indicadores de disponibilidade. Santa Tereza e
Carreiro têm 8.640/8.640 células ausentes nas 720 origens de 2023. Em
12h, 408/481 exemplos novos têm algum acumulado ausente, enquanto todas
as coberturas estão finitas. No test de cheia de 12h, há falta auxiliar
em 97/237 origens e falta de chuva em uma; os 28 alvos da validation
têm os dois blocos completos. A falha de base não foi excluída.

Retirar só as estações auxiliares não elimina a regressão causada pelo
acréscimo de 2023 neste teste de desenvolvimento: na validation com 108
campos, o MAE de cheia piora em dez dos 12 horizontes. Em 12h passa
de 0,8103 para 1,1071 m e os acertos caem de 8 para 4/28. Com 45 campos,
2023 melhora o MAE de validation em sete horizontes, mas em 12h piora
de 1,1743 para 1,2433 m, com acertos 3→2/28. Não há correção geral.

No test de cheia de 12h, adicionar o bloco de chuva reduz MAE e maior
erro nas quatro comparações de mesmo ano/estações:

| Campos sem→com chuva | Histórico | MAE antes→depois (m) | Maior erro antes→depois (m) | Acertos antes→depois /237 |
|---|---|---:|---:|---:|
| 33→108 | original | 1,3703→1,3578 | 10,0287→7,5134 | 83→78 |
| 33→108 | +2023 | 1,2930→1,2383 | 9,4211→7,4620 | 79→81 |
| 45→120 | original | 1,4276→1,3618 | 10,2112→7,5900 | 75→83 |
| 45→120 | +2023 | 1,3700→1,2567 | 9,3472→7,3628 | 78→89 |

Menor MAE não garante mais acertos: a primeira linha perde cinco.
Da mesma forma, 108+2023 tem MAE 1,2383 m contra 1,2567 m de120+2023,
mas perde oito acertos e aumenta o maior erro. Essas diferenças medem
o algoritmo congelado; não certificam causalidade física, equivalência
dos sensores ou o melhor conjunto possível após ajuste.

45+2023 atinge 233/237 alvos (98,31%, falha incluída) no test histórico
de cheia de 1h. São 233/236 pares, MAE 0,0769 m e maior erro 0,6959 m.
Em 6h, a mesma família tem 151/237; em 12h, 78/237 e MAE 1,3700 m.
Não é prova prospectiva, não satisfaz todos os horizontes e não permite
declarar a meta ou montar versões por horizonte a partir desses testes.

`outputs/verificacao-radar-factorial-blocos-20260921/` reproduziu os
96 modelos novos exatamente, recalculou 1.152 métricas, reconciliou
576 linhas dos controles e conferiu 108 hashes de artefatos e 108 de
entradas. effects.csv preserva os 12 contrastes das arestas da comparação
para todos os horizontes e os dois recortes. Nenhum candidato foi
promovido; a emissão horária e os critérios da meta permanecem iguais.

A auditoria independente em
`outputs/auditoria-independente-radar-factorial-blocos-20260921/` passou
458 verificações: 192 métricas de cheia, identidade das 102.084 linhas
e quatro controles, 36 máscaras e 96 combinações de amostras/pesos.
Dez hashes de artefatos foram conferidos também pelo coordenador.
Não há dominância conjunta de acertos, MAE e maior erro em todos os
horizontes, mesmo por fase. Acrescentar 2023 à família45 melhora MAE
de test nos 12 horizontes, mas perde acertos em oito. A interação entre
entradas e anos torna inadequado escolher só o menor MAE agregado.

Às 23:30:00 BRT, nova captura ANA retornou a observação exata das 23h:
17,07 m, marcada aprovada pela fonte. Recibo encadeado e XML conferidos:
`33a00fb7d21e6e0ad16bd7ca861dfc87e6409b0a5bd58d1d0b5edafbe1ca356f`.
O relatório `outputs/monitoramento-prospectivo/reports/20260922T023000097935Z/`
passou de 31 para 40 pares confrontados, sem alvo vencido ausente nesse
snapshot; 97 ainda não vencidos e zero pares elegíveis para a meta.
Os nove novos pares correspondem ao mesmo alvo das 23h, não a nove
observações ou eventos independentes; preservam importação histórica,
revisão manual e banda real inferior a1h com suas exclusões.

A emissão das 21:02:20 BRT previa 17,0410 m para23h, erro0,0290 m e
antecedência real1,961h. A emissão das18:02:09 previa15,4548 m, erro
1,6152 m e antecedência4,964h. São diagnósticos do mesmo evento em
andamento; não calibrar retroativamente essas previsões. Não houve
reemissão, mudança do relógio de treino ou promoção de candidatos.

## Novos períodos para diversidade e avaliação histórica reservada

O agente pesquisou fontes primárias em
`outputs/pesquisa-cheias-2021-2022-20260921/`, com duas buscas e cinco
URLs oficiais distintas. Dois relatórios SGB identificam cinco janelas:
28–31/05/2021 e quatro episódios em maio–junho/2022. Os máximos publicados
em Muçum são 7,15 m em 2021 e 13,39/12,80/12,43/11,16 m em 2022.
São descrições documentais, não novos alvos horários ou eventos já
certificados. Os 12 hashes do acervo foram conferidos pelo coordenador.

Os horários de máximos em 2022 aparecem com minutos :14/:29/:44/:59.
Uma tabela do segundo evento repete a data04/05, embora o texto descreva
28/05–01/06. Nada foi arredondado ou corrigido por suposição. A série
bruta deve esclarecer fase e datas antes de qualquer matriz. O relatório
2022 registra Santa Tereza como instalação do fim daquele ano, em testes;
isso não autoriza presumir dados desse sensor em maio/junho, nem prova
ausência de todo registro legado. Não houve consulta das séries2021/22,
inferência ou ajuste de modelo nesses períodos nesta etapa.

`docs/radar-historical-evaluation-reservation.json` reservou maio/2021 e
maio–junho/2022 contra uso futuro em ajuste/seleção antes da primeira
avaliação histórica predefinida. Documentos e máximos já foram vistos;
não se afirma desconhecimento integral dos períodos. A pesquisa de datas
nos scripts/docs atuais não encontrou referências a essas janelas antes
da reserva, mas não prova ausência em todo artefato/modelo histórico.
Coleta e auditoria de cobertura/QC são permitidas; antes de inferência,
congelar candidato, treino, parâmetros, controle e hashes. Se os erros
forem usados para modificar o modelo, os períodos passam a desenvolvimento.
Essa reserva não substitui a exigência prospectiva da meta.

## Levantamento delimitado dos insumos de julho de 2020

`outputs/pesquisa-insumos-observados-2020-20260921/` preserva oito consultas
ANA de04–13/07/2020: três níveis auxiliares e o posto de maior peso de
cada região de chuva. Antes da rede,190 XMLs existentes dessas estações
foram inspecionados e não tinham registros na janela. Todas as oito
respostas foram HTTP200; cinco continham dados, totalizando2.383 registros
conferidos campo a campo contra os XMLs. Os34 hashes de artefatos foram
verificados. Muçum e ONS existentes não foram baixados novamente.

Santa Tereza86472600, Carreiro86500000 e Prata-Turvo86125050 retornaram
ausência explícita. Linha José Júlio86472000 contém960 horários de15min,
mas911 níveis aprovados,41 suspeitos e oito vazios; sua chuva está aprovada
nas960 linhas. Nas nove origens de resposta de Muçum>8,09 m em12h já
identificadas em07/07 e12/07, os seis níveis para o bloco de Linha José
Júlio estão disponíveis:54 consultas rastreadas com atraso30min e idade
máxima15min após consulta. Isso não certifica os demais insumos.

O posto86450000 só tem46 chuvas, com lacunas que abrangem as duas subidas.
Tainhas86160000 tem36 timestamps ausentes durante07–08/07 e106 chuvas
vazias entre924 registros. Alto Antas86060010 tem213/240 horários e
Carreiro86479000 tem240/240. A amostra não cobre as27 estações; tetos
espaciais de pesos não foram tratados como cobertura temporal, nem os
pesos foram renormalizados. Ausências não viraram zero.

Julho2020 continua desenvolvimento já inspecionado, sem treino novo nesta
etapa. A próxima preparação requer os demais postos de chuva e auditoria
de Q/I e seus atrasos: o acervo ONS conhecido contém zeros suspeitos no
pico de08/07, que esta consulta não resolve. Não houve matriz completa,
promoção ou alteração do monitoramento. As novas janelas2021/22 permanecem
separadas dessa preparação e não foram usadas para escolher um modelo.

## Acervo completo solicitado e matriz observada de julho de 2020

`outputs/radar-insumos-observados-2020-20260921/` completou a janela
28/06–20/07/2020 das27 estações:34 GETs novos, todos HTTP200, e11 XMLs
reutilizados. Não houve retentativas. São15.244 registros únicos;
96 duplicatas de Muçum eram idênticas, sem conflito. Cinco postos não
tinham registros:86125000,86125050,86472600,86500000 e86504900. Coleta
concluída não significa cobertura temporal completa de todos os sensores.

O agente passou495 verificações. A conferência separada do coordenador
em `outputs/verificacao-insumos-observados-2020-20260921/` reproduziu
15.340 referências de registros diretamente dos45 XMLs, as15.244 linhas
brutas e os valores/QC/timestamps/proveniência dos27 NPZs ALL-QC.
Foram conferidos134 hashes do acervo. Índices de registros ANA são
1-based, conforme o contrato documentado pelo coletor. Suspeitos,
negativos e vazios permanecem preservados nas fontes.

`outputs/auditoria-qi-radar-2020-20260921/` acrescentou apenas um GET
CSV ONS de junho para aquecimento; julho foi reutilizado pelo hash do
CSV literal e do Parquet original. Junho tem720 linhas por usina e
julho744, total4.392. Os2.160 registros extraídos de junho foram
reconstruídos campo a campo do CSV bruto. Nenhum timestamp23:59 foi
transformado em24h. O Parquet de julho não foi redecodificado nesta
etapa; sua extração congelada coincide com a auditoria anterior.

Foram rastreadas8.640 consultas Q/I nas480 origens de01–20/07:
Q corrente/recuos1/2/4/8h e I corrente, nas três usinas, com atraso60min
e idade90min após consulta. Todas estão numericamente disponíveis.
23 origens usam algum zero reportado;16 usam Qzero com soma de
componentes>1m³/s. Esse limiar é diagnóstico, não regra oficial de QC.
As nove origens extremas já identificadas não usam esses zeros em
nenhuma dessas consultas. Valores não foram corrigidos ou mascarados.

O protocolo `docs/radar-2020-observed-features-protocol.json` precedeu
a preparação em `outputs/radar-matriz-observada-2020-20260921/`:
480×120 entradas,13.634 células ausentes,453 bases e454 níveis correntes
finitos. Mantidos pesos, atrasos, cobertura mínima0,5, parser e fórmula
dos campos originais, sem NWP ou substituto meteorológico. Santa Tereza
e Carreiro permanecem ausentes. Prata–Turvo não alcança cobertura0,5 em
nenhuma janela; seus acumulados ficam ausentes, sem baixar o limiar.

Há447/437/426 pares base/alvo em1/6/12h, respectivamente189/179/167
com alvo>=7m. A maior resposta de12h é11,53m; são exemplos potenciais,
não resultado de previsão. A auditoria independente em
`outputs/verificacao-radar-matriz-2020-20260921/` conferiu57.600 campos:
níveis/QI exatos e36.000 células de chuva com diferença máxima2,27e−13mm,
com ausências idênticas. As8.640 consultas Q/I coincidem com o CSV literal
e explicam os10.080 campos Q/I da matriz. Foram verificados17 hashes
da matriz e sete da auditoria independente.

As27 bases ausentes são23 suspeitas e quatro vazias; os26 níveis no
horário da origem ausentes são23 suspeitos e três vazios. São horários
distintos. Todas as bases consultam registro exato emO−15min; não houve
preenchimento por valor mais antigo. Os dados brutos mantêm o QC original.

`outputs/diagnostico-admissao-radar-2020-20260921/` alinhou exatamente
as480 chaves entre os avisos Q/I e a matriz. Das23 origens que usam
zeros,22 têm base ausente. A única com base finita é08/07/2020 05h,
19,02m, mas os12 alvos seguintes estão ausentes. Portanto nenhum par
elegível de1–12h usa esses zeros, sem mudar a máscara ou inventar
correção. Isso não valida as vazões: evidencia também a falta de
rótulos válidos em parte do pico, limitando o que o treino poderá aprender.

Não houve ajuste ou promoção nesta etapa. A próxima comparação deve
isolar o acréscimo de2020 à referência120 congelada, com os mesmos
parâmetros/máscaras de desenvolvimento e sem acrescentar2023/2024
simultaneamente. As reservas2021/2022 não foram acessadas e continuam
fora de ajuste/seleção. Referência da régua, fuso/publicação e regime
operacional seguem sem certificação para a meta prospectiva.

## Comparação controlada: referência120 com acréscimo de2020

O protocolo `docs/radar-2020-augmentation-protocol.json` foi registrado
antes do treino. `outputs/experimento-radar-historico-2020-20260921/`
acrescenta somente os pares elegíveis de01–20/07/2020 à referência120
observada, preservando parâmetros, pesos e máscaras originais. Não
entram2023/2024, nem as janelas reservadas2021/2022. O código verifica
explicitamente a exclusão dessas janelas e que nenhum novo par admitido
usa os zeros Q/I sinalizados; não acrescenta filtro de rejeição.

Foram ajustados24 modelos e reproduzidos exatamente24 controles
congelados. As102.084 linhas de avaliação, bases, alvos e disponibilidade
são idênticas. Em12h entram426 pares novos,167 com alvo>=7m, comparados
a255 pares de cheia nos10.814 exemplos originais da fase test. A maior
resposta do treino passa de8,09 para11,53m. É ampliação de exemplos,
não certificação de equivalência física ou precisão prospectiva.

| Fase | Horizonte | Acertos cheia referência→+2020 | MAE antes→depois (m) | Maior erro antes→depois (m) |
|---|---:|---:|---:|---:|
| validation | 1h | 28→28 /28 | 0,0667→0,0633 | 0,2537→0,2494 |
| validation | 6h | 24→21 /28 | 0,2587→0,3551 | 1,0963→1,3860 |
| validation | 12h | 7→7 /28 | 0,9085→0,8928 | 2,6195→2,6270 |
| test | 1h | 230→231 /237 | 0,0775→0,0648 | 1,2848→0,9375 |
| test | 6h | 149→163 /237 | 0,5993→0,5361 | 5,7173→4,7045 |
| test | 12h | 83→87 /237 | 1,3618→1,2303 | 7,5900→7,9746 |

O denominador237 inclui a falha de base, com236 pares. No recorte de
cheia de test, o MAE melhora nos12 horizontes; acertos aumentam em11
e empatam em2h. Contudo, o maior erro aumenta em9/11/12h. Na validation
de cheia, o MAE melhora em nove horizontes, mas acertos caem em quatro
(4/6/9/10h), aumentam em três e empatam em cinco. São os mesmos28 alvos
da validation, não novos eventos ou amostras independentes.

No conjunto geral de test, os acertos caem em10/11/12h, apesar da melhora
no recorte de cheia; o MAE geral melhora em nove horizontes. Não usar
somente a média ou o recorte favorável para declarar superioridade.
O pior erro de12h do candidato tem origem21/07/2026 17h, base3,21m,
alvo22/07 05h de15,16m: prevê7,1854m, contra7,7087m da referência.
A previsão do mesmo caso piora, mesmo com mais exemplos de subidas
rápidas no treino. Nenhuma compensação foi aplicada retrospectivamente.

`outputs/verificacao-radar-historico-2020-20260921/` reproduziu os24
modelos novos exatamente, recalculou288 métricas e reconciliou144
linhas dos controles. Foram conferidos36 hashes de artefatos e38 de
entradas. Mantidos os dados e versões anteriores, sem promoção,
mistura de horizontes ou alteração da emissão horária. Os resultados
justificam continuar a investigação, mas não comprovam a meta de98%.

A auditoria independente em
`outputs/auditoria-independente-radar-historico-2020-20260921/` passou
292 verificações, incluindo36 máscaras,24 linhas de treino,48 métricas
de cheia e identidade das102.084 linhas/controle. Os14 hashes próprios
foram conferidos também pelo coordenador. Os pesos nominais acrescentados
por2020 em1/6/12h são661/815/992; representam12,4552%/13,2542%/14,1795%
do ajuste da validation e5,6026%/6,0944%/6,7009% do test. São proporções
da soma de pesos, não medida causal da influência na previsão final.

## Primeira triagem da fase temporal da reserva de2022

Enquanto a auditoria do treino era finalizada, foi realizada uma única
consulta pública ANA de Muçum em04/05/2022, permitida pela reserva para
auditoria de cobertura. `outputs/pesquisa-fase-horaria-2022-20260921/`
preserva URL, instante, resposta XML e seis hashes conferidos. Não houve
inferência, cálculo de erros ou uso desses dados em treino/seleção.

O XML retornou96 registros aprovados, com minutos00/15/30/45 (24 de
cada) e segundos00. Existem24 observações em hora exata nesse dia.
O maior nível é1.339cm às04:15, enquanto a tabela do relatório SGB
indicava04:14 para o mesmo máximo. As duas fontes foram preservadas;
nenhum horário foi corrigido. Esse resultado não prova fase/cobertura
dos meses inteiros, erro no relatório, ausência de revisão ou vínculo
temporal certificado entre produtos. A próxima triagem pode ampliar
a consulta literal sem presumir que todas as observações2022 estejam
fora da grade. A reserva contra ajuste dos modelos continua vigente.

## Cobertura literal das reservas de 2021 e 2022 — 22/09, após 00h

Foram concluídas coletas limitadas e auditorias de cobertura, sem ajuste,
inferência, cálculo de erros ou seleção de modelo. Os planos foram salvos
antes das consultas; os XMLs, campos originais, QC, URLs, horários de coleta,
headers e hashes permanecem preservados. Os timestamps não foram corrigidos,
arredondados ou preenchidos. A presença de uma linha XML não garante uma
medição de nível utilizável.

| Reserva / posto | Registros 15 min, incluindo aquecimento | Níveis finais aprovados | Horas exatas aprovadas na janela de avaliação |
|---|---:|---:|---:|
| 28/04–31/05/2021, Muçum 86510000 | 3.264 | 3.264 | 744 / 744 em maio |
| 28/04–31/05/2021, Linha 86472000 | 3.264 | 0 | 0 / 744 em maio |
| 28/04–30/06/2022, Muçum 86510000 | 6.144 | 6.136 | 1.463 / 1.464 em maio–junho |
| 28/04–30/06/2022, Linha 86472000 | 6.144 | 3.109 | 707 / 1.464 em maio–junho |

`outputs/pesquisa-cobertura-reserva-2021-20260922/` contém quatro GETs
HTTP 200, sem retry, após inspeção restrita de 63 XMLs sem cache pertinente.
Todos os 6.528 registros foram reconciliados com os XMLs; o verificador
independente passou 25 verificações e o coordenador conferiu os 22 hashes
de artefatos. Não há duplicatas, conflitos ou lacunas de timestamps. Em
Linha, todos os campos NivelFinal e VazaoFinal estão vazios. Um valor
NivelDisplay sem QC foi preservado como outro campo, sem substituição.

`outputs/pesquisa-cobertura-reserva-2022-20260922/` contém seis GETs novos
HTTP 200, sem retry, após inspeção de 67 XMLs. O único overlap pertinente,
o probe de Muçum de 04/05, foi reutilizado e reconciliado: 96 referências
duplicadas idênticas, nenhum conflito. São 12.288 registros únicos, 12.384
referências XML e 15 hashes de artefatos conferidos pelo verificador em
`outputs/verificacao-cobertura-reserva-2022-20260922/`. Esse verificador
comparou todos os campos literais e proveniência; seus três hashes também
foram conferidos. Ambos os postos têm grade completa em 00/15/30/45 minutos,
com segundos zero. Em Muçum, os oito níveis ausentes permanecem ausentes.
Em Linha, há 3.032 vazios, dois suspeitos e um reprovado; a maior sequência
sem nível aprovado vai de 30/05 às 11h45 até 30/06 às 23h45, com 3.025 linhas.

A auditoria de disponibilidade de 2022, ainda sem modelos, encontrou
1.458 bases Muçum utilizáveis em O−15 min entre 1.464 origens; Linha tem
705 valores utilizáveis em O−30 min e 691 origens com os seis níveis
necessários às diferenças temporais. Exigindo que o alvo esteja dentro
da janela reservada, existem 1.457 pares base/alvo em 1h e 1.446 em 12h.
Há 312 alvos aprovados >=7 m em cada horizonte, dos quais 311 também têm
base disponível. São contagens históricas correlacionadas, não previsões
acertadas, eventos independentes ou evidência prospectiva.

Próximo passo: completar a triagem das demais entradas observadas e
congelar uma única família candidata/controle antes da primeira inferência,
conforme a reserva. Não selecionar variantes depois de ver erros dessas
janelas. Uma eventual aplicação de modelos ajustados com dados posteriores
a 2021/2022 será um teste retrospectivo em eventos reservados; não representa
uma simulação de treinamento exclusivamente anterior a esses eventos nem
emissões reais da época. Permanecem sem certificação o fuso, datum,
publicação original e equivalência de regime hidrológico.

## Recuperação do ciclo de 00h de 22/09/2026

As tentativas iniciadas às 00h00min59s e 00h02min18s terminaram em falha
de fonte obrigatória. Os manifests registram, respectivamente, um e nove
erros HTTP 500 ANA, além de 93 e 86 falhas auxiliares SIGMA. As falhas
permanecem no ledger; não foram reclassificadas como previsões emitidas.
A ausência de processo ativo e os recibos cycle_failed foram verificados
antes da nova tentativa, sem reinício baseado apenas em timeout.

`outputs/mucum-hourly-20260922T000704-0300/` concluiu a emissão única Radar
da referência 00h às 00h08min55,903820s BRT. Recibo:
`e322a0243173c064a6929cbd1ff7b22541c1ec2db705b79a6550fa605bce7a92`.
Houve 133 consultas, nenhuma falha em ANA/CERAN/Open-Meteo e 74 falhas
SIGMA preservadas. Estas são auxiliares pelo contrato existente, que não
foi relaxado nesta recuperação. O nível mais recente usado foi 17,45 m às
23h45 de 21/09, com idade real de 23,9317 minutos na emissão; o rótulo de
15 minutos no insumo corresponde à referência nominal, não à idade real.

`verify_receipt.py`/`receipt-verification.json` conferiram a cadeia do
ledger, a única emissão regular, cycle_completed, 22 artefatos de modelo,
128 recibos de entrada (originais e cópias seladas), cobertura das bandas
reais 1–12 h e reprodução exata das 14 inferências salvas. O log da execução
foi preservado na própria pasta. Nenhum modelo histórico experimental foi
promovido e o corte de treinamento operacional continua fixo.

O relatório `outputs/monitoramento-prospectivo/reports/20260922T030855989236Z/`
mostra 151 pares registrados: 40 associados a observações, dez ainda sem
observação exata e 101 com alvo ainda não vencido. São zero pares elegíveis
à meta certificada. As seis janelas horárias encerradas têm entrega
completa; a janela 00h ainda está aberta nesse relatório. Entrega completa
não mede assertividade e não apaga as tentativas falhas. Meta de 98% ativa,
não demonstrada.

## Candidato fixado e acervo completo das reservas — 22/09, após 00h11

Antes de qualquer inferência nas reservas foi registrado
`docs/radar-reserved-2021-2022-challenge-protocol.json`. A hipótese fixa é
comparar a referência observada de 120 entradas com a mesma família
acrescida dos pares elegíveis de julho de 2020. Foram escolhidos todos os
12 horizontes da fase test de cada família, com corte de alvos de treino
em 01/07/2026, sem mistura de horizontes, inclusão de 2023/2024 ou novo
ajuste. A escolha usa o resultado de desenvolvimento já conhecido, com
ganhos e regressões registrados; não constitui aprovação do candidato.

`outputs/congelamento-radar-reserva-2021-2022-20260922/` guarda cópias
idênticas dos 24 modelos, parâmetros, contagens de participação no treino,
referências das máscaras/matrizes e código de entradas. Foram conferidos
27 hashes de artefatos e 18 referências. Hash do protocolo:
`66d32e1aa148c165f01f0527bbe5fc0b47bd952a2f856fa9ba295b060d6ec0e8`.
As janelas 2021/2022 não aparecem nas matrizes de treino. A aplicação futura
será explicitamente retrospectiva: estes modelos aprenderam também com
dados posteriores aos eventos reservados. Não será apresentada como
treinamento temporal exclusivamente anterior ou emissão real da época.

O protocolo exige fontes/matrizes verificadas e hashes congelados antes
da primeira inferência, todas as origens com alvo dentro de cada janela,
todos os horizontes de 1–12h e resultados separados por ano e em conjunto.
Ausências de previsão contarão contra a fração de acertos entre alvos
observados; ausências de verdade serão reportadas como desconhecidas.
Os limites de 0,50 m, recorte >=7 m, fonte de nível final aprovada e regras
de atraso/cobertura não serão alterados depois de ver os erros. Nenhuma
inferência nas reservas ocorreu nesta etapa.

### ANA: 27 postos, dois anos, campos e QC preservados

O acervo `outputs/radar-insumos-reservados-2021-2022-20260922/` consolidou
os dez XMLs Muçum/Linha já coletados e fez 125 GETs adicionais, todos
HTTP 200, sem retry e com no máximo duas conexões simultâneas. Entre 135
fontes primárias, 113 contêm registros e 22 respondem “Sem dados”. Um
probe de 2022 foi usado apenas para conferência, com 96 registros iguais
à fonte mensal, sem duplicar a série canônica.

São 54 séries ALL-QC, 73.406 registros únicos: 25.061 em 2021 e 48.345 em
2022, incluindo 28–30 de abril como aquecimento. Esses totais incluem
os 18.816 registros Muçum/Linha anteriormente obtidos; não são todos novos.
Há 21.736 valores ChuvaFinal aprovados em 2021 e 42.304 em 2022. A auditoria
independente passou 1.511 verificações e reconciliou todos os campos de
todos os registros com os XMLs. O coordenador conferiu os 322 hashes de
artefatos e inspecionou o verificador. Não houve duplicatas, conflitos,
descartes ou registros fora do intervalo solicitado.

Sem série nos dois anos: 86125000, 86472600, 86500000 e 86504900;
86125050 também não tem série em 2021. Há registros mas ChuvaFinal
inteiramente vazia em 86200900/86493000 nos dois anos, 86298000 em 2021 e
86479000/86495500 em 2022. A auditoria preservou 722 níveis negativos
marcados como aprovados pela fonte 86479000/2022 e uma vazão negativa em
86448000/2021. São sinais reportados, não uma declaração automática de
invalidade física. O parser de entradas congelado continuará aplicando
suas regras existentes; a coleta não alterou valores/QC nem criou filtros.

### ONS: cinco meses e consultas de vazão verificadas

`outputs/ons-reserva-2021-2022-20260922/` preserva cinco CSVs públicos do
catálogo ONS: abril/maio de 2021 e abril/maio/junho de 2022. As cinco
consultas retornaram HTTP 200, sem retry. Foram selecionados os registros
literais de 14 de Julho, Monte Claro e Castro Alves, sem transformar os
horários 23:59 em meia-noite e sem substituir componentes de vazão.

O verificador em `outputs/verificacao-ons-reserva-2021-2022-20260922/`
releu 556.183 linhas dos arquivos brutos e reconciliou todos os campos
dos 10.941 registros selecionados, além dos 23 hashes finais do acervo.
Conferiu as 39.744 consultas de entrada: 18 por origem, em 744 origens de
2021 e 1.464 de 2022. Todas têm valor finito sob o atraso fixo de 60 min
e idade máxima de 90 min após a consulta. Isso não certifica disponibilidade
operacional passada, exatidão física ou horário de publicação original.

Uma origem de 2021 usa afluência zero reportada por 14 de Julho em
26/05 às 17h; o zero permanece no dado e no diagnóstico. Outro zero,
Castro Alves em 24/04/2021, fica fora das origens de avaliação. Há três
posições ausentes no padrão literal dos arquivos de abril, nenhuma
afetando as consultas das origens reservadas; detalhes estão em
literal-slot-audit.json. Nenhum zero/intervalo foi completado e nenhum
diagnóstico criou máscara adicional de rejeição.

O próximo trabalho é preparar e verificar as matrizes de 120 entradas
por ano usando essas fontes e o contrato já fixado, congelar seus hashes
e então executar a primeira comparação reservada. O modelo operacional
não foi alterado, as reservas não entraram no treino e a meta não foi
declarada alcançada.

### Conferência prospectiva às 00h19

Uma coleta pública adicional, às 00h19min46,688693s BRT, gerou o recibo
`743b01c06bc6c0cc8846c5bec8a226864a24600981e9dc8d9d2c0874967eccfd`.
O corpo selado e a cadeia do ledger foram conferidos. A última observação
aprovada continuava em 23h45, 17,45 m; não havia linha de 00h. O relatório
`outputs/monitoramento-prospectivo/reports/20260922T031946690964Z/`
mantém 40 pares associados, dez sem observação exata e 101 ainda não
vencidos, com zero pares elegíveis à meta certificada. Não foi usada
observação vizinha ou estimada para preencher o alvo ausente.

## Primeira comparação nas reservas de 2021/2022 — 22/09, 00h29

`scripts/hydro_radar_reserved_features.py` preparou separadamente os dois
anos, com 28–30/04 como aquecimento, contrato fixo de 120 entradas e alvos
Muçum exatos explicitamente aprovados. As matrizes estão em
`outputs/radar-matrizes-reservadas-2021-2022-20260922/`: 744×120 em 2021,
com 744 bases/alvos contemporâneos e 20.357 ausências; 1.464×120 em 2022,
com 1.458 bases, 1.463 alvos contemporâneos e 35.596 ausências. Nenhuma
origem tem as primeiras 24 entradas todas completas. Não foi criado
critério adicional de rejeição por campos auxiliares faltantes.

As 264.960 células foram reconstruídas de forma independente em
`outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922/`, sem
importar os helpers operacionais. Passaram 484 verificações, com níveis/QI
exatos, máscaras de ausência idênticas e maior diferença de chuva de
6,3949×10⁻¹³. Foram conferidos 8.832 rastros ANA, 39.744 consultas QI,
alvos, fronteiras por ano e cópias dos diagnósticos. Os dez hashes finais
da auditoria e 27 hashes das matrizes foram conferidos. Prata–Turvo em
2021 e Carreiro em 2022 não atingem a cobertura mínima de chuva em nenhuma
das seis janelas; esses acumulados continuam ausentes.

`scripts/hydro_radar_reserved_challenge.py freeze-inputs` registrou 153
arquivos por hash às 03h29min03,358072s UTC, após a auditoria final e antes
da inferência. A inferência começou às 03h29min09,860149s e terminou às
03h29min11,322655s UTC, usando os 24 modelos já congelados em 48 aplicações,
sem nenhum ajuste. Foram preservadas 26.340 linhas de previsão, 432 linhas
de métricas e 156 exclusões de fronteira predefinidas. Os hashes de todas
as entradas continuaram iguais após o cálculo. Saída:
`outputs/experimento-radar-reservas-2021-2022-20260922/`.

### Resultados de cheia, sem seleção de horizontes

O denominador é o total de alvos aprovados >=7 m, incluindo falhas de
previsão. Em 2022 há 312 alvos e 311 pares por horizonte; em 2021 são
apenas 11 alvos/pares, com dependência temporal. MAE/máximo usam os pares.

| Período | Horizonte | Acertos controle→+2020 / alvos | MAE controle→+2020 (m) | Máximo controle→+2020 (m) |
|---|---:|---:|---:|---:|
| 2021 | 1h | 11→11 / 11 | 0,0490→0,0608 | 0,1370→0,1434 |
| 2021 | 6h | 8→9 / 11 | 0,3474→0,2349 | 0,7555→0,6274 |
| 2021 | 12h | 6→10 / 11 | 0,4620→0,2649 | 0,7456→0,6157 |
| 2022 | 1h | 307→310 / 312 | 0,0739→0,0652 | 1,1085→0,9829 |
| 2022 | 6h | 194→218 / 312 | 0,6406→0,4714 | 3,7423→2,9726 |
| 2022 | 12h | 147→120 / 312 | 1,0272→1,0630 | 5,8169→4,8777 |
| Conjunto | 1h | 318→321 / 323 | 0,0731→0,0650 | 1,1085→0,9829 |
| Conjunto | 6h | 202→227 / 323 | 0,6306→0,4633 | 3,7423→2,9726 |
| Conjunto | 12h | 153→130 / 323 | 1,0079→1,0357 | 5,8169→4,8777 |

No conjunto de todos os níveis, os acertos agregados aumentam nos 12
horizontes. Isso não autoriza esconder regressões: separadamente, cada
ano perde acertos em três horizontes gerais. No recorte de cheia agregado,
acertos melhoram em nove horizontes e pioram em três. Em 2022, o maior
erro cai nos 12 horizontes, mas há menos acertos de cheia em quatro deles.
O candidato não apresenta ganho sustentado em todos os recortes exigidos.
Não foi promovido; a meta de 98% permanece não atingida.

Os 72 contrastes completos estão em
`outputs/analise-radar-reservas-2021-2022-20260922/changes.csv`. Em 12h,
o pior erro geral de 2021 aumenta de 1,9074 para 2,5291 m no mesmo caso
(origem 22/05 às 00h, base 1,04 m, alvo 1,81 m). O maior erro de 2022 cai
de 5,8169 para 4,8777 m, em casos distintos. Nenhum resultado constitui
evidência prospectiva ou dez eventos independentes; os modelos também
usam treinamento posterior aos anos reservados.

### Diagnóstico exploratório posterior, sem mudar o candidato

`outputs/diagnostico-radar-reservas-2021-2022-20260922/` separa os pares
de 6/12h por movimento observado posterior e por tendência recente de
entrada. É exploração posterior aos resultados, não nova validação.
Movimento futuro é apenas um rótulo diagnóstico, nunca entrada da previsão.
O placar principal continua incluindo todas as falhas; esta análise usa
pares para examinar direção do erro.

Nas cheias de 2022 em 12h, os 124 pares com subida observada >=0,50 m
passam de 31 para 17 acertos, embora o MAE caia de 1,8927 para 1,7233 m
e a subestimação média diminua. Nos 136 pares com queda >=0,50 m, os
acertos caem de 90 para 74 e o MAE sobe de 0,4426 para 0,6591 m. Nos 51
pares estáveis, os acertos passam de 26 para 29. Ao todo são 29 acertos
ganhos e 56 perdidos, resultando na perda líquida de 27 acertos. Melhorar
o erro médio de algumas subidas não garante atingir a tolerância de 0,50 m.
Essas partições não demonstram causalidade nem autorizam correções usando
o movimento futuro. Nenhum parâmetro ou máscara foi modificado.

As janelas já foram avaliadas. Qualquer ajuste futuro guiado por esses
erros deve tratá-las como desenvolvimento; repetir a comparação não pode
ser apresentado como um novo teste independente.

### Observação de 00h recebida às 00h30

Às 00h30min18,859686s BRT, a ANA retornou nível final aprovado de 17,59 m
às 00h. Recibo `761af5b9341a6e778fa6552dfa04e961fc97119980d5319976c8548a9ab0cb80`,
com corpo selado e cadeia conferidos. O relatório
`outputs/monitoramento-prospectivo/reports/20260922T033018862178Z/`
agora tem 50 pares associados e 101 ainda não vencidos, sem alvo vencido
faltante nesse snapshot. Os dez pares novos referem-se à mesma observação,
incluindo histórico/revisão e banda real zero; não são dez novos eventos.

Exemplos Radar regular para esse alvo: emissão às 22h02min08s prevê
17,6875 m, erro 0,0975 m e antecedência real 1,9643 h; emissão às
18h02min09s prevê 15,9920 m, erro 1,5980 m e antecedência real 5,9640 h.
Ambos permanecem registrados. A emissão 23h02 fica na banda real zero,
pois antecede o alvo em 0,9636 h, e não conta como previsão com 1h real.
São ainda zero pares elegíveis à meta certificada, com fuso/datum pendentes.

### Auditoria final da comparação e sensibilidade numérica identificada

`outputs/auditoria-radar-reservas-2021-2022-20260922/` passou 871
verificações, incluindo as 432 métricas, 26.340 linhas, 156 fronteiras,
24 modelos/48 aplicações e os 153 hashes congelados. O coordenador
conferiu os 18 hashes da auditoria final e novamente os 153 arquivos
de entrada. As regressões e denominadores publicados foram confirmados.
Nenhum artefato primário ou parâmetro foi alterado pela auditoria.

Foi encontrada sensibilidade real de reprodução. A matriz reconstruída
independentemente reproduz 34 aplicações exatamente; em 14, diferenças
de chuva da ordem de 10⁻¹³ cruzam limiares das árvores, alterando 203
células de previsão. Ao reaplicar a matriz ORIGINAL congelada nessas 14
aplicações, todas as previsões salvas são reproduzidas exatamente. São
191 origens distintas e 190 timestamps-alvo, não 203 eventos independentes.
O rastreamento de 253 divergências de caminho nas árvores explica todas
as diferenças pela soma dos valores das folhas, até 10⁻¹² m.

A maior diferença é 0,029309652 m no candidato de 4h com origem em
29/05/2022 às 23h. O coordenador rastreou esse caso separadamente em
`outputs/diagnostico-numerico-radar-reservas-20260922/`: uma única árvore
das 180 muda de folha ao comparar Tainhas:P48 com o limiar
76,2868852459016. A entrada original é 76,28688524590146 e a reconstruída
76,28688524590164. O resultado passa de 11,945531397 para 11,916221746 m;
a soma manual das folhas concorda com a aplicação do modelo. Isso é
uma explicação numérica observada, não uma hipótese de zero de chuva
inventado ou erro físico certificado de sensor.

Nenhuma das 203 diferenças muda a classificação de acerto <=0,50 m,
no geral ou no recorte >=7 m, em qualquer grupo família/ano/horizonte.
As métricas primárias continuam sendo as da matriz original, sem
arredondamento retrospectivo. A ausência de mudanças de classificação
neste conjunto não prova robustez em outros casos ou torna qualquer
diferença automaticamente aceitável.

Uma próxima investigação pode tratar a estabilidade da representação
numérica das entradas antes de novo ajuste e aplicação. Deve ser um
experimento separado, com regra fixa antes de medir o resultado, sem
editar modelos/entradas/placares já congelados. Os resultados de 2021/2022
já são conhecidos e não podem servir como novo teste independente para
essa alteração. O modelo operacional permanece inalterado e a meta ativa.


### Experimento registrado de estabilidade numérica — 22/09, 00h43

A regra fixa em `docs/radar-numeric-stability-protocol.json` foi registrada
antes de qualquer novo ajuste em `docs/radar-numeric-stability-registration.json`,
às 03:43:23,937903 UTC. Arredondar somente as colunas 45–119, de chuva e
cobertura, a oito casas decimais, depois das máscaras existentes; manter
níveis, vazões, alvos, timestamps, pesos, membros e parâmetros. A precisão
numérica não foi escolhida por comparação de erros dos modelos.

A auditoria `outputs/auditoria-normalizacao-radar-20260922/` passou 83
verificações antes do ajuste. As matrizes normalizadas originais e
reconstruídas de 2021/2022 ficaram exatamente iguais; NaNs, campos fora
da chuva, máscaras e limiar de cobertura permaneceram iguais. Perturbação
máxima de 4,9997e-9, sem divergência com Decimal nos valores testados.
O manifesto final tem SHA-256
`4e6cb47aa652d4f1c663d013f1a82a1745036d5566dbadef5c9f891232cd78fe`.
Para 2020 e 2025/2026 foram verificadas invariantes e perturbações, mas
não existe neste experimento uma segunda NPZ reconstruída independente
preservada desses períodos. A igualdade certificada se restringe às
reconstruções disponíveis de 2021/2022.

O novo experimento compara 48 ajustes (original e +2020, dois cortes,
12 horizontes) com seus respectivos controles congelados. A NPZ normalizada
e seu hash foram selados no manifesto pré-ajuste. Nenhum modelo operacional
é alterado. Todas essas janelas já são conhecidas; sua reavaliação mede
estabilidade e diagnóstico de desenvolvimento, sem criar um novo teste
independente de precisão.

### Coleta adicional às 00h50, sem nova emissão

A coleta ANA às 00h50min10,610089s BRT recebeu como observação mais recente
17,74 m às 00h15, com qualidade Dado aprovado. Recibo
`60b19b3a42a9faf8c5c5b79020c0a9dc0d8aa55f16c7ef86f315aa048fbdfb2b`;
corpo e cadeia de 2.197 registros verificados. O relatório
`outputs/monitoramento-prospectivo/reports/20260922T035010612616Z/`
permanece com 50 pares associados e 101 ainda não vencidos: a observação
00h15 não corresponde a um novo alvo horário. Permanecem zero pares
elegíveis à meta certificada. Não foi emitido um ciclo horário duplicado.


### Resultado do experimento de estabilidade — 22/09, 00h52

O experimento em `outputs/experimento-radar-estabilidade-numerica-20260922/`
terminou às 03:52:05,363135 UTC, após manifesto pré-ajuste de
03:49:13,234805 UTC. Foram 48 novos modelos, 48 controles reproduzidos,
102.084 linhas dos cortes originais e 26.340 linhas de desenvolvimento
reutilizado de 2021/2022, com 1.440 métricas. O coordenador conferiu
61 hashes de artefatos, 144 hashes de fontes e a NPZ normalizada selada.
Manifesto final:
`542045875177845d2d54e96ea173baa2d20cfa146e8730ddc4a09bffd1f6c9ef`.

As 48 aplicações de modelos normalizados às matrizes originais e
reconstruídas de 2021/2022 deram previsões exatamente iguais. Isso resolve
a divergência observada entre essas duas representações; não prova
estabilidade para todo arredondamento possível, generalização ou precisão.

A análise pareada está em
`outputs/analise-radar-estabilidade-numerica-20260922/`, com 720 contrastes
por composição de treino, horizonte, período, população e recorte. No
teste original de 2026, a família +2020 perde acertos gerais em oito
horizontes e ganha em dois; no recorte >=7 m perde em sete, ganha em um
e empata em quatro. A família original tem quatro ganhos, quatro perdas
e quatro empates no recorte de cheias. Não há melhora consistente.

Exemplos no recorte >=7 m, com falhas mantidas no denominador:

| Período e composição | h | Acertos bruto → normalizado | MAE bruto → normalizado | Máximo bruto → normalizado |
|---|---:|---:|---:|---:|
| Teste 2026, original | 6 | 149 → 148 / 237 | 0,5993 → 0,5976 m | 5,7173 → 5,7589 m |
| Teste 2026, original | 12 | 83 → 82 / 237 | 1,3618 → 1,3588 m | 7,5900 → 7,5480 m |
| Teste 2026, +2020 | 6 | 163 → 162 / 237 | 0,5361 → 0,5369 m | 4,7045 → 4,7049 m |
| Teste 2026, +2020 | 12 | 87 → 89 / 237 | 1,2303 → 1,2212 m | 7,9746 → 8,0674 m |
| Desenvolvimento 2022, +2020 | 6 | 218 → 217 / 312 | 0,4714 → 0,4537 m | 2,9726 → 2,7002 m |
| Desenvolvimento 2022, +2020 | 12 | 120 → 113 / 312 | 1,0630 → 1,0618 m | 4,8777 → 4,7442 m |

A melhoria do MAE não garante mais acertos dentro de 0,50 m. Em 2021,
os 11 alvos altos de 12h da família +2020 passam de 10 para 11 acertos,
mas essa amostra pequena já examinada não é evidência para a meta. O
resultado de 2022 na mesma família/horizonte piora em sete acertos.

Após reajustar, diferenças entre modelos bruto e normalizado chegam a
0,4688 m no conjunto original e 0,6693 m no desenvolvimento reutilizado
(+2020). Essas diferenças não são a instabilidade de aplicação de
0,0293 m do experimento anterior: agora o treinamento também recebeu
a representação nova. Não devem ser descritas como mera formatação sem
efeito sobre o modelo.

Nenhum modelo promovido, nenhuma nova precisão decimal escolhida após
observar os erros. A representação fixa pode ser mantida como fundamento
de reprodução em futuros experimentos previamente registrados; este
candidato não demonstra ganho suficiente de precisão. Todos os períodos
usados aqui já foram examinados e não são um novo teste independente.
A meta continua ativa e não atingida.


### Conferência independente do experimento de normalização

`outputs/auditoria-radar-estabilidade-numerica-20260922/` passou 2.374
verificações: 48 modelos, 48 controles reaplicados exatamente, 48
aplicações novas no acervo original, 48 no desenvolvimento reutilizado e
48 reaplicações exatamente iguais sobre reconstruções normalizadas.
Todas as 1.440 métricas e a associação das 128.424 linhas foram conferidas.
O coordenador conferiu os dez hashes de artefatos e os 129 hashes de fontes
da auditoria. Manifesto:
`eb5670e2fd63e505aadc4e03b2fbd9e070196686d606db43dded0cce3e182766`.

A auditoria reconstruiu membros, ordem, alvos e pesos a partir das máscaras,
fórmulas e código executado; os modelos ajustados não retêm todos os pesos
amostrais. Parâmetros e previsões iniciais dos controles correspondentes
conferem. Não existe evento separado de início de fit: a evidência é a
ordem do código e dos registros pré-ajuste, sem alegar certificação global
de histórico de execução. Nenhum ajuste adicional foi feito pela auditoria.
As regressões foram confirmadas e o candidato permanece experimental.


## Suporte histórico da previsão operacional — 22/09, 00h59

A rodada anterior constitui progresso: novos modelos e auditoria concluídos,
com regressões preservadas e nenhuma promoção. Nesta rodada o trabalho
continua somente com Radar, conforme a remoção expressa do HGE/ARNO.

`scripts/hydro_radar_live_support.py` audita uma emissão selada sem treinar.
O resultado final `outputs/auditoria-suporte-radar-live-00h-20260922-v2/`
reproduziu exatamente as 14 previsões das 00h08min55s e conferiu 2.520
faixas de entrada. As máscaras foram reconstruídas usando corte exclusivo
21/09/2026 às 00h e os primeiros 24 campos completos, como no runner.
Os alvos horários coincidem exatamente com a série de 15 minutos.
Foram conferidos seis hashes de artefatos e 27 de fontes.

Há 10.875 amostras de treino em 1h nominal e 10.843 em 14h. O último alvo
admitido em todos os prazos é 20/09 às 23h. A âncora atual de 17,45 m
supera o máximo de entrada de treino, 15,30 m; os alvos de treino chegam
a 15,31 m. Todos os 14 modelos recebem 24 entradas acima do máximo de
treino e uma abaixo do mínimo. Não faltam entradas nesta origem.

Entre os excessos estão os níveis de Linha José Júlio (19,95 versus
15,94 m) e Santa Tereza (16,52 versus 13,36 m), a vazão de 14 de Julho
(11.893,47 versus 6.148 m³/s) e chuva Tainhas em 24h (151,2814 versus
75,2967 mm). Cada nível é comparado na própria referência, sem inferir
conversão entre réguas. Estar dentro de uma faixa univariada não comprova
suporte conjunto, e estar fora não fornece uma probabilidade de erro.

O modelo é residual, com variação somada à âncora atual. Não existe um
teto obrigatório de previsão em 15,31 m; não foi introduzido clipping.
A diferença entre previsão meteorológica atual e produto histórico do dia
anterior também permanece explícita. A falta de diversidade histórica
motiva a nova pesquisa do agente sobre eventos anteriores a 2020, antes
de qualquer escolha de janela por desempenho do modelo.

A execução preliminar sem v2 foi preservada e substituída por v2 para
corrigir o nome de um campo de corte UTC: ele não era o último alvo
admitido. A coluna actual_last_training_target já mostrava corretamente
20/09 às 23h. Nenhum valor, previsão ou máscara mudou nessa correção.


### Ciclo das 01h e mudança das condições de entrada

O ciclo `outputs/mucum-hourly-20260922T010016-0300/` concluiu às
01h02min18,522238s BRT. Recibo
`b81cc15cedec3251abcd7a8a8be6b7b70652a99564065fbfe0506637e5c05e76`.
Último nível usado: 17,86 m às 00h30, com idade real de 32,3087 minutos
na emissão. Foram verificados 22 artefatos de modelo/código, 196 recibos
e 14 inferências exatas, uma única emissão regular e ciclo concluído.
As 133 coletas tiveram seis erros auxiliares SIGMA e nenhum nas fontes
obrigatórias ANA/CERAN/Open-Meteo. As bandas reais cobrem 1–12h; alvos
nominais adicionais permanecem explicitamente sem validação específica.

O maior ponto horário previsto é 19,2750 m às 04h; é previsão experimental,
não pico observado ou intervalo de confiança. O relatório
`outputs/monitoramento-prospectivo/reports/20260922T040218620924Z/`
mostra 50 pares associados, 11 alvos vencidos sem observação exata e
104 ainda não vencidos, zero elegíveis à meta. As sete janelas horárias
encerradas têm entrega completa; entrega não comprova precisão.

A auditoria de suporte das 01h reproduziu as 14 previsões. Há 22 entradas
acima e duas abaixo das respectivas faixas de treino. A âncora de 17,86 m
supera 15,31 m, agora máximo de entrada de treino. Não se deve apresentar
15,30 m do ciclo anterior como constante de todos os reajustes.

### Corte temporal fixo não congela a matriz de treinamento

A comparação `outputs/diagnostico-variacao-treino-horario-20260922/`
verificou 114 campos dos snapshots históricos anteriores ao corte: nenhum
valor ou timestamp desses insumos mudou entre 00h e 01h. Os campos crus
na grade também não mudaram. Mesmo assim, 94 das 180 colunas derivadas
mudaram, totalizando 538.204 células antes do corte.

O código `prepare_current` calcula o atraso atual de cada fonte e o aplica
a todo o histórico usado no ajuste. Entre os dois ciclos, o atraso de
Muçum passou de 15 para 30 min, Santa Tereza de 15 para 75 min e Castro
Alves de zero para 60 min. Isso muda âncoras, diferenças e disponibilidade
dos campos históricos sem mudar o limite final dos alvos de treinamento.
Em 1h nominal entraram 258 origens e saíram 234, levando a amostra de
10.875 a 10.899. Nas 10.641 origens comuns, 7.429 âncoras mudaram, mas
nenhum alvo observado mudou. O comportamento é explícito no runner e
precisa ser tratado como adaptação ao atraso, sem confundi-lo com
revisão dos dados brutos, vazamento de alvos futuros ou modelo congelado.

Essa evidência orienta um próximo experimento controlado sobre robustez
aos atrasos. Não autoriza trocar silenciosamente a política de treino nem
atribuir toda variação da previsão aos dados meteorológicos novos. Os
modelos emitidos, horários e hashes continuam preservados.

### Pesquisa de diversidade anterior a 2020: cobertura negativa delimitada

O agente concluiu `outputs/pesquisa-diversidade-eventos-pre2020-20260922/`,
com 22 verificações e 29 hashes de artefatos conferidos pelo coordenador.
Três sondagens ANA86510000 de sete dias retornaram HTTP 200 e a mensagem
Sem dados, sem nenhum registro: 18–24/07/2011, 08–14/10/2015 e
24–30/05/2017. O coordenador também analisou os três XMLs. Não houve
treinamento com essas janelas, interpolação ou substituição por zeros.

A escolha foi documental e registrada antes das consultas. O boletim
primário SGB de 26/05/2017 indica manutenção em Muçum. A referência de
2011 em artigo hospedado oficialmente é secundária e contém conflito
entre 11 e 21 de julho. O documento estadual de 2015 aparece no índice,
mas o acesso direto devolveu 404, preservado e distinguido do conteúdo
válido. Nenhuma janela de 2019 foi inventada para completar a pesquisa.

Essas respostas não esgotam o arquivo ANA nem demonstram que inexista
série convencional. O próximo caminho concreto é o acervo convencional
Hidroweb e os registros de dupla leitura citados pelo SGB, preservando
cadência e referências. Duas leituras diárias ou máximos anuais não podem
ser transformados em verdade horária por interpolação. Permanecem as
pendências de fuso/datum e regime das usinas. A meta está ativa e não foi
atingida; não houve promoção operacional nesta rodada.


A conferência independente final está em
`outputs/verificacao-variacao-treino-horario-20260922/`: 170 verificações
passaram. Além dos 114 campos históricos e 60 campos crus iguais, confirmou
as 94 colunas/538.204 células derivadas alteradas e a composição exata dos
14 treinos. O deslocamento direto de 15 min reproduz o novo histórico H
Muçum em 51.647 posições; deslocamentos de 60 min reproduzem Santa Tereza H
e Castro Alves Q em 51.644 posições cada, incluindo NaNs. As bordas foram
conferidas por consulta temporal independente às fontes. O coordenador
conferiu os oito hashes da auditoria final; manifesto
`4f93175fb11588bdee4516e33377d6488f5515c1396eeef4e8f17cba57a9c548`.
Isso confirma o mecanismo da variação do treino, sem certificar a
publicação histórica das observações nem provar a causa dos erros de nível.


## Experimento de robustez a perfis de atraso — registro de 22/09, 01h10

A rodada anterior trouxe progresso concreto: emissão das 01h, pesquisa de
cobertura e identificação auditada do mecanismo de mudança do treinamento.
A meta continua somente Radar; o texto original que menciona HGE foi
superado pela remoção expressa já documentada.

O protocolo `docs/radar-delay-profile-mixture-protocol.json`, registrado
às 04:10:35,814040 UTC, define um candidato exposto aos dois perfis de
atraso já selados (00h e 01h), além de controles separados de cada perfil.
SHA-256: `38f94ccdca7d60b237abe38cf1bdd2c23df283594f78211f195b4642b0470585`.
A preparação pré-ajuste foi selada às 04:12:30,163548 UTC em
`outputs/experimento-radar-mistura-atrasos-20260922/`.

A hipótese é que exposição a atrasos variados reduza a sensibilidade do
modelo. Não se usa duplicação de linhas: um único sorteio PCG64(57), salvo
antes dos ajustes, escolhe perfil A ou B para cada origem e é reutilizado
em todos os horizontes/cortes. São 6.408 escolhas A e 6.504 B na grade
completa, antes das máscaras. Cada amostra usa vetor e âncora do mesmo
perfil, com alvo observado comum e fórmula de pesos já existente.

Os três modelos usam exatamente a interseção das origens admissíveis
nos dois perfis: bases/alvo finitos e primeiros 24 campos completos em
ambos. Isso isola exposição ao perfil sem confundir o resultado com
novas origens de treino. Esses controles experimentais não são os modelos
operacionais já emitidos, que usam suas próprias máscaras. Parâmetros,
ordem cronológica e contagem de amostras permanecem iguais entre famílias.
Não se arredondam entradas, alteram chuva, adicionam anos ou buscam sementes.

São previstos 72 ajustes: três famílias, dois cortes e 12 horizontes.
Cada modelo será aplicado aos dois perfis separadamente, cobrindo todas
as linhas agendadas, as ausências e os recortes geral/cheias. A comparação
principal será com o controle correspondente ao perfil avaliado; o controle
do outro perfil também permanecerá visível. As 204.168 linhas previstas
são duas vistas de 102.084 pares origem/horizonte, não o dobro de eventos
independentes. Todos os períodos já eram conhecidos: resultado de
desenvolvimento, sem promoção, emissão nova ou comprovação dos 98%.


### Hidroweb convencional: séries recuperadas, cadência preservada

A pesquisa `outputs/pesquisa-hidroweb-convencional-mucum-20260922/`
recuperou dados de Muçum86510000 nas três janelas por
HidroSerieHistorica, operação distinta da telemetria. As seis consultas
semanais bruto/consistido deram Sem dados; os registros são mensais,
com DataHora no dia 1 e campos Cota01..31. Depois de ler o dicionário
oficial e registrar o plano mensal, as seis consultas aos três meses
encapsuladores retornaram dados. Esse comportamento é compatível com
filtro pela data do registro mensal, sem alegar inspeção do backend.
As sondagens telemétricas anteriores continuam válidas para aquele produto.

Foram recuperados 12 registros mensais e 357 valores em 372 campos de
calendário. Nas três semanas há 42 leituras brutas, às 07h e 17h, com
intervalos alternados de 10 e 14h; existem também médias diárias brutas
e consistidas, guardadas separadamente. Médias diárias rotuladas às 00h
não são leituras instantâneas nessa hora nem observações disponíveis no
início do dia. Não houve interpolação ou treino com esses dados.

Os máximos das leituras amostradas são 2.010 cm em 21/07/2011 às 07h,
1.693 cm em 09/10/2015 às 17h e 1.233 cm em 28/05/2017 às 07h, na
própria régua histórica. São máximos amostrados, não picos contínuos
certificados ou equivalência de datum com 2026. A leitura de 2011 traz
uma evidência primária para o catálogo sem reescrever o conflito de datas
da referência secundária anterior. Quarenta das 42 leituras brutas não
trazem tag de status; as duas de 14/10/2015 têm código 3. Ausência de
status não foi transformada em qualidade aprovada.

DataIns bruto é posterior aos episódios (2011-10-27, 2016-01-26 e
2017-10-06); o consistido tem 2018-06-29 ou 2024-04-09. Não se conhece
histórico completo de revisão nem se interpretou DataIns como primeira
publicação. O contrato consultado não resolve fuso/DST, monografia ou
continuidade física do zero da régua. O novo serviço autenticado foi
apenas documentado; não se usaram credenciais ou contatos externos.

Passaram 191 verificações do agente. O coordenador conferiu os 57 hashes,
os 12 registros campo a campo contra XML e as 84 células das semanas,
incluindo a separação das 42 leituras instantâneas e das médias. Manifesto:
`1ade8a7c38d5267146526c197daba6fecb6d62a272374b4ebb3f635546c8da2e`.
Esses dados ampliam o catálogo e a caracterização das amplitudes, mas
não constituem uma grade observada horária para cumprir a meta 1–12h.

### Coleta às 01h16 sem emissão adicional

A ANA retornou como última observação 18,00 m às 00h45, Dado aprovado,
recebida às 01h16min47,727273s BRT. Recibo
`b944b492d96b19b23df61fb805ed0721810aab57a474c9bf61bb2220c75aae25`,
corpo e cadeia de 2.397 registros verificados. O relatório
`outputs/monitoramento-prospectivo/reports/20260922T041647730008Z/`
mantém 50 pares associados, 11 alvos vencidos sem observação exata e
104 ainda não vencidos. Não foi usada interpolação para o alvo 01h,
nem criado ciclo horário duplicado. Zero pares elegíveis à meta certificada.


### Resultado da mistura de atrasos — 22/09, 01h17

O experimento terminou às 04:17:53,998674 UTC: 72 modelos, 204.168 linhas
em duas vistas da mesma grade e 864 métricas. O coordenador conferiu
81 hashes de artefatos, 29 hashes de fontes e as duas NPZs pré-ajuste.
Manifesto final:
`dc86055d4618dbeb612c6f490bb3589b2b49184ee606896040252b43e67f03f3`.
A análise em `outputs/analise-radar-mistura-atrasos-20260922/` contém
576 contrastes, incluindo candidato e controle do outro perfil contra
o controle correspondente. Não houve mistura oportunista de vencedores.

O candidato melhorou acertos de cheias em 6h nas duas vistas do teste,
mas piorou em 12h. No teste geral, o perfil A perde acertos em nove
horizontes, ganha em dois e empata em um; seu MAE piora nos 12. O perfil B
perde acertos em sete horizontes e ganha em cinco. No recorte >=7 m,
A tem cinco ganhos/cinco perdas/dois empates; B, quatro ganhos/seis
perdas/dois empates. Portanto a hipótese não obteve ganho consistente.

| Vista do teste, observado >=7 m | h | Acertos controle → mistura | MAE controle → mistura | Máximo controle → mistura |
|---|---:|---:|---:|---:|
| A, atrasos de 00h | 1 | 230 → 231 / 237 | 0,0837 → 0,0763 m | 1,2985 → 1,1414 m |
| A, atrasos de 00h | 6 | 162 → 170 / 237 | 0,6129 → 0,6021 m | 6,3832 → 6,2996 m |
| A, atrasos de 00h | 12 | 91 → 75 / 237 | 1,2469 → 1,3287 m | 7,5752 → 7,7928 m |
| B, atrasos de 01h | 1 | 230 → 230 / 237 | 0,0941 → 0,1051 m | 1,5101 → 1,5158 m |
| B, atrasos de 01h | 6 | 154 → 166 / 237 | 0,6423 → 0,6355 m | 6,6704 → 6,5058 m |
| B, atrasos de 01h | 12 | 77 → 75 / 237 | 1,3523 → 1,3849 m | 6,9600 → 7,6069 m |

Em 12h, as três famílias usam as mesmas 3.513 origens no primeiro
corte e 9.269 no segundo. O candidato recebe 1.704/1.809 origens A/B
no primeiro e 4.571/4.698 no segundo, sem duplicação. O número de alvos
altos de treinamento é respectivamente 166 e 194. A fórmula de pesos
é a mesma, mas sua soma varia porque delta usa a âncora do perfil de
cada amostra; isso está explicitamente registrado, sem alegar pesos
numéricos idênticos entre os perfis.

Conferências manuais adicionais do avaliador verificaram separadamente
alvo ausente, previsão ausente e contagem dos dois perfis: no caso com
três alvos conhecidos, duas previsões e um acerto, a fração pelo total de
alvos é 1/3, mantendo a falha no denominador, enquanto a fração dos pares
é 1/2. Médias/percentuais dessas vistas não substituem a amostra por evento.

Nenhum candidato foi promovido ou emitido. O treino misto não inclui um
campo explícito de idade das fontes; investigar essa informação é uma
hipótese futura, não uma explicação causal já demonstrada das regressões.
Dois perfis não representam todos os atrasos possíveis. As janelas
continuam desenvolvimento já examinado, e a meta permanece não atingida.


A auditoria independente final da mistura de atrasos, em
`outputs/auditoria-radar-mistura-atrasos-20260922/`, passou 2.157
verificações. As 144 reaplicações dos 72 modelos são exatamente iguais
às previsões salvas; as 864 métricas foram recalculadas, com tolerância
numérica de 1e-12. Foram reconstruídos o sorteio, as 24 máscaras e os
72 conjuntos de amostras/respostas/pesos, sem repetir os fits. Modelos
não retêm todas as listas originais de pesos: a auditoria confere o
contrato/código e os artefatos, não a trajetória inteira de otimização.

No recorte de cheias do teste são 237 alvos, 236 pares e uma falha por
grupo; a falha continua no denominador. Na validação há 28 alvos sem
falha. Ganhos de 6h e perdas de 12h nos dois perfis foram confirmados.
O coordenador conferiu os dez hashes da auditoria final, manifesto
`8e84daffc32231fd07b91cad8482a0b53ab14d7b02dc1c2dda923ec52cb73f8b`.
Nenhuma mudança operacional, promoção ou alegação de meta atingida.


## Idade explícita da observação de Muçum — 22/09, 01h24–01h27

A rodada anterior constitui progresso, com recuperação de séries convencionais
e experimento de atrasos concluído e auditado. Foi registrado novo protocolo
`docs/radar-anchor-age-feature-protocol.json` às 04:24:01,135046 UTC,
SHA-256 `c7ebbbb5221ed17ae21cf46b926829da1b99dca1991db435f6c2ea0c1af6ae63`.
O único campo adicional é a idade, em minutos, da observação que gerou a
âncora Muçum de cada origem. Não é o horário de coleta atual ou o tempo
de publicação histórica. O restante são as mesmas 180 colunas, amostras,
ordem, alvo, resposta, pesos e parâmetros da mistura anterior.

A busca temporal nas fontes seladas reproduz exatamente a âncora: último
registro antes de origem menos atraso aplicado, com idade máxima de 15min
nessa consulta. Não se pula um registro inválido para buscar um valor
antigo finito. A idade é origem menos timestamp dessa medição; fica NaN
quando a âncora é ausente. A matriz A tem 12.822 idades de 15min, seis de
30min e 84 ausências; B tem 12.824 de 30min, 15 de 45min e 73 ausências.
O sorteio e as 24 máscaras do experimento anterior foram mantidos.

A preparação foi selada antes do ajuste às 04:25:38,880348 UTC, após
reprodução exata das bases e aprovação das invariantes de idade. Os
24 modelos de 181 colunas terminaram às 04:27:29,988053 UTC em
`outputs/experimento-radar-idade-ancora-20260922/`. Foram reaplicados os
72 controles anteriores em 144 combinações modelo/perfil, exatamente.
O coordenador conferiu 35 hashes de artefatos, 90 de fontes e a NPZ de
idades. Manifesto:
`ba9eab5746c7537eb8d7bb923b034e223b998844a28982a7cbcd1ea200afdc74`.

As 204.168 linhas e 1.152 métricas preservam ambas as vistas e todas as
ausências. A análise `outputs/analise-radar-idade-ancora-20260922/`
contém 864 contrastes: idade versus mistura sem idade, versus controle
do perfil e versus controle cruzado. Ganhos isolados contra a mistura
não devem ser apresentados como ganho contra o melhor controle dedicado.

| Teste, observado >=7m | h | Acertos mistura → com idade | Controle dedicado | MAE mistura → com idade |
|---|---:|---:|---:|---:|
| Perfil A | 1 | 231 → 231 / 237 | 230 / 237 | 0,0763 → 0,0771m |
| Perfil A | 6 | 170 → 165 / 237 | 162 / 237 | 0,6021 → 0,6082m |
| Perfil A | 12 | 75 → 75 / 237 | 91 / 237 | 1,3287 → 1,3287m |
| Perfil B | 1 | 230 → 230 / 237 | 230 / 237 | 0,1051 → 0,1029m |
| Perfil B | 6 | 166 → 159 / 237 | 154 / 237 | 0,6355 → 0,6401m |
| Perfil B | 12 | 75 → 75 / 237 | 77 / 237 | 1,3849 → 1,3849m |

Não houve ganho consistente. Contra a mistura sem idade, os acertos de
cheias do teste melhoram em três/pioram em três/empatam em seis horizontes
no perfil A; em B, melhoram em três/pioram em quatro/empatam em cinco.
Os resultados de 12h permanecem abaixo dos controles dedicados. Nenhum
modelo foi promovido, emitido ou ajustado novamente depois desses erros.

### A coluna adicionada não foi usada nos modelos de 10–12h

A inspeção das árvores salvas encontrou uso efetivo da coluna de idade
em 17 dos 24 modelos. Em 10, 11 e 12h dos dois cortes, não há divisão
pela coluna180, e os 180 conjuntos de campos dos nós são exatamente
iguais aos da mistura sem idade. Em 9h da validação também não há divisão
pela idade: a única diferença é gain de uma folha (árvore45/nó27), sem
alterar rotas ou valores de previsão. Esse metadado não é uma mudança
no resultado. Não foram forçadas divisões ou alterados parâmetros para
obter resultado favorável depois da inspeção.

A auditoria independente
`outputs/auditoria-radar-idade-ancora-20260922/` passou 28.574 verificações:
144 aplicações dos controles e 48 novas exatamente reproduzidas, todas
as 1.152 métricas conferidas, 25.824 rastros de consulta reconstruídos
sem helper operacional. O suplemento de 12h confirma as 360 árvores e
interceptos idênticos entre candidato/controle misto nos dois cortes.
O coordenador conferiu seus 15 hashes; manifesto
`5642fb0415149d92527280a08777d5551c7cf9b8dc18e12f9f751441fa01e3d9`.

A correlação de 0,9983715 entre idade e perfil é associativa: os demais
atrasos mudam junto. A experiência não isola um efeito causal da idade
de Muçum nem prova generalização para configurações de atraso diferentes.
Os períodos continuam desenvolvimento já conhecido; a meta não foi atingida.

### Revisão do contrato de fuso

`outputs/pesquisa-fuso-contratos-hidroweb-20260922/` reexaminou 15
artefatos/recibos já preservados, sem novas requisições. O portal indica
UTC−3 e existem corroborações anteriores, mas os documentos examinados
não fecham explicitamente o vínculo com DataHora da operação legada
DadosHidrometeorologicosGerais de Muçum em 2025/2026. O manual legado
trata outra operação; os registros mensais convencionais e a API nova
têm semânticas próprias. A conclusão negativa é limitada ao acervo,
sem afirmar que documentação externa inexista. As flags permanecem
inalteradas. Passaram 32 verificações; oito hashes conferidos pelo
coordenador, manifesto
`5978f3a5a9b0d46d934c2001037bbebbfaf7eb86e8d119f7db9dd4e6fb87e8e3`.

### Observação das 01h recebida às 01h29

A ANA retornou 18,10m às 01h, com qualidade Dado aprovado. Recebimento
às 01h29min46,224256s BRT; recibo
`6e3be3cb009ebb443a0a3ce4c07aa316e315965d155ce2baacb7b5d119276542`,
corpo e cadeia de 2.398 registros conferidos. O relatório
`outputs/monitoramento-prospectivo/reports/20260922T042946226871Z/`
agora tem 61 pares associados e 104 ainda não vencidos. São 11 novos
pares para uma mesma observação, incluindo importação/revisão e banda
real zero; não são 11 novas medições ou eventos independentes.

Para esse alvo, o Radar regular emitido às 23h02 prevê 18,0829m, com
erro0,0171m e antecedência real1,96365h. A emissão de 18h02 prevê
17,4682m, erro0,6318m, antecedência real6,96399h. Ambas permanecem
registradas. A emissão de 00h08 tem erro0,0595m, mas antecedência real
0,85114h, portanto fica fora das bandas1–12h da meta. O acerto isolado
não demonstra98%; permanecem zero pares elegíveis à meta certificada.


## Tendência disponível e componente linear — 22/09, 01h40–01h45

A rodada anterior constituiu progresso: completou o experimento de idade,
a auditoria independente e nova observação. Esta rodada permanece somente
Radar; a retirada expressa de HGE/ARNO continua prevalecendo sobre o texto
antigo da meta. Não houve alteração operacional ou novo ciclo da mesma hora.

### Diagnóstico que orientou a hipótese

`scripts/hydro_radar_trend_diagnostic.py` registrou o plano às
04:40:49,283857 UTC antes dos cálculos. O diagnóstico terminou às
04:40:50,223830 em `outputs/diagnostico-radar-tendencia-atrasos-20260922/`:
4.608 métricas, 768 transições, 96 faixas de resposta de treino e 9.216
reconciliações com o placar congelado. Manifesto
`f1e1bd66588cd702c451e1aa9bb0fcb4483529c77dd2afcdda0de5bb9ef731e7`.
As quatro famílias, os dois perfis, ambos os cortes e todos os 12 horizontes
foram mantidos. Perfis são duas vistas dos mesmos horários, não réplicas
independentes. Plano, código e fontes preservados.

A tendência conhecida é a coluna 2, Muçum dH1, com limiares inclusivos
±0,10 m/h nominal. Movimento posterior usa observado menos base com
limiares ±0,50 m; faixa de resposta usa os extremos do treino de cada
família/corte/horizonte. As duas últimas partições usam informação futura
apenas para diagnóstico, nunca para selecionar uma previsão na origem.
Faltas de verdade são separadas; faltas de previsão permanecem falhas.
No recorte alto, classified_rows inclui os altos conhecidos mais os alvos
ainda desconhecidos, sem classificar estes últimos como cheias.

No candidato com idade em test/12h, perfil A, as 12 respostas acima do
máximo de treino não têm acertos e apresentam subestimação média de
5,9753 m. Porém, dentro da faixa de respostas, há somente 72/198 acertos;
em B, 73/197. Suporte univariado não certifica similaridade multivariada.
Na regressão de 6h da idade contra a mistura, a tendência conhecida
atribui saldo de acertos 0/−3/−2 a subida/descida/estabilidade no perfil A;
em B, −3/−2/−2. Não há fundamento para correção constante positiva.

A auditoria `outputs/auditoria-radar-tendencia-atrasos-20260922/` passou
12.828 verificações e conferiu todas as três tabelas solicitadas.
Reconstruiu 51.648 células dH1/dH2 diretamente dos históricos ANA.
Em 9 posições de A e 26 de B, o intervalo real dos registros de dH1 é
45 ou 75 minutos, apesar do divisor nominal de uma hora. Isso permanece
uma ressalva de contrato, sem arredondamento ou correção oportunista.
Os 12 hashes da auditoria foram conferidos pelo coordenador; manifesto
`f462c17c701dbe82857c34a26b49f0e98cf63fa7e1b9d7b1f78e28620c9adb52`.
A classificação dos maiores erros teve integridade conferida pelo agente,
mas seu ranqueamento não foi incluído no escopo independente desta auditoria.

### Experimento linear mais árvores dos resíduos

Protocolo `docs/radar-linear-trend-hybrid-protocol.json`, SHA
`523a56df3d6fe52a7ef856bf5f2d22be17f31a2b2f2f471a63d5592f23b2a613`,
registrado antes do ajuste. Manifesto pré-ajuste às 04:43:23,949303 UTC;
conclusão às 04:45:13,936891 UTC. Código
`scripts/hydro_radar_linear_trend_hybrid.py`; resultados
`outputs/experimento-radar-tendencia-linear-20260922/`.

Foram ajustados 24 conjuntos (48 estimadores): Ridge alpha1000 fixo com
as 20 tendências existentes dos quatro postos, seguido por HGB dos
resíduos, que recebe os 180 campos originais. A matriz, as 24 máscaras,
a atribuição PCG64(57), ordem, bases, alvos, pesos e parâmetros das árvores
são os da mistura anterior; nenhuma idade adicional ou amostra duplicada.
A mediana de imputação é não ponderada e usa somente treino; média e
escala são ponderadas pelos pesos originais, também só de treino.
As tendências de treino são todas finitas por contrato complete24;
na avaliação, a imputação afeta somente Ridge, mantendo NaNs na árvore.
Os pesos da árvore derivam da resposta original, não do resíduo Ridge.
A inferência é base + Ridge + árvore residual, sem truncamento ou troca
por horizonte. O componente linear isolado também foi reportado.

Os 72 modelos de controle foram reaplicados nos dois perfis, com igualdade
exata nas 144 aplicações. As 204.168 linhas e cinco famílias geraram
1.440 métricas; 34 hashes de artefatos e 85 fontes foram conferidos pelo
coordenador. Manifesto do experimento
`61a83240001370d94409e70a6a7de321f43f51131dc2c8a94636650afb8a9d53`.
As equações normais ponderadas do Ridge e do intercepto tiveram resíduos
absolutos abaixo de 1e−7; isso verifica ajuste numérico, não assertividade.

No recorte test observado ≥7 m, com 237 alvos, 236 pares e uma falha:

| Perfil | h | Acertos mistura → híbrido / alvos | MAE mistura → híbrido | Maior erro mistura → híbrido |
|---|---:|---:|---:|---:|
| A | 1 | 231 → 233 / 237 | 0,0763 → 0,0574 m | 1,1414 → 0,9270 m |
| A | 6 | 170 → 165 / 237 | 0,6021 → 0,4513 m | 6,2996 → 4,0801 m |
| A | 12 | 75 → 91 / 237 | 1,3287 → 1,1107 m | 7,7928 → 8,9919 m |
| B | 1 | 230 → 233 / 237 | 0,1051 → 0,0712 m | 1,5158 → 1,0790 m |
| B | 6 | 166 → 161 / 237 | 0,6355 → 0,4734 m | 6,5058 → 4,5216 m |
| B | 12 | 75 → 94 / 237 | 1,3849 → 1,1675 m | 7,6069 → 8,9139 m |

MAE melhora nos 12 horizontes altos de test em ambos os perfis; acertos
melhoram em 11 e pioram em 6h. No conjunto de todos os níveis, acertos
pioram em sete horizontes de A e quatro de B. Na validation de cheia,
pioram em cinco de A e seis de B. Os controles dedicados continuam
visíveis: test/A/12h já tinha 91 acertos, igual ao híbrido. Ganho sobre
a mistura anterior não prova ganho sobre toda referência.

A análise `outputs/analise-radar-tendencia-linear-20260922/` preserva
864 contrastes e decompõe os seis maiores erros de test/12h em 120
contribuições lineares. No pior A, origem 21/07 às 16h, base 3,27 m,
alvo 14,49 m: Ridge acrescenta 0,6689 m e a árvore residual 1,5592 m,
resultando em 5,4981 m, contra 6,6972 m da mistura anterior. As cinco
tendências Carreiro estão ausentes; dH1 Muçum = −0,14 m/h nominal.
A piora extrema é subestimação. A decomposição não prova causalidade
pela falta de Carreiro e não autoriza usar o movimento futuro no modelo.

233/237 em 1h corresponde a 98,31% histórico de desenvolvimento em um
horizonte nominal. Não demonstra o objetivo prospectivo em todas as bandas
reais de 1–12h, nem tamanho amostral ou dez eventos certificados. Todos
os períodos já eram desenvolvimento. Nenhum candidato foi promovido e
nenhum novo ajuste foi escolhido depois de ver estes resultados.

### Observação recebida às 01h44

Nova consulta pública ANA preservou recibo
`675b5b49a62f46c18d2a7cda24ff9a681e21e6cb94e6c2cc90e9d1565ceca641`
às 04:44:58,738957 UTC. Última observação pelo maior valid_at: 18,22 m
às 01h15 BRT, Dado aprovado. Corpo e cadeia de 2.399 registros conferidos.
O resumo inicial da ferramenta encontrou nome de campo incorreto depois
da captura; a recuperação leu o recibo já gravado, sem nova requisição.
Relatório `outputs/monitoramento-prospectivo/reports/20260922T044458741583Z/`:
165 pares, 61 associados e 104 ainda não vencidos, zero elegíveis à meta
certificada. A medição de quarto de hora não gerou alvo horário novo.
Fuso e datum continuam não certificados. A meta permanece ativa.


### Auditoria final da componente linear

`outputs/auditoria-radar-tendencia-linear-20260922/` encerrou estável com
5.982 verificações: 24 conjuntos, 144 reaplicações dos controles e 96
saídas novas exatamente reproduzidas (Ridge isolado e híbrido), 1.440
métricas conferidas, incluindo 864 métricas dos controles idênticas.
Medianas não ponderadas e padronização ponderada foram reconstruídas
somente do treino; máximo resíduo das equações Ridge 1,28e−10 e do
intercepto 3,20e−13. As duas maiores falhas de 12h foram reconstituídas
independentemente. Não houve refit ou rede na auditoria.

O coordenador conferiu os 12 hashes e o manifesto
`7ee8854f302477c9c97bf7f01bcf92beced07f371555b2e456aa86b22078d27a`.
A evidência combina código congelado, contratos, dados e artefatos: o
HGB salvo não retém todos os pesos/resíduos passados ao otimizador e não
os certifica isoladamente. A reprodução não altera o resultado misto,
a ausência de promoção ou as pendências da meta de 98%.


## Exposição controlada à falta do Carreiro — 22/09, 01h52–01h54

A rodada anterior foi progresso: completou diagnóstico, 24 conjuntos
lineares/híbridos, auditorias e captura pública. A hipótese desta rodada
foi a diferença entre treino completo e ausência real do Carreiro, sem
atribuir causalidade às maiores falhas. Escopo permanece somente Radar.

### Contrato e diferença entre treino e avaliação

O agente reconstruiu diretamente da fonte ANA as 154.944 células dos
blocos Carreiro dos dois perfis: colunas 18–23 são nível e tendências
nominais dH0.5/1/2/4/8 do posto 86500000, sem vazão ou chuva. Nas
12.912 origens de cada perfil, são 835 blocos totalmente ausentes,
90 parcialmente ausentes e 11.987 completos. As 24 máscaras de treino
não têm nenhuma ausência nesse bloco, por exigirem complete24.

No recorte de cheia de test, os blocos totalmente ausentes são 77/82/88
entre os 237 alvos de 1/6/12h; entre os 236 pares, são 76/81/87. Há
16/15/9 blocos parciais. Os 28 alvos altos de validation têm blocos
completos em todos os horizontes. A diferença de disponibilidade não
prova que ocultação aleatória imite os mecanismos/durações das falhas.

`outputs/auditoria-radar-ausencia-carreiro-20260922/` passou 299
verificações, sem carregar/ajustar modelos. O coordenador conferiu
os nove hashes; manifesto
`e6311673913aa3b7670afda4e1a439af4f9f853032bc31a3699807680ec5e076`.

### Treino com ocultação predefinida, avaliação intacta

Protocolo `docs/radar-carreiro-missing-exposure-protocol.json`, SHA
`5360df29a1c77e5b4bf69a21f56dddf2530428e928c299f7d69b444b8caf4aeb`,
registrado antes do ajuste. Código `scripts/hydro_radar_missing_exposure.py`.
Manifesto pré-ajuste às 04:52:36,978529 UTC e término às
04:54:27,096220 UTC em `outputs/experimento-radar-ausencia-carreiro-20260922/`.

Generator(PCG64(58)).random(n)<0.25 selecionou 3.274 das 12.912 origens
da grade, antes das máscaras e sem usar alvos, erros ou atribuição do
perfil. Em cada treino, somente as seis colunas Carreiro dessas origens
foram tornadas NaN numa cópia da matriz. A seleção por origem é a mesma
nos cortes/horizontes. Cada origem física continua contribuindo uma vez,
com o perfil A/B originalmente atribuído; todos os outros campos,
as 24 máscaras, a ordem, bases, respostas, pesos e configurações HGB
foram preservados. Não há componente linear nem idade adicional.
Avaliação usa as matrizes reais originais sem essa ocultação.

Foram ajustados 24 modelos e reproduzidas exatamente 144 aplicações dos
72 controles. 204.168 linhas, quatro famílias e 1.152 métricas;
34 artefatos e 85 fontes tiveram hashes conferidos pelo coordenador.
Manifesto `9d3532c5807b5bdca12e91e3253e022a3a089f2add38b22c251ca3ea5bb2322d`.
Plano de seleção NPZ SHA
`0fabcb9edd790ef1f2eeb641fcddc4a401ab08223d17e05c08e3c9371ba35ecd`.
Em test/12h, 2.364 de 9.269 origens foram ocultadas, incluindo 49 de
194 alvos altos; são 14.184 células adicionais ausentes. Em validation/12h,
são 838/3.513 origens, incluindo 39/166 alvos altos. Os alvos e pesos
não foram alterados para favorecer essas amostras.

No recorte test observado ≥7 m, 237 alvos, 236 pares e uma falha:

| Perfil | h | Acertos mistura → candidato / alvos | MAE mistura → candidato | Maior erro mistura → candidato |
|---|---:|---:|---:|---:|
| A | 1 | 231 → 231 / 237 | 0,0763 → 0,0763 m | 1,1414 → 1,0893 m |
| A | 6 | 170 → 158 / 237 | 0,6021 → 0,5987 m | 6,2996 → 5,9690 m |
| A | 12 | 75 → 78 / 237 | 1,3287 → 1,3028 m | 7,7928 → 7,5681 m |
| B | 1 | 230 → 230 / 237 | 0,1051 → 0,1029 m | 1,5158 → 1,4594 m |
| B | 6 | 166 → 153 / 237 | 0,6355 → 0,6288 m | 6,5058 → 6,3322 m |
| B | 12 | 75 → 81 / 237 | 1,3849 → 1,3624 m | 7,6069 → 7,4350 m |

Contra a mistura, em cheia/test, A melhora acertos em seis horizontes,
piora em cinco e empata em um; B melhora em dois, piora em quatro e
empata em seis. O controle dedicado A de 12h tinha 91 acertos, acima
dos 78 deste candidato. Na validation/6h, A cai 24→23/28, enquanto
B sobe 23→26/28, mas o MAE de B piora 0,2344→0,2858 m. Todos esses
resultados permanecem, sem seleção posterior de perfil/horizonte.

`outputs/analise-radar-ausencia-carreiro-20260922/` preserva 864 contrastes.
A partição posterior por disponibilidade real tem 1.152 métricas e 288
transições, reconciliadas com 2.304 verificações ao total congelado.
Em test/6h alto, blocos completos caem 113→102/140 em A e 109→99/140
em B; totalmente ausentes caem 42→41/82 e 42→40/82. Em 12h totalmente
ausentes, sobem 14→16/88 e 15→19/88. Portanto a hipótese traz ganho
limitado em 12h e perda relevante em 6h, não uma melhoria sustentada.

Nenhum modelo foi promovido, nenhuma previsão horária foi reescrita e
nenhum novo valor de probabilidade/semente foi escolhido após resultados.
Falta aleatória por origem não reproduz a duração nem a causa das falhas
reais. Os períodos continuam desenvolvimento conhecido; a meta de 98%
não foi atingida e permanece ativa.


### Auditoria final da exposição Carreiro

`outputs/auditoria-radar-exposicao-carreiro-20260922/` encerrou com
2.865 verificações: seleção PCG64(58) de 3.274/12.912 origens exata,
24 máscaras/treinos reconstruídos, 48 aplicações novas e 144 controles
exatamente reproduzidos sobre inputs reais intactos. Conferiu 1.152
métricas, incluindo 864 controles idênticos, e os seis contrastes
críticos de disponibilidade (12 grupos) citados acima. A auditoria
anterior de contrato/ausência foi preservada em sua pasta própria.

O coordenador conferiu os 11 hashes e o manifesto
`3fd42225e6e61e5c6d5728f903c4c2d7c1a62b5deb47c02bd18a1db1dcd6e202`.
Não houve refit ou rede na auditoria; código, máscaras e reconstrução
corroboram o contrato, mas o modelo HGB salvo não retém sozinho todos
os dados/pesos consumidos no ajuste. O resultado misto permanece sem
promoção ou alegação de 98% prospectivo.


## Ciclo regular Radar das 02h e pesquisa de lacuna — 22/09

A rodada anterior foi progresso: completou 24 candidatos de exposição
à ausência, confronto integral e auditoria. Nesta rodada, foi confirmada
a ausência de processo horário ativo e que a última emissão regular era
a de 01h antes de aguardar a fronteira das 02h. O ciclo atual começou
às 02h00min11 em `outputs/mucum-hourly-20260922T020011-0300/` e encerrou
com processo terminal exit0. Não houve repetição da hora anterior.

### Emissão e conferência das fontes

Emissão somente Radar às 02h02min07,766367 BRT; recibo
`fd47d506fd134b2e47e40ec7d74be104d68af7500a4512cda18340f5a1853fd8`.
A última medição usada foi 18,33 m às 01h30, com idade real de
32,12943945 minutos na emissão. São 133 coletas, duas falhas auxiliares
SIGMA e nenhuma falha obrigatória ANA/CERAN/Open-Meteo. Os 22 artefatos
selados, 200 recibos de entrada, encadeamento, conclusão do ciclo e
unicidade da emissão foram conferidos. As 14 inferências dos modelos
salvos reproduzem exatamente os pontos registrados, cobrindo bandas
reais 1–12h; há também pontos nas bandas 0 e 13, fora da meta.

O primeiro ponto, às 03h, é 18,8783 m, mas antecedência real de somente
0,96451h: não conta como banda real1h. O maior ponto horário é 19,4420 m
às 06h, e o último às 16h é 17,4789 m. São previsões experimentais,
sem comprovação de pico contínuo, intervalo de confiança ou98%.
`verify_receipt.py`, `receipt-verification.json` e `pipeline.log` estão
na pasta do ciclo; o log temporário desta rodada foi movido para lá.

Relatório `outputs/monitoramento-prospectivo/reports/20260922T050207867552Z/`:
2.602 registros,179 pares,61 associados,12 sem observação exata no
momento e106 ainda não vencidos,zero elegíveis à meta certificada.
Oito janelas horárias encerradas têm entrega completa; cobertura de
entrega não demonstra execução pelo agendador nem precisão do nível.

### Suporte do treino e comparação de emissões

`outputs/auditoria-suporte-radar-live-02h-20260922/` reconstruiu os
14 memberships,2.520 limites por campo e14 inferências. A âncora atual
18,33 m supera o máximo15,31 m das âncoras e alvos de treino. Há21
campos acima e2 abaixo da faixa univariada em cada horizonte, sem
inputs ausentes. O treino mantém o corte exclusivo21/09 às00h BRT;
último alvo efetivamente usado20/09 às23h. As contagens vão de10.899
em1h a10.872em14h. Os quatro hashes foram conferidos; manifesto
`352d8582de670ff02820b3a9736f2e1f87f48520f4ca2229b2b9ec042447cda3`.
Essas faixas são diagnóstico, não restrição de previsão ou incerteza.

`outputs/diagnostico-radar-emissoes-01h-02h-20260922/` compara os13
alvos compartilhados. A maior revisão ocorre às07h:18,5657→19,2283 m,
+0,6625 m. O maior ponto horário passou de19,2750 m às04h na emissão
anterior para19,4420 m às06h na atual. Revisão entre emissões com
informações distintas não é erro de previsão nem intervalo de confiança.
Nas12.912 origens anteriores ao corte, os alvos históricos permanecem
exatos, mas144.159 células de75colunas derivadas mudaram. A comparação
isolada não atribui essas diferenças a atrasos ou revisão de fonte bruta.
Nenhuma emissão antiga foi substituída.

### Consistência da receita declarada

`scripts/hydro_radar_recipe_audit.py` gerou a auditoria final
`outputs/auditoria-radar-identidade-receita-20260922-v2/`. Das11emissões
regulares Radar,10têm blobs suficientes:240artefatos conferidos e
140estimadores Radar inspecionados, sem inferência ou novo ajuste.
Em cada uma das três versões verificáveis, código/requisitos declarados,
runtime, parâmetros dos estimadores e corte de treino são iguais entre
suas emissões. A versão atual tem cinco emissões com uma receita
declarada e cinco conjuntos de pesos diferentes. Dados atualizados e
reconstrução com atrasos dinâmicos podem mudar pesos sem mudar essa receita.

A primeira emissão antiga não tem blobs de artefatos nem runtime
preservado suficiente; foi marcada não verificável, sem substituir
pela versão atual dos arquivos. Os modelos não Radar de pacotes antigos
compartilhados nunca foram carregados. A assinatura não prova inventário
transitivo completo, todos os arquivos estáticos de parâmetros, igualdade
de previsões ou meta cumprida. O model_version operacional continua sendo
baseado no script principal; nenhum registro foi renomeado retroativamente.

O primeiro rascunho da auditoria confundiu arquivos antigos de estado
NPZ/JSON com código e encontrou diferenças irrelevantes para essa receita.
Sua pasta sem sufixo v2 foi preservada como resultado superado; não é
prova de mudança de método. A versão corrigida exclui esses estados e
separa pesos ajustados da identidade declarada. Cinco hashes finais
conferidos; manifesto
`182bf2787b4e9720835d72733a11241c0855d6f7e28841110046d7020833e9af`.

### Pesquisa oficial da lacuna do Carreiro em julho

O agente concluiu busca limitada em
`outputs/pesquisa-carreiro-lacuna-julho-20260922/`:quatro buscas e cinco
consultas diretas públicas. Não recuperou série alternativa sub-horária
aprovada para21–22/07/2026. ANA retornou192registros/15min com valores
de sensor, todos explicitamente Dado reprovado. NivelFinal está vazio
em188, com apenas quatro leituras finais/manuais aprovadas:21/07 às07h
236cm e17h570cm;22/07 às07h840cm e17h852cm. Todos os campos coincidem
com o XML antigo, sem recuperação por revisão entre as capturas.
Os valores reprovados não foram convertidos em observações válidas.

SACE respondeu200 com2.878linhas recentes de22/08 a22/09, fora da
janela de julho; isso não prova inexistência no banco histórico.
SIGMA retornou404 nos dois dias, com corpos preservados. Essas duas
URLs já constavam como404 em um manifesto anterior sem corpos, mas o
inventário inicial do agente não detectou isso; as reconsultas evitáveis
foram explicitadas, sem retries posteriores. A nota oficial estadual
sobre a chuva não oferece série do posto. Horário, QC, datum e primeira
publicação continuam tratados separadamente e não certificados.

A pesquisa passou15verificações, preservou19artefatos e seus hashes foram
conferidos pelo coordenador; manifesto
`a5512d31fc139d60d30f858c4150a32b842365ecdd5371065c7fdaebef05be55`.
Não houve conta, mensagem externa, preenchimento de lacuna, importação,
treino com esses dados ou promoção. Conclusão negativa limitada às fontes
consultadas, sem afirmar inexistência absoluta. Meta permanece ativa.


## Variação entre as emissões de 01h e 02h — 22/09, diagnóstico controlado

A rodada anterior constituiu progresso: nova emissão horária conferida,
busca pública da lacuna e auditoria de identidade. Nesta rodada não
houve ajuste ou emissão: foi isolado o efeito dos modelos salvos e das
mudanças de reconstrução histórica antes de propor outro candidato.

`outputs/diagnostico-treino-radar-01h-02h-20260922/` compara as mesmas
12.912 origens anteriores a21/09 às00h BRT. Os114campos dos históricos
brutos são idênticos, incluindo NaNs; os campos brutos da grade também.
As144.159células alteradas estão exatamente nas75colunas45–119, de chuva
e cobertura. As outras105colunas são idênticas, inclusive as60de previsão
meteorológica histórica. Todos os14memberships, bases e alvos comuns
permanecem exatos:nenhuma origem foi adicionada ou removida. O número
de exemplos vai de10.899em1h a10.872em14h em ambos os ciclos.

O CSV de idades contém atrasos de níveis; ele não certifica por si os
atrasos de chuva. prepare_current calcula a disponibilidade de chuva
pelo último rain finito anterior à origem e reaplica esse atraso à grade
histórica, com truncagem para slots15min. A verificação independente
examina esse contrato separadamente. Sete hashes do diagnóstico foram
conferidos; manifesto
`003c25303e8a404179a273465d00d97c46cb910815ab2c60e8027a08ae9dfeff`.

### Modelos diferentes, inputs fixos

`scripts/hydro_radar_fixed_input_drift.py` registrou o plano antes de
reaplicar os modelos. Em `outputs/diagnostico-radar-pesos-inputs-fixos-20260922/`,
28modelos Radar salvos foram aplicados aos dois vetores180originais,
totalizando56resultados escalares. Os28casos com modelo e origem
correspondentes reproduzem exatamente as previsões emitidas. Parâmetros,
versão, runtime e corte são iguais. Entradas/modelos e recibos foram
conferidos contra os blobs; o registro permaneceu intacto.

Com os inputs e a base das02h fixos, a maior diferença entre pesos
antigos e novos é−0,1655285 m em horizonte nominal10h (alvo12h):
18,3170902 m com o conjunto anterior, contra18,1515617 m emitidos.
Nenhum dos14horizontes tem diferença superior a0,50 m nessa condição.
Com o vetor das01h, o maior efeito é+0,3861618 m em12h. São diferenças
computacionais, não erros ou ganhos de precisão. Reutilizar os pesos
anteriores com outra configuração de atraso não foi escolhido para operar.
Seis hashes conferidos; manifesto
`e19764d3b355ae6e915a32e540b5d64fa0304a3b2ff530c7500e3b3f1c5f637d`.

Comparar origens01h/02h no mesmo horizonte nominal envolve alvos diferentes.
Por isso essa tabela não foi apresentada como revisão do mesmo alvo.
O passo adicional `outputs/analise-radar-revisao-mesmo-alvo-20260922/`
recompõe as13revisões em alvos compartilhados por um caminho explícito:
primeiro atualizar inputs/base e horizonte com os pesos antigos; depois
trocar pelos pesos atuais, mantendo esses inputs. Cada identidade soma
à revisão observada com tolerância absoluta1e−12. As parcelas dependem
da ordem escolhida e não são causas físicas isoladas.

Para o alvo07h, a revisão18,5657436→19,2282537 m (+0,6625101 m) se
decompõe em+0,5408062 m de atualização conjunta de inputs/base/horizonte
e+0,1217039 m da troca de modelos nos inputs atuais. O intermediário
19,1065498 m não foi emitido ou incorporado à pontuação. Isso afasta
atribuir toda a revisão de66cm à mudança dos pesos, sem provar qual
previsão está correta. Três hashes conferidos; manifesto
`b6cde7d8d3a6580a180ca8caf62ed017255810aab1aee27b1eb7ff79b99d8a8d`.
Nenhum candidato novo, promoção, mudança de atraso ou meta atingida.


### Verificação independente do realinhamento

`outputs/verificacao-treino-radar-01h-02h-20260922/` passou381checks:
114campos normalizados sem revisão,14memberships/bases/alvos/respostas/
pesos idênticos, e confirmação das75colunas/144.159células alteradas.
A reconstrução independente de1.936.800células de chuva preserva NaNs
exatamente e difere no máximo8,87e−14 por aritmética de ponto flutuante.
São sete mudanças de atraso de chuva:86060010 1020→1080min;
86102000 900→960;86125000 781→841(com52→56slots15min);
86200900 840→900;86298000 360→420;86448000 360→420;
86403000 120→60. Nas seis primeiras fontes, a leitura não avançou;
na última, chegou chuva às01h. Para86200900, o atraso de nível é
780→840min, diferente do atraso de chuva; não foram confundidos.

A auditoria também reproduziu28diagonais exatamente e conferiu o alvo07h:
18,5657436028→19,1065497967→19,2282536724, com as parcelas indicadas.
Nenhum fit, rede ou emissão nessa auditoria. Seus15hashes foram
conferidos pelo coordenador; manifesto
`fcb54f130838083221237d27489729d6a931e1e3a02cc15cfcd12371ebe21ecb`.
A atribuição é à reconstrução computacional dos inputs; não estabelece
causalidade física, melhora de acurácia ou equivalência fora destes ciclos.

### Observação das01h45 recebida às02h15

Captura ANA às05:15:42,589228UTC preservou recibo
`c868479ad9cf327156c0350313e889050b560f2a60ef17981d2e2165f0a848fe`.
Última leitura pelo maior valid_at:18,39m às01h45BRT, Dado aprovado;
fuso e datum continuam não certificados. Corpo e cadeia de2.603registros
conferidos. Relatório
`outputs/monitoramento-prospectivo/reports/20260922T051542591962Z/`:
179pares,61associados,12sem observação exata e106não vencidos;zero
pares elegíveis à meta certificada. A nova medição de quarto de hora
não gerou novo alvo horário. A meta segue ativa e não atingida.


## Limiar do peso de treino em 7m — 22/09, 02h19–02h21

A rodada anterior foi progresso: isolou o realinhamento da chuva,
conferiu revisões com inputs fixos e capturou nova medição. Esta rodada
examinou uma hipótese distinta: o peso de treino aplica bônus no alvo≥9m,
enquanto o recorte analítico previamente definido para a meta é≥7m.
A hipótese não modifica a tolerância0,50m nem transforma7m em alerta oficial.

Protocolo `docs/radar-flood-weight-7m-protocol.json`, SHA
`1f8ccf42085b3c3430aa9c7efe03b49eb4ddf7dcf90cb688ce156ebb7355c35c`,
registrado antes do ajuste. Código `scripts/hydro_radar_flood_weight.py`.
Em `outputs/experimento-radar-peso-cheia-7m-20260922/`, o manifesto
pré-ajuste foi gravado às05:19:39,908589UTC e a conclusão às
05:21:30,612684UTC. Foram24modelos novos,144aplicações dos controles
exatamente reproduzidas,204.168linhas e1.152métricas.

A única mudança no candidato misto foi o peso:
1+2*(abs(delta)≥1)+2*(target≥9) →
1+2*(abs(delta)≥1)+2*(target≥7).
Amostras em[7,9) ganham exatamente2, sem renormalização; as demais
não mudam. Os180campos, NaNs, máscaras, atribuiçãoPCG64(57), ordem,
bases, alvos, respostas, cortes e parâmetros HGB são os mesmos.
Não há componente linear, idade adicional ou ocultação do Carreiro.

Os48vetores de pesos antigos/novos e suas contagens/hashes foram
preservados antes do treino. Em test/12h,89amostras mudam de peso,
e a soma11.749→11.927 aumenta178. Em validation/12h,são64amostras
e4.909→5.037(+128). A conferência independente preliminar passou
284checks; os vetores esperados foram calculados sem usar o candidato.
O coordenador conferiu35artefatos,85fontes e dois arquivos preparados;
manifesto `e07254722fc03b05e08bd193f4c51744b843b60e5d5b68575516dba7bce8616d`.

No recorte test observado≥7m,237alvos,236pares e uma falha:

| Perfil | h | Acertos peso9→peso7 / alvos | MAE peso9→peso7 | Maior erro peso9→peso7 |
|---|---:|---:|---:|---:|
| A | 1 | 231→231 /237 | 0,0763→0,0775m | 1,1414→1,1736m |
| A | 6 | 170→166 /237 | 0,6021→0,6065m | 6,2996→6,3078m |
| A | 12 | 75→67 /237 | 1,3287→1,3413m | 7,7928→7,5320m |
| B | 1 | 230→230 /237 | 0,1051→0,1026m | 1,5158→1,5507m |
| B | 6 | 166→169 /237 | 0,6355→0,6406m | 6,5058→6,4804m |
| B | 12 | 75→68 /237 | 1,3849→1,3923m | 7,6069→7,6053m |

Não houve ganho sustentado. Contra o controle misto, nos12horizontes
altos de test,A melhora em6,piora em4 e empata em2;B melhora em6,
piora em2 e empata em4. Porém, no conjunto de todos os níveis, os
acertos pioram em6horizontes nos dois perfis. Na validation de cheia,
A piora em5 e B em6. Em validation/A/12h,o MAE cai0,8212→0,7612m,
mas os acertos caem8→6/28; o erro médio não substitui a tolerância da meta.
O controle dedicado A de12h tinha91acertos, acima dos67do candidato.

`outputs/analise-radar-peso-cheia-7m-20260922/` contém864contrastes.
A avaliação complementar usa as mesmas fronteiras dos pesos: abaixo7,
[7,9),≥9 e desconhecido. Suas768métricas e192transições recompõem
os totais originais geral/≥7 por2.304verificações. Em test/12h, a
própria faixa[7,9) piora44→39/120emA e49→40/120emB. Nos alvos≥9,
A cai31→28/117 e B sobe26→28/117. Nenhuma faixa futura é usada para
escolher modelos na emissão; alvos desconhecidos continuam separados.

As duas vistas de atraso não são amostras independentes, e os períodos
já foram utilizados no desenvolvimento. Nenhuma promoção, nova busca de
limiar, alteração operacional ou previsão retroativamente substituída.
A meta de98% permanece ativa e não foi demonstrada.


### Auditoria final do peso7m

`outputs/auditoria-radar-peso-cheia-7m-20260922/` encerrou a etapa
final com2.917checks, preservando os284da conferência preliminar.
Os48vetores de pesos coincidem exatamente com expectativas independentes;
24máscaras/respostas/configurações foram conferidas,48aplicações do
candidato e144controles reproduzidas exatamente,1.152métricas verificadas
incluindo864controles idênticos. O suplemento confirmou os quatro grupos
de test/12h na faixa[7,9):A44→39/120 eB49→40/120.

O coordenador conferiu os16hashes; manifesto
`de957dd7733c5c1c9b9ad0b257d6d22d967d3e07ee4800bb37296288811ebbac`.
Sem refit ou rede. O HGB salvo não certifica isoladamente todos os pesos
consumidos pelo otimizador; a evidência combina código preservado,
vetores anteriores ao ajuste e reprodução. Nenhuma promoção ou mudança
no critério de sucesso resultou dessa auditoria.


## Captura das 02h34 e verificação do alvo das 02h — 22/09/2026

A captura ANA de 05:34:16,580219 UTC (02:34:16 BRT) trouxe
18,47 m às 02h e 18,55 m às 02h15, ambos Dado aprovado.
Recibo `b904257225dc2399a93a90d3b6f89f2cd28de1fd6a4b9fa562bc791cace68fb4`;
corpo bruto e cadeia de 2.604 registros conferidos. Os campos de
certificação de fuso e datum continuam falsos.

O relatório `outputs/monitoramento-prospectivo/reports/20260922T053416582836Z/`
passou de 61 para 73 pares diagnosticáveis; 106 permanecem futuros e
nenhum alvo vencido está sem observação exata nesta captura. Continuam
zero pares elegíveis à meta. Não foi emitido outro ciclo das 02h.

Em `outputs/verificacao-radar-alvo-02h-20260922/`, os 12 registros para
o mesmo alvo das 02h ficam separados por importação, revisão manual e
emissão, com antecedência real e versão preservadas no CSV. As quatro
emissões mais recentes erraram 0,1332; 0,2381; 0,1607; 0,2399 m.
A última tem apenas 0,9615 h de antecedência e não entra na faixa de 1 h.
Registros anteriores subestimaram mais o alvo: não se omitem seus erros.
Há apenas uma observação compartilhada por esses 12 pares, e não
12 eventos independentes. A mudança conjunta de dados, antecedência e
versão impede atribuir causalmente a diferença ao treinamento.

Foram feitas 72 verificações de erro, antecedência, faixa, tolerância,
exclusão e horário de registro. Manifesto
`ac156a9cd57b585b13c9388ddc967ccffcbe69b14aa44c160f2c2bab7d25a8c0`.
Nenhuma previsão foi substituída, nenhum ajuste executado e nenhuma
configuração operacional alterada. A meta permanece ativa e não atingida.
