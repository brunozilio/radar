"""Evaluate the preregistered two-gauge ridge candidate, without publishing it."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from hydro_history import ana_rows
from hydro_propagation_model import fit_ridge, infer_delta, metrics, score

ROOT = Path(__file__).resolve().parents[1]
STATIONS = ("86510000", "86472600")
TRAIN_END = datetime(2025, 10, 1, 3, tzinfo=timezone.utc).timestamp()
VALID_END = datetime(2026, 7, 1, 3, tzinfo=timezone.utc).timestamp()
TEST_END = datetime(2026, 9, 21, 3, tzinfo=timezone.utc).timestamp()
EMBARGO = 33 * 3600
ALPHAS = (1, 10, 100, 1000)
FILES = {
    "86510000": (
        "outputs/historico-cheias-mucum/raw/ana-86510000-2024-03-01--2024-03-31.xml",
        "outputs/historico-cheias-mucum/raw/ana-86510000-2024-04-01--2024-04-30.xml",
        "outputs/historico-cheias-mucum/raw/ana-86510000-2024-05-01--2024-05-31.xml",
        "outputs/radar-insumos-observados-junho2024-20260922/raw/ana-86510000-2024-06-12--2024-06-14.xml",
        "outputs/pesquisa-mucum-junho2024-20260922/raw/ana-86510000-20240615-20240621.xml",
    ),
    "86472600": (
        "outputs/radar-insumos-2024-hidrologia-20260921/raw/ana-86472600-2024-03-29--2024-03-31.xml",
        "outputs/radar-insumos-2024-hidrologia-20260921/raw/ana-86472600-2024-04-01--2024-04-30.xml",
        "outputs/radar-insumos-2024-hidrologia-20260921/raw/ana-86472600-2024-05-01--2024-05-01.xml",
        "outputs/radar-insumos-observados-junho2024-20260922/raw/ana-86472600-2024-06-12--2024-06-14.xml",
        "outputs/pesquisa-montante-junho2024-20260922/raw/ana-86472600-20240615-20240621.xml",
    ),
}


def epoch(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def load():
    values = {station: {} for station in STATIONS}
    hashes = {}
    for station, files in FILES.items():
        for name in files:
            path = ROOT / name
            blob = path.read_bytes()
            hashes[name] = hashlib.sha256(blob).hexdigest()
            parsed, _ = ana_rows(path, station, float("inf"), strict_quality=True)
            for t, fields in parsed.items():
                value = float(fields[0])
                if t % 3600 or not np.isfinite(value):
                    continue
                if t in values[station] and values[station][t] != value:
                    raise ValueError(f"Conflicting 2024 measurement {station} at {t}")
                values[station][t] = value
    dataset = ROOT / "outputs/propagacao-dados-20260923/exact-hour-level-flow.npz"
    hashes[str(dataset.relative_to(ROOT))] = hashlib.sha256(dataset.read_bytes()).hexdigest()
    with np.load(dataset) as data:
        for station in STATIONS:
            for t, value in zip(data["times"], data[station + ":H"]):
                if np.isfinite(value):
                    values[station][float(t)] = float(value)
    return values, hashes


def feature(values, t):
    local, santa = values[STATIONS[0]], values[STATIONS[1]]
    try:
        return np.asarray((local[t], (local[t]-local[t-3600]),
            (local[t]-local[t-7200])/2, (local[t]-local[t-21600])/6,
            santa[t], santa[t]-santa[t-3600], (santa[t]-santa[t-10800])/3), dtype=float)
    except KeyError:
        return None


def frozen_public():
    forecasts = {}
    path = ROOT / "outputs/propagacao-modelo-20260923/predictions.csv"
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["model"] == "lagged":
                forecasts[(int(row["h"]), epoch(row["origin"]))] = float(row["forecast_m"])
    return forecasts


def summary(rows, column):
    if not rows:
        return {"n": 0}
    pred = np.asarray([row[column] for row in rows])
    target = np.asarray([row["actual_m"] for row in rows])
    base = np.asarray([row["base_m"] for row in rows])
    return metrics(pred, target, base)


def main():
    output = ROOT / "outputs/candidato-duas-estacoes-20260928"
    output.mkdir(parents=True, exist_ok=False)
    values, hashes = load()
    baseline = frozen_public()
    all_times = sorted(values[STATIONS[0]])
    report = {"status": "offline_only", "promoted": False, "preregisteredRecipe": "docs/candidato-hidrometrico-2026-09-28.md",
              "inputSha256": hashes, "horizons": [], "limitations": [
                  "Historical availability of 2024 and later data at issue time was not reconstructed.",
                  "The 2024 flood episodes and later test periods were previously examined in this project.",
                  "Operational performance and the 98% accuracy objective are not established."]}
    pairs = []
    for h in range(1, 7):
        rows = []
        for t in all_times:
            x = feature(values, t)
            target = values[STATIONS[0]].get(t + h * 3600)
            if x is None or target is None:
                continue
            if t + h * 3600 < TRAIN_END:
                phase = "train"
            elif t >= TRAIN_END + EMBARGO and t + h * 3600 < VALID_END:
                phase = "validation"
            elif t >= VALID_END + EMBARGO and t + h * 3600 < TEST_END:
                phase = "test"
            elif t >= TEST_END:
                phase = "stress_current"
            else:
                continue
            rows.append((t, x, target, phase))
        X = np.stack([row[1] for row in rows]); y = np.array([row[2] for row in rows]); base = np.array([values[STATIONS[0]][row[0]] for row in rows])
        phase = np.array([row[3] for row in rows]); train = np.flatnonzero(phase == "train"); valid = np.flatnonzero(phase == "validation")
        if len(train) < 96 or len(valid) < 48:
            raise ValueError("Insufficient candidate training or validation rows")
        choices = []
        for alpha in ALPHAS:
            parameters = fit_ridge(X, y-base, train, alpha)
            predicted = base[valid] + infer_delta(parameters, X[valid])
            choices.append((score(predicted, y[valid], base[valid]), alpha))
        selected_score, alpha = min(choices, key=lambda item: (item[0], -item[1]))
        parameters = fit_ridge(X, y-base, np.r_[train, valid], alpha)
        result = {"h": h, "alpha": alpha, "validationScore": selected_score,
                  "rows": {name: int(np.sum(phase == name)) for name in ("train", "validation", "test", "stress_current")},
                  "train2024Rows": int(sum(rows[i][0] < datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() for i in train)),
                  "phases": {}}
        for name in ("test", "stress_current"):
            indices = np.flatnonzero(phase == name)
            predicted = base[indices] + infer_delta(parameters, X[indices])
            for index, forecast in zip(indices, predicted):
                t = rows[index][0]
                pairs.append({"phase": name, "h": h, "origin": datetime.fromtimestamp(t, timezone.utc).isoformat(),
                              "target": datetime.fromtimestamp(t+h*3600, timezone.utc).isoformat(),
                              "base_m": base[index], "actual_m": y[index], "candidate_m": float(forecast),
                              "public_frozen_m": baseline.get((h, t))})
            eligible = [row for row in pairs if row["phase"] == name and row["h"] == h]
            paired = [row for row in eligible if row["public_frozen_m"] is not None]
            result["phases"][name] = {"candidateNatural": summary(eligible, "candidate_m"),
                                       "candidatePaired": summary(paired, "candidate_m"),
                                       "publicPaired": summary(paired, "public_frozen_m"),
                                       "publicPairedN": len(paired)}
        report["horizons"].append(result)
    with (output / "pairs.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
        writer.writeheader(); writer.writerows(pairs)
    (output / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    for row in report["horizons"]:
        print(row["h"], row["rows"], [(name, round(entry["candidatePaired"].get("mae_m", float("nan")), 3),
              round(entry["publicPaired"].get("mae_m", float("nan")), 3)) for name, entry in row["phases"].items()])


if __name__ == "__main__":
    main()
