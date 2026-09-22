# Muçum: avaliação hidrológica de 21/09/2026

Elaborado em 21/09/2026 • 13:05 BRT. Resultado: **não há previsão numérica validada para divulgar à população a partir desta análise**. Os cálculos foram feitos e testados; o teste mostrou subestimação importante no próprio evento de hoje.

## Resultado que pode ser comunicado como observação

- Régua SGB 86510000: **7,20 m às 12:15 BRT**. A leitura é relativa à régua, não à profundidade nas ruas.
- 14 de Julho: vazão de saída **3016,20 m³/s às 12:00**, comparada a 512,86 m³/s às 10h. Não se somam as três usinas em série: isso contaria novamente a mesma água.
- Arquivo para compartilhar como situação observada: [mucum-observado.png](mucum-observado.png). Ele não assegura ausência de inundação. Siga orientações da Defesa Civil e os boletins do SACE/SGB.

## Consulta real à produção da Cloudflare

Banco D1 `sofik-monitoramento-push`, configurado em `wrangler.jsonc`, consultado com Wrangler remoto. Apenas SELECTs das tabelas hidrológicas. Respostas confirmam `rows_written=0` e `changed_db=false`. Nenhuma implantação, alerta ou mensagem externa foi realizada.

Foram extraídos 132 registros CERAN das três usinas, 861 registros SACE sem o prefixo duplicado `sace-`, e 2286 registros de chuva de 29 códigos. Há aproximadamente 45 horas de histórico nesse recorte da produção; não foi encontrado histórico contínuo longo das usinas nessas tabelas. SQL, horário, hashes e respostas estão em `raw/producao/`.

Das 29 estações de chuva do banco, 27 ficam dentro da bacia da régua: cinco já constavam no SIGMA e 22 são adicionais. Capigui e Linha Colombo ficam fora. O campo genérico de qualidade no banco não comprova a aprovação individual da chuva: o parser local aceita aprovação de nível OU de chuva.

## Cobertura dos pluviômetros

O HAR revelou os endpoints públicos de catálogos e históricos. Foram consultadas as redes identificadas ali e cruzadas as coordenadas com a drenagem ANA BHO2017 5K, seguindo a conectividade dos rios até o trecho 125779: 367 trechos, aproximadamente 16.047 km². O polígono inclui a microbacia inteira do trecho de saída (12,828 km²), sem corte topográfico exato na régua.

Inventário: **122 códigos** (100 SIGMA + 22 adicionais no D1). Isso não prova que todos os pluviômetros existentes foram encontrados, nem que instrumentos próximos sejam independentes. Dos 100 do SIGMA, 69 de redes públicas alimentaram a análise espacial de chuva; 31 de redes particulares ficaram como contexto. As 22 adições do D1 foram auditadas com suas séries curtas, sem criar um histórico artificial para treinamento.

Foram abrangidos Alto Antas, Tainhas, Prata/Turvo, Carreiro e Baixo Antas. O Guaporé desemboca **depois da régua SGB de Muçum**, portanto não se soma sua chuva como contribuição direta a essa régua. Isso não exclui inundação ou remanso na parte do município junto ao Guaporé. Ver [mapa](mapa-estacoes.png) e [inventário completo](inventario-completo-122.csv).

Chuva foi ponderada espacialmente por proximidade em malha de 2 km, recortada por sub-bacia; não somada entre estações. Cobertura de pesos com observações na última hora analisada: 88,8%. Valores negativos, ausência, reinícios de acumulado e divergência extrema de vizinhos foram tratados explicitamente. A semântica dos campos SIGMA ainda depende de confirmação documental; a chuva é uma análise provisória, não uma medição areal homologada.

## Cálculo e teste da projeção

Séries desde 25/07/2026 de Muçum, Linha José Júlio, Santa Tereza e Passo Carreiro. Níveis de réguas distintas permaneceram separados; não foram misturados com altitude absoluta DCRS. Fonte direta SACE tem prioridade sobre o espelho SIGMA. A maior diferença em horários coincidentes na conferência foi 0,07 m.

Regressão regularizada, um modelo para cada horizonte de 1 a 6 horas, usando níveis e variações de 1/2/3/6 horas. Foram comparados modelo local, modelo com montante, montante com chuva disponível, persistência e tendência de 2h. Treino até 25/08; escolha de hiperparâmetros em 26/08–07/09; teste separado em 08/09–21/09. Alvos que atravessam a fronteira de treino/validação foram excluídos. Entradas usam somente observações passadas; intervalos sem leitura não viram chuva zero.

