"""Reproducible, causal experimental hydrology assessment. Never publishes alerts.
PYTHONPATH=/tmp/radar-hydro-libs:/tmp/radar-plot-libs python3 scripts/hydro_model.py
"""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,csv,math,re,collections
import numpy as np
from shapely.geometry import shape,Point,mapping
from shapely.ops import unary_union,transform
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.linalg import solve

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/mucum-bacia-2026-09-21';RAW=OUT/'raw'
TZ=timezone(timedelta(hours=-3));HOUR=3600
GROUPS=['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']
PUBLIC={'cemaden','inmet','dcrs','sgb_cprm','epagri'}

def stamp(s):return datetime.strptime(s,'%Y-%m-%d_%H:%M').replace(tzinfo=TZ).timestamp()
def iso(t):return datetime.fromtimestamp(float(t),TZ).isoformat()
def asof(times,values,grid,max_age=3900):
    if not len(times):return np.full(len(grid),np.nan)
    ii=np.searchsorted(times,grid,side='right')-1;safe=np.maximum(ii,0)
    good=(ii>=0)&(grid-times[safe]<=max_age)
    return np.where(good,np.array(values)[safe],np.nan)
def save_csv(name,rows):
    if not rows:return
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def read_station(sid):
    rows={}
    for f in sorted(RAW.glob(f'station-{sid}-*.txt')):
        for line in f.read_text().splitlines():
            a=line.split()
            if len(a)<45 or a[2]!=sid:continue
            try:t=stamp(a[3]);cum=float(a[21]);hour=float(a[20]);level=float(a[45]) if len(a)>45 else np.nan
            except (ValueError,OverflowError):continue
            if t>datetime.now(TZ).timestamp()+60:continue
            rows[t]={'cum':cum if 0<=cum<1000 else np.nan,'hour':hour if 0<=hour<=150 else np.nan,'level':level if 0<=level<40 else np.nan}
    times=np.array(sorted(rows));return times,{k:np.array([rows[t][k] for t in times]) for k in ['cum','hour','level']}
def moving_sum(a,n):
    out=np.full_like(a,np.nan)
    for i in range(n-1,len(a)):
        sub=a[i-n+1:i+1]
        if np.all(np.isfinite(sub)):out[i]=sub.sum(axis=0)
    return out
def basin_group(code):
    code=str(code)
    return 'Carreiro' if code.startswith('7866') else 'Prata-Turvo' if code.startswith('7868') else 'Tainhas' if code.startswith('78696') else 'Alto Antas' if code.startswith('7869') else 'Baixo Antas'

