# Comparação das 22h sem previsão de chuva

Recalculada depois da emissão original, usando exclusivamente o snapshot de 21/09/2026 às 22h. Diagnóstico local; não publicado e não registrado como previsão prospectiva.

Base observada: 16,17 m às 21h30. Retidos níveis e tendências de quatro estações, vazões afluentes/defluentes e tendências de três usinas e chuva já observada em cinco regiões. Excluídas as 60 variáveis de previsão meteorológica; os modelos foram retreinados com 120 variáveis observadas. Não se impôs chuva futura igual a zero.

Mesmo algoritmo, hiperparâmetros, pesos e amostras nos dois lados da comparação. Alvos de treinamento estritamente anteriores a 21/09/2026 às 00h BRT. Controle com previsão de chuva reproduziu exatamente os seis modelos da rodada local das 22h. O site usa artefatos congelados distintos, portanto a diferença isolada da retirada da previsão de chuva deve ser medida contra o controle local, não contra a coluna do site.

| Alvo BRT | Site original (m) | Controle local com previsão (m) | Sem previsão de chuva (m) | Diferença pareada (m) |
|---|---:|---:|---:|---:|
| 21/09 23:00 | 16.856 | 17.138 | 17.199 | +0.061 |
| 22/09 00:00 | 17.639 | 17.688 | 17.869 | +0.181 |
| 22/09 01:00 | 18.000 | 18.156 | 18.155 | -0.001 |
| 22/09 02:00 | 18.266 | 18.337 | 18.410 | +0.073 |
| 22/09 03:00 | 18.195 | 18.077 | 18.085 | +0.008 |
| 22/09 04:00 | 17.943 | 18.103 | 17.914 | -0.190 |

Verificação: hashes dos insumos preservados; seis modelos recarregados com 120 entradas e resultados reproduzidos; controle reproduzido sem divergência. A variante sem previsão meteorológica não recebeu validação independente de precisão. Maior valor entre seis alvos não comprova horário ou magnitude do pico real.
