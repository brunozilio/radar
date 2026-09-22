"""Normalize primary hourly/quarter-hour telemetry and trace drainage connectivity."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,csv,xml.etree.ElementTree as ET,collections,math,re
import numpy as np
from shapely.geometry import shape,Point,LineString
from shapely.ops import transform,unary_union
from pyproj import Transformer
from scipy.spatial import cKDTree
from hydro_model import basin_group,asof
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/mucum-propagacao-2026-09-21';RAW=OUT/'raw';OLD=ROOT/'outputs/mucum-bacia-2026-09-21'
TZ=timezone(timedelta(hours=-3));STEP=900
def epoch(t):return datetime.fromisoformat(t).replace(tzinfo=TZ).timestamp()
def iso(t):return datetime.fromtimestamp(float(t),TZ).isoformat()
def number(x):
    try:v=float(x);return v if np.isfinite(v) and v>=0 else np.nan
    except (ValueError,TypeError):return np.nan
def savecsv(path,rows):
    if not rows:return
    with path.open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def load_ana(code):
    cache=RAW/f'normalized-{code}.npz';sources=[p for p in [RAW/f'ana-{code}-2025.xml',RAW/f'ana-{code}.xml',RAW/f'ana-{code}-latest.xml'] if p.exists()]
    if cache.exists() and cache.stat().st_mtime>=max(p.stat().st_mtime for p in sources):return dict(np.load(cache))
    data={};flags=collections.Counter()
    for _,el in (entry for source in sources for entry in ET.iterparse(source,events=['end'])):
        if el.tag.split('}')[-1]!='DadosHidrometereologicos':continue
        d={x.tag.split('}')[-1]:x.text for x in el};t=epoch(d['DataHora'])
        if t not in data:data[t]=[np.nan]*4
        for k,(field,qf) in enumerate([('NivelFinal','CQ_NivelFinal'),('VazaoFinal','CQ_VazaoFinal'),('ChuvaFinal','CQ_ChuvaFinal'),('ChuvaAcumAdotada','CQ_ChuvaAcumAdotada')]):
            flags[str(d.get(qf))]+=1;v=number(d.get(field))
            if d.get(qf) not in ['Dado aprovado',None]:v=np.nan
            if k==0:v/=100
            if k==2 and v>150:v=np.nan
            if np.isfinite(v):data[t][k]=v
        el.clear()
    times=np.array(sorted(data));values=np.array([data[t] for t in times]);result={'times':times,'level':values[:,0],'flow':values[:,1],'rain':values[:,2],'counter':values[:,3]}
    np.savez_compressed(cache,**result);return result
def geometry():
    allfeatures=json.loads((OLD/'raw/bho5-rivers-0.json').read_text())['features'];by={f['attributes']['COTRECHO']:f for f in allfeatures}
    ids=set(json.loads((OLD/'raw/upstream5-reach-ids.json').read_text()));basins=json.loads((OLD/'raw/upstream-basins.geojson').read_text())['features']
    project=Transformer.from_crs(4326,31982,always_xy=True).transform
    lines={k:transform(project,LineString(by[k]['geometry']['paths'][0])) for k in ids}
    outlet=125779;gauge=Point(project(-51.86722,-29.16694));og=lines[outlet]
    def from_upstream(k):
        coords=list(lines[k].coords);nxt=by[k]['attributes']['NUTRJUS'];nextline=lines.get(nxt)
        if nextline is None:
            nxtf=by.get(nxt);nextline=transform(project,LineString(nxtf['geometry']['paths'][0])) if nxtf else None
        if nextline is not None and Point(coords[0]).distance(nextline)<Point(coords[-1]).distance(nextline):coords.reverse()
        return LineString(coords)
    lines={k:from_upstream(k) for k in ids};outlet_offset=lines[outlet].project(gauge)
    def distance(k):
        if k==outlet:return outlet_offset
        return lines[k].length+distance(by[k]['attributes']['NUTRJUS'])
    lengths={k:distance(k) for k in ids}
    inv=list(csv.DictReader((OLD/'inventario-completo-122.csv').open()));records=[]
    for s in inv:
        point=Point(float(s['lon']),float(s['lat']));hit=next((f for f in basins if shape(f['geometry']).covers(point)),None)
        if hit is None:continue
        k=hit['properties']['COTRECHO'];p=transform(project,point)
        if s['id'] in ['86510000','86472000','86472600','86500000','86471000','86160000']:
            expected='Rio Carreiro' if s['id']=='86500000' else 'Rio Tainhas' if s['id']=='86160000' else 'Rio Taquari'
            choices=[rid for rid in ids if by[rid]['attributes']['NORIOCOMP']==expected]
            k=min(choices,key=lambda rid:p.distance(lines[rid]))
        line=lines[k]
        records.append({**s,'trecho':k,'rio':by[k]['attributes']['NORIOCOMP'],'distancia_rede_km':max(0,(lengths[k]-line.project(p))/1000),
                        'distancia_sensor_canal_m':p.distance(line),'area_montante_km2':by[k]['attributes']['NUAREAMONT'],
                        'nota_distancia':'Distancia pelo canal desde projecao na linha da microbacia; nao inclui escoamento na encosta.'})
    savecsv(OUT/'estacoes-conectividade.csv',records)
    (OUT/'grafo-drenagem.json').write_text(json.dumps({'outlet':outlet,'links':[{'id':k,'downstream':by[k]['attributes']['NUTRJUS'],'length_km':lines[k].length/1000,'distance_to_gauge_km':lengths[k]/1000,'area_km2':by[k]['attributes']['NUAREACONT'],'group':basin_group(by[k]['attributes']['COBACIA'])} for k in sorted(ids)]},indent=2))
    return basins,project,records
def run():
    basins,project,inventory=geometry();stations=[s for s in json.loads((OLD/'producao-estacoes.json').read_text()) if s['inside']]
    data={s['id']:load_ana(s['id']) for s in stations};last=max(data['86510000']['times']);start=min(data['86510000']['times']);grid=np.arange(start,math.floor(last/STEP)*STEP+1,STEP)
    normalized={};audit=[]
    for code,d in data.items():
        levels=asof(d['times'],d['level'],grid,max_age=1800);flow=asof(d['times'],d['flow'],grid,max_age=1800)
        # Do not carry a completed rain interval into an unobserved next hour.
        from hydro_rain_windows import observed_rain_windows
        tr=d['times'];amount,coverage=observed_rain_windows(tr,d['rain'],grid,[1])[1]
        hour=np.where(coverage>=.75,amount,np.nan)
        normalized[f'{code}:H']=levels;normalized[f'{code}:Q']=flow;normalized[f'{code}:P']=hour
        audit.append({'id':code,'start':iso(min(tr)),'end':iso(max(tr)),'n_records':len(tr),'level_min':float(np.nanmin(d['level'])),'level_max':float(np.nanmax(d['level'])),'rain_hour_coverage':float(np.isfinite(hour).mean()),'level_hour_coverage':float(np.isfinite(levels).mean())})
    savecsv(OUT/'auditoria-ana.csv',audit)
    # ONS hour labels are interval end, kept as published; no advancing data by one hour.
    ons={};rawrows=[]
    for f in sorted(RAW.glob('DADOS_HIDROLOGICOS_HO_*-ceran.csv')):
        for r in csv.DictReader(f.open(),delimiter=';'):
            name=r['nom_reservatorio'].strip();code={'14 DE JULHO':'julho','MONTE CLARO':'monte','CASTRO ALVES':'castro'}[name];t=epoch(r['din_instante'])
            ons[(code,t)]={'Q':number(r['val_vazaodefluente']),'I':number(r['val_vazaoafluente']),'U':number(r['val_nivelmontante']),'D':number(r['val_niveljusante'])}
    # CERAN most recent reports bridge ONS reporting delay; overlapping differences remain audited.
    overlaps=[]
    for batch in json.loads((OLD/'raw/producao/ceran.json').read_text()):
        for r in batch['results']:
            key=(r['plant_id'],datetime.fromisoformat(r['timestamp']).timestamp());vals={'Q':r['outflow'],'I':r['inflow'],'U':r['upstream_level'],'D':r['downstream_level']}
            if key in ons:overlaps.append({'plant':key[0],'timestamp':iso(key[1]),'ons_Q':ons[key]['Q'],'ceran_Q':vals['Q'],'difference':vals['Q']-ons[key]['Q']})
            # Current source can be instantaneous while ONS is hourly. Keep ONS at overlaps.
            else:ons[key]=vals
    savecsv(OUT/'ons-ceran-conferencia.csv',overlaps)
    for plant in ['julho','monte','castro']:
        path=RAW/f'ceran-current-{plant}.html'
        if not path.exists():continue
        for tr in re.findall(r'<tr>(.*?)</tr>',path.read_text(),re.S):
            td=re.findall(r'<td>(.*?)</td>',tr,re.S)
            if len(td)!=8:continue
            t=datetime.strptime(td[0],'%d/%m/%Y %H:%M:%S').replace(tzinfo=TZ).timestamp();key=(plant,t)
            if key not in ons:ons[key]={'Q':number(td[7]),'I':number(td[3]),'U':number(td[1]),'D':number(td[2])}
    for plant in ['julho','monte','castro']:
        times=sorted(t for p,t in ons if p==plant)
        for variable in ['Q','I','U','D']:
            values=[ons[(plant,t)][variable] for t in times]
            normalized[f'{plant}:{variable}']=asof(np.array(times),values,grid,max_age=5400)
    # Spatial rainfall weights computed within each polygon group with all ANA stations.
    polygon=transform(project,unary_union([shape(f['geometry']) for f in basins]));xx,yy=np.meshgrid(np.arange(polygon.bounds[0]+1000,polygon.bounds[2],2000),np.arange(polygon.bounds[1]+1000,polygon.bounds[3],2000));xy=np.array([(x,y) for x,y in zip(xx.ravel(),yy.ravel()) if polygon.covers(Point(x,y))]);coords=[project(s['lon'],s['lat']) for s in stations];dist,nearest=cKDTree(coords).query(xy)
    rain=np.column_stack([normalized[s['id']+':P'] for s in stations]);rainmeta=[]
    for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
        region=transform(project,unary_union([shape(f['geometry']) for f in basins if basin_group(f['properties']['COBACIA'])==group]));inside=np.array([region.covers(Point(x,y)) for x,y in xy]);w=np.bincount(nearest[inside],minlength=len(stations)).astype(float);w/=w.sum();coverage=np.sum(w*np.isfinite(rain),axis=1)
        vals=np.nansum(rain*w,axis=1)/np.maximum(coverage,1e-10);vals[coverage<.5]=np.nan
        normalized[group+':P']=vals;normalized[group+':coverage']=coverage
        rainmeta.append({'group':group,'area_km2':region.area/1e6,'weights':{s['id']:float(w[i]) for i,s in enumerate(stations) if w[i]>0},'latest_coverage':float(coverage[-1]),'latest_mm_h':float(vals[-1]) if np.isfinite(vals[-1]) else None})
    np.savez_compressed(OUT/'telemetria.npz',times=grid,**normalized)
    (OUT/'chuva-pesos.json').write_text(json.dumps(rainmeta,ensure_ascii=False,indent=2));(OUT/'metadata.json').write_text(json.dumps({'start':iso(start),'end':iso(last),'step_seconds':STEP,'stage_target':'86510000','ana_stations':len(stations),'ons_records':len(ons),'created_at':datetime.now(TZ).isoformat()},indent=2))
    print('NORMALIZED',len(grid),'quarter hours',len(normalized),'series','last Muçum',iso(last),data['86510000']['level'][-1],flush=True)
if __name__=='__main__':run()
