"""Publish the 12-hour calculation with competing models and temporal validation."""
import csv,json
from datetime import datetime
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from hydro_precision_audit import OUT,HORIZON
from hydro_routing_data import TZ,savecsv

def read(name):return list(csv.DictReader((OUT/name).open()))
def num(x):return f'{float(x):.1f}'.replace('.',',')
def errnum(x):return f'{float(x):.2f}'.replace('.',',')
def run():
    selected=read('previsao-atualizada.csv');candidates=read('candidatos-latencia.csv');routing=read('roteamento-previsao.csv')
    meta=json.loads((OUT/'previsao-atualizada.json').read_text());ages=read('idades-fontes.csv')
    assert len(selected)==len(routing)==HORIZON==12
    assert len({r['model'] for r in selected})==1
    rows=[]
    for s,r in zip(selected,routing):
        assert s['time']==r['time']
        values=[float(f['forecast_m']) for f in candidates if f['lead_h']==s['lead_h']]+[float(r['forecast_m'])]
        assert len(values)==4 and np.isfinite(values).all()
        rows.append({'horario_brt':s['time'],'antecedencia_h':int(float(s['lead_h'])),'estatistico_selecionado_m':float(s['forecast_m']),'modelo_selecionado':s['model'],'propagacao_vazao_m':float(r['forecast_m']),'menor_resultado_modelos_m':min(values),'maior_resultado_modelos_m':max(values),'interpretacao':'Estimativas independentes; amplitude entre modelos não é intervalo de confiança nem limite de cheia.'})
    savecsv(OUT/'mucum-previsao-12h.csv',rows)
    # Compare like-for-like origins and include a flood subset, not only many low-flow hours.
    retros=read('retrospectivas-latencia.csv');mr=read('roteamento-retrospectivas.csv');stats=[]
    for row in rows:
        h=row['antecedencia_h'];model=row['modelo_selecionado']
        statistical=[r for r in retros if int(float(r['lead_h']))==h and r['model']==model]
        physical=[r for r in mr if int(r['h'])==h]
        common={(r['phase'],r['origin']) for r in statistical}&{(r['phase'],r['origin']) for r in physical}
        baseline_lookup={(r['phase'],r['origin']):r['base_m'] for r in statistical}
        for r in physical:
            if (r['phase'],r['origin']) in common:r['base_m']=baseline_lookup[(r['phase'],r['origin'])]
        for label,data in [('estatistico',statistical),('propagacao',physical)]:
            data=[r for r in data if (r['phase'],r['origin']) in common]
            for phase in ['test','today']:
                part=[r for r in data if r['phase']==phase]
                for subset in ['todos','nivel_alvo_maior_igual_9m']:
                    ss=[r for r in part if subset=='todos' or float(r['actual_m'])>=9]
                    err=np.array([float(r['forecast_m'])-float(r['actual_m']) for r in ss])
                    baseline=np.array([abs(float(r['base_m'])-float(r['actual_m'])) for r in ss if 'base_m' in r])
                    stats.append({'h':h,'model':label,'phase':phase,'subset':subset,'n':len(err),'mae_m':float(np.mean(abs(err))) if len(err) else None,'p90_abs_m':float(np.quantile(abs(err),.9)) if len(err) else None,'bias_m':float(np.mean(err)) if len(err) else None,'persistence_mae_m':float(baseline.mean()) if len(baseline) else None})
    savecsv(OUT/'validacao-12h.csv',stats)
    def stat(h,model,phase,subset='todos'):return next(r for r in stats if r['h']==h and r['model']==model and r['phase']==phase and r['subset']==subset)
    times=[datetime.fromisoformat(r['horario_brt']) for r in rows]
    z=dict(np.load(OUT/'telemetria-latencia.npz'));tt=z['times'];hh=z['raw:86510000:H'];origin=datetime.fromisoformat(meta['origin'])
    good=(tt>=origin.timestamp()-8*3600)&np.isfinite(hh)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(13.5,8.1));fig.subplots_adjust(left=.085,right=.975,bottom=.25,top=.78)
    fig.text(.085,.95,'Muçum | previsão independente de 12 horas',fontsize=23,weight='bold',color='#10263b')
    fig.text(.085,.905,'Referência: 21/09/2026 às 14h  •  Horizonte: 15h até 02h de 22/09  •  Horário de Brasília',fontsize=11)
    fig.text(.085,.86,'OBSERVADO: 7,88 m às 13h45  |  PREVISÃO: divergência relevante entre os métodos',weight='bold',color='#92400e')
    ax.plot([datetime.fromtimestamp(t,TZ) for t in tt[good]],hh[good],color='#10263b',lw=3,label='Nível observado (ANA)')
    styles={'linear_log':('#946b9c','--','Regressão linear'), 'arvores':('#72acbb',':','Árvores sem previsão de chuva'),'arvores_previsao_chuva':('#268a9c','--','Árvores com previsão de chuva')}
    for model,(color,ls,label) in styles.items():
        vv=[float(next(f for f in candidates if f['model']==model and int(float(f['lead_h']))==h)['forecast_m']) for h in range(1,13)]
        ax.plot(times,vv,color=color,ls=ls,lw=1.6,alpha=.8,label=label)
    ax.plot(times,[r['estatistico_selecionado_m'] for r in rows],color='#1468b3',lw=2.8,marker='o',ms=4,label='Estatístico escolhido na validação')
    ax.plot(times,[r['propagacao_vazao_m'] for r in rows],color='#c15a1c',lw=2.8,marker='s',ms=4,label='Propagação de vazão estimada')
    ax.axvline(origin,color='#667788',ls=':',lw=1)
    ax.axvspan(times[5],times[-1],alpha=.045,color='#c15a1c')
    ax.set_ylabel('Nível na régua de Muçum (m)')
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2,tz=TZ));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh\n%d/%m',tz=TZ));ax.grid(axis='y',alpha=.16);ax.legend(loc='upper left',fontsize=8.5,ncol=2)
    fig.text(.085,.155,'As curvas são estimativas concorrentes: não delimitam uma faixa de segurança ou um intervalo de confiança.',weight='bold',fontsize=10)
    fig.text(.085,.12,'A validação não demonstrou alta precisão para esta cheia. Os resultados não confirmam o pico nem o horário de queda.',fontsize=10)
    fig.text(.085,.085,'Dados: ANA, ONS, CERAN e previsões GFS/ECMWF/ICON. Coleta ao vivo: 21/09, 14h20. Referência vertical própria da régua.',fontsize=9,color='#45576b')
    fig.text(.085,.05,'Previsão não oficial. Para decisões de proteção, acompanhe os alertas da Defesa Civil e do SGB.',fontsize=9,color='#45576b')
    fig.savefig(OUT/'mucum-previsao-12h.png',dpi=180);plt.close(fig)
    table='\n'.join(f"| {datetime.fromisoformat(r['horario_brt']).strftime('%d/%m %Hh')} | {num(r['estatistico_selecionado_m'])} m | {num(r['propagacao_vazao_m'])} m | {num(r['menor_resultado_modelos_m'])}–{num(r['maior_resultado_modelos_m'])} m |" for r in rows)
    evaluation=[]
    for h in [1,3,6,9,12]:
        a,b=stat(h,'estatistico','test'),stat(h,'propagacao','test');c,d=stat(h,'estatistico','today'),stat(h,'propagacao','today')
        evaluation.append(f"| {h}h | {errnum(a['mae_m'])} / {errnum(b['mae_m'])} m | {errnum(c['mae_m'])} / {errnum(d['mae_m'])} m | {c['n']} / {d['n']} |")
    age_lines='\n'.join(f"| {name} | {next(r for r in ages if r['source']==code)['last_time'][11:16]} | {num(next(r for r in ages if r['source']==code)['value'])} {unit} |" for code,name,unit in [('86510000','Muçum','m'),('86472000','Linha José Júlio','m'),('86472600','Santa Tereza','m'),('86500000','Passo Carreiro','m'),('julho','14 de Julho — saída','m³/s')])
    text=f'''# Muçum — previsão de 12 horas

Calculado em {datetime.now(TZ).strftime('%d/%m/%Y %H:%M')} BRT. Referência: **21/09/2026, 14h**. Horizonte de 12h após essa referência, até **22/09, 02h**; o prazo restante é menor que 12h no momento da entrega. Dados consultados às 14h20. Medição de Muçum usada: **7,88 m às 13h45**.

**Foi possível calcular o horizonte de 12 horas, mas não demonstrar alta precisão para esta cheia.** A divergência entre os métodos deve acompanhar qualquer divulgação. Nenhum dos valores constitui previsão oficial, limite máximo da inundação ou indicação de área segura.

| Horário BRT | Estatístico selecionado | Propagação de vazão | Menor–maior dos quatro modelos |
|---|---:|---:|---:|
{table}

A amplitude entre modelos **não é intervalo de confiança**. Não há fundamento para escolher a curva mais baixa ou mais alta como a verdadeira, nem para interpretar achatamento ou queda de uma curva como confirmação de pico. Os valores se referem à régua ANA 86510000, não à altitude absoluta nem à profundidade da água nas ruas.

## Atualizações incorporadas

| Fonte | Última observação em 21/09 | Valor |
|---|---|---:|
{age_lines}

A vazão de saída de 14 de Julho caiu de 4.212,67 m³/s às 13h para 3.962,18 m³/s às 14h. Esta informação substituiu a extrapolação que ainda não conhecia a leitura das 14h. Uma redução na usina não implica redução imediata em Muçum: a onda já propagada e as contribuições laterais continuam relevantes. As futuras operações da usina não são conhecidas.

## Como o prazo de 12h foi calculado

Foram ajustados modelos separados para cada antecedência de 1 a 12h. O estatístico seleciona entre regressão com transformação logarítmica e árvores, com/sem previsão meteorológica, usando somente a validação histórica. Para a curva de 12h, foi escolhida uma única família pelo escore médio de validação dos 12 prazos; escolher o vencedor independentemente em cada hora criava uma troca artificial de família entre 01h e 02h, com salto de quase 7 m. Essa troca foi eliminada sem suavizar ou alterar as previsões individuais. A alternativa por vazão usa propagação distribuída com pesos não negativos, conservação das entradas fluviais, chuva apenas na área incremental de 1.273 km² e assimilação da última observação de Muçum. O atraso real de 15 minutos dessa observação substituiu o valor fixo de 30 minutos da emissão anterior.

A vazão futura a montante também foi prevista separadamente para cada prazo; não foi mantida constante nem substituída por observações futuras. A chuva futura usa previsões de GFS, ECMWF e ICON arquivadas com antecedência de 24h do horário válido, permitindo comparação histórica causal até 12h. São previsões de pontos representativos, não medições futuras ou chuva areal exata. Novas emissões meteorológicas não foram inseridas apenas no caso atual em um modelo treinado com antecedências diferentes.

O catálogo da bacia contém 122 identificadores, mas **27 séries ANA** sustentam a calibração pluviométrica longa. Não se afirma que todos os 122 pluviômetros tenham sido calibrados individualmente. O trajeto até a régua usa a rede hidrográfica e exclui contribuição direta do Guaporé, cuja confluência fica abaixo da régua; possíveis efeitos de remanso não foram determinados. O atraso médio do roteamento é cerca de 5,4h desde 14 de Julho e 10,6h desde Passo Carreiro, respostas distribuídas que não equivalem a um tempo fixo para toda chuva atingir Muçum.

## Erro por antecedência

Treino inicial: abril–setembro/2025; escolha de parâmetros: outubro/2025–junho/2026; teste temporal: julho–20/09/2026. Os coeficientes finais usam apenas alvos anteriores a 21/09. A versão do método foi desenvolvida após observar erros desta manhã: o teste de hoje é diagnóstico retrospectivo, não validação prospectiva independente. Foram impostos os atrasos atuais de telemetria, sem reconstruir os horários históricos de publicação/revisão.

Cada célula abaixo informa **estatístico / propagação**, comparados nas mesmas origens disponíveis para os dois métodos. MAE é erro absoluto médio, não margem garantida.

| Prazo | MAE no teste histórico | MAE nas retrospectivas de hoje | N de origens de hoje |
|---|---:|---:|---:|
{chr(10).join(evaluation)}

Os testes de 9–12h de hoje usam poucas origens da madrugada, anteriores à aceleração atual. Não validam uma previsão emitida agora durante a subida. O arquivo `validacao-12h.csv` inclui P90, viés, persistência como referência e subconjunto de níveis ≥9 m, para não confundir muitos períodos de rio baixo com precisão em cheia. As amostras horárias se sobrepõem e não equivalem a eventos independentes.

A subida de Linha José Júlio de 7,34 para 11,35 m entre 12h30 e 13h30 excedeu a maior subida horária do histórico usado. As árvores podem subestimar eventos fora do treino; regressões podem extrapolar em excesso. A propagação também depende de curvas-chave e previsões das vazões futuras. Nenhum desses limites foi eliminado pelo simples aumento do horizonte.

## Verificação e reprodução

Os seis testes causais da integração da chuva passaram. Foram conferidos os 12 horários consecutivos, a mudança de data à meia-noite e valores finitos dos quatro modelos. Dados brutos e horários de coleta estão em `raw/manifest.json`. As previsões anteriores foram preservadas. Não houve nova escrita em produção, publicação ou envio de mensagens.

Executar com `HYDRO_OUTPUT_DIR` apontando para esta pasta e `HYDRO_HORIZON=12`: `hydro_latency_forecast.py`, `hydro_mass_check.py`, `hydro_mass_forecast.py`, `hydro_12h_report.py`. Scripts em `../../scripts/`. Dependências locais usadas: `/tmp/radar-hydro-libs` e `/tmp/radar-plot-libs`.

Fontes: [ANA — telemetria](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx), [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php), [ONS — reservatórios](https://dados.ons.org.br/dataset/dados_hidrologicos_ho), [Open-Meteo — arquivo de previsões](https://open-meteo.com/en/docs/previous-runs-api), [SGB — operação do Taquari](https://rigeo.sgb.gov.br/handle/doc/25841).
'''
    (OUT/'relatorio-12h.md').write_text(text)
    stamps=np.array([t.timestamp() for t in times]);assert np.all(np.diff(stamps)==3600) and stamps[-1]-origin.timestamp()==12*3600
    (OUT/'verificacao-12h.json').write_text(json.dumps({'hours':12,'finite_models':4,'consecutive_hourly_targets':True,'midnight_date_rollover':True,'last_target':times[-1].isoformat(),'single_statistical_family':True,'high_accuracy_demonstrated':False},indent=2))
    print(table);print('\n'.join(evaluation))

if __name__=='__main__':run()
