"""Create auditable local figures; no publication and no operational forecast claim."""
from pathlib import Path
from datetime import datetime,timedelta
import json,csv,collections,textwrap
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Polygon as PatchPolygon
from hydro_model import TZ,read_station,basin_group
from hydro_production_assess import rows
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/mucum-bacia-2026-09-21';RAW=OUT/'raw'
def load(name):return json.loads((OUT/name).read_text())
def pt(v,d=2):return f'{v:.{d}f}'.replace('.',',')
def dt(t):return datetime.fromisoformat(t)
def style(ax):
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh',tz=TZ))
def run():
    a=load('analise.json');prod=load('producao-resumo.json');ps=load('producao-estacoes.json');inv=list(csv.DictReader((OUT/'inventario-pluviometros.csv').open()))
    now=datetime.now(TZ);stamp=now.strftime('%d/%m/%Y • %H:%M BRT');origin=dt(a['model_origin']);end=origin+timedelta(hours=6)
    # Prefer direct SACE/D1 observations to the SIGMA mirror at equal timestamps.
    ts,v=read_station('86510000');obs={datetime.fromtimestamp(t,TZ):float(h) for t,h in zip(ts,v['level']) if np.isfinite(h)}
    for r in rows('sace'):
        if r['station']=='86510000':obs[dt(r['timestamp'])]=r['level']
    for r in csv.DictReader((RAW/'sace-3.csv').open(),delimiter=';'):obs[dt(r['data_hora_medicao']).replace(tzinfo=TZ)]=float(r['indice'])/100
    last=max(obs);lv=obs[last];today=origin.replace(hour=0,minute=0,second=0)
    ot=sorted(t for t in obs if today<=t<=last);oh=[obs[t] for t in ot]
    dams=rows('ceran');july=sorted([r for r in dams if r['plant_id']=='julho' and dt(r['timestamp'])>=today],key=lambda r:dt(r['timestamp']))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.labelcolor':'#243746','text.color':'#142b3b','axes.titleweight':'bold','savefig.facecolor':'#f7f9fb'})
    # Public-facing status chart contains observations and an explicitly unknown future.
    fig=plt.figure(figsize=(11,11),facecolor='#f7f9fb');gs=fig.add_gridspec(2,1,left=.11,right=.94,top=.77,bottom=.23,hspace=.55,height_ratios=[1.3,1])
    fig.text(.08,.955,'MUÇUM • RIO TAQUARI',size=25,weight='bold');fig.text(.08,.92,'Situação observada — 21 de setembro de 2026',size=15)
    fig.text(.08,.858,f'{pt(lv)} m',size=36,weight='bold',color='#075a8a');fig.text(.36,.868,f'Última medição: {last:%H:%M} BRT\nRégua SGB 86510000',size=13)
    ax=fig.add_subplot(gs[0]);ax.plot(ot,oh,color='#087bb8',lw=3);ax.scatter([last],[lv],s=65,color='#087bb8',zorder=4)
    ax.axvspan(last,end,color='#e8edf2');ax.text(last+(end-last)/2,min(oh)+(max(oh)-min(oh))*.25,'PRÓXIMAS HORAS\nSem previsão numérica validada',ha='center',size=13,weight='bold',color='#4b5b6b')
    ax.set(ylabel='Nível na régua (m)',xlim=(today+timedelta(hours=5),end),title='O nível observado está subindo');style(ax)
    ax2=fig.add_subplot(gs[1]);ax2.plot([dt(r['timestamp']) for r in july],[r['outflow'] for r in july],color='#aa4b19',marker='o',lw=2)
    latest=july[-1];ax2.annotate(f'{pt(latest["outflow"],0)} m³/s às {dt(latest["timestamp"]):%Hh}',(dt(latest['timestamp']),latest['outflow']),xytext=(-16,-25),textcoords='offset points',ha='right',weight='bold',color='#aa4b19')
    ax2.set(ylabel='Vazão de saída (m³/s)',title='Usina 14 de Julho • vazão informada pela CERAN');style(ax2)
    fig.text(.08,.162,'A água a montante ainda pode alterar a evolução em Muçum.',size=14,weight='bold')
    fig.text(.08,.123,'Não use este gráfico para concluir que não haverá inundação.\nPara decisões de segurança, acompanhe a Defesa Civil e o SACE/SGB.',size=12)
    fig.text(.08,.067,f'Elaborado em {stamp} • Não é boletim oficial.\nFontes: SGB/SACE e CERAN, conferidas no D1 de radar.brunozilio.com.\nNível relativo à régua; não representa a profundidade nas ruas.',size=10,color='#536575')
    fig.savefig(OUT/'mucum-observado.png',dpi=170);plt.close(fig)
    # Experimental outputs, visibly separated from the public observational chart.
    fig,ax=plt.subplots(figsize=(12,7),facecolor='#f7f9fb');fig.subplots_adjust(left=.09,right=.94,top=.73,bottom=.28)
    fig.text(.075,.94,'SIMULAÇÃO REPROVADA PARA USO PÚBLICO',size=22,weight='bold',color='#a52a25')
    fig.text(.075,.886,'Muçum • saídas experimentais por hora • 21/09/2026',size=16)
    fig.text(.075,.84,'Erro de 3,35 m na previsão de 6h → 12h de hoje. Barragens sem calibração histórica.',size=12,color='#a52a25')
    ax.plot(ot,oh,label='Observado SGB/SACE',lw=3,color='#087bb8')
    originlevel=obs[max(t for t in obs if t<=origin)]
    colors={'montante':'#b54430','montante_chuva':'#bd7900','tendencia_2h':'#66758a'}
    labels={'montante':'Modelo com níveis a montante','montante_chuva':'Modelo + chuva disponível (Tainhas)','tendencia_2h':'Extrapolação da tendência de 2h'}
    for method in colors:
        ev=sorted([e for e in a['evaluations'] if e['metodo']==method],key=lambda e:e['horizonte_h'])
        ax.plot([origin]+[origin+timedelta(hours=e['horizonte_h']) for e in ev],[originlevel]+[e['previsao_experimental_m'] for e in ev],ls='--',marker='o',color=colors[method],label=labels[method])
    ax.axvline(origin,color='#8795a2',ls=':');ax.set(xlim=(origin-timedelta(hours=4),end+timedelta(minutes=15)),ylabel='Nível na régua (m)');style(ax);ax.legend(loc='upper left',fontsize=10)
    vals='  |  '.join(f'{dt(r["horario"]):%Hh}: {pt(r["nivel_experimental_m"],1)} m' for r in a['forecast'])
    fig.text(.075,.19,vals,size=12,weight='bold')
    fig.text(.075,.13,'Os números são saídas de um modelo sem validação suficiente para esta chuva.\nAs linhas não delimitam o nível máximo possível nem um intervalo de confiança.',size=12,color='#a52a25')
    fig.text(.075,.065,f'Base do cálculo: {origin:%d/%m/%Y %H:%M} BRT • Emissão: {stamp}\nFontes: SIGMA, SGB/SACE e D1 de produção. Chuva adicional e CERAN analisadas como contexto.',size=10)
    fig.savefig(OUT/'mucum-simulacao-nao-validada.png',dpi=170);plt.close(fig)
    # Map: exact upstream graph topology with basin polygons, not municipality membership.
    fig,ax=plt.subplots(figsize=(12,10),facecolor='#f7f9fb');fig.subplots_adjust(top=.85,bottom=.16)
    palette={'Baixo Antas':'#c9e4f3','Carreiro':'#f5d8ab','Prata-Turvo':'#d4dfb5','Alto Antas':'#d4d1ef','Tainhas':'#f1c9d4'}
    for f in json.loads((RAW/'upstream-basins.geojson').read_text())['features']:
        geo=f['geometry'];polys=[geo['coordinates']] if geo['type']=='Polygon' else geo['coordinates']
        for polygon in polys:ax.add_patch(PatchPolygon(polygon[0],facecolor=palette[basin_group(f['properties']['COBACIA'])],edgecolor='white',linewidth=.15))
    sig=json.loads((RAW/'stations-inside.json').read_text());new=[s for s in ps if s['inside'] and not s['already_sigma']]
    ax.scatter([s['lon'] for s in sig],[s['lat'] for s in sig],s=20,c='#24627d',label='100 códigos SIGMA',zorder=3)
    ax.scatter([s['lon'] for s in new],[s['lat'] for s in new],s=48,c='#b04622',marker='^',edgecolors='white',linewidth=.5,label='22 códigos adicionais no D1',zorder=4)
    ax.scatter([-51.86722],[-29.16694],s=130,c='#111a24',marker='*',zorder=5);ax.annotate('Régua Muçum',(-51.86722,-29.16694),xytext=(-15,-28),textcoords='offset points',weight='bold')
    ax.text(-52.04,-28.55,'Guaporé\nfora da bacia\nda régua',fontsize=10,color='#7a4747',ha='right')
    ax.autoscale_view();ax.set_aspect(1/np.cos(np.deg2rad(29)));ax.legend(loc='lower right');ax.set(xlabel='Longitude',ylabel='Latitude');ax.grid(alpha=.15)
    for label,x,y in [('Carreiro',-51.86,-28.41),('Prata / Turvo',-51.46,-28.30),('Alto Antas',-50.65,-28.78),('Tainhas',-50.4,-29.29),('Baixo Antas',-51.45,-29.24)]:
        ax.text(x,y,label,ha='center',fontsize=10,weight='bold',color='#46535c',bbox={'facecolor':'white','alpha':.65,'edgecolor':'none','pad':2})
    fig.text(.08,.947,'ESTAÇÕES A MONTANTE DE MUÇUM',size=24,weight='bold');fig.text(.08,.903,'122 códigos identificados • área de contribuição aproximada: 16.047 km²',size=14)
    fig.text(.08,.092,'Delimitação ANA BHO2017 5K • 367 trechos conectados até a régua 86510000.\nO Guaporé entra depois da régua, mas pode afetar outras áreas do município.\nCódigos não equivalem necessariamente a instrumentos independentes; cobertura não é exaustiva.',size=11)
    fig.savefig(OUT/'mapa-estacoes.png',dpi=170);plt.close(fig)
    unified=[{'id':r['id'],'rede':r['network'],'nome':r['name'],'lat':r['lat'],'lon':r['lon'],'subbacia':r['subbacia'],'origem':'SIGMA','ultimo_dado':r['observado_em'],'qualidade':r['qualidade']} for r in inv]
    unified += [{'id':r['id'],'rede':'ANA via D1','nome':r['name'],'lat':r['lat'],'lon':r['lon'],'subbacia':r['subbacia'],'origem':'Cloudflare D1','ultimo_dado':r['last'],'qualidade':r['note']} for r in new]
    with (OUT/'inventario-completo-122.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(unified[0]));w.writeheader();w.writerows(unified)
    assert len(unified)==122 and len({r['id'] for r in unified})==122
    selected=next(e for e in a['evaluations'] if e['metodo']=='montante' and e['horizonte_h']==6)
    table='\n'.join(f'| {dt(r["horario"]):%H:%M} | {pt(r["nivel_experimental_m"],1)} m |' for r in a['forecast'])
    report=f'''# Muçum: avaliação hidrológica de 21/09/2026

Elaborado em {stamp}. Resultado: **não há previsão numérica validada para divulgar à população a partir desta análise**. Os cálculos foram feitos e testados; o teste mostrou subestimação importante no próprio evento de hoje.

## Resultado que pode ser comunicado como observação

- Régua SGB 86510000: **{pt(lv)} m às {last:%H:%M} BRT**. A leitura é relativa à régua, não à profundidade nas ruas.
- 14 de Julho: vazão de saída **{pt(latest['outflow'])} m³/s às {dt(latest['timestamp']):%H:%M}**, comparada a 512,86 m³/s às 10h. Não se somam as três usinas em série: isso contaria novamente a mesma água.
- Arquivo para compartilhar como situação observada: [mucum-observado.png](mucum-observado.png). Ele não assegura ausência de inundação. Siga orientações da Defesa Civil e os boletins do SACE/SGB.

## Consulta real à produção da Cloudflare

Banco D1 `sofik-monitoramento-push`, configurado em `wrangler.jsonc`, consultado com Wrangler remoto. Apenas SELECTs das tabelas hidrológicas. Respostas confirmam `rows_written=0` e `changed_db=false`. Nenhuma implantação, alerta ou mensagem externa foi realizada.

Foram extraídos {prod['ceran_rows']} registros CERAN das três usinas, {prod['sace_rows_deduplicated']} registros SACE sem o prefixo duplicado `sace-`, e {prod['rain_rows']} registros de chuva de 29 códigos. Há aproximadamente 45 horas de histórico nesse recorte da produção; não foi encontrado histórico contínuo longo das usinas nessas tabelas. SQL, horário, hashes e respostas estão em `raw/producao/`.

Das 29 estações de chuva do banco, 27 ficam dentro da bacia da régua: cinco já constavam no SIGMA e 22 são adicionais. Capigui e Linha Colombo ficam fora. O campo genérico de qualidade no banco não comprova a aprovação individual da chuva: o parser local aceita aprovação de nível OU de chuva.

## Cobertura dos pluviômetros

O HAR revelou os endpoints públicos de catálogos e históricos. Foram consultadas as redes identificadas ali e cruzadas as coordenadas com a drenagem ANA BHO2017 5K, seguindo a conectividade dos rios até o trecho 125779: 367 trechos, aproximadamente 16.047 km². O polígono inclui a microbacia inteira do trecho de saída (12,828 km²), sem corte topográfico exato na régua.

Inventário: **122 códigos** (100 SIGMA + 22 adicionais no D1). Isso não prova que todos os pluviômetros existentes foram encontrados, nem que instrumentos próximos sejam independentes. Dos 100 do SIGMA, 69 de redes públicas alimentaram a análise espacial de chuva; 31 de redes particulares ficaram como contexto. As 22 adições do D1 foram auditadas com suas séries curtas, sem criar um histórico artificial para treinamento.

Foram abrangidos Alto Antas, Tainhas, Prata/Turvo, Carreiro e Baixo Antas. O Guaporé desemboca **depois da régua SGB de Muçum**, portanto não se soma sua chuva como contribuição direta a essa régua. Isso não exclui inundação ou remanso na parte do município junto ao Guaporé. Ver [mapa](mapa-estacoes.png) e [inventário completo](inventario-completo-122.csv).

Chuva foi ponderada espacialmente por proximidade em malha de 2 km, recortada por sub-bacia; não somada entre estações. Cobertura de pesos com observações na última hora analisada: {pt(a['rain_weight_with_data_latest']*100,1)}%. Valores negativos, ausência, reinícios de acumulado e divergência extrema de vizinhos foram tratados explicitamente. A semântica dos campos SIGMA ainda depende de confirmação documental; a chuva é uma análise provisória, não uma medição areal homologada.

## Cálculo e teste da projeção

Séries desde 25/07/2026 de Muçum, Linha José Júlio, Santa Tereza e Passo Carreiro. Níveis de réguas distintas permaneceram separados; não foram misturados com altitude absoluta DCRS. Fonte direta SACE tem prioridade sobre o espelho SIGMA. A maior diferença em horários coincidentes na conferência foi {pt(a['sigma_sace_max_difference_m'])} m.

Regressão regularizada, um modelo para cada horizonte de 1 a 6 horas, usando níveis e variações de 1/2/3/6 horas. Foram comparados modelo local, modelo com montante, montante com chuva disponível, persistência e tendência de 2h. Treino até 25/08; escolha de hiperparâmetros em 26/08–07/09; teste separado em 08/09–21/09. Alvos que atravessam a fronteira de treino/validação foram excluídos. Entradas usam somente observações passadas; intervalos sem leitura não viram chuva zero.

Somente os atributos de chuva de Tainhas tinham disponibilidade histórica suficiente para entrar no candidato com chuva. Esse candidato não ganhou na validação. **Logo, os números abaixo não são o resultado de um modelo calibrado com os 122 pluviômetros e todas as barragens.** Eles usam o modelo selecionado com níveis a montante. As outras chuvas e as usinas serviram para avaliar por que esse resultado não é confiável no evento atual.

No horizonte de 6h: {selected['n_teste']} origens de teste, erro absoluto médio {pt(selected['mae_teste_m'])} m; {selected['n_subidas_teste']} origens já em subida ≥0,2 m/h, erro médio {pt(selected['mae_subidas_m'])} m. Essas origens se sobrepõem e não são eventos independentes. **O maior erro foi {pt(selected['max_erro_teste_m'])} m:** previsão emitida com dados das 06h de hoje teria indicado 3,73 m às 12h, diante de 7,08 m observados. Um erro médio pequeno em períodos estáveis escondeu essa falha no início da subida.

O teste independente só observou níveis até 7,08 m; não validou as cotas projetadas para esta tarde nem uma cheia extrema. O conjunto completo chegou a 15,31 m, porém esses maiores níveis estão no treino. Vários acumulados atuais de chuva superam os máximos do treino. Não há curva de propagação atual calibrada para as vazões CERAN, nem chuva futura incorporada. Coeficientes de estudos antigos não foram transferidos automaticamente para a situação de 2026.

## Saída experimental — não divulgar como previsão de cheia

Base do cálculo: **{origin:%d/%m/%Y %H:%M} BRT**. A janela abaixo é relativa a essa base; não se deve deslocá-la para seis horas depois do momento em que o arquivo for aberto.

| Horário BRT | Saída do modelo não validado |
|---|---:|
{table}

Os valores são arredondados a 0,1 m para evitar falsa precisão; ainda assim, podem errar por metros. Não são limite superior e não têm intervalo de confiança validado. O candidato com chuva indicou 10,4 m às 18h e a extrapolação de tendência 10,9 m, mas a divergência entre métodos também não delimita a faixa possível. [Gráfico técnico](mucum-simulacao-nao-validada.png), [cálculos completos](previsoes-experimentais.csv), [testes](avaliacao-modelos.csv).

Para uma previsão pública defensável falta validação hidrológica operacional: histórico consistente de vazões/níveis em eventos comparáveis, curvas atuais de descarga e propagação, precipitação observada com metadados e previsão de chuva, e revisão do SGB/Defesa Civil. Mais sensores, isoladamente, não resolvem esses pontos.

## Fontes e reprodução

- [SACE Taquari](https://sace.sgb.gov.br/taquari/) e [CSV direto de Muçum](https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv).
- [SGB — descrição do sistema](https://www.sgb.gov.br/sace/taquari_apresentacao.php): informa aproximadamente quatro horas para Muçum. Seis horas desta análise não equivalem ao produto operacional.
- [SGB — estudo da estação Muçum](https://rigeo.sgb.gov.br/bitstreams/665b8bfa-d4fe-4cca-8720-694fdc7964d2/download), posição antes da confluência do Guaporé.
- [SGB — inundação em Muçum e Encantado](https://rigeo.sgb.gov.br/bitstream/doc/24993/2/estudo_preliminar_areas_inundadas_encantado_mucum_cheias_2023_2024_poster.pdf), influência local do Guaporé.
- [ANA BHO2017, drenagem](https://portal1.snirh.gov.br/arcgis/rest/services/SPR/BHO2017_5K_TRECHODRENAGEM/MapServer/0) e [áreas](https://portal1.snirh.gov.br/arcgis/rest/services/SPR/BHO2017_5K_AREADRENAGEM/MapServer/0).
- [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php), [Monte Claro](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHMC.php), [Castro Alves](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php).
- Endpoints SIGMA e arquivos brutos estão nos manifestos em `raw/`. Credenciais do HAR não foram copiadas.

Scripts locais: `scripts/hydro_production_read.py`, `hydro_production_assess.py`, `hydro_model.py`, `hydro_deliver.py`. Dependências usadas: numpy/scipy, shapely/pyproj e matplotlib. Os scripts de coleta fazem GETs públicos; o script de produção faz SELECTs remotos. Não executar automaticamente como sistema de alerta.

**Substitui a extrapolação inicial em `outputs/mucum-2026-09-21/`, que não incorporava esta avaliação da bacia e não deve ser divulgada como previsão confiável.**
'''
    (OUT/'relatorio.md').write_text(report)
    (ROOT/'outputs/mucum-2026-09-21/LEIA-ANTES-DE-COMPARTILHAR.md').write_text('A extrapolação nesta pasta foi superada pela análise da bacia e reprovada para uso como previsão pública. Consulte ../mucum-bacia-2026-09-21/relatorio.md e o gráfico de observações, que não promete cotas futuras.\n')
    print('Created observed, experimental and basin charts, report, unified inventory.',flush=True)
if __name__=='__main__':run()
