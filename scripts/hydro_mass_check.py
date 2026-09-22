"""Independent discharge-routing diagnostic; does not invent future releases."""
import json,csv,sys
import numpy as np
from scipy.optimize import minimize,least_squares
from scipy.spatial import cKDTree
from shapely.geometry import shape,Point
from shapely.ops import unary_union,transform
from pyproj import Transformer
from hydro_precision_audit import OUT,PREV,observed_rain_windows
from hydro_latency_forecast import merged
from hydro_routing_data import OLD,epoch,iso,savecsv
from hydro_routing_fit import shift,metric

def prepare_data():
    z=dict(np.load(OUT/'telemetria-latencia.npz'));tt=z['times'];ix=np.arange(0,len(tt),4);t=tt[ix];q=z['raw:86510000:Q'][ix]/1000;h=z['raw:86510000:H'][ix];j=z['raw:julho:Q'][ix]/1000;c=z['raw:86500000:Q'][ix]/1000
    graph=json.loads((PREV/'grafo-drenagem.json').read_text())['links'];children={}
    for r in graph:children.setdefault(r['downstream'],[]).append(r['id'])
    def upstream(k):
        result={k}
        for a in children.get(k,[]):result.update(upstream(a))
        return result
    inv=list(csv.DictReader((PREV/'estacoes-conectividade.csv').open()));reach={r['id']:int(r['trecho']) for r in inv};excluded=upstream(reach['86471000'])|upstream(reach['86500000']);ids={r['id'] for r in graph}-excluded
    features=json.loads((OLD/'raw/upstream-basins.geojson').read_text())['features'];project=Transformer.from_crs(4326,31982,always_xy=True).transform
    region=transform(project,unary_union([shape(f['geometry']) for f in features if f['properties']['COTRECHO'] in ids]));area=region.area/1e6
    stations=[r for r in json.loads((OLD/'producao-estacoes.json').read_text()) if r['inside']];coords=[project(r['lon'],r['lat']) for r in stations];xx,yy=np.meshgrid(np.arange(region.bounds[0]+500,region.bounds[2],1000),np.arange(region.bounds[1]+500,region.bounds[3],1000));points=np.array([(x,y) for x,y in zip(xx.ravel(),yy.ravel()) if region.covers(Point(x,y))]);nearest=cKDTree(coords).query(points)[1];weights=np.bincount(nearest,minlength=len(stations))/len(points)
    amount=np.zeros(len(t));coverage=np.zeros(len(t))
    for station,weight in zip(stations,weights):
        if weight==0:continue
        d=merged(station['id']);v,cv=observed_rain_windows(d['times'],d['rain'],t,[1])[1];amount+=weight*v;coverage+=weight*cv
    rain=np.where(coverage>=.75,amount/np.maximum(coverage,1e-9),np.nan)*area/3600 # 1000 m3/s, if all rainfall became direct runoff.
    jl=list(range(1,13));cl=list(range(4,25));rl=list(range(0,25));X=np.column_stack([*[shift(j,k) for k in jl],*[shift(c,k) for k in cl],*[shift(rain,k) for k in rl],np.ones(len(t))]);nj=len(jl);nc=len(cl);nr=len(rl);p=X.shape[1]
    np.savez_compressed(OUT/'dados-roteamento.npz',times=t,q=q,h=h,julho=j,carreiro=c,rain=rain,amount=amount,coverage=coverage,X=X,area=area)
    return t,q,h,X,area,jl,cl,rl

def run():
    t,q,h,X,area,jl,cl,rl=prepare_data()
    nj=len(jl);nc=len(cl);nr=len(rl);p=X.shape[1]
    if '--prepare-only' in sys.argv:
        return
    valid=np.isfinite(X).all(axis=1)&np.isfinite(q)&np.isfinite(h);train=np.where(valid&(t<epoch('2026-07-01T00:00:00')))[0];test=np.where(valid&(t>=epoch('2026-07-01T00:00:00'))&(t<epoch('2026-09-21T00:00:00')))[0]
    sample=1+2*(q[train]>=2);a=X[train];target=q[train];gram=np.einsum('ni,n,nj->ij',a,sample,a)/len(train);rhs=np.einsum('ni,n,n->i',a,sample,target)/len(train)
    penalty=np.zeros((p,p))
    for start,n in [(0,nj),(nj,nc),(nj+nc,nr)]:
        for k in range(start,start+n-1):v=np.zeros(p);v[k]=1;v[k+1]=-1;penalty+=np.outer(v,v)
    gram+=.005*penalty
    def objective(v):return .5*np.einsum('i,ij,j',v,gram,v)-np.dot(rhs,v)
    def gradient(v):return np.einsum('ij,j->i',gram,v)-rhs
    x=np.zeros(p);x[jl.index(4)]=1;x[nj+cl.index(9)]=1;x[nj+nc+3]=.2
    constraints=[{'type':'eq','fun':lambda v:v[:nj].sum()-1},{'type':'eq','fun':lambda v:v[nj:nj+nc].sum()-1},{'type':'ineq','fun':lambda v:1-v[nj+nc:nj+nc+nr].sum()}]
    result=minimize(objective,x,jac=gradient,method='SLSQP',bounds=[(0,None)]*p,constraints=constraints,options={'maxiter':600,'ftol':1e-10});v=result.x
    rating=least_squares(lambda p:p[0]*q[train]**p[1]+p[2]-h[train],[4.5,.64,.4],bounds=([.01,.1,-10],[20,1.2,10]),loss='soft_l1').x
    predq=np.einsum('ni,i->n',X[test],v);predh=rating[0]*np.maximum(predq,0)**rating[1]+rating[2];m=metric(predh,h[test]);kernels=[]
    for name,lags,w in [('14 de Julho',jl,v[:nj]),('Passo Carreiro',cl,v[nj:nj+nc]),('chuva incremental',rl,v[nj+nc:nj+nc+nr])]:
        for lag,weight in zip(lags,w):kernels.append({'source':name,'lag_h':lag,'weight':float(weight)})
    savecsv(OUT/'roteamento-vazao-pesos.csv',kernels)
    summary={'success':bool(result.success),'message':str(result.message),'incremental_area_km2':area,'train_n':len(train),'test_n':len(test),'test_level_reconstruction':m,'rainfall_runoff_fraction':float(v[nj+nc:nj+nc+nr].sum()),'baseflow_1000m3s':float(v[-1]),'mean_delay_julho_h':float(np.dot(jl,v[:nj])),'mean_delay_carreiro_h':float(np.dot(cl,v[nj:nj+nc])),'rating_parameters':rating.tolist(),'use':'Diagnostic reconstruction from observed forcings; not a prospective forecast. Future discharges and rainfall are not filled with invented values.'}
    (OUT/'conferencia-balanco.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':run()
