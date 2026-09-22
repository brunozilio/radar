> **VERSÃO SUPERADA após auditoria:** foi corrigido o processamento das janelas de chuva. Consulte a [revisão e comparação dos erros](../mucum-auditoria-2026-09-21/relatorio-correcoes.md). Os números abaixo foram preservados como registro da emissão anterior.

# Muçum — previsão independente de seis horas

**21/09/2026. Base: 13h BRT, 7,46 m. Cálculo: 13h34 BRT.** Estação ANA/SGB 86510000. Valores referidos à régua dessa estação.

**Resultado:** a estimativa central indica subida para aproximadamente 11–12 m no fim da janela. A incerteza hoje é elevada. A oscilação de 18h para 19h resulta de ajustes separados por horizonte e não confirma o horário nem o nível de um pico.

| Horário BRT | Central (m) | Referência inferior–superior (m) |
|---|---:|---:|
| 14h | 7,9 | 7,5–8,4 |
| 15h | 8,8 | 7,4–10,3 |
| 16h | 9,4 | 7,7–11,0 |
| 17h | 10,4 | 8,3–12,5 |
| 18h | 11,5 | 8,8–14,1 |
| 19h | 11,3 | 8,2–14,3 |

A faixa é a estimativa central acrescida/subtraída do maior entre o percentil 90 do erro absoluto histórico em situações semelhantes e o percentil 90 do erro desta manhã. Não é intervalo probabilístico validado, nem máximo possível, nem cota de segurança. A série atual permanece fora do comportamento bem explicado pelos modelos em vários horários.

## O que foi efetivamente consultado

- Produção Cloudflare D1: consulta somente de leitura, zero linhas gravadas. O histórico curto de produção foi complementado diretamente nas fontes primárias.
- ANA: **27 estações a montante**, de abril/2025 a setembro/2026; 537,682 registros distintos de estação/hora ou estação/15 minutos. Nem todos os campos estão presentes em cada registro. O histórico inclui Muçum a 15,00 m em junho/2025 e 19,86 m em julho/2026.
- ONS: 38.776 registros horários das usinas Castro Alves, Monte Claro e 14 de Julho; CERAN complementa os horários mais recentes. Dados horários do ONS sujeitos a revisão, sem consistência final. A marca horária representa o fim do intervalo.
- SIGMA/HAR: 100 identificadores dentro da bacia, incluindo 69 da rede pública e 31 de redes particulares. Somados aos identificadores adicionais da ANA, o inventário contém **122 IDs**, não necessariamente 122 instrumentos fisicamente independentes.
- **A previsão não trata os 122 IDs como 122 contribuições independentes.** Os 27 com séries longas ANA entram na chuva espacial e/ou telemetria; as demais estações permitem conferência espacial. Séries curtas, sensores próximos e referências distintas impedem atribuir a cada ID um coeficiente confiável.
- Defesa Civil RS: oito estações conferidas; sete consultas históricas retornaram dados. Muitos Capões/Lagoa Vermelha retornou “Operação bloqueada”. Antônio Prado/Flores da Cunha apresentou nível inválido e homologação falsa, descartado. Muçum/Encantado usa outro datum e fica a jusante da régua-alvo: 40,85 m não equivale a 40,85 m na régua SGB.
- SGB/SACE: boletins históricos consultados e arquivados. O mais recente encontrado na listagem foi de 14/08/2026, às 22h; não foi usado como previsão vigente para 21/09.

## Leituras utilizadas como base

| Estação | Última observação até a base | Nível na própria régua (m) |
|---|---|---:|
| Muçum (86510000) | 13:00 | 7,46 |
| Linha José Júlio (86472000) | 12:30 | 7,34 |
| Santa Tereza (86472600) | 12:45 | 6,86 |
| Passo Carreiro (86500000) | 12:30 | 3,94 |
| Passo Tainhas (86160000) | 12:45 | 5,67 |

**14 de Julho às 13h:** afluência 4.534,89 m³/s e defluência 4.212,67 m³/s; às 10h a defluência era 512,86 m³/s. Castro Alves e Monte Claro estão em série com a 14 de Julho: suas vazões não foram somadas como volumes independentes.

