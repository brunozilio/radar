# Previsão hidrométrica pública de Muçum

Em 23/09/2026, o usuário solicitou explicitamente exibir a previsão hidrométrica no gráfico e retirar a trava de publicação. O modelo é agora a previsão pública principal, com identificação experimental. A meta de 98% permanece não demonstrada; ela não bloqueia a exibição solicitada.

O caminho ativo de `hydro_site_projection.py` coleta somente os níveis ANA 86510000, 86472000, 86472600 e 86500000 e as vazões das três usinas CERAN. Chuva, cobertura regional de chuva, NWP e checkpoints do modelo anterior não são dependências desse cálculo. O coletor completo continua disponível para os fluxos de pesquisa legados.

A publicação tem identidade própria: `radar_mucum_hydrometry_v1`, versão `mucum-hydrometry-public-v1`. Usa os mesmos pesos congelados da avaliação anterior, SHA-256 `8adc838b20fba1ec3edd63db53e4575b0b8df59c22a777ada434ed773fb58c97`, sem retreinar, relabelar estações ou alterar arquivos históricos.

O adaptador de publicação conserva referência, emissão, valores e alvos reais. Exige níveis e vazões completos também nas horas anteriores usadas pelas variáveis do modelo. Não substitui dados ausentes por zero nem cria horas futuras novas a partir de uma referência atrasada. A referência mais recente completa deve ter até três horas de idade. Depois da primeira publicação hidrométrica, uma mesma referência não é recalculada nem substituída por uma anterior.

O resultado público é gravado em `forecast.json`; o arquivo de pesquisa `propagation-shadow.json` continua preservado com sua identidade original. Dados brutos, código, pesos, os dois resultados e recibo compõem a evidência permanente da tentativa. `latest.json` só é publicado depois da confirmação do arquivo e com os alvos ainda futuros. Os antigos `history.tar.gz` e `audit.tar.gz` não são exigidos por este modelo.

A verificação existente da aplicação continua a cada 15 minutos. O gráfico e a tabela exibem a previsão hidrométrica com os horários de cálculo, referência e alvos. Mensagens de espera só aparecem quando faltam as medições intrínsecas exigidas pelo modelo, e não pela ausência de chuva ou de certificação da precisão.

O [registro de avaliação inicial](mucum-propagation-shadow.md) e o [protocolo científico congelado](mucum-propagation-validation-protocol.json) permanecem como evidência histórica. A decisão operacional de exibir o modelo experimental não altera seus resultados, os limites de precisão conhecidos nem transforma a meta em atingida.
