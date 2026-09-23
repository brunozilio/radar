"""Operational shadow metadata never carries forecast points into public state."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hydro_site_projection import shadow_refresh_status


class ShadowRefreshTests(unittest.TestCase):
    def test_only_shadow_metadata_is_exposed_and_bound_to_this_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            self.assertIsNone(shadow_refresh_status(out, 'projection/receipts/attempt.json'))
            value = dict(schema='radar-propagation-shadow/v1', mode='shadow', publishable=False,
                         station='86510000', status='calculated', modelVersion='mucum-hydrometry-shadow-v1',
                         referenceAt='2026-09-23T08:00:00-03:00', generatedAt='2026-09-23T10:02:00-03:00',
                         points=[dict(level=99)], reason='private', sources=[dict(raw='private')])
            (out / 'propagation-shadow.json').write_text(json.dumps(value))
            summary = shadow_refresh_status(out, 'projection/receipts/attempt.json')
            self.assertEqual(summary, {key: value[key] for key in ('status', 'modelVersion', 'referenceAt', 'generatedAt')} |
                             dict(archiveReceiptKey='projection/receipts/attempt.json'))
            for patch in (dict(station='86472600'), dict(publishable=True), dict(mode='public'),
                          dict(status='published'), dict(modelVersion='other')):
                (out / 'propagation-shadow.json').write_text(json.dumps(value | patch))
                self.assertIsNone(shadow_refresh_status(out, 'projection/receipts/attempt.json'))

    def test_unavailable_shadow_can_report_a_check_without_claiming_a_reference(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            value = dict(schema='radar-propagation-shadow/v1', mode='shadow', publishable=False,
                         station='86510000', status='unavailable', generatedAt='2026-09-23T10:02:00-03:00',
                         reason='source unavailable', candidates=[])
            (out / 'propagation-shadow.json').write_text(json.dumps(value))
            summary = shadow_refresh_status(out, 'projection/receipts/unavailable.json')
            self.assertEqual(summary['status'], 'unavailable')
            self.assertNotIn('referenceAt', summary)
            self.assertNotIn('reason', summary)

    def test_informational_metadata_failure_cannot_fail_the_primary_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            for invalid in ('{', '[]', 'null'):
                (out / 'propagation-shadow.json').write_text(invalid)
                self.assertIsNone(shadow_refresh_status(out, 'projection/receipts/attempt.json'))
            with patch.object(Path, 'read_text', side_effect=OSError('fixture read failure')):
                self.assertIsNone(shadow_refresh_status(out, 'projection/receipts/attempt.json'))


if __name__ == '__main__':
    unittest.main()
