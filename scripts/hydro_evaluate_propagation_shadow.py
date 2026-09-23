"""Offline scoring of archived Muçum hydrometric shadow issues.

Archive timestamps and object identity are supplied by a separately verified R2
extractor. This tool checks their consistency, not the remote object's existence.
No network requests, fitting, replacement of public forecasts, or promotion.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np

from hydro_history import ana_rows
from hydro_propagation_model import CONTRACT, MODEL_VERSION, epoch, iso

SHA256 = re.compile(r"^[0-9a-f]{64}$")
RECEIPT_KEY = re.compile(r"^projection/receipts/[0-9a-fA-F-]{36}\.json$")
STATION = "86510000"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("Expected a finite numerical level")
    return float(value)


def load_observations(directory, as_of):
    """Exact approved ANA levels, never interpolated or borrowed from a station."""
    directory = Path(directory)
    name = f"ana-{STATION}-fresh.xml"
    manifest_path = directory / "collection-manifest.json"
    if not manifest_path.is_file():
        return {}, {"status": "unavailable", "reason": "collection manifest missing"}
    manifest = json.loads(manifest_path.read_text())
    matches = [row for row in manifest if row.get("file") == name]
    if len(matches) > 1:
        raise ValueError("Duplicate Muçum observation receipts")
    details = {"manifestSha256": digest(manifest_path), "station": STATION,
               "source": "ANA", "unit": "m", "quality": "Dado aprovado",
               "datum": "Same ANA station and reported gauge scale; physical datum not independently certified."}
    path = directory / "raw" / name
    if not matches or not path.is_file():
        return {}, {**details, "status": "unavailable", "reason": "Muçum source missing"}
    receipt = matches[0]
    if digest(path) != receipt.get("sha256"):
        raise ValueError("Observation source checksum mismatch")
    if receipt.get("error"):
        return {}, {**details, "status": "unavailable", "reason": "source receipt reports an error"}
    received = epoch(receipt["collected_at"])
    details.update(sourceSha256=digest(path), collectedAt=iso(received))
    if received > as_of:
        return {}, {**details, "status": "unavailable", "reason": "source received after evaluation cutoff"}
    rows, rejected_future = ana_rows(path, STATION, received, strict_quality=True)
    observations = {at: float(values[0]) for at, values in rows.items()
                    if at <= as_of and np.isfinite(values[0])}
    return observations, {**details, "status": "available", "approvedObservations": len(observations),
                          "futureSourceRowsRejected": rejected_future,
                          "naiveSourceTimezone": "America/Sao_Paulo"}


def read_issue(entry, directory, as_of):
    if not isinstance(entry, dict):
        raise ValueError("Issue index entry must be an object")
    if not RECEIPT_KEY.fullmatch(str(entry.get("evidenceReceiptKey", ""))):
        raise ValueError("Missing or invalid immutable receipt key")
    if not SHA256.fullmatch(str(entry.get("archiveSha256", ""))):
        raise ValueError("Missing or invalid immutable archive SHA-256")
    archived = epoch(entry.get("archivedAt"))
    if archived > as_of:
        raise ValueError("Archive proof is later than evaluation cutoff")
    issue_path = Path(entry["issue"])
    if not issue_path.is_absolute():
        issue_path = directory / issue_path
    body = issue_path.read_bytes()
    issue_sha = hashlib.sha256(body).hexdigest()
    if entry.get("issueSha256") is not None and entry["issueSha256"] != issue_sha:
        raise ValueError("Extracted issue checksum mismatch")
    issue = json.loads(body)
    if not isinstance(issue, dict):
        raise ValueError("Extracted issue must be a JSON object")
    if issue.get("mode") != "shadow" or issue.get("publishable") is not False:
        raise ValueError("Only non-publishable shadow issues are admissible")
    station_values = [issue[key] for key in ("station", "stationCode") if key in issue]
    if not station_values or any(value != STATION for value in station_values):
        raise ValueError("Issue station identity mismatch")
    generated = epoch(issue["generatedAt"])
    if generated > archived:
        raise ValueError("Archive timestamp precedes forecast generation")
    evidence = {"issuePath": str(issue_path.resolve()), "issueSha256": issue_sha,
                "archiveSha256": entry["archiveSha256"], "evidenceReceiptKey": entry["evidenceReceiptKey"],
                "archivedAt": iso(archived), "generatedAt": iso(generated),
                "effectiveIssuedAt": iso(max(generated, archived)),
                "archiveEvidenceStatus": "Provided by external extractor; remote authenticity is not certified by hashes alone."}
    if issue.get("status") == "unavailable":
        return [], {**evidence, "status": "unavailable", "reason": issue.get("reason")}
    if issue.get("status") != "calculated" or issue.get("contract") != CONTRACT:
        raise ValueError("Calculated issue must match the frozen hydrometric contract")
    if issue.get("modelVersion") != MODEL_VERSION or not SHA256.fullmatch(str(issue.get("modelSha256", ""))):
        raise ValueError("Calculated issue must identify the frozen model and its SHA-256")
    reference = epoch(issue["referenceAt"])
    if reference % 3600 or not 0 <= generated - reference <= 3 * 3600:
        raise ValueError("Invalid reference hour or source age")
    observation = issue["observation"]
    if epoch(observation["timestamp"]) != reference:
        raise ValueError("Reference observation timestamp mismatch")
    finite_number(observation["level"])
    points = issue.get("points")
    if not isinstance(points, list) or not points or any(not isinstance(point, dict) for point in points):
        raise ValueError("Calculated issue has no forecast points")
    expected = [lead for lead in range(1, 7) if reference + lead * 3600 > generated]
    if [point.get("nominalLeadHours") for point in points] != expected:
        raise ValueError("Forecast must contain the complete original future suffix")
    result = []
    for point in points:
        lead = point["nominalLeadHours"]
        if isinstance(lead, bool) or not isinstance(lead, int):
            raise ValueError("Nominal lead must be an integer")
        target = epoch(point["timestamp"])
        if target != reference + lead * 3600:
            raise ValueError("Target timestamp does not match original nominal lead")
        level = finite_number(point["level"])
        # Ignore claimed realLeadHours: immutable archival time is conservative.
        real_lead = (target - max(generated, archived)) / 3600
        result.append({**evidence, "modelSha256": issue["modelSha256"], "modelVersion": MODEL_VERSION,
                       "station": STATION, "referenceAt": iso(reference), "targetAt": iso(target),
                       "nominalLeadHours": lead, "realLeadHours": real_lead,
                       "realLeadBand": f"[{math.floor(real_lead)},{math.floor(real_lead) + 1})",
                       "forecastLevel": level})
    return result, {**evidence, "status": "calculated"}


def summarize(rows):
    verified = [row for row in rows if row["status"] == "verified"]
    status = Counter(row["status"] for row in rows)
    result = {"opportunities": len(rows), "verifiedPairs": len(verified),
              "future": status["future"], "unobserved": status["unobserved"],
              "hitsWithin50cm": 0, "hitRateVerified": None, "hitRateMatureOpportunities": None,
              "mae_m": None, "bias_m": None, "p90_abs_m": None, "p98_abs_m": None, "max_abs_m": None}
    if verified:
        errors = np.asarray([row["errorMetres"] for row in verified])
        absolute = abs(errors)
        hits = int(np.sum(absolute <= .50))
        result.update(hitsWithin50cm=hits, hitRateVerified=hits / len(verified),
                      mae_m=float(absolute.mean()), bias_m=float(errors.mean()),
                      p90_abs_m=float(np.quantile(absolute, .90)), p98_abs_m=float(np.quantile(absolute, .98)),
                      max_abs_m=float(absolute.max()))
    mature = status["verified"] + status["unobserved"]
    if mature:
        result["hitRateMatureOpportunities"] = result["hitsWithin50cm"] / mature
    return result


def evaluate(index_path, observations_directory, as_of, *, now=None):
    as_of = epoch(as_of)
    now = datetime.now(timezone.utc).timestamp() if now is None else epoch(now)
    if as_of > now:
        raise ValueError("Evaluation cutoff cannot be in the future")
    index_path = Path(index_path)
    entries = json.loads(index_path.read_text())
    if not isinstance(entries, list):
        raise ValueError("Issue index must be a JSON array")
    counts = Counter(totalIssues=len(entries))
    candidates, exclusions = [], []
    for index, entry in enumerate(entries):
        try:
            points, metadata = read_issue(entry, index_path.parent, as_of)
            counts[metadata["status"] + "Issues"] += 1
            if metadata["status"] == "unavailable":
                exclusions.append({"index": index, **metadata})
                continue
            counts["rawPoints"] += len(points)
            candidates.extend(points)
        except (ValueError, TypeError, KeyError, OSError, OverflowError) as exc:
            counts["malformedIssues"] += 1
            exclusions.append({"index": index, "status": "malformed", "reason": str(exc)})
    # Select the earliest admissibly archived forecast before opening truth data.
    candidates.sort(key=lambda row: (row["archivedAt"], row["generatedAt"], row["evidenceReceiptKey"], row["issueSha256"]))
    selected, seen = [], set()
    for row in candidates:
        if row["realLeadHours"] <= 0:
            counts["expiredBeforeArchivePoints"] += 1
            exclusions.append({**row, "status": "expired", "reason": "Target was reached before immutable archival evidence"})
            continue
        key = (row["modelSha256"], row["referenceAt"], row["targetAt"])
        if key in seen:
            counts["duplicatePoints"] += 1
            exclusions.append({**row, "status": "duplicate"})
            continue
        seen.add(key)
        selected.append(row)
    observations, observation_metadata = load_observations(observations_directory, as_of)
    for row in selected:
        target = epoch(row["targetAt"])
        actual = observations.get(target)
        if target > as_of:
            row.update(status="future", observedLevel=None, errorMetres=None)
        elif actual is None:
            row.update(status="unobserved", observedLevel=None, errorMetres=None)
        else:
            row.update(status="verified", observedLevel=actual, errorMetres=row["forecastLevel"] - actual)
        counts[row["status"] + "Points"] += 1
    summary = summarize(selected)
    report = {
        "schema": "radar-propagation-prospective-evaluation/v1", "asOf": iso(as_of),
        "station": STATION, "contract": CONTRACT, "mode": "offline_audit", "trained": False,
        "promoted": False, "accuracyGoalAchieved": False,
        "inputIndexSha256": digest(index_path), "observations": observation_metadata,
        "counts": {key: counts[key] for key in ("totalIssues", "calculatedIssues", "unavailableIssues", "malformedIssues",
                   "rawPoints", "duplicatePoints", "expiredBeforeArchivePoints", "futurePoints", "unobservedPoints", "verifiedPoints")},
        "summary": summary,
        "nominalHorizons": {str(lead): summarize([row for row in selected if row["nominalLeadHours"] == lead]) for lead in range(1, 7)},
        "realLeadBands": {f"[{lead},{lead+1})": summarize([row for row in selected if lead <= row["realLeadHours"] < lead+1]) for lead in range(7)},
        "highWaterAtLeast7m": summarize([row for row in selected if row["observedLevel"] is not None and row["observedLevel"] >= 7]),
        "byModelSha256": {
            model_sha: {
                "summary": summarize([row for row in selected if row["modelSha256"] == model_sha]),
                "nominalHorizons": {str(lead): summarize([row for row in selected if row["modelSha256"] == model_sha and row["nominalLeadHours"] == lead]) for lead in range(1, 7)},
                "realLeadBands": {f"[{lead},{lead+1})": summarize([row for row in selected if row["modelSha256"] == model_sha and lead <= row["realLeadHours"] < lead+1]) for lead in range(7)},
            } for model_sha in sorted({row["modelSha256"] for row in selected})
        },
        "records": selected, "excluded": exclusions,
        "limitations": [
            "Archive identity, content hash and timestamp come from the input evidence index. Their consistency is checked; remote existence/authenticity is not certified by a hash alone.",
            "Effective issue time is max(generatedAt, archivedAt). A point first archived after its target is excluded, even if generated earlier.",
            "First admissibly archived emission is selected before reading target observations; repeated emissions do not create independent cases.",
            "Only exact approved ANA 86510000 observations received by asOf are matched; missing data are never zero or hits.",
            "Consecutive hours, shared references and overlapping targets are not independent flood events. This descriptive report cannot establish the 98% goal or authorize public promotion.",
            "Source gauge datum and original remote archive timestamps require external provenance verification.",
        ],
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issues", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).isoformat())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.issues, args.observations, args.as_of)
    args.output.mkdir(parents=True, exist_ok=False)
    report_path = args.output / "evaluation.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2) + "\n")
    fields = ["modelSha256", "referenceAt", "generatedAt", "archivedAt", "effectiveIssuedAt", "targetAt",
              "nominalLeadHours", "realLeadHours", "realLeadBand", "status", "forecastLevel", "observedLevel",
              "errorMetres", "evidenceReceiptKey", "archiveSha256", "issueSha256"]
    with (args.output / "pairs.csv").open("x", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(report["records"])
    files = {path.name: digest(path) for path in sorted(args.output.iterdir()) if path.is_file()}
    (args.output / "artifact-hashes.json").write_text(json.dumps(files, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "counts": report["counts"], "summary": report["summary"], "promoted": False}))


if __name__ == "__main__":
    main()