Como conferência de ordem de grandeza, a telemetria ANA associa 7,46 m em Muçum a 2.127,21 m³/s; pares históricos próximos de 4.200 m³/s correspondem a aproximadamente 11,86 m. Isso é uma associação nível–vazão da própria ANA, não uma medição independente nem uma previsão por balanço de massa. Atenuação, armazenamento, tributários e eventual remanso impedem transportar esse número diretamente para um horário futuro.

## Conectividade, distâncias e propagação

A rede dirigida da BHO2017/ANA contém 367 trechos a montante do trecho da estação e cerca de 16 mil km² de drenagem. A delimitação inclui a microbacia inteira do trecho de saída (12,8 km²); não substitui um levantamento exato da seção. Distâncias seguem o canal projetado em SIRGAS 2000 / UTM 22S. Alguns pontos de estação exigem encaixe no rio conhecido.

**O Guaporé desemboca depois da régua SGB de Muçum.** Sua chuva não foi somada à área contribuinte direta dessa régua. Isso não exclui risco no município ou influência de remanso a jusante; o modelo não resolve hidráulica de remanso.

| Origem | Distância no canal | Atraso mediano da onda | P10–P90 entre eventos | Eventos | Velocidade aparente pela mediana |
|---|---:|---:|---:|---:|---:|
| Linha José Júlio | 37,6 km | 3,0 h | 2,0–3,0 h | 9 | 12,5 km/h |
| Santa Tereza | 20,5 km | 1,5 h | 1,0–2,0 h | 8 | 13,7 km/h |
| 14 de Julho | 40,3 km | 4,0 h | 1,8–5,0 h | 9 | 10,1 km/h |
| Passo Carreiro | 77,3 km | 8,5 h | 5,0–17,5 h | 6 | 9,1 km/h |
| Carreiro — Cotiporã/Dois Lajeados | 48,1 km | 9,0 h | 9,0–9,0 h | 1 | 5,3 km/h |

Os atrasos foram estimados alinhando ondas em janelas de 37 horas ao redor de cheias ≥7 m, com correlação ≥0,8. P10–P90 descreve a pequena amostra histórica, não limites de viagem. **Carreiro tem identificação fraca pela mistura de afluentes; Cotiporã tem apenas um evento.** A velocidade acima é de propagação aparente da onda, não velocidade medida da água. Não existe aqui tempo exato de chegada de cada gota ou pluviômetro.

## Chuva e participação das estações

A chuva foi distribuída por cinco regiões usando áreas de influência do sensor mais próximo em grade de 2 km. Um sensor pode representar área dos dois lados de uma divisa: isso é interpolação de chuva, não transferência de vazão entre bacias. Foram usados incrementos ChuvaFinal; o contador acumulado não foi tratado como chuva diária. Lacunas não viraram zero. O peso disponível deve cobrir ≥50% da região; a fração disponível também entra como variável no ajuste.

| Região | Área aproximada | Fração do peso com dado recente às 13h | Chuva horária representada |
|---|---:|---:|---:|
| Baixo Antas | 1379 km² | 95% | 7,0 mm |
| Carreiro | 2557 km² | 100% | 7,7 mm |
| Prata-Turvo | 3770 km² | 96% | 28,0 mm |
| Alto Antas | 6872 km² | 56% | 11,2 mm |
| Tainhas | 1458 km² | 61% | 11,4 mm |

A fração não mede a porcentagem real da bacia observada sem erro. As janelas dos sensores são assíncronas e podem terminar antes das 13h. Alto Antas e Tainhas têm cobertura mais fraca. Usaram-se chuva acumulada em 1/3/6/12/24h, atrasos de 3/6/12h e chuva antecedente de 48h. Não foi inventado um tempo de infiltração/encosta por pluviômetro.

Previsões meteorológicas GFS e ECMWF emitidas com antecedência de 24h foram testadas para chuva futura em 3/6h. Isso permite retrospectiva causal, embora não use a emissão meteorológica mais recente. O ensemble meteorológico atual foi consultado como conferência; não recebeu multiplicador arbitrário para compensar a chuva intensa da manhã.

## Calibração e erros verificáveis

Seis regressões regularizadas por horizonte combinam níveis e tendências, vazões/afluências das usinas, tributários, chuva por região e históricos distribuídos em atrasos de 0–24h. Uma delas inclui as previsões de chuva. O método é estatístico calibrado; não é um modelo hidráulico completo com seções, rugosidade, balanço de massa e manobras futuras de comportas.

