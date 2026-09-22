"""Frozen chronological ridge experiment with additional September2023 flows.

Uses no Muçum peak target, does not mutate source files, and never promotes or
issues a live candidate. Historical publication delay is an explicit assumption.
"""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import BASE,ROOT,epoch,iso,dump,ridge_fit
from hydro_hourly_models import upstream_features
from hydro_routing_fit import shift
from hydro_upstream_audit import metrics,predict_many,savecsv
from hydro_upstream_tree_experiment import partitions,same_time_observation

PLANTS={'julho':'JIUHQJ','monte':'JIUHMC','castro':'JIUHCA'}


def numeric(value,negative_allowed=False):
    try:result=float(value)
    except (TypeError,ValueError):return np.nan
    return result if np.isfinite(result) and (negative_allowed or result>=0) else np.nan


def prepare_2023(rows,times):
    """Delay inputs60min, cap as-of age90min, require exact whole-hour targets."""
    times=np.asarray(times,dtype=float)
    if len(times)>1 and not np.all(np.diff(times)==3600):raise ValueError('Consecutive hourly grid required')
    columns=[];known=None;truth=np.full(len(times),np.nan);traces=[]
    for plant,identifier in PLANTS.items():
        selected={}
        for row in rows:
            if row['id_reservatorio']!=identifier:continue
            at=epoch(row['din_instante'])
            if at in selected:raise ValueError('Duplicate ONS plant/time, including identical repeats')
            selected[at]=row
        if not selected:raise ValueError('Missing required CERAN plant')
        stamps=np.array(sorted(selected));cutoff=times-3600
        ix=np.searchsorted(stamps,cutoff,side='right')-1
        safe=np.maximum(ix,0);age=cutoff-stamps[safe]
        usable=(ix>=0)&(age<=5400)&(age>=0)
        if np.any(stamps[safe][usable]>cutoff[usable]):raise ValueError('Future feature input')
        for variable,field in [('Q','val_vazaodefluente'),('I','val_vazaoafluente')]:
            values=np.array([numeric(selected[t].get(field),variable=='I')/1000 for t in stamps])
            a=np.where(usable,values[safe],np.nan)
            columns.extend([a,a-shift(a,1),(a-shift(a,3))/3,(a-shift(a,6))/6])
            if plant=='julho' and variable=='Q':
                known=a
                lookup={at:value for at,value in zip(stamps,values) if at%3600==0}
                truth=np.array([lookup.get(at,np.nan) for at in times])
            for i in range(len(times)):
                traces.append({'plant':plant,'variable':variable,'origin':iso(times[i]),'assumed_available_before':iso(cutoff[i]),'source_time':iso(stamps[safe[i]]) if ix[i]>=0 else '', 'source_age_minutes_after_delay':float(age[i]/60) if ix[i]>=0 else '', 'usable_input':bool(usable[i] and np.isfinite(a[i]))})
    return np.column_stack(columns),known,truth,traces


