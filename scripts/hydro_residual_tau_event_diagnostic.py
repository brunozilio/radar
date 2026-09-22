"""Reuse fixed historical clusters/trends to audit residual-decay sensitivity."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TAUS = (6, 2, 12)
FAMILIES = ('reference', 'julho_levels')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return list(csv.DictReader(p.open()))


def save(p, rows):
    with p.open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def key(r):
    return (r['origin'], r['target_time'], r['nominal_lead_h'])


def run():
    old = ROOT/'outputs/diagnostico-eventos-proxy-carreiro-20260921'
    protocol = ROOT/'docs/residual-tau-event-diagnostic-protocol.json'
    files = [old/'predictions-with-labels.csv', old/'observed-clusters.json', old/'policy.json', protocol]
    sources = {t: ROOT/f'outputs/experimento-correcao-tau-{t}h-20260921/predictions.csv' for t in TAUS}
    files += list(sources.values())
    hashes = {str(p): sha(p) for p in files}
    manifest = json.loads((old/'artifact-hashes.json').read_text())
    for p in files[:3]:
        expected = manifest[p.name] if isinstance(manifest, dict) else next(r['sha256'] for r in manifest if r['file'] == p.name)
        assert sha(p) == expected
    labels = read(files[0])
    data = {t: read(sources[t]) for t in TAUS}
    assert len(set(map(key, labels))) == len(labels)
    for t in TAUS:
        assert list(map(key, data[t])) == list(map(key, labels))
        for a, b in zip(data[t], labels):
            assert all(a[f] == b[f] for f in ('actual_m', 'anchor_at', 'status'))
            if t == 6:
                assert all(a[f+'_m'] == b[f+'_m'] for f in FAMILIES)
    clusters = json.loads(files[1].read_text())['represented_clusters']
    cluster_ids = [r['event_id'] for r in clusters]
    actual = np.array([float(r['actual_m']) if r['actual_m'] else np.nan for r in labels])
    horizon = np.array([int(r['nominal_lead_h']) for r in labels])
    trend = np.array([r['origin_trend'] for r in labels])
    event = np.array([r['observed_cluster_id'] or 'unassigned' for r in labels])
    high = np.isfinite(actual) & (actual >= 7)
    groups = [('event', name, 'level_ge_7m', high & (event == name)) for name in cluster_ids+['unassigned']]
    groups += [('trend', name, subset, (trend == name) & (high if subset != 'all' else True))
               for name in sorted(set(trend)) for subset in ('all', 'level_ge_7m')]
    results = []
    for t in TAUS:
        for family in FAMILIES:
            pred = np.array([float(r[family+'_m']) if r[family+'_m'] else np.nan for r in data[t]])
            for h in range(1, 13):
                for kind, name, subset, group in groups:
                    mask = group & (horizon == h)
                    observed = mask & np.isfinite(actual)
                    paired = observed & np.isfinite(pred)
                    error = pred[paired]-actual[paired]
                    ae = abs(error)
                    results.append(dict(tau_hours=t, family=family, horizon_h=h, group_kind=kind, group=name,
                                        subset=subset, scheduled_rows=int(mask.sum()), observed_n=int(observed.sum()),
                                        paired_n=len(ae), failures=int((observed & ~np.isfinite(pred)).sum()),
                                        hits=int((ae <= .5).sum()), hit_fraction=float((ae <= .5).mean()) if len(ae) else None,
                                        mae_m=float(ae.mean()) if len(ae) else None,
                                        bias_m=float(error.mean()) if len(ae) else None,
                                        p98_abs_m=float(np.quantile(ae, .98)) if len(ae) else None,
                                        max_abs_m=float(ae.max()) if len(ae) else None))
    equal = []
    for t in TAUS:
        for f in FAMILIES:
            for h in range(1, 13):
                rs = [r for r in results if r['tau_hours'] == t and r['family'] == f and r['horizon_h'] == h
                      and r['group_kind'] == 'event' and r['group'] in cluster_ids and r['paired_n']]
                equal.append(dict(tau_hours=t, family=f, horizon_h=h, represented_clusters=len(rs),
                                  equal_cluster_mae_m=float(np.mean([r['mae_m'] for r in rs])),
                                  equal_cluster_hit_fraction=float(np.mean([r['hit_fraction'] for r in rs]))))
    # Check disjoint cluster totals reproduce the full high-target sample.
    for t in TAUS:
        for f in FAMILIES:
            for h in range(1, 13):
                rs = [r for r in results if r['tau_hours']==t and r['family']==f and r['horizon_h']==h and r['group_kind']=='event']
                assert sum(r['observed_n'] for r in rs) == int((high & (horizon == h)).sum())
                base = [r for r in results if r['tau_hours']==6 and r['family']==f and r['horizon_h']==h and r['group_kind']=='event']
                assert [(r['group'],r['paired_n'],r['failures']) for r in rs] == [(r['group'],r['paired_n'],r['failures']) for r in base]
    out = ROOT/'outputs/diagnostico-correcao-tau-eventos-20260921'
    out.mkdir(exist_ok=False)
    save(out/'group-metrics.csv', results)
    save(out/'equal-cluster-metrics.csv', equal)
    (out/'protocol.json').write_bytes(protocol.read_bytes())
    (out/'clusters.json').write_text(json.dumps(clusters, indent=2)+'\n')
    (out/'analysis-code.py').write_bytes(Path(__file__).read_bytes())
    decision = dict(input_sha256=hashes, rows_each=len(labels), represented_clusters=len(clusters),
                    independent_events_certified=0, metrics_rows=len(results), promoted=False, goal_achieved=False,
                    limitations=['Outcome-based clusters are diagnostics, not runtime selection.',
                                 'Revised historical development, not independent validation.',
                                 'Two of the four clusters have observation gaps; all lack verified gauge/time metadata.',
                                 'Equal cluster weighting does not make the clusters statistically independent.'])
    (out/'decision.json').write_text(json.dumps(decision, indent=2)+'\n')
    lines = ['# Correção residual por evento de cheia', '',
             'Grupos e tendências reutilizados sem alteração. Nenhum parâmetro escolhido por evento ou tendência.', '',
             '|Pico do grupo (UTC)|Prazo|N|Acertos tau6|Acertos tau12|MAE tau6|MAE tau12|',
             '|---|---|---|---|---|---|---|']
    for c in clusters:
        for h in (1, 6, 12):
            rs = {r['tau_hours']: r for r in results if r['family']=='julho_levels' and r['horizon_h']==h
                  and r['group_kind']=='event' and r['group']==c['event_id']}
            a,b=rs[6],rs[12]
            lines.append(f"|{c['peak_at']}|{h}|{a['paired_n']}|{a['hits']}|{b['hits']}|{a['mae_m']:.4f}|{b['mae_m']:.4f}|")
    lines += ['', 'group-metrics.csv contém todos os prazos, dois modelos, três constantes e tendências, incluindo falhas e grupos vazios. equal-cluster-metrics.csv dá peso igual a cada grupo representado.', '',
              'Os grupos permanecem sem certificação de independência; dois têm lacunas. Dados e previsões são históricos de desenvolvimento. Não são evidência prospectiva dos 98%.', '']
    (out/'report.md').write_text('\n'.join(lines))
    for p,digest in hashes.items(): assert sha(Path(p)) == digest
    entries=[dict(file=str(p.relative_to(out)),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()]
    (out/'artifact-hashes.json').write_text(json.dumps(entries,indent=2)+'\n')
    print(json.dumps(decision,indent=2))


if __name__ == '__main__':
    run()
