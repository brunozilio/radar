from pathlib import Path
import urllib.request,urllib.error,datetime,hashlib,json,sys
P=Path(__file__).resolve().parent
mfile=P/'manifest.json'
m=json.loads(mfile.read_text()) if mfile.exists() else []
for name,url in zip(sys.argv[1::2],sys.argv[2::2]):
 r={'file':'raw/'+name,'url':url,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 public hydrology research'}),timeout=25) as q:
   b=q.read();r.update(status=q.status,final_url=q.url,headers=dict(q.headers))
  (P/r['file']).write_bytes(b);r.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());print(name,r['status'],len(b))
 except Exception as e:r['error']=str(e);print(name,str(e))
 m.append(r);mfile.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
