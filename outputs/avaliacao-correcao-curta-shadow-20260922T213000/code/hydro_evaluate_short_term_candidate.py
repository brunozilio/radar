"""Local-only replay of the fixed shadow recipe against preserved R2/D1 evidence."""
import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import hydro_short_term_candidate as candidate


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'docs/radar-short-term-shadow-protocol.json'
DEFAULT_AUDIT = ROOT / 'outputs/comparacao-producao-20260922T203322'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def epoch(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def metrics(rows):
    available = [r for r in rows if r['shadow_status'] == 'shadow_generated']
    pairs = [r for r in available if r['status'] == 'matched']
    missing = Counter(reason for r in rows if r['shadow_status'] != 'shadow_generated'
                      for reason in r['shadow_reasons'])
    result = dict(total=len(rows), candidate_available=len(available),
                  matched=len(pairs), missing_exact_target=sum(r['status'] != 'matched' for r in rows),
                  excluded_candidate=len(rows) - len(available), exclusion_reasons=dict(missing))
    for label, column in [('baseline', 'forecast_m'), ('shadow', 'shadow_m')]:
        errors = [r[column] - r['observed_m'] for r in pairs]
        result[label] = {
            'mae_m': sum(map(abs, errors)) / len(errors) if errors else None,
            'bias_m': sum(errors) / len(errors) if errors else None,
            'maximum_absolute_error_m': max(map(abs, errors)) if errors else None,
            'within_050m': sum(abs(e) <= .5 for e in errors),
            'within_050m_rate': sum(abs(e) <= .5 for e in errors) / len(errors) if errors else None,
        }
    changed = [abs(r['shadow_m'] - r['observed_m']) - abs(r['forecast_m'] - r['observed_m'])
               for r in pairs]
    result.update(improved=sum(v < -1e-12 for v in changed),
                  worsened=sum(v > 1e-12 for v in changed),
                  unchanged=sum(abs(v) <= 1e-12 for v in changed))
    return result


def evaluate(audit, output):
    if output.exists():
        raise ValueError('Refusing to overwrite a previous evaluation')
    protocol = json.loads(PROTOCOL.read_text())
    if protocol['candidate'] != candidate.VERSION or candidate.FORMULA != {
        'maximumWeight': .5, 'fullWeightUntilRealHours': 1.0,
        'zeroWeightAtRealHours': 3.0, 'maximumAbsoluteCorrectionM': .5,
        'trendLookbackHours': 1.0, 'directionThresholdMPerHour': .05,
    }:
        raise ValueError('Code differs from the registered recipe')
    manifest = json.loads((audit / 'manifest.json').read_text())['files']
    input_names = ['todas-emissoes.json', 'd1-observacoes.json', 'comparacao-antecedencia-real.json']
    for name in input_names:
        if sha(audit / name) != manifest[name]:
            raise ValueError('Frozen input integrity failure: ' + name)
    all_rows = [r for r in json.loads((audit / 'todas-emissoes.json').read_text())
                if r['station'] == 'mucum']
    selected = [r for r in json.loads((audit / 'comparacao-antecedencia-real.json').read_text())
                if r['station'] == 'mucum']
    observations = [r for batch in json.loads((audit / 'd1-observacoes.json').read_text())
                    for r in batch['results'] if r['station'] == '86510000' and r['origin'] == 'river_readings']
    by_issue = defaultdict(list)
    for row in all_rows:
        by_issue[row['generated_at']].append(row)
    source_paths = set()
    for rows in by_issue.values():
        source_paths.add(next(audit / 'r2' / name.replace('/', '__')
                             for name in rows[0]['source_objects'] if '/issues/' in name))
    for path in source_paths:
        relative = str(path.relative_to(audit))
        if sha(path) != manifest[relative]:
            raise ValueError('Frozen R2 issue integrity failure: ' + relative)
    paths = [PROTOCOL, Path(__file__), Path(candidate.__file__), audit / 'manifest.json']
    paths += [audit / name for name in input_names] + sorted(source_paths)
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    output.mkdir(parents=True)
    (output / 'code').mkdir()
    (output / 'protocol.json').write_bytes(PROTOCOL.read_bytes())
    for path in [Path(__file__), Path(candidate.__file__)]:
        (output / 'code' / path.name).write_bytes(path.read_bytes())
    # This immutable registration is written before the first candidate call.
    dump(output / 'pre-evaluation-manifest.json', {
        'registeredAt': datetime.now(timezone.utc).isoformat(), 'inputSha256': frozen,
        'candidateEvaluationStarted': False, 'fittingPlanned': False,
        'independentHoldout': False, 'publicationPlanned': False,
    })
    artifacts, results = [], []
    for generated, rows in sorted(by_issue.items()):
        path = next(audit / 'r2' / name.replace('/', '__') for name in rows[0]['source_objects'] if '/issues/' in name)
        issue = json.loads(path.read_text())
        if issue['generatedAt'] != generated:
            raise ValueError('Issue timestamp mismatch')
        issue_anchor = issue['observation']
        anchor = dict(station='86510000', timestamp=issue_anchor['timestamp'],
                      level=issue_anchor['level'], received_at=generated,
                      quality='legacy_unverified', evidence_id='r2-sha256:' + sha(path))
        # Historical D1 gives created_at, not a versioned receipt. Use only the
        # exact lag-1h row and disclose the explicit diagnostic-only exception.
        past_epoch = epoch(anchor['timestamp']) - 3600
        history = [dict(station='86510000', timestamp=o['timestamp'], level=o['level'],
                        received_at=o['created_at'], quality='legacy_unverified',
                        evidence_id=f'd1-snapshot-sha256:{manifest["d1-observacoes.json"]}:{i}')
                   for i, o in enumerate(observations) if epoch(o['timestamp']) == past_epoch]
        baseline = issue['models'][0]['points']
        shadow = candidate.build_shadow(reference_at=issue['referenceAt'], issued_at=generated,
            anchor=anchor, received_history=history, baseline_points=baseline,
            allow_legacy_unverified=True)
        artifacts.append(shadow)
        shadow_points = {p['timestamp']: p for p in shadow['points']}
        original_points = {p['timestamp']: p for p in baseline}
        for row in rows:
            point = original_points[row['target_at']]
            if point['level'] != row['forecast_m']:
                raise ValueError('Published baseline value differs from preserved issue')
            available_epoch = max(epoch(generated), epoch(row['first_stored_at']))
            operational_lead = (epoch(row['target_at']) - available_epoch) / 3600
            if operational_lead <= 0:
                raise ValueError('Persisted forecast was unavailable before target')
            p = shadow_points.get(row['target_at'])
            result = {**row, 'operational_real_lead_h': operational_lead,
                'real_lead_band': math.floor(operational_lead),
                'shadow_status': shadow['status'], 'shadow_reasons': shadow['reasons'],
                'shadow_m': p['shadowLevel'] if p else None,
                'weight': p['weight'] if p else None,
                'correction_m': p['correctionM'] if p else None,
                'direction_known_at_issue': shadow.get('directionKnownAtIssue', 'unavailable'),
                'input_sha256': shadow['inputSha256'], 'goal_evidence_eligible': False}
            if p and p['realLeadHours'] >= 3 and p['shadowLevel'] != row['forecast_m']:
                raise ValueError('Long lead must remain exactly unchanged')
            results.append(result)
    groups = []
    for lead in range(6):
        for direction in ['all', 'rising', 'falling', 'stable', 'unavailable']:
            group = [r for r in results if r['real_lead_band'] == lead and
                     (direction == 'all' or r['direction_known_at_issue'] == direction)]
            groups.append(dict(real_lead_band=f'[{lead},{lead+1})', direction=direction, **metrics(group)))
    indexed = {(r['generated_at'], r['target_at']): r for r in results}
    selected_results = [{**indexed[(r['generated_at'], r['target_at'])],
                         'minimum_real_lead_h': r['minimum_real_lead_h']} for r in selected]
    selected_metrics = [dict(minimum_real_lead_h=h,
        **metrics([r for r in selected_results if r['minimum_real_lead_h'] == h])) for h in range(1, 7)]
    for relative, digest in frozen.items():
        if sha(ROOT / relative) != digest:
            raise ValueError('Input changed during evaluation: ' + relative)
    dump(output / 'shadow-artifacts.json', artifacts)
    dump(output / 'all-issue-comparisons.json', results)
    dump(output / 'metrics-real-lead-direction.json', groups)
    dump(output / 'same-selected-cases.json', selected_results)
    dump(output / 'same-selected-metrics.json', selected_metrics)
    summary = dict(issues=len(artifacts), issue_targets=len(results),
                   aggregate=metrics(results), selected_cases=metrics(selected_results),
                   status='shadow_only_not_promoted', goal_achieved=False,
                   independent_holdout=False, fitted_models=0, published_forecasts=0,
                   input_sha256=frozen)
    dump(output / 'summary.json', summary)
    lines = ['# Candidato de correção curta: somente avaliação paralela', '',
        'Receita fixa registrada antes desta execução: peso 50% até 1h real, reduzindo linearmente até zero em 3h; correção máxima ±0,50m. Não houve ajuste de coeficientes, treinamento, consulta remota ou publicação. O modelo publicado foi lido exatamente de cada emissão preservada, sem refazer sua inferência.', '',
        f'Foram examinadas {len(artifacts)} emissões e {len(results)} pares emissão/alvo de Muçum. O horário disponível ao usuário é o maior entre emissão e primeiro armazenamento; a fórmula usa a antecedência real desde a emissão. As duas medidas estão preservadas por caso.', '',
        '**Este episódio já foi examinado no desenvolvimento. Não é teste independente.** Os valores antigos de D1 possuem created_at, mas não comprovam versões históricas imutáveis nem QC. A exceção legacy_unverified foi habilitada apenas neste diagnóstico. Nenhum par é elegível para provar a meta de 98%.', '',
        '## Mesmos casos selecionados pela auditoria anterior', '',
        '| Antecedência mínima real | Total | Pares disponíveis | MAE original → shadow (m) | ±0,50m original → shadow | Melhorou / piorou / igual |',
        '|---|---:|---:|---:|---:|---:|']
    def show(metric):
        if not metric['matched']:
            return '—', '—', '—'
        return (f'{metric["baseline"]["mae_m"]:.3f} → {metric["shadow"]["mae_m"]:.3f}',
            f'{metric["baseline"]["within_050m"]} → {metric["shadow"]["within_050m"]}',
            f'{metric["improved"]} / {metric["worsened"]} / {metric["unchanged"]}')
    for group in selected_metrics:
        mae, hits, change = show(group)
        lines.append(f'| ≥{group["minimum_real_lead_h"]}h | {group["total"]} | {group["matched"]} | {mae} | {hits} | {change} |')
    lines += ['', '## Todas as emissões, por antecedência real e direção conhecida', '',
        '| Intervalo real (h) | Direção | Total | Pares disponíveis | MAE original → shadow (m) | ±0,50m original → shadow |',
        '|---|---|---:|---:|---:|---:|']
    for group in groups:
        if group['total']:
            mae, hits, _ = show(group)
            lines.append(f'| {group["real_lead_band"]} | {group["direction"]} | {group["total"]} | {group["matched"]} | {mae} | {hits} |')
    lines += ['', '## Disponibilidade e decisão', '',
        f'Indisponibilidade do candidato: {summary["aggregate"]["excluded_candidate"]}/{len(results)} pares; motivo(s): {json.dumps(summary["aggregate"]["exclusion_reasons"], ensure_ascii=False)}.',
        'Alvos ainda sem leitura exata e candidato indisponível permanecem no denominador total e nos arquivos por caso. As métricas pareadas usam exatamente os mesmos alvos nos dois braços.', '',
        '**Não promover.** Melhora agregada neste episódio não estabelece segurança nas mudanças de direção/pico. Conferir MAE, viés, erro máximo, acertos e cobertura em cada grupo dos JSONs. A partir de 3h desde a emissão, a saída permanece exatamente igual ao modelo publicado. Validar a versão congelada em cheias independentes e prospectivamente, seguindo todos os critérios de protocol.json, antes de qualquer troca.']
    (output / 'README.md').write_text('\n'.join(lines) + '\n')
    dump(output / 'artifact-hashes.json', {str(p.relative_to(output)): sha(p)
        for p in sorted(output.rglob('*')) if p.is_file()})
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_sha256'}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', type=Path, default=DEFAULT_AUDIT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    evaluate(args.audit.resolve(), args.output.resolve())
