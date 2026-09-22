"""Fixed residual-decay sensitivity; historical development, never promotion."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TAUS = (6, 2, 12)
FAMILIES = ('reference', 'julho_levels')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def savecsv(path, rows):
    with path.open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run():
    out = ROOT/'outputs/comparacao-correcao-tau-20260921'
    out.mkdir(exist_ok=False)
    sources = {t: ROOT/f'outputs/experimento-correcao-tau-{t}h-20260921/predictions.csv' for t in TAUS}
    hashes = {str(p): sha(p) for p in sources.values()}
    rows = {t: list(csv.DictReader(p.open())) for t, p in sources.items()}
    key = lambda r: (r['origin'], r['target_time'], r['nominal_lead_h'], r['actual_m'], r['anchor_at'])
    assert all(list(map(key, rows[t])) == list(map(key, rows[6])) for t in TAUS)
    array = lambda rs, field: np.array([float(r[field]) if r[field] else np.nan for r in rs])
    actual = array(rows[6], 'actual_m')
    horizon = array(rows[6], 'nominal_lead_h')
    predictions = {(t, f): array(rows[t], f+'_m') for t in TAUS for f in FAMILIES}
    paired = {(t, f): np.isfinite(actual) & np.isfinite(predictions[t, f]) for t in TAUS for f in FAMILIES}
    common = {f: np.logical_and.reduce([paired[t, f] for t in TAUS]) for f in FAMILIES}
    metrics, coverage, transitions = [], [], []
    for h in range(1, 13):
        for subset in ('all', 'level_ge_7m'):
            target = (horizon == h) & np.isfinite(actual) & ((actual >= 7) if subset != 'all' else True)
            for f in FAMILIES:
                for t in TAUS:
                    coverage.append(dict(tau_hours=t, horizon_h=h, subset=subset, family=f,
                                         observed_targets=int(target.sum()), paired_n=int((target & paired[t, f]).sum()),
                                         common_three_n=int((target & common[f]).sum())))
                    for pop, mask in [('individual', paired[t, f]), ('common_three', common[f])]:
                        selected = target & mask
                        error = predictions[t, f][selected]-actual[selected]
                        ae = abs(error)
                        metrics.append(dict(tau_hours=t, horizon_h=h, subset=subset, family=f, population=pop,
                                            n=len(ae), hits=int((ae <= .5).sum()),
                                            hit_fraction=float((ae <= .5).mean()) if len(ae) else None,
                                            mae_m=float(ae.mean()) if len(ae) else None,
                                            rmse_m=float(np.sqrt(np.mean(error**2))) if len(ae) else None,
                                            bias_m=float(error.mean()) if len(ae) else None,
                                            p90_abs_m=float(np.quantile(ae, .9)) if len(ae) else None,
                                            p98_abs_m=float(np.quantile(ae, .98)) if len(ae) else None,
                                            max_abs_m=float(ae.max()) if len(ae) else None))
                select = target & common[f]
                old = abs(predictions[6, f][select]-actual[select]) <= .5
                for t in (2, 12):
                    new = abs(predictions[t, f][select]-actual[select]) <= .5
                    transitions.append(dict(tau_hours=t, horizon_h=h, subset=subset, family=f,
                                            n=int(select.sum()), lost_hits=int((old & ~new).sum()),
                                            gained_hits=int((~old & new).sum())))
    savecsv(out/'metrics.csv', metrics)
    savecsv(out/'coverage.csv', coverage)
    savecsv(out/'hit-transitions.csv', transitions)
    # Recombine independent full-routing/state replay components, without
    # inverting baseline forecast levels or using the candidate's components.
    replay_path = ROOT/'outputs/verificacao-integral-chuva-mucum-20260921/recomputed-levels.csv'
    rating_path = ROOT/'outputs/mucum-atualizacao-15h-2026-09-21/conferencia-balanco.json'
    hashes[str(replay_path)] = sha(replay_path)
    hashes[str(rating_path)] = sha(rating_path)
    balance = json.loads(rating_path.read_text())
    rating = balance['rating_parameters']
    checks = []
    for t in TAUS:
        indexed = {(r['origin'], r['target_time']): r for r in rows[t]}
        for r in csv.DictReader(replay_path.open()):
            q = sum(float(r[k]) for k in ('julho77_routed_m3_s', 'carreiro_routed_m3_s', 'local_q_m3_s'))
            q += float(r['residual_anchor_m3_s'])*np.exp(-(int(r['nominal_lead_h'])+.25)/t)
            expected = rating[0]*(q/1000)**rating[1]+rating[2]+float(r['anchor_offset_m'])
            saved = float(indexed[r['origin'], r['target_time']]['julho_levels_m'])
            assert q >= 0 and abs(expected-saved) < 1e-10
            checks.append(dict(tau_hours=t, origin=r['origin'], target_time=r['target_time'],
                               recomputed_m=expected, saved_m=saved, abs_difference_m=abs(expected-saved)))
    savecsv(out/'independent-component-recombination.csv', checks)
    decision = dict(input_sha256=hashes, scheduled_rows=len(rows[6]),
                    paired_by_tau_family={f'{t}:{f}': int(paired[t, f].sum()) for t in TAUS for f in FAMILIES},
                    independent_component_checks=len(checks),
                    component_max_error_m=max(r['abs_difference_m'] for r in checks),
                    promoted=False, goal_achieved=False, historical_availability_verified=False,
                    limitations=['Previously inspected historical development; no independent selection validation.',
                                 'Same 15-minute anchor and all other parameters; no tau selection per horizon.',
                                 'Residual correction is statistical, not a physical water-balance flux.',
                                 'Independent component check reuses prior full replay of six origins; not a fresh simulation of every origin.',
                                 'Overlapping targets are not independent flood events.'])
    (out/'decision.json').write_text(json.dumps(decision, indent=2)+'\n')
    lines = ['# Sensibilidade à duração da correção residual', '',
             'Constantes fixas de 2, 6 e 12 horas, âncora de 15 minutos. A referência operacional permanece em 6 horas.', '',
             'Desenvolvimento histórico já inspecionado; nenhum candidato foi promovido.', '',
             '|Prazo|Recorte|Tau (h)|N|Acertos ≤0,50 m|MAE (m)|Máximo (m)|',
             '|---|---|---|---|---|---|---|']
    for h in (1, 6, 12):
        for subset in ('all', 'level_ge_7m'):
            for t in TAUS:
                r = next(x for x in metrics if (x['horizon_h'], x['subset'], x['tau_hours'], x['family'], x['population']) == (h, subset, t, 'julho_levels', 'common_three'))
                lines.append(f"|{h}|{subset}|{t}|{r['n']}|{r['hits']} ({100*r['hit_fraction']:.2f}%)|{r['mae_m']:.4f}|{r['max_abs_m']:.4f}|")
    lines += ['', 'metrics.csv contém os dois modelos, todos os prazos e amostras individuais/comuns. Falhas e cobertura permanecem explícitas.', '',
              'A verificação independente recompõe 216 níveis com componentes de seis origens previamente recalculados integralmente. Não reutiliza a inversão dos níveis previstos.', '',
              'A correção estatística pode compensar erros de entrada, propagação e estado. Seu decaimento não identifica a causa física do erro. A conservação numérica do HGE não transforma essa correção em um fluxo físico.', '',
              'Sem validação temporal independente para selecionar a duração, os resultados não justificam mudar a emissão operacional nem comprovar 98% prospectivos.', '']
    (out/'report.md').write_text('\n'.join(lines))
    (out/'analysis-code.py').write_bytes(Path(__file__).read_bytes())
    for name, digest in hashes.items():
        assert sha(Path(name)) == digest
    manifest = [{'file': str(p.relative_to(out)), 'sha256': sha(p)} for p in sorted(out.rglob('*')) if p.is_file()]
    (out/'artifact-hashes.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(decision, indent=2))


if __name__ == '__main__':
    run()
