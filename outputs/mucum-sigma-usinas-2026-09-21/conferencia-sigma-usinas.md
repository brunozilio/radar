# Conferência de SIGMA e usinas — 21/09/2026

Consulta: 2026-09-21T14:28:37.237978-03:00. Esta auditoria verifica dados e uso no cálculo; não é uma nova emissão da previsão de 12h.

## O que efetivamente entrou na previsão de 12h

- As três usinas CERAN (Castro Alves, Monte Claro e 14 de Julho): afluência, defluência e tendências no modelo estatístico. Na propagação por vazão, 14 de Julho é a entrada principal do rio das Antas; dados das três usinas ajudam a prever a vazão futura. Não são somadas três vezes como entradas independentes.
- 27 estações ANA: chuva ponderada por área, com pesos positivos; suas séries longas de abril/2025 a setembro/2026 sustentaram a calibração. Quatro réguas têm nível e tendência usados diretamente: Muçum, Linha José Júlio, Santa Tereza e Passo Carreiro.
- SIGMA: telemetria foi baixada e usada na avaliação espacial e conferência inicial. A última previsão de 12h NÃO usa diretamente as 100 séries SIGMA como preditores. Cinco códigos coincidem com as 27 séries ANA, para as quais se usou a fonte ANA.

## Nova consulta da SIGMA

Foram atualizados os 27 endpoints de catálogo identificados no HAR, 100 arquivos de séries individuais e três páginas CERAN. As 130 requisições responderam HTTP 200. HTTP 200 não garante observações válidas: 99 séries SIGMA continham registros de hoje e 98 tinham a última observação há até 60 minutos às 14h28. ICAXIA4 não tinha registros reconhecidos; INMET B856 tinha leitura às 12h, com aproximadamente 149 minutos de atraso.

O catálogo das 14h contém 98 códigos na bacia, sem novos códigos frente aos 100 anteriormente identificados. Foram preservados os 100 para não apagar sensores temporariamente ausentes. O inventário contém 47 CEMADEN, 7 SGB/CPRM, 7 Defesa Civil RS, 6 INMET, 2 EPAGRI, 23 Weather Underground, 7 Davis e 1 Ambient Weather. São redes agregadas pela SIGMA, não necessariamente equipamentos de sua propriedade.

Muçum aparece na SIGMA com 7,88 m às 13h45, igual ao registro ANA. Linha José Júlio e Santa Tereza têm registros recentes, mas campo de nível -999,9 nos arquivos consultados: isso é ausência, não nível negativo. Por isso, ter muitos arquivos atualizados não assegura que todas as variáveis estejam disponíveis ou corretas.

Os campos de chuva foram preservados na auditoria com suas posições originais (20 e 21), sem converter ausência em zero ou afirmar uma semântica homologada para todas as redes. Há checagens anteriores que apoiam a interpretação de chuva horária e acumulado diário, mas a validação por rede e a calibração da incorporação direta continuam necessárias. Não foi somado o acumulado de estações distintas como volume da bacia.

## Usinas CERAN

Vazões em m³/s. A variação corresponde à defluência das 14h menos a das 13h.

| Usina | Observação BRT | Afluência | Defluência | Variação em 1h |
|---|---|---:|---:|---:|
| Castro Alves | 21/09/2026 14:00:00 | 3168.63 | 2828.10 | +251.25 |
| Monte Claro | 21/09/2026 14:00:00 | 4958.05 | 4641.38 | +829.34 |
| 14 de Julho | 21/09/2026 14:00:00 | 3784.96 | 3962.18 | -250.49 |

Fontes diretas: [Castro Alves](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php), [Monte Claro](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHMC.php), [14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php). Esses valores coincidem com os usados na última previsão de 12h. A maior vazão em Monte Claro é relevante para a evolução posterior a jusante, mas não se traduz em chegada instantânea ou soma simples na 14 de Julho.

## Outras usinas

A base ANA já contém estações associadas a Criúva, da Ilha, Caçador, Boa Fé, São Paulo, Autódromo, Linha Emília, Jardim, Pezzi, Serra dos Cavalinhos e outras. No modelo de 12h atual, sua chuva entra, mas seus níveis/vazões não foram todos usados diretamente como preditores nem equivalem a séries de manobras operacionais.

Exemplos conferidos na coleta ANA das 14h20: Boa Fé (86493000), vazão 243,80 m³/s às 13h; São Paulo (86495500), 341,55 m³/s às 13h; Autódromo jusante (86504900), 603,11 m³/s às 13h; Criúva (86200900), 833,57 m³/s às 12h. São valores do campo VazaoFinal da estação, com controle de qualidade aceito, e não necessariamente a defluência operacional publicada pela usina. Não devem ser somados entre barramentos da mesma cascata. Caçador e Linha Emília não tinham vazão válida no recorte de hoje consultado.

A [Hidrotérmica](https://www.ht-hidrotermica.com.br/pchs/) confirma empreendimentos nos rios Carreiro (Boa Fé, São Paulo e Autódromo), da Prata (Jararaca e da Ilha) e Lajeado Grande (Criúva e Palanquinho). O site consultado não apresentou uma tabela horária operacional equivalente à CERAN. Não foram enviadas solicitações por formulário ou e-mail.

## Evidências

- `auditoria-estacoes-sigma.csv`: 100 códigos, redes, horários, atraso e indicação explícita do uso no modelo de 12h.
- `auditoria-estacoes-ana-usinas.csv`: 27 códigos ANA, variáveis disponíveis e uso direto. `nivel_valor` está em centímetros como recebido da ANA; referências verticais variam entre estações.
- `usinas-ceran.csv`: valores operacionais e variação horária das três usinas.
- `raw/manifest.json`: URLs públicas, horários de coleta, tamanho e SHA256; arquivos brutos preservados.

**Conclusão:** os dados SIGMA estão sendo coletados, mas a integração de todas essas séries na previsão de 12h ainda não foi validada. A presença no inventário não deve ser apresentada como inclusão no modelo. A consulta adicional não elimina a incerteza da previsão já entregue.
