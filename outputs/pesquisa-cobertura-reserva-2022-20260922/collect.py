"""Literal ANA coverage collection for reserved 2022 windows; no model access."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from urllib.request import urlopen
from urllib.parse import urlencode
import hashlib, json, subprocess, xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
STATIONS = ('86510000', '86472000')
START, STOP = datetime(2022, 4, 28), datetime(2022, 7, 1)
WINDOWS = [('2022-04-28', '2022-04-30'), ('2022-05-01', '2022-05-31'), ('2022-06-01', '2022-06-30')]
PROBE = ROOT/'outputs/pesquisa-fase-horaria-2022-20260921'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
def rows_of(body):
    tree = ET.fromstring(body)
    return ([{c.tag.split('}')[-1]: c.text for c in e} for e in tree.iter()
             if e.tag.split('}')[-1] == 'DadosHidrometereologicos'],
            [e.text for e in tree.iter() if e.tag.split('}')[-1] == 'Error'])

def inventory():
    paths = subprocess.check_output(['rg', '--files', 'outputs', '-g', '*.xml'], cwd=ROOT, text=True).splitlines()
    result = []
    for name in sorted(paths):
        p = ROOT/name
        if OUT in p.parents or not (any(s in p.name for s in STATIONS) or '2022' in name): continue
        try:
            rows, errors = rows_of(p.read_bytes())
            selected = [r for r in rows if r.get('CodEstacao') in STATIONS]
            times = [r['DataHora'] for r in selected if r.get('DataHora')]
            overlap = sum(START <= datetime.fromisoformat(t) < STOP for t in times)
            result.append(dict(file=name, rows=len(selected), first=min(times) if times else None,
                               last=max(times) if times else None, overlap_rows=overlap, errors=errors))
        except (ET.ParseError, ValueError) as e:
            result.append(dict(file=name, inspection_error=str(e)))
    return result

def collect():
    assert not (OUT/'collection-plan.json').exists(), 'Existing attempt: inspect before any retry.'
    reserved = ROOT/'docs/radar-historical-evaluation-reservation.json'
    inv = inventory(); write(OUT/'existing-xml-inventory.json', inv)
    overlaps = [x for x in inv if x.get('overlap_rows', 0)]
    assert all((ROOT/x['file']).resolve() == (PROBE/'response.xml').resolve() for x in overlaps), overlaps
    requests = []
    for station in STATIONS:
        for begin, end in WINDOWS:
            args = dict(codEstacao=station, dataInicio=datetime.fromisoformat(begin).strftime('%d/%m/%Y'),
                        dataFim=datetime.fromisoformat(end).strftime('%d/%m/%Y'))
            requests.append(dict(station=station, start=begin, end=end,
                file=f'raw/ana-{station}-{begin}--{end}.xml',
                url='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urlencode(args)))
    write(OUT/'collection-plan.json', dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),
        reservation_sha256=sha(reserved), scope='Coverage/QC only; no training, inference or model selection.',
        timestamp_policy='Literal source timestamps. Working expected grid is not timezone certification.',
        windows=WINDOWS, stations=STATIONS, max_new_gets=6, automatic_retries=0, requests=requests,
        reused_probe=str(PROBE/'response.xml'), expected_probe_overlap_rows=96))
    (OUT/'raw').mkdir()
    manifest = []
    for req in requests:
        m = {**req, 'requested_at_utc':datetime.now(timezone.utc).isoformat(), 'status':'started'}
        manifest.append(m); write(OUT/'collection-manifest.json', manifest)
        try:
            with urlopen(req['url'], timeout=45) as res:
                body = res.read(8*1024*1024+1)
                m.update(http_status=res.status, headers=dict(res.headers))
            assert len(body) <= 8*1024*1024
            p = OUT/req['file']; p.write_bytes(body)
            m.update(status='preserved', collected_at_utc=datetime.now(timezone.utc).isoformat(),
                     bytes=len(body), sha256=sha(p))
            rows, errors = rows_of(body)
            m.update(rows=len(rows), source_errors=errors)
            assert all(r['CodEstacao'] == req['station'] and req['start'] <= r['DataHora'][:10] <= req['end'] for r in rows)
        except Exception as e:
            m.update(status='failed', error=f'{type(e).__name__}: {e}', finished_at_utc=datetime.now(timezone.utc).isoformat())
        write(OUT/'collection-manifest.json', manifest)
        print(json.dumps({k:m.get(k) for k in ('station','start','end','status','rows','error')}, ensure_ascii=False), flush=True)
    probe_meta = json.loads((PROBE/'source.json').read_text())
    assert sha(PROBE/'response.xml') == probe_meta['sha256']
    manifest.append(dict(file=str(PROBE/'response.xml'), station='86510000', start='2022-05-04', end='2022-05-04',
        status='reused', url=probe_meta['url'], sha256=probe_meta['sha256'], original_metadata=str(PROBE/'source.json')))
    write(OUT/'collection-manifest.json', manifest)
    audit(manifest)

def audit(manifest):
    grouped = defaultdict(list)
    total_refs = 0
    for m in manifest:
        if m['status'] not in ('preserved','reused'): continue
        p = Path(m['file']); p = p if p.is_absolute() else OUT/p
        assert sha(p) == m['sha256']
        rows, _ = rows_of(p.read_bytes())
        for i,r in enumerate(rows, 1):
            assert r['CodEstacao'] == m['station'] and START <= datetime.fromisoformat(r['DataHora']) < STOP
            ref = dict(source_file=str(p.resolve()), source_sha256=m['sha256'], source_record_index=i)
            grouped[(r['CodEstacao'],r['DataHora'])].append((r,ref)); total_refs += 1
    conflicts = []; unified = []
    for key, refs in sorted(grouped.items()):
        versions = {json.dumps(r,sort_keys=True,ensure_ascii=False) for r,_ in refs}
        if len(versions) != 1:
            conflicts.append(dict(station=key[0], time_original=key[1], versions=[dict(fields=r, **ref) for r,ref in refs]))
            continue
        r = dict(refs[0][0]); r['source_references'] = [ref for _,ref in refs]; unified.append(r)
    write(OUT/'conflicts.json', conflicts)
    (OUT/'rows-all-qc.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in unified))
    summaries = []; daily = []; gaps = []
    for station in STATIONS:
        rr = [r for r in unified if r['CodEstacao']==station]
        times = {datetime.fromisoformat(r['DataHora']):r for r in rr}
        assert all(t.tzinfo is None for t in times), 'Source timestamp changed contract; inspect before alignment.'
        expected = [START+timedelta(minutes=15*i) for i in range(int((STOP-START).total_seconds()/900))]
        missing = [t for t in expected if t not in times]
        run = []
        for t in missing:
            if run and t-run[-1] != timedelta(minutes=15):
                gaps.append(dict(station=station, first=run[0].isoformat(), last=run[-1].isoformat(), records=len(run))); run=[]
            run.append(t)
        if run: gaps.append(dict(station=station,first=run[0].isoformat(),last=run[-1].isoformat(),records=len(run)))
        approved = lambda r: r.get('CQ_NivelFinal')=='Dado aprovado' and r.get('NivelFinal') not in (None,'')
        for day in (START+timedelta(days=i) for i in range((STOP-START).days)):
            dayrows = [(t,r) for t,r in times.items() if day <= t < day+timedelta(days=1)]
            daily.append(dict(station=station, date=day.date().isoformat(), records=len(dayrows),
                exact_hour_records=sum(t.minute==0 and t.second==0 for t,r in dayrows),
                approved_level_records=sum(approved(r) for t,r in dayrows),
                exact_hour_approved_level_records=sum(t.minute==0 and t.second==0 and approved(r) for t,r in dayrows)))
        summaries.append(dict(station=station, records=len(rr), first=min(times).isoformat() if times else None,
            last=max(times).isoformat() if times else None, minute_counts=dict(Counter(t.minute for t in times)),
            second_counts=dict(Counter(t.second for t in times)), expected_quarter_records=len(expected),
            missing_quarter_timestamps=len(missing), off_grid_records=sum(t.minute%15!=0 or t.second!=0 for t in times),
            level_qc_counts=dict(Counter(str(r.get('CQ_NivelFinal')) for r in rr)),
            missing_level_values=sum(r.get('NivelFinal') in (None,'') for r in rr),
            approved_level_records=sum(approved(r) for r in rr),
            exact_hour_approved_level_records=sum(t.minute==0 and t.second==0 and approved(r) for t,r in times.items()),
            evaluation_exact_hour_approved_level_records=sum(t>=datetime(2022,5,1) and t.minute==0 and t.second==0 and approved(r) for t,r in times.items())))
    write(OUT/'daily-coverage.json',daily); write(OUT/'missing-quarter-runs.json',gaps)
    result = dict(stations=summaries, source_references=total_refs, unique_unconflicted_rows=len(unified),
        duplicate_extra_references=total_refs-len(grouped), conflicting_timestamp_groups=len(conflicts),
        failed_requests=sum(m['status']=='failed' for m in manifest), model_inference=False, training=False,
        timestamps_modified=False, timezone_certified=False, datum_certified=False, reservation_still_excludes_fitting=True)
    write(OUT/'coverage-summary.json',result)
    write(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*'))
                                     if p.is_file() and p.name!='artifact-hashes.json'])
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': collect()
