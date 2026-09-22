"""Read-only reconciliation of 2023 normalized series against preserved XML."""
from pathlib import Path
from datetime import datetime
import hashlib,json,math,xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'outputs/radar-insumos-observados-2023-20260921'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest=json.loads((SOURCE/'artifact-hashes.json').read_text())
    entries=list(manifest['files'].items()) if isinstance(manifest,dict) else [(r['file'],r['sha256']) for r in manifest]
    for f,h in entries:assert sha(SOURCE/f)==h
    plan=json.loads((SOURCE/'collection-plan.json').read_text())
    collected=json.loads((SOURCE/'source-manifest.json').read_text())
    assert len(plan['new_jobs'])==27 and len(plan['reused'])==11 and len(collected)==38
    bystation={c:[] for c in plan['stations']};source_checks=[]
    for source in collected:
        p=ROOT/source['source_path'];assert sha(p)==source['sha256']
        root=ET.parse(p).getroot();nr=0
        for e in root.iter():
            if e.tag.rsplit('}',1)[-1]!='DadosHidrometereologicos':continue
            nr+=1;row={c.tag.rsplit('}',1)[-1]:c.text for c in e}
            when=datetime.fromisoformat(row['DataHora'])
            if datetime(2023,8,29)<=when<datetime(2023,10,1):
                assert row['CodEstacao']==source['station']
                row.update(source_file=source['source_path'],source_sha256=source['sha256'],source_record_index=nr)
                bystation[source['station']].append(row)
        source_checks.append(dict(path=source['source_path'],sha256=source['sha256'],records_in_source=nr))
    checks=[]
    for code,original in bystation.items():
        original.sort(key=lambda r:r['DataHora'])
        assert len({r['DataHora'] for r in original})==len(original)
        actual=[json.loads(s) for s in (SOURCE/'stations'/f'ana-{code}-all-qc.jsonl').read_text().splitlines()]
        assert original==actual
        normalized=dict(np.load(SOURCE/'stations'/f'ana-{code}-normalized-all-qc.npz'))
        np.testing.assert_array_equal(normalized['time_original'],np.array([r['DataHora'] for r in original],dtype=str))
        np.testing.assert_array_equal(normalized['source_file'],np.array([r['source_file'] for r in original],dtype=str))
        np.testing.assert_array_equal(normalized['source_record_index'],[r['source_record_index'] for r in original])
        for source,target,scale in [('NivelFinal','level_m_raw',100),('VazaoFinal','flow_m3s_raw',1),('ChuvaFinal','rain_mm_raw',1),('ChuvaAcumAdotada','counter_mm_raw',1)]:
            expected=[]
            for r in original:
                try:v=float(r.get(source))
                except (TypeError,ValueError):v=float('nan')
                expected.append(v/scale if math.isfinite(v) else float('nan'))
            np.testing.assert_array_equal(normalized[target],expected)
            np.testing.assert_array_equal(normalized[source+'_qc'],np.array([r.get('CQ_'+source) or '' for r in original],dtype=str))
        checks.append(dict(station=code,records=len(original),all_raw_fields_exact=True,numeric_and_qc_arrays_exact=True))
    ons=json.loads((SOURCE/'ons-references.json').read_text())
    for r in ons:
        assert sha(ROOT/r['literal_csv'])==r['csv_sha256']
        assert sha(ROOT/r['raw_source_path'])==r['raw_source_sha256']
        assert sha(ROOT/r['csv_manifest'])==r['csv_manifest_sha256']
        assert r['timestamp_column_used']=='din_instante' and r['interpreted_columns_ignored']
    result=dict(passed=True,artifact_hashes_verified=len(entries),xml_sources_verified=len(source_checks),
        stations_verified=len(checks),raw_records_reconciled=sum(r['records'] for r in checks),
        ons_month_references_verified=len(ons),checks=checks,source_hashes=source_checks,
        no_source_mutation=True,trained=False,goal_achieved=False)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'README.md').write_text('# Reconciliação do acervo observado2023\n\n'
        f"Foram conferidos{len(entries)} hashes de artefatos e38XMLs. Os{result['raw_records_reconciled']} registros das27estações reproduzem integralmente os campos brutos, incluindo QC e proveniência. Arrays normalizados de quatro grandezas, seus QC e timestamps também conferem. Duas referências mensais ONS foram verificadas por hash; timestamps literais permanecem intactos.\n\n"
        'Esta conferência não certifica datum, fuso, publicação histórica ou continuidade física. Ausências, suspeitos e números negativos seguem preservados. Nenhuma matriz, correção, requisição, treino ou promoção.\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','source_hashes')},indent=2))
if __name__=='__main__':main()
