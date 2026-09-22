"""Immutable cumulative input snapshots for the local hourly experiment.

Latest receipts replace overlapping rows, including invalid revisions. Missing
rows never imply zero. Weather remains a model estimate, separate from gauges.
"""
import hashlib,json,os,re,xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np

TZ=ZoneInfo('America/Sao_Paulo')
FIELDS=['level','flow','rain','counter']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp(value):
    d=datetime.fromisoformat(value)
    return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()
def dump(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def number(value):
    try:
        v=float(value);return v if np.isfinite(v) and v>=0 else np.nan
    except (TypeError,ValueError):return np.nan

def merge_arrays(before,updates,fields):
    mapping={float(t):[before[k][i] for k in fields] for i,t in enumerate(before['times'])}
    mapping.update(updates)
    ts=np.array(sorted(mapping));a=np.array([mapping[t] for t in ts],dtype=float)
    if not len(ts):raise ValueError('No historical rows')
    return {'times':ts,**{k:a[:,i] for i,k in enumerate(fields)}}

def ana_rows(path,code,received):
    result={};future=0
    for el in ET.parse(path).getroot().iter():
        if el.tag.split('}')[-1]!='DadosHidrometereologicos':continue
        row={x.tag.split('}')[-1]:x.text for x in el}
        if row.get('CodEstacao')!=code:raise ValueError('ANA station identity mismatch')
        t=stamp(row['DataHora'])
        if t>received:future+=1;continue
        values=[]
        for field in ['NivelFinal','VazaoFinal','ChuvaFinal','ChuvaAcumAdotada']:
            values.append(number(row.get(field)) if row.get('CQ_'+field) in [None,'Dado aprovado'] else np.nan)
        values[0]/=100
        if values[2]>150:values[2]=np.nan
        if t in result and not np.allclose(result[t],values,equal_nan=True):raise ValueError('Conflicting ANA duplicate')
        result[t]=values
    if not result:raise ValueError('No admissible ANA rows')
    return result,future

def ceran_rows(path,received):
    result={};future=0
    for row in re.findall(r'<tr>(.*?)</tr>',path.read_text(),re.S):
        td=re.findall(r'<td>(.*?)</td>',row,re.S)
        if len(td)!=8:continue
        t=datetime.strptime(td[0],'%d/%m/%Y %H:%M:%S').replace(tzinfo=TZ).timestamp()
        if t>received:future+=1;continue
        values=[number(td[7]),number(td[3])]
        if t in result and not np.allclose(result[t],values,equal_nan=True):raise ValueError('Conflicting CERAN duplicate')
        result[t]=values
    if not result:raise ValueError('No admissible CERAN rows')
    return result,future

def merge_weather(before,after):
    if not isinstance(after,list) or len(after)!=5:raise ValueError('Expected five weather locations')
    if before is not None and len(before)!=len(after):raise ValueError('Weather location count changed')
    result=[]
    for i,new in enumerate(after):
        if new['utc_offset_seconds']!=-10800 or new['hourly_units']['precipitation']!='mm':raise ValueError('Weather timezone/units mismatch')
        old=before[i] if before else None
        if old and any(old.get(k)!=new.get(k) for k in ['latitude','longitude','utc_offset_seconds']):raise ValueError('Weather grid identity changed')
        values=dict(zip(old['hourly']['time'],old['hourly']['precipitation'])) if old else {}
        h=new['hourly']
        if len(h['time'])!=len(h['precipitation']) or len(set(h['time']))!=len(h['time']):raise ValueError('Weather row identity mismatch')
        if any(v is not None and (not np.isfinite(v) or v<0) for v in h['precipitation']):raise ValueError('Invalid model precipitation')
        values.update(zip(h['time'],h['precipitation']))
        times=sorted(values)
        result.append({**new,'hourly':{'time':times,'precipitation':[values[t] for t in times]},'role':'Cumulative collected model precipitation estimates; not observed rain or historical issuance proof.'})
    return result

def verify(directory):
    m=json.loads((directory/'manifest.json').read_text())
    for name,digest in m['files'].items():
        if Path(name).name!=name or sha(directory/name)!=digest:raise ValueError('History snapshot integrity failure')
    return m

def read_current(root):
    if not (root/'current.json').exists():return None
    pointer=json.loads((root/'current.json').read_text());directory=Path(pointer['directory'])
    if sha(directory/'manifest.json')!=pointer['manifest_sha256']:raise ValueError('History manifest changed')
    verify(directory)
    return directory

def build(out,root,baseline,weather_transition=None):
    """Caller holds the hourly lock. Publish pointer only after all files verify."""
    root.mkdir(parents=True,exist_ok=True)
    previous=read_current(root);parent=verify(previous) if previous else None
    manifest_path=out/'collection-manifest.json';items=json.loads(manifest_path.read_text())
    folder=out/'history';folder.mkdir(exist_ok=False)
    clocks=dict(parent['latest_collection_by_source']) if parent else {};audits=[]
    transition=json.loads(weather_transition.read_text()) if weather_transition else {}
    old=dict(np.load(baseline/'telemetria.npz'))
    # Scope matches the stations explicitly requested in this collection.
    requested={r['file'] for r in items if r['source']=='ANA'}
    stations={f'ana-{p.stem.split("-")[1]}-fresh.xml' for p in (baseline/'raw').glob('normalized-*.npz')}
    if not stations or requested!=stations:raise ValueError('Incomplete or changed ANA station set')
    expected=requested|{f'ceran-{s}-fresh.html' for s in ['julho','monte','castro']}|{f'weather-{s}.json' for s in ['gfs_seamless','ecmwf_ifs025','icon_global']}
    selected={r['file']:r for r in items if r['file'] in expected}
    if set(selected)!=expected:raise ValueError('Incomplete history source set')
    if parent and set(clocks)!=expected:raise ValueError('History source set changed')
    for name,item in selected.items():
        if 'error' in item:raise ValueError('Failed source cannot replace history')
        path=out/'raw'/name
        if sha(path)!=item['sha256']:raise ValueError('Raw source hash mismatch')
        received=stamp(item['collected_at'])
        if name in clocks and received<stamp(clocks[name]):raise ValueError('Older receipt cannot replace newer history')
        clocks[name]=item['collected_at']
        if name.startswith('ana-'):
            code=name.split('-')[1];filename=f'ana-{code}.npz'
            seed=previous/filename if previous else baseline/'raw'/f'normalized-{code}.npz'
            before=dict(np.load(seed));updates,future=ana_rows(path,code,received)
            merged=merge_arrays(before,updates,FIELDS);np.savez_compressed(folder/filename,**merged)
        elif name.startswith('ceran-'):
            plant=name.split('-')[1];filename=f'ceran-{plant}.npz'
            before=dict(np.load(previous/filename)) if previous else {'times':old['times'],'Q':old[plant+':Q'],'I':old[plant+':I']}
            updates,future=ceran_rows(path,received);merged=merge_arrays(before,updates,['Q','I']);np.savez_compressed(folder/filename,**merged)
        else:
            before=json.loads((previous/name).read_text()) if previous else None
            after=json.loads(path.read_text());migrated=False
            if before and name in transition.get('sources',{}):
                rule=transition['sources'][name]
                if sha(previous/name)!=rule['previous_sha256'] or sha(path)!=rule['new_sha256']:raise ValueError('Weather transition does not match exact saved inputs')
                locations=[[r['latitude'],r['longitude']] for r in after]
                if locations!=rule['expected_locations']:raise ValueError('Weather transition grid differs from approved historical grid')
                if any(not set(oldloc['hourly']['time'])<=set(newloc['hourly']['time']) for oldloc,newloc in zip(before,after)):raise ValueError('Weather transition would lose collected history')
                before=None;migrated=True
            value=merge_weather(before,after);dump(folder/name,value)
            audits.append({'source':name,'kind':'model_estimate','retained_hours':len(value[0]['hourly']['time']),'explicit_grid_transition':migrated});continue
        audits.append({'source':name,'retained_rows':len(merged['times']),'incoming_rows':len(updates),'future_observations_excluded':future})
    files={p.name:sha(p) for p in sorted(folder.iterdir())}
    metadata={'schema':1,'parent_directory':str(previous) if previous else None,'parent_manifest_sha256':sha(previous/'manifest.json') if previous else None,'collection_manifest':str(manifest_path.resolve()),'collection_manifest_sha256':sha(manifest_path),'latest_collection_by_source':clocks,'files':files,'audit':audits,'limitations':['Baseline CERAN input is an existing 15-minute as-of grid; new receipts retain actual source timestamps.','Model weather is not observed rain; unknown precipitation remains unknown.','Snapshot records information available by collection; it does not establish historical availability of the baseline.']}
    if weather_transition:
        metadata['explicit_weather_transition']={'path':str(weather_transition.resolve()),'sha256':sha(weather_transition),'policy':transition}
    dump(folder/'manifest.json',metadata);verify(folder)
    pointer={'directory':str(folder.resolve()),'manifest_sha256':sha(folder/'manifest.json')}
    temporary=root/'current.pending';dump(temporary,pointer);os.replace(temporary,root/'current.json')
    return folder.resolve()
