from pathlib import Path
import urllib.request,urllib.parse,http.cookiejar,datetime,hashlib,json
from html.parser import HTMLParser
P=Path(__file__).resolve().parent;m=json.loads((P/'manifest.json').read_text());op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));base='https://www.snirh.gov.br/hidrotelemetria/'
def get(name,url,data=None,ctype=None):
 x={'file':'raw/'+name,'url':url,'method':'POST' if data is not None else 'GET','purpose':'Anonymous public graph navigation/read query','retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 r=op.open(urllib.request.Request(url,data=data,headers={'User-Agent':'Mozilla/5.0',**({'Content-Type':ctype} if ctype else {})}),timeout=25);b=r.read();(P/x['file']).write_bytes(b);x.update(status=r.status,final_url=r.url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest());m.append(x);(P/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(name,r.status,len(b));return b
get('ana-cookie-form.json',base+'Default.aspx/SetCookie',b'','application/json; charset=utf-8')
b=get('ana-form-initial.html',base+'gerarGrafico.aspx');data={}
class Form(HTMLParser):
 def __init__(self):super().__init__();self.select=None;self.opts=[]
 def handle_starttag(self,tag,attrs):
  x=dict(attrs)
  if tag=='input' and 'name' in x:
   typ=x.get('type','text').lower()
   if typ in ['submit','button','image']:return
   if typ in ['radio','checkbox'] and 'checked' not in x:return
   data[x['name']]=x.get('value','')
  if tag=='select':self.select=x.get('name');self.opts=[]
  if tag=='option' and self.select:self.opts.append(x)
 def handle_endtag(self,tag):
  if tag=='select' and self.select:
   o=next((x for x in self.opts if 'selected' in x),self.opts[0] if self.opts else {});data[self.select]=o.get('value','');self.select=None
Form().feed(b.decode('utf-8',errors='replace'))
data['ctl00$cphCorpo$ctl01$txtPesquisa']='86510000';data['ctl00$cphCorpo$ctl01$imgPesquisa.x']='7';data['ctl00$cphCorpo$ctl01$imgPesquisa.y']='7'
# Only public form controls discovered in the served HTML.
b=get('ana-form-mucum-search.html',base+'gerarGrafico.aspx',urllib.parse.urlencode(data).encode(),'application/x-www-form-urlencoded')

data={}
Form().feed(b.decode('utf-8',errors='replace'))
data['ctl00$cphCorpo$ctl01$lstEstacoes']='291051520'
data['__EVENTTARGET']='ctl00$cphCorpo$ctl01$lstEstacoes'
data['__EVENTARGUMENT']=''
b=get('ana-form-mucum-data.html',base+'gerarGrafico.aspx',urllib.parse.urlencode(data).encode(),'application/x-www-form-urlencoded')
