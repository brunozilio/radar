"""Delivery coverage per fixed hourly window, distinct from forecast accuracy.

A started ledger record alone never proves that a process is currently running.
Only closed windows enter the denominator. No retrospective schedule is invented.
"""
from datetime import datetime,timedelta,timezone
import math
from collections import Counter

MODELS=['radar_arvores_live_candidate','hge_arno_live_candidate']
def stamp(value):
    d=datetime.fromisoformat(value)
    if d.tzinfo is None:raise ValueError('Cadence timestamps require timezone')
    return d.astimezone(timezone.utc)

def audit(records,at):
    policies=[r for r in records if r['kind']=='cadence_policy' and stamp(r['recorded_at'])<=at]
    if not policies:return {'configured':False,'closed_windows':0,'complete_windows':0,'coverage_percent':None,'windows':[],'note':'No preregistered cadence policy; do not infer historic scheduler execution.'}
    # One explicit policy starts this protocol. Changes require versioned audit
    # support, rather than silently discarding earlier unsuccessful windows.
    if len(policies)!=1:raise ValueError('Multiple cadence policies need an explicit transition audit')
    policy=policies[0];p=policy['payload'];start=stamp(p['effective_from'])
    if start<stamp(policy['recorded_at']):raise ValueError('Cadence policy cannot backdate its denominator')
    if p['interval_seconds']!=3600:raise ValueError('This protocol supports hourly windows only')
    expected=set(p['expected_models']);leads=set(p['required_actual_lead_buckets'])
    if not expected or leads!=set(range(1,13)):raise ValueError('Incomplete delivery criterion')
    records=[r for r in records if stamp(r['recorded_at'])<=at]
    starts=[r for r in records if r['kind']=='cycle_started']
    issues=[r for r in records if r['kind']=='forecast_issue']
    windows=[];cursor=start
    while cursor+timedelta(hours=1)<=at:
        end=cursor+timedelta(hours=1)
        attempts=[r for r in starts if cursor<=stamp(r['recorded_at'])<end]
        details=[]
        for cycle in attempts:
            linked=[r for r in issues if r['payload'].get('cycle_sha256')==cycle['sha256'] and stamp(r['recorded_at'])>=stamp(cycle['recorded_at'])]
            timely=[r for r in linked if stamp(r['recorded_at'])<end]
            by_model={};complete_by_reference={}
            for issue in timely:
                model=issue['payload']['model_id']
                buckets={math.floor((stamp(point['valid_at'])-stamp(issue['recorded_at'])).total_seconds()/3600) for point in issue['payload']['points']}
                if model not in by_model:by_model[model]=set()
                by_model[model]|=buckets
                if leads<=buckets:
                    complete_by_reference.setdefault(issue['payload']['reference_at'],set()).add(model)
            missing_models=sorted(expected-set(by_model))
            missing_leads={model:sorted(leads-by_model.get(model,set())) for model in sorted(expected)}
            terminal=[r for r in records if r['kind'] in ['cycle_completed','cycle_failed'] and r['payload'].get('cycle_sha256')==cycle['sha256'] and stamp(r['recorded_at'])<end]
            # Do not combine two partial attempts into a fictional complete cycle.
            coherent=any(expected<=models for models in complete_by_reference.values())
            complete=coherent and not missing_models and not any(missing_leads.values()) and any(r['kind']=='cycle_completed' for r in terminal) and not any(r['kind']=='cycle_failed' for r in terminal)
            details.append({'cycle_sha256':cycle['sha256'],'started_at':cycle['recorded_at'],'complete_delivery':complete,'timely_issues':len(timely),'late_issues':sum(stamp(r['recorded_at'])>=end for r in linked),'missing_models':missing_models,'missing_leads':missing_leads,'terminal_states':[r['kind'] for r in terminal],'unfinished_record':not terminal})
        if any(r['complete_delivery'] for r in details):status='complete'
        elif not attempts:status='no_start_record'
        elif any('cycle_failed' in r['terminal_states'] for r in details):status='failed'
        elif any(r['late_issues'] for r in details):status='late_or_incomplete'
        else:status='incomplete_or_unfinished'
        windows.append({'start':cursor.isoformat(),'end_exclusive':end.isoformat(),'status':status,'attempts':details})
        cursor=end
    complete=sum(w['status']=='complete' for w in windows)
    all_attempts=[]
    for cycle in starts:
        terminal=[r['kind'] for r in records if r['kind'] in ['cycle_failed','cycle_completed'] and r['payload'].get('cycle_sha256')==cycle['sha256']]
        all_attempts.append({'cycle_sha256':cycle['sha256'],'started_at':cycle['recorded_at'],'before_effective_period':stamp(cycle['recorded_at'])<start,'terminal_records':terminal,'unfinished_record':not terminal})
    return {'configured':True,'policy_record':policy['sha256'],'effective_from':p['effective_from'],'closed_windows':len(windows),'complete_windows':complete,'coverage_percent':100*complete/len(windows) if windows else None,'status_counts':dict(Counter(w['status'] for w in windows)),'current_window_started_at':cursor.isoformat() if at>=start else None,'windows':windows,'all_recorded_attempts':all_attempts,'unlinked_forecast_issues':sum(not r['payload'].get('cycle_sha256') for r in issues),'limitations':['Coverage is delivery within preregistered hourly windows, not proof of the scheduler trigger or exact-on-the-hour execution.','No start record means no recorded attempt; it does not prove whether the computer or application was off.','An unfinished record does not establish a live process.','Before the policy effective time, historical coverage remains unproven; recorded failures remain visible separately.','Delivery coverage is not level accuracy and cannot satisfy the 98% accuracy target.']}
