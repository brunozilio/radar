import csv, hashlib, json
from pathlib import Path

P = Path(__file__).resolve().parent
meta = json.loads((P/'experiment.json').read_text())
rows = list(csv.DictReader((P/'evaluation.csv').open()))
predictions = list(csv.DictReader((P/'predictions.csv').open()))
lookup = {(int(r['nominal_lead_h']), r['family'], r['subset']): r for r in rows}
assert len(predictions) == meta['scheduled_target_pairs']
assert sum(r['status'] == 'paired' for r in predictions) == meta['status_counts']['paired']
for h in range(1, 13):
    for subset in ['all', 'level_ge_7m']:
        a = lookup[h, 'reference', subset]; b = lookup[h, 'julho_levels', subset]
        for field in ['paired_n', 'observed_targets', 'forecast_failures_with_truth', 'coverage']:
            assert a[field] == b[field]
for path, digest in meta['input_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
decision = {'promoted': False, 'goal_achieved': False, 'live_issuance': False,
            'inputs_verified': True, 'paired_targets_verified': True,
            'reason': 'Mixed end-to-end performance.12h improves but shorter leads regress; flood accuracy far below98%. Historical availability unverified and forecast coverage incomplete. Preserve candidate for research, keep live models unchanged.',
            'status_counts': meta['status_counts'],
            'prospective_samples_added': 0, 'independent_flood_events_added': 0,
            'uncertainty': 'No confidence interval or independent-event claim from these overlapping historical forecasts.'}
(P/'decision.json').write_text(json.dumps(decision, ensure_ascii=False, indent=2)+'\n')
lines = ['# Efeito dos níveis dos reservatórios na previsão de Muçum', '',
         'O candidato troca somente a previsão de vazão de14deJulho. Carreiro, parâmetros HGE/ARNO, chuva, roteamento, curva de nível e correção residual são comuns. Não houve ajuste neste experimento nem alteração das emissões horárias.', '',
         '## Resultado comparável', '',
         '| Prazo nominal | Recorte | Pares | Cobertura¹ | MAE referência → candidato (m) | Acertos±0,50m referência → candidato |',
         '|---|---|---:|---:|---:|---:|']
for h in [1, 6, 12]:
    for subset in ['all', 'level_ge_7m']:
        a = lookup[h, 'reference', subset]; b = lookup[h, 'julho_levels', subset]
        lines.append(f"| {h}h | {'Geral' if subset == 'all' else 'Nível≥7m'} | {a['paired_n']} | {100*float(a['coverage']):.1f}% | {float(a['mae_m']):.3f} → {float(b['mae_m']):.3f} | {100*float(a['within_0_50_fraction']):.1f}% → {100*float(b['within_0_50_fraction']):.1f}% |")
lines += ['', '¹Cobertura entre alvos observados: os erros/acertos usam apenas pares calculáveis de ambos os modelos. Falhas e alvos sem medição permanecem registrados. Esses prazos são nominais de hindcast, não antecedências reais de emissões prospectivas.', '',
          'Em12h, o ganho aparece no nível final, mas a taxa de acerto nas cheias continua18,0%, com MAE1,663m. Em6h, o erro geral e a taxa de acerto pioram; mesmo a pequena redução deMAEnas cheias vem acompanhada de menor taxa dentro de±0,50m. Não se selecionou um horizonte favorável para declarar melhoria global.', '',
          '## Cobertura e causalidade do cálculo', '',
          f"Foram examinadas{meta['origin_count']}origens e{meta['scheduled_target_pairs']}alvos nominais anteriores a21/09. Estados: "+', '.join(f'{k}={v}' for k, v in meta['status_counts'].items())+'.', '',
          'As vazões são inferidas em todas as origens, sem exigir observação futura de vazão. Os modelos congelados pré-julho reproduziram os valores da avaliação anterior; dados ausentes no alvo deMuçum são registrados, não interpolados. Cada âncora exige H/Q exatos em origem−15min. Estado de chuva observada termina em origem−1h; origem e futuro usam previsões meteorológicas arquivadas, nunca chuva futura observada. Os dois modelos recebem a mesma correção inicial.', '',
          'A inferência usa os valores históricos finais disponíveis no acervo. Os atrasos de15min/60min e a disponibilidade dos arquivos previous_day1 não foram comprovados por recibos históricos. A comparação é de desenvolvimento, com períodos já examinados, e não demonstra o desempenho prospectivo do runner atual nem certifica dados históricos. A âncora é uma hipótese fixa, não observação de latência passada.', '',
          '## Decisão', '',
          'Não promover. O ganho de vazão não se traduz em ganho uniforme do nível. Manter o candidato para investigar erros por fase da cheia, lacunas e sensibilidade às anomalias documentadas, sem ajustar diretamente nos eventos usados para medir desempenho. A meta98%permanece não atingida; zero exemplos prospectivos ou cheias independentes foram adicionados ao placar por este experimento.', '',
          f"Preservados protocolo, código, hashes e todos os pares. Erro máximo na reprodução das vazões congeladas: {meta['upstream_reproduction_max_error_m3_s']:.2e}m³/s. Erro numérico máximo do balanço: {meta['max_numerical_balance_error_mm']:.2e}mm. Esses controles verificam implementação, não precisão hidrológica. Não foi produzido intervalo de confiança a partir dos pares sobrepostos."]
(P/'report.md').write_text('\n'.join(lines)+'\n')
files = [p for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != 'artifact-hashes.json']
(P/'artifact-hashes.json').write_text(json.dumps([{'file': str(p.relative_to(P)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)], indent=2)+'\n')
print(json.dumps(decision, ensure_ascii=False))
