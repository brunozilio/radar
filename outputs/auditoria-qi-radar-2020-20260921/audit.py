"""Literal ONS source and lag audit, no repairs, masks, feature matrix or fit."""
import csv,hashlib,json,math,bisect
from pathlib import Path
from datetime import datetime,timedelta
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
IDS={'JIUHQJ':'14 DE JULHO','JIUHMC':'MONTE CLARO','JIUHCA':'CASTRO ALVES'}
FIELDS=['val_vazaodefluente','val_vazaoafluente','val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def num(s):
 try:v=float(s)
 except (ValueError,TypeError):return None
 return v if math.isfinite(v) else None
def save(name,rows,fields=None):
 with (P/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def dump(name,d):(P/name).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
meta=json.loads((P/'raw/ons-2020-06.source.json').read_text());assert meta['status']=='response_preserved' and meta['http_status']==200
raw=P/meta['file'];assert sha(raw)==meta['sha256']
with raw.open(encoding='utf-8-sig') as f:
 reader=csv.DictReader(f,delimiter=';');fields=reader.fieldnames
 june=[]
 for line,r in enumerate(reader,2):
  if r['id_reservatorio'] in IDS:june.append(dict(r,source_file=str(raw.relative_to(ROOT)),source_record_index=line-2))
assert len(june)>0
save('ceran-2020-06-source-values.csv',june,fields+['source_file','source_record_index'])
july=ROOT/'outputs/historico-vazoes-ceran/ceran-2020-07-source-values.csv'
prior=ROOT/'outputs/viabilidade-historico-antigo-radar-20260921'
for r in json.loads((prior/'artifact-hashes.json').read_text()):assert sha(prior/r['file'])==r['sha256']
expected=json.loads((prior/'audit.json').read_text())['input_sha256'][str(july.relative_to(ROOT))];assert sha(july)==expected
oldroot=ROOT/'outputs/historico-vazoes-ceran'
oldmeta=next(r for r in json.loads((oldroot/'source-manifest.json').read_text()) if r['file']=='raw/ons-2020-07.parquet')
assert sha(oldroot/oldmeta['file'])==oldmeta['sha256']
oldrows=[dict(r,source_file=str(july.relative_to(ROOT)),source_record_index=i) for i,r in enumerate(csv.DictReader(july.open()))]
source=june+oldrows
assert all(r['nom_reservatorio']==IDS[r['id_reservatorio']] for r in source)
assert len({(r['id_reservatorio'],r['din_instante']) for r in source})==len(source)
index={code:sorted([r for r in source if r['id_reservatorio']==code],key=lambda r:r['din_instante']) for code in IDS}
times={code:[datetime.fromisoformat(r['din_instante']) for r in rr] for code,rr in index.items()}
def flags(r):
 q,i,t,v,o=(num(r[k]) for k in FIELDS);complete=all(x is not None for x in (t,v,o));cs=t+v+o if complete else None
 return dict(q_zero=q==0,i_zero=i==0,q_zero_positive_components=q==0 and cs is not None and cs>1,
   balance_residual_gt1=q is not None and cs is not None and abs(q-cs)>1,
   component_sum_m3s=cs,balance_residual_m3s=q-cs if q is not None and cs is not None else None)
flagrows=[dict(r,**flags(r)) for r in source if any(flags(r)[k] for k in ('q_zero','i_zero','q_zero_positive_components','balance_residual_gt1'))]
save('source-diagnostics.csv',flagrows,list(source[0])+list(flags(source[0])))
summaries=[]
for month in ('2020-06','2020-07'):
 for code in IDS:
  rr=[r for r in index[code] if r['din_instante'].startswith(month)]
  summaries.append(dict(month=month,plant=code,rows=len(rr),literal_2359=sum(r['din_instante'][11:16]=='23:59' for r in rr),
    Q_finite=sum(num(r[FIELDS[0]]) is not None for r in rr),I_finite=sum(num(r[FIELDS[1]]) is not None for r in rr),
    Q_zero=sum(flags(r)['q_zero'] for r in rr),I_zero=sum(flags(r)['i_zero'] for r in rr),
    Q_zero_positive_components=sum(flags(r)['q_zero_positive_components'] for r in rr),
    balance_residual_gt1=sum(flags(r)['balance_residual_gt1'] for r in rr)))
save('source-summary.csv',summaries)
origins=[datetime(2020,7,1)+timedelta(hours=h) for h in range(480)]
trace=[];originrows=[]
for origin in origins:
 current=[]
 for code in IDS:
  for kind,back in [('Q',0),('Q',1),('Q',2),('Q',4),('Q',8),('I',0)]:
   query=origin-timedelta(hours=1+back);j=bisect.bisect_right(times[code],query)-1
   r=index[code][j] if j>=0 else None;age=(query-times[code][j]).total_seconds() if r else None
   value=num(r['val_vazaodefluente' if kind=='Q' else 'val_vazaoafluente']) if r else None
   usable=r is not None and age<=5400 and value is not None
   f=flags(r) if r else {}
   row=dict(origin=origin.isoformat()+'-03:00',plant=code,variable=kind,back_hours=back,
    query_naive=query.isoformat(),source_time_naive=r['din_instante'] if r else None,age_seconds=age,
    value_m3s=value if usable else None,usable=usable,zero=usable and value==0,
    Q_zero_positive_components=bool(usable and kind=='Q' and f.get('q_zero_positive_components')),
    balance_residual_gt1=bool(usable and kind=='Q' and f.get('balance_residual_gt1')),
    source_file=r['source_file'] if r else None,source_record_index=r['source_record_index'] if r else None)
   trace.append(row);current.append(row)
 originrows.append(dict(origin=origin.isoformat()+'-03:00',all_18_lookups_available=all(r['usable'] for r in current),
    uses_any_zero=any(r['zero'] for r in current),uses_Q_zero_positive_components=any(r['Q_zero_positive_components'] for r in current),
    uses_Q_balance_residual_gt1=any(r['balance_residual_gt1'] for r in current)))
save('lag-source-trace.csv',trace);save('origin-diagnostics.csv',originrows)
extreme=[r for r in csv.DictReader((prior/'potential-pairs.csv').open()) if r['window'].startswith('2020') and r['horizon_h']=='12' and r['response_m'] and float(r['response_m'])>8.09]
exorig={r['origin'] for r in extreme};selected=[r for r in originrows if r['origin'] in exorig];assert len(selected)==9
save('extreme-origin-diagnostics.csv',selected)
refs=[dict(month='2020-06',literal_csv=str((P/'ceran-2020-06-source-values.csv').relative_to(ROOT)),csv_sha256=sha(P/'ceran-2020-06-source-values.csv'),raw_source_path=str(raw.relative_to(ROOT)),raw_source_sha256=sha(raw),raw_source_url=meta['url'],new_request=True),
 dict(month='2020-07',literal_csv=str(july.relative_to(ROOT)),csv_sha256=sha(july),raw_source_path=str((oldroot/oldmeta['file']).relative_to(ROOT)),raw_source_sha256=oldmeta['sha256'],raw_source_url=oldmeta['url'],new_request=False)]
dump('ons-references.json',refs)
result=dict(months=summaries,rows=len(source),scheduled_origins=480,lag_lookups=len(trace),
 source_rows_flagged=len(flagrows),origins_all_lookups_available=sum(r['all_18_lookups_available'] for r in originrows),
 origins_with_any_zero=sum(r['uses_any_zero'] for r in originrows),
 origins_with_Q_zero_positive_components=sum(r['uses_Q_zero_positive_components'] for r in originrows),
 origins_with_Q_balance_residual_gt1=sum(r['uses_Q_balance_residual_gt1'] for r in originrows),
 extreme_origins=selected,seconds_delay=3600,max_age_after_query_seconds=5400,
 timestamp_policy='Literal din_instante, including23:59. AssumedUTC-3 for origin labels only; no rounding or exporter certification.',
 flags_policy='Diagnostics only; source values unchanged, no rejection mask, no filling or component substitution.',
 reused_july_csv_verification='Hash equals frozen prior feasibility audit. Parquet hash matches retrieval manifest; Parquet not redecoded in this audit.',
 trained=False,promoted=False,goal_achieved=False)
dump('audit.json',result)
lines=['# Vazões ONS2020: valores literais e efeito nos atrasos RADAR','',
 'Uma consulta pública trouxe junho de2020 para aquecimento; julho foi reutilizado com hashes verificados. Somente14 deJulho, MonteClaro eCastroAlves foram extraídas. Não houve treino, correção de valores ou troca de componentes.','',
 '| Mês | Usina | Linhas | Q/I finitos | Qzero | Izero | Qzero com componentes>1 | Resíduo>1 |',
 '|---|---|---:|---:|---:|---:|---:|---:|']
for s in summaries:lines.append(f"| {s['month']} | {s['plant']} | {s['rows']} | {s['Q_finite']}/{s['I_finite']} | {s['Q_zero']} | {s['I_zero']} | {s['Q_zero_positive_components']} | {s['balance_residual_gt1']} |")
lines+=['',f"Foram rastreadas{len(trace)} consultas (18 por origem: Qcorrente e recuos1/2/4/8h, Icorrente, três usinas) nas480 origens de01–20/07. {result['origins_all_lookups_available']} têm todos os valores disponíveis sob atraso60min e idade90min após consulta. {result['origins_with_any_zero']} usam algum zero;{result['origins_with_Q_zero_positive_components']} usam Qzero com soma positiva de componentes;{result['origins_with_Q_balance_residual_gt1']} usam Qcom resíduo absoluto>1m³/s. As categorias se sobrepõem e não são rótulos oficiais de erro.", '',
 f"Nas nove origens extremas previamente identificadas, {sum(r['all_18_lookups_available'] for r in selected)}/9 têm todas as consultas e {sum(r['uses_any_zero'] for r in selected)}/9 usam algum zero. São origens de desenvolvimento previamente examinadas, não nove cheias independentes.", '',
 'Os zeros não foram trocados por valores estimados, componentes ouNaN. MonteClaro pode apresentar componentes tambémzero: consistência aritmética não comprova correção física. Afluência é outra grandeza; nenhuma checagem de soma de defluência a valida. O limiar1m³/s é diagnóstico congelado, não tolerância oficial.', '',
 'Junho foi extraído diretamente do CSVsemicolon com preservação dos campos textuais, linha e arquivo de origem. Julho preserva o CSVliteral da auditoria anterior e o hash doParquet; não foi redecodificado neste passo. Timestamps23:59 permanecem23:59; a auditoria não usa a coluna interpretada24h. Publicação histórica, revisão, fuso/exportador, datum e equivalência de regime continuam pendentes.', '',
 'ons-references.json serve para uma futura matriz, cujo protocolo deve declarar explicitamente como trata esses diagnósticos. A presente auditoria não aprovou todas as linhas para treino, não alterou máscaras e não acessou2021/2022reservados.']
(P/'README.md').write_text('\n'.join(lines)+'\n')
dump('artifact-hashes.json',[dict(file=str(p.relative_to(P)),sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps({k:v for k,v in result.items() if k not in ('months','extreme_origins')},indent=2))
