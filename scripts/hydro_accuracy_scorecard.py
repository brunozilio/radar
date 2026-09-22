"""Score saved retrospective predictions without claiming prospective accuracy.

This adapter only reads existing local CSVs. It never trains models, fills missing
truth, or treats the best of multiple models as an operational prediction.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def summarize(rows, tolerance=.5):
    groups = defaultdict(list)
    rejected = defaultdict(int)
    seen = set()
    for r in rows:
        key = (r['model'], r['phase'], float(r['lead_h']))
        identity = (*key, r['origin'], r['target_time'])
        if identity in seen:
            raise ValueError(f'Duplicate forecast pair: {identity}')
        seen.add(identity)
        try:
            pred, truth, base = (float(r[k]) for k in ['forecast_m', 'actual_m', 'base_m'])
        except (ValueError, TypeError):
            rejected[key] += 1
            continue
        if not all(math.isfinite(v) for v in [pred, truth, base]):
            rejected[key] += 1
            continue
        origin = datetime.fromisoformat(r['origin'])
        target = datetime.fromisoformat(r['target_time'])
        if origin.tzinfo is None or target.tzinfo is None:
            raise ValueError('Forecast times require explicit timezone')
        if abs((target-origin).total_seconds()/3600-key[2]) > 1e-6 or key[2] <= 0:
            raise ValueError('Incorrect nominal horizon')
        groups[key].append((pred, truth, base))
    output = []
    for key in sorted(set(groups) | set(rejected)):
        values = np.array(groups[key], dtype=float).reshape(-1, 3)
        for regime in ['all', 'level_ge_7m', 'rising_at_least_015m_per_h', 'falling_at_least_015m_per_h']:
            if regime == 'all':
                keep = np.ones(len(values), dtype=bool)
            elif regime == 'level_ge_7m':
                keep = values[:, 1] >= 7
            elif regime.startswith('rising'):
                keep = (values[:, 1]-values[:, 2])/key[2] >= .15
            else:
                keep = (values[:, 1]-values[:, 2])/key[2] <= -.15
            selected = values[keep]
            error = selected[:, 0]-selected[:, 1]
            absolute = abs(error)
            hits = int(np.sum(absolute <= tolerance))
            n = len(error)
            output.append({'model': key[0], 'phase': key[1], 'lead_h_nominal': key[2],
                           'regime': regime, 'n': n, 'hits': hits,
                           'accuracy_percent': 100*hits/n if n else None,
                           'mae_m': float(absolute.mean()) if n else None,
                           'bias_m': float(error.mean()) if n else None,
                           'p90_abs_m': float(np.quantile(absolute, .90)) if n else None,
                           'p98_abs_m': float(np.quantile(absolute, .98)) if n else None,
                           'max_abs_m': float(absolute.max()) if n else None,
                           'invalid_pairs_in_model_horizon': rejected[key],
                           'goal_prospectively_verified': False})
    return output


def run(source, out):
    with source.open() as f:
        rows = list(csv.DictReader(f))
    result = summarize(rows)
    out.mkdir(parents=True, exist_ok=True)
    with (out/'placar-retrospectivo.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    metadata = {'generated_at': datetime.now(timezone.utc).isoformat(),
                'source': str(source.resolve()), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'tolerance_m': .5, 'target_percent': 98,
                'prospective_evidence': False, 'goal_achieved': False,
                'limitations': [
                    'CSV contains retrospective predictions, not immutable emission records.',
                    'Lead times are nominal: actual historical source availability is not proven.',
                    'The test period has already been examined during development.',
                    'Only rows present in the input are assessed; missing scheduled forecasts cannot be counted from this CSV.',
                    'Rising/falling strata use base-to-target mean change, not instantaneous river slope.',
                    'Consecutive forecasts are dependent; no binomial confidence claim is made.',
                    'Missing/invalid values are not successes; unobserved river regime is unknown.',
                ], 'scorecard': result}
    (out/'placar-retrospectivo.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    current = [r for r in result if r['model']=='arvores_previsao_chuva' and r['phase']=='test' and r['regime'] in ['all','level_ge_7m']]
    table = '\n'.join(f"| {r['lead_h_nominal']:g}h | {r['regime']} | {r['n']} | {r['accuracy_percent']:.1f}% | {r['mae_m']:.2f} |" for r in current if r['n'])
    (out/'placar.md').write_text(f'''# Placar inicial da meta de 98%

Acerto = erro absoluto de até 0,50 m. **Este placar é retrospectivo; não comprova a meta prospectiva.**
Modelo atual: `arvores_previsao_chuva`; período rotulado `test` no arquivo de entrada.

| Antecedência nominal | Recorte | Pares válidos | Acertos até ±0,50 m | MAE (m) |
|---|---|---:|---:|---:|
{table}

O arquivo completo inclui os outros modelos, subida/recessão e as retrospectivas de hoje.
Não agrupar horizontes nem escolher o modelo vencedor por observação. Pares ausentes do
arquivo e fontes historicamente indisponíveis não podem ser auditados a partir deste CSV.
As previsões consecutivas não são amostras independentes.

Próximo requisito: registrar cada emissão real e confrontá-la com a medição posterior.
Não usar o bom desempenho de rio baixo para declarar sucesso em cheias.
''', encoding='utf-8')
    print(json.dumps(current, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args();run(a.source, a.output)
