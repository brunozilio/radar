import unittest, json, csv, math
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import xml.etree.ElementTree as ET
import analyze as a

class VerificationTests(unittest.TestCase):
 def setUp(self):
  self.issue={'forecast_record':'x','registered_at':'2026-09-21T20:02:00-03:00'}
  self.point={'valid_at':'2026-09-21T22:00:00-03:00','forecast_m':16.95}
  self.cut=a.ledger.timestamp('2026-09-21T22:25:00-03:00')
  self.observations={a.ledger.timestamp(self.point['valid_at']):{'quality':'Dado aprovado','level_m':16.45}}
 def test_exact_threshold_before_rounding(self):
  self.assertTrue(a.hit(16.95,16.45));self.assertTrue(a.hit(15.95,16.45));self.assertFalse(a.hit(16.9500001,16.45))
 def test_missing_is_not_interpolated(self):
  old={a.ledger.timestamp('2026-09-21T21:45:00-03:00'):{'quality':'Dado aprovado','level_m':16.32}}
  self.assertEqual(a.pair(self.issue,self.point,old,self.cut)['status'],'missing_exact_observation')
 def test_future_does_not_score_even_with_observation(self):
  r=a.pair(self.issue,self.point,self.observations,a.ledger.timestamp('2026-09-21T21:59:00-03:00'))
  self.assertEqual(r['status'],'not_due');self.assertIsNone(a.stats([r])['accuracy_percent'])
 def test_unapproved_revision_invalidates(self):
  self.observations[next(iter(self.observations))]['quality']='Dado suspeito'
  self.assertEqual(a.pair(self.issue,self.point,self.observations,self.cut)['status'],'invalid_or_unapproved_observation')
 def test_real_lead_not_nominal(self):
  r=a.pair(self.issue,self.point,self.observations,self.cut)
  self.assertEqual(r['minimum_verified_lead_h'],1);self.assertAlmostEqual(r['actual_lead_h'],118/60)
 def test_after_target_not_scored(self):
  self.issue['registered_at']='2026-09-21T22:01:00-03:00'
  self.assertEqual(a.pair(self.issue,self.point,self.observations,self.cut)['status'],'registered_after_target')
 def test_independent_raw_xml_and_csv_recount(self):
  xml={}
  for element in ET.parse(a.OUT/'ana-mucum.xml').getroot().iter():
   if element.tag.split('}')[-1]=='DadosHidrometereologicos':
    r={child.tag.split('}')[-1]:child.text for child in element}
    if r.get('CodEstacao')=='86510000' and r.get('CQ_NivelFinal')=='Dado aprovado' and r.get('NivelFinal'):
     xml[datetime.fromisoformat(r['DataHora']).replace(tzinfo=a.TZ).isoformat()]=Decimal(r['NivelFinal'])/100
  with (a.OUT/'verification-local.csv').open() as f: rows=list(csv.DictReader(f))
  selected=[r for r in rows if r['cohort']=='scheduled_local' and r['status']=='matched']
  errors=[]
  for r in selected:
   self.assertEqual(Decimal(r['observed_m']),xml[r['valid_at']]);e=Decimal(r['forecast_m'])-xml[r['valid_at']]
   self.assertAlmostEqual(float(e),float(r['error_m']));errors.append(e)
  summary=json.loads((a.OUT/'summary.json').read_text())['cohorts']['scheduled_local']
  self.assertEqual(len(errors),summary['n']);self.assertEqual(sum(abs(e)<=Decimal('.5') for e in errors),summary['hits'])
  self.assertAlmostEqual(float(sum(abs(e) for e in errors)/len(errors)),summary['mae_m'])
  self.assertEqual(len({(r['forecast_record'],r['valid_at']) for r in selected}),len(selected))
 def test_site_revisions_do_not_inflate_primary_count(self):
  s=json.loads((a.OUT/'summary.json').read_text())['cohorts']
  self.assertEqual(s['site_latest_rounds']['unique_targets'],1);self.assertEqual(s['site_latest_rounds']['n'],1)
  self.assertEqual(s['site_preserved_revisions_incomplete']['unique_targets'],1)
  self.assertEqual(s['observed_only_diagnostic']['n'],0)

if __name__=='__main__':unittest.main(verbosity=2)
