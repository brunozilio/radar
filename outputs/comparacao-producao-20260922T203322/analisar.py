"""Offline audit of exact production R2 forecasts against production D1 levels."""
import json, math, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
P=Path(__file__).resolve().parent
TZ=timezone(timedelta(hours=-3))
CITIES={'mucum':('Muçum','86510000'),'encantado':('Encantado','86720000'),'santa-tereza':('Santa Tereza','86472600')}
def epoch(x):return datetime.fromisoformat(x.replace('Z','+00:00')).timestamp()
def iso(x):return datetime.fromtimestamp(x,TZ).isoformat()
def show(x):return datetime.fromtimestamp(x,TZ).strftime('%d/%m %H:%M')
def write(name,data): (P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def finite(x):return isinstance(x,(int,float)) and math.isfinite(x)
def stats(rows):
    e=[r['error_m'] for r in rows if r['status']=='matched']
    return {'n':len(e),'mae_m':sum(abs(v) for v in e)/len(e) if e else None,'rmse_m':math.sqrt(sum(v*v for v in e)/len(e)) if e else None,'bias_m':sum(e)/len(e) if e else None,'max_abs_m':max(map(abs,e)) if e else None,'within_050m':sum(abs(v)<=.5 for v in e),'hit_rate_050m':sum(abs(v)<=.5 for v in e)/len(e) if e else None,'missing':sum(r['status']=='missing_observation' for r in rows),'future':sum(r['status']=='future' for r in rows),'publication_after_target':sum(r['status']=='publication_after_target' for r in rows)}
receipts=json.loads((P/'r2-receipts.json').read_text())['receipts']
cutoff=max(epoch(r['readAt']) for r in receipts)
query=json.loads((P/'d1-observacoes.json').read_text())
assert all(r['success'] and r['meta']['rows_written']==0 and not r['meta']['changed_db'] for r in query)
observations=[v for result in query for v in result['results']]
obs={};conflicts=[]
for row in observations:
    if not finite(row['level']) or not finite(row['level_cm']) or row['level_cm']<=-9999:continue
    key=(row['station'],epoch(row['timestamp']),row['source'])
    if key in obs and obs[key]['level']!=row['level']:raise ValueError('Conflicting measurement at same instant/source')
    if abs(row['level']-row['level_cm']/100)>1e-8:raise ValueError('Inconsistent level units')
    obs[key]=row
for station,t,source in obs:
    if source!='SACE/SGB':continue
    ana=obs.get((station,t,'ANA/SNIRH'))
    if ana and abs(ana['level']-obs[(station,t,source)]['level'])>1e-8:
        conflicts.append({'station':station,'timestamp':iso(t),'sace_m':obs[(station,t,source)]['level'],'ana_m':ana['level'],'difference_m':obs[(station,t,source)]['level']-ana['level']})
issues={};copies=0
for receipt in sorted(receipts,key=lambda r: 0 if '/issues/' in r['key'] else 1):
    raw=(P/receipt['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
    payload=json.loads(raw)
    for station in CITIES:
        value=payload if station=='mucum' else payload.get(station)
        if not value:continue
        ref=epoch(value['referenceAt']);generated=epoch(value['generatedAt'])
        for model in value['models']:
            key=(station,model['id'],generated,ref)
            content={'points':model['points'],'observation':value['observation'],'modelVersion':value.get('modelVersion')}
            if key in issues:
                assert issues[key]['content']==content, 'Conflicting stored prediction identity'
                copies+=1
            else:
                issues[key]={'station':station,'model':model['id'],'reference':ref,'generated':generated,'content':content,'sourceObjects':[],'storedTimes':[]}
            issues[key]['sourceObjects'].append(receipt['key'])
            uploaded=receipt['listed'].get('last_modified')
            if uploaded:issues[key]['storedTimes'].append(epoch(uploaded))
for issue in issues.values():
    issue['firstStored']=min(issue['storedTimes']) if issue['storedTimes'] else None
    assert issue['firstStored'] is not None, 'No production persistence time'
    assert issue['firstStored']>=issue['generated']-1, 'Storage precedes generation'
# Latest actual emission of each reference hour, chosen without observed outcomes.
rounds={}
for key,issue in issues.items():
    rk=(issue['station'],issue['model'],issue['reference'])
    if rk not in rounds or rounds[rk]['generated']<issue['generated']:rounds[rk]=issue

def compare(issue,point):
    station=issue['station'];code=CITIES[station][1];target=epoch(point['timestamp'])
    forecast=point['level'];assert finite(forecast)
    nominal=(target-issue['reference'])/3600
    assert nominal in range(1,7) and target>issue['generated']
    sace=obs.get((code,target,'SACE/SGB'));ana=obs.get((code,target,'ANA/SNIRH'));actual=sace or ana
    status='publication_after_target' if issue['firstStored']>=target else 'future' if target>cutoff else 'matched' if actual else 'missing_observation'
    return {'station':station,'station_code':code,'model':issue['model'],'model_version':issue['content']['modelVersion'],
            'reference_at':iso(issue['reference']),'generated_at':iso(issue['generated']),'first_stored_at':iso(issue['firstStored']),
            'target_at':iso(target),'nominal_lead_h':int(nominal),'actual_lead_h':(target-issue['generated'])/3600,
            'forecast_m':forecast,'observed_m':actual['level'] if actual else None,'observed_source':actual['source'] if actual else None,
            'ana_m':ana['level'] if ana else None,'sace_m':sace['level'] if sace else None,
            'error_m':forecast-actual['level'] if status=='matched' else None,
            'abs_error_m':abs(forecast-actual['level']) if status=='matched' else None,
            'ana_error_m':forecast-ana['level'] if status=='matched' and ana else None,
            'status':status,'source_objects':issue['sourceObjects']}
allrows=[compare(i,p) for i in issues.values() for p in i['content']['points']]
selected=[compare(i,p) for i in rounds.values() for p in i['content']['points']]
selected.sort(key=lambda r:(r['station'],r['target_at'],r['nominal_lead_h']))
metrics={c:{str(h):stats([r for r in selected if r['station']==c and r['nominal_lead_h']==h]) for h in range(1,7)} for c in CITIES}
summary={'extracted_at':iso(cutoff),'production_database':'sofik-monitoramento-push','production_bucket':'sofik-monitoramento-media',
         'observations_read':len(observations),'r2_objects_read':len(receipts),'unique_station_issues':len(issues),'duplicate_station_copies_removed':copies,
         'selected_station_rounds':len(rounds),'unique_issue_points':len(allrows),'selected_round_points':len(selected),
         'metrics':metrics,'observation_source_disagreements':len(conflicts),
         'method':'Latest generated station emission per reference hour; target equals observation instant exactly; SACE priority as production UI, ANA retained separately; no interpolation; errors=forecast-observed; forecasts persisted after target excluded.',
         'limits':['No level QC stored in D1, no independent datum certification; these are retrospective errors, not proof of the 98% goal.','D1 retention is approximately 48 hours.','Issues persisted in R2 prove storage, not exact browser visibility time.','Station round samples and horizons overlap; not independent flood events.','Nominal 1h forecasts can have under 1h actual lead because issues are recalculated within the hour.']}
write('resumo.json',summary);write('comparacao-hora-a-hora.json',selected);write('todas-emissoes.json',allrows);write('divergencias-fontes.json',conflicts)
lines=['# Previsão × nível observado — produção',f'\nExtração: {summary["extracted_at"]}. D1 `{summary["production_database"]}` e R2 `{summary["production_bucket"]}`. Consultas somente leitura; zero linhas escritas no D1.\n',
       'Cada coluna usa a última emissão da rodada de origem correspondente (H−1, H−2, … H−6), escolhida sem consultar o resultado observado. Os valores nas colunas são **previsto / erro** em metros. Erro positivo = previsão acima do real. Horários de Brasília (UTC−03). Sem interpolação ou aproximação do horário.\n',
       'O observado segue a prioridade do site: SACE/SGB; ANA/SNIRH quando não há SACE no instante. Ambas as fontes permanecem no JSON. Emissão/antecedência real/objeto R2 estão registrados para cada par.\n']
for city,(label,_) in CITIES.items():
    lines += [f'## {label}','', '| Horizonte nominal | Pares | MAE (m) | Viés (m) | Maior erro absoluto (m) | Dentro de ±0,50 m |','|---|---:|---:|---:|---:|---:|']
    for h in range(1,7):
        m=metrics[city][str(h)]
        if m['n']:lines.append(f'| +{h}h | {m["n"]} | {m["mae_m"]:.3f} | {m["bias_m"]:+.3f} | {m["max_abs_m"]:.3f} | {m["within_050m"]}/{m["n"]} ({m["hit_rate_050m"]:.1%}) |')
    lines += ['', '| Hora alvo | Observado | Fonte | +1h previsto / erro | +2h | +3h | +4h | +5h | +6h |','|---|---:|---|---:|---:|---:|---:|---:|---:|']
    targets=sorted({r['target_at'] for r in selected if r['station']==city})
    for target in targets:
        rs={r['nominal_lead_h']:r for r in selected if r['station']==city and r['target_at']==target}
        measured=next((r for r in rs.values() if r['status']=='matched'),None)
        observed=f'{measured["observed_m"]:.2f}' if measured else ('futuro' if epoch(target)>cutoff else 'sem leitura exata')
        source=measured['observed_source'] if measured else '—'
        cells=[]
        for h in range(1,7):
            row=rs.get(h)
            if row is None:cells.append('—')
            elif row['status']=='matched':cells.append(f'{row["forecast_m"]:.2f} / {row["error_m"]:+.2f}')
            else:cells.append(f'{row["forecast_m"]:.2f} / pendente' if row['status']=='future' else f'{row["forecast_m"]:.2f} / sem par')
        lines.append('| '+ ' | '.join([show(epoch(target)),observed,source,*cells])+' |')
    lines+=['']
lines+=['## Rastreabilidade e limites','',f'{len(receipts)} objetos R2, {len(observations)} medições D1, {len(issues)} emissões distintas por cidade, {len(rounds)} rodadas por cidade. {copies} cópias repetidas removidas. {len(conflicts)} divergências entre ANA e SACE no mesmo instante.','',*['- '+x for x in summary['limits']], '', 'Arquivos: `comparacao-hora-a-hora.json` contém a seleção principal; `todas-emissoes.json` preserva todas as revisões; `r2-receipts.json` identifica origem e hashes; `d1-observacoes.json` preserva o resultado e metadados remotos; `divergencias-fontes.json` compara as duas fontes observadas.']
(P/'comparacao-hora-a-hora.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
