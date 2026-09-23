"""Select only forecasts already persisted >= H real hours before each target."""
import json, math
from pathlib import Path
from datetime import datetime
P=Path(__file__).resolve().parent
rows=json.loads((P/'todas-emissoes.json').read_text())
def epoch(s):return datetime.fromisoformat(s).timestamp()
selected=[]
for city in ['mucum','encantado','santa-tereza']:
    targets=sorted({r['target_at'] for r in rows if r['station']==city})
    for target in targets:
        for horizon in range(1,7):
            candidates=[r for r in rows if r['station']==city and r['target_at']==target and max(epoch(r['generated_at']),epoch(r['first_stored_at']))<=epoch(target)-horizon*3600]
            if not candidates:continue
            last=max(candidates,key=lambda r:epoch(r['generated_at']))
            selected.append({**last,'minimum_real_lead_h':horizon})
(P/'comparacao-antecedencia-real.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
metrics={}
for city in ['mucum','encantado','santa-tereza']:
    metrics[city]={}
    for h in range(1,7):
        data=[r for r in selected if r['station']==city and r['minimum_real_lead_h']==h and r['status']=='matched']
        errors=[r['error_m'] for r in data]
        metrics[city][h]={'n':len(errors),'mae_m':sum(map(abs,errors))/len(errors) if errors else None,'bias_m':sum(errors)/len(errors) if errors else None,'max_abs_m':max(map(abs,errors)) if errors else None,'within_050m':sum(abs(v)<=.5 for v in errors)}
(P/'metricas-antecedencia-real.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
lines=['# Comparação com antecedência real','', 'Para cada alvo e antecedência mínima, selecionamos a última previsão que já estava persistida no R2 pelo menos H horas antes do alvo. Não há escolha pelo erro. Horário de emissão e primeiro armazenamento são exigidos antes desse limite. Erro = previsto − observado; valores em metros.','', 'Os modelos publicados cobrem seis alvos nominais por rodada. Como a emissão acontece depois da hora de referência, nenhum ponto da amostra oferece seis horas reais completas de antecedência. Isso não foi preenchido com uma previsão inventada.','']
for city,label in [('mucum','Muçum'),('encantado','Encantado'),('santa-tereza','Santa Tereza')]:
    lines += [f'## {label}','', '| Antecedência mínima real | Pares | Erro médio absoluto | Maior erro absoluto | Dentro de ±0,50 m |','|---|---:|---:|---:|---:|']
    for h,m in metrics[city].items():
        if m['n']:lines.append(f'| {h}h | {m["n"]} | {m["mae_m"]:.3f} | {m["max_abs_m"]:.3f} | {m["within_050m"]}/{m["n"]} |')
        else:lines.append(f'| {h}h | 0 | sem previsão elegível | — | — |')
    lines+=['','| Alvo | Emissão | Primeiro armazenamento | Previsto ≥1h antes | Observado | Erro | Fonte |','|---|---|---|---:|---:|---:|---|']
    for row in selected:
        if row['station']!=city or row['minimum_real_lead_h']!=1:continue
        fmt=lambda v:datetime.fromisoformat(v).strftime('%d/%m %H:%M:%S')
        real=f'{row["observed_m"]:.2f}' if row['status']=='matched' else row['status']
        error=f'{row["error_m"]:+.2f}' if row['status']=='matched' else '—'
        lines.append(f'| {fmt(row["target_at"])} | {fmt(row["generated_at"])} | {fmt(row["first_stored_at"])} | {row["forecast_m"]:.2f} | {real} | {error} | {row["observed_source"] or "—"} |')
    lines+=['']
(P/'comparacao-antecedencia-real.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(metrics,ensure_ascii=False,indent=2))
print('MUÇUM TODAY >=1 REAL HOUR')
for r in selected:
 if r['station']=='mucum' and r['minimum_real_lead_h']==1 and r['status']=='matched' and r['target_at'].startswith('2026-09-22'):
  print(r['target_at'][11:16],r['generated_at'][11:16],f'{r["forecast_m"]:.2f}',f'{r["observed_m"]:.2f}',f'{r["error_m"]:+.2f}')
