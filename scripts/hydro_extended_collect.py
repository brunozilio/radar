"""Read public ANA telemetry, ONS hourly reservoir data and DCRS monitoring APIs."""
from pathlib import Path
import urllib.request,urllib.parse,json,datetime,concurrent.futures,csv,io,hashlib,re,sys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/mucum-propagacao-2026-09-21';RAW=OUT/'raw'
def fetch(name,url):
    f=RAW/name
    if f.exists() and f.stat().st_size>1000:return {'file':name,'cached':True}
    try:
        b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=90).read();f.write_bytes(b)
        return {'file':name,'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    except Exception as e:return {'file':name,'url':url,'error':str(e)}
def ana():
    stations=json.loads((ROOT/'outputs/mucum-bacia-2026-09-21/producao-estacoes.json').read_text())
    jobs=[]
    for s in stations:
        if not s['inside']:continue
        q=urllib.parse.urlencode({'codEstacao':s['id'],'dataInicio':'01/01/2026','dataFim':'21/09/2026'})
        jobs.append((f'ana-{s["id"]}.xml','https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+q))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        results=[]
        for r in ex.map(lambda kv:fetch(*kv),jobs):results.append(r);print(r['file'],r.get('bytes',r.get('error','cached')),flush=True)
    (RAW/'ana-expanded-manifest.json').write_text(json.dumps(results,indent=2))
def ana2025():
    stations=json.loads((ROOT/'outputs/mucum-bacia-2026-09-21/producao-estacoes.json').read_text());jobs=[]
    for s in stations:
        if not s['inside']:continue
        q=urllib.parse.urlencode({'codEstacao':s['id'],'dataInicio':'01/04/2025','dataFim':'31/12/2025'})
        jobs.append((f'ana-{s["id"]}-2025.xml','https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+q))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        results=[]
        for r in ex.map(lambda kv:fetch(*kv),jobs):results.append(r);print(r['file'],r.get('bytes',r.get('error','cached')),flush=True)
    (RAW/'ana-2025-manifest.json').write_text(json.dumps(results,indent=2))
def ons():
    catalog=json.loads((RAW/'ons-hidraulicos-catalogo.json').read_text())['result']['results']
    ds=next(x for x in catalog if x['name']=='dados_hidrologicos_ho')
    urls=sorted({r['url'] for r in ds['resources'] if r['format']=='CSV' and ('2026' in r['name'] or any(f'2025-{m:02d}' in r['name'] for m in range(4,13)))})
    def get(url):
        name=url.rsplit('/',1)[-1].replace('.csv','-ceran.csv');f=RAW/name
        if f.exists():return {'file':name,'cached':True}
        try:
            with urllib.request.urlopen(url,timeout=90) as response:
                reader=csv.DictReader(io.TextIOWrapper(response,encoding='utf-8-sig'),delimiter=';');selected=[];n=0
                for row in reader:
                    n+=1
                    if any(x in ' '.join(str(v) for v in row.values()).upper() for x in ['14 DE JULHO','14 JULHO','MONTE CLARO','CASTRO ALVES']):selected.append(row)
            with f.open('w') as out:
                writer=csv.DictWriter(out,fieldnames=reader.fieldnames,delimiter=';');writer.writeheader();writer.writerows(selected)
            return {'file':name,'url':url,'rows_source':n,'selected_rows':len(selected),'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256_filtered':hashlib.sha256(f.read_bytes()).hexdigest()}
        except Exception as e:return {'file':name,'url':url,'error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        results=[]
        for r in ex.map(get,urls):results.append(r);print(r,flush=True)
    (RAW/'ons-manifest.json').write_text(json.dumps(results,indent=2))
def dcrs():
    js=(RAW/'dcrs-app.js').read_text();q=js[js.index('query Tags_data {'):];q=q[:q.index('`')]
    data=json.dumps({'query':q,'operationName':'Tags_data'}).encode()
    req=urllib.request.Request('https://redehidrometeorologica.defesacivil.rs.gov.br/graphql',data=data,headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
    b=urllib.request.urlopen(req,timeout=40).read();(RAW/'dcrs-stations.json').write_bytes(b);print('DCRS',len(b),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
