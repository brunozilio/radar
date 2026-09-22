from pathlib import Path
import re,json,datetime,csv,xml.etree.ElementTree as ET,hashlib
P=Path(__file__).resolve().parent;s=(P/'raw/ana-form-mucum-data.html').read_text();data=json.loads(re.search(r'var chartData = (\[.*?\]);',s).group(1));dump=lambda f,x:(P/f).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
dump('ana-graph-extracted-data.json',data)
x=ET.fromstring((P/'raw/ana-legacy-20260921.xml').read_bytes());rows=[{z.tag.split('}')[-1]:z.text for z in el} for el in x.iter() if el.tag.split('}')[-1]=='DadosHidrometereologicos'];leg={r['DataHora']:r for r in rows}
comparisons=[]
for r in data:
 t=datetime.datetime.strptime(r['data'],'%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S');a=leg.get(t)
 if a is None:continue
 try:v=float(r['nivel']);w=float(a['NivelFinal'])
 except (ValueError,TypeError):continue
 comparisons.append({'timestamp_portal_source':r['data'],'timestamp_legacy_source':t,'portal_level_cm':v,'legacy_NivelFinal_cm':w,'legacy_QC':a.get('CQ_NivelFinal'),'difference_cm':v-w})
with (P/'portal-legacy-comparison.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(comparisons[0]) if comparisons else ['empty']);w.writeheader();w.writerows(comparisons)
a=json.loads((P/'raw/ana-mucum-arcgis.json').read_text())['features'][0]['attributes'];utc=datetime.datetime.fromtimestamp(a['Data_ult_dado']/1000,datetime.timezone.utc);local=utc.astimezone(datetime.timezone(datetime.timedelta(hours=-3)));ar=leg.get(local.strftime('%Y-%m-%d %H:%M:%S'))
result={'graph_rows':len(data),'graph_first':data[0]['data'],'graph_last':data[-1]['data'],'graph_timezone_declaration':'UTC-3','graph_level_unit':'cm','station_title':re.search(r'var titulo = "(.*?)";',s).group(1),'overlap_numeric_rows':len(comparisons),'equal_rows':sum(x['difference_cm']==0 for x in comparisons),'max_abs_difference_cm':max(abs(x['difference_cm']) for x in comparisons) if comparisons else None,'arcgis_attributes':a,'arcgis_timestamp_utc':utc.isoformat(),'arcgis_timestamp_brasilia':local.isoformat(),'legacy_same_instant':ar,'graph_delivery':'chartData embedded in server-rendered HTML returned by POST gerarGrafico.aspx after selecting station; no client request to ServiceANA found','contract_status':'CURRENT_PORTAL_EXPLICIT_UTC_MINUS03_CM_STATION_VERIFIED; LEGACY_EQUIVALENCE_CORROBORATED_NOT_EXPLICIT_ENDPOINT_CONTRACT','historical_availability':'NOT_VERIFIED','datum_continuity':'NOT_VERIFIED','eligibility_flags_changed':False}
dump('comparison-summary.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['legacy_same_instant','arcgis_attributes']},ensure_ascii=False,indent=2))
# Compact evidence with original line references; don't include session fields.
keys=['lblMensagemGmt','var titulo =','"title": "nível (cm)"','"dataProvider": chartData','PageMethods.set_path','getNameTimeZone','LoginService.setTimeZone','getTimezoneOffset']
e=[]
for name in ['ana-form-mucum-data.html','sace-root.html']:
 for i,line in enumerate((P/'raw'/name).read_text().splitlines(),1):
  if any(k in line for k in keys):e.append({'file':'raw/'+name,'line':i,'text':line.strip()})
dump('contract-evidence.json',e)
