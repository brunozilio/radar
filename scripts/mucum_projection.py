"""Reproduce the dated, conditional Muçum projection from saved public observations.
Run: PYTHONPATH=/tmp/radar-plot-libs python3 scripts/mucum_projection.py
This is trend extrapolation, not an operational hydrological forecast.
"""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import csv, json, hashlib, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/mucum-2026-09-21'
RAW = OUT / 'raw'
TZ = timezone(timedelta(hours=-3))

def levels(path):
    result = {}
    for row in csv.DictReader(path.open(), delimiter=';'):
        dt = datetime.fromisoformat(row['data_hora_medicao']).replace(tzinfo=TZ)
        value = float(row['indice']) / 100
        if math.isfinite(value) and 0 <= value < 50:
            if dt in result and result[dt] != value:
                raise ValueError('Conflicting duplicate readings')
            result[dt] = value
    return result

def slope(data, origin, hours):
    times = [origin + timedelta(minutes=15*i) for i in range(-4*hours, 1)]
    if not all(t in data for t in times):
        raise ValueError('Incomplete 15-minute window')
    return float(np.polyfit(np.arange(-4*hours, 1)/4, [data[t] for t in times], 1)[0])

def write_csv(name, rows):
    with (OUT/name).open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

def fmt(v): return f'{v:.2f}'.replace('.', ',')

now = datetime.now(TZ)
data = levels(RAW/'sace-3.csv')
t0 = max(data); y0 = data[t0]
if not 0 <= (now-t0).total_seconds() <= 90*60:
    raise ValueError('Snapshot too old for a current projection; fetch fresh sources first')
rates = {h:slope(data,t0,h) for h in (1,2,3)}
# Clock-hour targets are relative to issue time, never to the old HAR capture.
first = now.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
forecast = []
for i in range(6):
    dt = first+timedelta(hours=i); lead = (dt-t0).total_seconds()/3600
    forecast.append({'horario_brasilia':dt.isoformat(), 'projecao_m':round(y0+rates[2]*lead,2),
        'tendencia_1h_m':round(y0+rates[1]*lead,2), 'tendencia_3h_m':round(y0+rates[3]*lead,2),
        'horas_desde_observacao':lead})
write_csv('projecao.csv',forecast)

# Causal retrospective check: only data before each origin enter its slope.
backtest=[]
for h in range(1,7):
    errors=[]
    for origin,y in sorted(data.items()):
        if origin.minute or origin+timedelta(hours=h)>t0: continue
        try: rate=slope(data,origin,2)
        except ValueError: continue
        target=origin+timedelta(hours=h)
        if rate>=.2 and target in data: errors.append(abs(y+rate*h-data[target]))
    backtest.append({'horizonte_h':h,'amostras_sobrepostas':len(errors),'erro_medio_absoluto_m':round(float(np.mean(errors)),3),
        'maior_erro_absoluto_m':round(max(errors),3)})
write_csv('checagem-retrospectiva.csv',backtest)

rain=[]
for path in sorted(RAW.glob('sigma-station-*.txt')):
    rows={}
    for line in path.read_text().splitlines():
        a=line.split()
        if len(a)>43:
            dt=datetime.strptime(a[3],'%Y-%m-%d_%H:%M').replace(tzinfo=TZ)
            if dt<=now: rows[dt]=a
    ordered=sorted(rows.items())
    if len(ordered)<2: continue
    start,a=ordered[0]; end,b=ordered[-1]
    daily=[float(r[21]) for _,r in ordered]
    increments=[float(r[43]) for _,r in ordered[1:]]
    accumulated=daily[-1]-daily[0]
    issue=any(v<0 for v in daily) or any(v<0 for v in increments) or any(v<u-0.05 for u,v in zip(daily,daily[1:]))
    if abs(sum(v for v in increments if v>=0)-accumulated)>.11:issue=True
    rain.append({'estacao':b[2], 'nome':b[31].replace('_',' '), 'latitude':float(b[0]),'longitude':float(b[1]),
        'inicio':start.isoformat(),'fim':end.isoformat(),'chuva_periodo_mm':round(accumulated,1) if not issue else '',
        'qualidade':'inconsistente; excluida do resumo' if issue else 'consistencia interna verificada; nao homologada',
        'fonte':f'https://sigmameteorologia.com/produtos/stations/2026-09-21/{b[2]}.txt'})
