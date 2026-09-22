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
    from urllib.parse import urlencode
    for code in ['86472000','86472600','86500000']:
        get(f'ana-{code}-20240615-20240621.xml','https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urlencode({'codEstacao':code,'dataInicio':'15/06/2024','dataFim':'21/06/2024'}),'level_availability')