def run():
    stations=json.loads((RAW/'stations-inside.json').read_text())
    basins=json.loads((RAW/'upstream-basins.geojson').read_text());polygon=unary_union([shape(f['geometry']) for f in basins['features']])
    (OUT/'bacia-mucum.geojson').write_text(json.dumps({'type':'Feature','properties':{'source':'ANA BHO2017 5K','outlet_reach':125779,'reach_upstream_area_km2':16047.2535,'limit':'includes full local outlet catchment of 12.828 km2; not a surveyed gauge watershed'},'geometry':mapping(polygon)}))
    project=Transformer.from_crs(4326,31982,always_xy=True).transform
    pp=transform(project,polygon)
    # Deterministic 2 km spatial quadrature of nearest-station areas, not sums of rainfall.
    xx,yy=np.meshgrid(np.arange(pp.bounds[0]+1000,pp.bounds[2],2000),np.arange(pp.bounds[1]+1000,pp.bounds[3],2000))
    gridxy=np.array([(x,y) for x,y in zip(xx.ravel(),yy.ravel()) if pp.covers(Point(x,y))])
    public=[s for s in stations if s['network'] in PUBLIC]
    coordinates=np.array([project(s['lon'],s['lat']) for s in public])
    nearest_dist,nearest=cKDTree(coordinates).query(gridxy);weights=np.bincount(nearest,minlength=len(public))/len(nearest)
    # Boundary uncertainty: local drainage polygon reaches beyond the exact gauge along 12.8 km2.
    station_data={s['id']:read_station(s['id']) for s in stations}
    hydro={}
    agreement=[]
    for code,sid in [('86510000',3),('86472000',4),('86472600',32),('86500000',54)]:
        ts,vals=station_data.get(code,read_station(code));d={t:v for t,v in zip(ts,vals['level']) if np.isfinite(v)}
        for batch in json.loads((RAW/'producao/sace.json').read_text()):
            for row in batch['results']:
                if row['station'].removeprefix('sace-')==code and 0<=row['level']<40:
                    d[datetime.fromisoformat(row['timestamp']).timestamp()]=row['level']
        for row in csv.DictReader((RAW/f'sace-{sid}.csv').open(),delimiter=';'):
            t=datetime.fromisoformat(row['data_hora_medicao']).replace(tzinfo=TZ).timestamp();v=float(row['indice'])/100
            if not 0<=v<40:continue
            if t in d:agreement.append({'station':code,'timestamp':iso(t),'sigma_m':d[t],'sace_m':v,'difference_m':abs(d[t]-v)})
            d[t]=v # direct primary source takes precedence at overlapping timestamps
        hydro[code]=d
    save_csv('comparacao-sigma-sace.csv',agreement)
    last=max(hydro['86510000']);end=math.floor(last/HOUR)*HOUR
    start=datetime(2026,7,25,tzinfo=TZ).timestamp();grid=np.arange(start,end+1,HOUR)
    levels={k:asof(np.array(sorted(d)),[d[t] for t in sorted(d)],grid,max_age=2700) for k,d in hydro.items()}
    # Hourly rain field is checked against elapsed counter changes below; negatives are missing.
    rain_columns=[]
    for station in public:
        ts,values=station_data[station['id']]
        hourly=asof(ts,values['hour'],grid)
        # Derive missing hourly values from same-day counter differences only.
        # Uses two past observations; never interpolates from the future or treats missing as dry.
        ii=np.searchsorted(ts,grid,side='right')-1
        jj=np.searchsorted(ts,grid-HOUR,side='right')-1
        for k,(a,b) in enumerate(zip(ii,jj)):
            if np.isfinite(hourly[k]) or min(a,b)<0:continue
            elapsed=ts[a]-ts[b]
            if not 1800<=elapsed<=5400 or grid[k]-ts[a]>3900 or grid[k]-HOUR-ts[b]>3900:continue
            if datetime.fromtimestamp(ts[a],TZ).date()!=datetime.fromtimestamp(ts[b],TZ).date():continue
            change=values['cum'][a]-values['cum'][b]
            if np.isfinite(change) and 0<=change<=150:hourly[k]=change*HOUR/elapsed
        rain_columns.append(hourly)
    rain=np.column_stack(rain_columns)
    # Flag stuck/near-zero gauges ONLY from observations available at that origin.
    qc_excluded=np.zeros_like(rain,dtype=bool)
    distances=np.linalg.norm(coordinates[:,None,:]-coordinates[None,:,:],axis=2)
    for j in range(len(public)):
        neighbors=np.where((distances[j]>250)&(distances[j]<25000))[0]
        if len(neighbors)<3:continue
        for i in range(5,len(grid)):
            own=rain[i-5:i+1,j];near=rain[i-5:i+1,neighbors]
            totals=np.where(np.sum(np.isfinite(near),axis=0)>=5,np.nansum(near,axis=0),np.nan)
            valid=totals[np.isfinite(totals)]
            if len(valid)>=3 and np.isfinite(own).sum()>=5 and np.nansum(own)<1 and np.median(valid)>40:
                qc_excluded[i,j]=True
    rain[qc_excluded]=np.nan
    rain_regions={};coverage={}
    for group in GROUPS:
        region=transform(project,unary_union([shape(f['geometry']) for f in basins['features'] if basin_group(f['properties']['COBACIA'])==group]))
        inside=np.array([region.covers(Point(x,y)) for x,y in gridxy])
        w=np.bincount(nearest[inside],minlength=len(public)).astype(float);w=w/w.sum()
        vals=rain;valid=np.isfinite(vals);den=np.sum(valid*w,axis=1)
        coverage[group]=den
        rain_regions[group]=np.where(den>=.6,np.nansum(vals*w,axis=1)/np.maximum(den,1e-10),np.nan)
    basin_den=np.sum(np.isfinite(rain)*weights,axis=1)
    basin_mean=np.nansum(rain*weights,axis=1)/np.maximum(basin_den,1e-10)
    save_csv('chuva-horaria-ponderada.csv',[{'horario':iso(t),'media_espacial_aprox_mm_h':round(float(basin_mean[i]),3) if basin_den[i]>=.6 else '', 'peso_com_dados':round(float(basin_den[i]),3),**{g:round(float(rain_regions[g][i]),3) if np.isfinite(rain_regions[g][i]) else '' for g in GROUPS}} for i,t in enumerate(grid)])
    # Audit all 100 catalogued in-basin gauges, including private sources and missing observations.
    inventory=[]
    for s in stations:
        ts,v=station_data[s['id']];valid=np.where(ts>=datetime(2026,9,21,tzinfo=TZ).timestamp())[0]
        issue=[];total=None;observed=None
        if len(valid):
            idx=valid[-1];observed=ts[idx];total=v['cum'][idx]
            if not np.isfinite(total):issue.append('acumulado ausente ou negativo');total=None
            dc=v['cum'][valid];diff=np.diff(dc)
            if np.any(diff<-.11):issue.append('reinicio ou queda do acumulado diario')
            if (datetime.now(TZ).timestamp()-observed)>5400:issue.append('leitura atrasada >90 min')
        else:issue.append('sem historico de hoje')
        if s in public:
            j=public.index(s)
            if qc_excluded[-1,j]:issue.append('possivel sensor travado: divergencia dos vizinhos')
        inv={k:s[k] for k in ['id','network','name','lat','lon','ottobacia','subbacia']}
        inv.update({'observado_em':iso(observed) if observed is not None else '', 'acumulado_hoje_mm':round(float(total),1) if total is not None else '',
                    'qualidade':'; '.join(issue) or 'checagens basicas aprovadas; nao homologado',
                    'usada_chuva_modelo':s['network'] in PUBLIC,
                    'proxima_limite_1km':transform(project,Point(s['lon'],s['lat'])).distance(pp.boundary)<1000,
                    'fonte':f'https://sigmameteorologia.com/produtos/stations/2026-09-21/{s["id"]}.txt'})
        inventory.append(inv)
    save_csv('inventario-pluviometros.csv',inventory)
    # Build all features causally. Stage is station-specific, never merged between gauges.
    names=[];columns=[]
    def add(name,v):names.append(name);columns.append(v)
    for code,L in levels.items():
        add(code+':nivel',L)
        for lag in [1,2,3,6]:
            v=np.full(len(L),np.nan);v[lag:]=(L[lag:]-L[:-lag])/lag;add(f'{code}:taxa{lag}h',v)
    hydro_count=len(columns)
    for group in GROUPS:
        for lag in [1,3,6]:add(f'{group}:chuva{lag}h',moving_sum(rain_regions[group],lag))
    X=np.column_stack(columns);y=levels['86510000'];origins=grid
    # Train to Aug 25, tune on Aug 26-Sep 7, final independent test Sep 8 onwards.
    train_end=datetime(2026,8,26,tzinfo=TZ).timestamp();val_end=datetime(2026,9,8,tzinfo=TZ).timestamp()
    # Select features with >=85% training availability; missing rain is imputed with TRAIN median + indicator.
    available=np.mean(np.isfinite(X[origins<train_end]),axis=0)>=.85
    available[:hydro_count]=True
    configurations={'local':list(range(5)),'montante':list(range(hydro_count)),
                    'montante_chuva':[i for i in range(X.shape[1]) if available[i]]}
    print('features rain included',[names[i] for i in configurations['montante_chuva'] if i>=hydro_count],flush=True)
    evaluations=[];predictions=[];details={};testrows=[]
    def fit_predict(xx,yy,tr,apply,alpha):
        med=np.array([np.nanmedian(xx[tr,j]) if np.isfinite(xx[tr,j]).any() else 0 for j in range(xx.shape[1])])
        def filled(a):return np.column_stack([np.where(np.isfinite(a),a,med),~np.isfinite(a)])
        a=filled(xx[tr]);mean=a.mean(axis=0);scale=a.std(axis=0);scale[scale<1e-12]=1
        a=(a-mean)/scale;target_mean=yy[tr].mean();b=yy[tr]-target_mean
        gram=np.einsum('ni,nj->ij',a,a,optimize=False)
        rhs=np.einsum('ni,n->i',a,b,optimize=False)
        beta=solve(gram+alpha*np.eye(a.shape[1]),rhs,assume_a='pos',check_finite=True)
        v=(filled(xx[apply])-mean)/scale
        pred=np.einsum('ni,i->n',v,beta,optimize=False)+target_mean
        assert np.all(np.isfinite(pred))
        return pred,(beta,mean,scale,med)
    for h in range(1,7):
        target=np.r_[y[h:],np.full(h,np.nan)];delta=target-y
        complete=np.all(np.isfinite(X[:,:hydro_count]),axis=1)&np.isfinite(delta)
        tr=np.where(complete&(origins+h*HOUR<train_end))[0]
        val=np.where(complete&(origins>=train_end)&(origins+h*HOUR<val_end))[0]
        test=np.where(complete&(origins>=val_end))[0]
        if min(len(tr),len(val),len(test))<24:raise ValueError('Insufficient temporal split')
        rising=X[:,1]>=.2
        # Explicit baseline comparison on identical eligible origins.
        candidates={}
        for conf,ix in configurations.items():
            xx=X[:,ix];opts=[]
            for alpha in [1.,10.,100.]:
                pv,_=fit_predict(xx,delta,tr,val,alpha)
                mask=rising[val]
                score=np.mean(abs(pv-delta[val]))+.5*np.mean(abs(pv[mask]-delta[val][mask])) if mask.any() else np.mean(abs(pv-delta[val]))
                opts.append((score,alpha))
            score,alpha=min(opts);combined=np.r_[tr,val]
            pt,params=fit_predict(xx,delta,combined,test,alpha)
            current_index=np.where(np.all(np.isfinite(X[:,:hydro_count]),axis=1)&np.isfinite(y))[0][-1]
            pc,_=fit_predict(xx,delta,combined,np.array([current_index]),alpha)
            err=pt-delta[test]; rising_err=err[rising[test]]
            evaluation={'horizonte_h':h,'metodo':conf,'alpha':alpha,'n_treino':len(tr),'n_validacao':len(val),'n_teste':len(test),
                'mae_teste_m':float(np.mean(abs(err))),'mae_subidas_m':float(np.mean(abs(rising_err))) if len(rising_err) else None,
                'n_subidas_teste':len(rising_err),'max_erro_teste_m':float(max(abs(err))),
                'previsao_experimental_m':float(y[current_index]+pc[0]),'origem':iso(origins[current_index]),
                'score_validacao':float(score)}
            evaluations.append(evaluation);candidates[conf]=(score,evaluation,pt)
            for k,j in enumerate(test):testrows.append({'origem':iso(origins[j]),'alvo':iso(origins[j]+h*HOUR),'metodo':conf,'horizonte_h':h,'observado_m':float(target[j]),'previsto_m':float(y[j]+pt[k]),'subida':bool(rising[j])})
        for method,pd in [('persistencia',np.zeros(len(test))),('tendencia_2h',X[test,2]*h)]:
            err=pd-delta[test];mask=rising[test]
            evaluations.append({'horizonte_h':h,'metodo':method,'alpha':None,'n_treino':0,'n_validacao':0,'n_teste':len(test),
             'mae_teste_m':float(np.mean(abs(err))),'mae_subidas_m':float(np.mean(abs(err[mask]))) if mask.any() else None,
             'n_subidas_teste':int(mask.sum()),'max_erro_teste_m':float(max(abs(err))),
             'previsao_experimental_m':float(y[current_index]+(X[current_index,2]*h if method=='tendencia_2h' else 0)),
             'origem':iso(origins[current_index]),'score_validacao':None})
        best=min(candidates,key=lambda k:candidates[k][0]);e=candidates[best][1]
        predictions.append({'horizonte_h':h,'origem':e['origem'],'horario':iso(origins[current_index]+h*HOUR),'metodo':best,'nivel_experimental_m':e['previsao_experimental_m'],
          'erro_medio_subidas_teste_m':e['mae_subidas_m'],'maior_erro_teste_m':e['max_erro_teste_m']})
        print('horizon',h,'selected',best,'forecast',round(e['previsao_experimental_m'],2),'test rising MAE',e['mae_subidas_m'],flush=True)
    save_csv('avaliacao-modelos.csv',evaluations);save_csv('previsoes-experimentais.csv',predictions);save_csv('predicoes-teste.csv',testrows)
    # Out-of-distribution and freshness audit. No probabilistic claims from these residuals.
    trainperiod=origins<val_end;ood=[]
    for i,n in enumerate(names):
        v=X[current_index,i];past=X[trainperiod,i];past=past[np.isfinite(past)]
        if np.isfinite(v) and len(past) and (v<np.min(past) or v>np.max(past)):
            ood.append({'feature':n,'current':float(v),'training_min':float(np.min(past)),'training_max':float(np.max(past))})
    current={code:{'timestamp':iso(max(d)),'level_m':float(d[max(d)])} for code,d in hydro.items()}
    # Empirical lag correlations in first differences, diagnostic ONLY, no fixed physical delay inferred.
    lagstats=[]
    for code in ['86472000','86472600','86500000']:
        a=np.diff(levels[code]);b=np.diff(y)
        for lag in range(0,19):
            aa=a[:len(a)-lag] if lag else a;bb=b[lag:];valid=np.isfinite(aa)&np.isfinite(bb)
            lagstats.append({'station':code,'lag_h':lag,'correlation_differences':float(np.corrcoef(aa[valid],bb[valid])[0,1]),'n':int(valid.sum())})
    save_csv('defasagens-diagnosticas.csv',lagstats)
    meta={'generated_at':datetime.now(TZ).isoformat(),'current':current,'model_origin':iso(origins[current_index]),'rain_origin':iso(grid[-1]),'forecast':predictions,
        'evaluations':evaluations,'out_of_training_range':ood,'features':names,'rain_features_used':[names[i] for i in configurations['montante_chuva'] if i>=hydro_count],
        'station_count':len(stations),'public_rain_gauges':len(public),'subbasin_counts':dict(collections.Counter(s['subbacia'] for s in stations)),
        'basin_area_km2':16047.2535,'local_outlet_area_km2':12.828,'rain_spatial_coverage_within_25km':float(np.mean(nearest_dist<25000)),
        'rain_weight_with_data_latest':float(basin_den[-1]),'rain_basin_latest_mm_h':float(basin_mean[-1]),
        'rain_region_latest':{g:float(rain_regions[g][-1]) if np.isfinite(rain_regions[g][-1]) else None for g in GROUPS},
        'sigma_sace_overlap_count':len(agreement),'sigma_sace_max_difference_m':max(a['difference_m'] for a in agreement),
        'independent_test_start':iso(val_end),'training_start':iso(start),'max_observed_level_m':float(np.nanmax(y)),
        'public_release_gate':'NOT_VALIDATED_FOR_PUBLIC_NUMERICAL_FORECAST',
        'release_reasons':['Production D1 also has only about 45 hours of reservoir history; no validated current flow-stage routing model.',
            'Only two months of events; no independent test at flood threshold, no validated probabilistic coverage.',
            'Rainfall metadata inferred and checked internally; mixed networks remain provisional.',
            'River delivery latency and future rainfall are not covered by a calibrated operational forecast.']}
    (OUT/'analise.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,allow_nan=False))
    np.savez_compressed(OUT/'series-modelo.npz',times=grid,features=X,level=y,rain=rain,weights=weights)
    print('Done',json.dumps({k:meta[k] for k in ['current','station_count','rain_weight_with_data_latest','out_of_training_range']},ensure_ascii=False),flush=True)
if __name__=='__main__':run()
