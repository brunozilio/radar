"""Bounded public-API research; never imports or changes the forecasting pipeline."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, urllib.request, urllib.parse, urllib.error, math
P=Path(__file__).resolve().parent
(P/'responses').mkdir(exist_ok=True)
dates=['2020-06-30','2020-07-07','2023-09-04','2024-03-15','2024-04-30','2024-05-02']
results=[]
for date in dates:
    args={'latitude':-29.10130785468805,'longitude':-51.61242071623862,'hourly':'precipitation_previous_day1','start_date':date,'end_date':date,'timezone':'America/Sao_Paulo','models':'gfs_seamless,ecmwf_ifs025,icon_global'}
    url='https://previous-runs-api.open-meteo.com/v1/forecast?'+urllib.parse.urlencode(args)
    record={'date':date,'url':url,'parameters':args,'requested_at_utc':datetime.now(timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(url,timeout=30) as response:
            body=response.read();record.update(status=response.status,headers=dict(response.headers))
    except urllib.error.HTTPError as error:
        body=error.read();record.update(status=error.code,headers=dict(error.headers))
    except Exception as error:
        record['error']=str(error);results.append(record);continue
    record['collected_at_utc']=datetime.now(timezone.utc).isoformat()
    dest=P/'responses'/f'{date}.json';dest.write_bytes(body)
    record.update(file=str(dest.relative_to(P)),sha256=hashlib.sha256(body).hexdigest(),bytes=len(body))
    try:
        payload=json.loads(body)
        if 'hourly' in payload:
            record['hours']=len(payload['hourly']['time']);record['timezone']=payload.get('timezone');record['utc_offset_seconds']=payload.get('utc_offset_seconds');record['units']=payload.get('hourly_units');record['fields']={}
            for k,v in payload['hourly'].items():
                if k=='time':continue
                finite=[x for x in v if x is not None and math.isfinite(x)]
                record['fields'][k]={'n':len(v),'finite':len(finite),'nulls':sum(x is None for x in v),'min':min(finite) if finite else None,'max':max(finite) if finite else None}
            record['top_level_keys']=list(payload)
        else:record['api_message']=payload
    except Exception as error:record['parse_error']=str(error)
    results.append(record)
    (P/'source-manifest.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
    print(date,record['status'],record.get('fields',record.get('api_message')),flush=True)
(P/'source-manifest.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
