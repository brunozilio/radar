from pathlib import Path
import hashlib,json,joblib,numpy as np
P=Path(__file__).resolve().parent;R=P.parents[1];result=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for phase in ('validation','test'):
 old=R/f'outputs/experimento-radar-mistura-atrasos-20260922/models/{phase}-mixed_profile_candidate-12.joblib';new=R/f'outputs/experimento-radar-idade-ancora-20260922/models/{phase}-age_mixed_candidate-12.joblib'
 a=joblib.load(old);b=joblib.load(new);fields=[];used=0
 assert len(a._predictors)==len(b._predictors)==180
 for i,(stagea,stageb) in enumerate(zip(a._predictors,b._predictors)):
  assert len(stagea)==len(stageb)==1
  ta,tb=stagea[0],stageb[0];nodes=tb.nodes;used+=int(((nodes['is_leaf']==0)&(nodes['feature_idx']==180)).sum())
  assert set(vars(ta))==set(vars(tb))
  for k in vars(ta):
   va,vb=getattr(ta,k),getattr(tb,k)
   if va.dtype.names:
    for name in va.dtype.names:
     ok=np.array_equal(va[name],vb[name],equal_nan=True);assert ok,(phase,i,k,name);fields.append((i,k,name))
   else:assert np.array_equal(va,vb,equal_nan=True),(phase,i,k);fields.append((i,k,None))
 assert used==0 and np.array_equal(a._baseline_prediction,b._baseline_prediction,equal_nan=True)
 result.append({'phase':phase,'horizon_h':12,'trees':180,'tree_attribute_fields_compared':len(fields),'all_tree_fields_equal':True,'nonleaf_splits_using_age_column180':used,'baseline_prediction_equal':True,'old_model':str(old.relative_to(R)),'old_sha256':sha(old),'new_model':str(new.relative_to(R)),'new_sha256':sha(new)})
(P/'tree-h12-verification.json').write_text(json.dumps({'passed':True,'results':result,'scope':'Onlyh12twofolds. Treefields/bitsets/intercept checked; no fit or change of models.'},indent=2)+'\n')
print('PASS h12:2folds,360trees identical;0age splits')
