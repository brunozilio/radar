"""Local HGE/ARNO experiment. This is NOT the complete MGB-IPH model.

SPDX-License-Identifier: GPL-3.0-only
Adapter created 2026-09-21. The upstream source in vendor/ is unmodified.
No network calls, production writes or notifications occur in this program.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from numba import njit
from scipy.optimize import differential_evolution

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "vendor"))
import hydrological_model as upstream

TZ = timezone(timedelta(hours=-3))
NAMES = ["Wm", "b", "kbas", "k", "CB", "Ws"]
BOUNDS = [(30., 1500.), (.01, 3.), (.01, 10.), (1., 20.), (1., 200.), (.2, 1.)]
compiled_step = njit(upstream.rainfall_runoff)


def epoch(value):
    d = datetime.fromisoformat(value)
    return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()


def iso(value):
    return datetime.fromtimestamp(float(value), TZ).isoformat()


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def savecsv(path, values):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parameters(x):
    return {**dict(zip(NAMES, map(float, x))), "n": 3}


def initial_state(x):
    # Hypothesis: half-full soil; groundwater in equilibrium with its initial
    # percolation. Exclude the first 60 days from calibration (warm-up).
    state = np.zeros(6)
    state[0] = x[0] / 2
    state[1] = .5 * x[2] * x[4]
    return state


@njit
def simulate_series(rain, pet_hourly, x, area, state):
    # A literal heterogeneous dictionary retains integer n for the ORIGINAL
    # upstream routine. JIT only accelerates the code; no equations are changed.
    p = {"Wm": x[0], "b": x[1], "kbas": x[2], "n": 3,
         "k": x[3], "CB": x[4], "Ws": x[5]}
    states = np.empty((len(rain), 6))
    errors = np.empty(len(rain))
    if len(pet_hourly) != len(rain):
        raise ValueError("Rain and PET lengths differ")
    for i in range(len(rain)):
        if not np.isfinite(pet_hourly[i]) or pet_hourly[i] < 0:
            raise ValueError("PET must be finite and nonnegative")
        old = state.copy()
        # The original routine mutates a reservoir slice: copy at its boundary
        # so previously saved states remain valid for audit and continuation.
        state = compiled_step(old.copy(), p, rain[i], pet_hourly[i], area, 3600.)
        states[i] = state
        et = pet_hourly[i] * min(1., old[0] / (x[0] * x[5]))
        discharge_mm = state[-1] * 3600. / (area * 1000.)
        errors[i] = old[:-1].sum() + rain[i] - et - discharge_mm - state[:-1].sum()
    return states, errors


def simulate(rain, pet_day, x, area, state):
    return simulate_series(rain, np.full(len(rain), pet_day / 24.), x, area, state)


def metrics(pred, truth):
    ok = np.isfinite(pred) & np.isfinite(truth)
    e = pred[ok] - truth[ok]
    if not len(e):
        return {"n": 0, "mae_m": None, "rmse_m": None, "bias_m": None}
    return {"n": len(e), "mae_m": float(np.mean(abs(e))),
            "rmse_m": float(np.sqrt(np.mean(e * e))), "bias_m": float(np.mean(e))}


def weather(path, times):
    data = json.loads(path.read_text())[0]  # Baixo Antas centroid, NOT an areal grid.
    hourly = data["hourly"]
    lookup = {epoch(t): v for t, v in zip(hourly["time"], hourly["precipitation_previous_day1"])}
    result = np.array([lookup.get(t, np.nan) for t in times], dtype=float)
    if np.any(result < 0) or not np.isfinite(result[-12:]).all():
        raise ValueError(f"Invalid weather forcing or missing future hours: {path}")
    return result


def stage(q, rating):
    return rating[0] * np.maximum(q / 1000., 0.) ** rating[1] + rating[2]


def run(args):
    source = args.source.resolve()
    out = args.output.resolve()
    if source == out:
        raise ValueError("Experimental output must not overwrite the source snapshot")
    out.mkdir(parents=True, exist_ok=True)
    provenance = json.loads((HERE / "vendor/provenance.json").read_text())
    for filename, detail in provenance["files"].items():
        assert sha(HERE / "vendor" / filename) == detail["sha256"]
    used = [source / n for n in ["dados-roteamento.npz", "telemetria-latencia.npz",
            "conferencia-balanco.json", "roteamento-vazao-pesos.csv",
            "previsao-vazoes-montante.csv", "previsao-atualizada.json",
            "previsao-atualizada.csv", "roteamento-previsao.csv"]]
    inputs_hash = {str(p.relative_to(ROOT)): sha(p) for p in used}
    d = dict(np.load(source / "dados-roteamento.npz"))
    z = dict(np.load(source / "telemetria-latencia.npz"))
    meta = json.loads((source / "previsao-atualizada.json").read_text())
    balance = json.loads((source / "conferencia-balanco.json").read_text())
    t = d["times"]
    origin = epoch(meta["origin"])
    assert t[-1] == origin and np.all(np.diff(t) == 3600)
    area = float(d["area"])
    pet_available = np.full(len(t), np.nan)
    pet_description = None
    if args.pet_series:
        pet_path = args.pet_series.resolve()
        pet_data = json.loads(pet_path.read_text())
        # Open-Meteo ERA5 ET0 is a reference evapotranspiration estimate in
        # mm for the preceding hour. It is NOT measured ET or archived forecast.
        if pet_data.get('utc_offset_seconds') != 0:
            raise ValueError('ET0 input must be requested in UTC')
        hourly = pet_data['hourly']
        if pet_data['hourly_units']['et0_fao_evapotranspiration'] != 'mm':
            raise ValueError('ET0 input must be mm per hour')
        lookup = {epoch(stamp + '+00:00'): value for stamp, value in
                  zip(hourly['time'], hourly['et0_fao_evapotranspiration'])}
        pet_available = np.array([lookup.get(when, np.nan) for when in t], dtype=float)
        valid_pet = np.isfinite(pet_available)
        if not valid_pet.any() or np.any(pet_available[valid_pet] < 0):
            raise ValueError('No valid ET0 forcing')
        inputs_hash[str(pet_path.relative_to(ROOT))] = sha(pet_path)
        pet_description = {'source_file': str(pet_path.relative_to(ROOT)),
                           'type': 'ERA5 FAO56 reference ET0 reanalysis proxy, not observed ET',
                           'latitude': pet_data['latitude'], 'longitude': pet_data['longitude'],
                           'matched_hours': int(valid_pet.sum()), 'missing_hours': int((~valid_pet).sum()),
                           'latest_valid_time': iso(t[valid_pet][-1]),
                           'missing_and_future_policy': 'Explicit 1/3/5 mm/day constant sensitivity hypotheses'}
    extended_times = np.r_[t, origin + np.arange(1, 13) * 3600]
    weather_files = {
        "gfs": ROOT / "outputs/mucum-propagacao-2026-09-21/raw/chuva-previsao-historica-gfs_seamless.json",
        "ecmwf": ROOT / "outputs/mucum-propagacao-2026-09-21/raw/chuva-previsao-historica-ecmwf_ifs025.json",
        "icon": source / "nwp-historical-icon.json",
    }
    if getattr(args, "weather_dir", None):
        weather_files = {name: args.weather_dir / f"hge-weather-{name}.json" for name in weather_files}
    nwp = {name: weather(path, extended_times) for name, path in weather_files.items()}
    inputs_hash.update({str(p.relative_to(ROOT)): sha(p) for p in weather_files.values()})
    # Some archives have historical gaps. Average only the members actually
    # available at that valid time; reject any hour without a usable member.
    nwp_count = np.sum(np.isfinite(list(nwp.values())), axis=0)
    assert np.all(nwp_count > 0)
    mean_nwp = np.nanmean(list(nwp.values()), axis=0)
    coverage = d["coverage"]
    assert np.all((coverage >= 0) & (coverage <= 1 + 1e-8))
    # Preserve the observed part of each interval. Forecasts estimate ONLY the
    # unobserved space/time fraction, including the partial hour at the origin.
    rain = d["amount"] + np.maximum(1 - coverage, 0) * mean_nwp[:len(t)]
    assert np.all(np.isfinite(rain)) and np.all(rain >= 0)
    weights = rows(source / "roteamento-vazao-pesos.csv")
    jw = np.array([float(r["weight"]) for r in weights if r["source"] == "14 de Julho"])
    cw = np.array([float(r["weight"]) for r in weights if r["source"] == "Passo Carreiro"])
    rw = np.array([float(r["weight"]) for r in weights if r["source"] == "chuva incremental"])
    assert abs(jw.sum() - 1) < 1e-6 and abs(cw.sum() - 1) < 1e-6
    upstream_q = (d["X"][:, :12] @ jw + d["X"][:, 12:33] @ cw) * 1000
    baseline_q = upstream_q + (d["X"][:, 33:58] @ rw + balance["baseflow_1000m3s"]) * 1000
    observed_q = d["q"] * 1000
    train_end = epoch("2026-07-01T00:00:00")
    test_end = epoch("2026-09-21T00:00:00")
    train = (t >= t[0] + 60 * 86400) & (t < train_end) & np.isfinite(upstream_q) & np.isfinite(observed_q) & (coverage >= .75)
    test = (t >= train_end) & (t < test_end) & np.isfinite(baseline_q) & np.isfinite(d["h"])
    assert train.sum() > 1000 and test.sum() > 100
    end = int(np.searchsorted(t, train_end))
    train_indices = np.where(train)[0]
    training_weights = 1 + 2 * (observed_q[train] >= 2000)
    rating = balance["rating_parameters"]
    calib = []
    reconstructions = []
    histories = {}
    print(f"Origin {iso(origin)}, area {area:.2f} km2; calibration {train.sum()}, reconstruction test {test.sum()}", flush=True)
    for pet in [1., 3., 5.]:
        actual_pet = np.where(np.isfinite(pet_available), pet_available, pet / 24.)
        def objective(logx):
            x = np.exp(logx)
            states, _ = simulate_series(rain[:end], actual_pet[:end], x, area, initial_state(x))
            err = (upstream_q[train] + states[train_indices, -1] - observed_q[train]) / 300.
            return float(np.mean(training_weights * (np.sqrt(1 + err * err) - 1)))

        count = [0]
        def progress(xk, convergence):
            count[0] += 1
            if count[0] % 15 == 0:
                print(f"PET hypothesis {pet:g} mm/day, optimization generation {count[0]}", flush=True)

        if getattr(args, "parameters", None):
            frozen = next(c for c in json.loads(args.parameters.read_text()) if c["pet_mm_day_hypothesis"] == pet)
            x = np.array([frozen["parameters"][name] for name in NAMES])
            result = SimpleNamespace(fun=frozen["objective"], success=frozen["optimizer_converged"],
                                     message="Frozen reference parameters; no optimization this run")
        else:
            result = differential_evolution(objective, np.log(BOUNDS), seed=57,
                                            maxiter=args.iterations, popsize=7,
                                            tol=.002, polish=True, callback=progress)
            x = np.exp(result.x)
        states, errors = simulate_series(rain, actual_pet, x, area, initial_state(x))
        assert np.min(states) >= -1e-9 and np.max(states[:, 0]) <= x[0] + 1e-8
        assert np.max(abs(errors)) < 1e-8
        histories[pet] = (x, states)
        pred = stage(upstream_q + states[:, -1], rating)
        label = f"hge_pet_{pet:g}"
        for subset, mask in [("all", test), ("level_ge_7m", test & (d["h"] >= 7))]:
            reconstructions.append({"model": label, "subset": subset, **metrics(pred[mask], d["h"][mask])})
        near_bounds = [name for name, value, (lo, hi) in zip(NAMES, x, BOUNDS)
                       if value <= lo * 1.02 or value >= hi * .98]
        calib.append({"pet_mm_day_hypothesis": pet, "parameters": parameters(x),
                      "objective": float(result.fun), "optimizer_converged": bool(result.success),
                      "optimizer_message": str(result.message), "near_parameter_bounds": near_bounds,
                      "max_water_balance_error_mm": float(np.max(abs(errors))),
                      "soil_fraction_at_origin": float(states[-1, 0] / x[0]),
                      "soil_fraction_before_today": float(states[np.searchsorted(t, test_end) - 1, 0] / x[0]),
                      "current_incremental_flow_m3_s": float(states[-1, -1])})
        print(json.dumps(calib[-1]), flush=True)
    for subset, mask in [("all", test), ("level_ge_7m", test & (d["h"] >= 7))]:
        reconstructions.append({"model": "existing_linear_routing", "subset": subset,
                                **metrics(stage(baseline_q[mask], rating), d["h"][mask])})
    savecsv(out / "reconstrucao-teste.csv", reconstructions)
    dump(out / "parametros.json", calib)
    forecasts_upstream = rows(source / "previsao-vazoes-montante.csv")
    future_q = {s: {int(r["lead_h"]): float(r["forecast_m3_s"]) for r in forecasts_upstream if r["source"] == s}
                for s in ["julho", "carreiro"]}

    def routed_at(lead):
        total = 0.
        for s, lags, ws in [("julho", range(1, 13), jw), ("carreiro", range(4, 25), cw)]:
            for lag, w in zip(lags, ws):
                k = lead - lag
                value = future_q[s][k] if k >= 0 else d[s][len(t) - 1 + k] * 1000.
                if not np.isfinite(value):
                    raise ValueError(f"Missing upstream flow {s} at lead {k}")
                total += w * value
        return total

    up_now_future = np.array([routed_at(h) for h in range(13)])
    zi = np.searchsorted(z["times"], origin)
    base_q = float(z["86510000:Q"][zi])
    observed = meta["last_observed_mucum"]
    last_observed_time = epoch(observed["last_time"])
    # Verify H and Q exist at the SAME actual observation time for anchoring.
    oi = np.searchsorted(z["times"], last_observed_time)
    assert np.isfinite(base_q) and base_q == z["raw:86510000:Q"][oi]
    assert abs(z["raw:86510000:H"][oi] - observed["value"]) < 1e-8
    age_h = (origin - last_observed_time) / 3600.
    rating_offset = observed["value"] - float(stage(base_q, rating))
    scenarios = []
    # PET=3, arithmetic mean rainfall and tau=6 define a REFERENCE scenario
    # before seeing the forecast. Other cases are sensitivity, not probabilities.
    future_weather = {**{name: a[len(t):] for name, a in nwp.items()}, "mean": mean_nwp[len(t):]}
    for pet, (x, history) in histories.items():
        known_q = upstream_q + history[:, -1]
        reconstructed_last = float(np.interp(last_observed_time, t[-25:], known_q[-25:]))
        residual = base_q - reconstructed_last
        for name, future_rain in future_weather.items():
            states, errors = simulate(future_rain, pet, x, area, history[-1].copy())
            assert np.max(abs(errors)) < 1e-8 and np.min(states) >= -1e-9
            for tau in [2., 6., 12.]:
                for i in range(12):
                    lead = i + 1
                    q_uncorrected = up_now_future[lead] + states[i, -1]
                    correction = residual * np.exp(-(lead + age_h) / tau)
                    q_corrected = q_uncorrected + correction
                    assert q_corrected >= 0
                    level = float(stage(q_corrected, rating) + rating_offset)
                    scenarios.append({"pet_mm_day": pet, "weather": name, "correction_tau_h": tau,
                                      "lead_h": lead, "time": iso(origin + lead * 3600),
                                      "forecast_m": level, "flow_m3_s": float(q_corrected),
                                      "incremental_flow_m3_s": float(states[i, -1]),
                                      "routed_upstream_flow_m3_s": float(up_now_future[lead]),
                                      "rain_mm": float(future_rain[i]), "soil_fraction": float(states[i, 0] / x[0]),
                                      "flow_correction_m3_s": float(correction)})
    savecsv(out / "cenarios.csv", scenarios)
    previous = rows(source / "previsao-atualizada.csv")
    previous_routing = rows(source / "roteamento-previsao.csv")
    reference = [r for r in scenarios if r["pet_mm_day"] == 3 and r["weather"] == "mean" and r["correction_tau_h"] == 6]
    comparison = []
    for i, r in enumerate(reference):
        levels = [s["forecast_m"] for s in scenarios if s["lead_h"] == r["lead_h"]]
        comparison.append({"time": r["time"], "lead_h": r["lead_h"], "hge_reference_m": r["forecast_m"],
                           "sensitivity_min_m": min(levels), "sensitivity_max_m": max(levels),
                           "previous_selected_m": float(previous[i]["forecast_m"]),
                           "previous_routing_m": float(previous_routing[i]["forecast_m"])})
    savecsv(out / "comparacao.csv", comparison)
    recent_indices = np.where(t >= test_end - 2 * 86400)[0]
    savecsv(out / "chuva-estados-recentes.csv", [
        {"time": iso(t[i]), "rain_observed_partial_mm": float(d["amount"][i]),
         "rain_coverage": float(coverage[i]), "rain_completed_mm": float(rain[i]),
         "soil_fraction_pet3": float(histories[3.][1][i, 0] / histories[3.][0][0]),
         "incremental_flow_m3_s": float(histories[3.][1][i, -1])}
        for i in recent_indices])
    summary = {
        "model": "HGE simple_water_balance (ARNO) + existing empirical upstream routing",
        "full_mgb_iph": False, "origin": iso(origin), "last_observed": observed,
        "generated_at": datetime.now(TZ).isoformat(), "area_incremental_km2": area,
        "source_code": provenance, "input_sha256": inputs_hash,
        "adapter_sha256": sha(Path(__file__)),
        "runtime_versions": {name: importlib.metadata.version(name) for name in ['numpy', 'scipy', 'numba', 'matplotlib']},
        "pet_reanalysis_input": pet_description,
        "weather_missing_hours": {name: int(np.sum(~np.isfinite(v))) for name, v in nwp.items()},
        "calibration": {"start_after_warmup": iso(t[0] + 60 * 86400), "end_exclusive": iso(train_end), "n": int(train.sum())},
        "reconstruction_test": {"start": iso(train_end), "end_exclusive": iso(test_end), "n": int(test.sum()),
                                "is_prospective_forecast_validation": False,
                                "note": "Observed upstream flows and rainfall; same origins and rating curve for both models."},
        "reference_scenario": {"pet_mm_day_hypothesis": 3, "rainfall": "mean of supplied meteorological forecasts at Baixo Antas centroid", "correction_tau_h_hypothesis": 6},
        "limitations": [
            "Not the complete MGB-IPH: no distributed HRUs, river hydraulics, backwater or floodplain storage.",
            "PET constants of 1/3/5 mm/day are sensitivity hypotheses, not observations; when ET0 is supplied, constants only fill unavailable and future hours.",
            "Soil parameters are effective residual fits; upstream routing and rating errors can be absorbed by them.",
            "Soil initialization is hypothetical with 60-day warm-up; spin-up convergence is not established.",
            "Upstream future discharges reuse the existing statistical forecasts; these are not observed releases.",
            "Future rainfall is a centroid proxy; collection and issuance are audited in the parent run manifest.",
            "Missing precipitation fractions are estimated with model rainfall, not replaced by zeros.",
            "Reference scenario is not selected by independent forecast validation; sensitivity bounds are not confidence intervals.",
            "Existing upstream kernels and rating were fitted before 2026-07-01, but the project has previously examined the test period.",
            "Input reference and observation ages are explicit; current-event errors did not tune frozen parameters.",
        ],
        "forecast": comparison, "reconstruction_metrics": reconstructions,
        "checks": {"vendor_hashes_match": True, "source_snapshot_unchanged": True,
                   "nonnegative_states": True, "water_conservation_tolerance_mm": 1e-8,
                   "max_mass_error_mm": max(c["max_water_balance_error_mm"] for c in calib),
                   "forecast_hours": 12, "forecast_validation_complete": False},
    }
    # Source snapshots are read-only, including while generating this report.
    for p, digest in inputs_hash.items():
        assert sha(ROOT / p) == digest
    dump(out / "resultado.json", summary)
    make_report(out, summary, calib)
    make_plot(out, summary, z)
    print(json.dumps({"forecast": comparison, "reconstruction": reconstructions}, ensure_ascii=False, indent=2), flush=True)


def make_report(out, result, calib):
    pet_input = result.get('pet_reanalysis_input')
    pet_note = (f"ET0 horária de referência FAO56 estimada pela reanálise ERA5, usada como aproximação da PET. "
                f"Há {pet_input['matched_hours']} horas correspondentes e {pet_input['missing_hours']} horas sem dado; "
                f"último valor em {pet_input['latest_valid_time']}. "
                "A cauda indisponível e as horas futuras usam hipóteses constantes de 1/3/5 mm/dia. "
                "ET0 não é evapotranspiração medida nem previsão meteorológica histórica emitida."
                if pet_input else "Evapotranspiração potencial constante de 1, 3 ou 5 mm/dia em toda a série, sem observações de PET.")
    table = "\n".join(f"| {datetime.fromisoformat(r['time']):%d/%m %Hh} | {r['hge_reference_m']:.2f} | {r['previous_selected_m']:.2f} | {r['previous_routing_m']:.2f} | {r['sensitivity_min_m']:.2f}–{r['sensitivity_max_m']:.2f} |" for r in result["forecast"])
    tests = "\n".join(f"| {r['model']} | {r['subset']} | {r['n']} | {r['mae_m']:.3f} |" for r in result["reconstruction_metrics"])
    params = "\n".join(f"| {c['pet_mm_day_hypothesis']:g} | {c['parameters']['Wm']:.1f} | {c['parameters']['b']:.3f} | {c['parameters']['k']:.2f} | {100*c['soil_fraction_at_origin']:.1f}% | {', '.join(c['near_parameter_bounds']) or 'nenhum'} |" for c in calib)
    metric_lookup = {(r['model'], r['subset']): r['mae_m'] for r in result['reconstruction_metrics']}
    mean_base = metric_lookup['existing_linear_routing', 'all']
    mean_new = metric_lookup['hge_pet_3', 'all']
    high_base = metric_lookup['existing_linear_routing', 'level_ge_7m']
    high_new = metric_lookup['hge_pet_3', 'level_ge_7m']
    comparison_note = ("o novo componente não demonstrou melhora para cheias" if high_new >= high_base
                       else "há ganho de reconstrução em cheias, ainda sem comprovação prospectiva")
    (out / "relatorio.md").write_text(f"""# Muçum — experimento com código HGE/ARNO

