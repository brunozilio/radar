"""Bounded public retrieval. Existing receipts prevent repeated network requests."""
from pathlib import Path
import json, hashlib, urllib.request, urllib.error, datetime, sys
ROOT=Path(__file__).resolve().parent
def get(name,url,kind):
    receipt=ROOT/'raw'/f'{name}.receipt.json'
    if receipt.exists(): return json.loads(receipt.read_text())
    meta={'url':url,'kind':kind,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'automatic_retries':0}
    try:
        with urllib.request.urlopen(url,timeout=40) as r:
            body=r.read();meta.update(http_status=r.status,headers=dict(r.headers),final_url=r.url)
    except urllib.error.HTTPError as e:
        body=e.read();meta.update(http_status=e.code,headers=dict(e.headers),error=str(e))
    except Exception as e:
        body=b'';meta.update(http_status=None,error=repr(e))
    target=ROOT/'raw'/name;target.write_bytes(body)
    meta.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),file=str(target.relative_to(ROOT)))
    receipt.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n');print(name,meta.get('http_status'),len(body),flush=True)
    return meta
if __name__=='__main__':
    if sys.argv[1]=='documents':
        get('sgb-20180902-17.pdf','https://www.sgb.gov.br/sace/boletins/Taquari/20180902_17-20180902%20-%20174931.pdf','official_bulletin')
        get('sgb-20181003-22.pdf','https://www.sgb.gov.br/sace/boletins/Taquari/20181003_22-20181004%20-%20092639.pdf','official_bulletin')
    elif sys.argv[1]=='telemetry':
        for name,start,end in [('ana-20180830-20180905.xml','30/08/2018','05/09/2018'),('ana-20180930-20181006.xml','30/09/2018','06/10/2018')]:
            from urllib.parse import urlencode
            get(name,'https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urlencode({'codEstacao':'86510000','dataInicio':start,'dataFim':end}),'telemetry_availability')
