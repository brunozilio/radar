# Auditoria da exposição à ausência de Carreiro

**2.865 verificações passaram**, sem divergência concreta. Os 24 modelos novos foram reaplicados aos dois perfis originais (48 aplicações), e os 72 modelos de controle foram reaplicados nos dois perfis (144 aplicações). Todas as previsões coincidiram exatamente, inclusive ausências. As 1.152 métricas foram recalculadas; as 864 métricas dos controles permanecem idênticas ao pai. A conferência suplementar de seis contrastes por disponibilidade real também passou (12 grupos de métricas).

## Seleção, treino e avaliação

O protocolo preservado tem SHA-256 `5360df29a1c77e5b4bf69a21f56dddf2530428e928c299f7d69b444b8caf4aeb`. Os horários locais registrados de protocolo, pré-fit e conclusão estão ordenados. Conferidos o manifesto de seleção anterior ao ajuste, o código executado, runtime e hashes de fontes/modelos, antes e depois da auditoria.

Reproduzido exatamente `Generator(PCG64(58)).random(12912) < 0.25`: **3.274 das 12.912 origens** selecionadas. A mesma seleção global antecede os recortes de treino de cada fase/horizonte; não usa nível, alvo, erro ou perfil. A escolha de perfil por PCG64(57) também foi reproduzida.

Reconstruí a cópia de treino modificada e as 24 máscaras originais. Somente as colunas 18–23 das linhas selecionadas recebem NaN; demais campos e linhas não selecionadas são iguais. O bloco corresponde ao nível de Passo Carreiro e suas cinco tendências nominais, não a vazão ou precipitação. Nas linhas admitidas ao treino, originalmente completas24, há exatamente seis novas ausências por origem selecionada. Ordem, uma linha por origem, bases, alvos, respostas, pesos originais, cortes temporais exclusivos, configuração HGB e 180 campos foram preservados. `training-reconstruction.csv` contém as contagens por fase/horizonte e hashes das amostras reconstruídas.

A avaliação usa os arrays originais A/B, sem aplicar a máscara artificial. A reaplicação independente sobre esses arrays reproduz exatamente as previsões salvas. Foram preservadas as 204.168 linhas, incluindo todos os campos dos controles. São duas vistas das mesmas 102.084 origens/horizontes, não duas amostras hidrológicas independentes.

## Resultado misto

Em cheia/test, contra o modelo misto anterior, o candidato ganha/empata/perde acertos em **6/1/5 horizontes no perfil A** e **2/6/4 no B**. O MAE melhora em 9/12 horizontes A e 10/12 B, mas isso não implica ganho sustentado na taxa de acerto. Na validação, os acertos ganham/empatam/perdem em 5/2/5 A e 3/7/2 B.

| Cheia/test | Acertos misto → candidato | MAE misto → candidato |
|---|---:|---:|
| A, 6h | 170 → 158 / 237 | 0,602111 → 0,598731 m |
| B, 6h | 166 → 153 / 237 | 0,635535 → 0,628828 m |
| A, 12h | 75 → 78 / 237 | 1,328673 → 1,302787 m |
| B, 12h | 75 → 81 / 237 | 1,384912 → 1,362444 m |

Cada grupo alto de test conserva 237 alvos conhecidos, 236 pares e uma falha no denominador observado. Validation conserva 28 alvos/pares. Alvos desconhecidos permanecem separados. Todas as métricas, inclusive `complete24` e `missing24`, foram recalculadas diretamente das previsões, com tolerância absoluta de 10⁻¹² nos campos numéricos.

## Conferência limitada da disponibilidade real

Os seis contrastes solicitados na análise secundária foram reconstruídos dos campos reais 18–23 e das previsões, sem inferência adicional:

| Perfil/horizonte | Bloco real | Acertos misto → candidato / alvos observados |
|---|---|---:|
| A, 6h | completo | 113 → 102 / 140 |
| B, 6h | completo | 109 → 99 / 140 |
| A, 6h | seis ausentes | 42 → 41 / 82 |
| B, 6h | seis ausentes | 42 → 40 / 82 |
| A, 12h | seis ausentes | 14 → 16 / 88 |
| B, 12h | seis ausentes | 15 → 19 / 88 |

Os denominadores acima incluem a falha quando a verdade é conhecida. A melhora localizada de 12h não elimina as regressões de 6h, inclusive com bloco real completo. A tabela é diagnóstico posterior; não autoriza escolher o candidato apenas quando Carreiro estiver ausente. O restante das 1.152 métricas/288 transições da análise secundária não foi reauditado nesta conferência limitada.

## Limites da prova e reprodução

O modelo HGB serializado não comprova sozinho as amostras e os pesos efetivamente consumidos pelo otimizador. A evidência disponível é o plano pré-fit preservado, a reconstrução das entradas/respostas/pesos, o código executado, os hashes, metadados e a reaplicação exata; não foi feito refit. Os horários registrados são locais, sem autenticação independente do início do ajuste.

Ocultar origens aleatórias não reproduz a duração, causas ou dependência temporal das falhas reais, nem cria observações novas. A taxa de 25% e a semente não foram ajustadas por esta auditoria. Os períodos já foram inspecionados como desenvolvimento; o resultado não certifica disponibilidade histórica, datum/fuso, generalização ou meta de 98%. Nenhuma promoção ou alteração operacional foi realizada.

`audit.py` e `check_availability.py` usam somente arquivos locais e não importam código operacional ou de ajuste. Executar no runtime do experimento com `PYTHONDONTWRITEBYTECODE=1`. `finalize.py` verifica fontes e grava o manifesto dos artefatos próprios, excluindo o manifesto de si mesmo. A auditoria anterior de frequência permanece intacta. Não reexecutar após congelamento externo sem autorização.
