# Auditoria pré-ajuste — normalização numérica RADAR

Gate fixo de oito casas: PASSOU. Comparação original versus reconstrução independente, após normalizar, em2021/2022: [{'year': 2021, 'shape': [744, 120], 'normalized_exact_with_NaNs': True, 'nan_masks_exact': True, 'different_finite_cells': 0, 'max_abs_normalized_difference': 0.0}, {'year': 2022, 'shape': [1464, 120], 'normalized_exact_with_NaNs': True, 'nan_masks_exact': True, 'different_finite_cells': 0, 'max_abs_normalized_difference': 0.0}].

A regra altera somente colunas45..119; níveis/QI0..44 permanecem idênticos bit a bit. NaNs, finitude, complete24, base, truth, horários e arquivos de máscaras permanecem iguais. A função retorna cópia e é idempotente. Todos os hashes de entrada foram conferidos novamente ao terminar.

| Matriz | Perturbação máxima | Células finitas alteradas | Nãozero→zero | Divergências Decimal binário/texto |
|---|---:|---:|---:|---:|
| original2025_2026 | 4.99967722778e-09 | 590874 | 0 | 0/0 |
| added2020 | 4.99739982729e-09 | 22231 | 0 | 0/0 |
| original2021 | 4.9970938637e-09 | 32036 | 0 | 0/0 |
| original2022 | 4.99709663926e-09 | 69699 | 0 | 0/0 |
| reconstructed2021 | 4.99709471025e-09 | 32031 | 0 | 0/0 |
| reconstructed2022 | 4.99709607027e-09 | 69665 | 0 | 0/0 |

Declared rule is NumPy binary floating rounding via scaling/nearest-even, not exact decimal arithmetic. Decimal.from_float tests the exact represented binary value; Decimal(str(value)) tests its shortest decimal text. Differences can occur at or near decimal half-way cases because scaling itself rounds. They do not silently replace the fixed NumPy rule.

Complete independent reconstructed matrices exist for2021/2022 only.2020 prior verifier preserved code/results but no reconstructedNPZ;2025/26 lacks a full independent reconstructedNPZ here. Those two originals are audited for invariance/perturbation only.
No precision tuning, models, fitting, prediction, network or changes to frozen inputs.
Rounded values must not be used to recompute admission masks or coverage thresholds.
Passing this numerical gate alone is not forecast accuracy or promotion.
