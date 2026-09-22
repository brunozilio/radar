"""Append-only local receipts and forecast verification; never backdates issuance.

Files are hash-linked and checked on every read. This detects local edits but is
not an external timestamp authority. Historical imports never count toward the
prospective accuracy goal. Exact timestamps and an approved observation are
required; interpolated or carried-forward levels are not used as truth.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'outputs/monitoramento-prospectivo'
TZ = timezone(timedelta(hours=-3))


def now():
    return datetime.now(timezone.utc)


def timestamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError('Explicit timezone required')
    return parsed.astimezone(timezone.utc)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_records(root):
    result = []
    previous = None
    for i, path in enumerate(sorted((root/'records').glob('*.json')), 1):
        wrapper = json.loads(path.read_text())
        record, sha = wrapper['record'], wrapper['sha256']
        if digest(canonical(record)) != sha or record['previous_sha256'] != previous or record['sequence'] != i:
            raise ValueError(f'Ledger integrity failure: {path.name}')
        if path.name != f'{i:08d}-{sha}.json':
            raise ValueError('Ledger filename mismatch')
        result.append({**record, 'sha256': sha})
        previous = sha
    return result


def append(root, kind, payload):
    (root/'records').mkdir(parents=True, exist_ok=True)
    with (root/'.write.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        records = read_records(root)
        at = now()
        if records and at < timestamp(records[-1]['recorded_at']):
            raise ValueError('Clock moved backwards')
        record = {'schema': 1, 'sequence': len(records)+1, 'kind': kind,
                  'recorded_at': at.isoformat(), 'previous_sha256': records[-1]['sha256'] if records else None,
                  'payload': payload}
        sha = digest(canonical(record))
        path = root/'records'/f'{record["sequence"]:08d}-{sha}.json'
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=root/'records',suffix='.pending',delete=False) as f:
                temporary=Path(f.name)
                f.write(canonical({'record':record, 'sha256':sha}) + b'\n')
                f.flush();os.fsync(f.fileno())
            # Atomic publication, without overwriting another issue. Readers
            # never see a partly written JSON while collection runs concurrently.
            os.link(temporary,path)
        finally:
            if temporary is not None:temporary.unlink(missing_ok=True)
        return {**record, 'sha256': sha}


def store_blob(root, content, suffix):
    sha = digest(content)
    (root/'blobs').mkdir(parents=True, exist_ok=True)
    path = root/'blobs'/f'{sha}.{suffix}'
    if path.exists():
        if digest(path.read_bytes()) != sha:
            raise ValueError('Existing blob changed')
    else:
        with path.open('xb') as f:
            f.write(content);f.flush();os.fsync(f.fileno())
    return str(path.relative_to(root)), sha


def parse_ana(content, station, datum, timezone_verified=False, datum_verified=False):
    result = []
    seen = {}
    for element in ET.fromstring(content).iter():
        if element.tag.split('}')[-1] != 'DadosHidrometereologicos':
            continue
        raw = {el.tag.split('}')[-1]:el.text for el in element}
        if raw.get('CodEstacao') != station:
            continue
        try:
            at = datetime.fromisoformat(raw['DataHora'])
        except (KeyError, TypeError, ValueError):
            continue
        if at.tzinfo is None:
            at = at.replace(tzinfo=TZ)
        try:
            level = float(raw['NivelFinal'])/100
            if not math.isfinite(level):
                level = None
        except (TypeError, ValueError, KeyError):
            level = None
        item = {'station_id':station, 'datum_id':datum, 'valid_at':at.isoformat(),
                       'level_m':level, 'quality':raw.get('CQ_NivelFinal'),
                       'timezone_verified':timezone_verified, 'datum_verified':datum_verified,
                       'raw_time':raw['DataHora'], 'raw_level_cm':raw.get('NivelFinal')}
        if at in seen:
            if seen[at] != item:
                raise ValueError('Conflicting observations at the same station/time')
            continue
        seen[at]=item
        result.append(item)
    return result


def capture_ana(root, station='86510000'):
    if station != '86510000':
        raise ValueError('This collector is scoped to the Muçum verification gauge')
    at = now().astimezone(TZ)
    params = {'codEstacao':station, 'dataInicio':(at-timedelta(days=1)).strftime('%d/%m/%Y'),
              'dataFim':at.strftime('%d/%m/%Y')}
    url = 'https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as response:
        content = response.read(5_000_001)
        status = response.status
    if len(content)>5_000_000:
        raise ValueError('Unexpectedly large ANA response')
    datum = 'ANA:86510000:reference-unverified'
    observations = parse_ana(content, station, datum)
    if not observations:
        raise ValueError('ANA returned no hydrometric rows; HTTP success is not data success')
    path, sha = store_blob(root, content, 'xml')
    # The receipt itself, not a caller-supplied timestamp, establishes collection.
    return append(root, 'observation_receipt', {'url':url,'http_status':status,'blob':path,
                  'blob_sha256':sha,'station_id':station,'observations':observations,
                  'note':'UTC-3 convention and physical gauge datum still need independent documentation.'})


def is_retired_model(model_id):
    return model_id.lower().startswith(('hge', 'arno'))


def register_forecast(root, packet, archival=False):
    if is_retired_model(packet.get('model_id', '')):
        raise ValueError('HGE/ARNO removed; only Radar forecasts may be issued or imported')
    for forbidden in ['issued_at', 'recorded_at', 'goal_achieved']:
        if forbidden in packet:
            raise ValueError(f'Caller cannot set {forbidden}')
    at = now()
    ref = timestamp(packet['reference_at'])
    produced = timestamp(packet['produced_at'])
    if produced>at or ref>at:
        raise ValueError('Forecast source timestamp is in the future')
    if not packet.get('model_version') or not packet.get('model_id'):
        raise ValueError('Model identity/version required')
    known = {r['sha256']:r for r in read_records(root)}
    receipts = packet.get('input_receipts', [])
    if not archival:
        cycle_id=packet.get('cycle_sha256')
        if cycle_id:
            cycle=known.get(cycle_id)
            if not cycle or cycle['kind']!='cycle_started' or timestamp(cycle['recorded_at'])>produced:
                raise ValueError('Forecast must link to a cycle started before production')
        if not receipts:
            raise ValueError('Live forecast requires previously recorded input receipts')
        for receipt in receipts:
            if receipt not in known or known[receipt]['kind'] not in ['observation_receipt','input_receipt']:
                raise ValueError('Unknown input receipt')
            prior = known[receipt]
            blob = prior['payload']['blob']
            if digest((root/blob).read_bytes()) != prior['payload']['blob_sha256']:
                raise ValueError('Input source hash mismatch')
        # Model artifacts are copied into a sealed issue packet as hashes/metadata;
        # this program cannot independently establish training-data correctness.
        if not packet.get('model_artifacts'):
            raise ValueError('Model artifacts/provenance required')
        for artifact in packet['model_artifacts']:
            if digest(Path(artifact['path']).read_bytes()) != artifact['sha256']:
                raise ValueError('Model artifact hash mismatch')
        if timestamp(packet['training_cutoff'])>produced:
            raise ValueError('Model training cutoff after production')
    seen = set()
    for point in packet['points']:
        valid = timestamp(point['valid_at'])
        horizon = float(point['nominal_lead_h'])
        if horizon<=0 or abs((valid-ref).total_seconds()/3600-horizon)>1e-6:
            raise ValueError('Horizon/reference mismatch')
        if valid in seen or not math.isfinite(float(point['level_m'])):
            raise ValueError('Duplicate target or nonfinite forecast')
        seen.add(valid)
    if not seen:
        raise ValueError('Empty forecast packet')
    return append(root, 'archival_forecast_import' if archival else 'forecast_issue', packet)


def import_saved(root, radar_dir):
    radar = json.loads((radar_dir/'previsao-atualizada.json').read_text())
    for model_id, source, metadata, produced, points in [
        ('radar_arvores_previsao_chuva',radar_dir/'previsao-atualizada.json',radar,radar['issued_at'],
         [{'valid_at':p['time'],'nominal_lead_h':p['lead_h'],'level_m':p['forecast_m']} for p in radar['forecast']]),

    ]:
        content = source.read_bytes()
        path, sha = store_blob(root, content, 'json')
        # Idempotent import does not generate artificial extra predictions.
        if any(r['kind']=='archival_forecast_import' and r['payload'].get('source_sha256')==sha for r in read_records(root)):
            continue
        packet = {'station_id':'86510000','datum_id':'ANA:86510000:reference-unverified',
                  'model_id':model_id,'model_version':'source-snapshot:'+sha,
                  'reference_at':metadata['origin'],'produced_at':produced,
                  'source_path':str(source.resolve()),'source_sha256':sha,'source_blob':path,
                  'input_receipts':[],'points':points,
                  'note':'Imported after original calculation. Excluded from prospective goal even if claimed production was earlier.'}
        register_forecast(root, packet, archival=True)


def latest_observations(root, records, at):
    observations = {}
    for record in records:
        if record['kind']!='observation_receipt' or timestamp(record['recorded_at'])>at:
            continue
        p = record['payload']
        if digest((root/p['blob']).read_bytes())!=p['blob_sha256']:
            raise ValueError('Observation blob changed')
        for row in p['observations']:
            valid = timestamp(row['valid_at'])
            # A future-dated measurement cannot be used as current ground truth.
            if valid>timestamp(record['recorded_at']):
                continue
            key = (row['station_id'],row['datum_id'],valid)
            observations[key] = (row,record['sha256']) # Latest revision replaces bad AND good values.
    return observations


def evaluate(root, at=None, records=None, observations=None):
    at = at or now()
    records = read_records(root) if records is None else records
    observations = latest_observations(root,records,at) if observations is None else observations
    pairs = []
    for record in records:
        if record['kind'] not in ['forecast_issue','archival_forecast_import'] or timestamp(record['recorded_at'])>at:
            continue
        p = record['payload']
        issued = timestamp(record['recorded_at'])
        for point in p['points']:
            valid = timestamp(point['valid_at'])
            reasons = []
            effective = (valid-issued).total_seconds()/3600
            effective_bucket = math.floor(effective)
            if record['kind']=='archival_forecast_import':reasons.append('archival_import')
            if p.get('manual_revision'):reasons.append('manual_revision_outside_scheduled_sample')
            if effective<=0:reasons.append('registered_after_target')
            if effective_bucket<1 or effective_bucket>12:reasons.append('outside_1_to_12h_actual_lead_buckets')
            observed = observations.get((p['station_id'],p['datum_id'],valid))
            row = {'forecast_record':record['sha256'],'evidence_kind':record['kind'],'station_id':p['station_id'],'datum_id':p['datum_id'],'model_id':p['model_id'],'model_version':p['model_version'],
                   'registered_at':record['recorded_at'],'valid_at':point['valid_at'],
                   'nominal_lead_h':point['nominal_lead_h'],'actual_lead_h':effective,
                   'minimum_verified_lead_h':effective_bucket,
                   'shorter_than_nominal_lead':effective<float(point['nominal_lead_h']),
                   'forecast_m':point['level_m'],'observed_m':None,'abs_error_m':None,
                   'observation_record':None,'goal_eligible':False,'hit_within_050m':None,'flood_event_id':None}
            if valid>at:
                status='not_due'
            elif observed is None:
                status='missing_exact_observation'
            else:
                obs,receipt = observed
                row['observation_record']=receipt
                if obs['level_m'] is None or obs['quality']!='Dado aprovado':
                    status='invalid_or_unapproved_observation'
                else:
                    status='matched'
                    row['observed_m']=obs['level_m']
                    row['abs_error_m']=abs(float(point['level_m'])-obs['level_m'])
                    row['hit_within_050m']=row['abs_error_m']<=.5
                    if not obs.get('timezone_verified'):reasons.append('timezone_unverified')
                    if not obs.get('datum_verified'):reasons.append('datum_unverified')
                    row['goal_eligible']=not reasons
            row['status']=status
            row['exclusion_reasons']=','.join(reasons)
            pairs.append(row)
    return pairs


def report(root):
    from hydro_cadence import audit as cadence_audit
    from hydro_flood_events import audit as flood_event_audit
    from hydro_verification_metrics import error_metrics,diagnostic_scorecard
    at=now();records=[r for r in read_records(root) if timestamp(r['recorded_at'])<=at]
    observations=latest_observations(root,records,at)
    all_pairs = evaluate(root,at,records,observations)
    pairs = [p for p in all_pairs if not is_retired_model(p['model_id'])]
    floods=flood_event_audit(records,observations,pairs,at)
    out = root/'reports'/at.strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    (out/'code').mkdir()
    report_code=[]
    for source in [Path(__file__),ROOT/'scripts/hydro_cadence.py',ROOT/'scripts/hydro_flood_events.py',ROOT/'scripts/hydro_verification_metrics.py']:
        content=source.read_bytes();target=out/'code'/source.name
        target.write_bytes(content)
        report_code.append({'path':str(target.relative_to(out)),'sha256':digest(content)})
    if pairs:
        with (out/'verification.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
    score = []
    groups=defaultdict(list)
    for p in pairs:
        if p['goal_eligible']:
            groups[(p['model_id'],p['model_version'],p['minimum_verified_lead_h'],'all')].append(p)
            if p['observed_m']>=7:
                groups[(p['model_id'],p['model_version'],p['minimum_verified_lead_h'],'level_ge_7m')].append(p)
    for key, group in sorted(groups.items()):
        score.append({'model_id':key[0],'version':key[1],'lead_h':key[2],'regime':key[3],
                      **error_metrics(group)})
    diagnostics=diagnostic_scorecard(pairs)
    (out/'diagnostic-scorecard.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    summary={'created_at':at.isoformat(),'records':len(records),'ledger_tip_sha256':records[-1]['sha256'] if records else None,'report_code':report_code,
             'retired_model_pairs_preserved':sum(is_retired_model(p['model_id']) for p in all_pairs),
             'pairs':len(pairs),'status_counts':dict(Counter(p['status'] for p in pairs)),
             'goal_eligible_pairs':sum(p['goal_eligible'] for p in pairs),'goal_achieved':False,
             'scorecard':score,'limitations':['Local hash chain is not an external time authority.',
                 'Lead h means at least h and less than h+1 real hours before target; never the nominal calculation label.',
                 'No event independence or sample-size sufficiency is certified by this report.',
                 'Imported old calculations never count toward the prospective target.',
                 'Delivery coverage is audited separately from paired prediction accuracy; scheduler execution is not inferred from pair count.']}
    coverage=cadence_audit(records,at)
    coverage_display='ainda não calculável' if coverage['coverage_percent'] is None else f"{coverage['coverage_percent']:.2f}%"
    summary['delivery_coverage']=coverage
    summary['flood_event_inventory']=floods
    (out/'flood-events.json').write_text(json.dumps(floods,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (out/'cadence.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    matched=[p for p in pairs if p['status']=='matched']
    table='\n'.join(f"| {p['model_id']} | {timestamp(p['valid_at']).astimezone(TZ):%d/%m %H:%M} | {p['forecast_m']:.2f} | {p['observed_m']:.2f} | {p['abs_error_m']:.2f} | {p['exclusion_reasons']} |" for p in matched)
    (out/'report.md').write_text(f'''# Verificação das previsões — registro local

Gerado em {summary['created_at']}. Pares elegíveis à meta: **{summary['goal_eligible_pairs']}**.
A meta de 98% não foi demonstrada.
Este relatório acompanha somente Radar. Modelos retirados permanecem nos recibos históricos.

`diagnostic-scorecard.json` detalha MAE, viés, P90/P98 e erro máximo, separando
importações antigas das emissões registradas. Valores com fuso/datum pendentes
podem aparecer no diagnóstico, mas não são promovidos a evidência da meta.
O arquivo também mostra alvos únicos e episódios; pares horários dependentes
não fornecem por si só um intervalo de confiança nem eventos independentes.

Episódios observados agrupados: {floods.get('observed_clusters',0)};
com começo/fim observados e sem lacunas: {floods.get('complete_observed_clusters',0)}.
Eventos independentes certificados: {floods['certified_independent_events']}.
Veja `flood-events.json`. O agrupamento diagnóstico não comprova independência;
várias previsões durante a mesma cheia não viram várias cheias na contagem.

Cobertura de entrega: {coverage['complete_windows']}/{coverage['closed_windows']}
janelas horárias encerradas e avaliáveis. Percentual: {coverage_display}.
Sem janelas encerradas, não se informa 100% nem 0%. Veja `cadence.json` para
tentativas ausentes, falhas, entregas incompletas e limitações. Registro iniciado
sem fechamento não comprova processo ativo. Cobertura não é precisão do nível.

| Modelo | Horário BRT | Previsto (m) | Observado (m) | Erro (m) | Exclusões da meta |
|---|---|---:|---:|---:|---|
{table}

Importações de cálculos antigos ficam disponíveis para diagnóstico e nunca são
convertidas retroativamente em previsões registradas antes do evento. O horário real
do registro é independente da referência temporal usada no cálculo. Apenas medições
no horário exato, aprovadas pela origem, entram nos pares; não há interpolação.

O placar usa antecedência efetiva mínima: 1h significa de 1 até menos de 2 horas
reais entre registro e alvo, e assim por diante. A antecedência nominal é preservada
apenas para auditoria. Isso não permite contar uma previsão de 40 minutos como 1h.
Para avaliar 12h, o ciclo precisa emitir também alvos com ao menos 12h restantes.

Pendências de fuso/referência da régua, revisões e fontes indisponíveis são explícitas.
O registro é local, encadeado por hashes e sem sobrescrita pela ferramenta; não é
carimbo de tempo externo nem prova de disponibilidade de todos os ciclos horários.
''',encoding='utf-8')
    print(json.dumps({'report':str(out),'summary':summary},ensure_ascii=False))
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger',type=Path,default=DEFAULT)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('capture-ana')
    imp=commands.add_parser('import-saved');imp.add_argument('--radar',type=Path,required=True)
    pub=commands.add_parser('issue');pub.add_argument('--packet',type=Path,required=True)
    commands.add_parser('report')
    args=parser.parse_args()
    if args.command=='capture-ana':print(json.dumps(capture_ana(args.ledger),ensure_ascii=False))
    elif args.command=='import-saved':import_saved(args.ledger,args.radar)
    elif args.command=='issue':print(json.dumps(register_forecast(args.ledger,json.loads(args.packet.read_text())),ensure_ascii=False))
    else:report(args.ledger)
