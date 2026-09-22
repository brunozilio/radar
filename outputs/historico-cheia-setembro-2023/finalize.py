from pathlib import Path
import json,hashlib,datetime,shutil
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[1];now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(name,x): (P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=pd.read_csv(P/'ons-ceran-source-values.csv');a=pd.read_csv(P/'ana-mucum/levels-approved.csv');peak=[]
for rid,g in d.groupby('id_reservatorio'):
 t=pd.to_datetime(g.din_instante);sel=g[(t>='2023-09-03')&(t<'2023-09-07')]
 maxima={c:g.loc[g[c].idxmax(),['din_instante',c]].to_dict() for c in ['val_vazaoafluente','val_vazaodefluente']}
 peak.append({'id':rid,'name':g.nom_reservatorio.iloc[0],'maxima_original_timestamps':maxima,'Sep3_to6_rows':len(sel),'Sep3_to6_expected':96,'QI_nonnull':int(sel[['val_vazaoafluente','val_vazaodefluente']].notna().all(axis=1).sum())})
before=a[a.timestamp_source_naive<='2023-09-04T19:30:00'].iloc[-1].to_dict();after=a[a.timestamp_source_naive>'2023-09-04T19:30:00'].iloc[0].to_dict()
dump('peak-coverage.json',{'ONS':peak,'ANA_last_approved_before_failure':before,'ANA_first_approved_after_failure':after,'retrospective_SGB_peak':{'level_m':26.108,'approx_local_time':'2023-09-05T02:30:00','survey_date':'2023-09-08','status':'RETROSPECTIVE_LEVELLED_MARK_NOT_TELEMETRY_NOT_INSERTED','datum_link_to_current_gauge':'UNVERIFIED'}})
# Reuse cached sources: store hashes and extraction references, no duplicate downloads.
sources=[];D=R/'outputs/historico-cheias-mucum/documentation'
for manifest,fil,pages,canonical in [('reference-investigation-manifest.json','sgb-cheia2024-v19-2026.pdf',[15,18,19],'https://rigeo.sgb.gov.br/handle/doc/24939.21'),('reference-latest-version-manifest.json','sgb-zeros-ortometricos-v3-2026.pdf',[12],'https://rigeo.sgb.gov.br/handle/doc/25578.3')]:
 mm=json.loads((D/manifest).read_text());mm=mm if isinstance(mm,list) else [mm];m=next(x for x in mm if x['file']==fil);f=D/fil;assert sha(f)==m['sha256'];sources.append({**m,'file':str(f.relative_to(R)),'canonical_url':canonical,'reused_cache':True,'reviewed_at':now,'relevant_pdf_pages_1based':pages})
qc=R/'outputs/pesquisa-qc-semantica-fontes';sources.append({'file':str((qc/'source-manifest.json').relative_to(R)),'sha256':sha(qc/'source-manifest.json'),'role':'Primary ONS dictionary/catalog/norm and CERAN cached-source provenance','reviewed_at':now})
dump('documentation-manifest.json',sources)
c=json.loads((P/'catalog.json').read_text());assert sum(c['ana']['grid_counts'].values())==2880;assert all(s['rows']==714 and s['missing_rows']==6 for s in c['ons']);assert len(d)==2142;assert len(a)==2023;assert ((a.NivelFinal/100-a.level_m).abs()<1e-9).all();assert sum(s['balance_abs_residual_gt1'] for s in c['ons'])==1
for m in json.loads((P/'source-manifest.json').read_text()):assert sha(P/m['file'])==m['sha256']
dump('validation.json',{'checked_at':now,'raw_sha256':'all_match','ANA_partition_2880':'pass','approved_cm_to_m_2023_rows':'pass','ONS_2142_rows_3x714':'pass','one_balance_review_flag':'pass','model_mutations':False,'interpolation':False,'training_or_test_allocation':False})
print(json.dumps(peak,ensure_ascii=False,indent=2))