Calculado em {result['generated_at']}. Base dos dados: **{result['origin']}**.
Último nível medido: **{result['last_observed']['value']:.2f} m**, em {result['last_observed']['last_time']}.

Foi copiado e executado o `simple_water_balance` do grupo HGE-IPH, commit
`{result['source_code']['commit']}`, com licença GPL-3.0 e arquivo original intacto.
**Este é o modelo simplificado ARNO do grupo; não é o MGB-IPH completo.**

## Cálculo e dados disponíveis

- Área incremental: **{result['area_incremental_km2']:.2f} km²**, excluindo as áreas já representadas pelas vazões de 14 de Julho e Passo Carreiro.
- Chuva observada parcial + estimativa meteorológica apenas para a fração sem cobertura.
- Solo, aquífero e três reservatórios em cascata calculados pelo código original; as cascatas representam atraso do escoamento local, não as usinas reais.
- Vazões de montante propagadas pelos pesos já calibrados; vazões futuras reaproveitadas da previsão estatística existente.
- Conversão vazão–nível pela curva local já ajustada, com ancoragem no par observado de vazão e nível em {result['last_observed']['last_time']}.
- Calibração de seis parâmetros efetivos com alvos anteriores a 01/07/2026; aquecimento inicial de 60 dias. Nenhum alvo do evento de hoje foi usado na calibração.

