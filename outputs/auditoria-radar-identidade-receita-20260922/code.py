"""Audit declared recipe equivalence of sealed regular Radar issues; no fit."""
import csv,hashlib,json,sys
from collections import defaultdict
from pathlib import Path
import joblib
import hydro_prospective_ledger as ledger

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/auditoria-radar-identidade-receita-20260922'
def digest(data):return hashlib.sha256(data).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def main():
    assert not OUT.exists()
    records=ledger.read_records(ledger.DEFAULT)
    issues=[r for r in records if r['kind']=='forecast_issue' and r['payload']['model_id']=='radar_arvores_live_candidate' and not r['payload'].get('manual_revision')]
    assert issues
    artifacts=0;models=0;rows=[];details=[];by_version=defaultdict(list)
    for issue in issues:
        p=issue['payload'];code={};params={};model_hashes={};unsealed=[];skipped=[]
        for a in p['model_artifacts']:
            name=Path(a['path']).name
            if name.endswith('.joblib') and not name.startswith('radar-'):
                skipped.append(name)
                continue  # Retired shared-packet models are never loaded.
            if 'blob' not in a:
                unsealed.append(name)
                continue  # Do not substitute current paths for missing sealed evidence.
            path=ledger.DEFAULT/a['blob'];assert digest(path.read_bytes())==a['sha256'];artifacts+=1
            if name.endswith('.joblib'):
                model=joblib.load(path);params[name]=model.get_params();model_hashes[name]=a['sha256'];models+=1
            else:
                assert name not in code;code[name]=a['sha256']
        recipe=dict(model_id=p['model_id'],training_cutoff=p['training_cutoff'],declared_code_and_requirements_sha256=code,
            declared_runtime_versions=p.get('runtime_versions'),fitted_estimator_parameters=params,
            station_id=p['station_id'],datum_id=p['datum_id'])
        identity=digest(canonical(recipe)) if not unsealed and params else None
        weights_identity=digest(canonical(model_hashes)) if not unsealed and params else None
        item=dict(receipt=issue['sha256'],issued_at=issue['recorded_at'],reference_at=p['reference_at'],model_version=p['model_version'],
            declared_recipe_sha256=identity,fitted_model_set_sha256=weights_identity,code_artifacts=len(code),model_artifacts=len(params),
            has_runtime_versions=bool(p.get('runtime_versions')),training_cutoff=p['training_cutoff'],unsealed_required_artifacts=len(unsealed),non_radar_models_skipped=len(skipped))
        rows.append(item);details.append(dict(**item,recipe=recipe,model_sha256=model_hashes,unsealed_names=unsealed,non_radar_skipped_names=skipped));by_version[p['model_version']].append(item)
    groups=[]
    for version,items in sorted(by_version.items()):
        known=[r for r in items if r['declared_recipe_sha256']]
        recipe_count=len({r['declared_recipe_sha256'] for r in known});weights_count=len({r['fitted_model_set_sha256'] for r in known})
        groups.append(dict(model_version=version,regular_issues=len(items),declared_recipe_variants=recipe_count,fitted_model_set_variants=weights_count,
            unverifiable_issues=len(items)-len(known),same_declared_recipe=recipe_count==1 if len(known)==len(items) else None,all_runtime_recorded=all(r['has_runtime_versions'] for r in items),receipts=[r['receipt'] for r in items]))
    OUT.mkdir();(OUT/'code.py').write_bytes(Path(__file__).read_bytes())
    with (OUT/'issues.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    dump(OUT/'recipe-details.json',details)
    summary=dict(ledger_tip_sha256=records[-1]['sha256'],ledger_records=len(records),regular_issues=len(issues),artifacts_verified=artifacts,models_inspected=models,
        version_groups=groups,source_code_sha256=digest(Path(__file__).read_bytes()),fit_performed=False,report_or_ledger_modified=False,goal_achieved=False,
        limitations=['Compares only code, runtime and settings declared/preserved in the packets; not proof of a complete transitive dependency inventory.',
        'Legacy packets lacking artifact blobs are explicitly unverifiable; current filesystem paths are not substituted. Non-Radar models from former shared packets are never loaded.',
        'The operational model_version hashes the main runner only. This audit does not change or backdate that identifier.',
        'Different fitted weights and historical feature matrices are expected from the documented dynamic source-delay policy, despite a fixed label cutoff.',
        'Static external parameter files are not automatically certified by equality of this recipe signature. Actual estimator parameters are inspected from sealed models.',
        'Recipe equality is not prediction equality, equivalent data quality, source publication proof, independent validation or 98% accuracy.'])
    dump(OUT/'audit.json',summary)
    lines=['# Identidade declarada das receitas de previsão','',
        'Auditoria somente de emissões regulares Radar, a partir de recibos e blobs selados. Revisões manuais e importações antigas não entram. Sem ajuste, inferência, alteração do registro ou agrupamento retroativo de versões.','',
        '| Versão | Emissões regulares | Não verificáveis | Receitas declaradas distintas | Conjuntos Radar distintos | Runtime em todas |','|---|---:|---:|---:|---:|---|']
    for g in groups:lines.append(f"| {g['model_version']} | {g['regular_issues']} | {g['unverifiable_issues']} | {g['declared_recipe_variants']} | {g['fitted_model_set_variants']} | {g['all_runtime_recorded']} |")
    lines+=['','A assinatura compara hashes dos códigos/requisitos declarados, versões do runtime, corte de treino, estação/referência e parâmetros dos estimadores lidos dos modelos selados. Não inclui os pesos ajustados na identidade da receita: cada conjunto de pesos permanece rastreado separadamente.','',*['- '+s for s in summary['limitations']],'']
    (OUT/'README.md').write_text('\n'.join(lines))
    dump(OUT/'artifact-hashes.json',[dict(file=p.name,sha256=digest(p.read_bytes())) for p in sorted(OUT.iterdir()) if p.is_file()])
    print(json.dumps({k:v for k,v in summary.items() if k!='limitations'}))

if __name__=='__main__':main()
