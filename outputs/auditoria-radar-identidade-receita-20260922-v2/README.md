# Identidade declarada das receitas de previsão

Auditoria somente de emissões regulares Radar, a partir de recibos e blobs selados. Revisões manuais e importações antigas não entram. Sem ajuste, inferência, alteração do registro ou agrupamento retroativo de versões.

| Versão | Emissões regulares | Não verificáveis | Receitas declaradas distintas | Conjuntos Radar distintos | Runtime em todas |
|---|---:|---:|---:|---:|---|
| hourly-live-weather-v1:2c265b53228f8345 | 3 | 0 | 1 | 3 | True |
| hourly-live-weather-v1:5e5d62467a8ec22d | 2 | 0 | 1 | 2 | True |
| hourly-live-weather-v1:6618f3723be5a3b3 | 1 | 1 | 0 | 0 | False |
| hourly-live-weather-v1:fd40fd74e87486e7 | 5 | 0 | 1 | 5 | True |

A assinatura compara hashes dos códigos/requisitos declarados, versões do runtime, corte de treino, estação/referência e parâmetros dos estimadores lidos dos modelos selados. Não inclui os pesos ajustados na identidade da receita: cada conjunto de pesos permanece rastreado separadamente.

- Compares only code, runtime and settings declared/preserved in the packets; not proof of a complete transitive dependency inventory.
- Version2 corrects the initial local audit that classified shared historical state NPZ/JSON as code. Initial output is retained as superseded; it does not prove recipe changes.
- Legacy packets lacking artifact blobs are explicitly unverifiable; current filesystem paths are not substituted. Non-Radar models from former shared packets are never loaded.
- The operational model_version hashes the main runner only. This audit does not change or backdate that identifier.
- Different fitted weights and historical feature matrices are expected from the documented dynamic source-delay policy, despite a fixed label cutoff.
- Static external parameter files are not automatically certified by equality of this recipe signature. Actual estimator parameters are inspected from sealed models.
- Recipe equality is not prediction equality, equivalent data quality, source publication proof, independent validation or 98% accuracy.
