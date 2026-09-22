from pathlib import Path
import json,hashlib,csv,datetime
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(f,x):(P/f).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
reg=pd.read_csv(P/'raw/ons-reservatorios.csv',sep=';');g=reg[reg.res_id.isin(['JIUHCA','JIUHMC','JIUHQJ'])].copy();g['derived_max_minus_min_hm3']=g.val_volmax-g.val_volmin;g['residual_vs_published_useful_hm3']=g.derived_max_minus_min_hm3-g.val_volutiltot;g.to_csv(P/'cadastro-three-reservoirs.csv',index=False)
files=list((R/'outputs/mucum-propagacao-2026-09-21/raw').glob('DADOS_HIDROLOGICOS_HO_*-ceran.csv'))
files += [R/'outputs/historico-vazoes-ceran/ceran-2020-07-source-values.csv',R/'outputs/historico-vazoes-ceran/ceran-2024-05-source-values.csv',R/'outputs/historico-cheia-setembro-2023/ons-ceran-source-values.csv']
inv=[];sources=[]
for f in files:
 sources.append({'path':str(f.relative_to(R)),'sha256':sha(f),'role':'existing local ONS source-derived rows; original download manifests in same acervo; not downloaded again'})
 d=pd.read_csv(f,sep=';' if 'DADOS_' in f.name else ',');
 for rid,a in d.groupby('id_reservatorio'):
  inv.append({'source':str(f.relative_to(R)),'id':rid,'rows':len(a),'first_original':str(a.din_instante.min()),'last_original':str(a.din_instante.max()),**{c:{'present':int(a[c].notna().sum()),'missing':int(a[c].isna().sum()),'min':float(a[c].min()) if a[c].notna().any() else None,'max':float(a[c].max()) if a[c].notna().any() else None} for c in ['val_nivelmontante','val_niveljusante','val_volumeutil']}})
for f in [R/'outputs/historico-vazoes-ceran/raw/ons-RO-AO-BR02-rev08.pdf',R/'outputs/historico-vazoes-ceran/raw/dictionary.json',R/'outputs/historico-vazoes-ceran/raw/catalog.json',R/'outputs/historico-vazoes-ceran/raw/ceran-situacao-2anos-2026.html',R/'outputs/pesquisa-castro-20260921T204404Z/raw/fepam-lpia-424-2025.pdf',R/'outputs/pesquisa-castro-20260921T204404Z/raw/ceran-obras-julho2026.html']:
 if f.exists():sources.append({'path':str(f.relative_to(R)),'sha256':sha(f),'role':'reused cached primary source; URL/acquisition provenance in origin acervo manifest'})
dump('historical-level-inventory.json',inv);dump('reused-source-manifest.json',sources)
agg=[]
for rid in ['JIUHCA','JIUHMC','JIUHQJ']:
 a=[x for x in inv if x['id']==rid and 'mucum-propagacao' in x['source']];agg.append({'id':rid,'rows_2025_2026':sum(x['rows'] for x in a),'level_present':sum(x['val_nivelmontante']['present'] for x in a),'level_missing':sum(x['val_nivelmontante']['missing'] for x in a),'volume_percent_present':sum(x['val_volumeutil']['present'] for x in a),'volume_percent_min':min(x['val_volumeutil']['min'] for x in a if x['val_volumeutil']['min'] is not None),'volume_percent_max':max(x['val_volumeutil']['max'] for x in a if x['val_volumeutil']['max'] is not None)})
dump('summary.json',{'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'current_registry':g.to_dict('records'),'registry_historical_version_available':False,'curve_full_table_found':False,'ONS_level_history':agg,'models_changed':False,'interpolation':False});print(agg)
