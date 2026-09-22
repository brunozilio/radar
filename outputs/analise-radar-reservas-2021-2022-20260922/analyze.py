"""Summarize the fixed reserved challenge without selecting or refitting any model."""
from pathlib import Path
from collections import Counter
import csv,json,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1];D=ROOT/'outputs/experimento-radar-reservas-2021-2022-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,v):(P/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
for h in json.loads((D/'artifact-hashes.json').read_text()):assert sha(D/h['file'])==h['sha256']
metrics=list(csv.DictReader((D/'evaluation.csv').open()));pred=list(csv.DictReader((D/'predictions.csv').open()))
lookup={(r['period'],int(r['horizon_h']),r['subset'],r['family']):r for r in metrics if r['population']=='full_schedule'}
changes=[];tallies=[]
for period in ('2021','2022','pooled'):
    for subset in ('all','level_ge_7m'):
        group=[]
        for h in range(1,13):
            b=lookup[period,h,subset,'control120'];c=lookup[period,h,subset,'candidate120_plus2020']
            assert (b['observed_targets'],b['paired_predictions'],b['missing_forecasts'])==(c['observed_targets'],c['paired_predictions'],c['missing_forecasts'])
            row=dict(period=period,subset=subset,horizon_h=h,observed_targets=int(b['observed_targets']),pairs=int(b['paired_predictions']),failures=int(b['missing_forecasts']),
                control_hits=int(b['hits']),candidate_hits=int(c['hits']),hit_change=int(c['hits'])-int(b['hits']),
                control_fraction=float(b['observed_target_hit_fraction']),candidate_fraction=float(c['observed_target_hit_fraction']),
                control_mae=float(b['mae_m']),candidate_mae=float(c['mae_m']),mae_change=float(c['mae_m'])-float(b['mae_m']),
                control_max=float(b['max_abs_m']),candidate_max=float(c['max_abs_m']),max_change=float(c['max_abs_m'])-float(b['max_abs_m']))
            changes.append(row);group.append(row)
        tallies.append(dict(period=period,subset=subset,hits_improve=sum(r['hit_change']>0 for r in group),hits_tie=sum(r['hit_change']==0 for r in group),hits_worse=sum(r['hit_change']<0 for r in group),
            mae_improve=sum(r['mae_change']<0 for r in group),mae_worse=sum(r['mae_change']>0 for r in group),max_worse=sum(r['max_change']>0 for r in group),
            candidate_point_fraction_ge98_horizons=[r['horizon_h'] for r in group if r['candidate_fraction']>=.98]))
with (P/'changes.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(changes[0]));w.writeheader();w.writerows(changes)
worst=[]
for year in (2021,2022):
    for family in ('control120','candidate120_plus2020'):
        rr=[r for r in pred if r['year']==str(year) and r['nominal_lead_h']=='12' and r['actual_m'] and r[family+'_m']]
        r=max(rr,key=lambda r:abs(float(r[family+'_m'])-float(r['actual_m'])))
        worst.append(dict(year=year,family=family,origin=r['origin'],target_time=r['target_time'],base_m=float(r['base_m']),actual_m=float(r['actual_m']),forecast_m=float(r[family+'_m']),absolute_error_m=abs(float(r[family+'_m'])-float(r['actual_m']))))
result=dict(tallies=tallies,worst_12h_cases=worst,input_sha256={str((D/f).relative_to(ROOT)):sha(D/f) for f in ('predictions.csv','evaluation.csv','experiment.json','pre-inference-manifest.json')},
    point_fractions_are_not_prospective_certification=True,no_model_selection_or_refit=True,promoted=False,goal_achieved=False)
dump('analysis.json',result)
lines=['# Primeira comparação retrospectiva nas reservas2021/2022','',
'Modelos e entradas foram fixados antes da inferência. Comparação120 observada versus120+2020; nenhum novo treino. Os modelos usam também treino posterior aos anos reservados: isto não reproduz uma previsão possível com somente dados disponíveis naquela época.',
'','## Recorte de nível observado >=7 m','',
'Acertos: erro absoluto <=0,50 m. O denominador inclui alvos observados sem previsão; MAE/máximo usam os pares disponíveis. Horas consecutivas e horizontes compartilham eventos e não são evidência independente.',
'','| Período | Horizonte | Acertos controle→candidato / alvos | MAE controle→candidato (m) | Máximo controle→candidato (m) |','|---|---:|---:|---:|---:|']
for r in changes:
    if r['subset']=='level_ge_7m' and r['horizon_h'] in (1,6,12):
        lines.append(f"| {r['period']} | {r['horizon_h']}h | {r['control_hits']}→{r['candidate_hits']} / {r['observed_targets']} | {r['control_mae']:.4f}→{r['candidate_mae']:.4f} | {r['control_max']:.4f}→{r['candidate_max']:.4f} |")
lines+=['','## Todos os horizontes, sem seleção','']
for s in tallies:lines.append(f"- {s['period']} / {s['subset']}: acertos melhoram/empatam/pioram em {s['hits_improve']}/{s['hits_tie']}/{s['hits_worse']} horizontes; MAE melhora em {s['mae_improve']}/12; máximo piora em {s['max_worse']}/12.")
lines+=['','Nenhum modelo foi promovido. Percentuais pontuais históricos não satisfazem a meta: faltam evidência prospectiva certificada, tamanho amostral por horizonte, dez eventos independentes e incerteza apropriada à dependência temporal. A janela já foi vista; se estes erros forem usados para modificar modelos, passa a ser desenvolvimento e não um novo teste independente.','',
'changes.csv contém todos os72 contrastes de período/subconjunto/horizonte, sem ocultar regressões. analysis.json preserva os piores casos de12h e hashes das entradas.']
(P/'README.md').write_text('\n'.join(lines)+'\n')
dump('artifact-hashes.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps(result,indent=2))
