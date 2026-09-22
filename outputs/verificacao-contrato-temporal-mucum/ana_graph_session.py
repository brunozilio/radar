from pathlib import Path
import urllib.request,http.cookiejar,datetime,hashlib,json
P=Path(__file__).resolve().parent;m=json.loads((P/'manifest.json').read_text());op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
for name,url,data in [('ana-public-cookie.json','https://www.snirh.gov.br/hidrotelemetria/Default.aspx/SetCookie',b''),('ana-graph.html','https://www.snirh.gov.br/hidrotelemetria/gerarGrafico.aspx',None)]:
 x={'file':'raw/'+name,'url':url,'method':'POST' if data is not None else 'GET','purpose':'Public anonymous session exactly following portal script; no credentials','retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  r=op.open(urllib.request.Request(url,data=data,headers={'User-Agent':'Mozilla/5.0','Content-Type':'application/json; charset=utf-8'}),timeout=25);b=r.read();(P/x['file']).write_bytes(b);x.update(status=r.status,final_url=r.url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest());print(name,r.status,len(b))
 except Exception as e:x['error']=str(e);print(name,str(e))
 m.append(x);(P/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
