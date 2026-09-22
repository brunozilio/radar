import unittest
from hydro_observation_latency import receipt_windows,first_seen_observations

def receipt(at,observations,collected=None):
    return dict(kind='observation_receipt',sha256=at,recorded_at=at,payload=dict(blob_sha256='same',collection={'collected_at':collected} if collected else {},observations=observations))
def observation(at,value=7.,quality='Dado aprovado'):
    return dict(station_id='x',datum_id='d',valid_at=at,level_m=value,quality=quality)

class LatencyTest(unittest.TestCase):
    def test_duplicate_collection_not_counted_twice_and_future_is_excluded(self):
        observations=[observation('2026-01-01T00:00:00Z'),observation('2026-01-01T02:00:00Z')]
        records=[receipt('2026-01-01T01:05:00Z',observations,'2026-01-01T01:00:00Z'),receipt('2026-01-01T01:10:00Z',observations,'2026-01-01T01:00:00Z')]
        snapshots=receipt_windows(records)
        self.assertEqual(len(snapshots),1);self.assertEqual(snapshots[0]['future_rows'],1)
        self.assertEqual(snapshots[0]['latest_approved_age_minutes'],60.)

    def test_past_history_is_censored_and_first_approval_is_preserved(self):
        records=[receipt('2026-01-01T01:00:00Z',[observation('2026-01-01T00:00:00Z')]),receipt('2026-01-01T02:00:00Z',[observation('2026-01-01T01:30:00Z',quality='Dado suspeito')]),receipt('2026-01-01T02:10:00Z',[observation('2026-01-01T01:30:00Z')])]
        got=first_seen_observations(receipt_windows(records))
        self.assertFalse(got[0]['at_or_after_audit_start']);self.assertTrue(got[1]['at_or_after_audit_start'])
        self.assertEqual(got[1]['first_seen_delay_minutes'],40.)

if __name__=='__main__':unittest.main()
