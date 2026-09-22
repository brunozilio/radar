"""Compare fixed normalization with exactly matched raw model families."""
import csv, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'outputs/experimento-radar-estabilidade-numerica-20260922'
OUT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    for entry in json.loads((SOURCE/'artifact-hashes.json').read_text()):
        assert sha(SOURCE/entry['file']) == entry['sha256']
    contrasts = []
    for filename, role in [('evaluation.csv', 'original_2025_2026'),
                           ('reused-2021-2022-evaluation.csv', 'reused_development')]:
        rows = list(csv.DictReader((SOURCE/filename).open()))
        lookup = {(r['period'],r['horizon_h'],r['population'],r['subset'],r['family']):r for r in rows}
        for r in rows:
            if not r['family'].startswith('raw_'):
                continue
            family = r['family'][4:]
            new = lookup[r['period'],r['horizon_h'],r['population'],r['subset'],'normalized_'+family]
            for field in ('scheduled_rows','missing_truth','observed_targets','pairs','failures'):
                assert r[field] == new[field], (field,r,new)
            contrast = dict(role=role,period=r['period'],horizon_h=int(r['horizon_h']),
                            population=r['population'],subset=r['subset'],family=family,
                            observed_targets=int(r['observed_targets']),pairs=int(r['pairs']),
                            failures=int(r['failures']),raw_hits=int(r['hits']),normalized_hits=int(new['hits']),
                            hits_delta=int(new['hits'])-int(r['hits']))
            for field in ('mae_m','bias_m','p98_abs_m','max_abs_m'):
                contrast['raw_'+field] = float(r[field]) if r[field] else None
                contrast['normalized_'+field] = float(new[field]) if new[field] else None
                contrast[field+'_delta'] = float(new[field])-float(r[field]) if r[field] else None
            contrasts.append(contrast)
    assert len(contrasts)==720
    with (OUT/'contrasts.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(contrasts[0]));writer.writeheader();writer.writerows(contrasts)
    grouped=defaultdict(list)
    for r in contrasts:
        if r['population']=='full_schedule':grouped[r['period'],r['subset'],r['family']].append(r)
    summary=[]
    for (period,subset,family),rows in sorted(grouped.items()):
        assert len(rows)==12
        signs=Counter('improved' if r['hits_delta']>0 else 'regressed' if r['hits_delta']<0 else 'unchanged' for r in rows)
        mae=Counter('improved' if r['mae_m_delta']<0 else 'regressed' if r['mae_m_delta']>0 else 'unchanged' for r in rows)
        summary.append(dict(period=period,subset=subset,family=family,hit_horizons=dict(signs),mae_horizons=dict(mae)))
    result=dict(source_manifest_sha256=sha(SOURCE/'artifact-hashes.json'),contrasts=len(contrasts),
                full_schedule_summary=summary,promoted=False,goal_achieved=False,
                limitation='2021/2022 and prior 2025/2026 evaluations are known development diagnostics for this change; no fresh independent accuracy test.')
    (OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    table=['| Período | Família | h | Acertos antes → depois | MAE antes → depois | Máximo antes → depois |',
           '|---|---|---:|---:|---:|---:|']
    for r in contrasts:
        if r['population']=='full_schedule' and r['subset']=='level_ge_7m' and r['horizon_h'] in (1,6,12):
            table.append(f"| {r['period']} | {r['family']} | {r['horizon_h']} | {r['raw_hits']} → {r['normalized_hits']} / {r['observed_targets']} | {r['raw_mae_m']:.6f} → {r['normalized_mae_m']:.6f} | {r['raw_max_abs_m']:.6f} → {r['normalized_max_abs_m']:.6f} |")
    (OUT/'README.md').write_text('# Representação numérica fixa: comparação pareada\n\n'
        'Regra registrada antes do ajuste: arredondar somente colunas de chuva/cobertura para oito casas. '
        'Cada família é comparada à mesma composição de treinamento. Todos os horizontes e populações estão no CSV. '
        'A tabela abaixo ilustra o recorte observado >=7 m; falhas permanecem no denominador. '
        'Os períodos já foram examinados: estes resultados não são um novo teste independente.\n\n'+
        '\n'.join(table)+'\n\nIgualdade numérica entre reconstruções não prova precisão hidrológica. Nenhuma promoção operacional. Meta de 98% não demonstrada.\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
