"""Extract only three CERAN reservoirs from verified ONS Parquets, without repair."""
import csv
import hashlib
import json
import math
from pathlib import Path

import duckdb

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/radar-insumos-2024-hidrologia-20260921'
PLANTS={'JIUHQJ':('14 DE JULHO',99),'JIUHMC':('MONTE CLARO',98),'JIUHCA':('CASTRO ALVES',97)}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def run():
    assert duckdb.__version__=='1.4.4'
    manifest=json.loads((OUT/'source-manifest.json').read_text())
    files=[r for r in manifest if r['source']=='ONS']
    assert len(files)==3 and all(r['status'] in ['downloaded','verified_reuse'] for r in files)
    records=[];summary=[];hashes={}
    con=duckdb.connect(':memory:')
    for item in sorted(files,key=lambda r:r['month']):
        path=ROOT/item['source_reference'] if item.get('source_reference') else OUT/item['file']
        assert sha(path)==item['sha256'];hashes[str(path.relative_to(ROOT))]=item['sha256']
        query=con.execute("SELECT * FROM read_parquet(?) WHERE trim(id_reservatorio) IN ('JIUHQJ','JIUHMC','JIUHCA') ORDER BY id_reservatorio,din_instante",[str(path)])
        columns=[r[0] for r in query.description]
        rows=[dict(zip(columns,row)) for row in query.fetchall()]
        seen=set()
        for row in rows:
            key=(row['id_reservatorio'].strip(),row['din_instante'])
            assert key not in seen;seen.add(key)
            assert row['nom_reservatorio'].strip()==PLANTS[key[0]][0] and row['cod_usina']==PLANTS[key[0]][1]
            assert row['din_instante'].tzinfo is None
        with (OUT/f'ons-{item["month"]}-ceran-source-values.csv').open('w') as f:
            writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(rows)
        for plant in PLANTS:
            group=[r for r in rows if r['id_reservatorio'].strip()==plant]
            assert group
            for field in [c for c in columns if c.startswith('val_')]:
                values=[float(r[field]) for r in group if r[field] is not None and math.isfinite(float(r[field]))]
                summary.append(dict(month=item['month'],plant=plant,field=field,records=len(group),
                    first_timestamp=str(group[0]['din_instante']),last_timestamp=str(group[-1]['din_instante']),
                    finite=len(values),missing=len(group)-len(values),zeros=sum(v==0 for v in values),
                    negative=sum(v<0 for v in values),minimum=min(values) if values else None,maximum=max(values) if values else None,
                    timestamps_2359=sum(r['din_instante'].strftime('%H:%M:%S')=='23:59:00' for r in group)))
        records += [dict(r,source_file=str(path.relative_to(ROOT)),source_sha256=item['sha256']) for r in rows]
    with (OUT/'ons-ceran-source-values.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    with (OUT/'ons-coverage.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    detail=dict(duckdb_version=duckdb.__version__,selected_rows=len(records),input_sha256=hashes,
        fields=columns,timestamps_shifted=False,values_corrected=False,normalized_for_model=False,
        trained=False,promoted=False,code_sha256=sha(Path(__file__)))
    (OUT/'ons-audit.json').write_text(json.dumps(detail,indent=2)+'\n')
    (OUT/'ons-auditor.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(detail,indent=2))


if __name__=='__main__':run()
