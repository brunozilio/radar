"""Produce a dated, auditable independent forecast and its scientific figure."""
import csv,json,math
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from hydro_routing_data import OUT,OLD,TZ,epoch,iso,load_ana,savecsv
from hydro_adaptive_ensemble import online

def fmt(x,n=1): return f'{x:.{n}f}'.replace('.',',')

def run():
    doc=json.loads((OUT/'previsao-combinada.json').read_text());rows=doc['forecast'];origin=epoch(doc['origin'][:19]);z=dict(np.load(OUT/'telemetria.npz'));t=z['times']
    # Meaningful audit: future target perturbations cannot affect an earlier issue.
    rng=np.random.default_rng(57);tt=np.arange(100)*3600.;pp=rng.normal(size=(100,6));yy=rng.normal(size=100)
    a,wa=online(tt,pp,yy,6,24,1,2,.25);modified=yy.copy();modified[45:]+=1000
    b,wb=online(tt,pp,modified,6,24,1,2,.25)
    assert np.allclose(a[:51],b[:51]) and np.allclose(wa[:51],wb[:51])
    rain=json.loads((OUT/'chuva-pesos.json').read_text());assert all(abs(sum(r['weights'].values())-1)<1e-10 for r in rain)
    assert all(r['lower_reference_m']<=r['forecast_m']<=r['upper_reference_m'] for r in rows)
    assert all(epoch(r['time'][:19])==origin+r['h']*3600 for r in rows)
    assert len(rows)==6 and abs(z['86510000:H'][-1]-doc['observed_level_m'])<1e-9
    observations=[]
    for code,name in [('86510000','Muçum'),('86472000','Linha José Júlio'),('86472600','Santa Tereza'),('86500000','Passo Carreiro'),('86160000','Passo Tainhas')]:
        d=load_ana(code);ii=np.where(np.isfinite(d['level'])&(d['times']<=origin))[0];j=ii[-1]
        observations.append({'station':code,'name':name,'time':iso(d['times'][j]),'level_m':float(d['level'][j]),'age_minutes_at_origin':(origin-d['times'][j])/60})
    savecsv(OUT/'observacoes-base.csv',observations)
    # Compare baselines on exactly the ensemble's test origins.
    tested=list(csv.DictReader((OUT/'teste-combinado.csv').open()));stats=[]
    for h in range(1,7):
        for phase in ['test','today']:
            rr=[r for r in tested if int(r['h'])==h and r['phase']==phase];err={k:[] for k in ['combinacao','persistencia','tendencia_2h']}
            for r in rr:
                j=int((epoch(r['origin'][:19])-t[0])/900);actual=float(r['actual_m']);base=z['86510000:H'][j];past=z['86510000:H'][j-8]
                if not np.isfinite(past):continue
                for name,pred in [('combinacao',float(r['forecast_m'])),('persistencia',base),('tendencia_2h',base+h*(base-past)/2)]:err[name].append(abs(pred-actual))
            for name,e in err.items():stats.append({'h':h,'phase':phase,'method':name,'n':len(e),'mae_m':float(np.mean(e)),'max_abs_m':float(max(e))})
    savecsv(OUT/'comparacao-referencias.csv',stats)
    audit={'causal_future_target_perturbation':'passed','rain_weights_sum_one':'passed','forecast_time_alignment':'passed','forecast_base_matches_observation':'passed','production_rows_written':0,'checked_at':datetime.now(TZ).isoformat()}
    (OUT/'verificacao-final.json').write_text(json.dumps(audit,indent=2))
    # Persist exact input manifest, including current quality and empirical error limits.
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
    fig=plt.figure(figsize=(13,10),facecolor='#fafbfc');gs=fig.add_gridspec(2,1,height_ratios=[3,1],left=.085,right=.97,top=.81,bottom=.19,hspace=.39)
    ax=fig.add_subplot(gs[0]);dam=fig.add_subplot(gs[1],sharex=ax)
    mask=t>=origin-10*3600;dates=[datetime.fromtimestamp(v,TZ) for v in t[mask]]
    x=[datetime.fromtimestamp(origin,TZ)]+[datetime.fromisoformat(r['time']) for r in rows]
    y=[doc['observed_level_m']]+[r['forecast_m'] for r in rows];lo=[y[0]]+[r['lower_reference_m'] for r in rows];hi=[y[0]]+[r['upper_reference_m'] for r in rows]
    ax.fill_between(x,lo,hi,color='#e6ad53',alpha=.27,label='Faixa de referência dos erros')
    ax.plot(dates,z['86510000:H'][mask],color='#146777',lw=3,label='Nível observado — ANA')
    ax.plot(x,y,color='#ab5415',lw=2,ls='--',marker='o',ms=5,label='Estimativa central independente')
    ax.scatter(x[0],y[0],s=70,color='#146777',zorder=5)
    for xx,yy in zip(x[1:],y[1:]):ax.annotate(fmt(yy)+' m',(xx,yy),xytext=(0,10),textcoords='offset points',ha='center',fontsize=10,fontweight='bold')
    ax.annotate('7,46 m\n13h observado',(x[0],y[0]),xytext=(-10,-33),textcoords='offset points',ha='right',color='#146777',fontweight='bold')
    ax.set_ylabel('Nível na régua de Muçum (m)');ax.set_ylim(2,16);ax.grid(axis='y',alpha=.2);ax.legend(loc='upper left',frameon=False,fontsize=10)
    ax.axvline(x[0],color='#77838d',ls=':',lw=1);ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh',tz=TZ));ax.xaxis.set_major_locator(mdates.HourLocator(interval=1,tz=TZ))
    dam.plot(dates,z['julho:Q'][mask]/1000,color='#615093',lw=2,drawstyle='steps-post');dam.set_ylabel('Saída da usina\n(mil m³/s)');dam.set_title('14 de Julho: descarga em forte aumento a montante',loc='left',fontsize=11,pad=10);dam.grid(axis='y',alpha=.2);dam.set_ylim(0,5)
    dam.annotate('4.213 m³/s às 13h',(x[0],z['julho:Q'][-1]/1000),xytext=(10,-4),textcoords='offset points',color='#615093',fontweight='bold')
    dam.axvline(x[0],color='#77838d',ls=':',lw=1);dam.xaxis.set_major_formatter(mdates.DateFormatter('%Hh',tz=TZ));dam.set_xlim(datetime.fromtimestamp(origin-10*3600,TZ),datetime.fromtimestamp(origin+6.5*3600,TZ));dam.set_xlabel('21 de setembro de 2026 • horário de Brasília (UTC−3)')
    fig.text(.085,.954,'MUÇUM · PREVISÃO PARA AS PRÓXIMAS 6 HORAS',fontsize=19,fontweight='bold',color='#173b49')
    fig.text(.085,.916,'21/09/2026 • Base observada: 13h • Cálculo concluído: 13h34',fontsize=12,color='#4b5d66')
    fig.text(.085,.879,'PREVISÃO INDEPENDENTE • NÃO É BOLETIM OFICIAL • INCERTEZA ELEVADA',fontsize=12,fontweight='bold',color='#a04b1b')
    fig.text(.085,.112,'A faixa mostra erros históricos e desta manhã; não garante cobertura e não é um limite máximo.',fontsize=11,color='#8a3f1a')
    fig.text(.085,.087,'Em 6h, o erro absoluto médio nesta manhã foi 1,63 m; o percentil 90 foi 3,06 m (8 previsões retrospectivas).',fontsize=10,color='#485b65')
    fig.text(.085,.062,'A pequena queda entre 18h e 19h não confirma um pico. Esta régua não representa todo o município.',fontsize=10,color='#485b65')
    fig.text(.085,.037,'Fontes: ANA, ONS/CERAN, SIGMA, SGB e Defesa Civil RS. Siga os alertas e as orientações da Defesa Civil.',fontsize=10,color='#485b65')
    fig.savefig(OUT/'mucum-previsao-6h.png',dpi=180,facecolor=fig.get_facecolor());plt.close(fig)
    propagation=json.loads((OUT/'propagacao-resumo.json').read_text());inventory=list(csv.DictReader((OUT/'pluviometros-estrutura-completa.csv').open()));ana=list(csv.DictReader((OUT/'auditoria-ana.csv').open()))
    report=['# Muçum — previsão independente de seis horas','',f'**21/09/2026. Base: 13h BRT, 7,46 m. Cálculo: 13h34 BRT.** Estação ANA/SGB 86510000. Valores referidos à régua dessa estação.','',
    '**Resultado:** a estimativa central indica subida para aproximadamente 11–12 m no fim da janela. A incerteza hoje é elevada. A oscilação de 18h para 19h resulta de ajustes separados por horizonte e não confirma o horário nem o nível de um pico.','',
    '| Horário BRT | Central (m) | Referência inferior–superior (m) |','|---|---:|---:|']
    report += [f"| {datetime.fromisoformat(r['time']):%Hh} | {fmt(r['forecast_m'])} | {fmt(r['lower_reference_m'])}–{fmt(r['upper_reference_m'])} |" for r in rows]
    report += ['', 'A faixa é a estimativa central acrescida/subtraída do maior entre o percentil 90 do erro absoluto histórico em situações semelhantes e o percentil 90 do erro desta manhã. Não é intervalo probabilístico validado, nem máximo possível, nem cota de segurança. A série atual permanece fora do comportamento bem explicado pelos modelos em vários horários.', '', '## O que foi efetivamente consultado', '',
    f'- Produção Cloudflare D1: consulta somente de leitura, zero linhas gravadas. O histórico curto de produção foi complementado diretamente nas fontes primárias.',
    f'- ANA: **27 estações a montante**, de abril/2025 a setembro/2026; {sum(int(r["n_records"]) for r in ana):,} registros distintos de estação/hora ou estação/15 minutos. Nem todos os campos estão presentes em cada registro. O histórico inclui Muçum a 15,00 m em junho/2025 e 19,86 m em julho/2026.',
    '- ONS: 38.776 registros horários das usinas Castro Alves, Monte Claro e 14 de Julho; CERAN complementa os horários mais recentes. Dados horários do ONS sujeitos a revisão, sem consistência final. A marca horária representa o fim do intervalo.',
    '- SIGMA/HAR: 100 identificadores dentro da bacia, incluindo 69 da rede pública e 31 de redes particulares. Somados aos identificadores adicionais da ANA, o inventário contém **122 IDs**, não necessariamente 122 instrumentos fisicamente independentes.',
    '- **A previsão não trata os 122 IDs como 122 contribuições independentes.** Os 27 com séries longas ANA entram na chuva espacial e/ou telemetria; as demais estações permitem conferência espacial. Séries curtas, sensores próximos e referências distintas impedem atribuir a cada ID um coeficiente confiável.',
    '- Defesa Civil RS: oito estações conferidas; sete consultas históricas retornaram dados. Muitos Capões/Lagoa Vermelha retornou “Operação bloqueada”. Antônio Prado/Flores da Cunha apresentou nível inválido e homologação falsa, descartado. Muçum/Encantado usa outro datum e fica a jusante da régua-alvo: 40,85 m não equivale a 40,85 m na régua SGB.',
    '- SGB/SACE: boletins históricos consultados e arquivados. O mais recente encontrado na listagem foi de 14/08/2026, às 22h; não foi usado como previsão vigente para 21/09.', '', '## Leituras utilizadas como base', '', '| Estação | Última observação até a base | Nível na própria régua (m) |', '|---|---|---:|']
    report += [f"| {r['name']} ({r['station']}) | {datetime.fromisoformat(r['time']):%H:%M} | {fmt(r['level_m'],2)} |" for r in observations]
    report += ['', '**14 de Julho às 13h:** afluência 4.534,89 m³/s e defluência 4.212,67 m³/s; às 10h a defluência era 512,86 m³/s. Castro Alves e Monte Claro estão em série com a 14 de Julho: suas vazões não foram somadas como volumes independentes.', '',
    'Como conferência de ordem de grandeza, a telemetria ANA associa 7,46 m em Muçum a 2.127,21 m³/s; pares históricos próximos de 4.200 m³/s correspondem a aproximadamente 11,86 m. Isso é uma associação nível–vazão da própria ANA, não uma medição independente nem uma previsão por balanço de massa. Atenuação, armazenamento, tributários e eventual remanso impedem transportar esse número diretamente para um horário futuro.', '',
    '## Conectividade, distâncias e propagação', '',
    'A rede dirigida da BHO2017/ANA contém 367 trechos a montante do trecho da estação e cerca de 16 mil km² de drenagem. A delimitação inclui a microbacia inteira do trecho de saída (12,8 km²); não substitui um levantamento exato da seção. Distâncias seguem o canal projetado em SIRGAS 2000 / UTM 22S. Alguns pontos de estação exigem encaixe no rio conhecido.', '',
    '**O Guaporé desemboca depois da régua SGB de Muçum.** Sua chuva não foi somada à área contribuinte direta dessa régua. Isso não exclui risco no município ou influência de remanso a jusante; o modelo não resolve hidráulica de remanso.', '',
    '| Origem | Distância no canal | Atraso mediano da onda | P10–P90 entre eventos | Eventos | Velocidade aparente pela mediana |','|---|---:|---:|---:|---:|---:|']
    for r in propagation:
        report.append(f"| {r['source']} | {fmt(r['distance_km'])} km | {fmt(r['median_h'])} h | {fmt(r['p10_h'])}–{fmt(r['p90_h'])} h | {r['events']} | {fmt(r['distance_km']/r['median_h'])} km/h |")
    report += ['', 'Os atrasos foram estimados alinhando ondas em janelas de 37 horas ao redor de cheias ≥7 m, com correlação ≥0,8. P10–P90 descreve a pequena amostra histórica, não limites de viagem. **Carreiro tem identificação fraca pela mistura de afluentes; Cotiporã tem apenas um evento.** A velocidade acima é de propagação aparente da onda, não velocidade medida da água. Não existe aqui tempo exato de chegada de cada gota ou pluviômetro.', '',
    '## Chuva e participação das estações', '',
    'A chuva foi distribuída por cinco regiões usando áreas de influência do sensor mais próximo em grade de 2 km. Um sensor pode representar área dos dois lados de uma divisa: isso é interpolação de chuva, não transferência de vazão entre bacias. Foram usados incrementos ChuvaFinal; o contador acumulado não foi tratado como chuva diária. Lacunas não viraram zero. O peso disponível deve cobrir ≥50% da região; a fração disponível também entra como variável no ajuste.', '',
    '| Região | Área aproximada | Fração do peso com dado recente às 13h | Chuva horária representada |','|---|---:|---:|---:|']
    report += [f"| {r['group']} | {fmt(r['area_km2'],0)} km² | {fmt(100*r['latest_coverage'],0)}% | {fmt(r['latest_mm_h'])} mm |" for r in rain]
    report += ['', 'A fração não mede a porcentagem real da bacia observada sem erro. As janelas dos sensores são assíncronas e podem terminar antes das 13h. Alto Antas e Tainhas têm cobertura mais fraca. Usaram-se chuva acumulada em 1/3/6/12/24h, atrasos de 3/6/12h e chuva antecedente de 48h. Não foi inventado um tempo de infiltração/encosta por pluviômetro.', '',
    'Previsões meteorológicas GFS e ECMWF emitidas com antecedência de 24h foram testadas para chuva futura em 3/6h. Isso permite retrospectiva causal, embora não use a emissão meteorológica mais recente. O ensemble meteorológico atual foi consultado como conferência; não recebeu multiplicador arbitrário para compensar a chuva intensa da manhã.', '',
    '## Calibração e erros verificáveis', '',
    'Seis regressões regularizadas por horizonte combinam níveis e tendências, vazões/afluências das usinas, tributários, chuva por região e históricos distribuídos em atrasos de 0–24h. Uma delas inclui as previsões de chuva. O método é estatístico calibrado; não é um modelo hidráulico completo com seções, rugosidade, balanço de massa e manobras futuras de comportas.', '',
    'Treino inicial: abril–setembro/2025. Seleção: outubro/2025–junho/2026. Teste temporal: julho–20/setembro/2026. O ajuste final usa alvos observados antes de 21/setembro. Os pesos entre modelos usam somente erros cujos horários-alvo já passaram, com memória exponencial. Hiperparâmetros foram escolhidos na validação. Os arquivos guardam cada previsão retrospectiva e seu erro.', '',
    'A avaliação usa arquivos históricos hoje disponíveis, sujeitos a revisões. Não reconstrói o instante exato de publicação de cada mensagem antiga; portanto não prova o mesmo desempenho em operação ao vivo. A amostra de cheias é pequena e os dados do teste foram vistos durante o desenvolvimento desta análise.', '',
    '| Antecedência | MAE teste temporal | MAE teste com nível ≥9 m | MAE desta manhã | P90 erro absoluto desta manhã |','|---|---:|---:|---:|---:|']
    for r,e in zip(rows,doc['evaluation']):report.append(f"| {r['h']} h | {fmt(e['mae_m'],2)} m | {fmt(e['high_water_mae_m'],2)} m | {fmt(r['today_mae_m'],2)} m | {fmt(r['today_p90_abs_m'],2)} m |")
    report += ['', 'Na comparação nas mesmas 1.357 origens do teste de 6h, a combinação teve MAE de 0,18 m, contra 0,62 m da persistência e 0,73 m da extrapolação da tendência de 2h. **Nas oito origens já verificáveis desta manhã, a persistência teve MAE de 1,52 m, ligeiramente melhor que os 1,63 m da combinação; a tendência teve 2,30 m.** O maior erro de 6h da combinação hoje foi 3,43 m. Portanto, o ganho histórico não se traduziu em superioridade demonstrada no evento atual.', '', '**A evidência atual não sustenta prometer alta precisão nas seis horas.** O erro de 6h desta manhã é muito maior que o erro médio histórico. A faixa foi ampliada por esse motivo, e não deve ser interpretada como segurança abaixo do extremo superior. Chuvas novas, falhas de telemetria, remanso e operação das usinas podem mudar a evolução.', '',
    '## Arquivos e reprodução', '',
    '- `mucum-previsao-6h.png`: gráfico com a ressalva incorporada à imagem.',
    '- `previsao-final.csv` e `previsao-combinada.json`: números, pesos e erros.',
    '- `pluviometros-estrutura-completa.csv`: cada ID, nome, coordenadas, subbacia, canal, distância, papel no modelo e pesos da chuva.',
    '- `ondas-calibradas.csv`: eventos usados para estimar propagação; `observacoes-base.csv`: idade da telemetria.',
    '- `teste-combinado.csv`, `comparacao-referencias.csv`: retrospectivas e comparação com persistência/tendência.',
    '- `verificacao-final.json`: verificações de causalidade, pesos, horário e base observada.',
    '- Scripts locais: `hydro_extended_collect.py` → `hydro_routing_data.py` → `hydro_forecast.py` → `hydro_adaptive_ensemble.py` → `hydro_supporting_checks.py` → `hydro_final_report.py`.', '',
    'As estimativas anteriores nas outras pastas ficam preservadas para auditoria; esta edição de base 13h é a versão consolidada deste trabalho. Nenhum alerta foi enviado e nenhum site foi publicado.', '',
    '## Fontes primárias', '',
    '- [ANA — serviço de telemetria](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx). Método DadosHidrometeorologicosGerais; códigos e períodos nos arquivos raw.',
    '- [ONS — dados hidráulicos horários](https://dados.ons.org.br/dataset/dados_hidrologicos_ho).',
    '- [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php).',
    '- [Defesa Civil RS — rede hidrometeorológica](https://redehidrometeorologica.defesacivil.rs.gov.br/Mapa).',
    '- [SGB — boletins da bacia do Taquari](https://www.sgb.gov.br/sace/boletins.php?idbacia=9).',
    '- [SGB — pesquisa sobre tempo de propagação das cheias](https://rigeo.sgb.gov.br/handle/doc/25757).',
    '- [Open-Meteo — arquivo de previsões anteriores](https://open-meteo.com/en/docs/previous-runs-api).', '',
    '**Para comunicação pública:** compartilhar junto o horário-base, a faixa de erro e a identificação de previsão independente. As orientações oficiais de proteção e evacuação têm prioridade; este produto não determina locais seguros no município.']
    (OUT/'relatorio.md').write_text('\n'.join(report)+'\n')
    print(json.dumps({'checks':audit,'forecast_rows':len(rows),'baseline_comparison':stats[-6:]},ensure_ascii=False,indent=2))

if __name__=='__main__':run()
