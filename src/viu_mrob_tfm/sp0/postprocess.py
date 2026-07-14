"""SP0 v1.1 confirmatory analysis and artifact rendering."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy import stats

from viu_mrob_tfm.utils.io import ensure_directory, save_json


def run_postprocessing(root: Path, *, analyze: bool, render_figures: bool, render_videos: bool) -> dict[str, Any]:
    root = Path(root)
    runs = load_campaign_runs(root)
    result: dict[str, Any] = {"generated_at_utc": datetime.now(UTC).isoformat(), "run_rows": len(runs)}
    if analyze:
        result["analysis"] = analyze_confirmatory(root, runs)
    if render_figures:
        result["figures"] = generate_figures(root, runs)
    if render_videos:
        result["videos"] = generate_videos(root, runs)
    save_json(root / "statistics" / "postprocess_manifest.json", result)
    return result


def load_campaign_runs(root: Path) -> pd.DataFrame:
    frames = []
    for block in ["b2", "b3", "b4", "b5", "b6", "b7"]:
        path = root / block / "runs.parquet"
        if path.exists():
            frame = pd.read_parquet(path)
            frame["source_file"] = str(path)
            frames.append(frame)
    for path in sorted((root / "extensions").glob("*.parquet")):
        frame = pd.read_parquet(path)
        frame["source_file"] = str(path)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    data = pd.concat(frames, ignore_index=True, sort=False)
    data["unit_id"] = data.apply(unit_id, axis=1)
    data["regime"] = np.select(
        [data["K"] > data["N"], data["K"] < data["N"]],
        ["robot_scarcity", "robot_surplus"],
        default="balanced",
    )
    return data


def unit_id(row: pd.Series | dict[str, Any]) -> str:
    method = str(row.get("method_variant") or row.get("method") or "unknown")
    seed = row.get("train_seed")
    if seed is not None and not (isinstance(seed, float) and np.isnan(seed)):
        return f"{method}::train_seed={int(seed)}"
    return method


def analyze_confirmatory(root: Path, runs: pd.DataFrame) -> dict[str, Any]:
    out = ensure_directory(root / "statistics")
    tables = ensure_directory(out / "tables")
    confirmatory = runs[runs["block_id"].isin(["B4", "B5", "B6", "B7"])].copy()
    primary = summarize_primary(confirmatory)
    contrasts = apply_holm_by_family(build_contrasts(confirmatory))
    models = fit_models(runs)
    prices = summarize_prices(confirmatory)
    rankings = build_rankings(runs)
    hypotheses = hypothesis_decisions(contrasts, models)
    artifacts = {
        "primary_summary.parquet": primary,
        "confirmatory_contrasts.parquet": contrasts,
        "model_results.parquet": models,
        "observed_prices.parquet": prices,
        "rankings.parquet": rankings,
        "hypotheses.parquet": hypotheses,
    }
    for name, frame in artifacts.items():
        frame.to_parquet(out / name, index=False)
    primary.to_csv(tables / "T10_results_main.csv", index=False)
    contrasts.to_csv(tables / "T08_hypotheses_tests.csv", index=False)
    prices.to_csv(tables / "T12_observed_prices.csv", index=False)
    write_required_tables(tables, runs, primary, hypotheses, rankings)
    report = {
        "status": "complete",
        "confirmatory_rows": len(confirmatory),
        "contrasts": len(contrasts),
        "models": len(models),
        "holm_applied_by_family": True,
        "exploratory_B2_excluded_from_confirmatory_claims": True,
    }
    save_json(out / "analysis_report.json", report)
    return report


def summarize_primary(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()
    rows = []
    keys = ["block_id", "unit_id", "method_variant", "N", "K", "regime"]
    for key, group in data.groupby(keys, dropna=False):
        nr = numeric(group["normalized_regret"])
        success = numeric(group["final_success"])
        nr_low, nr_high = bootstrap_ci(nr)
        success_low, success_high = bootstrap_ci(success)
        rows.append({
            **dict(zip(keys, key)),
            "n": len(group),
            "failures": int(group["error_type"].notna().sum()),
            "timeouts": int(group["continuous_timeout"].fillna(False).astype(bool).sum()),
            "success_rate": finite_mean(success),
            "success_CI95_low": success_low,
            "success_CI95_high": success_high,
            "mean_normalized_regret": finite_mean(nr),
            "median_normalized_regret": finite_median(nr),
            "NR_CI95_low": nr_low,
            "NR_CI95_high": nr_high,
            "CVaR95_NR": cvar95(nr),
            "mean_runtime_wall_s": finite_mean(numeric(group["runtime_wall_s"])),
            "mean_messages": finite_mean(numeric(group["messages"])),
            "mean_bytes": finite_mean(numeric(group["bytes"])),
            "mean_time_to_epsilon_s": finite_mean(numeric(group["time_to_epsilon_solution"])),
            "time_to_epsilon_event_rate": finite_mean(numeric(group["time_to_epsilon_observed"])),
            "mean_messages_to_epsilon": finite_mean(numeric(group["messages_to_epsilon_solution"])),
            "mean_bytes_to_epsilon": finite_mean(numeric(group["bytes_to_epsilon_solution"])),
        })
    return pd.DataFrame(rows)


def build_contrasts(data: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    b4 = data[data["block_id"] == "B4"]
    if not b4.empty:
        units = sorted(b4["unit_id"].dropna().unique())
        pairs = []
        if "HUN" in units:
            pairs += [("HUN", unit, "P") for unit in units if unit != "HUN"]
        for left, right in [("GRD", "EPS-AUCTION"), ("REP", "SMI"), ("SMI", "BNN"), ("SMI", "LOG"), ("SMI", "HYB")]:
            if left in units and right in units:
                pairs.append((left, right, "P"))
        for left, right, family in dict.fromkeys(pairs):
            rows += paired_contrasts(
                b4[b4["unit_id"] == left],
                b4[b4["unit_id"] == right],
                left, right, family, "B4",
            )
    b5 = data[data["block_id"] == "B5"]
    if not b4.empty and not b5.empty:
        full = b5[np.isclose(pd.to_numeric(b5["mean_degree"]), b5["N"] - 1)]
        for method in sorted(set(b4["method_variant"]) & set(full["method_variant"])):
            global_rows = b4[(b4["method_variant"] == method) & (b4["K"] == b4["N"]) & b4["N"].isin([32, 64])]
            local_rows = full[full["method_variant"] == method]
            rows += paired_contrasts(
                global_rows, local_rows, f"{method}_global", f"{method}_local", "C", "locality",
                metrics=("normalized_regret", "final_success", "messages_to_epsilon_solution", "bytes_to_epsilon_solution"),
            )
    b6 = data[data["block_id"] == "B6"]
    if not b6.empty:
        rows += cvar_risk_contrasts(b6)
    return pd.DataFrame(rows)


def cvar_risk_contrasts(data: pd.DataFrame) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for stress_type, stress in data.groupby("stress_type", dropna=False):
        units = sorted(stress["unit_id"].dropna().unique())
        reference = "HUN" if "HUN" in units else units[0]
        left = stress[stress["unit_id"] == reference][["world_hash", "normalized_regret"]]
        for unit in units:
            if unit == reference:
                continue
            right = stress[stress["unit_id"] == unit][["world_hash", "normalized_regret"]]
            merged = left.merge(right, on="world_hash", suffixes=("_reference", "_candidate"))
            a = numeric(merged["normalized_regret_reference"])
            b = numeric(merged["normalized_regret_candidate"])
            valid = np.isfinite(a) & np.isfinite(b)
            a, b = a[valid], b[valid]
            if not len(a):
                estimate = low = high = p_value = math.nan
            else:
                estimate = cvar95(b) - cvar95(a)
                rng = np.random.default_rng(20260710)
                indices = rng.integers(0, len(a), size=(4000, len(a)))
                boot = np.asarray([cvar95(b[index]) - cvar95(a[index]) for index in indices])
                low, high = (float(value) for value in np.quantile(boot, [0.025, 0.975]))
                p_value = float(min(1.0, 2.0 * min(np.mean(boot <= 0), np.mean(boot >= 0))))
            output.append({
                "hypothesis_family": "R", "context": f"B6:{stress_type}",
                "contrast": f"{unit} - {reference}", "left_unit": reference, "right_unit": unit,
                "metric": "CVaR95_normalized_regret", "effect_scale": "paired_bootstrap_CVaR_difference",
                "effect_estimate": estimate, "CI95_low": low, "CI95_high": high,
                "raw_p": p_value, "Holm_adjusted_p": math.nan, "effect_size": estimate,
                "n_worlds": len(a), "failures": 0, "timeouts": 0, "margin": math.nan,
                "decision": "pending_holm",
            })
    return output

def paired_contrasts(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_name: str,
    right_name: str,
    family: str,
    context: str,
    *,
    metrics: tuple[str, ...] = ("normalized_regret", "final_success"),
) -> list[dict[str, Any]]:
    if left.empty or right.empty:
        return []
    keys = ["world_hash", "N", "K"]
    columns = keys + list(metrics) + ["continuous_timeout", "error_type"]
    columns = list(dict.fromkeys(column for column in columns if column in left and column in right))
    merged = left[columns].merge(right[columns], on=keys, suffixes=("_left", "_right"))
    if merged.empty:
        return []
    output = []
    for metric in metrics:
        a = numeric(merged[f"{metric}_left"])
        b = numeric(merged[f"{metric}_right"])
        valid = np.isfinite(a) & np.isfinite(b)
        if metric in {"messages_to_epsilon_solution", "bytes_to_epsilon_solution"}:
            difference = np.log1p(b[valid]) - np.log1p(a[valid])
            effect_scale = "paired_log_ratio"
        else:
            difference = b[valid] - a[valid]
            effect_scale = "paired_difference"
        estimate, low, high = paired_bca(difference)
        if family == "C" and context == "locality" and metric == "normalized_regret":
            p_value = noninferiority_bootstrap_p(difference, margin=0.05)
        else:
            p_value = mcnemar_p(a[valid], b[valid]) if metric == "final_success" else paired_wilcoxon_p(difference)
        timeout_columns = [name for name in ["continuous_timeout_left", "continuous_timeout_right"] if name in merged]
        error_columns = [name for name in ["error_type_left", "error_type_right"] if name in merged]
        output.append({
            "hypothesis_family": family,
            "context": context,
            "contrast": f"{right_name} - {left_name}",
            "left_unit": left_name,
            "right_unit": right_name,
            "metric": metric,
            "effect_scale": effect_scale,
            "effect_estimate": estimate,
            "CI95_low": low,
            "CI95_high": high,
            "raw_p": p_value,
            "Holm_adjusted_p": math.nan,
            "effect_size": estimate,
            "n_worlds": len(difference),
            "failures": int(sum(merged[name].notna().sum() for name in error_columns)),
            "timeouts": int(sum(merged[name].fillna(False).astype(bool).sum() for name in timeout_columns)),
            "margin": 0.05 if metric == "normalized_regret" else math.nan,
            "decision": "pending_holm",
        })
    return output
def apply_holm_by_family(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    result["Holm_adjusted_p"] = math.nan
    for _, indices in result.groupby("hypothesis_family").groups.items():
        idx = list(indices)
        p = result.loc[idx, "raw_p"].astype(float).to_numpy()
        finite_positions = np.flatnonzero(np.isfinite(p))
        if not finite_positions.size:
            continue
        finite_p = p[finite_positions]
        order = np.argsort(finite_p)
        adjusted = np.empty_like(finite_p)
        running = 0.0
        for rank, position in enumerate(order):
            running = max(running, min(1.0, (len(finite_p) - rank) * finite_p[position]))
            adjusted[position] = running
        result.loc[[idx[position] for position in finite_positions], "Holm_adjusted_p"] = adjusted
    result["decision"] = np.select(
        [result["Holm_adjusted_p"].isna(), result["Holm_adjusted_p"] < 0.05],
        ["not_estimable", "reject_H0"],
        default="fail_to_reject_H0",
    )
    return result
def fit_models(data: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    b4 = data[data["block_id"] == "B4"].dropna(subset=["normalized_regret"]).copy()
    if b4.empty:
        return pd.DataFrame(records)
    b4["logN"] = np.log(b4["N"].astype(float))
    b4["success_numeric"] = pd.to_numeric(b4["final_success"], errors="coerce").astype(float)
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except Exception as exc:
        return pd.DataFrame([model_record("statsmodels_import", "failed", str(exc))])

    builders: list[tuple[str, Callable[[], Any]]] = [
        ("mixed_regret_world_random_intercept", lambda: smf.mixedlm(
            "normalized_regret ~ C(unit_id)*C(regime) + C(unit_id)*logN",
            b4, groups=b4["world_hash"],
        ).fit(reml=False, method="lbfgs", maxiter=300)),
        ("robust_regret_GEE_world_cluster", lambda: smf.gee(
            "normalized_regret ~ C(unit_id)*C(regime) + C(unit_id)*logN",
            groups="world_hash", data=b4, family=sm.families.Gaussian(),
        ).fit()),
    ]
    if b4["success_numeric"].nunique(dropna=True) > 1:
        builders.append(("clustered_logistic_GEE", lambda: smf.gee(
            "success_numeric ~ C(unit_id)*C(regime) + C(unit_id)*logN",
            groups="world_hash", data=b4, family=sm.families.Binomial(),
        ).fit()))
    else:
        records.append(model_record("clustered_logistic_GEE", "not_estimable_no_variation"))

    b5 = data[data["block_id"] == "B5"].copy()
    if not b5.empty:
        connectivity = b5.dropna(subset=["normalized_regret", "lambda2", "occupancy_error"])
        if not connectivity.empty:
            builders.append(("connectivity_regret_GEE", lambda: smf.gee(
                "normalized_regret ~ C(unit_id)*lambda2 + C(unit_id)*occupancy_error",
                groups="world_hash", data=connectivity, family=sm.families.Gaussian(),
            ).fit()))
        for metric in ["messages_to_epsilon_solution", "bytes_to_epsilon_solution"]:
            count_data = b5.dropna(subset=[metric, "lambda2"]).copy()
            if not count_data.empty:
                builders.append((f"negative_binomial_{metric}_GEE", lambda metric=metric, count_data=count_data: smf.gee(
                    f"{metric} ~ C(unit_id)*lambda2",
                    groups="world_hash", data=count_data, family=sm.families.NegativeBinomial(),
                ).fit()))

    b2 = data[data["block_id"] == "B2"].copy()
    b2_required = {"normalized_regret", "dynamic_id", "fitness_id", "rounding_id"}
    b2 = b2.dropna(subset=sorted(b2_required)) if b2_required.issubset(b2.columns) else pd.DataFrame()
    if not b2.empty:
        builders.append(("exploratory_dynamic_fitness_closure_GEE", lambda: smf.gee(
            "normalized_regret ~ C(dynamic_id)*C(fitness_id) + C(dynamic_id)*C(rounding_id) + C(fitness_id)*C(rounding_id)",
            groups="world_hash", data=b2, family=sm.families.Gaussian(),
        ).fit()))

    b6 = data[data["block_id"] == "B6"].dropna(
        subset=["normalized_regret", "stress_type"]
    ).copy()
    if not b6.empty:
        builders.append(("robustness_method_stress_GEE", lambda: smf.gee(
            "normalized_regret ~ C(unit_id)*C(stress_type)",
            groups="world_hash", data=b6, family=sm.families.Gaussian(),
        ).fit()))

    support = b6[b6["stress_type"] == "G-BIAS_G-ZERO"].dropna(
        subset=["normalized_regret", "geometry_id"]
    ) if not b6.empty and "stress_type" in b6 else pd.DataFrame()
    if not support.empty:
        builders.append(("initial_support_method_geometry_GEE", lambda: smf.gee(
            "normalized_regret ~ C(unit_id)*C(geometry_id)",
            groups="world_hash", data=support, family=sm.families.Gaussian(),
        ).fit()))
    b7 = data[data["block_id"] == "B7"].dropna(subset=["normalized_regret", "N"]).copy()
    if not b7.empty:
        builders.append(("generalization_method_logN_GEE", lambda: smf.gee(
            "normalized_regret ~ C(unit_id)*np.log(N)",
            groups="world_hash", data=b7, family=sm.families.Gaussian(),
        ).fit()))
    for name, builder in builders:
        try:
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                fitted = builder()
            start_index = len(records)
            append_fitted_model(records, name, fitted)
            annotate_model_diagnostics(records, start_index, fitted, captured)
        except Exception as exc:
            records.append(model_record(name, "fit_failed", f"{type(exc).__name__}: {exc}"))

    try:
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
        mixed_data = b4.dropna(subset=["success_numeric"]).copy()
        if mixed_data["success_numeric"].nunique() > 1:
            model = BinomialBayesMixedGLM.from_formula(
                "success_numeric ~ C(unit_id) + C(regime) + logN",
                {"world_intercept": "0 + C(world_hash)"}, mixed_data,
            )
            fitted = model.fit_vb()
            for parameter, estimate, standard_error in zip(model.exog_names, fitted.fe_mean, fitted.fe_sd):
                z_value = float(estimate / max(float(standard_error), 1.0e-12))
                records.append({
                    "model": "mixed_logistic_world_random_intercept", "status": "fit",
                    "parameter": str(parameter), "estimate": float(estimate),
                    "CI95_low": float(estimate - 1.96 * standard_error),
                    "CI95_high": float(estimate + 1.96 * standard_error),
                    "raw_p": float(2.0 * stats.norm.sf(abs(z_value))), "error": None,
                })
            annotate_model_diagnostics(records, start_index, fitted, captured)
        else:
            records.append(model_record("mixed_logistic_world_random_intercept", "not_estimable_no_variation"))
    except Exception as exc:
        records.append(model_record("mixed_logistic_world_random_intercept", "fit_failed", f"{type(exc).__name__}: {exc}"))

    try:
        from statsmodels.duration.hazard_regression import PHReg
        survival = b4.dropna(subset=["time_to_epsilon_duration_s", "time_to_epsilon_observed"]).copy()
        survival = survival[pd.to_numeric(survival["time_to_epsilon_duration_s"], errors="coerce") > 0.0]
        survival["event"] = pd.to_numeric(survival["time_to_epsilon_observed"], errors="coerce").astype(int)
        if not survival.empty and survival["event"].sum() > 0:
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                fitted = PHReg.from_formula(
                    "time_to_epsilon_duration_s ~ C(unit_id) + C(regime) + logN",
                    status=survival["event"], data=survival, ties="efron",
                ).fit(groups=survival["world_hash"])
            start_index = len(records)
            append_fitted_model(records, "cox_time_to_epsilon_world_cluster", fitted)
            annotate_model_diagnostics(records, start_index, fitted, captured)
        else:
            records.append(model_record("cox_time_to_epsilon_world_cluster", "not_estimable_no_events"))
    except Exception as exc:
        records.append(model_record("cox_time_to_epsilon_world_cluster", "fit_failed", f"{type(exc).__name__}: {exc}"))
    return pd.DataFrame(records)


def append_fitted_model(records: list[dict[str, Any]], name: str, fitted: Any) -> None:
    params = fitted.params
    names = list(params.index) if hasattr(params, "index") else list(getattr(fitted.model, "exog_names", []))
    values = np.asarray(params, dtype=float).reshape(-1)
    if len(names) < len(values):
        names.extend(f"parameter_{index}" for index in range(len(names), len(values)))
    confidence = np.asarray(fitted.conf_int(), dtype=float)
    pvalues = np.asarray(getattr(fitted, "pvalues", np.full(len(values), np.nan)), dtype=float)
    for index, (parameter, estimate) in enumerate(zip(names, values)):
        low, high = confidence[index] if index < len(confidence) else (math.nan, math.nan)
        records.append({
            "model": name, "status": "fit", "parameter": str(parameter),
            "estimate": float(estimate), "CI95_low": float(low), "CI95_high": float(high),
            "raw_p": float(pvalues[index]) if index < len(pvalues) else math.nan, "error": None,
        })
    try:
        terms = fitted.wald_test_terms().table
        for term, row in terms.iterrows():
            statistic = float(np.asarray(row["statistic"], dtype=float).reshape(-1)[0])
            p_value = float(np.asarray(row["pvalue"], dtype=float).reshape(-1)[0])
            records.append({
                "model": name,
                "status": "wald_term",
                "parameter": f"TERM::{term}",
                "estimate": statistic,
                "CI95_low": math.nan,
                "CI95_high": math.nan,
                "raw_p": p_value,
                "error": None,
            })
    except Exception:
        pass
def annotate_model_diagnostics(
    records: list[dict[str, Any]],
    start_index: int,
    fitted: Any,
    captured: list[Any],
) -> None:
    warning_text = " | ".join(
        dict.fromkeys(f"{item.category.__name__}: {item.message}" for item in captured)
    ) or None
    converged = getattr(fitted, "converged", None)
    for row in records[start_index:]:
        row["model_converged"] = None if converged is None else bool(converged)
        row["warnings"] = warning_text
        if converged is False and row.get("status") in {"fit", "wald_term"}:
            row["status"] = "fit_nonconverged"

def model_record(model: str, status: str, error: str | None = None) -> dict[str, Any]:
    return {"model": model, "status": status, "parameter": None, "estimate": math.nan,
            "CI95_low": math.nan, "CI95_high": math.nan, "raw_p": math.nan, "error": error}


def summarize_prices(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (block, unit), group in data.groupby(["block_id", "unit_id"]):
        j = numeric(group["social_cost"])
        oracle = numeric(group["oracle_social_cost"])
        valid = np.isfinite(j) & np.isfinite(oracle)
        ratios = (1 + j[valid]) / (1 + oracle[valid])
        rows.append({"block_id": block, "unit_id": unit, "n": int(valid.sum()),
                     "observed_PoA": float(np.max(ratios)) if ratios.size else math.nan,
                     "observed_PoS": float(np.min(ratios)) if ratios.size else math.nan,
                     "claim_scope": "observed_only_not_theoretical"})
    return pd.DataFrame(rows)


def build_rankings(runs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    specifications = [
        ("continuous_dynamics_only", runs[runs["block_id"].isin(["B2", "B3"])], "continuous_normalized_regret"),
        ("after_ARG", runs[runs["preclosure_normalized_regret"].notna()], "preclosure_normalized_regret"),
        ("after_REPAIR", runs[runs["rounding_id"].isin(["REPAIR", "POLICY_REPAIR"])], "normalized_regret"),
        ("after_QR1", runs[runs["rounding_id"] == "QR1"], "normalized_regret"),
        ("after_QR2", runs[runs["rounding_id"] == "QR2"], "normalized_regret"),
        ("after_QRA", runs[runs["rounding_id"] == "QRA"], "normalized_regret"),
        ("distributed_local_only", runs[runs["architecture"] == "distributed_local"], "normalized_regret"),
        ("global_information", runs[runs["architecture"].isin(["centralized", "distributed_global"])], "normalized_regret"),
        ("data_driven_final_checkpoint", runs[runs["method_family"] == "data_driven"], "normalized_regret"),
    ]
    for ranking, frame, metric in specifications:
        if frame.empty or metric not in frame:
            continue
        for rank, (unit, value) in enumerate(frame.groupby("unit_id")[metric].mean().sort_values().items(), 1):
            rows.append({"ranking_id": ranking, "rank": rank, "unit_id": unit, "metric": metric, "value": value})

    b4 = runs[runs["block_id"] == "B4"]
    for regime, frame in b4.groupby("regime") if not b4.empty else []:
        summary = frame.groupby("unit_id").agg(
            normalized_regret=("normalized_regret", "mean"),
            runtime_wall_s=("runtime_wall_s", "mean"),
            messages=("messages", "mean"),
        ).dropna()
        nondominated = []
        for unit, candidate in summary.iterrows():
            dominated = any(
                bool((other <= candidate).all() and (other < candidate).any())
                for other_unit, other in summary.iterrows() if other_unit != unit
            )
            if not dominated:
                nondominated.append((unit, candidate))
        for rank, (unit, candidate) in enumerate(sorted(nondominated, key=lambda item: item[1]["normalized_regret"]), 1):
            rows.append({
                "ranking_id": f"Pareto_by_regime::{regime}", "rank": rank, "unit_id": unit,
                "metric": "normalized_regret|runtime_wall_s|messages",
                "value": float(candidate["normalized_regret"]),
            })
    return pd.DataFrame(rows)


def hypothesis_decisions(contrasts: pd.DataFrame, models: pd.DataFrame) -> pd.DataFrame:
    config = yaml.safe_load(Path("configs/experiments/sp0/SP0_PROTOCOL_v1_1.yaml").read_text(encoding="utf-8"))

    def contrast_rows(*, family: str, metric: str, context: str | None = None) -> pd.DataFrame:
        if contrasts.empty:
            return pd.DataFrame()
        selected = contrasts[(contrasts["hypothesis_family"] == family) & (contrasts["metric"] == metric)]
        return selected[selected["context"] == context] if context is not None else selected

    def model_rows(model: str, term: str) -> pd.DataFrame:
        if models.empty:
            return pd.DataFrame()
        return models[(models["model"] == model) & (models["parameter"] == f"TERM::{term}")]

    selectors: dict[str, Callable[[], pd.DataFrame]] = {
        "H0-SP0-P1": lambda: contrast_rows(family="P", metric="final_success"),
        "H0-SP0-P2": lambda: contrast_rows(family="P", metric="normalized_regret"),
        "H0-SP0-P3": lambda: model_rows("cox_time_to_epsilon_world_cluster", "C(unit_id)"),
        "H0-SP0-P4": lambda: pd.concat([
            model_rows("negative_binomial_messages_to_epsilon_solution_GEE", "C(unit_id)"),
            model_rows("negative_binomial_bytes_to_epsilon_solution_GEE", "C(unit_id)"),
        ], ignore_index=True),
        "H0-SP0-P5": lambda: model_rows("robust_regret_GEE_world_cluster", "C(unit_id):C(regime)"),
        "H0-SP0-P6": lambda: model_rows("robust_regret_GEE_world_cluster", "C(unit_id):logN"),
        "H0-SP0-C1": lambda: contrast_rows(family="C", metric="normalized_regret", context="locality"),
        "H0-SP0-C2": lambda: model_rows("connectivity_regret_GEE", "C(unit_id):lambda2"),
        "H0-SP0-C3": lambda: model_rows("connectivity_regret_GEE", "C(unit_id):occupancy_error"),
        "H0-SP0-R1": lambda: contrast_rows(family="R", metric="CVaR95_normalized_regret"),
        "H0-SP0-R2": lambda: model_rows("generalization_method_logN_GEE", "C(unit_id):np.log(N)"),
        "H0-SP0-R3": lambda: model_rows("robustness_method_stress_GEE", "C(unit_id):C(stress_type)"),
        "H0-SP0-R4": lambda: model_rows("initial_support_method_geometry_GEE", "C(unit_id):C(geometry_id)"),
    }
    rows: list[dict[str, Any]] = []
    for item in config.get("hypotheses", []):
        hypothesis_id = str(item["id"])
        family = str(item["family"])
        status = str(item.get("status", "confirmatory"))
        if status.startswith("exploratory"):
            rows.append({
                "hypothesis_id": hypothesis_id, "family": family, "status": status,
                "outcome": item.get("outcome"), "effect_estimate": math.nan,
                "CI95_low": math.nan, "CI95_high": math.nan, "raw_p": math.nan,
                "Holm_adjusted_p": math.nan, "decision": "exploratory_only",
                "claim_permitted": "exploratory_only", "source": "B2_exploratory",
            })
            continue
        selected = selectors.get(hypothesis_id, lambda: pd.DataFrame())()
        selected = selected[pd.to_numeric(selected.get("raw_p"), errors="coerce").notna()] if not selected.empty else selected
        if selected.empty:
            rows.append({
                "hypothesis_id": hypothesis_id, "family": family, "status": status,
                "outcome": item.get("outcome"), "effect_estimate": math.nan,
                "CI95_low": math.nan, "CI95_high": math.nan, "raw_p": math.nan,
                "Holm_adjusted_p": math.nan, "decision": "not_estimable",
                "claim_permitted": "not_supported", "source": "missing_or_nonestimable",
            })
            continue
        pvalues = pd.to_numeric(selected["raw_p"], errors="coerce").to_numpy(dtype=float)
        best_position = int(np.nanargmin(pvalues))
        representative = selected.iloc[best_position]
        raw_p = min(1.0, float(np.nanmin(pvalues)) * len(pvalues))
        rows.append({
            "hypothesis_id": hypothesis_id, "family": family, "status": status,
            "outcome": item.get("outcome"),
            "effect_estimate": safe_series_value(representative, "effect_estimate", "estimate"),
            "CI95_low": safe_series_value(representative, "CI95_low"),
            "CI95_high": safe_series_value(representative, "CI95_high"),
            "raw_p": raw_p, "Holm_adjusted_p": math.nan, "decision": "pending_holm",
            "claim_permitted": "pending_holm",
            "source": str(representative.get("context", representative.get("model", "unknown"))),
            "within_hypothesis_Bonferroni_m": len(pvalues),
            "margin": item.get("margin"),
        })
    result = pd.DataFrame(rows)
    for family, indices in result[result["status"] == "confirmatory"].groupby("family").groups.items():
        idx = list(indices)
        p = pd.to_numeric(result.loc[idx, "raw_p"], errors="coerce").to_numpy(dtype=float)
        finite = np.flatnonzero(np.isfinite(p))
        order = finite[np.argsort(p[finite])] if finite.size else np.asarray([], dtype=int)
        running = 0.0
        for rank, position in enumerate(order):
            running = max(running, min(1.0, (len(finite) - rank) * p[position]))
            result.loc[idx[position], "Holm_adjusted_p"] = running
    for index, row in result.iterrows():
        adjusted = row.get("Holm_adjusted_p")
        if not np.isfinite(float(adjusted)) if adjusted is not None else True:
            continue
        reject = float(adjusted) < 0.05
        if row["hypothesis_id"] == "H0-SP0-C1":
            upper = float(row.get("CI95_high", math.nan))
            reject = reject and np.isfinite(upper) and upper < float(row.get("margin", 0.05))
            result.loc[index, "decision"] = "reject_H0_noninferior" if reject else "fail_to_show_noninferiority"
        else:
            result.loc[index, "decision"] = "reject_H0" if reject else "fail_to_reject_H0"
        result.loc[index, "claim_permitted"] = "empirically_supported" if reject else "not_supported"
    return result


def safe_series_value(row: pd.Series, *names: str) -> float:
    for name in names:
        value = row.get(name)
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(numeric_value):
            return numeric_value
    return math.nan
def write_required_tables(folder: Path, runs: pd.DataFrame, primary: pd.DataFrame, hypotheses: pd.DataFrame, rankings: pd.DataFrame) -> None:
    tables = {
        "T01_SP0_definition.csv": pd.DataFrame([{"scope": "homogeneous_one_to_one", "oracle": "Hungarian"}]),
        "T02_method_taxonomy.csv": runs[["method_family", "method_variant", "architecture"]].drop_duplicates(),
        "T03_dynamics.csv": pd.DataFrame({"dynamic": ["REP", "SMI", "BNN", "LOG", "PROJ", "IBR", "GPC", "HYB"]}),
        "T04_fitness.csv": pd.DataFrame({"fitness": ["LIN", "QUAD", "ASYM", "SIG", "MC"]}),
        "T05_integer_closures.csv": pd.DataFrame({
            "closure": ["RAW", "ARG", "REPAIR", "QR1", "QR2", "QRA"],
            "scope": ["continuous", "independent_decode", "greedy_conflict_repair", "unilateral", "unilateral_and_swaps", "alternating_paths_cycles"],
            "global_strong_closure": [False, False, False, False, False, True],
        }),
        "T06_hyperparameters.csv": pd.DataFrame([{"source": "frozen_protocol_v1_1.yaml"}]),
        "T07_worlds.csv": runs[["geometry_id", "N", "K", "R", "lambda2", "num_components"]].drop_duplicates(),
        "T09_metrics.csv": pd.DataFrame({"metric": [
            "final_success", "normalized_regret", "continuous_normalized_regret",
            "preclosure_normalized_regret", "closure_vs_preclosure_regret_delta",
            "final_vs_continuous_regret_delta", "time_to_epsilon_solution",
            "messages_to_epsilon_solution", "bytes_to_epsilon_solution",
        ]}),
        "T11_resources.csv": primary[["unit_id", "mean_runtime_wall_s", "mean_messages", "mean_bytes"]].drop_duplicates(),
        "T13_robustness.csv": primary[primary["block_id"] == "B6"],
        "T14_generalization.csv": primary[primary["block_id"] == "B7"],
        "T15_claims.csv": hypotheses,
        "T16_rankings.csv": rankings,
    }
    for name, frame in tables.items():
        frame.to_csv(folder / name, index=False)

def generate_figures(root: Path, runs: pd.DataFrame) -> dict[str, Any]:
    folder = ensure_directory(root / "figures")
    builders: list[tuple[str, Callable[[], plt.Figure]]] = [
        ("F01_architectures", figure_architectures),
        ("F02_method_taxonomy", figure_taxonomy),
        ("F03_dynamic_fitness_success_heatmap", lambda: figure_heatmap(runs, "final_success")),
        ("F04_dynamic_fitness_regret_heatmap", lambda: figure_heatmap(runs, "normalized_regret")),
        ("F05_dynamic_fitness_interaction", lambda: figure_interaction(runs)),
        ("F06_performance_by_regime", lambda: figure_grouped(runs, "regime", "normalized_regret", "B4")),
        ("F07_scaling_vs_N", lambda: figure_lines(runs, "N", "runtime_wall_s", "B4")),
        ("F08_lambda2_vs_success", lambda: figure_lines(runs, "lambda2", "final_success", "B5")),
        ("F09_lambda2_vs_regret", lambda: figure_lines(runs, "lambda2", "normalized_regret", "B5")),
        ("F10_quality_vs_messages_pareto", lambda: figure_pareto(runs, "messages")),
        ("F11_quality_vs_runtime_pareto", lambda: figure_pareto(runs, "runtime_wall_s")),
        ("F12_closure_ablation", lambda: figure_grouped(runs, "rounding_id", "normalized_regret", None)),
        ("F13_continuous_vs_closed_performance", lambda: figure_continuous_closed(runs)),
        ("F14_potential_equilibrium_fractionality_time", lambda: figure_trajectory(root)),
        ("F15_time_to_solution_survival", lambda: figure_survival(runs)),
        ("F16_stress_heatmap", lambda: figure_stress(runs)),
        ("F17_generalization", lambda: figure_lines(runs, "N", "normalized_regret", "B7")),
        ("F18_IPPO_MAPPO_training_curves", lambda: figure_training(root, "mean_NR")),
        ("F19_training_seed_variability", lambda: figure_training(root, "success")),
        ("F20_confirmatory_forest_plot", lambda: figure_forest(root)),
        ("F21_observed_PoA", lambda: figure_prices(root)),
        ("F22_training_budget_vs_performance", lambda: figure_training(root, "mean_NR")),
    ]
    files = []
    for name, builder in builders:
        fig = builder()
        for suffix in ["png", "pdf", "svg"]:
            target = folder / f"{name}.{suffix}"
            fig.savefig(target, dpi=180 if suffix == "png" else None, bbox_inches="tight")
            files.append(str(target))
        plt.close(fig)
    write_tikz(folder / "F01_architectures_tikz.tex")
    return {"status": "complete", "figure_count": len(builders), "files": files}


def base_figure(title: str) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.set_title(title)
    ax.grid(alpha=0.25)
    return fig, ax


def figure_architectures() -> plt.Figure:
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.2))
    for ax, title in zip(axes, ["Centralized", "Distributed global", "Distributed local", "Observe-Fitness-Dynamics-Closure"]):
        ax.set_title(title, fontsize=9)
        ax.set_axis_off()
        x = np.linspace(0.15, 0.85, 5)
        y = np.array([0.25, 0.75, 0.35, 0.7, 0.45])
        ax.scatter(x, y, color="#2878b5")
        for index in range(4):
            if title != "Distributed local" or index % 2 == 0:
                ax.plot(x[index:index + 2], y[index:index + 2], color="0.5")
    fig.suptitle("SP0 architectures")
    return fig


def figure_taxonomy() -> plt.Figure:
    fig, ax = base_figure("SP0 method taxonomy")
    ax.set_axis_off()
    rows = [
        ("Centralized", "HUN"),
        ("Classic distributed", "GRD, EPS-AUCTION"),
        ("Population", "REP, SMI, BNN, LOG, PROJ, IBR, GPC, HYB"),
        ("Data-driven", "IPPO-GNN, MAPPO-GNN"),
    ]
    for index, (family, methods) in enumerate(rows):
        y = 0.85 - 0.2 * index
        ax.text(0.05, y, family, weight="bold")
        ax.text(0.32, y, methods)
    return fig


def figure_heatmap(runs: pd.DataFrame, metric: str) -> plt.Figure:
    frame = runs[runs["block_id"] == "B2"] if not runs.empty else runs
    fig, ax = base_figure(f"Dynamic x fitness: {metric}; exploratory B2; n={len(frame)}")
    if frame.empty or metric not in frame:
        return fig
    pivot = frame.pivot_table(index="dynamic_id", columns="fitness_id", values=metric, aggfunc="mean")
    image = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    fig.colorbar(image, ax=ax)
    return fig


def figure_interaction(runs: pd.DataFrame) -> plt.Figure:
    frame = runs[runs["block_id"] == "B2"] if not runs.empty else runs
    fig, ax = base_figure(f"Dynamic x fitness interaction; exploratory; n={len(frame)}")
    if frame.empty:
        return fig
    fitness_order = [value for value in ["LIN", "QUAD", "ASYM", "SIG", "MC"] if value in set(frame["fitness_id"])]
    for dynamic, dynamic_rows in frame.groupby("dynamic_id"):
        means, lows, highs = [], [], []
        for fitness in fitness_order:
            values = numeric(dynamic_rows[dynamic_rows["fitness_id"] == fitness]["normalized_regret"])
            mean = finite_mean(values)
            low, high = bootstrap_ci(values)
            means.append(mean); lows.append(mean - low); highs.append(high - mean)
        ax.errorbar(fitness_order, means, yerr=[lows, highs], marker="o", capsize=2, label=dynamic)
    ax.legend(fontsize=6, ncol=2)
    ax.set_ylabel("Normalized regret")
    return fig
def figure_grouped(runs: pd.DataFrame, category: str, metric: str, block: str | None) -> plt.Figure:
    frame = runs[runs["block_id"] == block] if block and not runs.empty else runs
    fig, ax = base_figure(f"{metric} by {category}; n={len(frame)}")
    if frame.empty or category not in frame or metric not in frame:
        return fig
    labels, means, lows, highs = [], [], [], []
    for label, group in frame.groupby(category, dropna=False, sort=False):
        values = numeric(group[metric])
        mean = finite_mean(values)
        low, high = bootstrap_ci(values)
        labels.append(str(label)); means.append(mean); lows.append(mean - low); highs.append(high - mean)
    positions = np.arange(len(labels))
    ax.bar(positions, means, yerr=[lows, highs], capsize=3)
    ax.set_xticks(positions, labels, rotation=20)
    ax.set_ylabel(metric)
    return fig
def figure_lines(runs: pd.DataFrame, x: str, y: str, block: str) -> plt.Figure:
    frame = runs[runs["block_id"] == block] if not runs.empty else runs
    fig, ax = base_figure(f"{x} vs {y}; n={len(frame)}")
    if frame.empty or x not in frame or y not in frame:
        return fig
    for method, group in frame.groupby("method_variant"):
        x_values, means, lows, highs = [], [], [], []
        for x_value, cell in group.groupby(x, dropna=False):
            values = numeric(cell[y])
            mean = finite_mean(values)
            low, high = bootstrap_ci(values)
            x_values.append(x_value); means.append(mean); lows.append(mean - low); highs.append(high - mean)
        order = np.argsort(np.asarray(x_values, dtype=float))
        ordered_x = np.asarray(x_values)[order]
        ax.errorbar(
            ordered_x, np.asarray(means)[order],
            yerr=[np.asarray(lows)[order], np.asarray(highs)[order]],
            marker="o", capsize=2, label=method,
        )
    ax.set_xlabel(x); ax.set_ylabel(y)
    ax.legend(fontsize=6, ncol=3)
    return fig
def figure_pareto(runs: pd.DataFrame, resource: str) -> plt.Figure:
    frame = runs[runs["block_id"] == "B4"] if not runs.empty else runs
    fig, ax = base_figure(f"Quality vs {resource}; n={len(frame)}")
    if frame.empty:
        return fig
    summary = frame.groupby("unit_id").agg(quality=("normalized_regret", "mean"), resource=(resource, "mean"))
    for unit, row in summary.iterrows():
        ax.scatter(row["resource"], row["quality"])
        ax.annotate(unit, (row["resource"], row["quality"]), fontsize=6)
    ax.set_xlabel(resource)
    ax.set_ylabel("Normalized regret")
    return fig


def figure_continuous_closed(runs: pd.DataFrame) -> plt.Figure:
    fig, ax = base_figure("Continuous vs closed performance")
    if not runs.empty:
        frame = runs.dropna(subset=["continuous_normalized_regret", "normalized_regret"])
        ax.scatter(frame["continuous_normalized_regret"], frame["normalized_regret"], alpha=0.2)
    ax.set_xlabel("Continuous NR")
    ax.set_ylabel("Closed NR")
    return fig


def figure_trajectory(root: Path) -> plt.Figure:
    fig, axes = plt.subplots(2, 2, figsize=(9, 6))
    paths = sorted((root / "audit" / "trajectories").rglob("*.npz"))
    trajectory = None
    if paths:
        with np.load(paths[0], allow_pickle=False) as data:
            trajectory = {key: data[key] for key in data.files}
    for ax, key in zip(axes.ravel(), ["potential", "equilibrium_residual", "fractionality", "switches"]):
        if trajectory and key in trajectory:
            ax.plot(trajectory.get("time_s", np.arange(len(trajectory[key]))), trajectory[key])
        ax.set_title(key)
        ax.grid(alpha=0.25)
    return fig


def figure_survival(runs: pd.DataFrame) -> plt.Figure:
    frame = runs[runs["block_id"] == "B4"] if not runs.empty else runs
    fig, ax = base_figure("Time to useful solution; timeouts/failures censored")
    for method, group in frame.groupby("method_variant") if not frame.empty else []:
        durations = pd.to_numeric(group["time_to_epsilon_duration_s"], errors="coerce").to_numpy(dtype=float)
        events = pd.to_numeric(group["time_to_epsilon_observed"], errors="coerce").fillna(0).to_numpy(dtype=int)
        valid = np.isfinite(durations) & (durations >= 0.0)
        durations, events = durations[valid], events[valid]
        if not durations.size:
            continue
        survival = 1.0
        x_values = [0.0]
        y_values = [1.0]
        for time_value in np.unique(durations):
            at_risk = int(np.sum(durations >= time_value))
            observed = int(np.sum((durations == time_value) & (events == 1)))
            if at_risk > 0 and observed > 0:
                survival *= 1.0 - observed / at_risk
            x_values.append(float(time_value))
            y_values.append(float(survival))
        ax.step(x_values, y_values, where="post", label=f"{method} (n={len(durations)})")
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=6)
    ax.set_xlabel("Simulated time to useful solution (s)")
    ax.set_ylabel("P(solution not yet reached)")
    return fig
def figure_stress(runs: pd.DataFrame) -> plt.Figure:
    frame = runs[runs["block_id"] == "B6"] if not runs.empty else runs
    fig, ax = base_figure(f"Stress tests; n={len(frame)}")
    if frame.empty or "stress_type" not in frame:
        return fig
    pivot = frame.pivot_table(index="method_variant", columns="stress_type", values="normalized_regret", aggfunc="mean")
    image = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="magma")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns, rotation=20)
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    fig.colorbar(image, ax=ax)
    return fig


def training_frame(root: Path) -> pd.DataFrame:
    training_root = root / "training"
    metadata_paths = sorted(training_root.rglob("metadata.json"))
    official_paths = [path for path in metadata_paths if "dry_run" not in path.relative_to(training_root).parts]
    selected_paths = official_paths or metadata_paths
    rows = []
    for path in selected_paths:
        metadata = json.loads(path.read_text(encoding="utf-8"))
        for point in metadata.get("history", []):
            validation = point.get("validation", {})
            rows.append({"algorithm": metadata.get("algorithm"), "train_seed": metadata.get("train_seed"),
                         "training_steps": point.get("training_steps"), "mean_NR": validation.get("mean_NR"),
                         "success": validation.get("success"),
                         "artifact_scope": "official" if path in official_paths else "exploratory_debug_only"})
    return pd.DataFrame(rows)


def figure_training(root: Path, metric: str) -> plt.Figure:
    frame = training_frame(root)
    scope = "no data" if frame.empty else str(frame["artifact_scope"].iloc[0])
    fig, ax = base_figure(f"Training {metric}; scope={scope}; n={len(frame)}")
    for (algorithm, seed), group in frame.groupby(["algorithm", "train_seed"]) if not frame.empty else []:
        ax.plot(group["training_steps"], group[metric], label=f"{algorithm}:{seed}")
    ax.set_xlabel("Environment steps")
    ax.set_ylabel(metric)
    if not frame.empty:
        ax.legend(fontsize=6)
    return fig


def figure_forest(root: Path) -> plt.Figure:
    path = root / "statistics" / "confirmatory_contrasts.parquet"
    frame = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    fig, ax = base_figure("Confirmatory forest plot")
    if frame.empty:
        return fig
    selected = frame[frame["metric"] == "normalized_regret"].head(20).reset_index(drop=True)
    y = np.arange(len(selected))
    ax.errorbar(selected["effect_estimate"], y,
                xerr=[selected["effect_estimate"] - selected["CI95_low"],
                      selected["CI95_high"] - selected["effect_estimate"]], fmt="o")
    ax.axvline(0, color="black")
    ax.set_yticks(y, selected["contrast"], fontsize=6)
    return fig


def figure_prices(root: Path) -> plt.Figure:
    path = root / "statistics" / "observed_prices.parquet"
    frame = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    fig, ax = base_figure("Observed PoA (test set only)")
    if not frame.empty:
        frame.groupby("unit_id")["observed_PoA"].max().sort_values().plot(kind="bar", ax=ax)
    return fig


def write_tikz(path: Path) -> None:
    path.write_text(
        "\\begin{tikzpicture}[node distance=8mm]\n"
        "\\node (obs) {Perception};\\node[right=of obs] (fit) {Fitness};\n"
        "\\node[right=of fit] (dyn) {Dynamics};\\node[right=of dyn] (qr) {Closure};\n"
        "\\node[right=of qr] (asg) {Assignment};\\draw[->] (obs)--(fit)--(dyn)--(qr)--(asg);\n"
        "\\end{tikzpicture}\n", encoding="utf-8")

def generate_videos(root: Path, runs: pd.DataFrame) -> dict[str, Any]:
    folder = ensure_directory(root / "videos")
    dry_path = root / "smoke" / "integral_dry_run_runs.parquet"
    dry = pd.read_parquet(dry_path) if dry_path.exists() else pd.DataFrame()
    combined = pd.concat([runs, dry], ignore_index=True, sort=False) if not dry.empty else runs
    official_rows = int(len(runs))
    dry_rows = int(len(dry))
    artifact_scope = "official_posthoc" if official_rows else "exploratory_debug_only"
    selectors: list[tuple[str, Callable[[pd.DataFrame], pd.DataFrame]]] = [
        ("V01_balanced_nominal", lambda f: f[(f["N"] == f["K"]) & (f["N"] == 16)]),
        ("V02_robot_scarcity", lambda f: f[f["K"] > f["N"]]),
        ("V03_robot_surplus", lambda f: f[f["K"] < f["N"]]),
        ("V04_communication_sweep", lambda f: f[(f["block_id"] == "B5") | f.get("dry_case", pd.Series(index=f.index, dtype=str)).isin(["connected_local", "disconnected"])]),
        ("V05_RAW_ARG_REPAIR_QR1_QR2_QRA", lambda f: f[f["rounding_id"].isin(["RAW", "ARG", "REPAIR", "QR1", "QR2", "QRA"])]),
        ("V06_REP_support_failure_vs_LOG_and_HYB", lambda f: f[f["method_variant"].isin(["REP", "LOG", "HYB"])]),
        ("V07_crossed_matching_QR1_vs_QR2_vs_QRA", lambda f: f[(f["geometry_id"] == "G-X") & f["rounding_id"].isin(["QR1", "QR2", "QRA"])]),
        ("V08_generalization_N48", lambda f: f[f["N"] == 48]),
        ("V09_worst_CVaR_case", lambda f: f.sort_values("normalized_regret", ascending=False)),
        ("V10_data_driven_success_and_failure_seed", lambda f: f[f["method_family"].astype(str).str.startswith("data_driven")]),
    ]
    generated, skipped = [], []
    for name, selector in selectors:
        try:
            selected = selector(combined)
            if "trajectory_path" not in selected:
                selected = pd.DataFrame()
            else:
                selected = selected[selected["trajectory_path"].notna()]
            paths = [Path(value) for value in selected.get("trajectory_path", []) if Path(str(value)).exists()]
            paths = list(dict.fromkeys(paths))[:4]
            if not paths:
                skipped.append({"name": name, "reason": "no stored trajectory"})
                continue
            output = folder / f"{name}.mp4"
            render_video(paths, output, f"{name} | {artifact_scope}")
            generated.append(str(output))
        except Exception as exc:
            skipped.append({"name": name, "reason": f"{type(exc).__name__}: {exc}"})
    status = "complete" if len(generated) == len(selectors) else "incomplete"
    save_json(folder / "video_manifest.json", {
        "status": status, "artifact_scope": artifact_scope, "official_run_rows": official_rows,
        "exploratory_dry_run_rows": dry_rows, "generated": generated, "skipped": skipped,
    })
    return {"status": status, "generated": generated, "skipped": skipped, "expected": len(selectors)}


def render_video(paths: list[Path], output: Path, title: str) -> None:
    trajectories = []
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            trajectory = {key: data[key] for key in data.files}
        labels = np.asarray(
            trajectory.get("argmax_labels", trajectory["final_labels"][None, :]),
            dtype=int,
        )
        if labels.ndim == 1:
            labels = labels[None, :]
        final_labels = np.asarray(trajectory["final_labels"], dtype=int)
        times = np.asarray(trajectory.get("time_s", np.zeros(len(labels))), dtype=float)
        if not len(times):
            times = np.zeros(len(labels), dtype=float)
        final_appended = bool(not len(labels) or not np.array_equal(labels[-1], final_labels))
        if final_appended:
            labels = np.vstack([labels, final_labels]) if len(labels) else final_labels[None, :]
            final_time = float(scalar_value(trajectory.get("simulation_end_time_s"), times[-1] if len(times) else 0.0))
            times = np.append(times, final_time)
        trajectory["render_labels"] = labels
        trajectory["render_times"] = times
        trajectory["render_final_appended"] = np.asarray(int(final_appended), dtype=np.int8)
        trajectories.append(trajectory)
    frame_count = max(max(len(item["render_labels"]), 1) for item in trajectories)
    indices = np.unique(np.linspace(0, frame_count - 1, min(frame_count, 50)).astype(int))
    directory = output.parent / f".{output.stem}_frames"
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    try:
        for frame_index, source_index in enumerate(indices):
            fig, axes = plt.subplots(1, len(trajectories), figsize=(5.2 * len(trajectories), 5.0), squeeze=False)
            for ax, trajectory in zip(axes[0], trajectories):
                robots, loads = trajectory["robot_xy"], trajectory["load_xy"]
                series = trajectory["render_labels"]
                index = min(source_index, len(series) - 1)
                labels = series[index]
                ax.scatter(loads[:, 0], loads[:, 1], marker="s", color="#d1495b")
                ax.scatter(robots[:, 0], robots[:, 1], color="#2878b5")
                for robot_index, label in enumerate(labels):
                    if 1 <= int(label) <= len(loads):
                        ax.plot(
                            [robots[robot_index, 0], loads[int(label) - 1, 0]],
                            [robots[robot_index, 1], loads[int(label) - 1, 1]],
                            color="0.55", lw=0.7,
                        )
                times = trajectory["render_times"]
                t = float(times[min(index, len(times) - 1)]) if len(times) else 0.0
                residual = np.asarray(trajectory.get("equilibrium_residual", [math.nan]), dtype=float)
                potential = np.asarray(trajectory.get("potential", [math.nan]), dtype=float)
                e = float(residual[min(index, len(residual) - 1)]) if len(residual) else math.nan
                phi = float(potential[min(index, len(potential) - 1)]) if len(potential) else math.nan
                coverage, regret = trajectory_assignment_metrics(trajectory, labels)
                messages = trajectory_messages_at_frame(trajectory, index, len(series))
                method = str(scalar_value(trajectory.get("method_variant"), "method"))
                world_seed = int(scalar_value(trajectory.get("world_seed"), -1))
                train_seed = int(scalar_value(trajectory.get("train_seed"), -1))
                converged = int(scalar_value(trajectory.get("continuous_converged"), -1))
                lambda2 = float(scalar_value(trajectory.get("lambda2"), math.nan))
                components = int(scalar_value(trajectory.get("num_components"), -1))
                closure = str(scalar_value(trajectory.get("closure_type"), "none"))
                train_text = "n/a" if train_seed < 0 else str(train_seed)
                convergence_text = {1: "yes", 0: "no"}.get(converged, "n/a")
                ax.set_title(
                    f"{method} | world={world_seed} | train={train_text}\n"
                    f"t={t:.2f}s | continuous={convergence_text} | closure={closure}\n"
                    f"coverage={coverage:.3f} | NR={regret:.4f} | messages={messages}\n"
                    f"potential={phi:.4g} | epsilon_NE={e:.3g} | lambda2={lambda2:.3g} | components={components}",
                    fontsize=7,
                )
                ax.set_aspect("equal")
                ax.grid(alpha=0.2)
            fig.suptitle(title)
            fig.tight_layout()
            fig.savefig(directory / f"frame_{frame_index:04d}.png", dpi=110)
            plt.close(fig)
        completed = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i",
             str(directory / "frame_%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output)],
            capture_output=True, text=True,
        )
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip() or "ffmpeg failed")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def scalar_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    array = np.asarray(value)
    return array.reshape(-1)[0].item() if array.size else default


def trajectory_assignment_metrics(trajectory: dict[str, Any], labels: np.ndarray) -> tuple[float, float]:
    labels = np.asarray(labels, dtype=int)
    cost = np.asarray(trajectory.get("cost_matrix", np.empty((len(labels), 0))), dtype=float)
    s_star = int(scalar_value(trajectory.get("s_star"), min(len(labels), cost.shape[1])))
    positive = (labels > 0) & (labels <= cost.shape[1])
    covered = len(np.unique(labels[positive]))
    cost_sum = sum(float(cost[index, label - 1]) for index, label in enumerate(labels) if 1 <= label <= cost.shape[1])
    penalty = float(s_star + 1)
    duplicates = max(0, int(np.sum(positive)) - covered)
    objective = penalty * (s_star - covered + duplicates) + cost_sum
    oracle = float(scalar_value(trajectory.get("oracle_j_posthoc"), 0.0))
    denominator = float((s_star + 1) * s_star + s_star)
    return covered / max(s_star, 1), max(objective - oracle, 0.0) / max(denominator, 1.0e-12)


def trajectory_messages_at_frame(trajectory: dict[str, Any], index: int, frame_count: int) -> int:
    total = int(scalar_value(trajectory.get("messages_total"), 0))
    closure = int(scalar_value(trajectory.get("closure_messages"), 0))
    final_appended = bool(int(scalar_value(trajectory.get("render_final_appended"), 0)))
    if final_appended and index == frame_count - 1:
        return total
    iterations = max(int(scalar_value(trajectory.get("iterations"), frame_count)), 1)
    return int(math.ceil(max(total - closure, 0) * min(index + 1, iterations) / iterations))
def numeric(series: pd.Series) -> np.ndarray:
    return pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)


def finite_mean(values: np.ndarray) -> float:
    values = values[np.isfinite(values)]
    return float(np.mean(values)) if values.size else math.nan


def finite_median(values: np.ndarray) -> float:
    values = values[np.isfinite(values)]
    return float(np.median(values)) if values.size else math.nan


def cvar95(values: np.ndarray) -> float:
    values = values[np.isfinite(values)]
    if not values.size:
        return math.nan
    threshold = np.quantile(values, 0.95)
    return float(np.mean(values[values >= threshold]))


def bootstrap_ci(values: np.ndarray, samples: int = 2000) -> tuple[float, float]:
    values = values[np.isfinite(values)]
    if not values.size:
        return math.nan, math.nan
    if len(values) == 1 or np.allclose(values, values[0]):
        return float(values[0]), float(values[0])
    rng = np.random.default_rng(20260710)
    means = np.mean(values[rng.integers(0, len(values), size=(samples, len(values)))], axis=1)
    return tuple(float(value) for value in np.quantile(means, [0.025, 0.975]))


def paired_bca(values: np.ndarray, samples: int = 4000) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not values.size:
        return math.nan, math.nan, math.nan
    estimate = float(np.mean(values))
    if len(values) == 1 or np.allclose(values, values[0]):
        return estimate, estimate, estimate
    rng = np.random.default_rng(20260710)
    boot = np.mean(values[rng.integers(0, len(values), size=(samples, len(values)))], axis=1)
    proportion = np.clip(np.mean(boot < estimate), 1 / (2 * samples), 1 - 1 / (2 * samples))
    z0 = stats.norm.ppf(proportion)
    jack = np.array([np.mean(np.delete(values, index)) for index in range(len(values))])
    center = np.mean(jack)
    denominator = 6 * np.sum((center - jack) ** 2) ** 1.5
    acceleration = np.sum((center - jack) ** 3) / denominator if denominator else 0.0
    probabilities = []
    for alpha in [0.025, 0.975]:
        z = stats.norm.ppf(alpha)
        adjusted = stats.norm.cdf(z0 + (z0 + z) / max(1 - acceleration * (z0 + z), 1e-12))
        probabilities.append(np.clip(adjusted, 0, 1))
    low, high = np.quantile(boot, probabilities)
    return estimate, float(low), float(high)


def paired_wilcoxon_p(values: np.ndarray) -> float:
    values = values[np.isfinite(values)]
    if not values.size or np.allclose(values, 0):
        return 1.0
    try:
        return float(stats.wilcoxon(values, zero_method="pratt").pvalue)
    except ValueError:
        return 1.0


def noninferiority_bootstrap_p(values: np.ndarray, *, margin: float, samples: int = 4000) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not values.size:
        return math.nan
    rng = np.random.default_rng(20260710)
    boot = np.mean(values[rng.integers(0, len(values), size=(samples, len(values)))], axis=1)
    return float((1 + np.sum(boot >= margin)) / (samples + 1))

def mcnemar_p(left: np.ndarray, right: np.ndarray) -> float:
    left, right = np.asarray(left, dtype=int), np.asarray(right, dtype=int)
    b = int(np.sum((left == 1) & (right == 0)))
    c = int(np.sum((left == 0) & (right == 1)))
    return 1.0 if b + c == 0 else float(stats.binomtest(b, b + c, 0.5).pvalue)