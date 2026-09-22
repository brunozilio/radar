"""Local coverage/contract audit of the preserved payloads; no network or fitting."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,hashlib,math,collections
P=Path(__file__).resolve().parent;TZ=timezone(timedelta(hours=-3));sha=lambda b:hashlib.sha256(b).hexdigest()
def at(s):return datetime.fromisoformat(s).replace(tzinfo=TZ)
def finite(x):return isinstance(x,(float,int)) and not isinstance(x,bool) and math.isfinite(x)
start=at('2024-03-29T00:00');expected=[(start+timedelta(hours=i)).strftime('%Y-%m-%dT%H:%M') for i in range(35*24)]
origin_start=at('2024-04-01T00:00');origins=[origin_start+timedelta(hours=i) for i in range(31*24)]
coords=json.loads((P/'coordinate-provenance.json').read_text())['locations'];result={'audited_at_utc':datetime.now(timezone.utc).isoformat(),'requested_valid_start':expected[0],'requested_valid_end':expected[-1],'expected_hours_per_location':len(expected),'origins_start':origins[0].isoformat(),'origins_end':origins[-1].isoformat(),'origins_per_location':len(origins),'windows_hours':[3,6,9,12],'origin_excluded':True,'models':[],'failures':[],'certified_historical_publication':False}
window_rows=[]
for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
    record=json.loads((P/'raw'/f'{model}.source.json').read_text());entry={'model':model,'source':record,'locations':[]};result['models'].append(entry)
    if record.get('http_status')!=200:
        result['failures'].append(model+': no HTTP200 response');continue
    body=(P/record['file']).read_bytes();entry['hash_verified']=sha(body)==record['sha256'];payload=json.loads(body)
    if not isinstance(payload,list) or len(payload)!=5:
        result['failures'].append(model+': response is not a five-location array');continue
    for i,loc in enumerate(payload):
        hourly=loc['hourly'];times=hourly['time'];values=hourly['precipitation_previous_day1'];lookup=dict(zip(times,values));good=[v for v in values if finite(v)];absent=[t for t,v in zip(times,values) if not finite(v)]
        checks={'count_840':len(times)==840 and len(values)==840,'exact_expected_times':times==expected,'no_duplicate_times':len(set(times))==len(times),'mm':loc['hourly_units'].get('precipitation_previous_day1')=='mm','timezone':loc.get('timezone')=='America/Sao_Paulo','utc_offset_minus10800':loc.get('utc_offset_seconds')==-10800,'location_id':loc.get('location_id',0)==i,'hash':entry['hash_verified']}
        for k,v in checks.items():
            if not v:result['failures'].append(f'{model}:{i}:{k}')
        nullgroups=[]
        for t in absent:
            if nullgroups and at(t)-at(nullgroups[-1][-1])==timedelta(hours=1):nullgroups[-1].append(t)
            else:nullgroups.append([t])
        summary={'requested':coords[i],'response_position':i,'location_id':loc.get('location_id',0),'returned_grid_latitude':loc['latitude'],'returned_grid_longitude':loc['longitude'],'elevation_m':loc.get('elevation'),'timezone':loc.get('timezone'),'utc_offset_seconds':loc.get('utc_offset_seconds'),'hourly_units':loc['hourly_units'],'checks':checks,'finite_values':len(good),'nulls':sum(v is None for v in values),'other_nonfinite':sum(v is not None and not finite(v) for v in values),'negative':sum(v<0 for v in good),'min_mm':min(good) if good else None,'max_mm':max(good) if good else None,'null_intervals':[{'first':g[0],'last':g[-1],'hours':len(g)} for g in nullgroups],'window_coverage':{},'top_level_keys':list(loc),'per_value_run_or_publication_present':False}
        entry['locations'].append(summary)
        for w in [3,6,9,12]:
            n=0
            for origin in origins:
                slots=[(origin+timedelta(hours=h)).strftime('%Y-%m-%dT%H:%M') for h in range(1,w+1)];vv=[lookup.get(t) for t in slots];complete=all(finite(v) for v in vv);n+=complete
                window_rows.append({'model':model,'location':i,'group':coords[i]['group'],'origin':origin.isoformat(),'window_h':w,'n_expected':w,'n_finite':sum(finite(v) for v in vv),'complete':complete,'sum_mm':sum(vv) if complete else None})
            summary['window_coverage'][str(w)]={'complete':n,'total':len(origins),'incomplete':len(origins)-n}
(P/'coverage-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
with (P/'window-coverage.jsonl').open('w') as out:
    for row in window_rows:out.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
print(json.dumps({'failures':result['failures'],'locations':sum(len(m['locations']) for m in result['models']),'hours':sum(v['finite_values'] for m in result['models'] for v in m['locations']),'nulls':sum(v['nulls'] for m in result['models'] for v in m['locations']),'windows':len(window_rows),'complete_windows':sum(r['complete'] for r in window_rows)},indent=2))
for m in result['models']:
    print(m['model'],[(v['requested']['group'],v['returned_grid_latitude'],v['returned_grid_longitude'],v['nulls']) for v in m['locations']])
