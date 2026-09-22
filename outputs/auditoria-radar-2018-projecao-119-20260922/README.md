# Falha local de binning e projeção fixa119

Reprodução mínima confirmou a falha na combinação instalada scikit-learn1.9.1/NumPy2.5.3, sem alterar ambiente. `_find_binning_thresholds` elimina NaNs, obtém zero valores distintos, trata apenas o caso unitário e chama `sliding_window_view(...,2)` sobre array vazio. O resultado é `ValueError: window shape cannot be larger than input array shape`.

Foram executados apenas cálculos de limiar sobre quatro valores sintéticos e `_BinMapper.fit` sobre oito linhas, sem treino deHGB. QuatroNaNs com pesospositivos reproduzem o erro; quatroconstantes finitas retornam limites vazios, e `[1,NaN,2,NaN]` retorna1,5. `_BinMapper`8×2 com uma coluna todaNaN falha; o mesmo exemplo8×1 removendo essa coluna passa. Código instalado/hash/trecho e tracebacks completos ficam em `installed-binning-function.py.txt` e `minimal-reproduction.json`. Não generalizamos o problema para todas as versões.

**363 verificações passaram** sobre os48 conjuntos reais de treino preparados na tentativa120colunas. Em todos eles, o único índice totalmenteNaN/nãofinito é **1, Muçum dH0,5h**. Depois da projeção fixa `[0,2,3,...,119]`, nenhuma outra coluna é inteiramente ausente nesses conjuntos. Máscaras, quantidades, respostas, targets e fórmula de pesospositivos foram conferidos semrefit. Não há modelosjoblib salvos na tentativa120inspecionada; a falha ocorreu antes de qualquer modelo completo.

`48-fitset-missingness.csv` traz a evidência porfase/família/h e `projection-column-map.csv` o mapeamento das119colunas para as120originais. A projeção deve ser idêntica emcontrole/candidato, fit e inferência; não imputar nem escolher colunas por erro. `complete_upstream18` deve continuar sobre **originais6:24**, equivalente a **projetadas5:23**. Usar6:24 apósaprojeção removeria indevidamente o primeiro campoLinha e incluiria um campoQI. A versão119 revisada calcula a máscara nos originais antes deprojetar.

O suplemento `119-prefit-verification.json` conferiu os artefatos estáveis da nova rodada enquanto o coordenador treina: **48máscaras,144vetores**(48respostas+48pesos+48targets) e48planos são exatamente iguais aos da tentativa120. A projeção salva é exatamente a predeterminada. Código/protocolo119 foram lidos/hashados; não se inspecionaram modelos/predições em andamento e nenhum processo foi reiniciado.

Remover a coluna estruturalmente ausente resolve o gatilho local reproduzido, mas não certifica conclusão dos futurosfits ou qualidade de previsão. Não é teste de desempenho nem aprovação de promoção. Preservam-se matrizes120originais e tentativa falhada. Esta auditoria faz somente a confirmação limitada pedida; resultados futuros exigem verificação própria.

`audit.py` e `check_119_prefit.py` são reproduzíveis; manifesto/check final sela esta pasta. Nenhuma fonte, cache, protocolo, modelo, pacote ou operação foi alterado. Meta98% não aferida.
