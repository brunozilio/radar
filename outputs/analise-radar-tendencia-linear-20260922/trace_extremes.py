"""Decompose largest12h hybrid errors without changing or selecting a model."""
import csv, hashlib, json
from datetime import datetime
from pathlib import Path
import joblib, numpy as np
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'outputs/experimento-radar-tendencia-linear-20260922'
PARENT=ROOT/'outputs/experimento-radar-mistura-atrasos-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    for item in json.loads((SOURCE/'artifact-hashes.json').read_text()):assert sha(SOURCE/item['file'])==item['sha256']
    data=dict(np.load(PARENT/'prepared-inputs.npz'))
    rows=list(csv.DictReader((SOURCE/'predictions.csv').open()))
    bundle=joblib.load(SOURCE/'models/test-12.joblib')
    cases=[];contributions=[]
    for profile in ('A','B'):
        chosen=[r for r in rows if r['phase']=='test' and r['profile']==profile and r['nominal_lead_h']=='12' and r['actual_m'] and r['linear_trend_hybrid_m']]
        chosen.sort(key=lambda r:-abs(float(r['linear_trend_hybrid_m'])-float(r['actual_m'])))
        for rank,r in enumerate(chosen[:3],1):
            i=int(np.searchsorted(data['times'],datetime.fromisoformat(r['origin']).timestamp()))
            x=data['features_'+profile][i];slopes=x[bundle['indices']]
            imputed=np.where(np.isfinite(slopes),slopes,bundle['median'])
            standardized=bundle['scaler'].transform(imputed[None,:])[0]
            contributions_m=standardized*bundle['ridge'].coef_
            linear=float(bundle['ridge'].intercept_+contributions_m.sum())
            tree=float(bundle['tree'].predict(x[None,:])[0])
            base=float(r['base_m']);predicted=base+linear+tree
            assert abs(predicted-float(r['linear_trend_hybrid_m']))<1e-12
            assert abs(base+linear-float(r['linear_trend_only_m']))<1e-12
            cases.append(dict(profile=profile,rank=rank,origin=r['origin'],target_time=r['target_time'],base_m=base,actual_m=float(r['actual_m']),hybrid_m=predicted,
                mixed_tree_only_m=float(r['mixed_profile_candidate_m']),linear_delta_m=linear,residual_tree_delta_m=tree,
                ridge_intercept_m=float(bundle['ridge'].intercept_),missing_slope_columns=','.join(str(int(c)) for c in bundle['indices'][~np.isfinite(slopes)]),
                mucum_dH1_m_per_nominal_hour=float(x[2]) if np.isfinite(x[2]) else None,
                hybrid_error_m=predicted-float(r['actual_m']),mixed_error_m=float(r['mixed_profile_candidate_m'])-float(r['actual_m'])))
            for k,col in enumerate(bundle['indices']):
                contributions.append(dict(profile=profile,rank=rank,origin=r['origin'],column=int(col),raw_value=float(slopes[k]) if np.isfinite(slopes[k]) else None,
                    used_value=float(imputed[k]),was_imputed=bool(not np.isfinite(slopes[k])),standardized_value=float(standardized[k]),coefficient=float(bundle['ridge'].coef_[k]),contribution_m=float(contributions_m[k])))
    save('largest12h-cases.csv',cases);save('largest12h-linear-contributions.csv',contributions)
    with (OUT/'README.md').open('a') as f:
        f.write('\n## Limitações observadas\n\nNas cheias de test, o híbrido melhora MAE nos 12 horizontes dos dois perfis e acertos em 11, mas perde cinco acertos em 6h em cada perfil. No conjunto de todos os níveis contra a mistura, há menos acertos em sete horizontes de A e quatro de B. Na validation de cheia, perde acertos em cinco horizontes de A e seis de B. Não há ganho sustentado em todos os recortes.\n\nEm test/12h, o pior erro aumenta de 7,7928 para 8,9919m no perfil A e de 7,6069 para 8,9139m em B. São subestimações na subida de julho, não excesso de nível gerado por extrapolação linear. No pior A, origem21/07 às16h, base3,27m e alvo14,49m: ridge acrescenta0,6689m, árvore de resíduos1,5592m e o híbrido prevê5,4981m (mistura anterior6,6972m). As cinco tendências do Carreiro estão ausentes e são imputadas por medianas só para ridge; a árvore mantém os NaNs originais. Isso descreve o cálculo, não identifica causalidade da falta. Os seis maiores casos e as120contribuições estão nos CSVs.\n\nO acerto de 233/237 em1h (98,31%) é um resultado histórico de desenvolvimento em uma antecedência nominal, com uma falha no denominador. Não prova a meta prospectiva em1–12h nem dez cheias independentes. Sem promoção, troca de horizonte, recorte favorável ou novo ajuste após os resultados.\n')
    (OUT/'extreme-trace.json').write_text(json.dumps(dict(cases=len(cases),contributions=len(contributions),source_manifest_sha256=sha(SOURCE/'artifact-hashes.json'),matrix_sha256=sha(PARENT/'prepared-inputs.npz'),fit=False,promoted=False),indent=2)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps(cases))

if __name__=='__main__':
    with threadpool_limits(limits=2):main()
