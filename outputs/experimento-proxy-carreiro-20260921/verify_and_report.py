"""Verify the preserved missing-Carreiro-flow experiment and summarize paired results."""
import csv, hashlib, json, math
from pathlib import Path
from datetime import datetime
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
OLD = ROOT / 'outputs/experimento-niveis-ate-mucum-pesos-zero-20260921/predictions.csv'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, value): (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def rows(p): return list(csv.DictReader(p.open()))
def finite(s): return bool(s) and math.isfinite(float(s))
meta = json.loads((OUT/'experiment.json').read_text())
verified = []
for name, expected in meta['input_sha256'].items():
    source = Path(name)
    preserved = OUT/'protocol.json' if source.name == 'carreiro-missing-flow-proxy-protocol.json' else OUT/'code'/source.name
    used = preserved if preserved.exists() else source
    assert sha(used) == expected, str(used)
    verified.append({'original_path':name,'verified_path':str(used),'sha256':expected,'current_source_matches':source.exists() and sha(source)==expected})
training = rows(OUT/'proxy-training.csv')
assert len(training)==12
for r in training:
    assert datetime.fromisoformat(r['latest_training_target']) < datetime.fromisoformat(r['cutoff_exclusive'])
a, b = rows(OLD), rows(OUT/'predictions.csv')
assert len(a)==len(b)==23538
count, maxdiff, recovered, lost = 0, 0., [], []
common = []
for x,y in zip(a,b):
    for k in ['origin','target_time','nominal_lead_h','anchor_at','actual_m']:
        assert x[k]==y[k], k
    for k in ['reference_m','julho_levels_m']:
        if finite(x[k]):
            assert finite(y[k])
            diff=abs(float(x[k])-float(y[k])); maxdiff=max(maxdiff,diff); count+=1
    if x['status']=='paired':
        if y['status']!='paired': lost.append(y)
        else: common.append(y)
    elif y['status']=='paired': recovered.append(y)
assert maxdiff <= 1e-10 and not lost
assert len(recovered)==4122 and len(common)==18981 and count==38256
metrics=[]
for label, group in [('previously_paired',common),('newly_recovered',recovered)]:
    for lead in range(1,13):
        for subset in ['all','observed_ge_7m']:
            selected=[r for r in group if int(r['nominal_lead_h'])==lead and (subset=='all' or float(r['actual_m'])>=7)]
            for family in ['reference','julho_levels']:
                e=np.array([float(r[family+'_m'])-float(r['actual_m']) for r in selected])
                metrics.append(dict(population=label,nominal_lead_h=lead,subset=subset,family=family,n=len(e),mae_m=float(np.mean(abs(e))),within_0_50_n=int(np.sum(abs(e)<=.5)),within_0_50_fraction=float(np.mean(abs(e)<=.5)),bias_m=float(np.mean(e))))
with (OUT/'population-metrics.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(metrics[0])); w.writeheader(); w.writerows(metrics)
write('verification.json',dict(input_hashes=verified,training_models=12,training_cutoff_verified=True,identical_origin_target_truth_rows=len(a),previously_finite_values=count,max_preexisting_forecast_difference_m=maxdiff,previously_paired=len(common),recovered_pairs=len(recovered),lost_pairs=len(lost),previous_prediction_sha256=sha(OLD),prediction_sha256=sha(OUT/'predictions.csv'),documentation_clarification='Original executed protocol and code remain preserved. A post-run prose clarification is separately recorded; numerical settings unchanged.'))
write('decision.json',dict(promoted=False,live_issuance=False,goal_achieved=False,decision='Retain as a historical coverage candidate only.',reason='Recovers missing-input forecasts with every previously finite prediction unchanged. Twelve-hour high-water accuracy remains 30.2%, far below the 98% target. Previously inspected development periods and assumed input publication times do not supply independent or prospective proof.',next_evidence_needed=['Evaluate estimated upstream flow on observed held-out events and realistic missingness patterns without tuning against this test period.','Stratify recovered downstream predictions by flood event and origin trend.','Require independent temporal/event validation before any live candidate promotion.']))
full=rows(OUT/'evaluation.csv')
lines=['# Experimento de entradas estimadas para o Carreiro','','O teste recuperou **4.122 pares de previsões** antes inviáveis por falta de vazão do Carreiro. Os **38.256 valores de nível anteriormente calculáveis permaneceram idênticos**, com diferença máxima de 0 m. São dois modelos por par. Nenhum resultado foi promovido à rotina horária.','','Foram ajustados 12 modelos auxiliares com alvos observados anteriores a 01/07/2026. Eles usam 49 variáveis de chuva e das usinas, excluindo todas as quatro variáveis de vazão do próprio Carreiro. As estimativas substituem somente entradas ausentes dentro deste cálculo e ficam identificadas; nenhuma medição ou alvo foi preenchido. Modelos principais e parâmetros HGE permaneceram congelados.','','## Cobertura e precisão do conjunto completo','','| Prazo | Recorte | Modelo | Pares | Cobertura | Dentro de ±0,50 m | MAE |','|---|---|---|---:|---:|---:|---:|']
for r in full:
    if int(r['nominal_lead_h']) in [1,6,12]:
        lines.append(f"| {r['nominal_lead_h']} h | {r['subset']} | {r['family']} | {r['paired_n']} | {100*float(r['coverage']):.2f}% | {100*float(r['within_0_50_fraction']):.2f}% | {float(r['mae_m']):.3f} m |")
lines+=['','## Somente os pares recuperados','','| Prazo | Recorte | Modelo | Pares | Dentro de ±0,50 m | MAE |','|---|---|---|---:|---:|---:|']
for r in metrics:
    if r['population']=='newly_recovered' and r['nominal_lead_h'] in [1,6,12]:
        lines.append(f"| {r['nominal_lead_h']} h | {r['subset']} | {r['family']} | {r['n']} | {100*r['within_0_50_fraction']:.2f}% | {r['mae_m']:.3f} m |")
lines+=['','A melhoria de cobertura muda a população avaliada. A diferença nas métricas agregadas em relação ao experimento sem estimativas não representa melhoria nas previsões antigas: elas são exatamente iguais. O erro das vazões estimadas nos intervalos sem observações não pode ser medido diretamente.','','A precisão do candidato em 12 h nas cheias é de **30,21%**, apesar de cobertura de **99,16%** nesse recorte. O alvo continua sendo 98% de acertos por horizonte e nas cheias; ele não foi atingido.','','## Limites e integridade','','Este é um experimento histórico em períodos já examinados, com disponibilidade histórica das entradas ainda presumida. Não é evidência prospectiva, nem validação independente. Restam 147 alvos exatos ausentes e 288 âncoras ausentes, sem substituição por valores estimados.','','O protocolo e código efetivamente executados estão preservados em `protocol.json` e `code/`. A redação herdada dizia indevidamente que não haveria ajuste ou preenchimento, embora os campos explícitos já especificassem os 12 modelos auxiliares e seu uso. A correção posterior de texto está registrada em `documentation-clarification.json`; ela não altera os números nem reescreve o protocolo original.','','`verification.json` verifica os hashes das 22 entradas usando cópias executadas quando disponíveis, o corte temporal e a comparação completa das previsões. `population-metrics.csv` separa todas as métricas dos pares antigos e recuperados. A suíte local passou 89 testes antes desta consolidação documental.','']
(OUT/'report.md').write_text('\n'.join(lines))
write('artifact-hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps({'verified_inputs':len(verified),'recovered':len(recovered),'unchanged_values':count,'max_difference':maxdiff,'report':str(OUT/'report.md')}))
