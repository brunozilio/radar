import unittest
from datetime import datetime,timedelta,timezone
from hydro_flood_events import inventory,audit


class FloodEventInventoryTests(unittest.TestCase):
    def setUp(self):
        self.start=datetime(2026,1,1,tzinfo=timezone.utc)
        self.policy={'threshold_m':7,'dry_separation_hours':2,'max_observation_gap_minutes':20}

    def observations(self,levels,omit=(),invalid=(),datum='test'):
        result={}
        for i,value in enumerate(levels):
            if i in omit:continue
            at=self.start+timedelta(minutes=15*i)
            row={'station_id':'86510000','datum_id':datum,'valid_at':at.isoformat(),'level_m':value,'quality':'Dado suspeito' if i in invalid else 'Dado aprovado','timezone_verified':True,'datum_verified':True}
            result['86510000',datum,at]=row,'receipt'+str(i)
        return result

    def test_multiple_peaks_before_full_recession_are_one_event(self):
        levels=[3]*9+[8,9,8]+[3]*4+[8]+[3]*9
        events,membership=inventory(self.observations(levels),self.policy)
        self.assertEqual(len(events),1)
        self.assertTrue(events[0]['complete_observed_cluster'])
        self.assertEqual(events[0]['high_observation_count'],4)
        self.assertEqual(len(set(membership.values())),1)
        self.assertFalse(events[0]['independence_certified'])

    def test_completed_recession_separates_two_clusters(self):
        levels=[3]*9+[8]+[3]*9+[8]+[3]*9
        events,_=inventory(self.observations(levels),self.policy)
        self.assertEqual(len(events),2)
        self.assertTrue(all(e['complete_observed_cluster'] for e in events))

    def test_missing_or_invalid_samples_cannot_prove_separation(self):
        levels=[3]*9+[8]+[3]*9+[8]+[3]*9
        for kw in [{'omit':[14]},{'invalid':[14]}]:
            events,_=inventory(self.observations(levels,**kw),self.policy)
            self.assertEqual(len(events),1)
            self.assertTrue(events[0]['has_observation_gaps'])
            self.assertFalse(events[0]['complete_observed_cluster'])

    def test_first_and_open_last_event_remain_censored(self):
        events,_=inventory(self.observations([8,9,8,6]),self.policy)
        self.assertTrue(events[0]['left_censored'])
        self.assertTrue(events[0]['right_censored'])
        self.assertFalse(events[0]['complete_observed_cluster'])
        # The transition into a high reading cannot count as a low interval.
        events,_=inventory(self.observations([3]*8+[8]),self.policy)
        self.assertTrue(events[0]['left_censored'])

    def test_different_datums_never_supply_each_others_boundaries(self):
        rows=self.observations([3]*9,datum='old')
        rows.update(self.observations([None]*9+[8],datum='new'))
        events,_=inventory(rows,self.policy)
        self.assertEqual(len(events),1)
        self.assertTrue(events[0]['left_censored'])

    def test_repeated_forecasts_do_not_multiply_events_or_certify_independence(self):
        obs=self.observations([3]*9+[8]*3+[3]*9)
        points=[]
        for _ in range(10):
            points.append({'station_id':'86510000','datum_id':'test','status':'matched','observed_m':8,'valid_at':(self.start+timedelta(minutes=135)).isoformat(),'model_id':'model','model_version':'v1','minimum_verified_lead_h':1,'goal_eligible':True,'hit_within_050m':True})
        records=[{'kind':'flood_event_policy','recorded_at':self.start.isoformat(),'sha256':'policy','payload':self.policy}]
        report=audit(records,obs,points,self.start+timedelta(days=1))
        self.assertEqual(report['observed_clusters'],1)
        self.assertEqual(report['certified_independent_events'],0)
        self.assertEqual(report['scorecard'][0]['goal_eligible_pairs'],10)
        self.assertEqual(len(report['scorecard']),1)
        self.assertFalse(report['goal_achieved'])
