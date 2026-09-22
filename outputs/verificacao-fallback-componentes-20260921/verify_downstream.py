"""Downstream invariance only; no model execution or performance metrics."""
from pathlib import Path
import csv,json,hashlib,math
ROOT=Path('/Users/brunozilio/Documents/radar');OUT=ROOT/'outputs/verificacao-fallback-componentes-20260921'
RUN=ROOT/'outputs/experimento-fallback-ate-mucum-20260921';BASE=ROOT/'outputs/experimento-proxy-carreiro-20260921';UP=ROOT/'outputs/experimento-fallback-componentes-20260921'
checks=[];hashes={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):hashes[str(p)]=sha(p);return p
def rows(p):return list(csv.DictReader(read(p).open()))
def check(k,v,d=None):checks.append(dict(check=k,passed=bool(v),detail=d))
def key(r):return r['origin'],r['target_time'],int(r['nominal_lead_h'])
def equal(a,b):return (not a and not b) or bool(a and b and float(a)==float(b))
def run():
 if not (RUN/'experiment.json').exists():print('WAITING_DOWNSTREAM');return
 meta=json.loads(read(RUN/'experiment.json').read_text())
 for name,digest in meta['input_sha256'].items():
  p=Path(name);check('input hash '+name,sha(read(p))==digest)
  if p.suffix=='.py':check('executed code '+p.name,sha(read(RUN/'code'/p.name))==digest)
 upstream_audit=json.loads(read(OUT/'verification.json').read_text());check('independent upstream audit passed',upstream_audit['passed'])
 check('upstream selected predictions match audited hash',upstream_audit['input_sha256'][str(UP/'predictions.csv')]==sha(read(UP/'predictions.csv')))
 old=rows(BASE/'predictions.csv');oldmap={key(r):r for r in old};new=rows(RUN/'predictions.csv')
 check('23538 keys/order/rows preserved',len(new)==23538 and [key(r) for r in new]==[key(r) for r in old] and len({key(r) for r in new})==23538)
 check('baseline targets anchors statuses unchanged',all(equal(r['actual_m'],oldmap[key(r)]['actual_m']) and r['anchor_at']==oldmap[key(r)]['anchor_at'] and r['previous_status']==oldmap[key(r)]['status'] and equal(r['reference_m'],oldmap[key(r)]['julho_levels_m']) for r in new))
 flags={}
 for r in rows(UP/'predictions.csv'):
  if r['phase']!='test':continue
  value=r['fallback_selected']=='True'
  if r['origin'] in flags:assert flags[r['origin']]==value
  flags[r['origin']]=value
 check('downstream selection matches upstream mask',all((r['conditional_selected']=='True')==flags[r['origin']] for r in new))
 unselected=[r for r in new if r['conditional_selected']=='False'];selected=[r for r in new if r['conditional_selected']=='True']
 check('unselected values exactly unchanged',all(equal(r['candidate_m'],oldmap[key(r)]['julho_levels_m']) for r in unselected))
 check('unselected status exactly unchanged',all(r['candidate_status']==oldmap[key(r)]['status'] for r in unselected))
 check('unselected delta exactly zero',all(float(r['delta_julho_routed_m3_s'])==0 for r in unselected))
 check('metadata row/selection count',meta['rows']==23538 and meta['selected_rows']==len(selected))
 check('no retraining/promotion',meta['models_fitted']==0 and not meta['promoted'] and not meta['live_issuance'])
 check('inputs unchanged during audit',all(sha(Path(p))==v for p,v in hashes.items()))
 result={'passed':all(r['passed'] for r in checks),'checks':checks,'input_sha256':hashes,'rows':len(new),'selected_rows':len(selected),'unselected_rows':len(unselected),'selected_math_recomputed_here':False,'metrics_computed':False,'causality_certified':False,'automatic_transfer_to_other_snapshots_allowed':False,'limitation':'Only invariance verified here. Root independently verifies selected mathematical updates. ONS conflicts and mapping must be re-audited in every different snapshot.'}
 (OUT/'downstream-verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({k:result[k] for k in ['passed','rows','selected_rows','unselected_rows']},indent=2))
 if not result['passed']:raise SystemExit(1)
if __name__=='__main__':run()

