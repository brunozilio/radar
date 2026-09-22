"""Keep both primary feature ablation and profile-matched comparisons visible."""
import csv,hashlib,json
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'outputs/experimento-radar-ausencia-carreiro-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    for item in json.loads((SOURCE/'artifact-hashes.json').read_text()):assert sha(SOURCE/item['file'])==item['sha256']
    metrics=list(csv.DictReader((SOURCE/'evaluation.csv').open()))
    lookup={(r['phase'],r['profile'],r['horizon_h'],r['population'],r['subset'],r['family']):r for r in metrics}
    contrasts=[]
    for n in metrics:
        if n['family']!='carreiro_missing_exposure':continue
        for ref in ('mixed_profile_candidate','profile_A_control','profile_B_control'):
            r=lookup[n['phase'],n['profile'],n['horizon_h'],n['population'],n['subset'],ref]
            for field in ('scheduled_rows','missing_truth','observed_targets','pairs','failures'):assert r[field]==n[field]
            c=dict(phase=n['phase'],profile=n['profile'],horizon_h=int(n['horizon_h']),population=n['population'],subset=n['subset'],reference=ref,
                   relation='primary_unmasked' if ref=='mixed_profile_candidate' else 'matching_profile' if ref==f"profile_{n['profile']}_control" else 'cross_profile',
                   observed_targets=int(n['observed_targets']),pairs=int(n['pairs']),failures=int(n['failures']),reference_hits=int(r['hits']),exposed_hits=int(n['hits']),hits_delta=int(n['hits'])-int(r['hits']))
            for field in ('mae_m','bias_m','p98_abs_m','max_abs_m'):
                c['reference_'+field]=float(r[field]) if r[field] else None;c['exposed_'+field]=float(n[field]) if n[field] else None
                c[field+'_delta']=float(n[field])-float(r[field]) if r[field] else None
            contrasts.append(c)
    assert len(contrasts)==864
    with (OUT/'contrasts.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(contrasts[0]));w.writeheader();w.writerows(contrasts)
    groups=defaultdict(list)
    for r in contrasts:
        if r['population']=='full_schedule' and r['relation']!='cross_profile':groups[r['phase'],r['profile'],r['subset'],r['relation']].append(r)
    summaries=[]
    for (phase,profile,subset,relation),rows in sorted(groups.items()):
        assert len(rows)==12
        signs=lambda field,positive_good:dict(Counter('unchanged' if r[field]==0 else 'improved' if (r[field]>0)==positive_good else 'regressed' for r in rows))
        summaries.append(dict(phase=phase,profile=profile,subset=subset,relation=relation,hit_horizons=signs('hits_delta',True),mae_horizons=signs('mae_m_delta',False)))
    result=dict(source_manifest_sha256=sha(SOURCE/'artifact-hashes.json'),contrasts=len(contrasts),summary=summaries,independent_test=False,promoted=False,goal_achieved=False)
    (OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Exposição controlada à ausência do Carreiro','',
           'A única alteração é tornar NaN os seis campos do Carreiro em uma seleção fixa de origens do treino, com probabilidade25% e PCG64(58). Mesmas amostras, ordem, pesos, alvos,180colunas e configurações da mistura anterior; uma linha por origem. Avaliação nos dados reais originais, sem mascaramento adicional. Não simula duração ou causa das falhas, nem demonstra causalidade. Períodos já conhecidos de desenvolvimento.','',
           'Recorte observado >=7 m, todos os horários. Falhas no denominador. Erros em metros.','',
           '| Corte | Perfil | h | Acertos mistura → com exposição / alvos | Controle do perfil: acertos | MAE original → com exposição | Máximo original → com exposição |',
           '|---|---|---:|---:|---:|---:|---:|']
    for r in contrasts:
        if r['relation']=='primary_unmasked' and r['population']=='full_schedule' and r['subset']=='level_ge_7m' and r['horizon_h'] in (1,6,12):
            control=lookup[r['phase'],r['profile'],str(r['horizon_h']),'full_schedule','level_ge_7m',f"profile_{r['profile']}_control"]
            lines.append(f"| {r['phase']} | {r['profile']} | {r['horizon_h']} | {r['reference_hits']} → {r['exposed_hits']} / {r['observed_targets']} | {control['hits']} | {r['reference_mae_m']:.4f} → {r['exposed_mae_m']:.4f} | {r['reference_max_abs_m']:.4f} → {r['exposed_max_abs_m']:.4f} |")
    lines+=['','Comparações completas contra a mistura, contra o controle do perfil e contra o controle cruzado estão no CSV. Melhorar a mistura anterior não implica superar o controle dedicado. Não selecionar perfis ou horizontes favoráveis. Nenhuma promoção ou comprovação da meta de 98%.','']
    (OUT/'README.md').write_text('\n'.join(lines))
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
