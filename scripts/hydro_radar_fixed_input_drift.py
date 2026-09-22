"""Saved-model drift at fixed inputs; counterfactual only, never a new issue."""
import csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import joblib,numpy as np
from threadpoolctl import threadpool_limits
import hydro_prospective_ledger as ledger

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'outputs/mucum-hourly-20260922T010016-0300'
NEW=ROOT/'outputs/mucum-hourly-20260922T020011-0300'
OUT=ROOT/'outputs/diagnostico-radar-pesos-inputs-fixos-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    assert not OUT.exists()
    records=ledger.read_records(ledger.DEFAULT);lookup={r['sha256']:r for r in records}
    datasets={};issues={};paths=[Path(__file__)];controlpaths={}
    for tag,folder in (('old',OLD),('new',NEW)):
        r=json.loads((folder/'run-result.json').read_text());assert len(r['forecasts'])==1
        issue=lookup[r['forecasts'][0]['receipt_sha256']];p=issue['payload']
        assert p['model_id']=='radar_arvores_live_candidate' and not p.get('manual_revision')
        artifacts={Path(a['path']).name:a for a in p['model_artifacts']}
        controls=[]
        for h in range(1,15):
            path=folder/'models'/f'radar-{h}.joblib';a=artifacts[path.name]
            assert sha(path)==a['sha256']==sha(ledger.DEFAULT/a['blob'])
            paths.append(path);controls.append(path)
        feature=folder/'radar-features.npz'
        receipt=next(lookup[x] for x in p['input_receipts'] if lookup[x]['payload'].get('source_path')==str(feature))
        assert sha(feature)==receipt['payload']['blob_sha256']==sha(ledger.DEFAULT/receipt['payload']['blob'])
        datasets[tag]=dict(np.load(feature));issues[tag]=issue;controlpaths[tag]=controls
        paths.extend((feature,folder/'run-result.json',folder/'receipt-verification.json'))
    assert issues['old']['payload']['model_version']==issues['new']['payload']['model_version']
    assert issues['old']['payload']['training_cutoff']==issues['new']['payload']['training_cutoff']
    assert issues['old']['payload']['runtime_versions']==issues['new']['payload']['runtime_versions']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    OUT.mkdir()
    dump(OUT/'plan.json',dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,
        scope='Apply both sealed model sets at the old and new fixed180feature vectors in each nominal horizon1..14. Only same-model/same-origin diagonal values are issued predictions. Reusing old models at the new vector is an unissued counterfactual.',
        caution='The two origins with the same nominal horizon correspond to different target times. Do not label their difference as a same-target revision, forecast error, accuracy gain or confidence interval. No calibration, fit, promotion, ledger append or parameter choice.',
        planned_models_loaded=28,planned_scalar_predictions=56))
    rows=[];equality=[]
    for h in range(1,15):
        models={tag:joblib.load(controlpaths[tag][h-1]) for tag in ('old','new')}
        assert models['old'].get_params()==models['new'].get_params()
        x=np.vstack([datasets[tag]['features'][-1] for tag in ('old','new')])
        b=np.array([datasets[tag]['base'][-1] for tag in ('old','new')])
        values={tag:models[tag].predict(x)+b for tag in ('old','new')}
        for j,tag in enumerate(('old','new')):
            point=next(p for p in issues[tag]['payload']['points'] if p['nominal_lead_h']==h)
            # Batched vs single-row inference must agree exactly for the issued diagonal.
            assert float(values[tag][j])==point['level_m']
            equality.append(dict(origin=tag,horizon_h=h,issued_m=point['level_m'],reproduced_m=float(values[tag][j])))
            rows.append(dict(input_origin=tag,input_reference_at=issues[tag]['payload']['reference_at'],target_at=point['valid_at'],nominal_lead_h=h,
                input_base_m=float(b[j]),old_model_m=float(values['old'][j]),new_model_m=float(values['new'][j]),
                fitted_model_change_at_fixed_input_m=float(values['new'][j]-values['old'][j]),
                issued_model=tag,other_value_is_unissued_counterfactual=True))
    for filename,data in (('fixed-input-comparison.csv',rows),('issued-reproduction.csv',equality)):
        with (OUT/filename).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    summary=dict(finished_at_utc=datetime.now(timezone.utc).isoformat(),old_issue=issues['old']['sha256'],new_issue=issues['new']['sha256'],
        diagonal_predictions_exact=len(equality),scalar_predictions=56,models_loaded=28,model_parameters_equal=True,
        largest_effect_at_new_input=max((r for r in rows if r['input_origin']=='new'),key=lambda r:abs(r['fitted_model_change_at_fixed_input_m'])),
        largest_effect_at_old_input=max((r for r in rows if r['input_origin']=='old'),key=lambda r:abs(r['fitted_model_change_at_fixed_input_m'])),
        new_input_effects_gt_0_50m=sum(abs(r['fitted_model_change_at_fixed_input_m'])>.5 for r in rows if r['input_origin']=='new'),
        input_sha256=hashes,fit_performed=False,forecast_issued=False,promoted=False,goal_achieved=False)
    for path,digest in hashes.items():assert sha(ROOT/path)==digest
    # No report/capture/registration calls occurred; the existing ledger tail is untouched.
    assert ledger.read_records(ledger.DEFAULT)[-1]['sha256']==records[-1]['sha256']
    dump(OUT/'analysis.json',summary);(OUT/'code.py').write_bytes(Path(__file__).read_bytes())
    lines=['# Variação de pesos nos mesmos inputs','',
        'Comparação descritiva de dois conjuntos de modelos Radar já emitidos. Nenhum ajuste ou previsão nova foi registrada. Nas linhas abaixo, ambos os modelos recebem exatamente os mesmos180campos e a mesma base das02h. O valor do modelo das01h é um contrafactual não emitido.','',
        '| h nominal | Alvo a partir das02h | Modelo anterior | Modelo atual emitido | Efeito da troca de pesos |','|---:|---|---:|---:|---:|']
    for r in rows:
        if r['input_origin']=='new':lines.append(f"| {r['nominal_lead_h']} | {r['target_at']} | {r['old_model_m']:.4f} | {r['new_model_m']:.4f} | {r['fitted_model_change_at_fixed_input_m']:+.4f} |")
    lines+=['','As28diagonais (modelo/origem correspondentes) reproduzem exatamente as emissões originais. Parâmetros, versão declarada, runtime e corte são iguais entre os conjuntos.','',
        'Isso mede apenas o efeito computacional de trocar os modelos salvos com os inputs fixos. Não prova qual previsão é melhor. Aplicar pesos antigos a outra configuração de atraso pode criar desalinhamento; não foi escolhido para operação.','',
        'Ao comparar origens01h/02h no mesmo horizonte nominal, os alvos são diferentes. Não somar esta tabela à revisão por mesmo alvo sem uma decomposição que preserve os horizontes. H13/14 reutilizam parâmetros de12h e não são validação adicional de precisão.','']
    (OUT/'README.md').write_text('\n'.join(lines))
    dump(OUT/'artifact-hashes.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file()])
    print(json.dumps({k:v for k,v in summary.items() if k!='input_sha256'}))

if __name__=='__main__':
    with threadpool_limits(limits=2):main()
