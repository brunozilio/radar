"""Compare preregistered anchor-age scenarios on individual and common samples."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DELAYS = (15, 30, 45)
FAMILIES = ('reference', 'julho_levels')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def savecsv(path, rows):
    with path.open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run():
    out = ROOT/'outputs/comparacao-idade-ancora-20260921'
    out.mkdir(exist_ok=False)
    sources = {d: ROOT/f'outputs/experimento-idade-ancora-{d}min-20260921/predictions.csv' for d in DELAYS}
    hashes = {str(p): sha(p) for p in sources.values()}
    rows = {d: list(csv.DictReader(p.open())) for d, p in sources.items()}
    keys = lambda rs: [(r['origin'], r['target_time'], r['nominal_lead_h'], r['actual_m']) for r in rs]
    for d in DELAYS:
        if keys(rows[d]) != keys(rows[15]):
            raise ValueError('Changed target population')
    n = len(rows[15]); base = rows[15]
    paired = {d: np.array([r['status'] == 'paired' for r in rows[d]]) for d in DELAYS}
    common = np.logical_and.reduce([paired[d] for d in DELAYS])
    actual = np.array([float(r['actual_m']) if r['actual_m'] else np.nan for r in base])
    horizon = np.array([int(r['nominal_lead_h']) for r in base])
    predictions = {(d, f): np.array([float(r[f+'_m']) if r[f+'_m'] else np.nan for r in rows[d]])
                   for d in DELAYS for f in FAMILIES}
    metrics = []; transitions = []; coverage = []
    for h in range(1, 13):
        for high in (False, True):
            target = (horizon == h) & np.isfinite(actual) & ((actual >= 7) if high else True)
            label = 'level_ge_7m' if high else 'all'
            for d in DELAYS:
                selected = target & paired[d]
                coverage.append({'delay_minutes': d, 'horizon_h': h, 'subset': label,
                                 'observed_targets': int(target.sum()), 'paired_n': int(selected.sum()),
                                 'common_three_n': int((target & common).sum()),
                                 'lost_vs_15_n': int((target & paired[15] & ~paired[d]).sum()),
                                 'recovered_vs_15_n': int((target & ~paired[15] & paired[d]).sum())})
                for population, pairmask in [('individual', paired[d]), ('common_three', common)]:
                    select = target & pairmask
                    for f in FAMILIES:
                        error = predictions[d, f][select]-actual[select]; ae = abs(error)
                        metrics.append({'delay_minutes': d, 'horizon_h': h, 'subset': label,
                                        'population': population, 'family': f, 'n': len(error),
                                        'hits': int((ae <= .5).sum()),
                                        'hit_fraction': float((ae <= .5).mean()) if len(ae) else None,
                                        'mae_m': float(ae.mean()) if len(ae) else None,
                                        'bias_m': float(error.mean()) if len(ae) else None,
                                        'p90_abs_m': float(np.quantile(ae, .9)) if len(ae) else None,
                                        'p98_abs_m': float(np.quantile(ae, .98)) if len(ae) else None,
                                        'max_abs_m': float(ae.max()) if len(ae) else None})
            select = target & common
            for d in (30, 45):
                for f in FAMILIES:
                    old = abs(predictions[15, f][select]-actual[select]) <= .5
                    new = abs(predictions[d, f][select]-actual[select]) <= .5
                    transitions.append({'delay_minutes': d, 'horizon_h': h, 'subset': label,
                                        'family': f, 'common_n': int(select.sum()),
                                        'lost_hits': int((old & ~new).sum()), 'gained_hits': int((~old & new).sum())})
    savecsv(out/'metrics.csv', metrics); savecsv(out/'coverage.csv', coverage)
    savecsv(out/'hit-transitions.csv', transitions)
    decision = {'input_sha256': hashes, 'origin_target_rows_per_scenario': n,
                'paired_n': {d: int(paired[d].sum()) for d in DELAYS}, 'common_three_n': int(common.sum()),
                'interpretation': 'Sensitivity to anchor age only, not a new predictive model or optimization over available readings.',
                'historical_availability_verified': False, 'promoted': False, 'goal_achieved': False,
                'limitations': ['Latest revised historical measurements; no as-of publication timestamps.',
                                'Other source delays, weather predictors, models and hyperparameters remain fixed.',
                                'Previously inspected development periods; neither independent test nor prospective evidence.',
                                'A longer anchor delay must never be chosen retrospectively for better scores.',
                                'Source observations and model failures remain preserved.']}
    (out/'decision.json').write_text(json.dumps(decision, indent=2)+'\n')
    lines = ['# Sensibilidade à idade da leitura de Muçum', '',
             'Comparação histórica de 15, 30 e 45 minutos. Não houve promoção ou ajuste de parâmetros.', '',
             f'Cada cenário preserva {n} pares origem/alvo. Amostra comum aos três: {int(common.sum())}.', '',
             '## Julho com níveis de reservatório — amostra comum', '',
             '|Prazo|Recorte|Idade (min)|N|Acertos ≤0,50 m|MAE (m)|Máximo (m)|',
             '|---|---|---|---|---|---|---|']
    for h in (1, 6, 12):
        for subset in ('all', 'level_ge_7m'):
            for d in DELAYS:
                r = next(x for x in metrics if x['horizon_h'] == h and x['subset'] == subset and
                         x['delay_minutes'] == d and x['family'] == 'julho_levels' and x['population'] == 'common_three')
                lines.append(f"|{h} h|{subset}|{d}|{r['n']}|{r['hits']} ({100*r['hit_fraction']:.2f}%)|{r['mae_m']:.4f}|{r['max_abs_m']:.4f}|")
    lines += ['', 'As métricas completas dos dois modelos e de todos os prazos estão em metrics.csv; cobertura e transições são separadas.', '',
              'Amostras individuais podem mudar por lacunas da âncora. A interseção reduz esse efeito na comparação de erros, mas não elimina o viés de seleção nem certifica disponibilidade histórica.', '',
              'A idade efetivamente disponível deve determinar a leitura operacional. Escolher retroativamente o atraso de melhor resultado seria seleção de cenário, não ganho demonstrado.', '',
              'Os demais atrasos e as previsões meteorológicas ficam fixos. Dados revistos não reproduzem o histórico de publicação. Estes resultados não comprovam a meta prospectiva de 98%.', '']
    (out/'report.md').write_text('\n'.join(lines))
    (out/'analysis-code.py').write_bytes(Path(__file__).read_bytes())
    for p, digest in hashes.items():
        if sha(Path(p)) != digest: raise ValueError('Source changed during comparison')
    manifest = [{'file': str(p.relative_to(out)), 'sha256': sha(p)} for p in sorted(out.rglob('*')) if p.is_file()]
    (out/'artifact-hashes.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(decision, indent=2))


if __name__ == '__main__': run()
