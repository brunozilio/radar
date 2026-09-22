"""Intersect frozen target eligibility and diagnostic QI flags; no mask changes."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import csv,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
M=ROOT/'outputs/radar-matriz-observada-2020-20260921';Q=ROOT/'outputs/auditoria-qi-radar-2020-20260921'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,rows):
 with (P/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for folder in (M,Q):
 for r in json.loads((folder/'artifact-hashes.json').read_text()):assert sha(folder/r['file'])==r['sha256']
z=np.load(M/'features.npz');base=z['base'];truth=z['truth']
flags=list(csv.DictReader((Q/'origin-diagnostics.csv').open()))
assert len(flags)==len(base)==480
for t,r in zip(z['times'],flags):assert datetime.fromtimestamp(int(t),timezone(timedelta(hours=-3))).isoformat()==r['origin']
zero=np.array([r['uses_any_zero']=='True' for r in flags]);conflict=np.array([r['uses_Q_zero_positive_components']=='True' for r in flags])
summary=[];exclusions=[]
for h in range(1,13):
 target=np.r_[truth[h:],np.full(h,np.nan)];finitebase=np.isfinite(base);finitetarget=np.isfinite(target);valid=finitebase&finitetarget
 summary.append(dict(horizon_h=h,scheduled=480,valid_pairs=int(valid.sum()),high_pairs=int((valid&(target>=7)).sum()),
  zero_flagged_origins=int(zero.sum()),zero_flagged_with_finite_base=int((zero&finitebase).sum()),
  zero_flagged_admitted=int((zero&valid).sum()),positive_component_conflict_admitted=int((conflict&valid).sum()),
  zero_excluded_missing_base=int((zero&~finitebase).sum()),zero_excluded_finite_base_missing_target=int((zero&finitebase&~finitetarget).sum())))
 for i in np.where(zero)[0]:
  exclusions.append(dict(origin=flags[i]['origin'],horizon_h=h,base_m=float(base[i]) if finitebase[i] else None,
   target_m=float(target[i]) if finitetarget[i] else None,admitted=bool(valid[i]),
   missing_base=bool(~finitebase[i]),missing_target=bool(~finitetarget[i]),positive_component_conflict=bool(conflict[i])))
assert all(r['zero_flagged_admitted']==r['positive_component_conflict_admitted']==0 for r in summary)
save('eligibility-summary.csv',summary);save('flagged-origin-exclusions.csv',exclusions)
result=dict(matrix_sha256=sha(M/'features.npz'),qi_flags_sha256=sha(Q/'origin-diagnostics.csv'),
 all_12_horizons_checked=True,changed_masks=False,modified_source_values=False,trained=False,promoted=False,
 key_finding='No finite-base/exact-finite-target pair uses a reportedzero in current/laggedQI under the frozen matrix contract.',
 caveat='This is missing-target/base exclusion, not validation of the reported QI zeros, full peak coverage or certified physical equivalence.')
(P/'diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
(P/'README.md').write_text('''# Interseção dos zeros Q/I com admissão2020

As480 chaves de origem foram alinhadas exatamente entre a matriz congelada e a auditoria de18 consultas Q/I. Há23 origens com algum zero reportado, incluindo recuos de até8h. Em22 delas a base Muçum já está ausente. A única base finita é08/07/2020 05h (19,02m), mas seus12 alvos seguintes estão ausentes. Consequentemente, nenhum dos pares elegíveis de1–12h usa esses zeros; o mesmo vale para Qzero com componentes positivos.

As máscaras não foram modificadas. O diagnóstico não aprova zeros fisicamente, não recupera alvos e não cobre o pico ausente. É uma explicação da composição da amostra sob as regras previamente congeladas. A ausência de dados durante o pico pode limitar o treino e não deve ser descrita como cobertura integral da cheia. Os CSVs preservam todos os23×12 casos, razões de exclusão e contagens por horizonte. Nenhum treino ou seleção usando2021/2022 ocorreu.
''')
(P/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
print(json.dumps(summary[0]));print(json.dumps(summary[-1]))
