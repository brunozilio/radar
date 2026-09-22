import csv, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'outputs/experimento-radar-historico-2018-119-20260922'
assert (SOURCE/'experiment.json').exists() and not (OUT/'contrasts.csv').exists()
manifest=json.loads((SOURCE/'artifact-hashes.json').read_text())
for item in manifest:
    assert hashlib.sha256((SOURCE/item['file']).read_bytes()).hexdigest()==item['sha256']
rows=list(csv.DictReader((SOURCE/'evaluation.csv').open()))
groups={}
for r in rows:
    key=(r['phase'],int(r['horizon_h']),r['population'],r['subset'])
    groups.setdefault(key,{})[r['family']]=r
contrasts=[]
for key,group in sorted(groups.items()):
    a,b=group['hourly_control'],group['hourly_plus2018']
    assert all(a[k]==b[k] for k in ['scheduled_rows','missing_truth','observed_targets','pairs','failures'])
    contrasts.append({'phase':key[0],'horizon_h':key[1],'population':key[2],'subset':key[3],
        **{k:int(a[k]) for k in ['scheduled_rows','missing_truth','observed_targets','pairs','failures']},
        'control_hits':int(a['hits']),'augmented_hits':int(b['hits']),
        'hit_change':int(b['hits'])-int(a['hits']),
        'control_mae_m':a['mae_m'],'augmented_mae_m':b['mae_m'],
        'mae_change_m':float(b['mae_m'])-float(a['mae_m']) if a['mae_m'] else None,
        'control_max_abs_m':a['max_abs_m'],'augmented_max_abs_m':b['max_abs_m'],
        'max_change_m':float(b['max_abs_m'])-float(a['max_abs_m']) if a['max_abs_m'] else None})
with (OUT/'contrasts.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(contrasts[0]));w.writeheader();w.writerows(contrasts)
summary=[]
for phase in ('validation','test'):
    for subset in ('all','level_ge_7m'):
        group=[r for r in contrasts if r['phase']==phase and r['population']=='full_schedule' and r['subset']==subset]
        summary.append({'phase':phase,'subset':subset,'horizons':len(group),
            'hit_better':sum(r['hit_change']>0 for r in group),'hit_worse':sum(r['hit_change']<0 for r in group),'hit_equal':sum(r['hit_change']==0 for r in group),
            'mae_better':sum(r['mae_change_m']<0 for r in group),'mae_worse':sum(r['mae_change_m']>0 for r in group),
            'maximum_error_worse':sum(r['max_change_m']>0 for r in group)})
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# Efeito da adição de2018 sob a âncora horária experimental','',
'Comparação pareada entre novos controles somente2025/2026 e candidatos com todos os exemplos admissíveis de2018. Os dois lados usam a mesma preparação, os mesmos parâmetros, pesos e alvos. Os120campos preparados são preservados; o estimador recebe119, omitindo exclusivamente dH0,5deMuçum, inteiramente ausente nos dois lados. A tentativa120falhou antes de qualquer modelo concluído e permanece preservada.',
'','| Fase | Horizonte | Alvos≥7m | Pares | Acertos controle→+2018 | MAE controle→+2018(m) | Maior erro controle→+2018(m) |','|---|---:|---:|---:|---:|---:|---:|']
for r in contrasts:
    if r['population']=='full_schedule' and r['subset']=='level_ge_7m' and r['horizon_h'] in (1,6,12):
        lines.append(f"| {r['phase']} | {r['horizon_h']}h | {r['observed_targets']} | {r['pairs']} | {r['control_hits']}→{r['augmented_hits']} | {float(r['control_mae_m']):.4f}→{float(r['augmented_mae_m']):.4f} | {float(r['control_max_abs_m']):.4f}→{float(r['augmented_max_abs_m']):.4f} |")
lines+=['','## Os12horizontes, sem selecionar somente os favoráveis','']
for r in summary:
    lines.append(f"- {r['phase']}/{r['subset']}: acertos melhoram em{r['hit_better']}, pioram em{r['hit_worse']} e empatam em{r['hit_equal']}; MAE melhora em{r['mae_better']} e piora em{r['mae_worse']}; erro máximo piora em{r['maximum_error_worse']}.")
lines+=['',
'Os períodos de avaliação já eram conhecidos no desenvolvimento. As duas semanas2018 entram somente no treino e não são apresentadas como teste inédito. Esses controles foram treinados novamente sob a âncora1h; não representam reprodução dos modelos operacionais de180entradas nem dos controles antigos.',
'',
'Acerto exige erro absoluto≤0,50m antes de arredondamento. Falhas são mantidas no denominador de alvos observados; verdade ausente continua desconhecida. Os subconjuntos complete_upstream18/missing_upstream18 referem-se às colunas originais6..23, sem classificar a ausência estrutural de dH0,5 como perda de montante.',
'',
'Métricas retrospectivas não comprovam98%prospectivos. Fuso,datum,publicação histórica e equivalência entre regimes permanecem sem certificação. Nenhum candidato foi promovido, nenhuma previsão operacional foi substituída e nenhuma combinação porhorizonte foi escolhida depois dos resultados.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n')
(OUT/'manifest.json').write_text(json.dumps({'source_manifest_sha256':hashlib.sha256((SOURCE/'artifact-hashes.json').read_bytes()).hexdigest(),'files':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.iterdir())]},indent=2)+'\n')
print(json.dumps({'summary':summary,'selected_high_rows':[r for r in contrasts if r['population']=='full_schedule' and r['subset']=='level_ge_7m' and r['horizon_h'] in (1,6,12)]},indent=2))
