"""Inventory older target/partial-input support; no train/test allocation or fit."""
import bisect
import csv
import hashlib
import json
import math
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
TZ=timezone(timedelta(hours=-3))
PLANTS=['JIUHQJ','JIUHMC','JIUHCA']
FIELDS=['val_vazaodefluente','val_vazaoafluente','val_nivelmontante','val_niveljusante']
WINDOWS=[
 ('2020','2020-06-01','2020-07-21','outputs/historico-cheias-mucum/2020-jun-jul/levels-approved.csv','outputs/historico-vazoes-ceran/ceran-2020-07-source-values.csv'),
 ('2023','2023-09-01','2023-10-01','outputs/historico-cheia-setembro-2023/ana-mucum/levels-approved.csv','outputs/historico-cheia-setembro-2023/ons-ceran-source-values.csv'),
 ('2024','2024-03-01','2024-06-01','outputs/historico-cheias-mucum/2024-mar-mai/levels-approved.csv','outputs/historico-vazoes-ceran/ceran-2024-05-source-values.csv'),
]


def epoch(s):
    d=datetime.fromisoformat(s)
    return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()


def iso(t):
    return datetime.fromtimestamp(t,TZ).isoformat()


def number(s):
    try:v=float(s)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):return list(csv.DictReader(p.open()))


def save(name,rows):
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def run():
    limits=ROOT/'outputs/diagnostico-extremos-radar-20260921/training-response-ranges.csv'
    maxdelta={int(r['horizon_h']):float(r['max_delta_m']) for r in read(limits) if r['phase']=='test' and r['training_policy']=='candidate'}
    paths=[Path(__file__),limits]
    summaries=[];pairs=[];trace=[]
    for year,start,end,ana,ons in WINDOWS:
        ana=ROOT/ana;ons=ROOT/ons;paths += [ana,ons]
        levels={}
        for row in read(ana):
            assert row['CodEstacao']=='86510000' and row['CQ_NivelFinal']=='Dado aprovado' and row['duplicate_conflict']=='False'
            at=epoch(row['timestamp_source_naive']);value=float(row['level_m'])
            assert at not in levels and value==float(row['NivelFinal'])/100
            levels[at]=value
        reservoirs={p:{} for p in PLANTS}
        for line,row in enumerate(read(ons),2):
            plant=row['id_reservatorio'].strip();at=epoch(row['din_instante'])
            assert plant in reservoirs and at not in reservoirs[plant]
            reservoirs[plant][at]=(row,line)
        stamps={p:sorted(reservoirs[p]) for p in PLANTS}
        origins=list(range(int(epoch(start)),int(epoch(end)),3600))
        support={}
        for origin in origins:
            values={};flagged_zeros=0;stale=0
            for plant in PLANTS:
                s=stamps[plant];i=bisect.bisect_right(s,origin-3600)-1
                chosen=s[i] if i>=0 else None
                acceptable=chosen is not None and 0<=origin-3600-chosen<=5400
                row,line=reservoirs[plant][chosen] if chosen is not None else ({},None)
                if not acceptable:stale+=1
                for field in FIELDS:
                    value=number(row.get(field)) if acceptable else None
                    values[plant,field]=value
                    trace.append(dict(window=year,origin=iso(origin),plant=plant,field=field,
                        source_time=iso(chosen) if chosen is not None else None,
                        source_file=str(ons.relative_to(ROOT)),source_line=line,
                        age_after_delay_min=(origin-3600-chosen)/60 if chosen is not None else None,
                        accepted_by_time=acceptable,value=value))
                component=[number(row.get(k)) for k in ['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']]
                if acceptable and number(row.get('val_vazaodefluente'))==0 and all(v is not None for v in component) and sum(component)>0:
                    flagged_zeros+=1
            support[origin]=dict(all_6_QI_present=all(values[p,f] is not None for p in PLANTS for f in FIELDS[:2]),
                all_6_levels_present=all(values[p,f] is not None for p in PLANTS for f in FIELDS[2:]),
                zero_defluent_positive_components=flagged_zeros,plants_unavailable_by_time=stale)
        for h in range(1,13):
            scheduled=[o for o in origins if o+h*3600<epoch(end)]
            group=[]
            for origin in scheduled:
                base=levels.get(origin-900);target=levels.get(origin+h*3600)
                pair=base is not None and target is not None
                row=dict(window=year,horizon_h=h,origin=iso(origin),target_time=iso(origin+h*3600),
                    base_time=iso(origin-900),base_m=base,target_m=target,
                    response_m=target-base if pair else None,
                    above_current_training_max=bool(pair and target-base>maxdelta[h]),
                    target_ge7_in_source_reference=bool(target is not None and target>=7),
                    **support[origin])
                pairs.append(row);group.append(row)
            eligible=[r for r in group if r['response_m'] is not None]
            extreme=[r for r in eligible if r['above_current_training_max']]
            maximum=max(eligible,key=lambda r:r['response_m']) if eligible else None
            summaries.append(dict(window=year,horizon_h=h,scheduled=len(group),paired=len(eligible),
                missing_base=sum(r['base_m'] is None for r in group),missing_target=sum(r['target_m'] is None for r in group),
                approved_target_ge7=sum(r['target_ge7_in_source_reference'] for r in group),
                paired_ge7=sum(r['target_ge7_in_source_reference'] for r in eligible),
                above_current_training_max=len(extreme),
                extreme_with_all_6_QI=sum(r['all_6_QI_present'] for r in extreme),
                extreme_with_all_6_reservoir_levels=sum(r['all_6_levels_present'] for r in extreme),
                extreme_with_zero_defluent_positive_components=sum(r['zero_defluent_positive_components']>0 for r in extreme),
                maximum_response_m=maximum['response_m'] if maximum else None,
                maximum_response_origin=maximum['origin'] if maximum else None,
                maximum_response_target=maximum['target_time'] if maximum else None,
                maximum_response_base_m=maximum['base_m'] if maximum else None,
                maximum_response_target_m=maximum['target_m'] if maximum else None,
                maximum_response_all_6_QI=maximum['all_6_QI_present'] if maximum else False))
    save('summary.csv',summaries);save('potential-pairs.csv',pairs);save('reservoir-source-trace.csv',trace)
    summary=dict(potential_rows=len(pairs),trace_rows=len(trace),summary_rows=len(summaries),
        target_definition='Exact approved Muçum level at O-15min and O+h, no interpolation or older finite fallback.',
        partial_input_definition='Only current Q/I and U/D from three reservoirs, source timestamp literal,60min assumed delay plus90min age after lookup; not the entire204-feature matrix.',
        missing_other_inputs='Other three ANA levels, regional rainfall and archived weather coverage not established by this script.',
        timezones_verified=False,datum_continuity_verified=False,historical_availability_verified=False,
        no_new_holdout=True,trained=False,allocated_to_training=False,promoted=False,goal_achieved=False,
        input_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths})
    (OUT/'audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([r for r in summaries if r['horizon_h'] in [1,6,12]],ensure_ascii=False,indent=2))


if __name__=='__main__':run()
