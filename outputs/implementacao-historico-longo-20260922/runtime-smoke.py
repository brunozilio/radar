import json, sys, tempfile, pathlib, tarfile, hashlib
sys.path.insert(0, '/app/projection-runtime/scripts')
import hydro_site_projection as site
from hydro_hourly_collect import TZ
from datetime import datetime
with tempfile.TemporaryDirectory() as td:
    root=pathlib.Path(td); source=root/'source'; state=root/'state'
    (source/'raw').mkdir(parents=True)
    (source/'collection-manifest.json').write_text('[]')
    sys.argv=['hydro_site_projection.py','--source',str(source),'--state',str(state), '--attempt-id','runtime-smoke', '--reference',datetime.now(TZ).replace(minute=0,second=0,microsecond=0).isoformat()]
    site.main()
    status=json.loads((state/'refresh-status.json').read_text())
    assert status['status']=='waiting_for_data'
    assert not (state/'result.json').exists()
    receipt=json.loads((state/'archive/pending/runtime-smoke.json').read_text())
    assert len(receipt['objects'])==2
    for obj in receipt['objects']:
        p=state/'archive/blobs'/pathlib.Path(obj['key']).name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==obj['sha256']
        with tarfile.open(p) as tar:
            names=tar.getnames()
            if obj['role']=='runtime':
                assert 'scripts/hydro_short_term_candidate.py' in names
                assert 'scripts/hydro_feature_contract.py' in names
                assert 'model-artifacts/forecast-6h-v1/forecast-6.joblib' in names
            else: assert 'input-readiness.json' in names
    print('SMOKE_OK: packaged runtime preserved blocked attempt, checksums verified, no forecast')
