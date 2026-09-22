import json,hashlib,datetime,math,pathlib,urllib.parse
ROOT=pathlib.Path('/Users/brunozilio/Documents/radar')
OUT=ROOT/'outputs/pesquisa-contrato-chuva-prevista-20260921'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def intervals(times,indices):
 out=[]
 for i in indices:
  if out and i==out[-1][1]+1:out[-1][1]=i
  else:out.append([i,i])
 return [{'start':times[a],'end':times[b],'hours':b-a+1} for a,b in out]
audit=[]
for model,rel in [
 ('gfs_seamless','outputs/mucum-propagacao-2026-09-21/raw/chuva-previsao-historica-gfs_seamless.json'),
 ('ecmwf_ifs025','outputs/mucum-propagacao-2026-09-21/raw/chuva-previsao-historica-ecmwf_ifs025.json'),
 ('icon_global','outputs/mucum-atualizacao-15h-2026-09-21/nwp-historical-icon.json')]:
 p=ROOT/rel;data=json.loads(p.read_text());side=p.with_name(p.stem+'-fonte.json')
 source=json.loads(side.read_text()) if side.exists() else None
 a={'model_label_from_local_configuration':model,'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p),'source_sidecar':source,'source_sidecar_sha256':digest(side) if side.exists() else None,'original_url_verified':bool(source),'locations':[]}
 for n,d in enumerate(data):
  h=d['hourly'];t=h['time'];v=h['precipitation_previous_day1'];bad=[i for i,x in enumerate(v) if x is None or not math.isfinite(x)]
  a['locations'].append({'index':n,'latitude':d['latitude'],'longitude':d['longitude'],'timezone':d['timezone'],'utc_offset_seconds':d['utc_offset_seconds'],'units':d['hourly_units'],'first':t[0],'last':t[-1],'count':len(v),'nonfinite_count':len(bad),'nonfinite_intervals':intervals(t,bad),'negative_count':sum(x is not None and x<0 for x in v),'duplicate_time_count':len(t)-len(set(t)),'top_level_keys':list(d),'per_record_run_initialization_present':False,'per_record_publication_present':False})
 audit.append(a)
(OUT/'local-input-audit.json').write_text(json.dumps({'audited_at_utc':now,'inputs':audit},ensure_ascii=False,indent=2)+'\n')
contract={'audited_at_utc':now,'scope':'Development-only retrospective forecasts, no promotion or eligibility change','variable':'precipitation_previous_day1','unit':'mm','valid_time_definition':'Sum of precipitation during preceding hour, ending at timestamp T','nominal_lead_hours':24,'origin':'O','accumulation':'sum(P_previous_day1(O+h) for h in 1..W), W in {3,6,9,12}','nominal_reference_formula':'T-24h = O+h-24h; NOT a certified per-record initialization timestamp','nominal_hours_before_origin':[{ 'h':h,'nominal_hours_before_origin':24-h} for h in range(1,13)],'compatible_with_no_post_origin_initializations_under_documented_contract':True,'individual_run_identity_verified':False,'historical_publication_verified':False,'archive_version_immutability_verified':False,'historical_availability_status':'assumed; not certified','live_distribution_difference':'Previous Runs fixed-lead mixed vintages versus live Forecast API most recent stitched runs','no_new_observations_inserted':True}
(OUT/'timing-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
m=json.loads((OUT/'source-manifest.json').read_text())
(OUT/'source-manifest.json').write_text(json.dumps({'direct_http_attempts':m,'web_tool_extraction':{'file':'sources/open-meteo-web-extract.txt','sha256':digest(OUT/'sources/open-meteo-web-extract.txt'),'preserved_at_utc':now,'collected_date_utc':'2026-09-21','exact_web_request_timestamp_not_exposed':True,'format':'Public web tool text extraction; not raw HTTP body. Original HTML requests returned HTTP 403.','urls':['https://open-meteo.com/en/docs/previous-runs-api','https://open-meteo.com/en/docs/single-runs-api','https://open-meteo.com/en/docs/model-updates','https://open-meteo.com/en/docs']}},ensure_ascii=False,indent=2)+'\n')
for a in audit: print(a['model_label_from_local_configuration'],[(x['count'],x['nonfinite_count'],x['nonfinite_intervals']) for x in a['locations'][:1]])

