"""Pre-fit numerical representation gate only; no models, fitting or prediction."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal,ROUND_HALF_EVEN,localcontext
import csv,json,hashlib,importlib.util
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
PROTOCOL=ROOT/'docs/radar-numeric-stability-protocol.json';HELPER=ROOT/'scripts/hydro_radar_numeric.py'
DATA={
 'original2025_2026':ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921/features.npz',
 'added2020':ROOT/'outputs/radar-matriz-observada-2020-20260921/features.npz',
 'original2021':ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922/2021/features.npz',
 'original2022':ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922/2022/features.npz',
 'reconstructed2021':ROOT/'outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922/reconstructed-2021.npz',
 'reconstructed2022':ROOT/'outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922/reconstructed-2022.npz'}
MASKS=[ROOT/'outputs/experimento-radar-observado-120-20260921/training-masks.npz',ROOT/'outputs/experimento-radar-historico-2020-20260921/training-masks.npz']
checks=[];sources={};records=[];decimal_rows=[];normal={};loaded={};mismatches=[];decimal_cache={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def dump(name,x):(P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ok(name,x):assert x,name;checks.append(dict(name=name,passed=True))
def arrhash(a):return hashlib.sha256(np.ascontiguousarray(a).view(np.uint8)).hexdigest()
def save(name,rows):
 if rows:
  with (P/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
 protocol=json.loads(use(PROTOCOL).read_text());use(HELPER)
 # Source inspected before loading: only numpy import/constants and normalization function.
 spec=importlib.util.spec_from_file_location('audited_numeric_helper',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 ok('fixed_precision_and_columns',helper.RAIN_DECIMALS==8 and helper.RAIN_START==45 and helper.FEATURE_COUNT==120)
 before={str(p.relative_to(ROOT)):sha(p) for p in [*DATA.values(),*MASKS,PROTOCOL,HELPER]}
 for m in MASKS:use(m)
 quantum=Decimal('0.00000001')
 for label,path in DATA.items():
  d=dict(np.load(use(path)));loaded[label]=d;F=d['features'][:,:120];prior={k:arrhash(v) for k,v in d.items()};sourcecopy=F.copy();out=helper.normalize_observed_features(F);normal[label]=out
  ok(label+':shape',out.shape==F.shape and out.shape[1]==120);ok(label+':copy',not np.shares_memory(F,out));ok(label+':source_unmodified',all(arrhash(d[k])==h for k,h in prior.items()))
  ok(label+':nonrain_bits_exact',np.array_equal(out[:,:45].view(np.uint64),F[:,:45].view(np.uint64)));ok(label+':NaNmask_exact',np.array_equal(np.isnan(F),np.isnan(out)));ok(label+':finite_mask_exact',np.array_equal(np.isfinite(F),np.isfinite(out)));ok(label+':complete24_exact',np.array_equal(np.isfinite(F[:,:24]).all(1),np.isfinite(out[:,:24]).all(1)))
  if 'complete24' in d:ok(label+':saved_complete24',np.array_equal(d['complete24'],np.isfinite(out[:,:24]).all(1)))
  ok(label+':base_truth_times_unchanged',all(arrhash(d[k])==prior[k] for k in ('base','truth','times')))
  x=F[:,45:];y=out[:,45:];finite=np.isfinite(x);ok(label+':rain_positive_zero',not np.signbit(y[y==0]).any());ok(label+':idempotent',np.array_equal(helper.normalize_observed_features(out),out,equal_nan=True));perturb=np.abs(y[finite]-x[finite]);mx=float(perturb.max()) if len(perturb) else 0;ok(label+':perturbation_bound',mx<=5e-9+1e-12)
  values,first,counts=np.unique(x[finite],return_index=True,return_counts=True);actual=y[finite][first];binary_diff=string_diff=ties_binary=ties_string=0;unique_binary_diff=unique_string_diff=0;max_decimal_discrepancy=0.
  for value,got,count in zip(values,actual,counts):
   key=float(value)
   if key not in decimal_cache:
    with localcontext() as ctx:
     ctx.prec=80;db=Decimal.from_float(key);ds=Decimal(str(key));qb=db.quantize(quantum,rounding=ROUND_HALF_EVEN);qs=ds.quantize(quantum,rounding=ROUND_HALF_EVEN);tb=(db/quantum)%1==Decimal('.5');ts=(ds/quantum)%1==Decimal('.5')
    decimal_cache[key]=(float(qb),float(qs),str(qb),str(qs),bool(tb),bool(ts))
   expected_binary,expected_string,qb,qs,tb,ts=decimal_cache[key];bd=got!=expected_binary;sd=got!=expected_string;binary_diff+=int(bd)*int(count);string_diff+=int(sd)*int(count);ties_binary+=int(tb)*int(count);ties_string+=int(ts)*int(count);unique_binary_diff+=int(bd);unique_string_diff+=int(sd);max_decimal_discrepancy=max(max_decimal_discrepancy,abs(got-expected_binary),abs(got-expected_string))
   if bd or sd:decimal_rows.append(dict(dataset=label,value_repr=repr(key),occurrences=int(count),numpy_round8=float(got),decimal_from_binary_round8=qb,decimal_from_short_repr_round8=qs,diff_binary=bool(bd),diff_short_repr=bool(sd),exact_binary_half_tie=tb,short_repr_half_tie=ts))
  # Rounding may change a coverage fraction's comparison with0.5; amounts' pre-existingNaN admission must not be recomputed.
  coverage_cols=[45+g*15+offset for g in range(5) for offset in (1,3,5,7,9,11)];threshold_cross=int(((F[:,coverage_cols]>=.5)!=(out[:,coverage_cols]>=.5)).sum())
  records.append(dict(dataset=label,source_shape=list(d['features'].shape),audited_shape=list(F.shape),rain_cells=int(x.size),finite_rain_cells=int(finite.sum()),nan_rain_cells=int(np.isnan(x).sum()),max_abs_perturbation=mx,changed_finite_rain_cells=int((x[finite]!=y[finite]).sum()),input_zeros=int((x==0).sum()),output_zeros=int((y==0).sum()),nonzero_to_zero=int(((x!=0)&finite&(y==0)).sum()),input_negative_zero=int(np.signbit(x[x==0]).sum()),output_negative_zero=int(np.signbit(y[y==0]).sum()),coverage_point5_comparison_changes=threshold_cross,decimal_exact_binary_disagreement_cells=binary_diff,decimal_short_repr_disagreement_cells=string_diff,decimal_exact_binary_disagreement_unique_values=unique_binary_diff,decimal_short_repr_disagreement_unique_values=unique_string_diff,exact_binary_half_ties=ties_binary,short_repr_half_ties=ties_string,max_numpy_vs_decimal_discrepancy=max_decimal_discrepancy))
  print(label,'max perturb',mx,'Decimal disagreements',binary_diff,string_diff,flush=True)
 comparisons=[]
 for year in (2021,2022):
  a=normal[f'original{year}'];b=normal[f'reconstructed{year}'];finite=np.isfinite(a)&np.isfinite(b);same=np.array_equal(a,b,equal_nan=True);nan_same=np.array_equal(np.isnan(a),np.isnan(b));mask=finite&(a!=b)
  for i,j in np.argwhere(mask):mismatches.append(dict(year=year,row=int(i),column=int(j),original_normalized=float(a[i,j]),reconstructed_normalized=float(b[i,j]),original_raw=float(loaded[f'original{year}']['features'][i,j]),reconstructed_raw=float(loaded[f'reconstructed{year}']['features'][i,j])))
  comparisons.append(dict(year=year,shape=list(a.shape),normalized_exact_with_NaNs=same,nan_masks_exact=nan_same,different_finite_cells=int(mask.sum()),max_abs_normalized_difference=float(np.max(abs(a[finite]-b[finite]))) if finite.any() else 0))
  checks.append(dict(name=f'{year}:normalized_original_reconstruction_exact',passed=bool(same and nan_same)))
 for path,h in before.items():ok('frozen_input_unmodified:'+path,sha(ROOT/path)==h)
 gate=all(c['normalized_exact_with_NaNs'] and c['nan_masks_exact'] for c in comparisons)
 report=dict(pre_fit_gate_passed=gate,fitting_performed=False,prediction_performed=False,registered_rule='numpy.round(decimals=8), columns45:120 only, canonical positive zero, after admission masks',checks=checks,datasets=records,original_vs_reconstructed=comparisons,normalization_mismatches=mismatches,decimal_disagreement_rows=len(decimal_rows),decimal_interpretation='Declared rule is NumPy binary floating rounding via scaling/nearest-even, not exact decimal arithmetic. Decimal.from_float tests the exact represented binary value; Decimal(str(value)) tests its shortest decimal text. Differences can occur at or near decimal half-way cases because scaling itself rounds. They do not silently replace the fixed NumPy rule.',limitations=['Complete independent reconstructed matrices exist for2021/2022 only.2020 prior verifier preserved code/results but no reconstructedNPZ;2025/26 lacks a full independent reconstructedNPZ here. Those two originals are audited for invariance/perturbation only.','No precision tuning, models, fitting, prediction, network or changes to frozen inputs.','Rounded values must not be used to recompute admission masks or coverage thresholds.','Passing this numerical gate alone is not forecast accuracy or promotion.'],source_sha256=sources,numpy_version=np.__version__)
 dump('verification.json',report);save('normalization-summary.csv',records);save('decimal-disagreements.csv',decimal_rows);save('normalized-original-reconstruction-mismatches.csv',mismatches)
 lines=['# Auditoria pré-ajuste — normalização numérica RADAR','',f"Gate fixo de oito casas: {'PASSOU' if gate else 'FALHOU; não ajustar modelos'}. Comparação original versus reconstrução independente, após normalizar, em2021/2022: {comparisons}.",'','A regra altera somente colunas45..119; níveis/QI0..44 permanecem idênticos bit a bit. NaNs, finitude, complete24, base, truth, horários e arquivos de máscaras permanecem iguais. A função retorna cópia e é idempotente. Todos os hashes de entrada foram conferidos novamente ao terminar.','', '| Matriz | Perturbação máxima | Células finitas alteradas | Nãozero→zero | Divergências Decimal binário/texto |','|---|---:|---:|---:|---:|']
 for r in records:lines.append(f"| {r['dataset']} | {r['max_abs_perturbation']:.12g} | {r['changed_finite_rain_cells']} | {r['nonzero_to_zero']} | {r['decimal_exact_binary_disagreement_cells']}/{r['decimal_short_repr_disagreement_cells']} |")
 lines+=['',report['decimal_interpretation'],'',*report['limitations']]
 (P/'README.md').write_text('\n'.join(lines)+'\n');dump('artifact-hashes.json',[dict(file=str(p.relative_to(P)),sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json']);print(json.dumps(dict(gate_passed=gate,comparisons=comparisons,checks=len(checks),decimal_disagreement_rows=len(decimal_rows)),indent=2),flush=True)
if __name__=='__main__':main()
