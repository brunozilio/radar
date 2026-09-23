"""Archive contract tests using only disposable local fixtures."""
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

import hydro_projection_archive as archive


class ProjectionArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'runtime'
        self.state = self.base / 'state'
        self.out = self.base / 'attempt'
        (self.root / 'scripts').mkdir(parents=True)
        (self.root / 'scripts/hydro_example.py').write_text('VERSION = 1\n')
        (self.root / 'scripts/hydro-hourly-requirements.txt').write_text('numpy==2.5.3\n')
        for model in ('forecast-6h-v1', 'encantado-6h-v1', 'santa-tereza-6h-v1'):
            folder = self.root / 'model-artifacts' / model
            folder.mkdir(parents=True)
            (folder / 'forecast-1.joblib').write_bytes(b'fixture-model-only')
            (folder / 'model.json').write_text('{"fixture":true}')
        (self.out / 'raw').mkdir(parents=True)
        (self.out / 'raw/ana.xml').write_bytes(b'<received><level>123</level></received>')
        (self.out / 'collection-manifest.json').write_text('[{"file":"ana.xml","source":"ANA"}]')
        (self.out / 'input-readiness.json').write_text('{"status":"waiting_for_data","missing":["rain"]}')

    def enqueue(self, **changes):
        args = dict(attempt_id='attempt-001', reference_at='2026-09-22T20:00:00-03:00',
                    status='waiting_for_data', missing=['rain'])
        return archive.enqueue_attempt(self.state, self.out, self.root, **{**args, **changes})

    def receipt(self):
        return json.loads((self.state / 'archive/pending/attempt-001.json').read_text())

    def members(self, body):
        with tarfile.open(fileobj=io.BytesIO(body), mode='r:gz') as tar:
            return {m.name: tar.extractfile(m).read() for m in tar.getmembers()}

    def object_bytes(self, item):
        path = self.state / 'archive/blobs' / (item['sha256'] + '.tar.gz')
        body = path.read_bytes()
        self.assertEqual(archive.digest(body), item['sha256'])
        self.assertEqual(len(body), item['bytes'])
        self.assertEqual(item['key'], f'projection/blobs/{item["sha256"]}.tar.gz')
        return body

    def test_bundle_is_deterministic_and_deduplicates_files(self):
        name = Path('raw/ana.xml')
        first = archive.bundle(self.out, [name, name, Path('input-readiness.json')])
        os.utime(self.out / name, (1, 2))
        os.chmod(self.out / name, 0o600)
        second = archive.bundle(self.out, [Path('input-readiness.json'), name])
        self.assertEqual(first, second)
        self.assertEqual(set(self.members(first)), {'raw/ana.xml', 'input-readiness.json'})
        with tarfile.open(fileobj=io.BytesIO(first), mode='r:gz') as tar:
            for member in tar.getmembers():
                self.assertEqual(member.mtime, 0)
                self.assertEqual(member.uid, 0)
                self.assertEqual(member.mode, 0o644)

    def test_waiting_attempt_keeps_raw_inputs_and_prior_result(self):
        self.state.mkdir()
        prior = b'{"generatedAt":"previous","models":["baseline"]}'
        (self.state / 'result.json').write_bytes(prior)
        source = (self.out / 'raw/ana.xml').read_bytes()
        key = self.enqueue()
        self.assertEqual(key, 'projection/receipts/attempt-001.json')
        receipt = self.receipt()
        self.assertEqual(receipt['status'], 'waiting_for_data')
        self.assertEqual(receipt['missing'], ['rain'])
        self.assertEqual(receipt['retention'], 'No automatic time-based expiration')
        contents = self.members(self.object_bytes(next(o for o in receipt['objects'] if o['role'] == 'attempt')))
        self.assertEqual(contents['raw/ana.xml'], source)
        self.assertIn('collection-manifest.json', contents)
        self.assertIn('input-readiness.json', contents)
        self.assertEqual((self.state / 'result.json').read_bytes(), prior)
        self.assertEqual((self.out / 'raw/ana.xml').read_bytes(), source)

    def test_snapshot_shadow_and_forecast_are_archived_verbatim(self):
        values = {
            'feature-snapshot.json': b'{"features":[1,2],"receivedAt":"now"}',
            'short-term-shadow.json': b'{"mode":"shadow","publishable":false}',
            'propagation-shadow.json': b'{"mode":"shadow","rainRequired":false,"publishable":false}',
            'forecast.json': b'{"models":[{"id":"frozen","points":[1]}]}',
            'model-metadata.json': b'{"version":"frozen"}',
        }
        for name, body in values.items():
            (self.out / name).write_bytes(body)
        self.enqueue(status='calculated', generated_at='2026-09-22T20:25:00-03:00', missing=[])
        contents = self.members(self.object_bytes(next(o for o in self.receipt()['objects'] if o['role'] == 'attempt')))
        for name, body in values.items():
            self.assertEqual(contents[name], body)
        self.assertFalse((self.state / 'result.json').exists())

    def test_identical_retry_keeps_receipt_and_deduplicated_blobs(self):
        self.enqueue()
        before = {str(p.relative_to(self.state)): p.read_bytes()
                  for p in self.state.rglob('*') if p.is_file()}
        self.enqueue()
        after = {str(p.relative_to(self.state)): p.read_bytes()
                 for p in self.state.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(len(list((self.state / 'archive/blobs').iterdir())), 2)
        self.assertFalse(list(self.state.rglob('*.pending')))

    def test_retry_with_different_evidence_cannot_overwrite_receipt(self):
        self.enqueue()
        receipt_path = self.state / 'archive/pending/attempt-001.json'
        before = receipt_path.read_bytes()
        (self.out / 'raw/ana.xml').write_bytes(b'<revised/>')
        with self.assertRaisesRegex(ValueError, 'cannot be overwritten'):
            self.enqueue()
        self.assertEqual(receipt_path.read_bytes(), before)

    def test_existing_corrupt_blob_is_detected(self):
        self.enqueue()
        item = self.receipt()['objects'][0]
        (self.state / 'archive/blobs' / (item['sha256'] + '.tar.gz')).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'corrupt'):
            self.enqueue()

    def test_local_runtime_preserves_code_requirements_and_all_frozen_models(self):
        contents = self.members(archive.runtime_bundle(self.root))
        self.assertIn('scripts/hydro_example.py', contents)
        self.assertIn('scripts/hydro-hourly-requirements.txt', contents)
        for model in ('forecast-6h-v1', 'encantado-6h-v1', 'santa-tereza-6h-v1'):
            self.assertIn(f'model-artifacts/{model}/forecast-1.joblib', contents)

    def test_packaged_runtime_manifest_is_verified(self):
        name = 'scripts/hydro_example.py'
        manifest = {name: archive.digest((self.root / name).read_bytes())}
        (self.root / 'manifest.json').write_text(json.dumps(manifest))
        contents = self.members(archive.runtime_bundle(self.root))
        self.assertEqual(set(contents), {'manifest.json', name})
        (self.root / name).write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            archive.runtime_bundle(self.root)

    def test_manifest_cannot_address_outside_runtime(self):
        outside = self.base / 'private.txt'
        outside.write_bytes(b'not-an-archive-input')
        for name in ('../private.txt', str(outside)):
            (self.root / 'manifest.json').write_text(json.dumps({name: archive.digest(outside.read_bytes())}))
            with self.subTest(name=name), self.assertRaises(ValueError):
                archive.runtime_bundle(self.root)

    def test_bundle_rejects_absolute_parent_and_symlink_paths(self):
        outside = self.base / 'private.txt'
        outside.write_bytes(b'not-an-archive-input')
        (self.out / 'raw/link.xml').symlink_to(outside)
        (self.out / 'linked-directory').symlink_to(self.base, target_is_directory=True)
        paths = [Path('../private.txt'), outside, Path('raw/link.xml'),
                 Path('linked-directory/private.txt')]
        for relative in paths:
            with self.subTest(path=relative), self.assertRaises(ValueError):
                archive.bundle(self.out, [relative])

    def test_raw_symlink_cannot_enter_an_attempt(self):
        outside = self.base / 'private.txt'
        outside.write_bytes(b'not-an-archive-input')
        (self.out / 'raw/link.xml').symlink_to(outside)
        with self.assertRaises(ValueError):
            self.enqueue()
        self.assertFalse((self.state / 'archive/pending/attempt-001.json').exists())

    def test_attempt_id_cannot_escape_pending_directory(self):
        for identifier in ('../escape', '/absolute', 'bad/name', '', 'a' * 81):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                self.enqueue(attempt_id=identifier)
        self.assertFalse(self.state.exists())


if __name__ == '__main__':
    unittest.main()
