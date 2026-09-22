from pathlib import Path
import json,hashlib,datetime as dt,urllib.request,urllib.error,urllib.parse,concurrent.futures,shutil
R=Path(__file__).resolve().parent;W=R.parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n')
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
def fetch(q):
 name=f"ana-{q['station']}-{q['start']}--{q['end']}.xml";p=R/'raw'/name;rp=p.with_suffix('.receipt.json');ap=p.with_suffix('.attempt.json')
 if rp.exists():
  m=json.loads(rp.read_text());assert p.exists() and sha(p.read_bytes())==m['sha256'];return m
 if ap.exists():return {**q,'status':'prior_attempt_without_receipt_not_retried','attempt_file':str(ap.relative_to(R))}
 url='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urllib.parse.urlencode({'codEstacao':q['station'],'dataInicio':dt.date.fromisoformat(q['start']).strftime('%d/%m/%Y'),'dataFim':dt.date.fromisoformat(q['end']).strftime('%d/%m/%Y')})
 m={**q,'url':url,'started_utc':now(),'automatic_retries':0,'automatic_redirects':False,'reused':False};dump(ap,m)
 try:
  opener=urllib.request.build_opener(NoRedirect)
  with opener.open(url,timeout=45) as r:body=r.read();m.update(http_status=r.status,headers=dict(r.headers),final_url=r.url,status='received')
 except urllib.error.HTTPError as e:body=e.read();m.update(http_status=e.code,headers=dict(e.headers),status='http_error',error=str(e))
 except Exception as e:body=b'';m.update(http_status=None,headers={},status='network_error',error=repr(e))
 p.write_bytes(body);m.update(finished_utc=now(),file=str(p.relative_to(R)),bytes=len(body),sha256=sha(body));dump(rp,m)
 print(q['station'],q['start'],m['http_status'],len(body),flush=True);return m
def main():
 plan=json.loads((R/'plan.json').read_text());(R/'raw').mkdir(exist_ok=True);manifest=[]
 for q in plan['reuse']:
  src=W/q['source_path'];assert sha(src.read_bytes())==q['sha256'];name=f"reused-{q['station']}-{q['start']}--{q['end']}.xml";p=R/'raw'/name
  if p.exists():assert sha(p.read_bytes())==q['sha256']
  else:shutil.copyfile(src,p)
  m={**q,**q['original_receipt'],'station':q['station'],'window':q['window'],'start':q['start'],'end':q['end'],'reused':True,'file':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'status':'reused','original_source_path':q['source_path'],'original_receipt_path':q['receipt_path'],'copied_utc':now()}
  dump(p.with_suffix('.receipt.json'),m);manifest.append(m)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for m in pool.map(fetch,plan['new_requests']):manifest.append(m)
 dump(R/'source-manifest.json',manifest)
 print('Complete',len(manifest),'sources',flush=True)
if __name__=='__main__':main()