**Evapotranspiração:** {pet_note}

**Hipóteses necessárias:** solo inicial a 50% da capacidade; três reservatórios;
correção do erro atual com tempos de 2, 6 ou 12h.
São hipóteses e parâmetros ajustados, não medições físicas da bacia. O valor de referência usa PET=3,
quando não há ET0 disponível, chuva média de GFS/ECMWF/ICON e correção de 6h,
definidos antes de inspecionar o resultado.

## Resultado experimental

| Horário BRT | HGE referência (m) | Previsão anterior (m) | Roteamento anterior (m) | Sensibilidade HGE (m) |
|---|---:|---:|---:|---:|
{table}

A amplitude é apenas a sensibilidade às hipóteses testadas. **Não é intervalo de confiança,
limite máximo de cheia ou confirmação de pico.** A referência não foi escolhida por desempenho
em previsões independentes. Os cenários dependem das mesmas vazões futuras estimadas a montante.

## Verificação histórica disponível

Teste de **reconstrução** entre 01/07 e 20/09/2026, com chuva e vazões de montante observadas.
Os dois métodos usam exatamente os mesmos horários e a mesma curva vazão–nível.
Esses erros **não medem precisão de previsão com 12h de antecedência**.
O período já foi examinado em análises anteriores do projeto: não é uma nova avaliação cega.

