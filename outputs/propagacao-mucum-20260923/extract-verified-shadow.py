"""Inspect only named members after the remote downloader verified both blobs."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import tarfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
proof = json.loads((BASE / 'verified-shadow-archive.json').read_text())
directory = Path(proof['directory'])
objects = {o['role']: o for o in proof['objects']}

def digest(body):
    return hashlib.sha256(body).hexdigest()

def member(archive, name):
    rows = [m for m in archive.getmembers() if m.name == name]
    assert len(rows) == 1 and rows[0].isfile(), name
    return archive.extractfile(rows[0]).read()

for role, obj in objects.items():
    assert digest((directory / (role + '.tar.gz')).read_bytes()) == obj['sha256']
with tarfile.open(directory / 'runtime.tar.gz') as runtime:
    manifest_body = member(runtime, 'manifest.json')
    assert manifest_body == (ROOT / 'projection-runtime/manifest.json').read_bytes()
    manifest = json.loads(manifest_body)
    for name, expected in manifest.items():
        assert digest(member(runtime, name)) == expected, name
    model_sha = manifest['model-artifacts/mucum-propagation-v1/model.json']
with tarfile.open(directory / 'attempt.tar.gz') as attempt:
    issue_body = member(attempt, 'propagation-shadow.json')
    issue = json.loads(issue_body)
    assert issue['mode'] == 'shadow' and issue['publishable'] is False
    assert issue['modelSha256'] == model_sha
    (directory / 'propagation-shadow.json').write_bytes(issue_body)
    collected_body = member(attempt, 'collection-manifest.json')
    collected = json.loads(collected_body)
    # Verify all seven live source hashes against their archived receipts.
    for source in issue.get('sources', []):
        rows = [row for row in collected if row.get('file') == source['file']]
        assert len(rows) == 1 and rows[0]['sha256'] == source['sha256']
        assert digest(member(attempt, 'raw/' + source['file'])) == source['sha256']
        assert rows[0]['collected_at'] == source['availableAt']
    observations = directory / 'observations'
    (observations / 'raw').mkdir(parents=True, exist_ok=True)
    (observations / 'collection-manifest.json').write_bytes(collected_body)
    (observations / 'raw/ana-86510000-fresh.xml').write_bytes(member(attempt, 'raw/ana-86510000-fresh.xml'))
    public_forecast_present = 'forecast.json' in attempt.getnames()

archive_at = max(proof['receiptLastModified'], objects['attempt']['lastModified'])
index = [dict(issue=str((directory/'propagation-shadow.json').relative_to(BASE)),
              archivedAt=archive_at, evidenceReceiptKey=proof['receiptKey'],
              archiveSha256=objects['attempt']['sha256'], issueSha256=digest(issue_body))]
(BASE/'prospective-index.json').write_text(json.dumps(index, indent=2)+'\n')
result = dict(checkedAt=proof['checkedAt'], source='Production R2 immutable receipt and content-addressed blobs',
              receiptKey=proof['receiptKey'], status=issue['status'],
              generatedAt=issue['generatedAt'], referenceAt=issue.get('referenceAt'),
              archivedAt=archive_at, modelSha256=model_sha,
              runtimeManifestAndEveryMemberVerified=True, liveSourceHashesVerified=True,
              points=len(issue['points']), publicForecastPresent=public_forecast_present,
              prospectiveObservations=str(observations.relative_to(ROOT)))
(BASE/'production-shadow-proof.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
