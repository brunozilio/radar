"""Show corrected inputs, measured improvements, and unresolved model disagreement."""
import csv,json,xml.etree.ElementTree as ET
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from hydro_precision_audit import OUT,PREV
from hydro_routing_data import TZ,epoch,iso,savecsv

def f(v,n=2):return f'{float(v):.{n}f}'.replace('.',',')
def run():
    current=json.loads((OUT/'previsao-atualizada.json').read_text());old=json.loads((PREV/'previsao-combinada.json').read_text());evals=list(csv.DictReader((OUT/'avaliacao-correcoes.csv').open()));candidates=list(csv.DictReader((OUT/'candidatos-latencia.csv').open()));comparison=[]
    for h in range(1,7):
        rows=[r for r in evals if int(r['h'])==h and r['phase']=='today'];best=min(rows,key=lambda r:float(r['validation_score']));prior=old['forecast'][h-1]['today_mae_m'];after=float(best['mae_m'])
        comparison.append({'h':h,'old_mae_m':prior,'corrected_mae_m':after,'relative_improvement_pct':100*(prior-after)/prior,'n':int(best['n']),'model':best['model']})
    savecsv(OUT/'antes-depois-mesmas-origens.csv',comparison)
    physical=list(csv.DictReader((OUT/'roteamento-previsao.csv').open()))
    verification=json.loads((OUT/'raw/verification-manifest.json').read_text());latest=max([r for d in verification if d['station']=='86510000' for r in d['last'] if r.get('NivelFinal') is not None],key=lambda r:r['DataHora']);latest_t=epoch(latest['DataHora']);latest_h=float(latest['NivelFinal'])/100
    discussion=[]
    for row in current['forecast']:
        same=[c for c in candidates if float(c['lead_h'])==row['lead_h']];p=next(r for r in physical if float(r['h'])==row['lead_h']);values=[float(c['forecast_m']) for c in same]+[float(p['forecast_m'])];lo=min(values);hi=max(values)
        discussion.append({'time':row['time'],'selected_by_historical_validation_m':row['forecast_m'],'minimum_candidate_m':lo,'maximum_candidate_m':hi,'selected_empirical_error_m':row['today_p90_abs_m'],'interpretation':'Model spread is not a probabilistic interval or a safety limit.'})
    savecsv(OUT/'divergencia-modelos.csv',discussion)
    z=dict(np.load(OUT/'telemetria-latencia.npz'));t=z['times'];observed=z['raw:86510000:H'];mask=(t>=epoch('2026-09-21T07:00:00'))&np.isfinite(observed);dates=[datetime.fromtimestamp(v,TZ) for v in t[mask]];forecast_times=[datetime.fromisoformat(r['time']) for r in current['forecast']]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(13,8),facecolor='#fafbfc');fig.subplots_adjust(left=.085,right=.97,top=.78,bottom=.24)
    ax.plot(dates,observed[mask],lw=3,color='#156779',label='Muçum observado — ANA')
    ax.plot([dates[-1],datetime.fromtimestamp(latest_t,TZ)],[observed[mask][-1],latest_h],color='#156779',lw=3)
    labels={'linear_log':'Regressão: extrapola a subida forte','arvores':'Resposta não linear','arvores_previsao_chuva':'Resposta não linear + previsão de chuva'};colors={'linear_log':'#a85c20','arvores':'#78558e','arvores_previsao_chuva':'#a27daf'}
    for name in labels:
        rows=sorted([r for r in candidates if r['model']==name],key=lambda r:float(r['lead_h']));x=[dates[-1]]+[datetime.fromisoformat(r['time']) for r in rows];y=[observed[mask][-1]]+[float(r['forecast_m']) for r in rows];ax.plot(x,y,lw=2,ls='--',marker='o',ms=4,color=colors[name],label=labels[name])
    ax.plot([dates[-1]]+[datetime.fromisoformat(r['time']) for r in physical],[observed[mask][-1]]+[float(r['forecast_m']) for r in physical],color='#428367',lw=2,ls='--',marker='o',ms=4,label='Propagação de vazão + contribuição local')
    ax.axvline(datetime.fromisoformat(current['origin']),color='#6c7982',ls=':',lw=1);ax.annotate('7,88 m\n13h45 observado',(datetime.fromtimestamp(latest_t,TZ),latest_h),xytext=(-8,-35),textcoords='offset points',ha='right',color='#156779',fontweight='bold')
    ax.set_ylabel('Nível na régua de Muçum (m)');ax.set_ylim(3,20);ax.set_xlim(datetime(2026,9,21,7,tzinfo=TZ),datetime(2026,9,21,20,25,tzinfo=TZ));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh',tz=TZ));ax.xaxis.set_major_locator(mdates.HourLocator(interval=1,tz=TZ));ax.grid(axis='y',alpha=.2);ax.legend(frameon=False,loc='upper left',fontsize=10);ax.set_xlabel('21/09/2026 • Horário de Brasília (UTC−3)')
    ax.annotate('18,0 m',(forecast_times[-1],float(next(r['forecast_m'] for r in candidates if r['model']=='linear_log' and float(r['lead_h'])==6))),xytext=(-8,10),textcoords='offset points',ha='right',color='#a85c20',fontweight='bold')
    ax.annotate('12,0–12,2 m',(forecast_times[-1],12.16),xytext=(-8,14),textcoords='offset points',ha='right',color='#78558e',fontweight='bold')
    ax.annotate('16,7 m',(forecast_times[-1],16.66),xytext=(-8,10),textcoords='offset points',ha='right',color='#428367',fontweight='bold')
    fig.text(.085,.945,'MUÇUM · REVISÃO APÓS AUDITORIA DOS ERROS',fontsize=19,fontweight='bold',color='#173b49')
    fig.text(.085,.905,'Referência: 14h • Muçum usado no cálculo: 7,69 m às 13h30 • Recebido depois: 7,88 m às 13h45',fontsize=11,color='#4e626c')
    fig.text(.085,.86,'INCERTEZA ELEVADA NAS 4–6H • PREVISÃO INDEPENDENTE, NÃO OFICIAL',fontsize=12,fontweight='bold',color='#9f4c22')
    fig.text(.085,.145,'As curvas mostram resultados de modelos calibrados. A divergência aumenta nas próximas horas.',fontsize=10,color='#485c66')
    fig.text(.085,.114,'Linha José Júlio subiu 4,01 m/h; o máximo no histórico usado era 1,63 m/h. A extrapolação é especialmente incerta.',fontsize=10,color='#485c66')
    fig.text(.085,.083,'12 m e 18 m são resultados alternativos, não limites mínimo e máximo. Não há pico confirmado nesta janela.',fontsize=10,color='#8b4320')
    fig.text(.085,.052,'Fontes: ANA, SGB, ONS/CERAN e previsões meteorológicas. Siga as orientações da Defesa Civil.',fontsize=10,color='#485c66')
    fig.savefig(OUT/'mucum-revisao-6h.png',dpi=180,facecolor=fig.get_facecolor());plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5.8),facecolor='#fafbfc');fig.subplots_adjust(bottom=.21,top=.80);hh=np.arange(1,7);before=[r['old_mae_m'] for r in comparison];after=[r['corrected_mae_m'] for r in comparison]
    ax.bar(hh-.18,before,width=.35,color='#acb5bd',label='Versão anterior');ax.bar(hh+.18,after,width=.35,color='#186c7b',label='Correção + resposta não linear');ax.set_xticks(hh,[str(h)+'h' for h in hh]);ax.set_ylabel('Erro absoluto médio (m)');ax.grid(axis='y',alpha=.2);ax.legend(frameon=False)
    for h,b,a in zip(hh,before,after):ax.text(h+.18,a+.025,f(a),ha='center',fontsize=10)
    fig.text(.10,.93,'O que melhorou — e o que ainda não melhorou',fontsize=18,fontweight='bold');fig.text(.10,.865,'Mesmas origens retrospectivas desta manhã • dados congelados na base de 13h',fontsize=11);fig.text(.10,.08,'A melhora em 1–3h não se estende consistentemente a 4–6h. Este diagnóstico não garante erro futuro.',fontsize=10)
    fig.savefig(OUT/'comparacao-erros.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)
    mass=json.loads((OUT/'conferencia-balanco.json').read_text());ages=current['source_ages'];summary=['# Auditoria e correção da previsão de Muçum','',f'Emitido em {datetime.now(TZ):%d/%m/%Y %H:%M} BRT. Referência da nova previsão: 14h. Medição de Muçum usada no cálculo: **7,69 m às 13h30**. Recebida depois do cálculo, às 14h12: **7,88 m às 13h45**; essa leitura não foi incorporada retroativamente à emissão congelada.','',
    '**Conclusão:** houve um defeito real de processamento da chuva e ele foi corrigido. A resposta não linear reduziu os erros retrospectivos de 1–3h, mas a precisão de 4–6h permanece insuficiente para divulgar um único nível como resultado confiável. A nova onda a montante está fora da amplitude de variação horária do histórico usado.','',
    '## 1. Erro de chuva localizado e corrigido','',
    'O código anterior calculava uma chuva horária terminando na última leitura e a mantinha por até 65 minutos. Ao somar essas entradas em várias horas, podia reutilizar o mesmo intervalo enquanto faltava a próxima leitura. Exemplo auditado: a estação ANA 86403000 tinha 25,8 mm no intervalo terminado às 12h; no retrato anterior, essa mesma leitura podia aparecer novamente no campo horário das 13h. Ausência de leitura das 13h não significa nem 25,8 mm novos nem zero chuva.', '',
    'A função `observed_rain_windows` integra apenas os intervalos efetivamente medidos, divide intervalos de fronteira proporcionalmente e mantém explícita a fração sem observação. O acumulado de várias horas não soma cópias de uma chuva horária mantida por atraso. Essa função substituiu o trecho defeituoso em `hydro_routing_data.py` e alimenta as rotinas novas.', '',
    'Seis testes passaram: ausência de repetição na hora seguinte; independência de observações futuras; conservação nos intervalos parciais; distinção entre dado ausente e chuva zero; rejeição de lacunas longas; e monotonicidade dos totais com a duração da janela. A conferência com os contadores das seis estações que os disponibilizam apresentou concordância ≥99,998%: ChuvaFinal é consistente com os incrementos nessas séries, sem evidência de um erro geral de unidade por fator quatro.', '',
    '## 2. Extrapolação identificada; melhora parcial quantificada','',
    'As regressões anteriores combinavam chuva intensa, tendências e interação com chuva antecedente. Hoje, vários preditores ficaram além do intervalo histórico. Foram testadas janelas corrigidas, retirada da interação, transformação logarítmica e resposta não linear por árvores, com escolha de parâmetros pela validação histórica.', '',
    'Comparação controlada: mesmas origens, mesmos horários-alvo e dados congelados em 13h. Nenhum alvo de hoje foi usado para ajustar os coeficientes. O desenvolvimento foi motivado pelos erros observados hoje, portanto estes números são diagnóstico retrospectivo, não validação independente da solução corrigida.', '',
    '| Antecedência | MAE anterior | MAE corrigido | Mudança | N de origens |','|---|---:|---:|---:|---:|']
    for r in comparison:summary.append(f"| {r['h']}h | {f(r['old_mae_m'])} m | {f(r['corrected_mae_m'])} m | {'redução' if r['relative_improvement_pct']>=0 else 'aumento'} de {f(abs(r['relative_improvement_pct']),1)}% | {r['n']} |")
    summary+=['','**Não houve melhoria consistente de 4–6h.** Não foi escolhido um parâmetro por apresentar o menor erro nesta manhã. Uma árvore também pode limitar excessivamente a resposta fora do histórico; a regressão pode extrapolá-la demais. A divergência entre ambas é informação relevante, não ruído a esconder.','',
    '## 3. Defasagem da telemetria e nova onda','',
    'Uma base histórica completa contém leituras que ainda não haviam chegado no momento de uma previsão ao vivo. A nova avaliação impõe aos preditores as idades relativas observadas no corte das 14h. Os alvos de nível exigem medição exata; não são cópias mantidas de um nível antigo. O teste não reconstrói o horário de publicação de cada mensagem passada, que não está disponível. É um teste com atraso imposto, não prova de desempenho operacional.', '',
    '| Fonte | Horário da observação | Idade às 14h | Valor |','|---|---|---:|---:|']
    keep={'86510000':'Muçum','86472000':'Linha José Júlio','86472600':'Santa Tereza','86500000':'Passo Carreiro','julho':'14 de Julho — saída'}
    for a in ages:
        if a['source'] in keep:summary.append(f"| {keep[a['source']]} | {datetime.fromisoformat(a['last_time']):%H:%M} | {f(a['delay_minutes'],0)} min | {f(a['value'])} {'m³/s' if a['source']=='julho' else 'm'} |")
    summary+=['','A ANA informou Linha José Júlio em **11,35 m às 13h30**, com indicação de dado aprovado. Às 12h30 eram 7,34 m: **4,01 m de subida em uma hora**, contra máximo de **1,63 m/h** no histórico de abril/2025 a setembro/2026 usado aqui. O SGB consultado confirmou a subida até 8,32 m às 13h, mas ainda não havia publicado a leitura das 13h30. As fontes compartilham a rede de origem; isso não equivale a dois instrumentos independentes.', '',
    '## 4. Checagem física independente','',
    f'Foi delimitada a área incremental entre a 14 de Julho, o Passo Carreiro e Muçum: aproximadamente **{f(mass["incremental_area_km2"],0)} km²**. A chuva dessa área foi separada da chuva já representada pelos fluxos a montante, evitando dupla contagem de volume.', '',
    'Foi ajustado um roteamento de vazão com pesos não negativos; os pesos de cada entrada fluvial somam 1 e a fração de escoamento direto da chuva fica entre 0 e 1. O ajuste convergiu. O atraso médio ponderado resultou em 5,42h para a 14 de Julho e 10,60h para o Passo Carreiro; são médias da resposta distribuída, distintas das medianas de alinhamento dos picos/ondas da análise anterior.', '',
    'Mesmo usando as vazões e chuvas efetivamente observadas, a reconstrução no teste temporal apresentou MAE de **0,43 m**, P90 de **0,81 m** e erro máximo de **3,05 m**. Esse teste é de reconstrução da resposta, não de previsão: conhecer as vazões futuras seria informação adicional indisponível ao emitir a previsão. Por isso esse ajuste não foi apresentado como uma previsão mais precisa.', '',
    'Também foi executada a versão prospectiva: vazões futuras a montante estimadas com modelos treinados em dados anteriores, chuva futura de previsões previamente emitidas e assimilação do desvio da última vazão de Muçum observada. Partes de intervalos de chuva sem medição foram estimadas pela previsão meteorológica, sem apagar as parcelas já medidas. Nenhuma vazão futura observada entrou como preditor.', '',
    'Essa versão por vazão resultou em aproximadamente 10,3 / 12,1 / 13,4 / 14,6 / 15,5 / 16,7 m, de 15h a 20h. No teste temporal, seu MAE de 6h foi **0,40 m**, pior que os **0,18 m** do candidato estatístico; nas retrospectivas desta manhã, teve **1,47 m**, contra **1,61 m** do estatístico com atrasos impostos. Essa diferença no pequeno evento atual não demonstra superioridade prospectiva e não foi usada para escolher a curva de 16,7 m como previsão oficial ou precisa.', '',
    'As vazões da ANA associadas às réguas dependem das curvas-chave. Não são medições independentes contínuas de vazão. Seções, rugosidade, remanso e operação futura dos reservatórios não foram determinados por este ajuste.', '',
    '## 5. Previsão meteorológica faltante','',
    'Foram recuperadas também emissões individuais de GFS, ECMWF e ICON de 00 UTC e/ou 06 UTC, além do arquivo de previsões do ICON. A emissão de 00 UTC, disponível antes da subida da manhã, previa chuva muito menor em alguns pontos do que a observada nos pluviômetros da região. Como os pontos de grade e as áreas de influência dos pluviômetros diferem, essa comparação é diagnóstico de insuficiência da representação da chuva, não uma razão exata para multiplicar a previsão.', '',
    'A versão com previsões históricas de chuva usa valores emitidos com 24h de antecedência para permitir teste sem usar chuva futura observada. A inclusão de GFS/ECMWF/ICON produziu mudanças pequenas e não eliminou os erros do início da subida. As emissões individuais mais recentes foram usadas para conferência; não foram introduzidas apenas hoje num modelo treinado com outro prazo meteorológico.', '',
    '## 6. Revisão numérica — referência 14h','',
    'O candidato abaixo foi selecionado pela validação histórica. **A coluna não significa nível confirmado ou de alta precisão.** A amplitude das alternativas é especialmente relevante porque a nova aceleração está fora do histórico.', '',
    '| Horário | Candidato estatístico selecionado no histórico | Resultados dos quatro candidatos |','|---|---:|---:|']
    for r in discussion:summary.append(f"| {datetime.fromisoformat(r['time']):%Hh} | {f(r['selected_by_historical_validation_m'],1)} m | {f(r['minimum_candidate_m'],1)}–{f(r['maximum_candidate_m'],1)} m |")
    summary+=['','**A faixa entre candidatos não é intervalo de confiança nem limite máximo.** Em 20h, o modelo linear resulta em cerca de 18 m, o roteamento de vazão em 16,7 m e os não lineares em cerca de 12 m. A avaliação disponível não permite resolver essa divergência com alta confiança. Tampouco confirma pico ou queda.', '',
    'Esta edição substitui a versão anterior para consulta do método e dos resultados. As previsões antigas foram preservadas para auditoria. Nenhum alerta foi enviado e nenhuma alteração foi feita no banco de produção.', '',
    '## Arquivos e reprodução','',
    '- `mucum-revisao-6h.png`: gráfico da divergência, com horários e limitações dentro da imagem.',
    '- `comparacao-erros.png` e `antes-depois-mesmas-origens.csv`: ganho e piora na comparação controlada.',
    '- `previsao-atualizada.csv`, `divergencia-modelos.csv`, `retrospectivas-latencia.csv`: valores e erros auditáveis.',
    '- `auditoria-contadores.csv`, `janelas-chuva-corrigidas.csv`, `idades-fontes.csv`: diagnóstico dos dados.',
    '- `conferencia-balanco.json`, `roteamento-vazao-pesos.csv`: restrições e resultado do ajuste por vazão.',
    '- Scripts: `hydro_rain_windows.py`, `test_hydro_rain_windows.py`, `hydro_precision_audit.py`, `hydro_precision_fit.py`, `hydro_latency_forecast.py`, `hydro_mass_check.py`, `hydro_precision_report.py`.', '',
    '## Fontes','',
    '- [ANA — telemetria](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx).',
    '- [SGB — dados da régua de Muçum](https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv).',
    '- [ONS — dados horários de reservatórios](https://dados.ons.org.br/dataset/dados_hidrologicos_ho).',
    '- [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php).',
    '- [Open-Meteo — emissões meteorológicas individuais e disponibilidade](https://open-meteo.com/en/docs/single-runs-api).',
    '- [SGB — operação do sistema Taquari em 2025](https://rigeo.sgb.gov.br/handle/doc/25841).', '',
    'Para divulgação à população, preservar as datas, a identificação de previsão independente e a divergência. Este trabalho não identifica áreas seguras nem substitui as orientações da Defesa Civil.']
    (OUT/'relatorio-correcoes.md').write_text('\n'.join(summary)+'\n')
    prior=PREV/'relatorio.md';content=prior.read_text();banner='> **VERSÃO SUPERADA após auditoria:** foi corrigido o processamento das janelas de chuva. Consulte a [revisão e comparação dos erros](../mucum-auditoria-2026-09-21/relatorio-correcoes.md). Os números abaixo foram preservados como registro da emissão anterior.\n\n'
    if not content.startswith('> **VERSÃO SUPERADA'):prior.write_text(banner+content)
    print('Figures and audit report generated; no claim of solved six-hour accuracy.')

if __name__=='__main__':run()
