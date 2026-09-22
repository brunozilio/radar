"""Three bounded requests; stores public research inputs, never trains or runs models."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse, urlencode
from urllib.request import urlopen
from urllib.error import HTTPError
import json, hashlib

P=Path(__file__).resolve().parent
ROOT=P.parents[1]
SOURCE=ROOT/'outputs/mucum-propagacao-2026-09-21/raw/chuva-prevista-query.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
meta=json.loads(SOURCE.read_text());query=parse_qs(urlparse(meta['url']).query)
locations=[{'index':i,'group':group,'latitude_requested':float(lat),'longitude_requested':float(lon)} for i,(group,lat,lon) in enumerate(zip(meta['groups'],query['latitude'][0].split(','),query['longitude'][0].split(',')))]
assert len(locations)==5
source={'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE.read_bytes()),'original':meta,'locations':locations,'note':'Coordinates only are reused; original source URL refers to a different ensemble product.'}
(P/'coordinate-provenance.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
(P/'raw').mkdir(exist_ok=True)
for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
    sidecar=P/'raw'/f'{model}.source.json';dest=P/'raw'/f'{model}.json'
    if sidecar.exists():
        print(model,'request already recorded; no duplicate request',flush=True);continue
    assert not dest.exists(), f'Orphan response exists: inspect rather than request again: {dest}'
    args={'latitude':query['latitude'][0],'longitude':query['longitude'][0],'hourly':'precipitation_previous_day1','start_date':'2024-03-29','end_date':'2024-05-02','timezone':'America/Sao_Paulo','models':model}
    url='https://previous-runs-api.open-meteo.com/v1/forecast?'+urlencode(args)
    record={'model_requested':model,'url':url,'parameters':args,'requested_at_utc':datetime.now(timezone.utc).isoformat(),'status':'request_started','coordinate_source_sha256':source['sha256']}
    # Even interrupted requests remain marked; never silently repeat a potentially completed fetch.
    sidecar.write_text(json.dumps(record,indent=2)+'\n')
    try:
        try:
            with urlopen(url,timeout=45) as response:
                body=response.read();record.update(http_status=response.status,response_url=response.url,headers=dict(response.headers))
        except HTTPError as error:
            body=error.read();record.update(http_status=error.code,headers=dict(error.headers))
        dest.write_bytes(body)
        record.update(status='response_preserved',collected_at_utc=datetime.now(timezone.utc).isoformat(),file=str(dest.relative_to(P)),bytes=len(body),sha256=sha(body))
    except Exception as error:
        record.update(status='request_failed',finished_at_utc=datetime.now(timezone.utc).isoformat(),error=str(error))
    sidecar.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(model,record['status'],record.get('http_status'),record.get('bytes'),flush=True)
