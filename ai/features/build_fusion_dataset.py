"""Build validated, per-region fusion-ready datasets from Milestone 1.4 AOI features.

This is a 2024 daily AOI-level prototype only. It creates no pooled dataset, model,
spatial grid, or evaluation result.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIRECTORY = REPOSITORY_ROOT / "datasets" / "processed"
REGION_IDS = ("uttarakhand", "california", "australia")
START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 12, 31)
EXPECTED_DATES = pd.date_range(START_DATE, END_DATE, freq="D")
TARGET_COLUMN = "fire_label"
DATE_COLUMN = "date"
FUSION_CONFIGURATION = "satellite_weather_historical_v1"

SATELLITE_FEATURES = (
    "ndvi_mean",
    "ndwi_mean",
    "cloud_cover_percent_mean",
)
WEATHER_FEATURES = (
    "temperature_2m_mean",
    "precipitation_sum",
    "relative_humidity_2m_mean",
)
HISTORICAL_FEATURES = (
    "prior_fire_days_7d",
    "prior_fire_days_30d",
    "days_since_prior_fire",
    "ndvi_prior_7d_mean",
    "ndvi_prior_30d_mean",
    "ndvi_prior_30d_trend",
    "ndwi_prior_7d_mean",
    "ndwi_prior_30d_mean",
    "ndwi_prior_30d_trend",
)
FEATURE_GROUPS = {
    "satellite": SATELLITE_FEATURES,
    "weather": WEATHER_FEATURES,
    "historical": HISTORICAL_FEATURES,
}
FUSION_FEATURES = (*SATELLITE_FEATURES, *WEATHER_FEATURES, *HISTORICAL_FEATURES)
REQUIRED_COLUMNS = (DATE_COLUMN, "region_id", TARGET_COLUMN, *FUSION_FEATURES)
OPTIONAL_PROVENANCE_COLUMNS = (
    "study_region",
    "operational_aoi",
    "aoi_file",
    "run_start_date",
    "run_end_date",
)


def source_stem() -> str:
    return f"daily_aoi_features_{START_DATE.isoformat()}_{END_DATE.isoformat()}"


def fusion_stem() -> str:
    return f"fusion_ready_daily_aoi_features_{START_DATE.isoformat()}_{END_DATE.isoformat()}"


def source_path(region: str) -> Path:
    return PROCESSED_DATA_DIRECTORY / region / f"{source_stem()}.csv"


def write_json(path: Path, content: dict[str, Any]) -> None:
    path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def class_counts(frame: pd.DataFrame) -> dict[str, int]:
    positives = int(frame[TARGET_COLUMN].sum())
    return {"positive": positives, "negative": int(len(frame) - positives)}


def validate_numeric_features(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    for column in FUSION_FEATURES:
        original = frame[column]
        numeric = pd.to_numeric(original, errors="coerce")
        invalid = original.notna() & numeric.isna()
        if invalid.any():
            errors.append(f"{column} has {int(invalid.sum())} non-numeric non-null values")
        frame[column] = numeric
    return errors


def validate_input(region: str, frame: pd.DataFrame, input_path: Path) -> tuple[list[str], list[str]]:
    """Return validation errors and non-fatal provenance/configuration warnings."""

    errors: list[str] = []
    warnings: list[str] = []
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing_columns:
        return [f"Input is missing required columns: {', '.join(missing_columns)}"], warnings

    missing_provenance = [column for column in OPTIONAL_PROVENANCE_COLUMNS if column not in frame]
    if missing_provenance:
        warnings.append(f"Optional provenance columns not available: {', '.join(missing_provenance)}")

    parsed_dates = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    invalid_dates = int(parsed_dates.isna().sum())
    if invalid_dates:
        errors.append(f"Temporal key contains {invalid_dates} invalid or empty dates")
    else:
        frame[DATE_COLUMN] = parsed_dates.dt.normalize()
        duplicate_dates = int(frame.duplicated(DATE_COLUMN).sum())
        if duplicate_dates:
            errors.append(f"Temporal key contains {duplicate_dates} duplicate dates")
        actual_dates = pd.DatetimeIndex(frame[DATE_COLUMN])
        missing_dates = EXPECTED_DATES.difference(actual_dates)
        extra_dates = actual_dates.difference(EXPECTED_DATES)
        if len(frame) != len(EXPECTED_DATES):
            errors.append(
                f"Expected {len(EXPECTED_DATES)} 2024 calendar rows but found {len(frame)}"
            )
        if len(missing_dates) or len(extra_dates):
            errors.append(
                "Input does not have exact 2024 calendar coverage "
                f"(missing={len(missing_dates)}, outside_range={len(extra_dates)})"
            )
        if not frame[DATE_COLUMN].is_monotonic_increasing:
            warnings.append("Input dates were not sorted; fusion output is sorted chronologically.")

    if not frame["region_id"].eq(region).all():
        errors.append(f"region_id provenance does not match requested region '{region}'")

    label_numeric = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    if label_numeric.isna().any() or not label_numeric.isin([0, 1]).all():
        errors.append("fire_label must contain only binary 0/1 values with no missing values")
    else:
        frame[TARGET_COLUMN] = label_numeric.astype("int8")

    errors.extend(validate_numeric_features(frame))
    if TARGET_COLUMN in FUSION_FEATURES:
        errors.append("Target leakage: fire_label is present in the fusion feature set")
    if len(set(FUSION_FEATURES)) != len(FUSION_FEATURES):
        errors.append("Feature isolation failure: fusion feature columns overlap")
    prohibited = {DATE_COLUMN, "region_id", TARGET_COLUMN}.intersection(FUSION_FEATURES)
    if prohibited:
        errors.append(f"Feature isolation failure: prohibited columns selected: {sorted(prohibited)}")

    if input_path.name != f"{source_stem()}.csv":
        warnings.append(f"Input filename differs from expected convention: {input_path.name}")
    return errors, warnings


def missingness_summary(frame: pd.DataFrame) -> dict[str, Any]:
    group_missing_masks = {
        group_name: frame.loc[:, columns].isna().any(axis=1)
        for group_name, columns in FEATURE_GROUPS.items()
    }
    complete_mask = ~pd.DataFrame(group_missing_masks).any(axis=1)
    return {
        "missing_values_by_feature": {
            column: int(frame[column].isna().sum()) for column in FUSION_FEATURES
        },
        "rows_missing_by_feature_group": {
            group_name: int(mask.sum()) for group_name, mask in group_missing_masks.items()
        },
        "rows_missing_multiple_feature_groups": int(
            pd.DataFrame(group_missing_masks).sum(axis=1).gt(1).sum()
        ),
        "complete_case_rows": int(complete_mask.sum()),
        "excluded_rows_any_required_feature_missing": int((~complete_mask).sum()),
        "complete_mask": complete_mask,
    }


def build_fusion_dataset(region: str) -> tuple[Path, dict[str, Any]]:
    input_path = source_path(region)
    if not input_path.exists():
        raise FileNotFoundError(f"Milestone 1.4 feature table not found: {input_path}")

    full_table = pd.read_csv(input_path)
    errors, warnings = validate_input(region, full_table, input_path)
    if errors:
        raise ValueError("; ".join(errors))

    full_table = full_table.sort_values(DATE_COLUMN).reset_index(drop=True)
    summary = missingness_summary(full_table)
    complete_mask = summary.pop("complete_mask")
    provenance_columns = [
        column for column in OPTIONAL_PROVENANCE_COLUMNS if column in full_table.columns
    ]
    output_columns = [
        DATE_COLUMN,
        "region_id",
        *provenance_columns,
        TARGET_COLUMN,
        *FUSION_FEATURES,
    ]
    fusion = full_table.loc[complete_mask, output_columns].copy()
    fusion["source_input_filename"] = input_path.name
    fusion["fusion_start_date"] = START_DATE.isoformat()
    fusion["fusion_end_date"] = END_DATE.isoformat()
    fusion["fusion_feature_configuration"] = FUSION_CONFIGURATION

    if fusion[TARGET_COLUMN].isna().any() or TARGET_COLUMN in FUSION_FEATURES:
        raise ValueError("Target leakage validation failed while building fusion output")
    if fusion.duplicated(DATE_COLUMN).any():
        raise ValueError("Fusion output has duplicate temporal rows")

    output_directory = input_path.parent
    output_path = output_directory / f"{fusion_stem()}.csv"
    validation_path = output_directory / f"{fusion_stem()}.validation.json"
    metadata_path = output_directory / f"{fusion_stem()}.metadata.json"
    fusion.to_csv(output_path, index=False, date_format="%Y-%m-%d")

    full_counts = class_counts(full_table)
    complete_counts = class_counts(fusion)
    metadata: dict[str, Any] = {
        "prototype_scope": (
            "Fusion dataset prototype based on the existing 2024 daily AOI-level validation data. "
            "It is not a pooled dataset, spatial-tile dataset, multi-year temporal holdout, "
            "or spatial-block CV evaluation dataset."
        ),
        "region_id": region,
        "input_filename": input_path.name,
        "input_path": str(input_path.relative_to(REPOSITORY_ROOT)),
        "output_filename": output_path.name,
        "output_path": str(output_path.relative_to(REPOSITORY_ROOT)),
        "date_range": {"start_date": START_DATE.isoformat(), "end_date": END_DATE.isoformat()},
        "full_calendar_feature_table": {
            "total_rows": int(len(full_table)),
            "class_counts": full_counts,
            "date_min": full_table[DATE_COLUMN].min().date().isoformat(),
            "date_max": full_table[DATE_COLUMN].max().date().isoformat(),
            "duplicate_dates": int(full_table.duplicated(DATE_COLUMN).sum()),
        },
        "complete_case_fusion_model_dataset": {
            "complete_fusion_rows": int(len(fusion)),
            "excluded_rows_any_required_feature_missing": summary[
                "excluded_rows_any_required_feature_missing"
            ],
            "class_counts": complete_counts,
            "duplicate_dates": int(fusion.duplicated(DATE_COLUMN).sum()),
        },
        "dropped_rows_by_missing_feature_group": summary["rows_missing_by_feature_group"],
        "missingness": {
            "missing_values_by_feature": summary["missing_values_by_feature"],
            "rows_missing_multiple_feature_groups": summary[
                "rows_missing_multiple_feature_groups"
            ],
        },
        "selected_feature_columns": {
            "satellite": list(SATELLITE_FEATURES),
            "weather": list(WEATHER_FEATURES),
            "historical": list(HISTORICAL_FEATURES),
            "all_fusion_features": list(FUSION_FEATURES),
        },
        "preserved_provenance_columns": ["region_id", *provenance_columns],
        "validation_warnings": warnings,
        "pipeline_configuration": {
            "feature_configuration": FUSION_CONFIGURATION,
            "target_column": TARGET_COLUMN,
            "target_policy": "fire_label is retained only as the target and is never an input feature.",
            "missing_value_policy": (
                "No feature values are imputed. Rows missing one or more required satellite, weather, "
                "or historical values are excluded only from the complete-case fusion-model dataset."
            ),
            "leakage_policy": (
                "Historical fire and vegetation inputs are the Milestone 1.4 prior/shifted features; "
                "target-day fire_label is not selected as an input."
            ),
            "region_pooling": "disabled; each region is written and validated independently.",
        },
    }
    validation = {
        "region_id": region,
        "input_filename": input_path.name,
        "validation_passed": True,
        "checks": {
            "input_exists": True,
            "expected_columns_present": True,
            "valid_temporal_key": True,
            "exact_2024_calendar_coverage": True,
            "duplicate_input_dates": 0,
            "duplicate_output_dates": 0,
            "binary_fire_label": True,
            "fire_label_excluded_from_features": TARGET_COLUMN not in FUSION_FEATURES,
            "feature_groups_are_disjoint": len(set(FUSION_FEATURES)) == len(FUSION_FEATURES),
            "missing_satellite_values_imputed": False,
        },
        "full_calendar_feature_table_statistics": metadata["full_calendar_feature_table"],
        "complete_case_fusion_model_dataset_statistics": metadata[
            "complete_case_fusion_model_dataset"
        ],
        "dropped_rows_by_missing_feature_group": metadata[
            "dropped_rows_by_missing_feature_group"
        ],
        "validation_warnings": warnings,
    }
    write_json(metadata_path, metadata)
    write_json(validation_path, validation)
    return output_path, metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--region",
        required=True,
        choices=(*REGION_IDS, "all"),
        help="Build the fusion dataset for one approved region or all approved regions.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    regions = REGION_IDS if args.region == "all" else (args.region,)
    for region in regions:
        try:
            output_path, metadata = build_fusion_dataset(region)
        except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
            raise SystemExit(f"Fusion dataset preparation failed for {region}: {error}") from error
        complete = metadata["complete_case_fusion_model_dataset"]
        counts = complete["class_counts"]
        print(
            f"{region}: {complete['complete_fusion_rows']} complete fusion rows "
            f"({counts['positive']} positive, {counts['negative']} negative), saved to {output_path}"
        )


if __name__ == "__main__":
    main()
