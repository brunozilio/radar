"""Exact-hour observed inputs for the separate no-rain Muçum experiment.

This module only reads local source files. Historical observations are a revised
retrospective sample, not a reconstruction of operational publication times.
No interpolation, carry-forward, rain imputation or training occurs here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

TZ = ZoneInfo('America/Sao_Paulo')
STATIONS = ('86510000', '86472000', '86472600', '86500000')
PLANTS = {'JIUHQJ': ('julho', '14 DE JULHO', '99'),
          'JIUHMC': ('monte', 'MONTE CLARO', '98'),
          'JIUHCA': ('castro', 'CASTRO ALVES', '97')}
KEYS = tuple(f'{code}:H' for code in STATIONS) + tuple(
    f'{plant}:{field}' for plant in ('julho', 'monte', 'castro') for field in ('Q', 'I'))
CONTRACT = 'mucum-exact-hour-level-flow-retrospective/v1'


def epoch(value: str) -> float:
    parsed = datetime.fromisoformat(value)
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=TZ)).timestamp()


def number(value) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) and result >= 0 else np.nan
    except (TypeError, ValueError):
        return np.nan


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iso(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def parse_ana(path: Path, station: str):
    """Keep literal exact hours; rejected revisions remain NaN."""
    rows, flags = {}, Counter()
    for _, element in ET.iterparse(path, events=['end']):
        if element.tag.split('}')[-1] != 'DadosHidrometereologicos':
            continue
        row = {child.tag.split('}')[-1]: child.text for child in element}
        if row.get('CodEstacao') != station:
            raise ValueError(f'ANA station identity mismatch: {path.name}')
        at = epoch(row['DataHora'])
        if at % 3600:
            flags['non_hourly_records_omitted'] += 1
            element.clear()
            continue
        value = number(row.get('NivelFinal')) / 100
        if row.get('CQ_NivelFinal') != 'Dado aprovado':
            value = np.nan
            flags['level_quality_rejected'] += 1
        if at in rows and not np.allclose(rows[at], value, equal_nan=True):
            raise ValueError(f'Conflicting ANA duplicate: {path.name} {iso(at)}')
        rows[at] = value
        element.clear()
    return {station + ':H': rows}, flags


def parse_ons(path: Path):
    rows = {key: {} for key in KEYS if not key.endswith(':H')}
    flags = Counter()
    with path.open() as stream:
        for row in csv.DictReader(stream, delimiter=';'):
            identity = row['id_reservatorio'].strip()
            if identity not in PLANTS:
                raise ValueError('Unexpected ONS reservoir identity')
            plant, name, code = PLANTS[identity]
            if row['nom_reservatorio'].strip() != name or number(row['cod_usina']) != int(code):
                raise ValueError('ONS reservoir name/code mismatch')
            at = epoch(row['din_instante'])
            if at % 3600:
                flags['non_hourly_records_omitted'] += 1
                continue
            q, inflow = number(row.get('val_vazaodefluente')), number(row.get('val_vazaoafluente'))
            components = [number(row.get(field)) for field in
                          ('val_vazaoturbinada', 'val_vazaovertida', 'val_vazaooutrasestruturas')]
            # A contradictory zero is unavailable, not replaced by the sum.
            # Other residuals remain diagnostic: ONS fields can use different conventions.
            if q == 0 and all(math.isfinite(v) for v in components) and sum(components) > 1:
                flags[f'{plant}:zero_flow_positive_components_rejected'] += 1
                q = np.nan
            for field, value in [('Q', q), ('I', inflow)]:
                target = rows[f'{plant}:{field}']
                if at in target and not np.allclose(target[at], value, equal_nan=True):
                    raise ValueError(f'Conflicting ONS duplicate: {path.name} {iso(at)}')
                target[at] = value
    return rows, flags


def parse_ceran(path: Path, plant: str):
    rows = {plant + ':Q': {}, plant + ':I': {}}
    flags = Counter()
    for row in re.findall(r'<tr>(.*?)</tr>', path.read_text(), re.S):
        cells = re.findall(r'<td>(.*?)</td>', row, re.S)
        if len(cells) != 8:
            continue
        at = datetime.strptime(cells[0], '%d/%m/%Y %H:%M:%S').replace(tzinfo=TZ).timestamp()
        if at % 3600:
            flags['non_hourly_records_omitted'] += 1
            continue
        for field, value in [('Q', number(cells[7])), ('I', number(cells[3]))]:
            target = rows[plant + ':' + field]
            if at in target and not np.allclose(target[at], value, equal_nan=True):
                raise ValueError(f'Conflicting CERAN duplicate: {path.name} {iso(at)}')
            target[at] = value
    return rows, flags


def baseline_receipts(raw: Path):
    receipts = {}
    for name in ('ana-initial-manifest.json', 'ana-expanded-manifest.json',
                 'ana-2025-manifest.json', 'ons-manifest.json'):
        path = raw / name
        if not path.is_file():
            continue
        for item in json.loads(path.read_text()):
            filename = item.get('file') or f"ana-{item['station']}.xml"
            receipts[filename] = {**item, 'manifest_path': str(path.resolve())}
    return receipts


def load_dataset(baseline: Path, collections=()):
    """Return (times, data, metadata), with raw-source and receipt arrays in data.

    received_at:<key> means the selected file's actual local receipt, never an
    invented publication time. Historical values with unknown receipts use NaN.
    source_index:<key> indexes metadata.sources; absent cells use -1.
    """
    baseline = Path(baseline)
    sources, values = [], {key: {} for key in KEYS}
    receipts = baseline_receipts(baseline / 'raw')
    jobs = []
    for station in STATIONS:
        for suffix in ('-2025', ''):
            path = baseline / 'raw' / f'ana-{station}{suffix}.xml'
            if path.is_file():
                jobs.append((path, 'ANA', station, receipts.get(path.name, {})))
    for path in sorted((baseline / 'raw').glob('DADOS_HIDROLOGICOS_HO_*-ceran.csv')):
        jobs.append((path, 'ONS', None, receipts.get(path.name, {})))
    collection_jobs = []
    for directory in collections:
        directory = Path(directory)
        manifest = directory / 'collection-manifest.json'
        for item in json.loads(manifest.read_text()):
            name = item['file']
            match = re.fullmatch(r'ana-(\d+)-fresh.xml', name)
            ceran = re.fullmatch(r'ceran-(julho|monte|castro)-fresh.html', name)
            if 'error' in item or not ((match and match[1] in STATIONS) or ceran):
                continue
            if not item.get('sha256') or not item.get('collected_at'):
                raise ValueError('Current source requires a hash and actual receipt timestamp')
            identity = match[1] if match else ceran[1]
            collection_jobs.append((directory / 'raw' / name, 'ANA' if match else 'CERAN', identity,
                                    {**item, 'manifest_path': str(manifest.resolve())}))
    jobs.extend(sorted(collection_jobs, key=lambda job: epoch(job[3]['collected_at'])))
    for path, provider, identity, receipt in jobs:
        digest = sha(path)
        expected = receipt.get('sha256') or receipt.get('sha256_filtered')
        if expected and expected != digest:
            raise ValueError(f'Raw source hash mismatch: {path}')
        received = epoch(receipt['collected_at'] if receipt.get('collected_at') else receipt['at']) if receipt.get('collected_at') or receipt.get('at') else np.nan
        parsed, flags = (parse_ana(path, identity) if provider == 'ANA' else
                         parse_ceran(path, identity) if provider == 'CERAN' else parse_ons(path))
        index = len(sources)
        sources.append({'path': str(path.resolve()), 'sha256': digest, 'provider': provider,
                        'identity': identity, 'url': receipt.get('url'),
                        'receipt_manifest': receipt.get('manifest_path'),
                        'received_at': iso(received) if math.isfinite(received) else None,
                        'original_hash_verified': bool(expected), 'flags': flags})
        for key, records in parsed.items():
            for at, value in records.items():
                if math.isfinite(received) and at > received:
                    flags['future_observations_rejected'] += 1
                    continue
                previous = values[key].get(at)
                if (previous and math.isfinite(previous[1]) and
                        (not math.isfinite(received) or received < previous[1])):
                    flags['older_or_unknown_receipt_revisions_rejected'] += 1
                    continue
                if previous and not np.allclose(previous[0], value, equal_nan=True):
                    flags['revised_or_cross_provider_values'] += 1
                # Keep later collected revisions, including invalid ones. Different
                # ONS/CERAN measurement semantics are declared in the manifest.
                values[key][at] = (value, received, index)
    observed = [at for records in values.values() for at in records]
    if not observed:
        raise ValueError('No exact-hour source records')
    times = np.arange(min(observed), max(observed) + 1, 3600, dtype=float)
    data, coverage = {}, {}
    for key in KEYS:
        rows = [values[key].get(at, (np.nan, np.nan, -1)) for at in times]
        array = np.asarray(rows, dtype=float)
        data[key], data['received_at:' + key], data['source_index:' + key] = array.T
        valid = np.isfinite(data[key])
        coverage[key] = {'valid_hours': int(valid.sum()), 'total_hours': len(times),
                         'first_valid': iso(times[valid][0]) if valid.any() else None,
                         'last_valid': iso(times[valid][-1]) if valid.any() else None}
    metadata = {'schema': 1, 'contract': CONTRACT, 'created_at': datetime.now(timezone.utc).isoformat(),
                'time_basis': 'UTC epoch seconds, exact source timestamps only; naive source clocks interpreted as America/Sao_Paulo',
                'keys': list(KEYS), 'units': {key: 'm' if key.endswith(':H') else 'm3/s' for key in KEYS},
                'sources': sources, 'coverage': coverage,
                'start': iso(times[0]), 'end': iso(times[-1]), 'hours': len(times),
                'complete_current_hours': int(np.all(np.isfinite(np.column_stack([data[k] for k in KEYS])), axis=1).sum()),
                'limitations': [
                    'Historical files are retrospective and can include later revisions. This does not certify operational causal availability.',
                    'received_at is the actual local file receipt when known, not observation time or initial source publication time.',
                    'ANA values retain station-specific gauge references; datum stability is not independently certified.',
                    'ONS clock denotes hourly interval end; CERAN recent readings may be instantaneous. Cross-provider equivalence is not certified.',
                    'Rain, NWP, interpolation, carry-forward and synthetic replacements are absent.',
                    'A zero ONS defluence contradicted by positive components is rejected, never replaced with component sum.',
                ], 'trained': False, 'promoted': False}
    return times, data, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--collection', action='append', type=Path, default=[])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    times, data, metadata = load_dataset(args.baseline, args.collection)
    args.out.mkdir(parents=True, exist_ok=False)
    dataset = args.out / 'exact-hour-level-flow.npz'
    np.savez_compressed(dataset, times=times, **data)
    metadata['dataset_sha256'] = sha(dataset)
    metadata['script_sha256'] = sha(Path(__file__))
    (args.out / 'manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(dataset), 'hours': len(times), 'complete_current_hours': metadata['complete_current_hours'], 'coverage': metadata['coverage']}, indent=2))


if __name__ == '__main__':
    main()
