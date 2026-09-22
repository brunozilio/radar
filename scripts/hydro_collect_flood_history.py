"""Collect a bounded, public ANA flood-history audit dataset; never train a model.

Only the five specified station/month windows are requested. Existing raw files
are reused only when their manifests match their URL and SHA-256. Naive ANA
timestamps are preserved: UTC conversion explicitly assumes UTC-03, pending
official verification. No datum consistency or target eligibility is inferred.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/historico-cheias-mucum"
STATION = "86510000"
ENDPOINT = "https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais"
WINDOWS = {
    "2020-jun-jul": [("2020-06-01", "2020-06-30"), ("2020-07-01", "2020-07-20")],
    "2024-mar-mai": [("2024-03-01", "2024-03-31"), ("2024-04-01", "2024-04-30"), ("2024-05-01", "2024-05-31")],
}
VARIABLES = ("ChuvaAcumAdotada", "ChuvaFinal", "NivelSensor", "NivelDisplay", "NivelManual", "NivelFinal", "VazaoFinal")
ASSUMED_TZ = dt.timezone(dt.timedelta(hours=-3))
APPROVED = "Dado aprovado"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def fetch(start, end, offline=False):
    args = dict(codEstacao=STATION, dataInicio=dt.date.fromisoformat(start).strftime("%d/%m/%Y"), dataFim=dt.date.fromisoformat(end).strftime("%d/%m/%Y"))
    url = ENDPOINT + "?" + urllib.parse.urlencode(args)
    stem = f"ana-{STATION}-{start}--{end}"
    raw = OUT / "raw" / (stem + ".xml")
    metadata = OUT / "raw" / (stem + ".manifest.json")
    entry = {"station": STATION, "start_inclusive": start, "end_inclusive": end, "url": url, "raw_file": str(raw.relative_to(OUT)), "access": "public_read_only"}
    body = None
    if raw.exists() and metadata.exists():
        old = json.loads(metadata.read_text())
        candidate = raw.read_bytes()
        if old.get("url") == url and old.get("sha256") == hashlib.sha256(candidate).hexdigest():
            body = candidate
            entry.update(old)
            entry["cache_used"] = True
            entry["cache_verified_at"] = now()
    if body is None and offline:
        entry.update(status="unavailable", error="No verified cached response; offline mode", checked_at=now())
        return [], entry
    if body is None:
        entry["retrieved_at"] = now()
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Radar-Hydrology-Research/1.0", "Accept": "application/xml,text/xml"})
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read(32 * 1024 * 1024 + 1)
                entry.update(http_status=response.status, content_type=response.headers.get("Content-Type"), last_modified=response.headers.get("Last-Modified"), etag=response.headers.get("ETag"), final_url=response.url)
            if len(body) > 32 * 1024 * 1024:
                raise ValueError("Response exceeds bounded 32 MiB limit")
            raw.write_bytes(body)
            entry.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), cache_used=False)
        except Exception as exc:
            entry.update(status="unavailable", error=f"{type(exc).__name__}: {exc}")
            dump(metadata, entry)
            return [], entry
    try:
        xml = ET.fromstring(body)
        errors = [node.text for node in xml.iter() if node.tag.split("}")[-1] == "Error" and node.text]
        rows = [{child.tag.split("}")[-1]: child.text for child in node} for node in xml.iter() if node.tag.split("}")[-1] == "DadosHidrometereologicos"]
        entry.update(status="data" if rows else "no_data", rows=len(rows), source_errors=errors)
        if errors:
            entry["status"] = "source_error"
            rows = []
    except ET.ParseError as exc:
        entry.update(status="invalid_xml", error=str(exc))
        rows = []
    dump(metadata, entry)
    return [dict(row, source_file=entry["raw_file"]) for row in rows], entry


def write_csv(path, rows, fields):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summarize(event, windows, raw_rows):
    start = dt.datetime.fromisoformat(windows[0][0])
    stop = dt.datetime.fromisoformat(windows[-1][1]) + dt.timedelta(days=1)
    by_time = collections.defaultdict(list)
    rejected_rows = []
    for row in raw_rows:
        try:
            timestamp = dt.datetime.fromisoformat(row.get("DataHora") or "")
            if timestamp.tzinfo is not None or not start <= timestamp < stop or row.get("CodEstacao") != STATION:
                raise ValueError("Timestamp outside expected naive window, or station mismatch")
            by_time[timestamp].append(row)
        except ValueError as exc:
            rejected_rows.append(dict(row, rejection_reason=str(exc)))
    (OUT / event).mkdir(exist_ok=True)
    target = OUT / event
    with (target / "rows-all-qc.jsonl").open("w") as handle:
        for row in raw_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (target / "rows-rejected.jsonl").open("w") as handle:
        for row in rejected_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    rows, duplicates, conflicts = [], 0, []
    for timestamp, group in sorted(by_time.items()):
        signatures = {tuple((key, row.get(key)) for key in ("CodEstacao", "DataHora") + VARIABLES + tuple("CQ_" + v for v in VARIABLES)) for row in group}
        duplicates += len(group) - 1
        conflict = len(signatures) > 1
        if conflict:
            conflicts.append(timestamp.isoformat())
        row = dict(group[0])
        row.update(timestamp_source_naive=timestamp.isoformat(), timestamp_utc_assuming_minus03=timestamp.replace(tzinfo=ASSUMED_TZ).astimezone(dt.timezone.utc).isoformat(), timezone_status="ASSUMED_UTC_MINUS03_NOT_VERIFIED", datum_status="UNVERIFIED", duplicate_conflict=conflict)
        value = number(row.get("NivelFinal"))
        row["level_m"] = value / 100 if value is not None else None
        row["level_partition"] = "approved" if value is not None and row.get("CQ_NivelFinal") == APPROVED and not conflict else "suspect" if value is not None and row.get("CQ_NivelFinal") == "Dado suspeito" and not conflict else "unavailable_or_other_qc"
        rows.append(row)
    fields = ["CodEstacao", "timestamp_source_naive", "timestamp_utc_assuming_minus03", "timezone_status", "datum_status", "NivelFinal", "level_m", "CQ_NivelFinal", "duplicate_conflict", "source_file"]
    for partition in ("approved", "suspect", "unavailable_or_other_qc"):
        write_csv(target / f"levels-{partition}.csv", [row for row in rows if row["level_partition"] == partition], fields)
    variable_stats = {}
    for variable in VARIABLES:
        finite = [number(row.get(variable)) for row in rows if number(row.get(variable)) is not None]
        variable_stats[variable] = {"numeric_count": len(finite), "missing_or_nonfinite": len(rows) - len(finite), "qc_counts": dict(collections.Counter(row.get("CQ_" + variable) or "MISSING_QC" for row in rows)), "approved_numeric_count": sum(number(row.get(variable)) is not None and row.get("CQ_" + variable) == APPROVED and not row["duplicate_conflict"] for row in rows), "min": min(finite) if finite else None, "max": max(finite) if finite else None}
    grid = []
    t = start
    indexed = {dt.datetime.fromisoformat(row["timestamp_source_naive"]): row for row in rows}
    while t < stop:
        row = indexed.get(t)
        grid.append((t, "no_record" if row is None else row["level_partition"]))
        t += dt.timedelta(minutes=15)
    gaps = []
    for t, status in grid:
        if status == "approved":
            continue
        if gaps and gaps[-1]["status"] == status and dt.datetime.fromisoformat(gaps[-1]["end_source_naive"]) + dt.timedelta(minutes=15) == t:
            gaps[-1]["end_source_naive"] = t.isoformat()
            gaps[-1]["slots_15min"] += 1
        else:
            gaps.append({"start_source_naive": t.isoformat(), "end_source_naive": t.isoformat(), "slots_15min": 1, "status": status})
    write_csv(target / "gaps-15min.csv", gaps, ["start_source_naive", "end_source_naive", "slots_15min", "status"])
    summary = {"station": STATION, "window_id": event, "start_inclusive_source_naive": start.isoformat(), "stop_exclusive_source_naive": stop.isoformat(), "role": "AUDIT_ONLY_UNASSIGNED_NO_TRAIN_TEST_ALLOCATION", "timestamp_timezone": "Assumed UTC-03; official convention pending; preserve original naive timestamp", "datum": "Unverified; gauge zero, relocation and validity metadata pending", "rating_curve_and_cross_sections": "Not collected; official validity metadata pending", "raw_rows": len(raw_rows), "unique_valid_timestamp_rows": len(rows), "rejected_rows": len(rejected_rows), "duplicate_rows": duplicates, "conflicting_timestamps": conflicts, "nominal_grid_minutes": 15, "expected_grid_slots": len(grid), "grid_counts": dict(collections.Counter(status for _, status in grid)), "off_grid_records": sum(t.minute % 15 != 0 or t.second != 0 for t in indexed), "level_counts": dict(collections.Counter(row["level_partition"] for row in rows)), "variables": variable_stats, "interpolation": "NONE", "next_official_source": "https://www.snirh.gov.br/hidroweb/serieshistoricas?codigoEstacao=86510000", "official_geometry_api_docs": "https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html"}
    dump(target / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Only read SHA-verified cache; perform zero network requests")
    args = parser.parse_args()
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    manifests, summaries = [], []
    for event, windows in WINDOWS.items():
        rows = []
        for start, end in windows:
            collected, manifest = fetch(start, end, offline=args.offline)
            manifests.append(manifest)
            rows.extend(collected)
            print(json.dumps({"window": [start, end], "status": manifest["status"], "rows": len(collected), "cache": manifest.get("cache_used", False)}), flush=True)
        summaries.append(summarize(event, windows, rows))
    dump(OUT / "manifest.json", {"created_at": now(), "offline": args.offline, "station": STATION, "requests": manifests})
    dump(OUT / "catalog.json", {"created_at": now(), "eligibility": "AUDIT_ONLY; no model training or train/test assignment", "windows": summaries})
    lines = ["# Histórico de cheias de Muçum — auditoria", "", "Dados oficiais ANA preservados em XML. Níveis aprovados convertidos de cm para m; suspeitos separados. Nenhuma interpolação, treino ou divisão treino/teste executada.", "", "| Janela | Registros | Níveis aprovados | Suspeitos | Sem registro na grade de 15 min | Nível ausente/outro QC |", "|---|---:|---:|---:|---:|---:|"]
    for item in summaries:
        counts = item["level_counts"]
        lines.append(f"| {item['window_id']} | {item['unique_valid_timestamp_rows']} | {counts.get('approved', 0)} | {counts.get('suspect', 0)} | {item['grid_counts'].get('no_record', 0)} | {counts.get('unavailable_or_other_qc', 0)} |")
    lines += ["", "Os horários originais não informam fuso. A coluna UTC usa hipótese explícita UTC−03, ainda não verificada; não integrar com outras fontes até confirmar. O datum, zero da régua, relocação, curvas-chave válidas e seções transversais continuam pendentes. Dado aprovado pela fonte não demonstra datum consistente entre anos.", "", "As janelas são lotes para auditoria, sem atribuição a treino ou teste. Os primeiros meses permitem investigar aquecimento, mas nenhuma adequação ao treino foi concluída. A grade de 15 min é nominal para medir cobertura; ausências não são zeros.", "", "Cada pasta contém summary.json (variável/QC), levels-approved.csv, levels-suspect.csv, levels-unavailable_or_other_qc.csv, gaps-15min.csv e rows-all-qc.jsonl. Os manifestos individuais registram URL, instante, resposta, bytes e hash SHA-256.", "", "Próxima fonte em caso de falha/lacuna: [Hidroweb da estação](https://www.snirh.gov.br/hidroweb/serieshistoricas?codigoEstacao=86510000). Para curvas e perfis: [API ANA oficial](https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html), com acesso autorizado. Não foi contornada autenticação. O endpoint legado tem aviso de descontinuação; manter os dados baixados imutáveis.", "", "Reprodução sem rede: `python3 scripts/hydro_collect_flood_history.py --offline`. A execução padrão reutiliza apenas cache com URL e hash verificados."]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({item["window_id"]: item["level_counts"] for item in summaries}), flush=True)


if __name__ == "__main__":
    main()
