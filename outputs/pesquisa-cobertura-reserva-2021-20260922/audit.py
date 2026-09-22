"""Offline coverage/QC only: never read predictions/models or compute errors."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter,defaultdict
import json,csv,hashlib,math,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1];LO=datetime(2021,4,28);HI=datetime(2021,6,1);plan=json.loads((P/'collection-plan.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def numeric(x):
 try:v=float(x)
 except (ValueError,TypeError):return None
 return v if math.isfinite(v) else None
def gaps(tt,step):
 gs=[]
 for t in sorted(tt):
  if gs and t-gs[-1][-1]==timedelta(seconds=step):gs[-1].append(t)
  else:gs.append([t])
 return [{'first':str(g[0]),'last':str(g[-1]),'slots':len(g)} for g in gs]
records=defaultdict(list);sources=[];duplicates=[];conflicts=[];summary=[];daily=[];samples=[]
for j in plan['jobs']:
 m=json.loads((P/j['file']).with_suffix('.source.json').read_text());sources.append(m)
 if m['status']!='response_preserved':m['audit_status']='request_failed';continue
 f=ROOT/m['source_file'];assert sha(f)==m['sha256'];b=f.read_bytes()
 try:tree=ET.fromstring(b)
 except ET.ParseError as e:m['audit_status']='invalid_xml';m['parse_error']=str(e);continue
 errors=[e.text for e in tree.iter() if e.tag.split('}')[-1]=='Error'];m['source_errors']=errors
 rows=[{c.tag.split('}')[-1]:c.text for c in e} for e in tree.iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos'];m['audit_status']='parsed' if rows else 'no_data_api' if errors else 'empty_response';m['record_count']=len(rows)
 for idx,r in enumerate(rows,1):
  t=datetime.fromisoformat(r['DataHora']);assert t.tzinfo is None and LO<=t<HI and j['start']<=t.date().isoformat()<=j['end'] and r['CodEstacao']==j['station']
  records[j['station']].append({'fields':r,'source_file':m['source_file'],'source_sha256':m['sha256'],'source_record_index':idx})
(P/'stations').mkdir(exist_ok=True)
for code in ('86510000','86472000'):
 rr=records[code];rr.sort(key=lambda r:r['fields']['DataHora']);bytime=defaultdict(list)
 with (P/'stations'/f'ana-{code}-all-qc.jsonl').open('w') as f:
  for r in rr:f.write(json.dumps(r,ensure_ascii=False)+'\n');bytime[r['fields']['DataHora']].append(r)
 for t,rs in bytime.items():
  if len(rs)>1:
   same=all(r['fields']==rs[0]['fields'] for r in rs);item={'station':code,'timestamp_literal':t,'occurrences':len(rs),'identical_all_fields':same,'records':rs};duplicates.append(item)
   if not same:conflicts.append(item)
 # Coverage reports a timestamp only once; conflicting timestamps never counted approved.
 unique={datetime.fromisoformat(t):rs[0]['fields'] for t,rs in bytime.items()};ambiguous={datetime.fromisoformat(r['timestamp_literal']) for r in conflicts if r['station']==code};tt=sorted(unique)
 fields=sorted({k for r in unique.values() for k in r if k not in ('CodEstacao','DataHora') and not k.startswith('CQ_')})
 item={'station':code,'raw_records':len(rr),'unique_timestamps':len(tt),'duplicate_extra_records':len(rr)-len(tt),'conflicting_timestamps':len(ambiguous),'first_literal':str(tt[0]) if tt else None,'last_literal':str(tt[-1]) if tt else None,'cadence_seconds_counts':dict(Counter(int((b-a).total_seconds()) for a,b in zip(tt,tt[1:]))),'minute_counts':dict(Counter(t.minute for t in tt)),'second_counts':dict(Counter(t.second for t in tt)),'fields':{},'windows':{}}
 for field in fields:
  vals=[(t,r.get(field),r.get('CQ_'+field)) for t,r in unique.items()];approved=[t for t,v,q in vals if numeric(v) is not None and q=='Dado aprovado' and t not in ambiguous]
  item['fields'][field]={'qc_counts':dict(Counter(str(q) for _,_,q in vals)),'empty_values':sum(v in (None,'') for _,v,_ in vals),'nonempty_nonfinite_or_nonnumeric':sum(v not in (None,'') and numeric(v) is None for _,v,_ in vals),'numeric':sum(numeric(v) is not None for _,v,_ in vals),'approved_numeric':len(approved),'suspect_numeric':sum(numeric(v) is not None and q=='Dado suspeito' for _,v,q in vals),'numeric_without_qc':sum(numeric(v) is not None and q in (None,'') for _,v,q in vals),'zero_numeric':sum(numeric(v)==0 for _,v,_ in vals),'negative_numeric':sum(numeric(v) is not None and numeric(v)<0 for _,v,_ in vals),'approved_exact_hour':sum(t.minute==t.second==t.microsecond==0 for t in approved),'approved_exact_quarter_hour':sum(t.minute%15==t.second==t.microsecond==0 for t in approved)}
  for qc in sorted({str(q) for _,_,q in vals}):
   sample=next((r for r in rr if str(r['fields'].get('CQ_'+field))==qc),None)
   if sample:samples.append({'station':code,'field':field,'qc':qc,'sample_record':sample})
 for label,lo,hi in [('all',LO,HI),('warmup',LO,datetime(2021,5,1)),('reserved_may',datetime(2021,5,1),HI)]:
  win={t:r for t,r in unique.items() if lo<=t<hi};stats={'records':len(win),'grids':{}}
  for step,name in [(900,'exact_15min'),(3600,'exact_hour')]:
   grid=[lo+timedelta(seconds=i*step) for i in range(int((hi-lo).total_seconds())//step)];gridset=set(grid);missing=[t for t in grid if t not in win]
   g={'expected':len(grid),'records_present':len(grid)-len(missing),'records_absent':len(missing),'off_grid_records':sum(t not in gridset for t in win),'absent_intervals':gaps(missing,step),'fields':{}}
   for field in ('NivelFinal','VazaoFinal','ChuvaFinal'):
    good={t for t,r in win.items() if numeric(r.get(field)) is not None and r.get('CQ_'+field)=='Dado aprovado' and t not in ambiguous};bad=[t for t in grid if t not in good]
    g['fields'][field]={'approved_numeric':len(gridset&good),'unavailable_or_not_approved':len(bad),'unavailable_or_not_approved_intervals':gaps(bad,step)}
   stats['grids'][name]=g
  item['windows'][label]=stats
 for i in range((HI-LO).days):
  day=LO+timedelta(days=i);subset={t:r for t,r in unique.items() if day<=t<day+timedelta(days=1)}
  dr={'station':code,'date':day.date().isoformat(),'records':len(subset),'records_exact_hour':sum(t.minute==t.second==0 for t in subset),'records_exact_15min':sum(t.minute%15==t.second==0 for t in subset)}
  for field in ('NivelFinal','VazaoFinal','ChuvaFinal'):
   good=[t for t,r in subset.items() if numeric(r.get(field)) is not None and r.get('CQ_'+field)=='Dado aprovado' and t not in ambiguous];dr[field+'_approved']=len(good);dr[field+'_approved_exact_hour']=sum(t.minute==t.second==0 for t in good)
  daily.append(dr)
 summary.append(item)
dump(P/'source-manifest.json',sources);dump(P/'duplicate-audit.json',{'duplicate_groups':duplicates,'conflicts':conflicts,'policy':'Every raw occurrence retained; no conflicts resolved; conflicting timestamps excluded only from approved coverage counts.'});dump(P/'qc-samples.json',samples)
for f,h in plan['reference_hashes'].items():assert sha(ROOT/f)==h
result={'audited_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Coverage/QC only; no training/inference/error calculation/model selection; reserved2021 excluded from fit.','get_attempts':len(sources),'statuses':dict(Counter(r['audit_status'] for r in sources)),'stations':summary,'limitations':['Literal naive DataHora; no certified timezone/datum/2021gauge continuity.','Exact-grid absence is distinct from absence of offgrid records; no timestamp rounding.','Approved is source QC text, not independent accuracy certification.','No record receipt/publication times; present-day retrospective source may contain revisions.','Unavailable field/record never replaced with zero; all source values/QC remain in JSONL/XML.']}
dump(P/'coverage.json',result)
with (P/'daily-coverage.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(daily[0]));w.writeheader();w.writerows(daily)
lines=['# Cobertura ANA — reserva de maio de 2021','','Escopo: Muçum 86510000 e Linha José Júlio 86472000, 28/04–31/05/2021. Aquecimento 28–30/04. Nenhum treino, inferência, cálculo de erros ou seleção de modelo. A reserva continua excluída do ajuste.','',f"Busca restrita em {len(json.loads((P/'cache-inventory.json').read_text())['scanned'])} XMLs não encontrou resposta pertinente. Quatro GETs, sem retry automático; status: {result['statuses']}. Plano registrado antes da rede.",'','| Posto | Registros | Nível aprovado | Suspeito | Nível vazio | Maio: nível aprovado exato 15min | Maio: nível aprovado exato hora |','|---|---:|---:|---:|---:|---:|---:|']
for s in summary:
 q=s['fields'].get('NivelFinal',{});w=s['windows']['reserved_may']['grids'];lines.append(f"| {s['station']} | {s['unique_timestamps']} | {q.get('approved_numeric',0)} | {q.get('suspect_numeric',0)} | {q.get('empty_values',0)} | {w['exact_15min']['fields']['NivelFinal']['approved_numeric']}/2976 | {w['exact_hour']['fields']['NivelFinal']['approved_numeric']}/744 |")
lines+=['',f'Duplicatas extras: {sum(s["duplicate_extra_records"] for s in summary)}; conflitos: {len(conflicts)}. `coverage.json` preserva histogramas de cadência/minuto/segundo, todos os campos/QC, grades exatas e intervalos ausentes ou não aprovados. `daily-coverage.csv` detalha os dias. JSONL mantém todos os campos literais, fonte/hash e índice de registro XML (1-based). XMLs permanecem integrais e imutáveis.','','Não arredondamos timestamps nem interpolamos registros; ausência permanece ausência. Unidades/texto numérico permanecem como no XML, sem conversão. Esta auditoria não certifica fuso, datum, vigência da régua, disponibilidade histórica em tempo real nem independência física da vazão reportada. Não foram calculados picos ou métricas de modelos.']
lines += ['', 'Muçum também tem 3.264 vazões finais aprovadas; ChuvaFinal tem 3.256 valores aprovados e oito vazios. Linha tem VazaoFinal vazio nos 3.264 registros; ChuvaFinal tem 3.098 valores aprovados e 166 vazios. Há um NivelDisplay numérico em Linha, sem QC; ele permanece como campo distinto e não substitui NivelFinal. Em ambas as estações, todos os 3.263 intervalos consecutivos têm 900 segundos; não há registros fora da grade nem lacunas de timestamps. As lacunas descritas são de campos/QC.']
(P/'README.md').write_text('\n'.join(lines)+'\n')
dump(P/'artifact-hashes.json',[{'file':str(f.relative_to(P)),'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact-hashes.json'])
for s in summary:print(s['station'],s['unique_timestamps'],s['minute_counts'],s['fields']['NivelFinal'],flush=True)
