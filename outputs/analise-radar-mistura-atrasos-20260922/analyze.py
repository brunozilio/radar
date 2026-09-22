"""Paired, profile-specific comparisons of the registered delay experiment."""
import csv,hashlib,json
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'outputs/experimento-radar-mistura-atrasos-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    for r in json.loads((SOURCE/'artifact-hashes.json').read_text()):assert sha(SOURCE/r['file'])==r['sha256']
    metrics=list(csv.DictReader((SOURCE/'evaluation.csv').open()))
    lookup={(r['phase'],r['profile'],r['horizon_h'],r['population'],r['subset'],r['family']):r for r in metrics}
    contrasts=[]
    for r in metrics:
        if r['family']!=f"profile_{r['profile']}_control":continue
        other='B' if r['profile']=='A' else 'A'
        for family in ('mixed_profile_candidate',f'profile_{other}_control'):
            n=lookup[r['phase'],r['profile'],r['horizon_h'],r['population'],r['subset'],family]
            for field in ('scheduled_rows','missing_truth','observed_targets','pairs','failures'):assert r[field]==n[field]
            c=dict(phase=r['phase'],profile=r['profile'],horizon_h=int(r['horizon_h']),population=r['population'],subset=r['subset'],
                   compared_family=family,matching_control=r['family'],observed_targets=int(r['observed_targets']),pairs=int(r['pairs']),failures=int(r['failures']),
                   baseline_hits=int(r['hits']),compared_hits=int(n['hits']),hits_delta=int(n['hits'])-int(r['hits']))
            for field in ('mae_m','bias_m','p98_abs_m','max_abs_m'):
                c['baseline_'+field]=float(r[field]) if r[field] else None;c['compared_'+field]=float(n[field]) if n[field] else None
                c[field+'_delta']=float(n[field])-float(r[field]) if r[field] else None
            contrasts.append(c)
    assert len(contrasts)==576
    with (OUT/'contrasts.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(contrasts[0]));w.writeheader();w.writerows(contrasts)
    group=defaultdict(list)
    for r in contrasts:
        if r['population']=='full_schedule' and r['compared_family']=='mixed_profile_candidate':group[r['phase'],r['profile'],r['subset']].append(r)
    summaries=[]
    for (phase,profile,subset),rows in sorted(group.items()):
        assert len(rows)==12
        signs=lambda field,positive_good:dict(Counter('unchanged' if r[field]==0 else 'improved' if (r[field]>0)==positive_good else 'regressed' for r in rows))
        summaries.append(dict(phase=phase,profile=profile,subset=subset,hit_horizons=signs('hits_delta',True),mae_horizons=signs('mae_m_delta',False)))
    result=dict(source_manifest_sha256=sha(SOURCE/'artifact-hashes.json'),contrasts=len(contrasts),candidate_vs_matching_control=summaries,
                paired_profile_views_are_not_independent_events=True,independent_test=False,promoted=False,goal_achieved=False)
    (OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Mistura de perfis de atraso — resultados de desenvolvimento','',
           'Cada comparação usa a mesma população de avaliação e o controle treinado no perfil correspondente. A mistura usa uma única amostra por origem, com perfil escolhido por PCG64(57) antes dos ajustes. Os dois perfis são vistas alternativas das mesmas origens, nunca eventos independentes. Todos os períodos já eram conhecidos.','',
           'Tabela: observado >=7 m, população completa de horários. Falhas permanecem no denominador. Valores de erro em metros.','',
           '| Corte | Perfil | h | Acertos controle → mistura | MAE controle → mistura | Máximo controle → mistura |',
           '|---|---|---:|---:|---:|---:|']
    for r in contrasts:
        if r['compared_family']=='mixed_profile_candidate' and r['population']=='full_schedule' and r['subset']=='level_ge_7m' and r['horizon_h'] in (1,6,12):
            lines.append(f"| {r['phase']} | {r['profile']} | {r['horizon_h']} | {r['baseline_hits']} → {r['compared_hits']} / {r['observed_targets']} | {r['baseline_mae_m']:.4f} → {r['compared_mae_m']:.4f} | {r['baseline_max_abs_m']:.4f} → {r['compared_max_abs_m']:.4f} |")
    lines += ['', 'Os CSVs completos preservam todos os horizontes, recortes, ausências e também o controle treinado no outro perfil. Não selecionar o melhor perfil por horizonte. Nenhuma promoção operacional ou alegação de 98%.','']
    (OUT/'README.md').write_text('\n'.join(lines))
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
