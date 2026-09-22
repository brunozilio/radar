"""One selected forecast curve, preserving evidence and limitations separately."""
import csv,json
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from hydro_precision_audit import OUT,HORIZON
from hydro_routing_data import TZ,savecsv

def read(name):return list(csv.DictReader((OUT/name).open()))
def fmt(x,n=1):return f'{float(x):.{n}f}'.replace('.',',')
def run():
    meta=json.loads((OUT/'previsao-atualizada.json').read_text());rows=read('previsao-atualizada.csv');allrows=read('candidatos-latencia.csv');routing=read('roteamento-previsao.csv');obs=meta['last_observed_mucum']
    assert len(rows)==HORIZON==12 and len({r['model'] for r in rows})==1
    family=rows[0]['model'];scores=meta['family_validation_scores'];assert family==min(scores,key=scores.get)
    dates=[datetime.fromisoformat(r['time']) for r in rows];values=np.array([float(r['forecast_m']) for r in rows]);origin=datetime.fromisoformat(meta['origin']);stamp=datetime.now(TZ)
    assert np.isfinite(values).all() and all((d-origin).total_seconds()==3600*(i+1) for i,d in enumerate(dates))
    records=[{'horario_brasilia':r['time'],'nivel_estimado_m':round(float(r['forecast_m']),3),'antecedencia_h':int(float(r['lead_h'])),'modelo':family,'status':'Estimativa central independente; alta precisão não demonstrada'} for r in rows];savecsv(OUT/'previsao-unica.csv',records)
    futuretimes=[datetime.fromisoformat(obs['last_time'])]+dates;futurelevels=[obs['value']]+values.tolist()
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(13.5,7.8));fig.subplots_adjust(left=.075,right=.965,top=.77,bottom=.25)
    fig.text(.075,.94,'Muçum | estimativa central para 12 horas',fontsize=23,weight='bold',color='#122e45')
    fig.text(.075,.893,f"Referência: {origin.strftime('%d/%m/%Y, %Hh')}  •  Até {dates[-1].strftime('%d/%m, %Hh')}  •  Horário de Brasília",fontsize=12)
    fig.text(.075,.847,f"Último nível observado: {fmt(obs['value'],2)} m às {datetime.fromisoformat(obs['last_time']).strftime('%Hh%M')}  |  Emissão: {stamp.strftime('%Hh%M')}",color='#405768')
    # Only the central forecast is drawn as a line; the last observation is a separate point.
    ax.plot(dates,values,color='#1769b2',lw=3,marker='o',ms=5,label='Estimativa central')
    ax.scatter([futuretimes[0]],[obs['value']],color='#142e45',s=50,zorder=5,label='Última observação')
    for d,v in zip(dates,values):ax.annotate(fmt(v),(d,v),xytext=(0,10),textcoords='offset points',ha='center',fontsize=10,weight='bold',color='#145787')
    ax.annotate(fmt(obs['value'],2),(futuretimes[0],obs['value']),xytext=(0,12),textcoords='offset points',ha='center',fontsize=10)
    ax.set_ylim(min(obs['value'],values.min())-.8,values.max()+1.3);ax.set_ylabel('Nível na régua de Muçum (m)');ax.grid(axis='y',alpha=.16)
    ax.set_xticks(dates);ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh\n%d/%m',tz=TZ));ax.tick_params(axis='x',labelsize=9);ax.legend(loc='upper left',frameon=False,fontsize=10)
    fig.text(.075,.155,'PREVISÃO NÃO OFICIAL • Alta precisão ainda não demonstrada nesta cheia.',fontsize=11,weight='bold',color='#8d460c')
    fig.text(.075,.113,'A curva não confirma o pico nem o horário de queda. Uma única linha não elimina a incerteza entre os métodos.',fontsize=10)
    fig.text(.075,.073,'Cálculo: telemetria ANA e três usinas CERAN; SIGMA usada para conferência. Referência vertical da régua ANA 86510000.',fontsize=9,color='#405768')
    fig.text(.075,.039,'Para decisões de proteção, acompanhe os alertas oficiais da Defesa Civil e do SGB.',fontsize=9,color='#405768')
    fig.savefig(OUT/'mucum-previsao-unica.png',dpi=180);plt.close(fig)
    last=rows[-1];spread=[float(r['forecast_m']) for r in allrows if int(float(r['lead_h']))==12]+[float(routing[-1]['forecast_m'])]
    table='\n'.join(f"| {d.strftime('%d/%m %Hh')} | {fmt(v)} m |" for d,v in zip(dates,values))
    text=f'''# Muçum — atualização com uma curva central

Emitido em {stamp.isoformat()}. Referência {origin.isoformat()}; último nível observado {obs['value']} m em {obs['last_time']}. Os dados brutos novos e horários de coleta estão em `raw/manifest.json`.

| Horário BRT | Estimativa central |
|---|---:|
{table}

A família **{family}** foi escolhida pelo menor escore médio na validação histórica dos 12 prazos: {json.dumps(scores,ensure_ascii=False)}. Não houve escolha pela preferência por um nível menor/maior, nem suavização manual para parecer mais confiável. Os coeficientes foram ajustados com alvos anteriores a hoje. A seleção e o desenvolvimento anteriores já observaram erros deste evento; retrospectivas de hoje não são validação prospectiva independente.

Foram atualizadas 27 séries ANA, três usinas CERAN e 100 séries individuais SIGMA. A SIGMA confirmou a última leitura de Muçum; as séries SIGMA não foram inseridas apenas no caso atual em um modelo calibrado com outra base. Suas diferenças e atrasos estão em `auditoria-sigma.csv`. O cálculo de chuva continua usando as 27 séries ANA e pesos de área; vazões/afluências das três usinas entram como preditores. Não se afirma que todas as estações SIGMA estejam assimiladas.

Para 12h, esta família apresentou MAE de {fmt(last['test_mae_m'],2)} m no teste histórico e {fmt(last['today_mae_m'],2)} m nas {int(float(last['today_n']))} retrospectivas disponíveis de hoje. O primeiro valor mistura condições de rio baixo e cheias; nenhum deles é uma margem garantida para a previsão atual. A onda atual ultrapassa condições do histórico. A representação com uma linha atende ao formato solicitado e não resolve a incerteza.

Os quatro métodos ainda resultam em {fmt(min(spread))} a {fmt(max(spread))} m no último horário, inclusive {fmt(routing[-1]['forecast_m'])} m na propagação por vazão. Essa amplitude não é um intervalo de confiança nem um limite de cheia. As alternativas foram preservadas em `candidatos-latencia.csv` e `roteamento-previsao.csv`, embora o gráfico mostre só a curva selecionada. Os resultados não confirmam pico ou queda.

Conferência: 12 horários consecutivos e valores finitos, uma família em toda a curva, seleção pelo escore histórico. O último observado é um ponto separado, sem inventar uma medição às 15h. Nenhuma mudança em produção ou mensagem externa.

Fontes: [ANA](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx), [SIGMA — Muçum](https://sigmameteorologia.com/produtos/stations/2026-09-21/86510000.txt), [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php), [Monte Claro](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHMC.php), [Castro Alves](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php). Arquivo histórico de reservatórios ONS e previsões meteorológicas GFS/ECMWF/ICON complementam o ajuste e as alternativas.
'''
    (OUT/'relatorio-atualizacao.md').write_text(text);(OUT/'verificacao-curva.json').write_text(json.dumps({'origin':meta['origin'],'last_observation':obs,'model':family,'horizons':12,'finite':True,'selected_by_historical_validation':True,'high_accuracy_demonstrated':False},indent=2,ensure_ascii=False));print(table);print('12h diagnostics',last,'routing',routing[-1])

if __name__=='__main__':run()
