"""Conservative observed flood clusters, distinct from certified independence.

Group by station and datum, retain open/censored episodes, and never bridge a
missing observation to establish the below-threshold separation requirement.
No forecast residuals are used to define episodes or filter their membership.
"""
import hashlib
import math
from collections import defaultdict
from datetime import datetime,timezone


def stamp(value):
    result=datetime.fromisoformat(value)
    if result.tzinfo is None:raise ValueError('Event times require explicit timezone')
    return result.astimezone(timezone.utc)


def inventory(observations,policy):
    """observations is the latest-revision mapping used by the level verifier."""
    if policy['threshold_m']!=7 or policy['dry_separation_hours']<=0 or policy['max_observation_gap_minutes']<=0:
        raise ValueError('Invalid event inventory policy')
    groups=defaultdict(list)
    for (station,datum,valid),(row,receipt) in observations.items():
        groups[station,datum].append((valid,row,receipt))
    events=[];membership={}
    for (station,datum),rows in sorted(groups.items()):
        active=None;dry_since=None;dry_until=None;dry_verified=True;previous=None
        for at,row,receipt in sorted(rows,key=lambda x:x[0]):
            gap=previous is not None and (at-previous).total_seconds()>policy['max_observation_gap_minutes']*60
            if gap:
                dry_since=None;dry_verified=True
                if active is not None:active['has_observation_gaps']=True
            previous=at
            level=row.get('level_m')
            valid=level is not None and math.isfinite(level) and row.get('quality')=='Dado aprovado'
            if not valid:
                dry_since=None;dry_verified=True
                if active is not None:active['has_observation_gaps']=True
                continue
            metadata=bool(row.get('timezone_verified') and row.get('datum_verified'))
            if level>=policy['threshold_m']:
                if active is None:
                    separated=dry_since is not None and dry_until is not None and (dry_until-dry_since).total_seconds()>=policy['dry_separation_hours']*3600
                    event_id=hashlib.sha256((station+'|'+datum+'|'+at.isoformat()).encode()).hexdigest()[:24]
                    active={'event_id':event_id,'station_id':station,'datum_id':datum,'first_exceedance_at':at.isoformat(),'last_exceedance_at':at.isoformat(),'peak_at':at.isoformat(),'peak_level_m':level,'high_observation_count':0,'left_censored':not separated,'closed_at':None,'right_censored':True,'has_observation_gaps':False,'all_metadata_verified':metadata and dry_verified,'separation_start_at':dry_since.isoformat() if separated else None,'first_observation_receipt':receipt,'last_observation_receipt':receipt,'independence_certified':False}
                    events.append(active)
                active['high_observation_count']+=1
                active['last_exceedance_at']=at.isoformat()
                active['last_observation_receipt']=receipt
                active['all_metadata_verified']&=metadata
                if level>active['peak_level_m']:
                    active['peak_level_m']=level;active['peak_at']=at.isoformat()
                membership[station,datum,at]=active['event_id']
                dry_since=None;dry_verified=True
            else:
                if dry_since is None:dry_since=at
                dry_until=at
                dry_verified&=metadata
                if active is not None:
                    active['all_metadata_verified']&=metadata
                    if (at-dry_since).total_seconds()>=policy['dry_separation_hours']*3600:
                        active['closed_at']=at.isoformat();active['right_censored']=False
                        active=None
        for event in events:
            if event['station_id']==station and event['datum_id']==datum:
                event['complete_observed_cluster']=not(event['left_censored'] or event['right_censored'] or event['has_observation_gaps'])
    return events,membership


def audit(records,observations,pairs,at):
    policies=[r for r in records if r['kind']=='flood_event_policy' and stamp(r['recorded_at'])<=at]
    if not policies:return {'configured':False,'events':[],'scorecard':[],'certified_independent_events':0,'note':'No registered event grouping policy.'}
    if len(policies)!=1:raise ValueError('Event policy changes require an explicit versioned comparison')
    record=policies[0];policy=record['payload']
    events,membership=inventory(observations,policy)
    lookup={e['event_id']:e for e in events}
    grouped=defaultdict(list)
    for pair in pairs:
        if pair['status']=='matched' and pair['observed_m']>=7:
            key=(pair['station_id'],pair['datum_id'],stamp(pair['valid_at']))
            event_id=membership.get(key)
            pair['flood_event_id']=event_id
            if event_id is not None:
                grouped[pair['model_id'],pair['model_version'],pair['minimum_verified_lead_h'],event_id].append(pair)
    scores=[]
    for (model,version,lead,event_id),group in sorted(grouped.items()):
        eligible=[p for p in group if p['goal_eligible']]
        scores.append({'model_id':model,'model_version':version,'lead_h':lead,'event_id':event_id,'diagnostic_matched_pairs':len(group),'goal_eligible_pairs':len(eligible),'hits':sum(p['hit_within_050m'] for p in eligible),'accuracy_percent':100*sum(p['hit_within_050m'] for p in eligible)/len(eligible) if eligible else None,'complete_observed_cluster':lookup[event_id]['complete_observed_cluster'],'independence_certified':False})
    return {'configured':True,'policy_record':record['sha256'],'policy':policy,'observed_clusters':len(events),'complete_observed_clusters':sum(e['complete_observed_cluster'] for e in events),'certified_independent_events':0,'events':events,'scorecard':scores,'goal_achieved':False,'limitations':['A 72-hour below-threshold run is a conservative operational grouping candidate, not a verified independence criterion for this basin.','Open, left-censored and gap-affected clusters remain visible; missing data cannot establish separation.','Only exact approved observations define exceedances. Metadata validity is tracked separately.','Repeated forecasts for one episode do not become multiple independent events.','This inventory does not certify ten independent floods or infer uncertainty from treating hourly samples as independent.','A later observation revision can change the inventory; every report retains its ledger cutoff and source receipts.']}
