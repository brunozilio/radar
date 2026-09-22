"""Check whether the appended age feature is actually used by saved trees."""
import csv,hashlib,json
from pathlib import Path
import joblib,numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
A=ROOT/'outputs/experimento-radar-idade-ancora-20260922'
B=ROOT/'outputs/experimento-radar-mistura-atrasos-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rows=[];metadata_only_differences=[];hashes={str(Path(__file__)):sha(Path(__file__))}
    for phase in ('validation','test'):
        for h in range(1,13):
            pa=A/'models'/f'{phase}-age_mixed_candidate-{h}.joblib';pb=B/'models'/f'{phase}-mixed_profile_candidate-{h}.joblib'
            a,b=joblib.load(pa),joblib.load(pb);hashes.update({str(p):sha(p) for p in (pa,pb)})
            assert a.n_features_in_==181 and b.n_features_in_==180
            assert len(a._predictors)==len(b._predictors)==180
            uses=0;trees=0;identical=0;identical_without_gain=0
            for tree_index,(aa,bb) in enumerate(zip(a._predictors,b._predictors)):
                assert len(aa)==len(bb)==1
                x,y=aa[0].nodes,bb[0].nodes
                n=int(((x['feature_idx']==180)&(x['is_leaf']==0)).sum());uses+=n;trees+=int(n>0)
                identical+=int(x.shape==y.shape and x.dtype.names==y.dtype.names and all(np.array_equal(x[name],y[name],equal_nan=True) for name in x.dtype.names))
                same_without_gain=x.shape==y.shape and x.dtype.names==y.dtype.names and all(np.array_equal(x[name],y[name],equal_nan=True) for name in x.dtype.names if name!='gain')
                identical_without_gain+=int(same_without_gain)
                if same_without_gain and not np.array_equal(x['gain'],y['gain'],equal_nan=True):
                    for node in np.flatnonzero(x['gain']!=y['gain']):
                        metadata_only_differences.append(dict(phase=phase,horizon_h=h,tree=tree_index,node=int(node),is_leaf=bool(x['is_leaf'][node]),gain_with_age=float(x['gain'][node]),gain_without_age=float(y['gain'][node])))
            same_bins=all(np.array_equal(x,y,equal_nan=True) for x,y in zip(a._bin_mapper.bin_thresholds_[:180],b._bin_mapper.bin_thresholds_))
            rows.append(dict(phase=phase,horizon_h=h,age_split_nodes=uses,trees_using_age=trees,trees_identical_to_unaged=identical,trees_identical_except_gain=identical_without_gain,total_trees=180,original180_bin_thresholds_identical=same_bins))
    with (OUT/'tree-age-use.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result=dict(models_checked=24,models_using_age=sum(r['age_split_nodes']>0 for r in rows),source_sha256=hashes,
                no_age_models=[dict(phase=r['phase'],horizon_h=r['horizon_h'],all_trees_identical=r['trees_identical_to_unaged']==180) for r in rows if r['age_split_nodes']==0],
                metadata_only_differences=metadata_only_differences,
                limits='Feature use or non-use is a property of these saved trees, not a causal attribution of prediction error or justification to force splits/tune thresholds.')
    (OUT/'tree-inspection.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