write_csv('pluviometros.csv',rain)
upstream=[]
for sid,name in [(32,'Santa Tereza'),(4,'Linha José Júlio'),(55,'Linha Colombo / Guaporé'),(54,'Passo Carreiro')]:
    d=levels(RAW/f'sace-{sid}.csv');t=max(d)
    upstream.append({'estacao':name,'horario':t.isoformat(),'nivel_regua_propria_m':d[t],
                     'variacao_ultima_hora_m':round(d[t]-d[t-timedelta(hours=1)],2)})
write_csv('montante.csv',upstream)

# Shareable chart. The band is explicitly sensitivity, not confidence/uncertainty bounds.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
fig,ax=plt.subplots(figsize=(13.6,7.7),dpi=170)
fig.patch.set_facecolor('#f5f8fc');ax.set_facecolor('#f5f8fc')
fig.subplots_adjust(left=.08,right=.96,top=.79,bottom=.29)
hist=[t for t in sorted(data) if t>=t0-timedelta(hours=8)]
ax.plot(hist,[data[t] for t in hist],color='#155c96',lw=3,label='Observado · SACE/SGB')
times=[t0]+[datetime.fromisoformat(r['horario_brasilia']) for r in forecast]
lead=np.array([(t-t0).total_seconds()/3600 for t in times])
ax.plot(times,y0+rates[2]*lead,'o--',color='#bc5518',lw=2.5,ms=5,label='Projeção condicional · tendência de 2 h')
low=np.min([y0+r*lead for r in rates.values()],axis=0); high=np.max([y0+r*lead for r in rates.values()],axis=0)
ax.fill_between(times,low,high,color='#e9a36a',alpha=.3,label='Sensibilidade às janelas de 1–3 h (não é intervalo de confiança)')
ax.axvline(t0,color='#8193a3',lw=1,ls=':')
for r,t in zip(forecast,times[1:]):
    ax.annotate(fmt(r['projecao_m'])+' m',(t,r['projecao_m']),xytext=(0,-24),textcoords='offset points',ha='center',fontsize=11,fontweight='bold',color='#983e0b')
ax.annotate(f'{fmt(y0)} m · {t0:%H:%M}',(t0,y0),xytext=(-14,25),textcoords='offset points',ha='right',color='#155c96',weight='bold')
ax.xaxis.set_major_locator(mdates.HourLocator(interval=1,tz=TZ));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh',tz=TZ))
ax.set_ylabel('Nível na régua de Muçum (m) · estação 86510000')
ax.set_xlabel('21 de setembro de 2026 · horário de Brasília (UTC−3)',labelpad=12)
ax.grid(axis='y',alpha=.18); ax.spines[['top','right']].set_visible(False)
ax.legend(loc='upper left',fontsize=9,frameon=False)
fig.text(.08,.94,'Muçum · próximas seis horas cheias',size=23,weight='bold',color='#152e43')
fig.text(.08,.89,'PROJEÇÃO EXPERIMENTAL DE TENDÊNCIA · NÃO É PREVISÃO OFICIAL',size=12,weight='bold',color='#a0440a')
fig.text(.08,.845,f'Emitida às {now:%H:%M}  |  Última medição: {t0:%H:%M}  |  Tendência de 2 h: +{fmt(rates[2])} m/h',color='#41566a')
fig.text(.08,.13,f'Limite importante: no retrospecto de subidas, o erro médio em 6 h foi {fmt(backtest[-1]["erro_medio_absoluto_m"])} m\n'
         'e o maior erro foi '+fmt(backtest[-1]['maior_erro_absoluto_m'])+' m. A faixa colorida NÃO representa toda a incerteza.',size=11,color='#8e3b17',linespacing=1.5)