Treino inicial: abril–setembro/2025. Seleção: outubro/2025–junho/2026. Teste temporal: julho–20/setembro/2026. O ajuste final usa alvos observados antes de 21/setembro. Os pesos entre modelos usam somente erros cujos horários-alvo já passaram, com memória exponencial. Hiperparâmetros foram escolhidos na validação. Os arquivos guardam cada previsão retrospectiva e seu erro.

A avaliação usa arquivos históricos hoje disponíveis, sujeitos a revisões. Não reconstrói o instante exato de publicação de cada mensagem antiga; portanto não prova o mesmo desempenho em operação ao vivo. A amostra de cheias é pequena e os dados do teste foram vistos durante o desenvolvimento desta análise.

| Antecedência | MAE teste temporal | MAE teste com nível ≥9 m | MAE desta manhã | P90 erro absoluto desta manhã |
|---|---:|---:|---:|---:|
| 1 h | 0,03 m | 0,04 m | 0,16 m | 0,45 m |
| 2 h | 0,07 m | 0,12 m | 0,49 m | 1,44 m |
| 3 h | 0,09 m | 0,21 m | 0,74 m | 1,63 m |
| 4 h | 0,11 m | 0,30 m | 0,92 m | 2,10 m |
| 5 h | 0,14 m | 0,42 m | 1,15 m | 2,67 m |
| 6 h | 0,18 m | 0,55 m | 1,63 m | 3,06 m |

Na comparação nas mesmas 1.357 origens do teste de 6h, a combinação teve MAE de 0,18 m, contra 0,62 m da persistência e 0,73 m da extrapolação da tendência de 2h. **Nas oito origens já verificáveis desta manhã, a persistência teve MAE de 1,52 m, ligeiramente melhor que os 1,63 m da combinação; a tendência teve 2,30 m.** O maior erro de 6h da combinação hoje foi 3,43 m. Portanto, o ganho histórico não se traduziu em superioridade demonstrada no evento atual.

**A evidência atual não sustenta prometer alta precisão nas seis horas.** O erro de 6h desta manhã é muito maior que o erro médio histórico. A faixa foi ampliada por esse motivo, e não deve ser interpretada como segurança abaixo do extremo superior. Chuvas novas, falhas de telemetria, remanso e operação das usinas podem mudar a evolução.

## Arquivos e reprodução

- `mucum-previsao-6h.png`: gráfico com a ressalva incorporada à imagem.
- `previsao-final.csv` e `previsao-combinada.json`: números, pesos e erros.
- `pluviometros-estrutura-completa.csv`: cada ID, nome, coordenadas, subbacia, canal, distância, papel no modelo e pesos da chuva.
- `ondas-calibradas.csv`: eventos usados para estimar propagação; `observacoes-base.csv`: idade da telemetria.
- `teste-combinado.csv`, `comparacao-referencias.csv`: retrospectivas e comparação com persistência/tendência.
- `verificacao-final.json`: verificações de causalidade, pesos, horário e base observada.
- Scripts locais: `hydro_extended_collect.py` → `hydro_routing_data.py` → `hydro_forecast.py` → `hydro_adaptive_ensemble.py` → `hydro_supporting_checks.py` → `hydro_final_report.py`.

As estimativas anteriores nas outras pastas ficam preservadas para auditoria; esta edição de base 13h é a versão consolidada deste trabalho. Nenhum alerta foi enviado e nenhum site foi publicado.

## Fontes primárias

- [ANA — serviço de telemetria](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx). Método DadosHidrometeorologicosGerais; códigos e períodos nos arquivos raw.
- [ONS — dados hidráulicos horários](https://dados.ons.org.br/dataset/dados_hidrologicos_ho).
- [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php).
- [Defesa Civil RS — rede hidrometeorológica](https://redehidrometeorologica.defesacivil.rs.gov.br/Mapa).
- [SGB — boletins da bacia do Taquari](https://www.sgb.gov.br/sace/boletins.php?idbacia=9).
- [SGB — pesquisa sobre tempo de propagação das cheias](https://rigeo.sgb.gov.br/handle/doc/25757).
- [Open-Meteo — arquivo de previsões anteriores](https://open-meteo.com/en/docs/previous-runs-api).

**Para comunicação pública:** compartilhar junto o horário-base, a faixa de erro e a identificação de previsão independente. As orientações oficiais de proteção e evacuação têm prioridade; este produto não determina locais seguros no município.
