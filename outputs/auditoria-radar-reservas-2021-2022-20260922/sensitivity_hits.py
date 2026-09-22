"""Hit-class sensitivity diagnostic only; primary frozen metrics remain unchanged."""
from pathlib import Path
from collections import Counter
import csv,json,hashlib,math
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
r=json.loads((P/'verification.json').read_text());cases=r['threshold_sensitivity_cases'];primary=ROOT/'outputs/experimento-radar-reservas-2021-2022-20260922/predictions.csv';pred=list(csv.DictReader(primary.open()));lookup={(int(x['year']),x['origin'],int(x['nominal_lead_h'])):x for x in pred};details=[]
for c in cases:
 row=lookup[c['year'],c['origin'],c['horizon_h']];truth=float(row['actual_m']) if row['actual_m'] else None;assert float(row[c['family']+'_m'])==c['saved_m'];original_error=abs(c['saved_m']-truth) if truth is not None else None;new_error=abs(c['independent_m']-truth) if truth is not None else None
 details.append(dict(**c,target_time=row['target_time'],actual_m=truth,truth_finite=truth is not None,level_ge7=truth is not None and truth>=7,original_abs_error_m=original_error,reconstructed_abs_error_m=new_error,original_hit=original_error<=.5 if truth is not None else None,reconstructed_hit=new_error<=.5 if truth is not None else None,classification_changed=(original_error<=.5)!=(new_error<=.5) if truth is not None else None))
groups=[]
for year in (2021,2022):
 for family in ('control120','candidate120_plus2020'):
  for h in range(1,13):
   for subset in ('all','level_ge_7m'):
    selected=[c for c in details if c['year']==year and c['family']==family and c['horizon_h']==h and c['truth_finite'] and (subset=='all' or c['level_ge7'])]
    gains=sum(not c['original_hit'] and c['reconstructed_hit'] for c in selected);losses=sum(c['original_hit'] and not c['reconstructed_hit'] for c in selected)
    groups.append(dict(year=year,family=family,horizon_h=h,subset=subset,changed_prediction_cells_with_observed_truth=len(selected),hit_to_miss=losses,miss_to_hit=gains,net_hits_change=gains-losses,classification_changes=gains+losses,max_abs_prediction_difference_m=max((abs(c['difference_m']) for c in selected),default=0.)))
flips=[c for c in details if c['classification_changed']];assert len({(c['year'],c['family'],c['horizon_h'],c['origin']) for c in cases})==len(cases)==203
summary=dict(scope='Numerical sensitivity diagnostic only; no input correction or modification of primary frozen metrics.',prediction_cells=203,unique_year_origin_pairs=len({(c['year'],c['origin']) for c in details}),unique_year_target_time_pairs=len({(c['year'],c['target_time']) for c in details}),unique_scheduled_year_origin_horizon_rows=len({(c['year'],c['origin'],c['horizon_h']) for c in details}),certified_independent_events=None,finite_truth_cells=sum(c['truth_finite'] for c in details),unknown_truth_cells=sum(not c['truth_finite'] for c in details),classification_changed_cells=len(flips),classification_changed_highwater_cells=sum(c['level_ge7'] for c in flips),hit_to_miss=sum(c['original_hit'] and not c['reconstructed_hit'] for c in flips),miss_to_hit=sum(not c['original_hit'] and c['reconstructed_hit'] for c in flips),max_abs_prediction_difference_m=max(abs(c['difference_m']) for c in cases),independent_exact_applications=34,original_matrix_exact_fallback_applications=14,total_frozen_applications=48,primary_predictions_sha256=hashlib.sha256(primary.read_bytes()).hexdigest(),groups=groups,classification_changed_cases=flips,limits=['203 is a count of family/horizon forecast cells, not203origins/targets/events.','A difference below0.50m is not automatically tolerable: threshold sensitivity affects reproducibility and hit classification.','Unknown truth is excluded from hit classification, never counted as hit.','No retuning/rounding/new forecast family or change to primary evaluation.'])
(P/'hit-sensitivity.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
for name,rows in [('hit-sensitivity-groups.csv',groups),('hit-sensitivity-cases.csv',details)]:
 with (P/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps({k:v for k,v in summary.items() if k not in ('groups','limits')},indent=2))
