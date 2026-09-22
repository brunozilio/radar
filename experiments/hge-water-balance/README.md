# Experimento HGE/ARNO para Muçum

Executa o `simple_water_balance` publicado pelo HGE-IPH com os dados locais de
21/09/2026 às 15h BRT. **Não é o modelo MGB-IPH completo.** O módulo copiado é
preservado byte a byte em `vendor/`; licença, commit e hashes estão junto dele.

O adapter `run.py` (GPL-3.0) usa a rotina original de chuva–vazão compilada por
Numba, sem modificar suas equações. A condição inicial é construída no adapter;
não usamos `generate_ic`. Uma cópia do estado evita que a atualização original
dos reservatórios altere linhas históricas já salvas.

O modelo trata a área incremental entre 14 de Julho / Passo Carreiro e Muçum.
Reutiliza a propagação a montante e a curva vazão–nível já calibradas. Substitui
a resposta linear da chuva local e a vazão de base por solo, aquífero e três
reservatórios conceituais. Esses reservatórios não representam usinas reais.

Requer Python 3.12 e as dependências de `requirements.txt`:

```sh
python3.12 -m venv /tmp/radar-hge-venv
/tmp/radar-hge-venv/bin/python -m pip install -r experiments/hge-water-balance/requirements.txt
/tmp/radar-hge-venv/bin/python -m unittest discover -s experiments/hge-water-balance -p 'test_*.py'
/tmp/radar-hge-venv/bin/python experiments/hge-water-balance/run.py
```

O programa usa apenas os arquivos locais, sem rede, produção ou notificações.
Saídas: `outputs/mucum-hge-experimental-2026-09-21/`.

Calibração: seis parâmetros efetivos, com dados anteriores a 01/07/2026 e 60 dias
iniciais excluídos. Os kernels de propagação existentes também foram ajustados
antes de julho. O teste de julho a 20/09 usa chuva/vazões observadas e é uma
**reconstrução**, não um teste de previsões emitidas com antecedência.

PET de 1/3/5 mm/dia é hipótese constante, não observação. Estado inicial e três
reservatórios são hipóteses estruturais. Parâmetros podem absorver erros da chuva,
propagação e curva-chave. A previsão usa as vazões futuras já estimadas no Radar
e chuva pontual dos arquivos meteorológicos salvos; ainda não testa todo o ganho
prospectivo do novo componente. A faixa de cenários não é intervalo de confiança.

O relatório gerado distingue esses limites. Não altera o produto existente.

## Candidato com ET0 variável

`--pet-series caminho.json --output outputs/pasta-candidata` aceita ET0 horária
do Open-Meteo/ERA5, em UTC e mm por hora. A série é alinhada ao instante final de
cada intervalo e usada como aproximação da PET. Não é evapotranspiração observada.
Horas sem reanálise e o futuro preservam as hipóteses de 1/3/5 mm/dia, explicitadas
no resultado. O código original em `vendor/` continua intacto; só o adapter muda
a entrada PET por passo. Todo candidato deve usar uma pasta nova e ser comparado
com a referência no mesmo recorte, sem promoção automática por um único teste.

Fonte: https://github.com/HGE-IPH/simple_water_balance