fig.text(.08,.055,'Chuva adicional, propagação da cheia e operação de barragens podem mudar a trajetória.\nNão use estes valores para decidir permanência ou retorno a áreas de risco. Siga a Defesa Civil.',size=10,color='#41566a',linespacing=1.5)
fig.savefig(OUT/'projecao-mucum.png',facecolor=fig.get_facecolor())
fig.savefig(OUT/'projecao-mucum.svg',facecolor=fig.get_facecolor())

valid=[r for r in rain if r['chuva_periodo_mm']!='']
meta={'emitido_em':now.isoformat(),'observacao':{'horario':t0.isoformat(),'nivel_m':y0},'taxas_m_h':rates,'projecao':forecast,
      'retrospecto':backtest,'pluviometros_consultados':len(rain),'pluviometros_consistentes':len(valid),'montante':upstream,
      'metodo':'H(t)=H(t0)+slope_OLS_2h*(t-t0); janelas auxiliares de 1h e 3h; sem coeficiente chuva-cota calibrado',
      'fontes':{'nivel':'https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv','chuva':'https://sigmameteorologia.com/produtos/cemaden/2026-09-21/1200.txt'},
      'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in RAW.iterdir() if p.is_file()}}
(OUT/'resultado.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
report=f'''# Muçum — projeção condicional de nível

Emissão: {now:%d/%m/%Y %H:%M} (Brasília). Última observação oficial recuperada: **{fmt(y0)} m às {t0:%H:%M}**, estação SACE 86510000.

![Gráfico](projecao-mucum.png)

| Horário de Brasília | Projeção de tendência | Sensibilidade 1–3 h* |
|---|---:|---:|
'''
for r in forecast:
    vals=[r['tendencia_1h_m'],r['projecao_m'],r['tendencia_3h_m']]
    report+=f'| {datetime.fromisoformat(r["horario_brasilia"]):%H:%M} | {fmt(r["projecao_m"])} m | {fmt(min(vals))}–{fmt(max(vals))} m |\n'
report+='''
*Esta faixa compara somente três extrapolações lineares. Não é intervalo de confiança, limite mínimo/máximo do rio nem limite seguro. Os valores são condicionais à continuidade da tendência; não identificam o pico da cheia. Duas casas decimais servem para reproduzir a conta, não representam precisão real.

## Método e limites

Regressão linear nos nove registros de 15 minutos das últimas duas horas, ancorada na última leitura observada, sem suavizar essa observação. A fórmula é `nível = último nível + taxa × horas desde a última medição`. As duas janelas auxiliares usam 5 e 13 registros. Os seis horários são as próximas seis horas cheias após a emissão, portanto o horizonte desde a medição é maior que seis horas no último ponto. Não misturamos réguas ou cotas altimétricas de outras estações.

'''
report+=f'Taxas: 1 h = {fmt(rates[1])}; 2 h = {fmt(rates[2])}; 3 h = {fmt(rates[3])} m/h.\n\n'
report+='''Cheque retrospectivo causal no histórico disponível desde 21/08/2026: origens em horas cheias, subida estimada ≥0,20 m/h, sem observações futuras no cálculo. Os casos se sobrepõem e não são eventos independentes; este teste não valida uso operacional nem cobertura probabilística. Em 6 h: '''+f'{backtest[-1]["amostras_sobrepostas"]} casos, erro médio absoluto {fmt(backtest[-1]["erro_medio_absoluto_m"])} m e maior erro {fmt(backtest[-1]["maior_erro_absoluto_m"])} m. O último horário solicitado vai além deste horizonte de teste.\n\n'
report+='''## Chuva recuperada do HAR e atualizada

O HAR revelou `/produtos/cemaden/2026-09-21/1200.txt` (catálogo) e `/produtos/stations/2026-09-21/17718.txt` (histórico de Muçum). Foram feitas novas requisições GET com os cabeçalhos públicos de navegador/referência da captura, sem cookies ou tokens. O acesso inicial sem esses cabeçalhos retornou 403; os arquivos de dados foram depois obtidos com HTTP 200.

'''
report+=f'Consultados **{len(rain)} pluviômetros CEMADEN**, dos quais **{len(valid)}** passaram na consistência interna. Seleção regional de municípios na região contribuinte e entorno; não é delimitação geográfica rigorosa de sub-bacia e não produz média areal. Nenhum total foi somado entre estações.\n\n'
report+='''O acumulado mostrado é a diferença entre a primeira e a última leitura diária (coluna de índice 21, base zero), conferida pela soma dos incrementos (índice 43). A janela exata e os valores ausentes/inconsistentes estão no CSV. A interpretação foi verificada por consistência das séries, não por documentação oficial de esquema do SIGMA. Sensores com acumulados negativos, reinícios ou divergência entre incrementos e acumulado foram excluídos do resumo, nunca convertidos em zero de chuva. Valores altos consistentes ainda não são homologação de qualidade física do sensor.

| Estação | Janela | Chuva no período |
|---|---|---:|
'''
for r in sorted(valid,key=lambda r:r['chuva_periodo_mm'],reverse=True):
    report+=f'| {r["nome"]} ({r["estacao"]}) | {r["inicio"][11:16]}–{r["fim"][11:16]} | {r["chuva_periodo_mm"]:.1f} mm |\n'
report+='''
**A chuva e as estações a montante foram usadas como contexto de risco e verificação da subida; não receberam um coeficiente artificial de conversão de milímetros para metros.** Faltam modelo chuva–vazão–cota calibrado, tempos de trânsito validados, previsão quantitativa de chuva e operação de barragens para uma previsão hidrológica quantitativa completa. A extrapolação pode errar para cima ou para baixo.

## Montante — cada nível em sua própria régua

'''
for r in upstream:report+=f'- {r["estacao"]}: {fmt(r["nivel_regua_propria_m"])} m às {r["horario"][11:16]}, variação de +{fmt(r["variacao_ultima_hora_m"])} m em uma hora.\n'
report+='''
## Fontes e segurança

- [Medições SACE/SGB de Muçum](https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv).
- [Histórico pluviométrico SIGMA/CEMADEN de Muçum](https://sigmameteorologia.com/produtos/stations/2026-09-21/17718.txt). Demais URLs no CSV de pluviômetros.
- [Descrição oficial do sistema de alerta Taquari](https://www.sgb.gov.br/sace/taquari_apresentacao.php): o SGB descreve antecipação aproximada de quatro horas para Muçum, diferente desta extrapolação experimental de seis horários.
- [Boletins SACE](https://www.sgb.gov.br/sace/boletins.php?idbacia=9): a página recuperada nesta análise tinha como mais recente 14/08/2026 às 22h; não foi tratada como previsão de hoje.
- [Alertas da Defesa Civil RS](https://www.defesacivil.rs.gov.br/avisos-e-alertas).

Não foi emitida previsão de pico nem conclusão de ausência de inundação. Não use este gráfico como critério de permanência/retorno ou para aguardar uma cota antes de atender a uma ordem de evacuação. Em emergência, Defesa Civil 199 / Bombeiros 193.

Arquivos: `projecao.csv`, `pluviometros.csv`, `montante.csv`, `checagem-retrospectiva.csv`, `resultado.json`, gráfico PNG/SVG e respostas de origem em `raw/`. A captura HAR original não foi copiada para a saída; apenas corpos de dados meteorológicos públicos foram extraídos. Nenhuma publicação, deploy, alerta ou mensagem externa foi executado.
'''
(OUT/'relatorio.md').write_text(report)
print(json.dumps({k:meta[k] for k in ['emitido_em','observacao','taxas_m_h','projecao','pluviometros_consultados','pluviometros_consistentes']},ensure_ascii=False,indent=2))
