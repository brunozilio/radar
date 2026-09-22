"""Independent telemetry checks, event travel times and station participation audit."""
import json,csv,math
from datetime import datetime
import numpy as np
from scipy.signal import find_peaks
from hydro_routing_data import OUT,RAW,OLD,iso,epoch,TZ,savecsv
from hydro_model import asof
def run():
    z=dict(np.load(OUT/'telemetria.npz'));times=z['times'];hour=np.arange(0,len(times),4);t=times[hour];H=z['86510000:H'][hour]
    peaks,_=find_peaks(np.where(np.isfinite(H),H,-999),prominence=1.5,distance=36)
    distances={r['id']:float(r['distancia_rede_km']) for r in csv.DictReader((OUT/'estacoes-conectividade.csv').open())}
    stage={'Linha José Júlio':('86472000',z['86472000:H'][hour],12),'Santa Tereza':('86472600',z['86472600:H'][hour],12),'14 de Julho':('86471000',z['julho:Q'][hour],18),'Passo Carreiro':('86500000',z['86500000:H'][hour],30)}
    dcrs=[]
    for station in json.loads((RAW/'dcrs-inbasin.json').read_text()):
        code=station['codigo'];doc=json.loads((RAW/f'dcrs-history-{code}.json').read_text());items=(doc.get('data') or {}).get('historic',{}).get('items',[])
        valid=[r for r in items if isinstance(r.get('rio_nivel'),(int,float)) and 0<float(r['rio_nivel'])<2000]
        good=station['data']['rio']['homologacao']['relacao']['valido']['value']
        dcrs.append({'id':code,'name':station['name']['general'],'historical_rows':len(items),'valid_level_rows':len(valid),'latest_report':station['timestamp'],'latest_level_own_datum':station['data']['rio']['rio_nivel']['value'],'latest_homologation':good,'role':'check only; distinct vertical datum; no automatic conversion to SGB gauge'})
        if code=='DCRS-00057' and valid:
            tt=np.array([datetime.fromisoformat(r['ts'].replace('Z','+00:00')).timestamp() for r in valid]);vv=[r['rio_nivel'] for r in valid];order=np.argsort(tt)
            stage['Carreiro — Cotiporã/Dois Lajeados']=(code,asof(tt[order],np.array(vv)[order],t,max_age=5400),24)
    savecsv(OUT/'defesa-civil-conferencia.csv',dcrs)
    waves=[]
    for name,(code,x,maxlag) in stage.items():
        for p in peaks:
            if H[p]<7 or t[p]>=epoch('2026-09-21T00:00:00'):continue
            start=max(0,p-18);end=min(len(H),p+19);down=H[start:end]
            options=[]
            for lag in range(maxlag+1):
                if start-lag<0:continue
                up=x[start-lag:end-lag];mask=np.isfinite(up)&np.isfinite(down)
                if mask.sum()<30 or np.std(up[mask])<.1:continue
                corr=float(np.corrcoef(up[mask],down[mask])[0,1]);options.append((corr,lag))
            if not options:continue
            corr,lag=max(options)
            if corr<.8:continue
            near=[l for c,l in options if c>=corr-.02]
            waves.append({'source':name,'id':code,'event_peak':iso(t[p]),'mucum_peak_m':float(H[p]),'best_lag_h':lag,'similar_lag_min_h':min(near),'similar_lag_max_h':max(near),'correlation':corr,'river_distance_km':distances.get(code),'apparent_wave_speed_km_h':distances.get(code)/lag if distances.get(code) and lag>0 else None})
    savecsv(OUT/'ondas-calibradas.csv',waves)
    summary=[]
    for name,(code,x,_) in stage.items():
        rows=[r for r in waves if r['source']==name and r['best_lag_h']>0];lags=[r['best_lag_h'] for r in rows]
        summary.append({'source':name,'id':code,'events':len(rows),'median_h':float(np.median(lags)) if lags else None,'p10_h':float(np.quantile(lags,.1)) if lags else None,'p90_h':float(np.quantile(lags,.9)) if lags else None,'distance_km':distances.get(code),'identification':'weak: tributary mixture' if 'Carreiro' in name else 'empirical alignment of whole wave; not parcel travel time'})
    (OUT/'propagacao-resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    # Every catalogued gauge receives a clear role; no invented travel time for rainfall on hillslopes.
    weights=json.loads((OUT/'chuva-pesos.json').read_text());ana={r['id'] for r in json.loads((OLD/'producao-estacoes.json').read_text()) if r['inside']};inventory=list(csv.DictReader((OUT/'estacoes-conectividade.csv').open()))
    for row in inventory:
        code=row['id'];row['papel_modelo']='serie longa ANA: chuva e/ou telemetria' if code in ana else 'conferencia espacial SIGMA; nao parametro independente do modelo'
        row['pesos_chuva_por_subbacia']='; '.join(f'{w["group"]}: {w["weights"].get(code,0):.4f}' for w in weights if w['weights'].get(code,0)>0)
        row['tempo_chuva_ate_mucum']='Nao atribuido por sensor: inclui infiltracao e encosta, alem de propagacao no canal.'
    savecsv(OUT/'pluviometros-estrutura-completa.csv',inventory)
    print('Supporting checks:',len(dcrs),'DCRS stations,',len(waves),'matched waves,',len(inventory),'catalogue IDs',flush=True)
if __name__=='__main__':run()
