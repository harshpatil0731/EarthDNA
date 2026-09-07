"""Run per-region, five-seed fusion model comparisons for the 2024 prototype."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from evaluation import (
    METRIC_NAMES,
    aggregate_seed_metrics,
    calculate_metrics,
    chronological_split,
    class_counts,
    evaluation_capabilities,
    paired_wilcoxon,
)
from multi_source_model import (
    FUSION_FEATURES,
    MODEL_SPECS,
    REGION_IDS,
    TARGET_COLUMN,
    build_model,
    fusion_path,
    load_fusion_dataset,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = REPOSITORY_ROOT / "experiments" / "model_comparison_results.md"
SEEDS = (11, 23, 37, 53, 71)


def run_model(
    name: str,
    spec: Any,
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for seed in SEEDS:
        model = build_model(spec, seed, train[TARGET_COLUMN])
        model.fit(train.loc[:, FUSION_FEATURES], train[TARGET_COLUMN])
        probabilities = model.predict_proba(test.loc[:, FUSION_FEATURES])[:, 1]
        runs.append({"seed": seed, "metrics": calculate_metrics(test[TARGET_COLUMN], probabilities)})
    return {
        "model": name,
        "configuration": spec.configuration,
        "seed_results": runs,
        "aggregate": aggregate_seed_metrics(runs),
    }


def best_non_baseline(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [result for result in results if result["model"] != "Fusion Logistic Regression"]
    valid = [result for result in candidates if result["aggregate"]["available"]]
    if not valid:
        return None
    return max(valid, key=lambda result: result["aggregate"]["metrics"]["pr_auc"]["mean"])


def run_region(region: str) -> dict[str, Any]:
    frame = load_fusion_dataset(region)
    split = chronological_split(frame)
    capabilities = evaluation_capabilities(frame, split)
    model_results = [run_model(spec.name, spec, split.train, split.test) for spec in MODEL_SPECS]
    baseline = next(result for result in model_results if result["model"] == "Fusion Logistic Regression")
    candidate = best_non_baseline(model_results)
    if not capabilities["significance_testing"]["available"]:
        significance = {"available": False, "reason": capabilities["significance_testing"]["reason"]}
    elif candidate is None:
        significance = {"available": False, "reason": "No candidate model has valid aggregate metrics."}
    else:
        significance = paired_wilcoxon(baseline["seed_results"], candidate["seed_results"])
    return {
        "region_id": region,
        "study_region": frame["study_region"].iloc[0],
        "operational_aoi": frame["operational_aoi"].iloc[0],
        "dataset_path": str(fusion_path(region).relative_to(REPOSITORY_ROOT)),
        "dataset_rows": len(frame),
        "dataset_class_counts": class_counts(frame),
        "date_range": {
            "start": frame["date"].min().date().isoformat(),
            "end": frame["date"].max().date().isoformat(),
        },
        "feature_count": len(FUSION_FEATURES),
        "feature_columns": list(FUSION_FEATURES),
        "split": {
            "train_rows": len(split.train),
            "test_rows": len(split.test),
            "train_class_counts": class_counts(split.train),
            "test_class_counts": class_counts(split.test),
        },
        "capabilities": capabilities,
        "model_results": model_results,
        "significance": significance,
        "significance_candidate": candidate["model"] if candidate is not None else None,
    }


def metric_text(value: float | None) -> str:
    return "unavailable" if value is None else f"{value:.4f}"


def aggregate_text(result: dict[str, Any], metric: str) -> str:
    aggregate = result["aggregate"]
    if not aggregate["available"]:
        return "unavailable"
    summary = aggregate["metrics"][metric]
    return f"{summary['mean']:.4f} ± {summary['std']:.4f}"


def render_seed_table(result: dict[str, Any]) -> list[str]:
    if not result["aggregate"]["available"]:
        return [f"Seed-wise metrics unavailable: {result['aggregate']['reason']}", ""]
    lines = [
        "| Seed | Precision | Recall | F1 | PR-AUC | ROC-AUC |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for run in result["seed_results"]:
        values = run["metrics"]["values"]
        lines.append(
            "| {seed} | {precision} | {recall} | {f1} | {pr_auc} | {roc_auc} |".format(
                seed=run["seed"], **{name: metric_text(values[name]) for name in METRIC_NAMES}
            )
        )
    lines.append("")
    return lines


def render_report(reports: list[dict[str, Any]]) -> None:
    lines = [
        "# Milestone 2.1 Multi-Source Model Comparison",
        "",
        "## Prototype Scope",
        "",
        "This report evaluates separate per-region fusion models on the existing 2024 daily AOI-level complete-case datasets. "
        "It does not pool regions, compare numerically against Phase 1 single-source results with different usable dates, "
        "or claim research-grade spatial or multi-year temporal validation.",
        "",
        "## Fixed Evaluation Design",
        "",
        "- Inputs: the approved 15-feature satellite + weather + leakage-safe historical fusion schema only.",
        "- Target: `fire_label`; it and all provenance/metadata fields are excluded from model inputs.",
        "- Temporal split: train through `2024-10-18`; test from `2024-10-19` onward. The split is never changed to obtain positives.",
        "- Seeds: `11, 23, 37, 53, 71` for every model configuration.",
        "- Metrics: precision, recall, F1, PR-AUC, and ROC-AUC only when held-out data contains both classes.",
        "- Spatial-block CV: unavailable for this AOI-level dataset; no fabricated blocks are used.",
        "",
    ]
    for report in reports:
        counts = report["dataset_class_counts"]
        split = report["split"]
        lines.extend(
            [
                f"## {report['study_region']} — {report['operational_aoi']}",
                "",
                f"- Fusion dataset: `{report['dataset_path']}`",
                f"- Dataset: {report['dataset_rows']} rows; {counts['positive']} positive / {counts['negative']} negative; "
                f"coverage `{report['date_range']['start']}` to `{report['date_range']['end']}`.",
                f"- Fixed split: train {split['train_rows']} rows ({split['train_class_counts']['positive']} positive / {split['train_class_counts']['negative']} negative); "
                f"test {split['test_rows']} rows ({split['test_class_counts']['positive']} positive / {split['test_class_counts']['negative']} negative).",
                f"- Feature count: {report['feature_count']} approved fusion features.",
                f"- Temporal holdout: {report['capabilities']['temporal_holdout']['status']}. "
                f"{report['capabilities']['temporal_holdout']['reason']}",
                f"- Spatial CV: unavailable. {report['capabilities']['spatial_block_cv']['reason']}",
                "",
                "### Model Configurations",
                "",
            ]
        )
        for result in report["model_results"]:
            settings = ", ".join(f"`{key}={value}`" for key, value in result["configuration"].items())
            lines.append(f"- **{result['model']}**: {settings}.")
        lines.extend(
            [
                "",
                "### Five-Seed Aggregate Results",
                "",
                "| Model | Precision | Recall | F1 | PR-AUC | ROC-AUC | Status |",
                "|---|---:|---:|---:|---:|---:|---|",
            ]
        )
        for result in report["model_results"]:
            status = "prototype-valid metrics" if result["aggregate"]["available"] else result["aggregate"]["reason"]
            lines.append(
                f"| {result['model']} | {aggregate_text(result, 'precision')} | {aggregate_text(result, 'recall')} | "
                f"{aggregate_text(result, 'f1')} | {aggregate_text(result, 'pr_auc')} | {aggregate_text(result, 'roc_auc')} | {status} |"
            )
        lines.append("")
        for result in report["model_results"]:
            lines.extend([f"### {result['model']} Seed-wise Results", "", *render_seed_table(result)])

        significance = report["significance"]
        lines.extend(["### Significance Status", ""])
        if significance["available"]:
            lines.append(
                f"- Fusion Logistic Regression vs. {report['significance_candidate']} on `{significance['metric']}`: "
                f"paired Wilcoxon statistic={significance['statistic']:.4f}, p={significance['p_value']:.4f}, "
                f"n={significance['paired_seed_count']}."
            )
            lines.append(f"- {significance['interpretation']}")
        else:
            lines.append(f"- Unavailable: {significance['reason']}")
        lines.extend(
            [
                "",
                "### Limitations",
                "",
                "- Same-day satellite observations retain a detection/prototype framing, not a forward-looking wildfire prediction framing.",
                "- Complete-case filtering leaves sparse and non-contiguous observation dates because Sentinel-2 coverage is limited.",
                "- This result does not satisfy future spatial-tile, spatial-block CV, or multi-year temporal-holdout requirements.",
                "",
            ]
        )
        if split["test_class_counts"]["positive"] == 0:
            lines.insert(
                len(lines) - 1,
                "- The fixed held-out partition contains zero positive days, so no test metrics or significance result is available.",
            )
        elif split["test_rows"] < 20:
            lines.insert(
                len(lines) - 1,
                "- The fixed held-out partition contains fewer than 20 rows; metrics are prototype-only and significance testing is intentionally unavailable.",
            )
    lines.extend(
        [
            "## Cross-Region Limitation",
            "",
            "These regional results must not be pooled or interpreted as LORO evidence. LORO and pooled-model evaluation remain Milestone 2.1b.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", required=True, choices=(*REGION_IDS, "all"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    regions = REGION_IDS if args.region == "all" else (args.region,)
    reports = [run_region(region) for region in regions]
    render_report(reports)
    for report in reports:
        print(
            f"{report['region_id']}: {report['dataset_rows']} rows, "
            f"test positives={report['split']['test_class_counts']['positive']}, "
            f"spatial_cv={report['capabilities']['spatial_block_cv']['available']}"
        )
    print(f"Results report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