Somente os atributos de chuva de Tainhas tinham disponibilidade histórica suficiente para entrar no candidato com chuva. Esse candidato não ganhou na validação. **Logo, os números abaixo não são o resultado de um modelo calibrado com os 122 pluviômetros e todas as barragens.** Eles usam o modelo selecionado com níveis a montante. As outras chuvas e as usinas serviram para avaliar por que esse resultado não é confiável no evento atual.

No horizonte de 6h: 319 origens de teste, erro absoluto médio 0,18 m; 34 origens já em subida ≥0,2 m/h, erro médio 0,22 m. Essas origens se sobrepõem e não são eventos independentes. **O maior erro foi 3,35 m:** previsão emitida com dados das 06h de hoje teria indicado 3,73 m às 12h, diante de 7,08 m observados. Um erro médio pequeno em períodos estáveis escondeu essa falha no início da subida.

O teste independente só observou níveis até 7,08 m; não validou as cotas projetadas para esta tarde nem uma cheia extrema. O conjunto completo chegou a 15,31 m, porém esses maiores níveis estão no treino. Vários acumulados atuais de chuva superam os máximos do treino. Não há curva de propagação atual calibrada para as vazões CERAN, nem chuva futura incorporada. Coeficientes de estudos antigos não foram transferidos automaticamente para a situação de 2026.

## Saída experimental — não divulgar como previsão de cheia

Base do cálculo: **21/09/2026 12:00 BRT**. A janela abaixo é relativa a essa base; não se deve deslocá-la para seis horas depois do momento em que o arquivo for aberto.

| Horário BRT | Saída do modelo não validado |
|---|---:|
| 13:00 | 7,6 m |
| 14:00 | 8,1 m |
| 15:00 | 8,2 m |
| 16:00 | 8,4 m |
| 17:00 | 8,8 m |
| 18:00 | 9,4 m |

Os valores são arredondados a 0,1 m para evitar falsa precisão; ainda assim, podem errar por metros. Não são limite superior e não têm intervalo de confiança validado. O candidato com chuva indicou 10,4 m às 18h e a extrapolação de tendência 10,9 m, mas a divergência entre métodos também não delimita a faixa possível. [Gráfico técnico](mucum-simulacao-nao-validada.png), [cálculos completos](previsoes-experimentais.csv), [testes](avaliacao-modelos.csv).

Para uma previsão pública defensável falta validação hidrológica operacional: histórico consistente de vazões/níveis em eventos comparáveis, curvas atuais de descarga e propagação, precipitação observada com metadados e previsão de chuva, e revisão do SGB/Defesa Civil. Mais sensores, isoladamente, não resolvem esses pontos.

## Fontes e reprodução

- [SACE Taquari](https://sace.sgb.gov.br/taquari/) e [CSV direto de Muçum](https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv).
- [SGB — descrição do sistema](https://www.sgb.gov.br/sace/taquari_apresentacao.php): informa aproximadamente quatro horas para Muçum. Seis horas desta análise não equivalem ao produto operacional.
- [SGB — estudo da estação Muçum](https://rigeo.sgb.gov.br/bitstreams/665b8bfa-d4fe-4cca-8720-694fdc7964d2/download), posição antes da confluência do Guaporé.
- [SGB — inundação em Muçum e Encantado](https://rigeo.sgb.gov.br/bitstream/doc/24993/2/estudo_preliminar_areas_inundadas_encantado_mucum_cheias_2023_2024_poster.pdf), influência local do Guaporé.
- [ANA BHO2017, drenagem](https://portal1.snirh.gov.br/arcgis/rest/services/SPR/BHO2017_5K_TRECHODRENAGEM/MapServer/0) e [áreas](https://portal1.snirh.gov.br/arcgis/rest/services/SPR/BHO2017_5K_AREADRENAGEM/MapServer/0).
- [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php), [Monte Claro](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHMC.php), [Castro Alves](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php).
- Endpoints SIGMA e arquivos brutos estão nos manifestos em `raw/`. Credenciais do HAR não foram copiadas.

Scripts locais: `scripts/hydro_production_read.py`, `hydro_production_assess.py`, `hydro_model.py`, `hydro_deliver.py`. Dependências usadas: numpy/scipy, shapely/pyproj e matplotlib. Os scripts de coleta fazem GETs públicos; o script de produção faz SELECTs remotos. Não executar automaticamente como sistema de alerta.

**Substitui a extrapolação inicial em `outputs/mucum-2026-09-21/`, que não incorporava esta avaliação da bacia e não deve ser divulgada como previsão confiável.**
