import csv,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[1];S=W/'outputs/experimento-radar-historico-junho2024-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for item in json.loads((S/'artifact-hashes.json').read_text()):assert sha(S/item['file'])==item['sha256']
 rows=list(csv.DictReader((S/'evaluation.csv').open()));assert len(rows)==288
 lookup={(r['phase'],int(r['horizon_h']),r['subset'],r['population'],r['family']):r for r in rows};assert len(lookup)==288
 contrasts=[]
 for phase in ['validation','test']:
  for h in range(1,13):
   for subset in ['all','level_ge_7m']:
    for population in ['full_schedule','complete24','missing24']:
     a=lookup[phase,h,subset,population,'native_control'];b=lookup[phase,h,subset,population,'augmented']
     for k in ['scheduled_rows','observed_targets','n','failures']:assert a[k]==b[k]
     r={'phase':phase,'horizon_h':h,'subset':subset,'population':population,**{k:int(a[k]) for k in ['scheduled_rows','observed_targets','n','failures']}}
     for k in ['hits','mae_m','bias_m','p98_abs_m','max_abs_m']:
      av=float(a[k]) if a[k] else None;bv=float(b[k]) if b[k] else None
      r['control_'+k]=av;r['candidate_'+k]=bv;r['change_'+k]=bv-av if av is not None and bv is not None else None
     contrasts.append(r)
 with (R/'contrasts.csv').open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(contrasts[0]));w.writeheader();w.writerows(contrasts)
 summary=[]
 for phase in ['validation','test']:
  for subset in ['all','level_ge_7m']:
   z=[r for r in contrasts if r['phase']==phase and r['subset']==subset and r['population']=='full_schedule']
   summary.append({'phase':phase,'subset':subset,'horizons':12,'hits_improved':sum(r['change_hits']>0 for r in z),'hits_worsened':sum(r['change_hits']<0 for r in z),'hits_equal':sum(r['change_hits']==0 for r in z),'mae_improved':sum(r['change_mae_m']<0 for r in z),'mae_worsened':sum(r['change_mae_m']>0 for r in z),'maximum_worsened':sum(r['change_max_abs_m']>0 for r in z)})
 (R/'summary.json').write_text(json.dumps({'contrasts':144,'groups':summary,'source_manifest_sha256':sha(S/'artifact-hashes.json'),'promoted':False,'goal_achieved':False},indent=2)+'\n')
 text='# Adição de junho de 2024 — comparação de desenvolvimento\n\n24 modelos candidatos foram ajustados com junho acrescido ao histórico recente; os24 controles congelados de120variáveis foram reproduzidos exatamente. Mesmos alvos, disponibilidade, cortes e parâmetros. O controle nesta tabela é experimental observado120, não a operação com180entradas. Todos os resultados são desenvolvimento conhecido; não comprovam98% nem validam eventos independentes.\n'
 for phase in ['validation','test']:
  text+='\n## '+phase+' — nível observado ≥7m\n\n| Horizonte nominal | Alvos / pares / falhas | Acertos controle → junho | MAE controle → junho (m) | Maior erro controle → junho (m) |\n|---|---|---|---|---|\n'
  for r in contrasts:
   if r['phase']==phase and r['subset']=='level_ge_7m' and r['population']=='full_schedule':
    text+=f"| {r['horizon_h']}h | {r['observed_targets']} / {r['n']} / {r['failures']} | {r['control_hits']:.0f} → {r['candidate_hits']:.0f} | {r['control_mae_m']:.3f} → {r['candidate_mae_m']:.3f} | {r['control_max_abs_m']:.3f} → {r['candidate_max_abs_m']:.3f} |\n"
 text+='\n`contrasts.csv` inclui também todos os níveis e os recortes de disponibilidade. Nenhum horizonte foi escolhido para montar um modelo misto. As tolerâncias não foram ampliadas. Regime pós-avaria, referência da régua e publicação histórica de junho permanecem limitações. Falhas são mantidas no denominador observado. Nenhuma promoção operacional.\n'
 (R/'README.md').write_text(text)
 (R/'manifest.json').write_text(json.dumps([{'file':p.name,'sha256':sha(p)} for p in sorted(R.iterdir()) if p.is_file()],indent=2)+'\n')
 print(json.dumps(summary))
if __name__=='__main__':main()
