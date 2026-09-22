from pathlib import Path
import urllib.request, urllib.parse, json, concurrent.futures, re
P=Path(__file__).resolve().parents[1]/'outputs/mucum-bacia-2026-09-21/raw'
BASE='https://portal1.snirh.gov.br/arcgis/rest/services/SPR/'
def fetch(name,url):
 try:
  b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read();(P/name).write_bytes(b);return name,len(b)
 except Exception as e:return name,str(e)
def query(service,params):
 return BASE+service+'/MapServer/0/query?'+urllib.parse.urlencode({'f':'json','outFields':'*','outSR':4326,**params})
urls={
 'bho-outlet-river.json':query('BHO2017_50K_TRECHODRENAGEM',{'where':'COTRECHO=15365','returnGeometry':'true'}),
 'bho-rivers-count.json':query('BHO2017_50K_TRECHODRENAGEM',{'where':"COBACIA LIKE '786%'",'returnCountOnly':'true'}),
 'bho-rivers-0.json':query('BHO2017_50K_TRECHODRENAGEM',{'where':"COBACIA LIKE '786%'",'returnGeometry':'true','resultOffset':0,'resultRecordCount':1000,'orderByFields':'OBJECTID'}),
}
s=(P/'sace-root.html').read_text(errors='replace')
for path in re.findall(r'<script[^>]+src=["\']([^"\']+)',s):
 if any(k in path for k in ['exibirDadosScript','boletimScript','modeloPrevisaoScript','mapaScript']):
  urls[path.split('/')[-1].split('?')[0]]='https://sace.sgb.gov.br'+path
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 for r in ex.map(lambda kv:fetch(*kv),urls.items()):print(r)
(P/'research-queries.json').write_text(json.dumps(urls,indent=2))
