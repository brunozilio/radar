import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from hydro_propagation_data import (KEYS, epoch, load_dataset, parse_ana,
                                    parse_ceran, parse_ons, sha)


def xml(station='86510000', time='2026-09-21T10:00:00', level='750', quality='Dado aprovado'):
    return ('<DadosHidrometereologicos><CodEstacao>' + station + '</CodEstacao>'
            '<DataHora>' + time + '</DataHora><NivelFinal>' + level + '</NivelFinal>'
            '<CQ_NivelFinal>' + quality + '</CQ_NivelFinal></DadosHidrometereologicos>')


class ExactHourDataTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_xml(self, rows, name='source.xml'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('<root>' + ''.join(rows) + '</root>')
        return path

    def test_exact_hour_and_metres_without_carry_forward(self):
        path = self.write_xml([xml(), xml(time='2026-09-21T10:15:00', level='800'),
                               xml(time='2026-09-21T12:00:00', level='900')])
        records, flags = parse_ana(path, '86510000')
        self.assertEqual(records['86510000:H'], {epoch('2026-09-21T10:00:00'): 7.5,
                                                epoch('2026-09-21T12:00:00'): 9.0})
        self.assertEqual(flags['non_hourly_records_omitted'], 1)
        self.assertEqual(epoch('2026-09-21T10:00:00'), epoch('2026-09-21T13:00:00+00:00'))

    def test_rejected_quality_and_nonfinite_are_unknown(self):
        path = self.write_xml([xml(quality='Dado suspeito'),
                               xml(time='2026-09-21T11:00:00', level='NaN'),
                               xml(time='2026-09-21T12:00:00', level='-100')])
        records, _ = parse_ana(path, '86510000')
        self.assertTrue(all(np.isnan(v) for v in records['86510000:H'].values()))

    def test_wrong_station_fails(self):
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            parse_ana(self.write_xml([xml(station='86720000')]), '86510000')

    def test_conflicting_duplicate_fails(self):
        with self.assertRaisesRegex(ValueError, 'Conflicting ANA duplicate'):
            parse_ana(self.write_xml([xml(), xml(level='999')]), '86510000')

    def ons(self, **changes):
        row = dict(id_reservatorio='JIUHQJ', nom_reservatorio='14 DE JULHO', cod_usina='99.0',
                   din_instante='2026-09-21 10:00:00', val_vazaodefluente='0',
                   val_vazaoafluente='100', val_vazaoturbinada='100',
                   val_vazaovertida='0', val_vazaooutrasestruturas='0')
        row.update(changes)
        path = self.root / 'ons.csv'
        with path.open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(row), delimiter=';')
            writer.writeheader()
            writer.writerow(row)
        return path

    def test_contradicted_zero_is_not_replaced_by_components(self):
        rows, flags = parse_ons(self.ons())
        at = epoch('2026-09-21T10:00:00')
        self.assertTrue(np.isnan(rows['julho:Q'][at]))
        self.assertEqual(rows['julho:I'][at], 100)
        self.assertEqual(flags['julho:zero_flow_positive_components_rejected'], 1)

    def test_uncontradicted_zero_kept_and_no_clock_shift(self):
        rows, _ = parse_ons(self.ons(val_vazaoturbinada='0'))
        self.assertEqual(rows['julho:Q'], {epoch('2026-09-21T10:00:00'): 0})

    def test_ons_2359_is_not_relabelled_as_midnight(self):
        rows, flags = parse_ons(self.ons(din_instante='2026-09-21 23:59:00'))
        self.assertEqual(rows['julho:Q'], {})
        self.assertEqual(flags['non_hourly_records_omitted'], 1)

    def test_ons_identity_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, 'name/code mismatch'):
            parse_ons(self.ons(cod_usina='98'))

    def test_ceran_exact_hour_and_columns(self):
        path = self.root / 'ceran.html'
        path.write_text('<tr>' + ''.join(f'<td>{v}</td>' for v in
                                       ['21/09/2026 10:00:00', '0', '0', '25.5', '0', '0', '0', '35.2']) + '</tr>')
        rows, _ = parse_ceran(path, 'julho')
        self.assertEqual(rows['julho:Q'][epoch('2026-09-21T10:00:00')], 35.2)
        self.assertEqual(rows['julho:I'][epoch('2026-09-21T10:00:00')], 25.5)

    def fixture(self):
        baseline = self.root / 'baseline'
        self.write_xml([xml(), xml(time='2026-09-21T12:00:00')], 'baseline/raw/ana-86510000.xml')
        return baseline

    def collection(self, rows, received='2026-09-21T13:00:00-03:00', digest=None):
        path = self.write_xml(rows, 'collection/raw/ana-86510000-fresh.xml')
        directory = self.root / 'collection'
        manifest = [dict(file=path.name, source='ANA', collected_at=received,
                         sha256=digest or sha(path))]
        (directory / 'collection-manifest.json').write_text(json.dumps(manifest))
        return directory

    def test_grid_missing_cells_and_unknown_receipt_are_explicit(self):
        times, data, metadata = load_dataset(self.fixture())
        self.assertEqual(np.diff(times).tolist(), [3600, 3600])
        self.assertTrue(np.isnan(data['86510000:H'][1]))
        self.assertTrue(np.isnan(data['julho:Q']).all())
        self.assertTrue(np.isnan(data['received_at:86510000:H']).all())
        self.assertEqual(data['source_index:86510000:H'].tolist(), [0, -1, 0])
        self.assertEqual(metadata['complete_current_hours'], 0)
        self.assertEqual(metadata['keys'], list(KEYS))

    def test_invalid_revision_replaces_previous_valid_observation(self):
        baseline = self.fixture()
        collection = self.collection([xml(quality='Dado reprovado')])
        times, data, _ = load_dataset(baseline, [collection])
        self.assertTrue(np.isnan(data['86510000:H'][0]))
        self.assertEqual(data['received_at:86510000:H'][0], epoch('2026-09-21T13:00:00-03:00'))
        self.assertGreater(data['received_at:86510000:H'][0], times[0])

    def test_older_collection_cannot_replace_newer_received_revision(self):
        baseline = self.fixture()
        raw = baseline / 'raw'
        original = raw / 'ana-86510000.xml'
        (raw / 'ana-expanded-manifest.json').write_text(json.dumps([
            dict(file=original.name, at='2026-09-21T15:00:00-03:00', sha256=sha(original))]))
        collection = self.collection([xml(level='999')])
        _, data, metadata = load_dataset(baseline, [collection])
        self.assertEqual(data['86510000:H'][0], 7.5)
        self.assertEqual(metadata['sources'][-1]['flags']['older_or_unknown_receipt_revisions_rejected'], 1)

    def test_hash_mismatch_fails(self):
        baseline = self.fixture()
        collection = self.collection([xml()], digest='0' * 64)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            load_dataset(baseline, [collection])

    def test_future_source_observation_is_excluded(self):
        baseline = self.fixture()
        collection = self.collection([xml(time='2026-09-21T14:00:00', level='999')])
        times, _, metadata = load_dataset(baseline, [collection])
        self.assertEqual(times[-1], epoch('2026-09-21T12:00:00'))
        self.assertEqual(metadata['sources'][-1]['flags']['future_observations_rejected'], 1)


if __name__ == '__main__':
    unittest.main()
