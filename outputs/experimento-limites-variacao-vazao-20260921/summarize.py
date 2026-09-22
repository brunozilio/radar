import csv,hashlib,json
from collections import defaultdict
from pathlib import Path
from datetime import datetime
OUT=Path(__file__).resolve().parent

def rows(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
meta=json.loads((OUT/'experiment.json').read_text())
for name,expected in meta['input_sha256'].items():
    p=Path(name);assert sha(p)==expected
transforms=json.loads((OUT/'transforms.json').read_text())
for t in transforms:assert datetime.fromisoformat(t['latest_training_target'])<datetime.fromisoformat(t['cutoff_exclusive'])
data=rows(OUT/'predictions.csv');group=defaultdict(list)
for r in data:group[r['family']].append(r)
a,b=group['level_and_slopes'],group['level_clipped_flow_changes']
assert len(a)==len(b)
for x,y in zip(a,b):
    for k in ['source','lead_h','phase','origin','target_time','actual_m3_s','high_flow']:assert x[k]==y[k]
evaluation=rows(OUT/'evaluation.csv');summary=[]
for source in ['julho','carreiro']:
    for phase in ['validation','test']:
        for family in group:
            aggregate={}
            for subset in ['all','high_flow']:
                selected=[r for r in evaluation if (r['source'],r['phase'],r['family'],r['subset'])==(source,phase,family,subset)]
                n=sum(int(r['n']) for r in selected)
                aggregate[subset]={'predictions_n':n,'mae_m3_s':sum(int(r['n'])*float(r['mae_m3_s']) for r in selected)/n,'bias_m3_s':sum(int(r['n'])*float(r['bias_m3_s']) for r in selected)/n}
            score=sum(float(r['mae_m3_s'])*(1 if r['subset']=='all' else .5) for r in evaluation if (r['source'],r['phase'],r['family'])==(source,phase,family))/12
            summary.append(dict(source=source,phase=phase,family=family,mean_lead_score_m3_s=score,**aggregate))
dump('summary.json',summary)
dump('verification.json',dict(input_hashes_verified=len(meta['input_sha256']),identical_target_pairs_per_family=len(a),training_cutoffs_verified=len(transforms),reference_reproduction_max_difference_m3_s=meta['reference_reproduction_max_difference_m3_s'],tests_passed=93,goal_achieved=False))
dump('decision.json',dict(promoted=False,live_issuance=False,goal_achieved=False,decision='Reject promotion of this statistical clipping candidate.',reason='July high-flow validation MAE worsened despite test-period improvement. Carreiro high-flow test MAE worsened despite aggregate validation improvement. No consistent benefit across chronological periods; no downstream level accuracy claim.',candidate_is_physical_limit=False,observations_modified=False))
lines=['# Limites estatísticos nas variações de vazão','','Foram ajustados 48 modelos novos e reutilizados 48 modelos congelados. Os dois candidatos usam exatamente os mesmos 197.206 pares por família, sem eliminar os extremos. A referência foi reproduzida com diferença máxima de 0 m³/s.','','O candidato limita somente 21 variáveis de mudança de vazão aos percentis 0,5 e 99,5 do treino de cada fonte/prazo. As vazões conhecidas, a chuva, os níveis e suas variações permanecem intactos. Esses limites controlam a influência estatística; não são limites físicos nem identificam automaticamente dados incorretos.','','## Resultados','','MAE agregado ponderado pelo número de pares, em m³/s. Contagens somadas entre prazos contêm alvos repetidos; não são eventos independentes.','','| Fonte | Período | Modelo | MAE geral | MAE vazões altas |','|---|---|---|---:|---:|']
for r in summary:lines.append(f"| {r['source']} | {r['phase']} | {r['family']} | {r['all']['mae_m3_s']:.2f} | {r['high_flow']['mae_m3_s']:.2f} |")
lines+=['','Para Julho, o erro em vazões altas no período de teste caiu de 396,03 para 315,62 m³/s, mas na validação anterior piorou de 266,58 para 277,63 m³/s. Para Carreiro, a validação em vazões altas melhorou, mas o teste piorou de 77,33 para 81,84 m³/s. Todos os prazos e vieses permanecem em `evaluation.csv`.','','## Decisão','','**Não promover.** A melhoria localizada no período motivador do diagnóstico não se sustentou nos dois períodos. Não foi feito ajuste dos percentis após ver os resultados. O teste continua sendo desenvolvimento em períodos já examinados, sem prova independente ou prospectiva. Não foi declarado ganho no nível de Muçum: isso exigiria avaliação da cadeia completa.','','Todos os parâmetros de transformação estão em `transforms.json`, com corte temporal e quantidade de entradas alteradas. Medições, previsões anteriores e rotina horária foram preservadas. A suíte passou 93 testes, incluindo isolamento dos limites em relação a valores futuros e preservação de variáveis não selecionadas/ausências.','']
(OUT/'report.md').write_text('\n'.join(lines))
log=Path('/tmp/radar-flow-clipping.log')
if log.exists() and not (OUT/'execution.log').exists():log.rename(OUT/'execution.log')
dump('artifact-hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps({'pairs_per_family':len(a),'inputs_verified':len(meta['input_sha256']),'decision':'not_promoted'}))