| Modelo | Recorte | Horas | Erro absoluto médio (m) |
|---|---|---:|---:|
{tests}

No cenário de referência, o erro geral mudou de **{mean_base:.3f} para {mean_new:.3f} m**,
mas acima de 7 m mudou de **{high_base:.3f} para {high_new:.3f} m**. Nesta comparação,
{comparison_note}. Não há base para substituir
a previsão atual por ele. A proximidade ao roteamento anterior não é confirmação
independente: os dois reutilizam as mesmas estimativas de vazões futuras a montante.

## Parâmetros e sensibilidade

| PET hipotética (mm/dia) | Capacidade do solo (mm) | b | k por reservatório (h) | Saturação na referência | Próximos dos limites de ajuste |
|---|---:|---:|---:|---:|---|
{params}

Os parâmetros completos, a convergência do otimizador e as condições de contorno estão em
`parametros.json`. Ajuste junto aos limites e diferenças entre hipóteses são sinais de identificação
limitada. A saturação é estado do modelo, não um sensor de umidade.

## Limites e verificações

Não há geometria de canal, remanso, planícies de inundação, discretização completa em minibacias/URHs
nem evapotranspiração observada. A chuva prevista representa um ponto do Baixo Antas, não toda a área.
Os horários de referência e observação constam acima; a coleta está auditada na pasta da execução.

