"""Verify paired targets/reference and summarize the fixed local experiment."""
import csv, hashlib, json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
rows = list(csv.DictReader((P/'evaluation.csv').open()))
oldpath = ROOT/'outputs/experimento-centralizacao-ponderada-20260921/evaluation.csv'
old = {(r['source'], r['lead_h'], r['phase'], r['subset']): r
       for r in csv.DictReader(oldpath.open()) if r['family'] == 'reference_delta'}
max_error = 0.
for r in rows:
    if r['family'] != 'reference': continue
    previous = old[r['source'], r['lead_h'], r['phase'], r['subset']]
    for field in ['n', 'mae_m3_s', 'bias_m3_s', 'p90_absolute_m3_s']:
        max_error = max(max_error, abs(float(r[field])-float(previous[field])))
assert max_error < 1e-8
families = ['reference', 'level_and_slopes', 'slopes_only']
hashes = {family: hashlib.sha256() for family in families}; counts = dict.fromkeys(families, 0)
for row in csv.DictReader((P/'predictions.csv').open()):
    text = '|'.join(row[k] for k in ['source', 'lead_h', 'phase', 'origin', 'target_time', 'actual_m3_s', 'high_flow'])
    hashes[row['family']].update((text+'\n').encode()); counts[row['family']] += 1
assert len({h.hexdigest() for h in hashes.values()}) == 1
aggregate = []; scores = {}
for source in ['julho', 'carreiro']:
    scores[source] = {}
    for family in families:
        score = 0.
        for phase in ['validation', 'test']:
            for subset in ['all', 'high_flow']:
                chosen = [r for r in rows if r['source'] == source and r['family'] == family and r['phase'] == phase and r['subset'] == subset]
                n = sum(int(r['n']) for r in chosen)
                mae = sum(int(r['n'])*float(r['mae_m3_s']) for r in chosen)/n
                bias = sum(int(r['n'])*float(r['bias_m3_s']) for r in chosen)/n
                aggregate.append({'source': source, 'family': family, 'phase': phase, 'subset': subset, 'n': n, 'mae_m3_s': mae, 'bias_m3_s': bias})
                if phase == 'validation':
                    score += (1 if subset == 'all' else .5)*sum(float(r['mae_m3_s']) for r in chosen)/len(chosen)
        scores[source][family] = score
metadata = json.loads((P/'experiment.json').read_text())
for path, digest in metadata['input_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
result = {'aggregate': aggregate, 'validation_mean_horizon_scores': scores,
          'best_by_validation_score': {s: min(v, key=v.get) for s, v in scores.items()},
          'target_pairs_per_family': counts, 'identical_target_pairs': True,
          'target_pair_sha256': hashes['reference'].hexdigest(),
          'baseline_metric_reproduction_max_error': max_error,
          'baseline_comparison_file': str(oldpath), 'baseline_comparison_sha256': hashlib.sha256(oldpath.read_bytes()).hexdigest(),
          'input_hashes_verified': True, 'promoted': False, 'goal_achieved': False,
          'decision': 'July level_and_slopes improves high-flow MAE in all12leads in validation and later development. Carreiro validation high-flow MAE worsens. Preserve candidate for end-to-end Muçum validation; no live replacement and no98%claim.'}
(P/'decision.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
lines = ['# Níveis dos reservatórios como preditores de vazão', '',
         'Comparação local pré-especificada com os mesmos alvos, parâmetros e cortes temporais. Níveis e variações foram acrescentados aos53preditores originais. Não houve conversão para armazenamento, ajuste de volume, máscaras de anomalias ou promoção. A disponibilidade histórica dos níveis usa atraso presumido60min e expiração90min; publicações/revisões passadas não estão verificadas.', '',
         '| Fonte | Família | Validação geral | Validação vazões altas | Desenvolvimento posterior geral | Desenvolvimento posterior vazões altas |',
         '|---|---|---:|---:|---:|---:|']
for s in ['julho', 'carreiro']:
    for f in families:
        a = [r['mae_m3_s'] for r in aggregate if r['source'] == s and r['family'] == f]
        lines.append('| '+s+' | '+f+' | '+' | '.join(f'{v:.2f}' for v in a)+' |')
lines += ['', 'Valores são MAE em m³/s, ponderados pelo número de pares de cada horizonte. Não são erros em metros do nível de Muçum. Vazões altas usam percentil95da fonte antes da validação, não a cota analítica7m de Muçum.', '',
          'Em14deJulho, nível+variações melhora o erro de vazões altas em todas as12antecedências nominais testadas, de0a11h. A média cai285,24→266,58m³/s na validação e437,99→396,03no desenvolvimento posterior. Em11h, o erro ainda é601,77m³/s na validação e687,95no período posterior. Esse ganho não demonstra precisão suficiente do nível final, nem resolve sozinho extrapolações futuras.', '',
          'Carreiro piora no recorte de vazões altas da validação com ambos os grupos adicionais. Seu uso não é justificado por esta comparação, mesmo que uma pontuação agregada beneficie erros de níveis baixos.', '',
          'A auditoria separada encontrou nível jusante de14deJulho168,74m em03/05/2025 às14h, entre68,74e68,75m. Esse valor foi mantido, inclusive sua propagação nas variações e no treinamento. Está documentado em outputs/auditoria-niveis-reservatorios-ceran/. Não se limpou a série após observar resultados favoráveis.', '',
          f'Verificação: {counts["reference"]} pares idênticos por família; referência anterior reproduzida em contagens/MAE/viés/P90 com diferença máxima{max_error:.2e}; todos os hashes de entrada conferidos. Foram preservados144modelos de fase/antecedência/fonte/família, entradas adicionais, rastreio de horários e previsões pareadas.', '',
          'Os períodos de2025–2026 já foram inspecionados em estudos anteriores e continuam sendo desenvolvimento. Próximo passo: avaliar a propagação do candidato até Muçum e sua robustez por eventos, sem reutilizar o evento de avaliação no ajuste. Os modelos horários permanecem intactos; meta98%não comprovada.']
(P/'report.md').write_text('\n'.join(lines)+'\n')
files = [p for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != 'artifact-hashes.json']
(P/'artifact-hashes.json').write_text(json.dumps([{'file': str(p.relative_to(P)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)], indent=2)+'\n')
print(json.dumps({'pairs': counts, 'reference_max_error': max_error, 'validation_scores': scores}))
