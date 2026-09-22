from pathlib import Path
import json,hashlib,csv,numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];OLD=W/'outputs/experimento-radar-historico-2018-20260922';NEW=W/'outputs/experimento-radar-historico-2018-119-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources={};checks=[]
for name,expected_n in [('training-masks.npz',48),('training-vectors.npz',144)]:
 a=dict(np.load(OLD/name));b=dict(np.load(NEW/name));assert set(a)==set(b) and len(a)==expected_n
 for k in a:assert np.array_equal(a[k],b[k],equal_nan=True);checks.append({'check':name+':'+k,'passed':True})
 for folder in [OLD,NEW]:sources[str((folder/name).relative_to(W))]=sha(folder/name)
ap=list(csv.DictReader((OLD/'training-plan.csv').open()));bp=list(csv.DictReader((NEW/'training-plan.csv').open()));assert ap==bp and len(ap)==48;checks.append({'check':'48 training plans identical','passed':True})
projection=np.load(NEW/'feature-indices.npy');assert np.array_equal(projection,np.r_[0,np.arange(2,120)]);checks.append({'check':'fixed119projection','passed':True})
protocol=W/'docs/radar-2018-hourly-augmentation-119-protocol.json';assert sha(protocol)=='69fe4433ade7cea1e561b9b8558a224745f6b78c23f3b613667400b8d2dc470d'
for p in [OLD/'training-plan.csv',NEW/'training-plan.csv',NEW/'feature-indices.npy',NEW/'pre-fit-manifest.json',protocol,W/'scripts/hydro_radar_2018_augmentation_119.py']:sources[str(p.relative_to(W))]=sha(p)
pre=json.loads((NEW/'pre-fit-manifest.json').read_text())
for p,h in pre['prepared_sha256'].items():assert sha(NEW/p)==h;checks.append({'check':'new prepared hash '+p,'passed':True})
(R/'119-prefit-verification.json').write_text(json.dumps({'passed':True,'checks':checks,'counts':{'masks':48,'vectors':144,'training_plan_rows':48,'projected_features':119},'source_sha256':sources,'scope':'Only stable prefit artifacts during coordinator training; no candidate model/prediction inspection or rerun','static_review':'upstream_complete is computed on sourceX[:,6:24] before projection; same feature_indices applies to recent and both2018matrices before fit/predict'},indent=2)+'\n');print(len(checks),'passed')
