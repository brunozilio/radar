"""Observed rainfall versus Muçum response timing, not parcel travel times."""
import json,csv,xml.etree.ElementTree as ET
from datetime import datetime
import numpy as np
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from hydro_precision_audit import OUT,PREV,observed_rain_windows
from hydro_latency_forecast import merged
from hydro_routing_data import epoch,iso,number,TZ,savecsv
from hydro_model import asof
from hydro_routing_fit import shift,avg

def run():
    t=np.arange(epoch('2025-04-01T00:00:00'),epoch('2026-09-21T15:00:00')+1,3600)
    weights=json.loads((PREV/'chuva-pesos.json').read_text());codes={c for g in weights for c in g['weights']};data={c:merged(c) for c in codes};rain={};coverage={}
    windows={c:observed_rain_windows(d['times'],d['rain'],t,[1])[1] for c,d in data.items()}
    for g in weights:
        cov=sum(w*windows[c][1] for c,w in g['weights'].items());amount=sum(w*windows[c][0] for c,w in g['weights'].items());rain[g['group']]=np.where(cov>=.85,amount/np.maximum(cov,1e-9),np.nan);coverage[g['group']]=cov
    gua={}
    for file in sorted((OUT/'raw').glob('guapore-*.xml')):
        for _,el in ET.iterparse(file,events=['end']):
            if not el.tag.endswith('DadosHidrometereologicos'):continue
            r={x.tag.split('}')[-1]:x.text for x in el};gua[epoch(r['DataHora'])]=number(r.get('ChuvaFinal')) if r.get('CQ_ChuvaFinal') in [None,'Dado aprovado'] else np.nan;el.clear()
    if gua:
        gt=np.array(sorted(gua));gv=np.array([gua[x] for x in gt]);a,cov=observed_rain_windows(gt,gv,t,[1])[1];rain['Guaporé: Linha Colombo']=np.where(cov>=.85,a/np.maximum(cov,1e-9),np.nan);coverage['Guaporé: Linha Colombo']=cov
    muc=data['86510000'];H=asof(muc['times'],muc['level'],t,max_age=0);rise=(H-shift(H,3))/3;today=epoch('2026-09-21T00:00:00');historical=t<today
    filled=np.interp(np.arange(len(H)),np.where(np.isfinite(H))[0],H[np.isfinite(H)]);peaks,_=find_peaks(filled,prominence=1.5,distance=96)
    peaks=[p for p in peaks if p>=96 and p+24<len(H) and t[p+24]<today and H[p]>=7 and np.isfinite(H[p-48:p+25]).mean()>=.85]
    correlations=[];events=[];summary=[]
    for group,P in rain.items():
        P3=avg(P,3)*3
        for period,periodmask in [('historico',historical),('abril_set2025',t<epoch('2025-10-01')),('out2025_set2026',(t>=epoch('2025-10-01'))&historical)]:
            for lag in range(49):
                x=shift(P3,lag);mask=periodmask&np.isfinite(x)&np.isfinite(rise);r=float(np.corrcoef(x[mask],rise[mask])[0,1]) if mask.sum()>200 else np.nan
                correlations.append({'regiao':group,'periodo':period,'atraso_h':lag,'correlacao':r,'n_horas':int(mask.sum())})
        for p in peaks:
            target=np.arange(p-24,p+13);options=[]
            for lag in range(49):
                x=P3[target-lag];y=rise[target];valid=np.isfinite(x)&np.isfinite(y)
                if valid.sum()<28 or np.nanmax(x)<10 or np.nanstd(x[valid])<.1 or np.nanstd(y[valid])<.01:continue
                options.append((float(np.corrcoef(x[valid],y[valid])[0,1]),lag,int(valid.sum())))
            if not options:continue
            r,lag,n=max(options);near=[k for rr,k,nn in options if rr>=r-.05]
            events.append({'regiao':group,'pico_mucum':iso(t[p]),'nivel_pico_m':float(H[p]),'melhor_atraso_h':lag,'correlacao':r,'atraso_semelhante_min_h':min(near),'atraso_semelhante_max_h':max(near),'n_horas':n,'associacao_util':r>=.35,'limite_busca':lag in [0,48]})
        ev=[r for r in events if r['regiao']==group and r['associacao_util']];lags=[r['melhor_atraso_h'] for r in ev];globalrows=[r for r in correlations if r['regiao']==group and r['periodo']=='historico'];best=max(globalrows,key=lambda r:r['correlacao'])
        current=(t>today)&(t<=t[-1]);known=np.isfinite(P[current]);summary.append({'regiao':group,'melhor_atraso_historico_h':best['atraso_h'],'correlacao_historica':best['correlacao'],'eventos_com_associacao':len(ev),'eventos_avaliados':sum(r['regiao']==group for r in events),'mediana_eventos_h':float(np.median(lags)) if lags else None,'p10_eventos_h':float(np.quantile(lags,.1)) if lags else None,'p90_eventos_h':float(np.quantile(lags,.9)) if lags else None,'chuva_hoje_horas_cobertas_mm':float(np.nansum(P[current])),'horas_cobertas_hoje':int(known.sum()),'interpretacao':'Associação temporal chuva em 3h versus taxa de subida em 3h; não identifica percurso da água ou causalidade regional.'})
    savecsv(OUT/'atrasos-chuva-resposta.csv',summary);savecsv(OUT/'correlacoes-por-atraso.csv',correlations);savecsv(OUT/'atrasos-por-evento.csv',events)
    names=list(rain);np.savez_compressed(OUT/'chuva-e-nivel.npz',times=t,level=H,**{g:rain[g] for g in names})
    current=(t>=epoch('2026-09-21T00:00:00'))&(t<=t[-1]);series=[]
    for i in np.where(current)[0]:series.append({'hora_brt':iso(t[i]),'nivel_mucum_m':float(H[i]) if np.isfinite(H[i]) else None,**{g:float(rain[g][i]) if np.isfinite(rain[g][i]) else None for g in names}})
    savecsv(OUT/'chuva-hoje-hora-a-hora.csv',series)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False})
    fig,axes=plt.subplots(len(names),1,figsize=(13.5,13),sharex=True);fig.subplots_adjust(left=.085,right=.90,top=.88,bottom=.11,hspace=.30)
    fig.text(.085,.965,'Chuva medida e resposta do rio em Muçum',fontsize=23,weight='bold',color='#16334a');fig.text(.085,.929,'21/09/2026 • Horário de Brasília • Barras: chuva da hora anterior | Linha: nível observado em Muçum',fontsize=11)
    current=(t>=epoch('2026-09-21T02:00:00'))&(t<=t[-1]);times=[datetime.fromtimestamp(x,TZ) for x in t[current]]
    for ax,g in zip(axes,names):
        P=rain[g][current];ax.bar(times,P,width=.030,color='#3786bf',alpha=.8);ax.set_ylabel('mm em 1h',color='#22689b');ax.set_ylim(0,max(5,float(np.nanmax(P))*1.3));ax.grid(axis='y',alpha=.13)
        ax.text(.008,.85,g+(' (um pluviômetro)' if g.startswith('Guaporé') else ' (média espacial estimada)'),transform=ax.transAxes,weight='bold',fontsize=10)
        right=ax.twinx();right.plot(times,H[current],color='#b44b20',lw=2.2);right.set_ylim(3,11);right.set_ylabel('Muçum (m)',color='#b44b20');right.spines['top'].set_visible(False)
        missing=~np.isfinite(P)
        for x in np.array(times)[missing]:ax.axvspan(x,datetime.fromtimestamp(x.timestamp()+1800,TZ),color='#777777',alpha=.12)
    axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=1,tz=TZ));axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Hh',tz=TZ))
    fig.text(.085,.066,'Cinza: chuva sem cobertura suficiente. A linha de Muçum é a mesma nos seis painéis; as contribuições não foram isoladas.',fontsize=10)
    fig.text(.085,.038,'O pico do rio de hoje ainda não foi observado. Guaporé: comparação temporal, sem quantificação do remanso.',fontsize=10,weight='bold',color='#8b4e1b')
    fig.savefig(OUT/'chuva-versus-mucum-hoje.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(13.5,6.7));fig.subplots_adjust(left=.19,right=.96,top=.78,bottom=.22)
    matrix=np.array([[next(r['correlacao'] for r in correlations if r['regiao']==g and r['periodo']=='historico' and r['atraso_h']==k) for k in range(49)] for g in names]);im=ax.imshow(matrix,aspect='auto',origin='upper',cmap='YlGnBu',vmin=0,vmax=max(.5,float(np.nanmax(matrix))))
    ax.set_yticks(range(len(names)),names);ax.set_xticks(range(0,49,3));ax.set_xlabel('Chuva antecedendo a resposta do nível em Muçum (horas)')
    for i,s in enumerate(summary):ax.scatter(s['melhor_atraso_historico_h'],i,s=75,facecolor='none',edgecolor='#e77721',linewidth=2)
    fig.colorbar(im,ax=ax,label='Correlação com a taxa de subida',fraction=.025,pad=.02)
    fig.text(.085,.93,'Em quantas horas a chuva se associa à subida?',fontsize=22,weight='bold');fig.text(.085,.865,'Abril/2025–20/09/2026 • Círculo: maior correlação • Chuva acumulada e taxa de subida em janelas de 3h',fontsize=11)
    fig.text(.085,.10,'Associação estatística, não tempo físico de chegada. Chuva simultânea em regiões diferentes confunde a atribuição.',fontsize=10,weight='bold',color='#8b4e1b');fig.text(.085,.055,'Guaporé representa apenas o pluviômetro de Linha Colombo; esta análise não mede seu efeito de remanso.',fontsize=10)
    fig.savefig(OUT/'atrasos-chuva-mucum.png',dpi=160);plt.close(fig)
    print(json.dumps({'peaks':len(peaks),'summary':summary},indent=2,ensure_ascii=False))

if __name__=='__main__':run()
