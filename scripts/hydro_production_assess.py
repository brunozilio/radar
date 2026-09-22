"""Classify and audit production hydrological readings; never modifies production."""
from pathlib import Path
import json,re,csv,collections
from datetime import datetime,timedelta
from shapely.geometry import shape,Point
from hydro_model import basin_group
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/mucum-bacia-2026-09-21';RAW=OUT/'raw'
def rows(name):return [r for b in json.loads((RAW/f'producao/{name}.json').read_text()) for r in b['results']]
def run():
    rain=rows('chuva');codes={r['station'] for r in rain}
    old=json.loads((RAW/'stations-inside.json').read_text());oldby={s['id']:s for s in old}
    basins=json.loads((RAW/'upstream-basins.geojson').read_text())['features']
    src=(ROOT/'lib/hydro.ts').read_text();meta={}
    # Split literal station objects by code, allowing nested threshold objects.
    for block in re.split(r'(?=code: "\d+")',src):
        code=re.search(r'^code: "(\d+)"',block);lat=re.search(r'latitude: ([\d.-]+)',block);lon=re.search(r'longitude: ([\d.-]+)',block)
        if code and lat and lon:
            name=re.search(r'name: "([^"]+)"',block)
            meta[code[1]]={'id':code[1],'name':name[1],'lat':float(lat[1]),'lon':float(lon[1])}
    for code,s in oldby.items():meta.setdefault(code,{k:s[k] for k in ['id','name','lat','lon']})
    for f in RAW.glob('sigma-*.txt'):
        for line in f.read_text().splitlines():
            a=line.split()
            if len(a)>31 and a[2] in codes:
                meta.setdefault(a[2],{'id':a[2],'name':a[31].replace('_',' '),'lat':float(a[0]),'lon':float(a[1])})
    out=[]
    for code in sorted(codes):
        s=meta[code];hit=[f for f in basins if shape(f['geometry']).covers(Point(s['lon'],s['lat']))]
        rr=sorted([r for r in rain if r['station']==code],key=lambda r:datetime.fromisoformat(r['timestamp']))
        latest=rr[-1];end=datetime.fromisoformat(latest['timestamp']);recent=[r for r in rr if end-timedelta(hours=6)<datetime.fromisoformat(r['timestamp'])<=end]
        valid=[r['rain'] for r in recent if r['rain'] is not None and 0<=r['rain']<=150]
        ott=str(hit[0]['properties']['COBACIA']) if hit else ''
        out.append({**s,'inside':bool(hit),'already_sigma':code in oldby,'ottobacia':ott,'subbacia':basin_group(ott) if hit else 'jusante/fora',
                    'last':latest['timestamp'],'records':len(rr),'rain_sum_last6h_records_mm':round(sum(valid),2) if valid else None,
                    'records_last6h':len(recent),'valid_rain_records_last6h':len(valid),'quality_last':latest['quality'],
                    'note':'Soma dos registros ChuvaFinal na janela; sem preenchimento de lacunas. Qualidade do banco nao garante qualidade de cada variavel.'})
    (OUT/'producao-estacoes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    with (OUT/'producao-chuva.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    extra=[r for r in out if r['inside'] and not r['already_sigma']]
    summary={'production_rain_stations':len(out),'in_basin':sum(r['inside'] for r in out),'extra_station_ids':len(extra),'unique_catalogue_ids':len(old)+len(extra),'rain_rows':len(rain),'ceran_rows':len(rows('ceran')),'sace_rows_deduplicated':len(rows('sace')),'production_read_only':True,'rows_written':0,
             'station_identity_limit':'Unique catalogue IDs; nearby or co-located instruments may not represent independent sites.'}
    (OUT/'producao-resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(summary)
if __name__=='__main__':run()
