"""Retrospective, explicitly unverified replay of the local nowcast hypothesis."""
from bisect import bisect_right
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import numpy as np

MODEL = "mucum-hydrometry-public-v1"
TZ = ZoneInfo("America/Sao_Paulo")
ASSUMED_PUBLICATION_LAG = 45 * 60
MAX_READING_AGE = 60 * 60
MAX_CORRECTION = .5


def stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def metrics(rows, field):
    if not rows:
        return {"n": 0}
    errors = np.asarray([row[field]-row["observed_m"] for row in rows])
    return {"n": len(rows), "mae_m": float(np.abs(errors).mean()),
            "bias_m": float(errors.mean()), "maxAbs_m": float(np.abs(errors).max()),
            "hits50cm": int(np.sum(np.abs(errors) <= .5)),
            "hitRate50cm": float(np.mean(np.abs(errors) <= .5))}


def main():
    source, output = map(Path, sys.argv[1:3])
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((source / "manifest.json").read_text())
    truth_body = (source / "sgb-mucum-cota.csv").read_bytes()
    if hashlib.sha256(truth_body).hexdigest() != manifest["truthSha256"]:
        raise ValueError("SGB snapshot checksum mismatch")
    truth = {}
    for row in csv.DictReader(truth_body.decode().splitlines(), delimiter=";"):
        t = datetime.fromisoformat(row["data_hora_medicao"]).replace(tzinfo=TZ).timestamp()
        truth[t] = float(row["indice"])/100
    hours = sorted(truth)
    pairs, exclusions = [], []
    for entry in manifest["rounds"]:
        body = (source / entry["file"]).read_bytes()
        if hashlib.sha256(body).hexdigest() != entry["sha256"]:
            raise ValueError("Forecast snapshot checksum mismatch")
        forecast = json.loads(body)["projection"]
        if forecast.get("modelVersion") != MODEL:
            continue
        reference = stamp(forecast["referenceAt"])
        issued = stamp(forecast["generatedAt"])
        index = bisect_right(hours, issued-ASSUMED_PUBLICATION_LAG)-1
        if index < 0 or not reference < hours[index] <= issued or issued-hours[index] > MAX_READING_AGE:
            exclusions.append({"referenceAt": forecast["referenceAt"], "reason": "No eligible SGB sample under assumed 45-minute lag"})
            continue
        observed_at = hours[index]
        first = forecast["models"][0]["points"][0]
        expected = forecast["observation"]["level"] + (first["level"]-forecast["observation"]["level"]) * (observed_at-reference)/(stamp(first["timestamp"])-reference)
        correction = max(-MAX_CORRECTION, min(MAX_CORRECTION, truth[observed_at]-expected))
        for point in forecast["models"][0]["points"]:
            target = stamp(point["timestamp"])
            if target not in truth:
                continue
            pairs.append({"referenceAt": forecast["referenceAt"], "generatedAt": forecast["generatedAt"],
                          "targetAt": point["timestamp"], "nominalLeadHours": point["nominalLeadHours"],
                          "assumedKnownObservationAt": datetime.fromtimestamp(observed_at, TZ).isoformat(),
                          "observed_m": truth[target], "original_m": point["level"],
                          "candidate_m": point["level"]+correction, "correction_m": correction,
                          "archiveReceiptKey": forecast.get("archiveReceiptKey")})
    report = {"schema": "radar-nowcast-retrospective-replay/v1", "status": "development_only",
              "publicModelUnchanged": True, "sourceManifestSha256": hashlib.sha256((source / "manifest.json").read_bytes()).hexdigest(),
              "assumedSgbPublicationLagMinutes": 45, "maxObservationAgeMinutes": 60,
              "eligiblePairs": len(pairs), "excludedIssues": exclusions,
              "byNominalHorizon": {str(h): {"original": metrics([r for r in pairs if r["nominalLeadHours"] == h], "original_m"),
                                          "candidate": metrics([r for r in pairs if r["nominalLeadHours"] == h], "candidate_m")}
                                   for h in range(1, 7)},
              "atLeast7m": {"original": metrics([r for r in pairs if r["observed_m"] >= 7], "original_m"),
                            "candidate": metrics([r for r in pairs if r["observed_m"] >= 7], "candidate_m")},
              "limitations": ["SGB CSV was downloaded after the forecast issues; historical availability, QC and revisions are unverified.",
                              "A 45-minute publication lag is assumed, not observed. This is not a prospective validation.",
                              "Overlapping hourly targets are not independent flood events and do not establish the 98% objective."]}
    with (output / "pairs.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
        writer.writeheader(); writer.writerows(pairs)
    (output / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(output), "pairs": len(pairs), "horizons": report["byNominalHorizon"]}))


if __name__ == "__main__":
    main()
