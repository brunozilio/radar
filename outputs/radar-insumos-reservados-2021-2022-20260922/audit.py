"""Offline ALL-QC reserved ANA catalog. No features, targets, models or errors."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import defaultdict,Counter
import json,csv,math,hashlib,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1];plan=json.loads((P/'collection-plan.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def num(v):
 try:x=float(v)
 except (ValueError,TypeError):return None
 return x if math.isfinite(x) else None
def runs(times,step):
 out=[]
 for t in sorted(times):
  if out and t-out[-1][1]==timedelta(seconds=step):out[-1][1]=t;out[-1][2]+=1
  else:out.append([t,t,1])
 return [dict(first=str(a),last=str(b),slots=n) for a,b,n in out]
def original(r):return {k:v for k,v in r.items() if not k.startswith('source_')}
def ref(r):return {k:r[k] for k in ('source_file','source_sha256','source_record_index')}
def writejsonl(p,rr):
 with p.open('w') as f:
  for r in rr:f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')

sources=[];by_station=defaultdict(list);outside=[];raw_by_source={};anomalies=[]
for r in plan['reused']:
 m=dict(r['source_metadata']);m.update(source_file=r['source_file'],sha256=r['sha256'],year=r['year'],usage='primary_reuse');sources.append(m)
for j in plan['new_jobs']:
 side=(P/j['file']).with_suffix('.source.json');assert side.exists(),'Collection incomplete: '+str(side);m=json.loads(side.read_text());m['usage']='primary_new';sources.append(m)
for m in sources:
 m['audit_status']='request_failed_or_incomplete';m['record_count']=0;m['retained_record_count']=0
 if 'source_file' not in m:continue
 f=ROOT/m['source_file'];assert sha(f)==m['sha256']
 try:tree=ET.parse(f).getroot()
 except ET.ParseError as e:m.update(audit_status='invalid_xml',parse_error=str(e));continue
 errors=[e.text for e in tree.iter() if e.tag.split('}')[-1]=='Error'];m['source_errors']=errors
 rows=[{c.tag.split('}')[-1]:c.text for c in e} for e in tree.iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos'];raw_by_source[m['source_file']]=rows;m['record_count']=len(rows)
 m['audit_status']='http_error' if m.get('http_status')!=200 else 'parsed' if rows else 'no_data_api' if any('sem dados' in str(x).lower() for x in errors) else 'other_api_error' if errors else 'empty_xml'
 for idx,r in enumerate(rows,1):
  row={**r,'source_file':m['source_file'],'source_sha256':m['sha256'],'source_record_index':idx}
  try:t=datetime.fromisoformat(r['DataHora'])
  except (ValueError,KeyError,TypeError) as e:anomalies.append(dict(source_record=row,error='timestamp_unparseable'));continue
  if r.get('CodEstacao')!=m['station'] or t.tzinfo is not None:anomalies.append(dict(source_record=row,error='station_or_timezone_contract_unexpected'));continue
  if not m['start']<=t.date().isoformat()<=m['end']:outside.append(row);continue
  by_station[(m['year'],m['station'])].append(row);m['retained_record_count']+=1

# Probe is audit-only: preserve disagreement without changing the primary monthly data.
ov=plan['overlap_audit'];f=ROOT/ov['source_file'];assert sha(f)==ov['sha256'];prows=[{c.tag.split('}')[-1]:c.text for c in e} for e in ET.parse(f).iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos'];monthly=defaultdict(list)
for r in by_station[(2022,'86510000')]:monthly[r['DataHora']].append(r)
probe_audit=[]
for idx,r in enumerate(prows,1):
 matches=monthly[r['DataHora']];same=any(original(x)==r for x in matches)
 probe_audit.append(dict(timestamp_literal=r['DataHora'],probe_source_file=ov['source_file'],probe_source_sha256=ov['sha256'],probe_source_record_index=idx,monthly_matches=len(matches),all_fields_identical=same,probe_fields=r if not same else None,monthly_records=matches if not same else None))
dump(P/'probe-overlap-audit.json',dict(source=ov,records=len(prows),identical=sum(r['all_fields_identical'] for r in probe_audit),mismatching_or_missing=sum(not r['all_fields_identical'] for r in probe_audit),comparisons=probe_audit,policy='Audit only; not appended or used to revise monthly primary records.'))

summaries=[];duplicates=[];conflicts=[];daily=[];field_table=[];samples=[];field_names=['ChuvaAcumAdotada','ChuvaFinal','NivelSensor','NivelDisplay','NivelManual','NivelFinal','VazaoFinal']
for year in (2021,2022):
 lo=datetime(year,4,28);hi=datetime(year,6 if year==2021 else 7,1);folder=P/'stations'/str(year);folder.mkdir(parents=True,exist_ok=True)
 for code in plan['stations']:
  raw=by_station[(year,code)];groups=defaultdict(list)
  for r in raw:groups[r['DataHora']].append(r)
  ordered=[];uncertain=set()
  for t,rr in sorted(groups.items()):
   versions={}
   for r in rr:
    key=json.dumps(original(r),sort_keys=True,ensure_ascii=False)
    if key not in versions:versions[key]={**r,'source_references':[ref(r)]}
    else:versions[key]['source_references'].append(ref(r))
   if len(rr)>1:duplicates.append(dict(year=year,station=code,time_literal=t,raw_occurrences=len(rr),distinct_versions=len(versions),all_fields_identical=len(versions)==1,sources=[ref(r) for r in rr]))
   if len(versions)>1:uncertain.add(t);conflicts.append(dict(year=year,station=code,time_literal=t,versions=list(versions.values())))
   ordered.extend(versions.values())
  writejsonl(folder/f'ana-{code}-all-qc.jsonl',ordered)
  tt=sorted(datetime.fromisoformat(t) for t in groups);diffs=Counter(int((b-a).total_seconds()) for a,b in zip(tt,tt[1:]));mode=diffs.most_common(1)[0][0] if diffs else None
  stable={datetime.fromisoformat(t):rr[0] for t,rr in groups.items() if t not in uncertain};s=dict(year=year,station=code,raw_records=len(raw),normalized_rows=len(ordered),unique_timestamps=len(tt),identical_extra_records=len(raw)-len(ordered),conflicting_timestamps=len(uncertain),first_literal=str(tt[0]) if tt else None,last_literal=str(tt[-1]) if tt else None,source_status_counts=dict(Counter(m['audit_status'] for m in sources if m['year']==year and m['station']==code)),delta_seconds_counts=dict(sorted(diffs.items())),modal_cadence_seconds=mode,minute_counts=dict(Counter(t.minute for t in tt)),second_counts=dict(Counter(t.second for t in tt)),fields={},grids={})
  for step,label in [(900,'exact_15min'),(3600,'exact_hour')]:
   grid={lo+timedelta(seconds=step*i) for i in range(int((hi-lo).total_seconds())//step)};timestamps=set(tt);g=dict(expected=len(grid),timestamp_present=len(grid&timestamps),timestamp_absent=len(grid-timestamps),off_grid_records=len(timestamps-grid),fields={})
   for field in field_names:
    good={t for t,r in stable.items() if num(r.get(field)) is not None and r.get('CQ_'+field)=='Dado aprovado'};g['fields'][field]=dict(approved_numeric=len(good&grid),unavailable_or_not_approved=len(grid-good))
   s['grids'][label]=g
  if mode and mode>0:
   phase=Counter(int((t-lo).total_seconds())%mode for t in tt).most_common(1)[0][0];expected=[lo+timedelta(seconds=phase+i*mode) for i in range(math.ceil(((hi-lo).total_seconds()-phase)/mode))];expected=[t for t in expected if lo<=t<hi];ts=set(tt);missing=[t for t in expected if t not in ts]
   s['modal_grid']=dict(step_seconds=mode,phase_seconds=phase,expected=len(expected),present=len(expected)-len(missing),absent=len(missing),off_modal_grid=len(ts-set(expected)),absent_intervals=runs(missing,mode),interpretation='Descriptive grid only; not a timestamp correction or universal station cadence contract.')
   s['long_interrecord_gaps']=[dict(before=str(a),after=str(b),gap_seconds=int((b-a).total_seconds())) for a,b in zip(tt,tt[1:]) if (b-a).total_seconds()>mode]
  for field in field_names:
   vals=[(r,r.get(field),r.get('CQ_'+field)) for r in ordered];numeric=[(r,num(v),q) for r,v,q in vals if num(v) is not None];approved=[r for r,v,q in numeric if q=='Dado aprovado' and r['DataHora'] not in uncertain]
   st=dict(year=year,station=code,field=field,rows=len(ordered),field_absent=sum(field not in r for r,_,_ in vals),empty_values=sum(v in (None,'') for _,v,_ in vals),nonempty_nonnumeric_or_nonfinite=sum(v not in (None,'') and num(v) is None for _,v,_ in vals),numeric=len(numeric),approved_numeric=len(approved),suspect_numeric=sum(q=='Dado suspeito' for _,_,q in numeric),numeric_missing_qc=sum(q in (None,'') for _,_,q in numeric),numeric_other_qc=sum(q not in (None,'','Dado aprovado','Dado suspeito') for _,_,q in numeric),negative_numeric=sum(v<0 for _,v,_ in numeric),zero_numeric=sum(v==0 for _,v,_ in numeric),qc_counts=dict(Counter(str(q) for _,_,q in vals)))
   if mode:
    bad=[t for t,r in stable.items() if num(r.get(field)) is None or r.get('CQ_'+field)!='Dado aprovado'];st['observed_unavailable_or_not_approved_runs']=runs(bad,mode)
   s['fields'][field]=st;field_table.append({k:v for k,v in st.items() if not isinstance(v,(dict,list))})
   for qc in sorted({str(q) for _,_,q in vals}):
    r=next(r for r,_,q in vals if str(q)==qc);samples.append(dict(year=year,station=code,field=field,qc=qc,sample=r))
  for i in range((hi-lo).days):
   d=lo+timedelta(days=i);subset={t:r for t,r in stable.items() if d<=t<d+timedelta(days=1)};dr=dict(year=year,station=code,date=d.date().isoformat(),unambiguous_records=len(subset),records_exact_hour=sum(t.minute==t.second==t.microsecond==0 for t in subset),records_exact_15min=sum(t.minute%15==t.second==t.microsecond==0 for t in subset))
   for field in ('NivelFinal','VazaoFinal','ChuvaFinal'):
    good=[t for t,r in subset.items() if num(r.get(field)) is not None and r.get('CQ_'+field)=='Dado aprovado'];dr[field+'_approved']=len(good);dr[field+'_approved_exact_hour']=sum(t.minute==t.second==t.microsecond==0 for t in good)
   daily.append(dr)
  summaries.append(s);print(year,code,len(raw),'H',s['fields']['NivelFinal']['approved_numeric'],'P',s['fields']['ChuvaFinal']['approved_numeric'],'cadence',mode,flush=True)

dump(P/'source-manifest.json',sources);dump(P/'duplicate-audit.json',dict(duplicate_groups=duplicates,conflicts=conflicts,identical_extra_records=sum(s['identical_extra_records'] for s in summaries),conflicting_timestamps=len(conflicts),policy='Canonical rows include every distinct field version. Identical occurrences grouped with source_references; no conflicting version automatically selected. Probe separate.'));writejsonl(P/'out-of-request-window.jsonl',outside);dump(P/'record-contract-anomalies.json',anomalies);dump(P/'qc-samples.json',samples)
for name,rr in [('field-summary.csv',field_table),('daily-coverage.csv',daily)]:
 with (P/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
result=dict(audited_at_utc=datetime.now(timezone.utc).isoformat(),scope='Reserved inputs coverage/QC only; no models/features/inference/errors/selection.',new_get_attempts=len(plan['new_jobs']),primary_reused_XMLs=len(plan['reused']),probe_audit_only_XMLs=1,primary_source_statuses=dict(Counter(m['audit_status'] for m in sources)),all_primary_raw_records=sum(m['record_count'] for m in sources),retained_raw_records=sum(s['raw_records'] for s in summaries),normalized_rows=sum(s['normalized_rows'] for s in summaries),out_of_request_window=len(outside),record_contract_anomalies=len(anomalies),stations=summaries,limits=['DataHora strings remain literal naive local times; timezone and gauge datum not certified.','No record publication/receipt-time history; sources may contain retrospective revisions.','Source QC approved does not certify physical truth; suspect/negative/raw missing values preserved.','Exact15min absence is not automatically failure for hourly stations; modal cadence is descriptive.','Conflicting versions retained, no automatic preference. No interpolation/rounding/zero fill/unit conversion.','2021/2022 remain reserved from fitting/tuning/model selection; collection does not constitute evaluation.'])
dump(P/'coverage.json',result)
for path,h in plan['reference_sha256'].items():assert sha(ROOT/path)==h
lines=['# Acervo observado ANA — reservas de 2021 e 2022','','27 postos do mapa e das latências congeladas. Janelas 28/04–31/05/2021 e 28/04–30/06/2022; 28–30/04 são aquecimento. Somente coleta e cobertura/QC; nenhum modelo, matriz, previsão, erro ou ajuste foi executado. As janelas permanecem reservadas.','',f"125 novos GETs planejados (limite125), no máximo duas conexões, sem retry ou redirecionamento automático. Dez XMLs anteriores reutilizados; um probe de 2022 comparado somente como auditoria, sem entrar nas séries. Status primários: {result['primary_source_statuses']}.",'',f"{result['retained_raw_records']} registros brutos retidos, {result['normalized_rows']} linhas ALL-QC, {len(conflicts)} timestamps conflitantes. Cada registro mantém campos originais no topo e source_file/source_sha256/source_record_index (índice XML1-based), além de source_references. Valores/unidades/textos permanecem literais. Respostas sem dados e falhas são distinguidas no source-manifest.",'','| Ano | Posto | Timestamps | Cadência modal(s) | Nível aprovado | Chuva aprovada | Chuva vazia |','|---|---|---:|---:|---:|---:|---:|']
for s in summaries:lines.append(f"| {s['year']} | {s['station']} | {s['unique_timestamps']} | {s['modal_cadence_seconds']} | {s['fields']['NivelFinal']['approved_numeric']} | {s['fields']['ChuvaFinal']['approved_numeric']} | {s['fields']['ChuvaFinal']['empty_values']} |")
lines+=['','`coverage.json` inclui contagens nas grades exatas hora/15min, cadências/segundos literais, gaps e todos os campos/QC. `daily-coverage.csv` e `field-summary.csv` permitem inspeção tabular. A grade de15min não é denominador de completude universal para postos horários. `duplicate-audit.json` preserva conflitos sem escolher versões. `probe-overlap-audit.json` distingue revisões/divergências de outra consulta.','','Ausências, valores suspeitos, negativos e sem QC não foram corrigidos, interpolados, arredondados nem preenchidos com zero. A presença de timestamp não significa que o campo desejado esteja preenchido. A coleta não certifica fuso, datum, vigência da régua ou disponibilidade operacional passada. Não houve inferência sobre as reservas.']
lines += ['', 'Lacunas principais: sem qualquer série em ambos os anos: 86125000, 86472600 (Santa Tereza), 86500000 (Carreiro), 86504900; 86125050 também sem série em 2021. ChuvaFinal inteiramente vazia apesar de registros: 86200900 e 86493000 nos dois anos; 86298000 em 2021; 86479000 e 86495500 em 2022. Não confundir essa ausência de campo com falha de rede: todos os 125 novos GETs retornaram HTTP200.', '', 'Linha 86472000: NivelFinal totalmente vazio em 2021; em 2022, 3.109 níveis aprovados, dois suspeitos, um reprovado e 3.032 vazios. Muçum: 3.264 níveis aprovados em 2021; 6.136 aprovados e oito vazios em 2022. Estes totais incluem o aquecimento. Nenhum nível alternativo substitui NivelFinal.', '', 'Sinais numéricos preservados sem correção: 722 NivelFinal negativos aprovados na fonte 86479000/2022; uma VazaoFinal negativa na fonte 86448000/2021. numeric-qc-flags.jsonl enumera sinais negativos e QC numérico não aprovado em todos os campos, com registro/proveniência integral. Isto não é uma declaração de invalidade física oficial.', '', '2021 contém 25.061 registros e 21.736 valores ChuvaFinal aprovados; 2022 contém 48.345 registros e 42.304 valores de chuva aprovados. O probe reaproveitado coincide em todos os 96 registros com a série mensal e não duplica a série canônica.']
(P/'README.md').write_text('\n'.join(lines)+'\n')
dump(P/'artifact-hashes.json',[dict(file=str(f.relative_to(P)),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact-hashes.json'])