Foi verificada a identidade do código copiado, a conservação de água (erro máximo
{result['checks']['max_mass_error_mm']:.3g} mm por passo), estoques não negativos e 12 saídas horárias.
Os arquivos de entrada foram preservados e suas assinaturas estão em `resultado.json`.
Ainda falta uma validação de previsões por evento, respeitando a disponibilidade histórica de cada fonte,
para decidir se esse modelo melhora a previsão operacional. Nenhuma alteração em produção.

Fonte do código: https://github.com/HGE-IPH/simple_water_balance
""", encoding="utf-8")


def make_plot(out, result, z):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    origin = epoch(result["origin"])
    fig, ax = plt.subplots(figsize=(12.5, 7.5))
    fig.subplots_adjust(left=.08, right=.96, top=.79, bottom=.24)
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    selected = (z["times"] >= origin - 9*3600) & (z["times"] <= origin) & np.isfinite(z["raw:86510000:H"])
    ax.plot([datetime.fromtimestamp(t, TZ) for t in z["times"][selected]], z["raw:86510000:H"][selected],
            color="#172b4d", lw=2.8, label="Nível observado")
    f = result["forecast"]
    dates = [datetime.fromisoformat(r["time"]) for r in f]
    ax.fill_between(dates, [r["sensitivity_min_m"] for r in f], [r["sensitivity_max_m"] for r in f],
                    color="#bb6b27", alpha=.14, label="Sensibilidade das hipóteses")
    ax.plot(dates, [r["hge_reference_m"] for r in f], color="#a85416", lw=2.6, label="HGE/ARNO experimental")
    ax.plot(dates, [r["previous_selected_m"] for r in f], color="#2867a4", lw=2, ls="--", label="Radar estatístico selecionado")
    ax.plot(dates, [r["previous_routing_m"] for r in f], color="#757f8d", lw=1.8, ls=":", label="Roteamento anterior")
    ax.axvline(datetime.fromtimestamp(origin, TZ), color="#97a6b5", lw=1)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3, tz=TZ))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%Hh", tz=TZ))
    ax.set_ylabel("Nível na régua de Muçum (m)")
    ax.grid(axis="y", alpha=.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    title = "Muçum · HGE/ARNO com ET0 de reanálise" if result.get('pet_reanalysis_input') else "Muçum · cálculo experimental com HGE/ARNO"
    fig.text(.08, .93, title, fontsize=20, weight="bold", color="#172b4d")
    fig.text(.08, .865, f"Base: {result['origin']}  |  Observado: {result['last_observed']['value']:.2f} m ({result['last_observed']['last_time'][11:16]})", fontsize=12, color="#465871")
    fig.text(.08, .12, "Modelo simplificado do grupo HGE-IPH, acoplado ao roteamento existente. Não é o MGB-IPH completo.", fontsize=10)
    fig.text(.08, .075, "Faixa = sensibilidade, não intervalo de confiança. Precisão futura e horário do pico ainda não validados.", fontsize=10, color="#924715")
    fig.savefig(out / "comparacao.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "outputs/mucum-atualizacao-15h-2026-09-21")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/mucum-hge-experimental-2026-09-21")
    parser.add_argument("--parameters", type=Path, help="Reuse calibrated parameters without optimization")
    parser.add_argument("--weather-dir", type=Path, help="Run-specific merged historical/current weather")
    parser.add_argument("--iterations", type=int, default=120)
    parser.add_argument("--pet-series", type=Path, help="Open-Meteo ERA5 hourly ET0 JSON requested in UTC; research only")
    run(parser.parse_args())
