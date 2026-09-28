"""Frozen, rain-independent Muçum stage model with causal hydrometric lags.

This is an experimental statistical model, not a calibrated hydraulic routing
model. Lag correlations do not identify water-particle or flood-wave travel
times. Cascade dam discharges remain separate covariates; they are never added.
Training is an explicit offline command. Inference never fits or fills data.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

CONTRACT = "radar-hydrometry-propagation/v1"
MODEL_VERSION = "mucum-hydrometry-shadow-v1"
TARGET = "86510000:H"
LEVELS = (TARGET, "86472000:H", "86472600:H", "86500000:H")
FLOWS = tuple(f"{plant}:{kind}" for plant in ("julho", "monte", "castro") for kind in ("Q", "I"))
SOURCES = LEVELS[1:] + FLOWS
REQUIRED = LEVELS + FLOWS
ALPHAS = (1.0, 10.0, 100.0, 1000.0)
MAX_LAG_HOURS = 24
EMBARGO_HOURS = 33  # Maximum lookback (24 + 3) plus maximum target lead (6).


class IncompleteHydrometry(ValueError):
    """An exact observed input needed by the frozen model is unavailable."""


def epoch(value):
    if isinstance(value, (int, float, np.integer, np.floating)):
        result = float(value)
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Timestamp must include its timezone")
        result = parsed.timestamp()
    if not np.isfinite(result):
        raise ValueError("Timestamp must be finite")
    return result


def iso(value):
    return datetime.fromtimestamp(float(value), timezone.utc).isoformat()


def validate_series(times, data):
    times = np.asarray(times, dtype=float)
    if times.ndim != 1 or not len(times) or not np.isfinite(times).all():
        raise ValueError("Expected nonempty finite hourly timestamps")
    if np.any(times % 3600 != 0) or np.any(np.diff(times) != 3600):
        raise ValueError("Expected a continuous exact UTC hourly grid")
    missing = [key for key in REQUIRED if key not in data]
    if missing:
        raise IncompleteHydrometry("Missing series: " + ", ".join(missing))
    arrays = {key: np.asarray(data[key], dtype=float) for key in REQUIRED}
    if any(values.shape != times.shape for values in arrays.values()):
        raise ValueError("Every series must match the hourly timestamps")
    for key in FLOWS:
        arrays[key] = np.where(arrays[key] >= 0, arrays[key], np.nan)
    return times, arrays


def shift(values, lag):
    out = np.full(len(values), np.nan)
    if lag == 0:
        return values.copy()
    if 0 < lag < len(values):
        out[lag:] = values[:-lag]
    elif -len(values) < lag < 0:
        out[:lag] = values[-lag:]
    return out


def transformed(key, values):
    # Monotonic scale compression, identical in training and inference.
    return np.log1p(values / 1000.0) if key in FLOWS else values


def calibrate_lags(times, data, train_end, minimum_pairs=48):
    """Describe training-only statistical delay in observed first differences."""
    cutoff = epoch(train_end)
    response = data[TARGET] - shift(data[TARGET], 1)
    training = times < cutoff
    rows, selected = [], {}
    for key in SOURCES:
        values = transformed(key, data[key])
        changes = values - shift(values, 1)
        candidates = []
        for lag in range(MAX_LAG_HOURS + 1):
            predictor = shift(changes, lag)
            mask = training & np.isfinite(response) & np.isfinite(predictor)
            n = int(mask.sum())
            correlation = None
            if n >= minimum_pairs and np.std(response[mask]) > 1e-10 and np.std(predictor[mask]) > 1e-10:
                correlation = float(np.corrcoef(predictor[mask], response[mask])[0, 1])
                if not np.isfinite(correlation):
                    correlation = None
            row = {"source": key, "lagHours": lag, "pairs": n, "correlation": correlation}
            rows.append(row)
            if correlation is not None and correlation > 0:
                candidates.append(row)
        best = max(candidates, key=lambda row: (row["correlation"], -row["lagHours"])) if candidates else None
        selected[key] = {
            "lagHours": int(best["lagHours"]) if best else 0,
            "correlation": best["correlation"] if best else None,
            "pairs": best["pairs"] if best else 0,
            "informative": best is not None,
        }
    return selected, rows


def feature_matrix(data, lags, family):
    if family not in ("contemporaneous", "lagged"):
        raise ValueError("Unknown hydrometric model family")
    columns, names = [], []

    def add(name, values):
        names.append(name)
        columns.append(values)

    local = data[TARGET]
    add(TARGET, local)
    for hours in (1, 2, 6):
        add(f"{TARGET}:slope{hours}", (local - shift(local, hours)) / hours)
    for key in SOURCES:
        values = transformed(key, data[key])
        add(key, values)
        for hours in (1, 3):
            add(f"{key}:slope{hours}", (values - shift(values, hours)) / hours)
        if family == "lagged":
            lag = int(lags[key]["lagHours"])
            # At zero lag these are already present in the control model.
            if lag:
                delayed = shift(values, lag)
                add(f"{key}:lag{lag}", delayed)
                for hours in (1, 3):
                    add(f"{key}:lag{lag}:slope{hours}", (delayed - shift(values, lag + hours)) / hours)
    return np.column_stack(columns), names


def fit_ridge(features, delta, rows, alpha):
    values = features[rows]
    if not np.isfinite(values).all() or not np.isfinite(delta[rows]).all():
        raise IncompleteHydrometry("Training never imputes missing inputs or targets")
    mean = values.mean(axis=0)
    scale = values.std(axis=0)
    scale[scale < 1e-8] = 1.0
    normalized = (values - mean) / scale
    intercept = float(delta[rows].mean())
    beta = np.linalg.solve(normalized.T @ normalized + float(alpha) * np.eye(values.shape[1]), normalized.T @ (delta[rows] - intercept))
    return {
        "mean": mean.tolist(), "scale": scale.tolist(), "beta": beta.tolist(),
        "intercept": intercept, "alpha": float(alpha),
        "featureMin": values.min(axis=0).tolist(), "featureMax": values.max(axis=0).tolist(),
        "trainingRows": int(len(rows)),
    }


def infer_delta(parameters, features):
    values = np.asarray(features, dtype=float)
    mean, scale, beta = (np.asarray(parameters[key], dtype=float) for key in ("mean", "scale", "beta"))
    if values.shape[-1] != len(mean) or mean.shape != scale.shape or mean.shape != beta.shape:
        raise ValueError("Frozen model feature dimensions do not match")
    if not np.isfinite(values).all() or not np.isfinite(mean).all() or not np.isfinite(scale).all() or np.any(scale <= 0) or not np.isfinite(beta).all():
        raise IncompleteHydrometry("Frozen model requires all finite inputs and coefficients")
    result = ((values - mean) / scale) @ beta + float(parameters["intercept"])
    if not np.isfinite(result).all():
        raise ValueError("Frozen model produced a nonfinite result")
    return result


def metrics(predicted, observed, base, origin_slope=None):
    if not len(observed):
        return {"n": 0}
    errors = np.asarray(predicted) - observed
    absolute = abs(errors)
    rising, high, high7 = observed - base >= 1.0, observed >= 9.0, observed >= 7.0
    result = {
        "n": int(len(errors)), "mae_m": float(absolute.mean()),
        "rmse_m": float(np.sqrt(np.mean(errors ** 2))), "bias_m": float(errors.mean()),
        "p90_abs_m": float(np.quantile(absolute, .9)), "max_abs_m": float(absolute.max()),
        "p98_abs_m": float(np.quantile(absolute, .98)),
        "within_10cm_rate": float(np.mean(absolute <= .10)),
        "within_20cm_rate": float(np.mean(absolute <= .20)),
        "within_50cm_rate": float(np.mean(absolute <= .50)),
        "within_50cm_hits": int(np.sum(absolute <= .50)),
        "rapid_rise_n": int(rising.sum()),
        "rapid_rise_mae_m": float(absolute[rising].mean()) if rising.any() else None,
        "high_water_n": int(high.sum()),
        "high_water_mae_m": float(absolute[high].mean()) if high.any() else None,
        "water_at_least_7m_n": int(high7.sum()),
        "water_at_least_7m_mae_m": float(absolute[high7].mean()) if high7.any() else None,
        "water_at_least_7m_within_20cm_rate": float(np.mean(absolute[high7] <= .20)) if high7.any() else None,
        "water_at_least_7m_within_50cm_rate": float(np.mean(absolute[high7] <= .50)) if high7.any() else None,
    }
    if origin_slope is not None:
        masks = {"rising": origin_slope > .05, "falling": origin_slope < -.05,
                 "stable": abs(origin_slope) <= .05}
        result["originPhases"] = {
            phase: {"n": int(mask.sum()),
                    "mae_m": float(absolute[mask].mean()) if mask.any() else None,
                    "within_20cm_rate": float(np.mean(absolute[mask] <= .20)) if mask.any() else None}
            for phase, mask in masks.items()
        }
    return result


def score(predicted, observed, base):
    result = metrics(predicted, observed, base)
    return result["mae_m"] + .5 * (result["rapid_rise_mae_m"] or 0) + .5 * (result["high_water_mae_m"] or 0)


def split_rows(times, valid, horizon, train_end, validation_end, test_end, embargo_hours=EMBARGO_HOURS):
    train, validation, test = map(epoch, (train_end, validation_end, test_end))
    if not train < validation < test:
        raise ValueError("Split cutoffs must be strictly chronological")
    target_times = times + horizon * 3600
    embargo = embargo_hours * 3600
    return {
        "train": np.flatnonzero(valid & (target_times < train)),
        "validation": np.flatnonzero(valid & (times >= train + embargo) & (target_times < validation)),
        "test": np.flatnonzero(valid & (times >= validation + embargo) & (target_times < test)),
        # This event is a separate stress report, not a new fitting/selection split.
        "stress_current": np.flatnonzero(valid & (times >= test)),
    }


def fit_model(times, data, train_end, validation_end, test_end, *, dataset_metadata=None, minimum_train=96, minimum_validation=48, prediction_sink=None):
    """Offline training; validation selects parameters, test never selects them."""
    times, data = validate_series(times, data)
    train_end, validation_end, test_end = map(epoch, (train_end, validation_end, test_end))
    if not train_end < validation_end < test_end:
        raise ValueError("Split cutoffs must be strictly chronological")
    lags, lag_correlations = calibrate_lags(times, data, train_end)
    matrices = {family: feature_matrix(data, lags, family) for family in ("contemporaneous", "lagged")}
    complete = np.logical_and.reduce([np.isfinite(values).all(axis=1) for values, _ in matrices.values()])
    # All baselines/families use these identical, exactly observed origins.
    complete &= np.logical_and.reduce([np.isfinite(data[key]) for key in REQUIRED])
    local = data[TARGET]
    trend = (local - shift(local, 2)) / 2
    artifact = {
        "schemaVersion": 1, "contract": CONTRACT, "modelVersion": MODEL_VERSION,
        "targetStation": "86510000", "experimental": True, "mode": "shadow",
        "promotionEligible": False, "rainRequired": False, "forecastHorizonHours": 6,
        "maximumReferenceAgeHours": 3, "requiredSources": list(REQUIRED),
        "lagCalibrationEnd": iso(train_end), "lags": lags,
        "lagInterpretation": "Training-only statistical associations, not physical travel times; cascade flows are separate predictors, never summed.",
        "historicalAvailabilityReconstructed": False,
        "trainingCutoff": iso(train_end), "validationCutoff": iso(validation_end), "testCutoff": iso(test_end),
        "embargoHours": EMBARGO_HOURS,
        "evaluationStatus": "Retrospective development evaluation; prospective shadow validation is required before operational use.",
        "dataset": dataset_metadata or {}, "horizons": [],
    }
    evaluations, selection, predictions = [], [], []
    pending_evaluations = []
    row_membership, availability = {}, {}
    for horizon in range(1, 7):
        target = shift(local, -horizon)
        delta = target - local
        rows = split_rows(times, complete & np.isfinite(target), horizon, train_end, validation_end, test_end)
        row_membership[str(horizon)] = {phase: indices.tolist() for phase, indices in rows.items()}
        natural_masks = {
            **{family: np.isfinite(features).all(axis=1) & np.isfinite(target) for family, (features, _) in matrices.items()},
            "persistence": np.isfinite(local) & np.isfinite(target),
            "local_trend_2h": np.isfinite(local) & np.isfinite(trend) & np.isfinite(target),
        }
        availability[str(horizon)] = {
            family: {phase: int(len(indices)) for phase, indices in split_rows(times, mask, horizon, train_end, validation_end, test_end).items()}
            for family, mask in natural_masks.items()
        }
        if len(rows["train"]) < minimum_train or len(rows["validation"]) < minimum_validation:
            raise ValueError(f"Insufficient complete training/validation examples for +{horizon}h: {len(rows['train'])}/{len(rows['validation'])}")
        choices = []
        validation_predictions = {}
        for family, (features, names) in matrices.items():
            candidates = []
            for alpha in ALPHAS:
                parameters = fit_ridge(features, delta, rows["train"], alpha)
                predicted = local[rows["validation"]] + infer_delta(parameters, features[rows["validation"]])
                candidate_score = score(predicted, target[rows["validation"]], local[rows["validation"]])
                validation_metrics = metrics(predicted, target[rows["validation"]], local[rows["validation"]])
                omitted = [group for group in ("rapid_rise", "high_water") if not validation_metrics[f"{group}_n"]]
                selection.append({"h": horizon, "family": family, "alpha": alpha,
                                  "validationScore": candidate_score, "validationMetrics": validation_metrics,
                                  "omittedPenaltyTerms": omitted})
                candidates.append((candidate_score, alpha, predicted))
            best_score, alpha, predicted = min(candidates, key=lambda candidate: (candidate[0], -candidate[1]))
            validation_predictions[family] = predicted
            # Refit coefficients on train+validation after selection. Lags remain train-only.
            final_rows = np.r_[rows["train"], rows["validation"]]
            parameters = fit_ridge(features, delta, final_rows, alpha)
            choices.append((best_score, family, parameters))
            for phase in ("validation", "test", "stress_current"):
                indices = rows[phase]
                if not len(indices):
                    continue
                pred = predicted if phase == "validation" else local[indices] + infer_delta(parameters, features[indices])
                pending_evaluations.append((horizon, family, phase, pred, target[indices], local[indices], trend[indices]))
                predictions.extend({"h": horizon, "model": family, "phase": phase, "origin": iso(times[index]), "target_time": iso(times[index] + horizon * 3600), "base_m": float(local[index]), "actual_m": float(target[index]), "forecast_m": float(value)} for index, value in zip(indices, pred))
        best_score, family, parameters = min(choices, key=lambda candidate: (candidate[0], candidate[1]))
        residuals = target[rows["validation"]] - validation_predictions[family]
        baseline_scores = {}
        for name in ("persistence", "local_trend_2h"):
            for phase in ("validation", "test", "stress_current"):
                indices = rows[phase]
                if not len(indices):
                    continue
                pred = local[indices] + (horizon * trend[indices] if name == "local_trend_2h" else 0)
                pending_evaluations.append((horizon, name, phase, pred, target[indices], local[indices], trend[indices]))
                if phase == "validation":
                    baseline_scores[name] = score(pred, target[indices], local[indices])
                predictions.extend({"h": horizon, "model": name, "phase": phase, "origin": iso(times[index]), "target_time": iso(times[index] + horizon * 3600), "base_m": float(local[index]), "actual_m": float(target[index]), "forecast_m": float(value)} for index, value in zip(indices, pred))
        features, names = matrices[family]
        artifact["horizons"].append({
            "h": horizon, "family": family, "featureNames": names, "parameters": parameters,
            "validationScore": float(best_score), "baselineValidationScores": baseline_scores,
            "beatsBothBaselinesOnValidation": all(best_score < value for value in baseline_scores.values()),
            "rows": {key: int(len(value)) for key, value in rows.items()},
            "empiricalErrorQuantiles": {"p05": float(np.quantile(residuals, .05)), "p95": float(np.quantile(residuals, .95))},
            "uncertainty": "Empirical validation residual envelope; no nominal coverage or safety bound.",
        })
    artifact["requiredHistoryHours"] = max(6, max(row["lagHours"] + 3 for row in lags.values()))
    # The CLI freezes predictions before calculating the test/stress metrics.
    # Validation scores above are necessarily used to select the model.
    if prediction_sink is not None:
        prediction_sink(predictions)
    for horizon, family, phase, pred, target, base, origin_trend in pending_evaluations:
        evaluations.append({"h": horizon, "model": family, "phase": phase,
                            **metrics(pred, target, base, origin_trend)})
    report = {
        "modelVersion": MODEL_VERSION, "contract": CONTRACT,
        "evaluationStatus": artifact["evaluationStatus"], "promotionEligible": False,
        "historicalAvailabilityReconstructed": False, "selection": selection,
        "evaluations": evaluations, "lagCorrelations": lag_correlations,
        "selectedFamilies": {str(row["h"]): row["family"] for row in artifact["horizons"]},
        "missingOriginsExcluded": int((~complete).sum()), "totalOrigins": int(len(times)),
        "rowMembershipByHorizon": row_membership,
        "rowMembershipDefinition": "Zero-based indices into the frozen dataset; all other rows are excluded. Split rules and exact target timestamps remain in the frozen code and protocol.",
        "naturalAvailabilityByHorizon": availability,
        "originPhaseDefinition": "Exact two-hour local slope: rising > 0.05m/h, falling < -0.05m/h, otherwise stable.",
        "accuracyDefinition": "Rates report absolute error within 0.10m, 0.20m and 0.50m; no unspecified percent accuracy claim.",
    }
    return artifact, report, predictions


def predict(model, times, data, reference_at, issued_at):
    """Predict only still-future original targets, using frozen parameters."""
    if model.get("contract") != CONTRACT or model.get("targetStation") != "86510000":
        raise ValueError("Incompatible frozen hydrometric model")
    if [row.get("h") for row in model.get("horizons", [])] != list(range(1, 7)):
        raise ValueError("Frozen model must contain the six ordered nominal horizons")
    times, data = validate_series(times, data)
    reference, issued = epoch(reference_at), epoch(issued_at)
    if reference % 3600 or issued < reference or issued - reference > 3 * 3600:
        raise ValueError("Reference must be an exact hour no more than three hours before issue")
    positions = np.flatnonzero(times == reference)
    if len(positions) != 1:
        raise IncompleteHydrometry("Reference hour is not present exactly")
    index = int(positions[0])
    missing = [key for key in REQUIRED if not np.isfinite(data[key][index])]
    if missing:
        raise IncompleteHydrometry("Missing reference-hour hydrometry: " + ", ".join(missing))
    points, extrapolations = [], set()
    for horizon in model["horizons"]:
        lead = int(horizon["h"])
        target = reference + lead * 3600
        if target <= issued:
            continue
        features, names = feature_matrix(data, model["lags"], horizon["family"])
        if names != horizon["featureNames"]:
            raise ValueError("Frozen feature names or ordering do not match")
        values = features[index]
        absent = [name for name, value in zip(names, values) if not np.isfinite(value)]
        if absent:
            raise IncompleteHydrometry("Missing exact historical inputs: " + ", ".join(absent))
        parameters = horizon["parameters"]
        outside = (values < np.asarray(parameters["featureMin"])) | (values > np.asarray(parameters["featureMax"]))
        extrapolations.update(name for name, is_outside in zip(names, outside) if is_outside)
        level = float(data[TARGET][index] + infer_delta(parameters, values))
        envelope = horizon["empiricalErrorQuantiles"]
        points.append({"leadHours": lead, "nominalLeadHours": lead,
                       "realLeadHours": (target - issued) / 3600,
                       "time": iso(target), "timestamp": iso(target), "level": level,
                       "lower": level + envelope["p05"], "upper": level + envelope["p95"],
                       "family": horizon["family"]})
    if not points:
        raise ValueError("No forecast target remains in the future")
    return {
        "modelVersion": model["modelVersion"], "contract": CONTRACT,
        "stationCode": "86510000", "experimental": True, "mode": "shadow",
        "publishable": False, "status": "calculated",
        "referenceAt": iso(reference), "generatedAt": iso(issued),
        "observation": {"timestamp": iso(reference), "level": float(data[TARGET][index])},
        "observedLevel": float(data[TARGET][index]), "horizonHours": 6,
        "forecastStartLeadHours": points[0]["leadHours"], "points": points,
        "rainRequired": False, "extrapolatedFeatures": sorted(extrapolations),
        "uncertainty": "Empirical validation residual envelope; no nominal coverage or safety bound.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    train = subparsers.add_parser("train", help="Explicit offline calibration only")
    train.add_argument("--dataset", type=Path, required=True)
    train.add_argument("--dataset-metadata", type=Path)
    train.add_argument("--output", type=Path, required=True)
    train.add_argument("--train-end", required=True)
    train.add_argument("--validation-end", required=True)
    train.add_argument("--test-end", required=True)
    infer = subparsers.add_parser("predict", help="Frozen, no-training inference")
    infer.add_argument("--dataset", type=Path, required=True)
    infer.add_argument("--model", type=Path, required=True)
    infer.add_argument("--reference", required=True)
    infer.add_argument("--issued-at", required=True)
    args = parser.parse_args()
    with np.load(args.dataset, allow_pickle=False) as loaded:
        data = {key: loaded[key] for key in loaded.files}
    times = data.pop("times")
    if args.command == "predict":
        print(json.dumps(predict(json.loads(args.model.read_text()), times, data, args.reference, args.issued_at), allow_nan=False, indent=2))
        return
    metadata = json.loads(args.dataset_metadata.read_text()) if args.dataset_metadata else {}
    metadata["npzSha256"] = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    args.output.mkdir(parents=True, exist_ok=True)
    for filename in ("model.json", "evaluation.json", "predictions.csv", "predictions.sha256"):
        if (args.output / filename).exists():
            raise FileExistsError(f"Refusing to replace a frozen run: {args.output / filename}")

    def freeze_predictions(rows):
        prediction_path = args.output / "predictions.csv"
        with prediction_path.open("x", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=["h", "model", "phase", "origin", "target_time", "base_m", "actual_m", "forecast_m"])
            writer.writeheader()
            writer.writerows(rows)
        digest = hashlib.sha256(prediction_path.read_bytes()).hexdigest()
        with (args.output / "predictions.sha256").open("x") as output:
            output.write(digest + "  predictions.csv\n")

    artifact, report, rows = fit_model(times, data, args.train_end, args.validation_end, args.test_end,
                                     dataset_metadata=metadata, prediction_sink=freeze_predictions)
    for filename, content in (("model.json", artifact), ("evaluation.json", report)):
        with (args.output / filename).open("x") as output:
            output.write(json.dumps(content, ensure_ascii=False, allow_nan=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "selectedFamilies": report["selectedFamilies"], "promotionEligible": False}))


if __name__ == "__main__":
    main()
