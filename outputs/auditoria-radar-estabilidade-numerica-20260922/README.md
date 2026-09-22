# Auditoria independente — estabilidade numérica RADAR

2374 verificações passaram. Foram auditados 48 modelos novos, preservando máscaras, ordem, pesos reconstruídos e parâmetros dos controles correspondentes. Reprodução exata de 48 controles, 48 aplicações novas no acervo original e 48 no acervo reutilizado; as 48 reaplicações sobre reconstruções normalizadas são idênticas.

Conferidas 102.084 linhas originais, 26.340 linhas de desenvolvimento reutilizado e 1.440 métricas. Ausências de previsão contam contra alvos observados; truth ausente permanece desconhecido.

normalization-effects.csv compara apenas mesma membership antes/depois da normalização. training-reconstruction.csv e NPZ registram os alvos, ordem e pesos reconstruídos; sem novo ajuste.

No fit/tuning, external lookup or operational action in this audit.
Membership/order/targets/weights reconstructed from frozen masks/formula and executed source; fittedmodels do not retain full sample weights. Initial predictions and parameters are identical to paired raw controls.
No separate fit-start event exists: preregistration/prefit record and code order verified, not a global execution-history certificate.
2021/2022 are explicitly reused development after first challenge, never a new independent test.
Numerical reproducibility is not hydrological accuracy; source timestamp/datum/availability limits remain.
No horizon-specific model mixing or promotion.
