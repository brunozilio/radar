# Encantado: implementação e validação local

- Estação-alvo ANA/SGB: 86720000. Entrada a montante: Muçum, 86510000.
- Fontes brutas e recibos com URL, data de coleta e SHA-256 em `raw/`.
- Artefatos congelados: `../../model-artifacts/encantado-6h-v1/`.
- Separação cronológica e métricas por horizonte: `validation.json`.
- `live/`: inferência independente com duas consultas recentes da ANA.
- `runtime-check/`: execução real do pacote com o coletado de Muçum das 22h e coleta recente adicional de Encantado. `result.json` contém as duas cidades; `audit.tar.gz` preserva os insumos.
- `desktop.png` e `mobile.png`: painel real servido pelo build de produção local. API retornou seis alvos; troca por clique e teclado manteve os dados separados. Tela de 390px sem transbordamento da página; tabela usa rolagem horizontal.
- 38 testes Node, 6 testes Python, lint e build aprovados. React Doctor permaneceu em 48/100, com os mesmos três avisos existentes em `app/page.tsx`.
- A prévia usa armazenamento local isolado, sem worker de coleta ou envio de alertas. Por isso os demais painéis retornam indisponibilidade nessa prévia.
- Nenhum deploy ou gravação em serviços externos foi realizado.

A avaliação é retrospectiva, com cenários de atraso simulados. Não comprova disponibilidade histórica dos dados, desempenho prospectivo ou desempenho nas cheias de 2023/2024. As previsões permanecem experimentais.
