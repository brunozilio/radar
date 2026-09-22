"""Local receipt freshness, not a certification of provider publication latency."""
import argparse,csv,hashlib,json,math
from pathlib import Path
from hydro_prospective_ledger import DEFAULT,ROOT,read_records,timestamp,parse_ana,canonical
from hydro_verification_metrics import quantile


def receipt_windows(records):
    result=[];seen=set()
    for r in records:
        if r['kind']!='observation_receipt':continue
        p=r['payload'];collection=p.get('collection',{});registered=timestamp(r['recorded_at'])
        collected=timestamp(collection['collected_at']) if collection.get('collected_at') else registered
        if collected>registered:raise ValueError('Collection timestamp after its receipt')
        identity=(p['blob_sha256'],collected.isoformat())
        if identity in seen:continue
        seen.add(identity)
        valid=[o for o in p['observations'] if timestamp(o['valid_at'])<=collected]
        approved=[o for o in valid if o['quality']=='Dado aprovado' and o['level_m'] is not None and math.isfinite(o['level_m'])]
        latest=max((timestamp(o['valid_at']) for o in approved),default=None)
        result.append(dict(receipt_sha256=r['sha256'],registered_at=registered.isoformat(),collected_or_registered_at=collected.isoformat(),collection_clock_available=bool(collection.get('collected_at')),blob_sha256=p['blob_sha256'],latest_returned_time=max((timestamp(o['valid_at']) for o in valid),default=None),latest_approved_time=latest,latest_approved_age_minutes=(collected-latest).total_seconds()/60 if latest else None,future_rows=len(p['observations'])-len(valid),observations=valid))
    return sorted(result,key=lambda r:timestamp(r['collected_or_registered_at']))


def first_seen_observations(snapshots):
    first={}
    if not snapshots:return []
    started=timestamp(snapshots[0]['collected_or_registered_at'])
    for r in snapshots:
        received=timestamp(r['collected_or_registered_at'])
        for o in r['observations']:
            if o['quality']!='Dado aprovado' or o['level_m'] is None or not math.isfinite(o['level_m']):continue
            at=timestamp(o['valid_at']);key=(o['station_id'],o['datum_id'],at)
            if key in first:continue
            first[key]=dict(station_id=o['station_id'],datum_id=o['datum_id'],valid_at=at.isoformat(),first_approved_level_m=o['level_m'],first_seen_at=received.isoformat(),first_registered_at=r['registered_at'],first_seen_delay_minutes=(received-at).total_seconds()/60,at_or_after_audit_start=at>=started,receipt_sha256=r['receipt_sha256'])
    return sorted(first.values(),key=lambda r:r['valid_at'])


def audit(root,out):
    records=read_records(root);snapshot=[r for r in records if r['kind']=='observation_receipt'];verified=[]
    for r in snapshot:
        p=r['payload'];data=(root/p['blob']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=p['blob_sha256']:raise ValueError('Changed observation blob')
        station=p['observations'][0]['station_id'];datum=p['observations'][0]['datum_id']
        parsed=parse_ana(data,station,datum)
        fields=['station_id','datum_id','valid_at','level_m','quality']
        def comparable(observations):return sorted([{k:o[k] for k in fields} for o in observations],key=lambda o:o['valid_at'])
        if comparable(parsed)!=comparable(p['observations']):raise ValueError('Receipt observations mismatch raw XML')
        verified.append(dict(receipt_sha256=r['sha256'],blob=p['blob'],sha256=p['blob_sha256']))
    snapshots=receipt_windows(records);first=first_seen_observations(snapshots)
    contemporary=[r for r in first if r['at_or_after_audit_start']]
    issues=[]
    by_sha={r['sha256']:r for r in records}
    for r in records:
        if r['kind']!='forecast_issue':continue
        p=r['payload'];reference=timestamp(p['reference_at']);last=timestamp(p['last_observed']['last_time']);issued=timestamp(r['recorded_at'])
        expected=(reference.timestamp()-900)
        linked=[by_sha[sha] for sha in p['input_receipts'] if sha in by_sha and by_sha[sha]['kind']=='observation_receipt']
        usable=[o for rec in linked for o in rec['payload']['observations'] if o['quality']=='Dado aprovado' and o['level_m'] is not None and math.isfinite(o['level_m'])]
        issues.append(dict(forecast_sha256=r['sha256'],model_id=p['model_id'],reference_at=p['reference_at'],issued_at=r['recorded_at'],manual_revision=bool(p.get('manual_revision')),observed_anchor_at=p['last_observed']['last_time'],anchor_age_at_reference_min=(reference-last).total_seconds()/60,anchor_age_at_actual_issue_min=(issued-last).total_seconds()/60,reference_minus15min_present_in_linked_receipts=any(timestamp(o['valid_at']).timestamp()==expected for o in usable),linked_observation_receipts=len(linked)))
    out.mkdir(parents=True,exist_ok=False)
    def save(name,rows):
        with (out/name).open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    serial=[]
    for r in snapshots:
        x={k:v for k,v in r.items() if k!='observations'}
        for k in ['latest_returned_time','latest_approved_time']:x[k]=x[k].isoformat() if x[k] else ''
        serial.append(x)
    save('receipt-freshness.csv',serial);save('first-seen-observations.csv',first);save('forecast-anchor-ages.csv',issues)
    delay=[r['first_seen_delay_minutes'] for r in contemporary]
    summary=dict(ledger_tip_sha256=records[-1]['sha256'],ledger_records=len(records),observation_receipts_verified=len(verified),distinct_collection_snapshots=len(snapshots),audit_start=snapshots[0]['collected_or_registered_at'],audit_end=snapshots[-1]['collected_or_registered_at'],first_approved_observations_after_audit_start=len(delay),first_seen_delay_minutes={'minimum':min(delay) if delay else None,'median':quantile(delay,.5),'p90':quantile(delay,.9),'maximum':max(delay) if delay else None},first_seen_within15min=sum(v<=15 for v in delay),provider_publication_latency_certified=False,timezone_or_datum_verified=False,goal_achieved=False,limitations=['First seen is an upper bound on when our sampled collector discovered an observation, not an exact publication time.','Earlier-than-audit observations are left-censored and excluded from delay summary.','Collection cadence, API caching and collector downtime can all increase first-seen delay.','Limited observation of one event cannot establish a universal delay distribution.','No forecast, metadata eligibility or source observation is changed.'])
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (out/'verified-receipts.json').write_text(json.dumps(verified,indent=2)+'\n')
    (out/'code').mkdir()
    for p in [Path(__file__),ROOT/'scripts/hydro_prospective_ledger.py',ROOT/'scripts/hydro_verification_metrics.py']:(out/'code'/p.name).write_bytes(p.read_bytes())
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ledger',type=Path,default=DEFAULT);p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(a.ledger,a.output)
