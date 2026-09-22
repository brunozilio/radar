"""Descriptive errors; no independence, confidence or accuracy-goal claim."""
import math
from collections import Counter,defaultdict


def quantile(values,p):
    values=sorted(values)
    if not values:return None
    x=(len(values)-1)*p;lo=math.floor(x);hi=math.ceil(x)
    return values[lo]+(values[hi]-values[lo])*(x-lo)


def error_metrics(pairs):
    errors=[float(p['forecast_m'])-float(p['observed_m']) for p in pairs]
    if not all(math.isfinite(e) for e in errors):raise ValueError('Nonfinite verification error')
    absolute=[abs(e) for e in errors];n=len(errors);hits=sum(e<=.5 for e in absolute)
    return {'n':n,'hits':hits,'accuracy_percent':100*hits/n if n else None,
            'mae_m':sum(absolute)/n if n else None,'bias_m':sum(errors)/n if n else None,
            'p90_abs_m':quantile(absolute,.90),'p98_abs_m':quantile(absolute,.98),
            'max_abs_m':max(absolute) if absolute else None,
            'unique_target_times':len({p['valid_at'] for p in pairs}),
            'observed_flood_clusters':len({p['flood_event_id'] for p in pairs if p.get('flood_event_id')}),
            'confidence_interval':None,'uncertainty_status':'Independent-event validation unavailable; hourly pairs are dependent.'}


def diagnostic_scorecard(pairs):
    groups=defaultdict(list)
    for p in pairs:
        groups[p['evidence_kind'],p['model_id'],p['model_version'],p['minimum_verified_lead_h']].append(p)
    result=[]
    for (kind,model,version,lead),rows in sorted(groups.items()):
        matched=[p for p in rows if p['status']=='matched']
        for regime in ['all','level_ge_7m']:
            selected=matched if regime=='all' else [p for p in matched if p['observed_m']>=7]
            result.append({'evidence_kind':kind,'model_id':model,'model_version':version,'actual_lead_bucket_h':lead,'regime':regime,**error_metrics(selected),'goal_eligible_n':sum(p['goal_eligible'] for p in selected),'registered_points_in_model_horizon':len(rows),'status_counts_in_model_horizon':dict(Counter(p['status'] for p in rows)),'exclusion_counts':dict(Counter(reason for p in selected for reason in p['exclusion_reasons'].split(',') if reason)),'diagnostic_only':True,'goal_achieved':False})
    return result
