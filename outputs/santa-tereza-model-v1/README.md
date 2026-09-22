# Santa Tereza e níveis de Encantado — validação local

- Santa Tereza: régua-alvo 86472600; entrada a montante 86472000, Linha José Júlio.
- Identidades conferidas no GeoJSON público SACE, conservado em `sources/sace-points.json`. Encantado é o ponto 2 do SACE; ANA 86720000. A sigla no GeoJSON do SACE omite um zero, mas nome e coordenadas correspondem à estação ANA.
- Artefatos: `../../model-artifacts/santa-tereza-6h-v1/`, incluindo hashes dos arquivos e insumos de treino.
- Treino em 2025, validação janeiro–junho de 2026, teste julho–20/09/2026; modelo final usa alvos anteriores a 21/09/2026. Cenários repetidos de atraso não são amostras independentes.
- `validation.json`: métricas por horizonte. Todos os horizontes melhoraram a persistência na validação e no teste. Sem validação nas cheias extremas de 2023/2024.
- `runtime-check/result.json`: pacote completo calculou seis horários para as três cidades com as observações disponíveis na rodada das 00h de 22/09. Insumos e modelos da emissão preservados em `audit.tar.gz`.
- `level-collection.json`: coleta real ANA/SACE das seis réguas. Encantado retornou 14,51 m às 23:45 de 21/09, ANA/SNIRH, com 13 pontos na janela de 3h. São dados daquela consulta, não leituras atuais garantidas.
- 40 testes Node e 8 testes Python passaram; lint e build passaram. React Doctor: 49 para 50, com os mesmos três avisos existentes em `app/page.tsx`.
- Encantado: os seis valores da emissão congelada anterior foram reproduzidos sem mudança após generalizar os parâmetros por estação.
- Navegador real: seleção de Santa Tereza por clique e teclado; seis valores exclusivos; foco preservado; Encantado visível nos níveis com fonte, tendência e histórico. Telas de 390px sem transbordamento horizontal da página.
- Prévia isolada: sem worker e sem envio de alertas; banco SQLite preenchido apenas com leituras públicas. A régua Rede RS não foi coletada na prévia.
- Nenhum deploy ou escrita em serviços externos.
