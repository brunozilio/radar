# Auditoria independente das partições por tendência

Todas as **12.828 verificações passaram**. Recalculadas a partir das previsões congeladas: 4.608 métricas estratificadas, 768 transições de acerto e 96 faixas de resposta do treino. Nenhuma divergência concreta encontrada. Nenhum ajuste, inferência, consulta de rede ou alteração de fonte/modelo foi executado nesta auditoria.

`audit.py` usa somente bibliotecas de leitura/cálculo e a reconstrução independente local de `verify_contract.py`; não importa o diagnóstico nem os geradores operacionais. Conferiu os manifestos do diagnóstico, experimento de idade e experimento misto, as fontes declaradas e sua integridade ao término. As 24 máscaras de treino foram reconstruídas dos cortes e requisitos de admissibilidade; a atribuição PCG64(57), as bases por família e os 96 mínimos/máximos foram reproduzidos. As 204.168 linhas representam duas vistas de 102.084 origens/horizontes, não observações independentes.

## Contrato temporal e índices

- Coluna 2: `86510000:dH1` = diferença de Muçum entre consultas nominais separadas por uma hora, dividida por uma hora.
- Coluna 3: `86510000:dH2` = diferença entre consultas nominais separadas por duas horas, dividida por duas horas.
- Unidade: m/h nominal. Os atrasos de 15 minutos (A) e 30 minutos (B), com validade posterior à consulta de até 15 minutos, são reaplicados a toda a série. O registro mais recente inválido não é contornado para encontrar outro finito.

As 51.648 células das colunas 2/3 nas duas matrizes foram reconstruídas diretamente dos históricos ANA e coincidem exatamente, inclusive NaNs. Para dH1, 9 posições finitas em A e 26 em B usam intervalos reais entre medições de 45 ou 75 minutos. Para dH2, são 11 e 30 posições com 105 ou 135 minutos. O divisor permanece nominal. Esses números contam posições de cada vista; não certificam disponibilidade/publicação histórica nem contam eventos independentes.

Os limiares de tendência incluem as fronteiras: subida ≥0,10 m/h e descida ≤−0,10 m/h; valores estritamente entre elas são estáveis. A resposta futura usa os limites inclusivos ±0,50 m de `truth − base`. Comparações seguem os valores binários preservados, sem arredondamento corretivo. A resposta futura e sua posição na faixa de treino só podem ser rótulos retrospectivos; não são informações disponíveis para escolher uma previsão na origem.

## Denominadores e ausências

Cada uma das três partições recompõe os alvos observados, pares, falhas, acertos, MAE ponderado por pares e viés de `evaluation.csv/full_schedule`. Alvos desconhecidos permanecem desconhecidos; previsões ausentes para alvos conhecidos contam como falhas. As contagens inteiras conferem, e métricas numéricas foram comparadas com tolerância absoluta de 1e−12 (1e−10 nas somas de erros, que usam ordem de redução independente).

No recorte de cheia, `classified_rows` compreende os alvos observados ≥7 m **mais os alvos desconhecidos**. Não é o total de linhas agendadas, e desconhecido não foi tratado como cheia observada. Exemplo test/A/6h: 1.962 linhas agendadas, 260 classificadas no recorte, sendo 237 alvos altos conhecidos e 23 desconhecidos. Validation/A/6h: 6.546 agendadas, 62 classificadas, sendo 28 altas conhecidas e 34 desconhecidas.

## Achados descritivos conferidos

Ao acrescentar idade ao modelo misto, em cheia/test/6h, o saldo de acertos é −5 no perfil A e −7 em B. Pelas tendências conhecidas na origem, A distribui o saldo como 0 em subida, −3 em descida e −2 estável; B como −3, −2 e −2. Há um par com tendência desconhecida em cada vista, sem mudança de acerto. Isso localiza regressões, sem estabelecer sua causa.

Em 12h, não há transições de acerto entre os modelos mistos com e sem idade: ambos mantêm 75/237 em cada perfil. No candidato com idade, perfil A, os 12 pares de cheia acima do máximo de resposta do respectivo treino têm zero acertos, MAE 5,975298 m e máximo 7,792800 m; 198 pares dentro da faixa têm 72 acertos e MAE 0,983290 m. A classificação usa a resposta futura observada, não detecta prospectivamente extrapolação. Estar dentro de um intervalo univariado tampouco demonstra suporte multivariado suficiente.

As faixas, as partições e suas médias não equivalem a uma comparação causal ou a eventos hidrológicos independentes. Os períodos já foram inspecionados; nenhuma escolha por horizonte, promoção ou alegação de meta atingida resulta deste diagnóstico. `largest-errors.csv` teve integridade verificada pelo manifesto, mas seu ranqueamento não foi recalculado, pois ficou fora das três tabelas solicitadas.

## Reprodução

Executar `audit.py` com NumPy no runtime local existente, com `PYTHONDONTWRITEBYTECODE=1`. O script não treina nem carrega modelos. `verify_contract.py` pode ser executado isoladamente para reproduzir somente a conferência dos índices; `audit.py` atualiza a conclusão para incluir as partições completas. `finalize.py` verifica os hashes das fontes e grava o manifesto dos artefatos próprios, excluindo o manifesto de si mesmo. Não executar novamente após eventual congelamento externo sem autorização.
