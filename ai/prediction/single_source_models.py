"""Train Phase 1 single-source Logistic Regression baselines per EarthDNA region."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIRECTORY = REPOSITORY_ROOT / "datasets" / "processed"
REPORT_PATH = REPOSITORY_ROOT / "experiments" / "phase1_baseline_results.md"
REGION_IDS = ("uttarakhand", "california", "australia")
TARGET_COLUMN = "fire_label"


@dataclass(frozen=True)
class FeatureGroup:
    name: str
    framing: str
    missing_data_policy: str
    columns: tuple[str, ...]


FEATURE_GROUPS = (
    FeatureGroup(
        name="Satellite-only",
        framing=(
            "Same-day detection/prototype framing. Sentinel-2 observations acquired on "
            "the target date are not forward-looking wildfire predictors."
        ),
        missing_data_policy=(
            "Use only dates with complete same-day NDVI, NDWI, and cloud-cover values; "
            "never impute or silently include missing satellite days."
        ),
        columns=("ndvi_mean", "ndwi_mean", "cloud_cover_percent_mean"),
    ),
    FeatureGroup(
        name="Weather-only",
        framing="Daily AOI-centroid weather conditions aligned to the target date.",
        missing_data_policy="Use only rows with complete weather values; no imputation is applied.",
        columns=("temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean"),
    ),
    FeatureGroup(
        name="Historical-only",
        framing=(
            "Prior fire activity and shifted vegetation history available before the target day."
        ),
        missing_data_policy="Use only rows with complete historical values; no imputation is applied.",
        columns=(
            "prior_fire_days_7d",
            "prior_fire_days_30d",
            "days_since_prior_fire",
            "ndvi_prior_7d_mean",
            "ndvi_prior_30d_mean",
            "ndvi_prior_30d_trend",
            "ndwi_prior_7d_mean",
            "ndwi_prior_30d_mean",
            "ndwi_prior_30d_trend",
        ),
    ),
)


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Use dates in YYYY-MM-DD format.") from error


def feature_table_path(region: str, start_date: date, end_date: date) -> Path:
    stem = f"daily_aoi_features_{start_date.isoformat()}_{end_date.isoformat()}"
    return PROCESSED_DATA_DIRECTORY / region / f"{stem}.csv"


def metadata_path(region: str, start_date: date, end_date: date) -> Path:
    stem = f"daily_aoi_features_{start_date.isoformat()}_{end_date.isoformat()}"
    return PROCESSED_DATA_DIRECTORY / region / f"{stem}.metadata.json"


def split_boundary(start_date: date, end_date: date, train_fraction: float) -> date:
    total_days = (end_date - start_date).days + 1
    train_days = int(total_days * train_fraction)
    if train_days < 1 or train_days >= total_days:
        raise ValueError("--train-fraction must leave at least one calendar day for each split.")
    return start_date + timedelta(days=train_days)


def class_counts(frame: pd.DataFrame) -> dict[str, int]:
    positives = int(frame[TARGET_COLUMN].sum())
    return {"positive": positives, "negative": len(frame) - positives}


def format_metric(value: float | None) -> str:
    return "unavailable" if value is None else f"{value:.4f}"


def validate_feature_groups(frame: pd.DataFrame) -> None:
    all_columns = set(frame.columns)
    groups = [set(group.columns) for group in FEATURE_GROUPS]
    for group in FEATURE_GROUPS:
        missing = set(group.columns) - all_columns
        if missing:
            raise ValueError(f"{group.name} is missing columns: {', '.join(sorted(missing))}")
        if TARGET_COLUMN in group.columns or "date" in group.columns or "region_id" in group.columns:
            raise ValueError(f"{group.name} includes a prohibited target or provenance column.")
    if any(left.intersection(right) for index, left in enumerate(groups) for right in groups[index + 1 :]):
        raise ValueError("Single-source feature groups overlap.")


def evaluate_group(
    frame: pd.DataFrame,
    group: FeatureGroup,
    cutoff: date,
) -> dict[str, Any]:
    before_filter = len(frame)
    missing_by_feature = {column: int(frame[column].isna().sum()) for column in group.columns}
    usable = frame.dropna(subset=group.columns).copy()
    usable = usable.sort_values("date")
    train = usable[usable["date"].dt.date < cutoff].copy()
    test = usable[usable["date"].dt.date >= cutoff].copy()
    result: dict[str, Any] = {
        "feature_group": group.name,
        "features": list(group.columns),
        "framing": group.framing,
        "missing_data_policy": group.missing_data_policy,
        "rows_available": before_filter,
        "rows_usable": len(usable),
        "rows_dropped_for_missing_features": before_filter - len(usable),
        "missing_by_feature": missing_by_feature,
        "train_rows": len(train),
        "test_rows": len(test),
        "train_counts": class_counts(train),
        "test_counts": class_counts(test),
        "metrics": {"precision": None, "recall": None, "f1": None, "pr_auc": None},
        "status": "not_run",
        "note": "",
    }

    if len(train) == 0 or len(test) == 0:
        result["status"] = "unavailable"
        result["note"] = "The fixed chronological split produced an empty train or test set."
        return result
    if train[TARGET_COLUMN].nunique() < 2:
        result["status"] = "unavailable"
        result["note"] = "The fixed training split contains only one target class."
        return result
    if test[TARGET_COLUMN].nunique() < 2:
        result["status"] = "unavailable"
        result["note"] = (
            "The fixed test split contains only one target class; precision, recall, F1, "
            "and PR-AUC are not meaningful and are reported unavailable."
        )
        return result

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=42,
                    solver="liblinear",
                ),
            ),
        ]
    )
    model.fit(train[list(group.columns)], train[TARGET_COLUMN])
    predictions = model.predict(test[list(group.columns)])
    probabilities = model.predict_proba(test[list(group.columns)])[:, 1]
    result["metrics"] = {
        "precision": float(precision_score(test[TARGET_COLUMN], predictions, zero_division=0)),
        "recall": float(recall_score(test[TARGET_COLUMN], predictions, zero_division=0)),
        "f1": float(f1_score(test[TARGET_COLUMN], predictions, zero_division=0)),
        "pr_auc": float(average_precision_score(test[TARGET_COLUMN], probabilities)),
    }
    result["status"] = "evaluated"
    if result["test_counts"]["positive"] < 5:
        result["note"] = (
            "The fixed test split has fewer than five positive days; the reported metrics "
            "are numerically computable but highly unstable."
        )
    return result


def run_region(region: str, start_date: date, end_date: date, cutoff: date) -> dict[str, Any]:
    table_path = feature_table_path(region, start_date, end_date)
    source_metadata_path = metadata_path(region, start_date, end_date)
    if not table_path.exists() or not source_metadata_path.exists():
        raise FileNotFoundError(
            f"Missing Milestone 1.4 output for {region}; run build_features.py first."
        )
    frame = pd.read_csv(table_path, parse_dates=["date"])
    source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))
    if not frame["region_id"].eq(region).all():
        raise ValueError(f"Feature table provenance does not match requested region: {region}")
    validate_feature_groups(frame)
    return {
        "region_id": region,
        "study_region": frame["study_region"].iloc[0],
        "operational_aoi": frame["operational_aoi"].iloc[0],
        "feature_table": str(table_path.relative_to(REPOSITORY_ROOT)),
        "source_metadata": str(source_metadata_path.relative_to(REPOSITORY_ROOT)),
        "source_coverage": source_metadata["coverage"],
        "results": [evaluate_group(frame, group, cutoff) for group in FEATURE_GROUPS],
    }


def markdown_table(results: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Source baseline | Usable / dropped rows | Train (+ / -) | Test (+ / -) | Precision | Recall | F1 | PR-AUC | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in results:
        train = result["train_counts"]
        test = result["test_counts"]
        metrics = result["metrics"]
        lines.append(
            "| {name} | {usable} / {dropped} | {train_pos} / {train_neg} | "
            "{test_pos} / {test_neg} | {precision} | {recall} | {f1} | {pr_auc} | {status} |".format(
                name=result["feature_group"],
                usable=result["rows_usable"],
                dropped=result["rows_dropped_for_missing_features"],
                train_pos=train["positive"],
                train_neg=train["negative"],
                test_pos=test["positive"],
                test_neg=test["negative"],
                precision=format_metric(metrics["precision"]),
                recall=format_metric(metrics["recall"]),
                f1=format_metric(metrics["f1"]),
                pr_auc=format_metric(metrics["pr_auc"]),
                status=result["status"],
            )
        )
    return lines


def write_report(
    region_reports: list[dict[str, Any]],
    start_date: date,
    end_date: date,
    cutoff: date,
    train_fraction: float,
) -> None:
    train_end = cutoff - timedelta(days=1)
    lines = [
        "# Phase 1 Single-Source Baseline Results",
        "",
        "## Prototype Scope",
        "",
        "These are 2024 daily AOI-level validation-prototype results, not final research claims. "
        "Each region is trained independently; no pooled or cross-region model is used.",
        "",
        "## Reproducible Model and Split Settings",
        "",
        "- Algorithm: `StandardScaler` + class-weighted `LogisticRegression`.",
        "- Logistic Regression: `solver=liblinear`, `class_weight=balanced`, `max_iter=1000`, `random_state=42`.",
        f"- Calendar window: `{start_date.isoformat()}` through `{end_date.isoformat()}`.",
        f"- Chronological split: train `{start_date.isoformat()}` through `{train_end.isoformat()}` "
        f"({train_fraction:.0%} of the {((end_date - start_date).days + 1)} calendar days); "
        f"test `{cutoff.isoformat()}` through `{end_date.isoformat()}`.",
        "- The same fixed calendar cutoff is retained for every region and source group. "
        "Rows lacking a source group's required features are excluded only from that group's baseline; no values are imputed.",
        "- `fire_label=1` means one or more FIRMS detections occurred within the finalized AOI on the date.",
        "",
        "## Source-Group Policy and Leakage Check",
        "",
        "- Satellite-only uses `ndvi_mean`, `ndwi_mean`, and `cloud_cover_percent_mean`. "
        "Cloud cover is retained as a Sentinel-2 acquisition-condition input, not a weather or historical feature. "
        "This is a same-day detection/prototype framing, not forward-looking wildfire prediction.",
        "- Weather-only uses `temperature_2m_mean`, `precipitation_sum`, and `relative_humidity_2m_mean`.",
        "- Historical-only uses only prior fire activity and shifted prior vegetation statistics. "
        "Milestone 1.4 shifted every fire and vegetation value before rolling, so target-day fire labels and target-day vegetation values are excluded.",
        "- The script validates that feature groups are disjoint and exclude the target, date, and provenance columns.",
        "",
    ]
    for report in region_reports:
        lines.extend(
            [
                f"## {report['study_region']} ({report['operational_aoi']})",
                "",
                f"- Feature table: `{report['feature_table']}`",
                f"- Milestone 1.4 metadata: `{report['source_metadata']}`",
                f"- Source coverage: {report['source_coverage']['calendar_days']} calendar days, "
                f"{report['source_coverage']['weather_days']} complete weather days, "
                f"{report['source_coverage']['satellite_days']} satellite days, and "
                f"{report['source_coverage']['positive_label_days']} positive-label days.",
                "",
                *markdown_table(report["results"]),
                "",
            ]
        )
        for result in report["results"]:
            missing = ", ".join(
                f"{column}: {count}" for column, count in result["missing_by_feature"].items()
            )
            lines.extend(
                [
                    f"### {result['feature_group']} details",
                    "",
                    f"- Features: `{', '.join(result['features'])}`",
                    f"- Input framing: {result['framing']}",
                    f"- Missingness before source-specific filtering: {missing}.",
                    f"- Missing-data policy: {result['missing_data_policy']}",
                ]
            )
            if result["note"]:
                lines.append(f"- Metric note: {result['note']}")
            lines.append("")

    lines.extend(
        [
            "## Cross-Region Comparison",
            "",
            "| Region | Satellite usable rows / positive days | Weather usable rows / positive days | Historical usable rows / positive days |",
            "|---|---:|---:|---:|",
        ]
    )
    for report in region_reports:
        values = {
            result["feature_group"]: result for result in report["results"]
        }
        cells = []
        for name in ("Satellite-only", "Weather-only", "Historical-only"):
            result = values[name]
            counts = result["train_counts"]["positive"] + result["test_counts"]["positive"]
            cells.append(f"{result['rows_usable']} / {counts}")
        lines.append(f"| {report['study_region']} | " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- This is a one-year, 2024 AOI-level prototype. It cannot support the later temporal-holdout or spatial-block evaluation claims.",
            "- Satellite coverage is sparse and source-specific complete-case filtering substantially reduces satellite baseline sample sizes.",
            "- Uttarakhand and Southeastern Australia satellite test windows contain no positive days under the fixed split, so their satellite metrics are unavailable rather than altered.",
            "- Southeastern Australia has very few positive days overall, especially for satellite-only rows; any available baseline metrics are unstable.",
            "- FIRMS active-fire detections are an operational proxy for the chosen daily target and do not constitute confirmed wildfire-event labels.",
            "- Phase 2 must add the approved multi-year dataset, spatial-block CV, temporal holdout evaluation, multi-seed runs, model-family comparison, and fusion modelling.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--region", choices=REGION_IDS)
    group.add_argument("--all-regions", action="store_true")
    parser.add_argument("--start-date", type=parse_iso_date, required=True)
    parser.add_argument("--end-date", type=parse_iso_date, required=True)
    parser.add_argument("--train-fraction", type=float, default=0.8)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.start_date >= args.end_date:
        raise SystemExit("Model training failed: --start-date must be before --end-date.")
    if not 0 < args.train_fraction < 1:
        raise SystemExit("Model training failed: --train-fraction must be between 0 and 1.")
    cutoff = split_boundary(args.start_date, args.end_date, args.train_fraction)
    regions = REGION_IDS if args.all_regions else (args.region,)
    try:
        reports = [run_region(region, args.start_date, args.end_date, cutoff) for region in regions]
    except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
        raise SystemExit(f"Model training failed: {error}") from error
    write_report(reports, args.start_date, args.end_date, cutoff, args.train_fraction)
    for report in reports:
        statuses = ", ".join(
            f"{result['feature_group']}={result['status']}" for result in report["results"]
        )
        print(f"{report['region_id']}: {statuses}")
    print(f"Results report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
