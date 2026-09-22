"""Independent raw-field reconciliation and coverage-only audit of reserved ANA data."""
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import hashlib, json, math, xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
DATA=ROOT/'outputs/pesquisa-cobertura-reserva-2022-20260922'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def usable(row):
    if row is None or row.get('CQ_NivelFinal')!='Dado aprovado': return False
    try: return math.isfinite(float(row['NivelFinal']))
    except (KeyError,TypeError,ValueError): return False

def main():
    hh=json.loads((DATA/'artifact-hashes.json').read_text())
    for h in hh: assert sha(DATA/h['file'])==h['sha256'],h['file']
    manifest=json.loads((DATA/'collection-manifest.json').read_text()); parsed={}
    for source in manifest:
        assert source['status'] in ('preserved','reused')
        p=Path(source['file']);p=p if p.is_absolute() else DATA/p
        assert sha(p)==source['sha256']
        root=ET.parse(p).getroot()
        parsed[str(p.resolve())]=[{c.tag.rsplit('}',1)[-1]:c.text for c in e} for e in root.iter() if e.tag.rsplit('}',1)[-1]=='DadosHidrometereologicos']
    rows=[json.loads(s) for s in (DATA/'rows-all-qc.jsonl').read_text().splitlines()]
    keys=set();refs=set();references=0;by_station={}
    for r in rows:
        raw={k:v for k,v in r.items() if k!='source_references'};key=(r['CodEstacao'],r['DataHora'])
        assert key not in keys;keys.add(key)
        for ref in r['source_references']:
            fk=(ref['source_file'],ref['source_record_index']); assert fk not in refs;refs.add(fk)
            assert parsed[ref['source_file']][ref['source_record_index']-1]==raw
            assert sha(Path(ref['source_file']))==ref['source_sha256']
            references+=1
        t=datetime.fromisoformat(r['DataHora']);assert t.tzinfo is None
        by_station.setdefault(r['CodEstacao'],{})[t]=raw
    assert sum(len(v) for v in parsed.values())==references
    summary=json.loads((DATA/'coverage-summary.json').read_text())
    assert summary['source_references']==references and summary['unique_unconflicted_rows']==len(rows)
    start=datetime(2022,4,28);stop=datetime(2022,7,1);evstart=datetime(2022,5,1)
    grid={start+timedelta(minutes=15*i) for i in range(6144)}
    gaps=[];checks=0
    for s in summary['stations']:
        station=s['station']; rr=by_station[station]
        assert set(rr)==grid
        assert len(rr)==s['records']==6144
        assert dict(Counter(str(r.get('CQ_NivelFinal')) for r in rr.values()))==s['level_qc_counts']
        assert sum(usable(r) for r in rr.values())==s['approved_level_records']
        assert sum(usable(r) and t>=evstart and t.minute==t.second==0 for t,r in rr.items())==s['evaluation_exact_hour_approved_level_records']
        checks+=5
        active=[]
        for t in sorted(grid):
            if not usable(rr[t]): active.append(t)
            elif active:
                gaps.append(dict(station=station,first=active[0].isoformat(),last=active[-1].isoformat(),quarter_records=len(active)));active=[]
        if active:gaps.append(dict(station=station,first=active[0].isoformat(),last=active[-1].isoformat(),quarter_records=len(active)))
    mucum=by_station['86510000'];linha=by_station['86472000']
    origins=[evstart+timedelta(hours=i) for i in range(1464)]
    availability=[]
    for h in range(1,13):
        oo=[t for t in origins if t+timedelta(hours=h)<stop]
        base=lambda t:usable(mucum.get(t-timedelta(minutes=15)))
        truth=lambda t:usable(mucum.get(t+timedelta(hours=h)))
        high=lambda t:truth(t) and float(mucum[t+timedelta(hours=h)]['NivelFinal'])>=700
        availability.append(dict(horizon_h=h,scheduled_with_target_inside_window=len(oo),
            usable_exact_targets=sum(truth(t) for t in oo),usable_base_and_target=sum(base(t) and truth(t) for t in oo),
            usable_high_targets=sum(high(t) for t in oo),usable_base_and_high_target=sum(base(t) and high(t) for t in oo),
            no_model_inference=True))
    # Only literal availability at the frozen delay queries; no predictions or interpolation.
    current_inputs=dict(origins=len(origins),mucum_base_O_minus15_usable=sum(usable(mucum.get(t-timedelta(minutes=15))) for t in origins),
        linha_current_O_minus30_usable=sum(usable(linha.get(t-timedelta(minutes=30))) for t in origins),
        linha_all_six_query_levels_usable=sum(all(usable(linha.get(t-timedelta(minutes=30)-timedelta(hours=lag))) for lag in (0,.5,1,2,4,8)) for t in origins))
    result=dict(hashes_verified=len(hh),xml_responses_verified=len(parsed),raw_rows_reconciled=len(rows),raw_references_reconciled=references,
        station_summary_checks=checks,availability=current_inputs,horizon_coverage=availability,
        training=False,model_inference=False,model_errors_computed=False,timestamps_changed=False,
        datum_or_timezone_certified=False,goal_achieved=False)
    dump(OUT/'verification.json',result);dump(OUT/'unusable-level-runs.json',gaps)
    dump(OUT/'artifact-hashes.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'])
    print(json.dumps(result,indent=2));print('largest_unusable_runs',json.dumps(sorted(gaps,key=lambda x:x['quarter_records'],reverse=True)[:8]))

if __name__=='__main__': main()
