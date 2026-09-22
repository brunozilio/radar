"""Independent measured-interval overlap reconstruction of 2024 rain features."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
TZ=timezone(timedelta(hours=-3))


def epoch(s):
    t=datetime.fromisoformat(s)
    return (t if t.tzinfo else t.replace(tzinfo=TZ)).timestamp()


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    hydro=ROOT/'outputs/radar-insumos-2024-hidrologia-20260921'
    matrix=ROOT/'outputs/radar-matriz-2024-20260921/features.npz'
    weightfile=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json'
    delayfile=ROOT/'outputs/auditoria-latencias-chuva-20260921/latencies.json'
    data=dict(np.load(matrix)); times=data['times']; weights=json.loads(weightfile.read_text())
    lags={r['station']:r['shift_steps_15min']*900 for r in json.loads(delayfile.read_text())['stations']}
    paths=[matrix,weightfile,delayfile]
    requests=[(w,0) for w in (1,3,6,12,24,48)]+[(3,lag) for lag in (3,6,12)]
    result={}; details=[]
    for code,delay in lags.items():
        path=hydro/'stations'/f'ana-{code}-all-qc.jsonl'; paths.append(path)
        rows=[json.loads(s) for s in path.read_text().splitlines()]
        if rows:
            ends=np.array([epoch(r['DataHora']) for r in rows]); dt=np.r_[0,np.diff(ends)]
            values=[]
            for r in rows:
                try: v=float(r.get('ChuvaFinal'))
                except (ValueError,TypeError): v=np.nan
                if not (np.isfinite(v) and 0<=v<=150 and r.get('CQ_ChuvaFinal') in ('Dado aprovado',None)): v=np.nan
                values.append(v)
            values=np.array(values); good=np.isfinite(values)&(dt>0)&(dt<=5400)
            left=ends[good]-dt[good]; right=ends[good]; duration=dt[good]; rain=values[good]
        else:
            left=right=duration=rain=np.array([])
        details.append(dict(station=code,source_rows=len(rows),measured_intervals=len(rain),effective_delay_seconds=delay))
        for window,lag in requests:
            queries=times-delay-lag*3600
            amounts=[]; cover=[]
            for offset in range(0,len(queries),128):
                q=queries[offset:offset+128,None]
                overlap=np.maximum(0,right[None,:]-np.maximum(left[None,:],q-window*3600))
                overlap*=right[None,:]<=q
                amounts.extend((overlap/duration[None,:]*rain[None,:]).sum(axis=1))
                cover.extend(overlap.sum(axis=1)/(window*3600))
            result[code,window,lag]=(np.array(amounts),np.clip(cover,0,1))
    columns=[]
    for group in weights:
        current={}
        for window,lag in requests:
            p=sum(w*result[code,window,lag][0] for code,w in group['weights'].items())
            c=sum(w*result[code,window,lag][1] for code,w in group['weights'].items())
            current[window,lag]=(np.where(c>=.5,p,np.nan),c)
        for window in (1,3,6,12,24,48): columns.extend(current[window,0])
        for lag in (3,6,12): columns.append(current[3,lag][0])
    actual=np.column_stack(columns); expected=data['features'][:,45:120]
    assert actual.shape==expected.shape==(744,75)
    np.testing.assert_array_equal(np.isnan(actual),np.isnan(expected))
    np.testing.assert_allclose(actual,expected,atol=2e-10,rtol=0,equal_nan=True)
    report=dict(passed=True,cells=actual.size,finite_cells=int(np.isfinite(actual).sum()),
        missing_cells=int(np.isnan(actual).sum()),maximum_absolute_difference=float(np.nanmax(abs(actual-expected))),
        method='Independent interval-overlap integration; a measured interval contributes only after its end timestamp. No calls to observed_rain_windows or telemetry_features.',
        source_scope='Normalized all-QC ANA rows, previously independently checked against raw XMLs. No network calls or source mutations.',
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},stations=details,
        publication_times_certified=False,promoted=False,goal_achieved=False)
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'README.md').write_text('# Conferência independente da chuva observada2024\n\n'
        f"As{actual.size:,} células dos75 campos de chuva foram reconstruídas diretamente dos intervalos medidos nas séries ANA normalizadas, sem chamar os helpers da matriz. Máscaras de ausência idênticas; maior diferença numérica{report['maximum_absolute_difference']:.3g}.\n\n"
        'Cada intervalo só entra após seu timestamp final. Foram preservados limites de duração, QC, segundos, atrasos efetivos, pesos, cobertura mínima e ausências. Esta auditoria verifica o cálculo; não certifica a publicação histórica nem a comparabilidade física entre anos. Nenhum treino ou alteração operacional.\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','stations')},indent=2))


if __name__=='__main__': main()