def run(out,protocol_path):
    protocol=json.loads(protocol_path.read_text())
    if protocol['ridge_alpha']!=1000 or protocol['leads_h']!=list(range(12)):
        raise ValueError('This implementation requires the preregistered fixed parameters')
    source=ROOT/protocol['current_diagnostic_snapshot'];archive=ROOT/protocol['source_2023']
    # Verify the delivered extraction against the research artifact manifest.
    manifest=json.loads((archive.parent/'artifact-hashes.json').read_text())
    expected=next(r['sha256'] for r in manifest if r['file']==archive.name)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:raise ValueError('2023 extraction was modified')
    with archive.open() as f:raw=list(csv.DictReader(f))
    at=np.arange(epoch('2023-09-01T00:00:00-03:00'),epoch('2023-10-01T00:00:00-03:00'),3600.)
    AF,AK,AQ,trace=prepare_2023(raw,at)
    d=dict(np.load(BASE/'dados-roteamento.npz'));z=dict(np.load(BASE/'telemetria-latencia.npz'))
    nd=dict(np.load(source/'dados-roteamento.npz'));nz=dict(np.load(source/'telemetria-latencia.npz'))
    t=d['times'];F=upstream_features(z,t);NF=upstream_features(nz,nd['times'])[-1:]
    known=z['julho:Q'][np.searchsorted(z['times'],t)]/1000;latest=nz['julho:Q'][-1]/1000
    high=float(np.nanquantile(d['julho'][t<epoch(protocol['splits']['validation_training_targets_before'])],.95))
    if not np.isfinite(latest):raise ValueError('Current reference unavailable')
    out.mkdir(parents=True,exist_ok=False);(out/'protocol.json').write_bytes(protocol_path.read_bytes())
    savecsv(out/'2023-input-trace.csv',trace)
    np.savez_compressed(out/'2023-training-inputs.npz',times=at,features=AF,known=AK,target_exact=AQ)
    allF=np.vstack([F[:,:24],AF]);evals=[];current=[];predictions=[];membership=[];models={}
    for lead in protocol['leads_h']:
        target=shift(d['julho'],-lead);delta=target-known;idx=partitions(t,target,known,lead)
        added_target=shift(AQ,-lead);added_delta=added_target-AK
        added=np.where(np.isfinite(added_target)&np.isfinite(AK))[0]
        if np.any(at[added]+lead*3600>=epoch('2023-10-01T00:00:00-03:00')):raise ValueError('Added target outside collection')
        membership.append({'lead_h':lead,'added_training_rows':len(added),'added_first_target':iso((at[added]+lead*3600).min()),'added_last_target':iso((at[added]+lead*3600).max()),'added_max_target_m3_s':float(added_target[added].max()*1000)})
        augmented_y=np.r_[delta,added_delta];weights=1+2*(target>2)
        augmented_weights=np.r_[weights,1+2*(added_target>2)]
        for family in ['reference_full','reference_ceran_only','augmented_ceran_2023']:
            for phase,train,apply in [('validation',idx['train'],idx['validation']),('test',idx['pretest'],idx['test']),('current',idx['final'],None)]:
                if family=='augmented_ceran_2023':
                    trainX,trainY,trainW,trainI=allF,augmented_y,augmented_weights,np.r_[train,len(t)+added]
                else:
                    trainX=F if family=='reference_full' else F[:,:24]
                    trainY,trainW,trainI=delta,weights,train
                model=ridge_fit(trainX,trainY,trainI,1000.,trainW)
                features=NF if apply is None else F[apply]
                if family!='reference_full':features=features[:,:24]
                base=latest if apply is None else known[apply]
                pred=np.maximum(base+predict_many(model,features),0)
                if phase=='current':
                    observed=same_time_observation(source,nz,'julho:Q',nd['times'][-1])
                    unanchored=float(pred[0])
                    if lead==0 and np.isfinite(observed):pred[0]=observed
                    current.append({'lead_h':lead,'family':family,'forecast_m3_s':float(pred[0]*1000),'unanchored_m3_s':unanchored*1000,'training_rows':len(trainI)})
                    models[f'{family}:{lead}']={k:v.tolist() if isinstance(v,np.ndarray) else float(v) for k,v in model.items()}
                else:
                    for subset,values in metrics(pred,target[apply],target[apply]>=high).items():
                        evals.append({'lead_h':lead,'family':family,'phase':phase,'subset':subset,'training_rows':len(trainI),**values})
                    for i,p in zip(apply,pred):predictions.append({'lead_h':lead,'family':family,'phase':phase,'origin':iso(t[i]),'target_time':iso(t[i]+lead*3600),'actual_m3_s':float(target[i]*1000),'forecast_m3_s':float(p*1000),'high_flow':bool(target[i]>=high)})
        print('lead',lead,'complete',flush=True)
    for name,rows in [('evaluation',evals),('current',current),('predictions',predictions),('added-training-membership',membership)]:savecsv(out/f'{name}.csv',rows)
    dump(out/'frozen-models.json',models)
    code=[Path(__file__),ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_routing_fit.py',ROOT/'scripts/hydro_upstream_audit.py',ROOT/'scripts/hydro_upstream_tree_experiment.py']
    (out/'code').mkdir()
    for p in code:(out/'code'/p.name).write_bytes(p.read_bytes())
    inputs=[archive,archive.parent/'artifact-hashes.json',protocol_path,BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',source/'dados-roteamento.npz',source/'telemetria-latencia.npz',source/'idades-fontes.csv',*code]
    dump(out/'experiment.json',{'input_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'high_flow_threshold_m3_s':high*1000,'source_snapshot':str(source),'2023_exact_targets':int(np.isfinite(AQ).sum()),'clock_and_latency':'UTC-03 and60min availability assumed, not historical real-time evidence','reference':'Frozen15h latency history, not active hourly refitted models','status':'Inspected development periods; no independent validation or candidate promotion','live_issuance':False,'promoted':False,'goal_achieved':False})
    print(json.dumps({'output':str(out),'models_saved':len(models),'added_rows':membership}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--protocol',type=Path,default=ROOT/'docs/upstream-2023-augmentation-protocol.json');a=p.parse_args()
    with threadpool_limits(limits=2):run(a.output,a.protocol)
