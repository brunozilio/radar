"""Read-only public data collection. No cookies, credentials, provider writes or alerts."""
import urllib.request, urllib.parse, concurrent.futures, pathlib,json,datetime,hashlib
P=pathlib.Path(__file__).resolve().parents[1]/'outputs/mucum-bacia-2026-09-21'; R=P/'raw'
headers={'User-Agent':'Mozilla/5.0','Referer':'https://sigmameteorologia.com/nowcasting/','Accept':'*/*'}
manifest=[]
def get(name,url):
 try:
  response=urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=25); b=response.read();(R/name).write_bytes(b)
  result={'file':name,'url':url,'status':response.status,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 except Exception as e:result={'file':name,'url':url,'error':str(e)}
 manifest.append(result);return result
if __name__=='__main__':
 rs=json.loads((R/'bho5-rivers-0.json').read_text())['features'];by={f['attributes']['COTRECHO']:f for f in rs};ids={125779}
 while True:
  more={k for k,f in by.items() if f['attributes']['NUTRJUS'] in ids}
  if more<=ids:break
  ids|=more
 print('BHO5 reaches',len(ids),'area',sum(by[k]['attributes']['NUAREACONT'] for k in ids),flush=True)
 (R/'upstream5-reach-ids.json').write_text(json.dumps(sorted(ids)))
 args={'f':'geojson','outFields':'COTRECHO,COBACIA,COCURSODAG,NUAREACONT','outSR':4326,'where':'COTRECHO IN ('+','.join(map(str,ids))+')','returnGeometry':'true'}
 urls={'upstream-basins.geojson':'https://portal1.snirh.gov.br/arcgis/rest/services/SPR/BHO2017_5K_AREADRENAGEM/MapServer/0/query?'+urllib.parse.urlencode(args)}
 # Networks observed in the user's HAR. Snapshot hour is the current local hour.
 now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))); slot=now.strftime('%H00'); day=now.strftime('%Y-%m-%d')
 har=json.load(open('/Users/brunozilio/Downloads/SIGMA.har'))['log']['entries']
 networks=set()
 for e in har:
  u=urllib.parse.urlsplit(e['request']['url']); parts=u.path.split('/')
  if u.netloc=='sigmameteorologia.com' and len(parts)==5 and parts[1]=='produtos' and parts[-1].endswith('.txt') and parts[2]!='stations':networks.add(parts[2])
 for net in networks:urls['sigma-'+net+'.txt']=f'https://sigmameteorologia.com/produtos/{net}/{day}/{slot}.txt'
 for sid in [3,32,4,54,55]:urls[f'sace-{sid}.csv']=f'https://sace.sgb.gov.br/api/dados/taquari_{sid}_cota.csv'
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
  for result in ex.map(lambda kv:get(*kv),urls.items()):print(result['file'],result.get('status',result.get('error')),result.get('bytes'),flush=True)
 (R/'collection-manifest.json').write_text(json.dumps(manifest,indent=2))
