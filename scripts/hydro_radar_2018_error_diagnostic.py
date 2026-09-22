"""Explain frozen paired errors without refitting, filtering failures or promotion."""
import csv, hashlib, json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/experimento-radar-historico-2018-119-20260922'
MATRIX=ROOT/'outputs/radar-matriz-recente-ancora-horaria-20260922/features.npz'
OUT=ROOT/'outputs/diagnostico-erros-radar-2018-20260922-v2'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def numeric(v):return float(v) if v else None

def summarize(rows):
    observed=[r for r in rows if r['actual_m'] is not None]
    paired=[r for r in observed if r['control_m'] is not None and r['augmented_m'] is not None]
    ce=np.array([r['control_m']-r['actual_m'] for r in paired]);ae=np.array([r['augmented_m']-r['actual_m'] for r in paired])
    ch=abs(ce)<=.5;ah=abs(ae)<=.5
    return {'scheduled_rows':len(rows),'observed':len(observed),'unknown_truth':len(rows)-len(observed),'pairs':len(paired),'failures':len(observed)-len(paired),
        'both_hit':int((ch&ah).sum()),'hit_to_miss':int((ch&~ah).sum()),'miss_to_hit':int((~ch&ah).sum()),'both_miss':int((~ch&~ah).sum()),
        'control_hits':int(ch.sum()),'augmented_hits':int(ah.sum()),
        'control_mae':float(np.mean(abs(ce))) if len(ce) else None,'augmented_mae':float(np.mean(abs(ae))) if len(ae) else None,
        'sum_absolute_error_change':float((abs(ae)-abs(ce)).sum()) if len(ce) else 0,
        'control_under_halfmeter':int((ce<-.5).sum()),'augmented_under_halfmeter':int((ae<-.5).sum()),
        'control_over_halfmeter':int((ce>.5).sum()),'augmented_over_halfmeter':int((ae>.5).sum())}


