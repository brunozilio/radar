"""Describe historical extreme errors without training, filtering or attribution claims."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import epoch, iso
from hydro_radar_native_missing import training_masks
from hydro_routing_fit import shift

OUT = Path(__file__).resolve().parent
RUN = ROOT/'outputs/experimento-radar-ausencias-reservatorios-20260921'
LEVELS = ROOT/'outputs/experimento-radar-niveis-reservatorios-20260921'
FAMILIES = ['baseline','native_only','reservoir_only','combined']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name,rows):
    with (OUT/name).open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def read(path):
    return list(csv.DictReader(path.open()))


def run():
    for folder,name in [(RUN,'predictions.csv'),(LEVELS,'features.npz')]:
        manifest=json.loads((folder/'artifact-hashes.json').read_text())
        assert sha(folder/name)==next(r['sha256'] for r in manifest if r['file']==name)
    data=dict(np.load(LEVELS/'features.npz'))
    t,F,base,truth,complete=(data[k] for k in ('times','features','base','truth','complete24'))
    rows=read(RUN/'predictions.csv')
    indices={iso(at):i for i,at in enumerate(t)}
    ranges=[];strata=[];detail=[];daily=[]
    for h in range(1,13):
        target=shift(truth,-h);delta=target-base
        masks=training_masks(t,base,target,complete,h,epoch('2025-10-01T00:00:00-03:00'),epoch('2026-07-01T00:00:00-03:00'))
        for phase in ('validation','test'):
            selected=[r for r in rows if r['phase']==phase and int(r['nominal_lead_h'])==h]
            for policy in ('baseline','candidate'):
                ix=np.where(masks[phase,policy])[0]
                a,b=ix[np.argmin(delta[ix])],ix[np.argmax(delta[ix])]
                ranges.append(dict(phase=phase,horizon_h=h,training_policy=policy,n=len(ix),
                    min_delta_m=float(delta[a]),max_delta_m=float(delta[b]),
                    min_origin=iso(t[a]),max_origin=iso(t[b]),max_base_m=float(base[b]),max_target_m=float(target[b]),
                    q99_delta_m=float(np.quantile(delta[ix],.99))))
            for family in FAMILIES:
                policy='candidate' if family in ('native_only','combined') else 'baseline'
                train=np.where(masks[phase,policy])[0]
                low,high=float(delta[train].min()),float(delta[train].max())
                pairs=[]
                for row in selected:
                    if not row['actual_m'] or not row[family+'_m']:
                        continue
                    i=indices[row['origin']]
                    observed=float(row['actual_m']);pred=float(row[family+'_m'])
                    assert observed==target[i]
                    regime='above_train_max' if delta[i]>high else 'below_train_min' if delta[i]<low else 'within_train_range'
                    item=dict(phase=phase,horizon_h=h,family=family,origin=row['origin'],target_time=row['target_time'],
                        base_m=float(base[i]),observed_m=observed,prediction_m=pred,error_m=pred-observed,
                        response_m=float(delta[i]),predicted_response_m=pred-float(base[i]),response_regime=regime,
                        missing_first24=int((~np.isfinite(F[i,:24])).sum()),
                        missing_carreiro6=int((~np.isfinite(F[i,18:24])).sum()),
                        missing_reservoir24=int((~np.isfinite(F[i,180:])).sum()))
                    pairs.append(item)
                for subset in ('all','level_ge_7m'):
                    for regime in ('above_train_max','below_train_min','within_train_range'):
                        g=[r for r in pairs if r['response_regime']==regime and (subset=='all' or r['observed_m']>=7)]
                        errors=np.array([r['error_m'] for r in g]);ae=abs(errors)
                        strata.append(dict(phase=phase,horizon_h=h,family=family,subset=subset,regime=regime,n=len(g),
                            hits=int((ae<=.5).sum()),mae_m=float(ae.mean()) if len(g) else None,
                            bias_m=float(errors.mean()) if len(g) else None,max_error_m=float(ae.max()) if len(g) else None))
                if phase=='test' and h==12:
                    detail.extend(sorted(pairs,key=lambda r:abs(r['error_m']),reverse=True)[:20])
                    total=sum(abs(r['error_m']) for r in pairs)
                    for day in sorted(set(r['target_time'][:10] for r in pairs)):
                        g=[r for r in pairs if r['target_time'].startswith(day)]
                        error=np.array([r['error_m'] for r in g])
                        daily.append(dict(family=family,target_day=day,n=len(g),high_targets=sum(r['observed_m']>=7 for r in g),
                            absolute_error_sum_m=float(abs(error).sum()),fraction_total_absolute_error=float(abs(error).sum()/total),
                            mae_m=float(abs(error).mean()),max_error_m=float(abs(error).max()),
                            missing_carreiro6=sum(r['missing_carreiro6']==6 for r in g)))
    # Trace the entire selected failure window; this is a posthoc diagnostic,
    # never a newly independent holdout or a reason to exclude those rows.
    feature_names=[]
    for station in ['86510000','86472000','86472600','86500000']:
        feature_names += [station+':H']+[station+':dH'+str(h) for h in (.5,1,2,4,8)]
    for plant in ['julho','monte','castro']:
        feature_names += [plant+':Q06',plant+':Q',plant+':I']+[plant+':dQ'+str(h) for h in (1,2,4,8)]
    for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
        feature_names += [group+':'+kind+str(h) for h in (1,3,6,12,24,48) for kind in ('P','C')]
        feature_names += [group+':P3lag'+str(h) for h in (3,6,12)]
    for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
        for loc in range(5):
            feature_names += [f'{model}:loc{loc}:futureP{h}' for h in (3,6,9,12)]
    for plant in ['julho','monte','castro']:
        for field in ['val_nivelmontante','val_niveljusante']:
            feature_names += [f'{plant}:{field}:{kind}' for kind in ['level','change1','slope3','slope6']]
    assert len(feature_names)==F.shape[1]
    window=np.where((t>=epoch('2026-07-21T12:00:00-03:00'))&(t<=epoch('2026-07-21T23:00:00-03:00')))[0]
    trace=[dict(origin=iso(t[i]),column=j,name=name,value=float(F[i,j]) if np.isfinite(F[i,j]) else None) for i in window for j,name in enumerate(feature_names)]
    save('training-response-ranges.csv',ranges);save('response-strata.csv',strata)
    save('largest-errors.csv',detail);save('daily-errors-12h.csv',daily);save('july-input-window.csv',trace)
    summary=dict(rows=len(rows),range_records=len(ranges),strata_records=len(strata),feature_trace_rows=len(trace),
        diagnostic_selection='Largest12h errors selected after inspecting results; not an independent evaluation set.',
        causal_attribution_proven=False,trained=False,promoted=False,goal_achieved=False,
        input_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),RUN/'predictions.csv',LEVELS/'features.npz',ROOT/'scripts/hydro_radar_native_missing.py',ROOT/'scripts/hydro_routing_fit.py']})
    (OUT/'diagnostic.json').write_text(json.dumps(summary,indent=2)+'\n')
    for h in (1,6,12):
        print('TRAIN',*[r for r in ranges if r['phase']=='test' and r['horizon_h']==h],sep='\n')
        print('STRATA',*[r for r in strata if r['phase']=='test' and r['horizon_h']==h and r['family']=='combined' and r['subset']=='level_ge_7m'],sep='\n')
    print('DAYS',*sorted([r for r in daily if r['family']=='combined'],key=lambda r:r['absolute_error_sum_m'],reverse=True)[:5],sep='\n')


if __name__=='__main__':run()
