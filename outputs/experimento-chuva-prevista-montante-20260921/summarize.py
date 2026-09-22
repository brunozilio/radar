import csv,hashlib,json
from collections import defaultdict
from pathlib import Path
from datetime import datetime
OUT=Path(__file__).resolve().parent

def rows(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
meta=json.loads((OUT/'experiment.json').read_text())
for name,expected in meta['input_sha256'].items():assert sha(Path(name))==expected
training=rows(OUT/'training.csv')
for t in training:assert datetime.fromisoformat(t['latest_training_target'])<datetime.fromisoformat(t['cutoff_exclusive'])
group=defaultdict(list)
for r in rows(OUT/'predictions.csv'):group[r['family']].append(r)
a,b=group['level_and_slopes'],group['levels_forecast_rain'];assert len(a)==len(b)==197206
for x,y in zip(a,b):
    for k in ['source','lead_h','phase','origin','target_time','actual_m3_s','high_flow']:assert x[k]==y[k]
evaluation=rows(OUT/'evaluation.csv');summary=[];lead_comparisons=[]
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
        for subset in ['all','high_flow']:
            matched={}
            for r in evaluation:
                if (r['source'],r['phase'],r['subset'])==(source,phase,subset):matched[int(r['lead_h']),r['family']]=r
            wins=0
            for h in range(12):
                ref,can=matched[h,'level_and_slopes'],matched[h,'levels_forecast_rain'];assert ref['n']==can['n']
                wins+=float(can['mae_m3_s'])<float(ref['mae_m3_s'])
            lead_comparisons.append(dict(source=source,phase=phase,subset=subset,leads_with_lower_mae=wins,total_leads=12))
dump('summary.json',{'aggregate':summary,'lead_comparisons':lead_comparisons})
dump('verification.json',dict(input_hashes_verified=len(meta['input_sha256']),identical_target_pairs_per_family=len(a),training_cutoffs_verified=len(training),reference_reproduction_max_difference_m3_s=meta['reference_reproduction_max_difference_m3_s'],tests_passed=97,goal_achieved=False))
dump('decision.json',dict(promoted=False,live_issuance=False,goal_achieved=False,decision='Advance July only to a local downstream diagnostic; reject Carreiro rain extension.',reason='July aggregate general/high-flow MAE improved in both chronological development phases. Carreiro aggregate errors worsened. Actual prospective accuracy, independent event validation and downstream stage improvement remain unproven.',next_step='Use frozen pre-July July rain models with unchanged reference Carreiro and explicit missing-input proxy in paired downstream evaluation. Compare against preserved level-feature candidate, retaining every failure and horizon.',historical_weather_availability='Assumed fixed24h lead contract, not certified run-by-run publication.',live_distribution_gap='Latest-run live forecasts differ from fixed24h historical forecast vintages. No automatic integration.'))
lines=['# Chuva prevista nos preditores de vazão','','Foram acrescentadas 20 variáveis de chuva prevista à referência com níveis das usinas: acumulados de 3, 6, 9 e 12 h em cinco pontos, usando GFS/ECMWF/ICON. Cada média usa apenas membros com janela completa; dado ausente não vira chuva zero. Não foi utilizada chuva observada futura.','','Foram ajustados 48 modelos e preservadas 48 referências, sem busca de hiperparâmetros. A referência reproduziu exatamente os valores anteriores. As duas famílias têm os mesmos 197.206 pares, com corte de treino anterior ao período avaliado. Contagens somadas entre prazos contêm alvos repetidos, não eventos independentes.','','## Resultado','','MAE agregado ponderado por contagem, em m³/s:','','| Fonte | Período | Família | Geral | Vazões altas |','|---|---|---|---:|---:|']
for r in summary:lines.append(f"| {r['source']} | {r['phase']} | {r['family']} | {r['all']['mae_m3_s']:.2f} | {r['high_flow']['mae_m3_s']:.2f} |")
lines+=['','Em Julho, o erro em vazões altas caiu de 266,58 para 241,57 m³/s na validação e de 396,03 para 389,60 m³/s no teste. No prazo de 11 h, a queda foi 601,77→480,29 m³/s na validação e 687,95→669,61 m³/s no teste. Esses ganhos são de vazão, não porcentagens de acerto do nível do rio.','','## Diferenças entre prazos','']
for r in lead_comparisons:lines.append(f"- {r['source']}, {r['phase']}, {r['subset']}: MAE menor em {r['leads_with_lower_mae']}/12 prazos.")
lines+=['','## Decisão e limites','','Levar somente o candidato de Julho à comparação local de propagação até Muçum. A extensão de Carreiro piorou os resultados agregados e não foi selecionada. **Nenhuma promoção à rotina horária.**','','Os arquivos usam `precipitation_previous_day1`: cada tempo válido está associado à antecedência nominal de 24 h. Para alvos origem+1…+12 h, isso sugere inicializações anteriores à origem, mas não há `run`, `issued_at` ou recibo histórico de publicação por registro. Vintages podem variar dentro de uma janela; não é uma rodada única. A disponibilidade histórica permanece presumida.','','A previsão operacional mais recente tem distribuição de antecedências diferente deste arquivo. Antes de integrar, é preciso lidar com essa diferença e provar ganho no nível, em eventos separados e prospectivamente. Os cinco pontos não são médias espaciais completas das bacias. Os períodos avaliados já foram examinados e continuam desenvolvimento.','','Os 97 testes passaram. Parâmetros, entradas e saídas permanecem preservados; a meta de 98% não foi atingida.','']
(OUT/'report.md').write_text('\n'.join(lines))
log=Path('/tmp/radar-upstream-rain.log')
if log.exists() and not (OUT/'execution.log').exists():log.rename(OUT/'execution.log')
dump('artifact-hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps({'pairs_per_family':len(a),'inputs_verified':len(meta['input_sha256']),'lead_comparisons':lead_comparisons}))
