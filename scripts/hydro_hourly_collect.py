"""Public-only refresh into a unique run folder; never reuse cached responses."""
from __future__ import annotations
import concurrent.futures, hashlib, json, urllib.parse, urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo('America/Sao_Paulo')
BASE = ROOT / 'outputs/mucum-atualizacao-15h-2026-09-21'

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def collect(out, now):
    raw = out / 'raw'
    raw.mkdir(parents=True, exist_ok=False)
    jobs = []
    codes = sorted(p.name.split('-')[1] for p in (BASE/'raw').glob('ana-*-fresh.xml'))
    for code in codes:
        query = urllib.parse.urlencode({'codEstacao':code, 'dataInicio':(now-timedelta(days=7)).strftime('%d/%m/%Y'), 'dataFim':now.strftime('%d/%m/%Y')})
        jobs.append((f'ana-{code}-fresh.xml','https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+query,'ANA'))
    for plant, code in [('julho','UHQJ'),('monte','UHMC'),('castro','UHCA')]:
        jobs.append((f'ceran-{plant}-fresh.html',f'https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_{code}.php','CERAN'))
    for path in sorted((BASE/'raw').glob('sigma-*.txt')):
        sid = path.stem.removeprefix('sigma-')
        jobs.append((path.name,f'https://sigmameteorologia.com/produtos/stations/{now:%Y-%m-%d}/{sid}.txt','SIGMA'))
    query_info=json.loads((ROOT/'outputs/mucum-propagacao-2026-09-21/raw/chuva-prevista-query.json').read_text())
    coordinates=urllib.parse.parse_qs(urllib.parse.urlsplit(query_info['url']).query)
    for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
        params = {'latitude':coordinates['latitude'][0], 'longitude':coordinates['longitude'][0], 'hourly':'precipitation', 'models':model, 'timezone':'America/Sao_Paulo', 'past_days':7, 'forecast_days':3}
        jobs.append((f'weather-{model}.json','https://api.open-meteo.com/v1/forecast?'+urllib.parse.urlencode(params),'Open-Meteo'))
    def fetch(job):
        name,url,source = job
        item = {'file':name,'source':source,'url':url,'requested_at':datetime.now(TZ).isoformat(),'issued_at':None,'issuance_note':'Not exposed by this endpoint; collection time is not model issuance.'}
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'Radar-public-research/1.0','Cache-Control':'no-cache','Referer':'https://sigmameteorologia.com/nowcasting/'})
            with urllib.request.urlopen(request,timeout=40) as response:
                body=response.read(); item.update(status=response.status,http_date=response.headers.get('Date'),http_last_modified=response.headers.get('Last-Modified'))
            (raw/name).write_bytes(body)
            item.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
        except Exception as exc:
            item['first_attempt_error']=str(exc)
            try:
                with urllib.request.urlopen(request,timeout=40) as response:
                    body=response.read(); item.update(status=response.status,http_date=response.headers.get('Date'),http_last_modified=response.headers.get('Last-Modified'))
                (raw/name).write_bytes(body)
                item.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
            except Exception as retry_exc:
                item['error']=str(retry_exc)
        item['collected_at']=datetime.now(TZ).isoformat()
        return item
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        manifest=list(pool.map(fetch,jobs))
    dump(out/'collection-manifest.json',manifest)
    return manifest

if __name__ == '__main__':
    now=datetime.now(TZ)
    out=ROOT/'outputs'/('mucum-hourly-'+now.strftime('%Y%m%dT%H%M%S%z'))
    out.mkdir(exist_ok=False)
    dump(out/'run.json',{'started_at':now.isoformat(),'reference_time':now.replace(minute=0,second=0,microsecond=0).isoformat(),'timezone':'America/Sao_Paulo','status':'collecting'})
    print(out,flush=True)
    manifest=collect(out,now)
    print(json.dumps({'requests':len(manifest),'failures':[x for x in manifest if 'error' in x]},ensure_ascii=False),flush=True)
