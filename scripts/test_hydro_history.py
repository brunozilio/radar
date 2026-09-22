import hashlib,json,tempfile,unittest
from pathlib import Path
import numpy as np
import hydro_history as h

class HistoryTests(unittest.TestCase):
    def test_overlap_invalid_revision_wins_and_old_rows_survive(self):
        seed={'times':np.array([0,86400,10*86400]),'level':np.array([1.,2.,3.])}
        got=h.merge_arrays(seed,{10*86400:[np.nan],20*86400:[4.]},['level'])
        np.testing.assert_array_equal(got['times'],[0,86400,10*86400,20*86400])
        np.testing.assert_allclose(got['level'],[1,2,np.nan,4],equal_nan=True)
        self.assertNotIn(15*86400,got['times'])

    def weather(self,times,values):
        return [{'latitude':-29.,'longitude':-51.,'utc_offset_seconds':-10800,'hourly_units':{'precipitation':'mm'},'hourly':{'time':times,'precipitation':values}} for _ in range(5)]

    def test_weather_accumulates_beyond_week_and_preserves_null_revision(self):
        before=self.weather(['2026-01-01T00:00','2026-01-10T00:00'],[5,10])
        after=self.weather(['2026-01-10T00:00','2026-01-20T00:00'],[None,2])
        got=h.merge_weather(before,after)[0]['hourly']
        self.assertEqual(got['precipitation'],[5,None,2])
        self.assertEqual(got['time'],['2026-01-01T00:00','2026-01-10T00:00','2026-01-20T00:00'])
        after[0]['longitude']=-50.
        with self.assertRaises(ValueError):h.merge_weather(before,after)

    def xml(self,t,quality='Dado aprovado',station='86510000'):
        return f'<DadosHidrometereologicos><CodEstacao>{station}</CodEstacao><DataHora>{t}</DataHora><NivelFinal>123</NivelFinal><CQ_NivelFinal>{quality}</CQ_NivelFinal><VazaoFinal>100</VazaoFinal><ChuvaFinal>2</ChuvaFinal></DadosHidrometereologicos>'

    def test_ana_future_and_identity_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'a.xml';p.write_text('<root>'+self.xml('2026-01-01T00:00')+self.xml('2026-01-02T00:00')+'</root>')
            rows,n=h.ana_rows(p,'86510000',h.stamp('2026-01-01T12:00'))
            self.assertEqual(n,1);self.assertEqual(len(rows),1);self.assertAlmostEqual(next(iter(rows.values()))[0],1.23)
            with self.assertRaises(ValueError):h.ana_rows(p,'123',h.stamp('2026-01-01T12:00'))

    def fixture(self,root,name,day):
        out=root/name;(out/'raw').mkdir(parents=True);at=f'2026-01-{day:02d}T12:00:00-03:00';items=[]
        def add(filename,body,source):
            p=out/'raw'/filename;p.write_text(body);items.append({'file':filename,'source':source,'sha256':h.sha(p),'collected_at':at})
        add('ana-86510000-fresh.xml','<root>'+self.xml(f'2026-01-{day:02d}T10:00')+'</root>','ANA')
        for plant in ['julho','monte','castro']:
            td=[f'{day:02d}/01/2026 10:00:00','0','0','90','0','0','0','100']
            add(f'ceran-{plant}-fresh.html','<tr>'+''.join(f'<td>{v}</td>' for v in td)+'</tr>','CERAN')
        for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
            add(f'weather-{model}.json',json.dumps(self.weather([f'2026-01-{day:02d}T10:00'],[2])),'Open-Meteo')
        h.dump(out/'collection-manifest.json',items);return out

    def test_checkpoint_survives_rollover_and_rejects_tampering_and_rollback(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);baseline=root/'baseline';(baseline/'raw').mkdir(parents=True)
            t=np.array([h.stamp('2026-01-01T10:00')])
            np.savez(baseline/'raw/normalized-86510000.npz',times=t,**{k:np.array([1.]) for k in h.FIELDS})
            np.savez(baseline/'telemetria.npz',times=t,**{f'{p}:{k}':np.array([50.]) for p in ['julho','monte','castro'] for k in ['Q','I']})
            out1=self.fixture(root,'first',10);one=h.build(out1,root/'index',baseline)
            out2=self.fixture(root,'second',20);two=h.build(out2,root/'index',baseline)
            self.assertEqual(h.read_current(root/'index'),two)
            a=np.load(two/'ana-86510000.npz');self.assertEqual(len(a['times']),3)
            c=np.load(two/'ceran-julho.npz');np.testing.assert_array_equal(c['Q'],[50,100,100])
            w=json.loads((two/'weather-gfs_seamless.json').read_text());self.assertEqual(len(w[0]['hourly']['time']),2)
            older=self.fixture(root,'older',15)
            with self.assertRaises(ValueError):h.build(older,root/'index',baseline)
            self.assertEqual(h.read_current(root/'index'),two)
            (two/'ana-86510000.npz').write_bytes(b'changed')
            with self.assertRaises(ValueError):h.read_current(root/'index')

    def test_explicit_grid_transition_is_hash_bound_and_preserves_time_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);baseline=root/'baseline';(baseline/'raw').mkdir(parents=True)
            t=np.array([h.stamp('2026-01-01T10:00')])
            np.savez(baseline/'raw/normalized-86510000.npz',times=t,**{k:np.array([1.]) for k in h.FIELDS})
            np.savez(baseline/'telemetria.npz',times=t,**{f'{p}:{k}':np.array([50.]) for p in ['julho','monte','castro'] for k in ['Q','I']})
            one=h.build(self.fixture(root,'first',10),root/'index',baseline)
            out=self.fixture(root,'second',11);name='weather-icon_global.json';path=out/'raw'/name
            new=self.weather(['2026-01-10T10:00','2026-01-11T10:00'],[2,3]);new[0]['longitude']=-50.;h.dump(path,new)
            manifest=json.loads((out/'collection-manifest.json').read_text())
            next(r for r in manifest if r['file']==name)['sha256']=h.sha(path);h.dump(out/'collection-manifest.json',manifest)
            policy=root/'transition.json';h.dump(policy,{'sources':{name:{'previous_sha256':h.sha(one/name),'new_sha256':h.sha(path),'expected_locations':[[r['latitude'],r['longitude']] for r in new]}}})
            two=h.build(out,root/'index',baseline,policy)
            self.assertTrue(next(r for r in h.verify(two)['audit'] if r['source']==name)['explicit_grid_transition'])
            self.assertEqual(json.loads((one/name).read_text())[0]['longitude'],-51.)
            # Reusing the one-off approval against a different prior snapshot fails.
            third=self.fixture(root,'third',12)
            with self.assertRaises(ValueError):h.build(third,root/'index',baseline,policy)
            self.assertEqual(h.read_current(root/'index'),two)

if __name__=='__main__':unittest.main()