def run():
    OUT.mkdir(exist_ok=False)
    paths=[SOURCE/'predictions.csv',SOURCE/'evaluation.csv',SOURCE/'artifact-hashes.json',MATRIX,Path(__file__)]
    for entry in json.loads((SOURCE/'artifact-hashes.json').read_text()):assert sha(SOURCE/entry['file'])==entry['sha256']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    dump(OUT/'plan.json',{'created_at_utc':datetime.now(timezone.utc).isoformat(),'input_sha256':hashes,
        'scope':'Post-result diagnostic of every frozen paired forecast. No new model fit, inference, promotion or changed tolerance.',
        'axes':{'target_level':'below7,[7,9),atleast9,unknown; diagnostic future truth, never selectable at issuance.',
                'known_trend':'Muçum dH1 original feature2, rise>=0.1m/h,fall<=-0.1m/h,otherwise stable,unknown separately; no rounding.',
                'upstream':'Original18upstream level/trend fields6..23 allfinite or missing.',
                'transition':'Both hit,hit-to-miss,miss-to-hit,bothmiss; missingtruth/missingforecast separate; hit iff absolute error<=0.50m before rounding.'},
        'subsets':'All schedule; observed>=7m contains only known hightruth and records unknowntruth separately in global groups. Do not label unknown as high.',
        'limits':'Known development periods; calendar target dates are not certified independent events. Descriptive partitioning cannot establish a causal mechanism or justify cherry-picking horizons.'})
    d=dict(np.load(MATRIX));lookup={float(t):i for i,t in enumerate(d['times'])}
    rows=[]
    for r in csv.DictReader((SOURCE/'predictions.csv').open()):
        t=datetime.fromisoformat(r['origin']).timestamp();i=lookup[t]
        actual=numeric(r['actual_m']);control=numeric(r['hourly_control_m']);aug=numeric(r['hourly_plus2018_m']);base=numeric(r['base_m'])
        assert (control is None)==(aug is None)==(base is None)
        trend=d['features'][i,2]
        band='unknown' if actual is None else 'below7' if actual<7 else '7to9' if actual<9 else 'atleast9'
        slope='unknown' if not np.isfinite(trend) else 'rising' if trend>=.1 else 'falling' if trend<=-.1 else 'stable'
        complete=bool(np.isfinite(d['features'][i,6:24]).all());assert complete==(r['complete_upstream18']=='True')
        if actual is None:transition='unknown_truth'
        elif control is None:transition='missing_forecast'
        else:
            ch=abs(control-actual)<=.5;ah=abs(aug-actual)<=.5
            transition='both_hit' if ch and ah else 'hit_to_miss' if ch else 'miss_to_hit' if ah else 'both_miss'
        rows.append({'phase':r['phase'],'origin':r['origin'],'target_time':r['target_time'],'horizon_h':int(r['horizon_h']),
            'base_m':base,'actual_m':actual,'control_m':control,'augmented_m':aug,'known_dH1_m_per_h':float(trend) if np.isfinite(trend) else None,
            'target_level':band,'known_trend':slope,'upstream':'complete' if complete else 'missing','transition':transition})
    save(OUT/'annotated-pairs.csv',rows)
    groups=defaultdict(list)
    for r in rows:groups[r['phase'],r['horizon_h']].append(r)
    metrics=[];days=[];checks=0
    original={(r['phase'],int(r['horizon_h']),r['subset'],r['family']):r for r in csv.DictReader((SOURCE/'evaluation.csv').open()) if r['population']=='full_schedule'}
    count_keys=['scheduled_rows','observed','unknown_truth','pairs','failures','both_hit','hit_to_miss','miss_to_hit','both_miss','control_hits','augmented_hits','control_under_halfmeter','augmented_under_halfmeter','control_over_halfmeter','augmented_over_halfmeter']
    for (phase,h),all_rows in sorted(groups.items()):
        for subset in ('all','level_ge_7m'):
            rr=all_rows if subset=='all' else [r for r in all_rows if r['actual_m'] is not None and r['actual_m']>=7]
            total=summarize(rr)
            for family,key in [('hourly_control','control_hits'),('hourly_plus2018','augmented_hits')]:
                old=original[phase,h,subset,family]
                assert total['observed']==int(old['observed_targets']) and total['pairs']==int(old['pairs']) and total['failures']==int(old['failures']) and total[key]==int(old['hits'])
                checks+=4
            metrics.append({'phase':phase,'horizon_h':h,'subset':subset,'axis':'total','stratum':'all',**total})
            for axis in ('target_level','known_trend','upstream','transition'):
                partitions=defaultdict(list)
                for r in rr:partitions[r[axis]].append(r)
                stats=[summarize(v) for v in partitions.values()]
                for key in count_keys:
                    assert sum(s[key] for s in stats)==total[key];checks+=1
                assert abs(sum(s['sum_absolute_error_change'] for s in stats)-total['sum_absolute_error_change'])<1e-9;checks+=1
                for (label,_),s in zip(partitions.items(),stats):metrics.append({'phase':phase,'horizon_h':h,'subset':subset,'axis':axis,'stratum':label,**s})
            if h==12 and subset=='level_ge_7m':
                dates=defaultdict(list)
                for r in rr:dates[r['target_time'][:10]].append(r)
                for day,group in sorted(dates.items()):days.append({'phase':phase,'target_date':day,**summarize(group)})
    save(OUT/'strata.csv',metrics);save(OUT/'target-days-h12.csv',days)
    for name,digest in hashes.items():assert sha(ROOT/name)==digest
    dump(OUT/'verification.json',{'rows':len(rows),'metrics':len(metrics),'calendar_days_h12':len(days),'checks':checks,'fits':0,'inferences':0,'promoted':False,'goal_achieved':False})
    dump(OUT/'manifest.json',{'input_sha256':hashes,'files':[{'file':p.name,'sha256':sha(p)} for p in sorted(OUT.iterdir())]})
    print(json.dumps({'checks':checks,'h12high':[m for m in metrics if m['horizon_h']==12 and m['subset']=='level_ge_7m' and m['axis'] in ('total','transition','known_trend','target_level')]},indent=2))


if __name__=='__main__':run()
