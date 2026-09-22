import unittest
from datetime import datetime,timedelta,timezone
from hydro_cadence import audit

MODELS=['radar_arvores_live_candidate','hge_arno_live_candidate']  # Original historical policy

BASE=datetime(2026,9,21,18,tzinfo=timezone.utc)
def iso(minutes):return (BASE+timedelta(minutes=minutes)).isoformat()
def record(kind,minute,payload,identifier):return {'kind':kind,'recorded_at':iso(minute),'payload':payload,'sha256':identifier}
def policy():return record('cadence_policy',-10,{'effective_from':iso(0),'interval_seconds':3600,'expected_models':MODELS,'required_actual_lead_buckets':list(range(1,13))},'policy')
def cycle(identifier='cycle',start=1):return record('cycle_started',start,{},identifier)
def issue(model,minute=10,cycle_id='cycle',leads=range(1,13),reference=None):
    return record('forecast_issue',minute,{'model_id':model,'cycle_sha256':cycle_id,'reference_at':reference or iso(0),'points':[{'valid_at':iso(minute+60*h)} for h in leads]},model+str(minute))
def completed(minute=11,identifier='cycle'):return record('cycle_completed',minute,{'cycle_sha256':identifier},'finished')

class CadenceTests(unittest.TestCase):
    def test_radar_only_transition_preserves_old_windows(self):
        transition=record('cadence_model_transition',50,{'effective_from':iso(60),'expected_models':[MODELS[0]]},'transition')
        records=[policy(),cycle(),issue(MODELS[0]),completed(),transition,
                 cycle('new',61),issue(MODELS[0],70,cycle_id='new',reference=iso(60)),completed(71,'new')]
        got=audit(records,BASE+timedelta(hours=2))
        self.assertEqual(got['windows'][0]['status'],'incomplete_or_unfinished')
        self.assertEqual(got['windows'][1]['status'],'complete')
        self.assertEqual(got['coverage_percent'],50)
        transition['payload']['effective_from']=iso(0)
        with self.assertRaises(ValueError):audit(records,BASE+timedelta(hours=2))

    def test_before_policy_and_open_window_do_not_claim_perfect_coverage(self):
        self.assertIsNone(audit([],BASE)['coverage_percent'])
        got=audit([policy()],BASE+timedelta(minutes=59))
        self.assertEqual(got['closed_windows'],0);self.assertIsNone(got['coverage_percent'])

    def test_missing_window_remains_in_denominator(self):
        records=[policy(),cycle(),*[issue(m) for m in MODELS],completed()]
        got=audit(records,BASE+timedelta(hours=2))
        self.assertEqual(got['coverage_percent'],50)
        self.assertEqual(got['windows'][1]['status'],'no_start_record')

    def test_completion_label_without_both_packets_does_not_pass(self):
        records=[policy(),cycle(),issue(MODELS[0]),completed()]
        got=audit(records,BASE+timedelta(hours=1))
        self.assertEqual(got['complete_windows'],0)

    def test_late_delivery_and_unfinished_record_are_not_running_claims(self):
        got=audit([policy(),cycle(),*[issue(m,65) for m in MODELS],completed(66)],BASE+timedelta(hours=2))
        self.assertEqual(got['windows'][0]['status'],'late_or_incomplete')
        self.assertTrue(got['windows'][0]['attempts'][0]['unfinished_record'])
        self.assertEqual(got['complete_windows'],0)

    def test_real_twelve_hour_band_is_required(self):
        got=audit([policy(),cycle(),*[issue(m,leads=range(12)) for m in MODELS],completed()],BASE+timedelta(hours=1))
        self.assertEqual(got['complete_windows'],0)

    def test_different_cycles_references_and_partial_packets_cannot_be_combined(self):
        variants=[
            [cycle('a'),cycle('b'),issue(MODELS[0],cycle_id='a'),issue(MODELS[1],cycle_id='b'),completed(identifier='a'),completed(identifier='b')],
            [cycle(),issue(MODELS[0]),issue(MODELS[1],reference=iso(60)),completed()],
            [cycle(),issue(MODELS[0],leads=range(1,7)),issue(MODELS[0],minute=11,leads=range(7,13)),issue(MODELS[1]),completed(12)],
        ]
        for records in variants:self.assertEqual(audit([policy(),*records],BASE+timedelta(hours=1))['complete_windows'],0)

    def test_backdated_policy_and_future_records_rejected_or_ignored(self):
        p=policy();p['payload']['effective_from']=iso(-20)
        with self.assertRaises(ValueError):audit([p],BASE)
        got=audit([policy(),cycle( start=70),*[issue(m,75) for m in MODELS],completed(76)],BASE+timedelta(hours=1))
        self.assertEqual(got['windows'][0]['status'],'no_start_record')

if __name__=='__main__':unittest.main()
