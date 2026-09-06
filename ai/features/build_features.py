"""Build leakage-aware daily AOI-level wildfire feature tables for EarthDNA."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from collection_common import (
    RAW_DATA_DIRECTORY,
    REGION_IDS,
    REPOSITORY_ROOT,
    add_collection_arguments,
    load_aoi,
    output_directory,
    validate_date_range,
    write_json,
)


PROCESSED_DATA_DIRECTORY = REPOSITORY_ROOT / "datasets" / "processed"
WEATHER_COLUMNS = [
    "temperature_2m_mean",
    "precipitation_sum",
    "relative_humidity_2m_mean",
]
SATELLITE_COLUMNS = ["scene_id", "acquired_at", "cloud_cover_percent", "ndvi", "ndwi"]
FIRMS_REQUIRED_COLUMNS = ["latitude", "longitude", "acq_date"]


def source_path(region: str, source: str, filename: str) -> Path:
    return RAW_DATA_DIRECTORY / region / source / filename


def date_range_frame(region: str, start_date: date, end_date: date) -> pd.DataFrame:
    dates = pd.date_range(start_date, end_date, freq="D")
    return pd.DataFrame({"date": dates, "region_id": region})


def read_weather(region: str, start_date: date, end_date: date) -> tuple[pd.DataFrame, dict[str, Any]]:
    filename = f"open_meteo_daily_{start_date.isoformat()}_{end_date.isoformat()}.json"
    path = source_path(region, "weather", filename)
    if not path.exists():
        raise FileNotFoundError(f"Weather source file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    daily = payload.get("response", {}).get("daily", {})
    missing = [column for column in ["time", *WEATHER_COLUMNS] if column not in daily]
    if missing:
        raise ValueError(f"Weather source is missing columns: {', '.join(missing)}")

    weather = pd.DataFrame({"date": pd.to_datetime(daily["time"], utc=True).tz_localize(None)})
    for column in WEATHER_COLUMNS:
        weather[column] = pd.to_numeric(daily[column], errors="coerce")

    duplicates = int(weather.duplicated("date").sum())
    if duplicates:
        weather = weather.groupby("date", as_index=False)[WEATHER_COLUMNS].mean()

    return weather, {
        "file": str(path.relative_to(REPOSITORY_ROOT)),
        "rows_read": len(daily["time"]),
        "duplicate_dates": duplicates,
        "date_min": weather["date"].min().date().isoformat(),
        "date_max": weather["date"].max().date().isoformat(),
        "null_values": {column: int(weather[column].isna().sum()) for column in WEATHER_COLUMNS},
    }


def read_satellite(region: str, start_date: date, end_date: date) -> tuple[pd.DataFrame, dict[str, Any]]:
    filename = f"sentinel2_ndvi_ndwi_{start_date.isoformat()}_{end_date.isoformat()}.geojson"
    path = source_path(region, "satellite", filename)
    if not path.exists():
        raise FileNotFoundError(f"Satellite source file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    rows = [feature.get("properties", {}) for feature in features]
    satellite = pd.DataFrame(rows)
    missing = [column for column in SATELLITE_COLUMNS if column not in satellite.columns]
    if missing:
        raise ValueError(f"Satellite source is missing columns: {', '.join(missing)}")

    satellite["date"] = pd.to_datetime(satellite["acquired_at"], utc=True).dt.tz_localize(None).dt.normalize()
    for column in ["cloud_cover_percent", "ndvi", "ndwi"]:
        satellite[column] = pd.to_numeric(satellite[column], errors="coerce")

    empty_scenes = int(satellite[["ndvi", "ndwi"]].isna().all(axis=1).sum())
    duplicate_scenes = int(satellite.duplicated("scene_id").sum())
    same_day_scene_count = satellite.groupby("date").size().rename("satellite_scene_count")
    daily = (
        satellite.groupby("date", as_index=False)
        .agg(
            ndvi_mean=("ndvi", "mean"),
            ndwi_mean=("ndwi", "mean"),
            cloud_cover_percent_mean=("cloud_cover_percent", "mean"),
        )
        .merge(same_day_scene_count, on="date", how="left")
    )

    return daily, {
        "file": str(path.relative_to(REPOSITORY_ROOT)),
        "scenes_read": len(satellite),
        "days_with_scenes": len(daily),
        "duplicate_scene_ids": duplicate_scenes,
        "empty_scenes": empty_scenes,
        "date_min": daily["date"].min().date().isoformat(),
        "date_max": daily["date"].max().date().isoformat(),
        "null_values": {
            "ndvi": int(satellite["ndvi"].isna().sum()),
            "ndwi": int(satellite["ndwi"].isna().sum()),
        },
    }


def read_labels(region: str, start_date: date, end_date: date) -> tuple[pd.DataFrame, dict[str, Any]]:
    directory = RAW_DATA_DIRECTORY / region / "labels" / "firms"
    manifest_path = directory / (
        f"manifest_viirs_noaa20_sp_{start_date.isoformat()}_{end_date.isoformat()}.json"
    )
    if not manifest_path.exists():
        raise FileNotFoundError(f"FIRMS manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames: list[pd.DataFrame] = []
    schema_issues: list[str] = []
    empty_files = 0
    chunks_read = 0
    for download in manifest.get("downloads", []):
        path = RAW_DATA_DIRECTORY / download["file"]
        if not path.exists():
            schema_issues.append(f"Missing FIRMS chunk: {path.relative_to(REPOSITORY_ROOT)}")
            continue
        frame = pd.read_csv(path)
        missing = [column for column in FIRMS_REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            schema_issues.append(f"{path.name} missing {', '.join(missing)}")
            continue
        chunks_read += 1
        if frame.empty:
            empty_files += 1
            continue
        frame["source_file"] = path.name
        frames.append(frame)

    if schema_issues:
        raise ValueError("; ".join(schema_issues))
    labels = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=FIRMS_REQUIRED_COLUMNS)
    labels["date"] = pd.to_datetime(labels.get("acq_date"), errors="coerce").dt.normalize()
    invalid_dates = int(labels["date"].isna().sum())
    labels = labels.dropna(subset=["date"])
    duplicate_detections = int(labels.duplicated().sum())
    daily = labels.groupby("date").size().rename("fire_detection_count").reset_index()

    return daily, {
        "manifest": str(manifest_path.relative_to(REPOSITORY_ROOT)),
        "product": manifest.get("product"),
        "chunks_expected": len(manifest.get("downloads", [])),
        "chunks_read": chunks_read,
        "empty_files": empty_files,
        "detections_read": len(labels),
        "duplicate_detection_rows": duplicate_detections,
        "invalid_dates": invalid_dates,
        "days_with_detections": len(daily),
        "date_min": daily["date"].min().date().isoformat() if len(daily) else None,
        "date_max": daily["date"].max().date().isoformat() if len(daily) else None,
    }


def add_historical_features(features: pd.DataFrame) -> pd.DataFrame:
    """Create features that never use the current target day's fire or vegetation value."""

    prior_fire = features["fire_label"].shift(1)
    features["prior_fire_days_7d"] = prior_fire.rolling(7, min_periods=1).sum()
    features["prior_fire_days_30d"] = prior_fire.rolling(30, min_periods=1).sum()

    prior_fire_date = features["date"].where(features["fire_label"].eq(1)).shift(1).ffill()
    features["days_since_prior_fire"] = (features["date"] - prior_fire_date).dt.days

    for column in ["ndvi_mean", "ndwi_mean"]:
        prior_values = features[column].shift(1)
        prefix = column.removesuffix("_mean")
        features[f"{prefix}_prior_7d_mean"] = prior_values.rolling(7, min_periods=1).mean()
        features[f"{prefix}_prior_30d_mean"] = prior_values.rolling(30, min_periods=1).mean()
        features[f"{prefix}_prior_30d_trend"] = (
            features[f"{prefix}_prior_7d_mean"] - features[f"{prefix}_prior_30d_mean"]
        )
    return features


def build_features(region: str, start_date: date, end_date: date) -> tuple[Path, dict[str, Any]]:
    """Build one calendar-complete, daily AOI-level table for a selected region."""

    validate_date_range(start_date, end_date)
    aoi = load_aoi(region)
    features = date_range_frame(region, start_date, end_date)
    weather, weather_report = read_weather(region, start_date, end_date)
    satellite, satellite_report = read_satellite(region, start_date, end_date)
    labels, labels_report = read_labels(region, start_date, end_date)

    features = features.merge(weather, on="date", how="left", validate="one_to_one")
    features = features.merge(satellite, on="date", how="left", validate="one_to_one")
    features = features.merge(labels, on="date", how="left", validate="one_to_one")
    features["fire_detection_count"] = features["fire_detection_count"].fillna(0).astype("int64")
    features["fire_label"] = features["fire_detection_count"].gt(0).astype("int8")

    features = add_historical_features(features)
    features.insert(1, "study_region", aoi.study_region)
    features.insert(2, "operational_aoi", aoi.operational_aoi)
    features.insert(3, "aoi_file", f"datasets/aoi/{region}.geojson")
    features.insert(4, "run_start_date", start_date.isoformat())
    features.insert(5, "run_end_date", end_date.isoformat())

    processed_directory = PROCESSED_DATA_DIRECTORY / region
    processed_directory.mkdir(parents=True, exist_ok=True)
    stem = f"daily_aoi_features_{start_date.isoformat()}_{end_date.isoformat()}"
    output_path = processed_directory / f"{stem}.csv"
    features.to_csv(output_path, index=False, date_format="%Y-%m-%d")

    report = {
        "prototype_scope": "2024 validation dataset; daily AOI-level rows, not a spatial tile dataset.",
        "region": asdict(aoi),
        "time_window": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "row_count": len(features),
        "target_definition": "fire_label is 1 when one or more FIRMS detections occur in the AOI on the calendar day; otherwise 0.",
        "feature_definitions": {
            "same_day_satellite": "NDVI/NDWI and cloud cover are mean values across all Sentinel-2 scenes acquired on the date.",
            "historical_fire": "prior_fire_days_* and days_since_prior_fire use fire_label shifted by one calendar day.",
            "vegetation_history": "prior NDVI/NDWI rolling means and trends shift observations by one calendar day before rolling.",
        },
        "sources": {
            "weather": weather_report,
            "satellite": satellite_report,
            "labels": labels_report,
        },
        "output": str(output_path.relative_to(REPOSITORY_ROOT)),
        "missing_values": {column: int(count) for column, count in features.isna().sum().items() if count},
        "coverage": {
            "calendar_days": len(features),
            "weather_days": int(features[WEATHER_COLUMNS].notna().all(axis=1).sum()),
            "satellite_days": int(features["satellite_scene_count"].notna().sum()),
            "satellite_missing_days": int(features["satellite_scene_count"].isna().sum()),
            "positive_label_days": int(features["fire_label"].sum()),
            "negative_label_days": int((features["fire_label"] == 0).sum()),
        },
    }
    write_json(processed_directory / f"{stem}.metadata.json", report)
    return output_path, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--region", choices=REGION_IDS)
    group.add_argument("--all-regions", action="store_true")
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    regions = REGION_IDS if args.all_regions else (args.region,)
    for region in regions:
        try:
            output_path, report = build_features(region, args.start_date, args.end_date)
        except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
            raise SystemExit(f"Feature engineering failed for {region}: {error}") from error
        print(
            f"{region}: {report['row_count']} daily rows, "
            f"{report['coverage']['positive_label_days']} positive label days, saved to {output_path}"
        )


if __name__ == "__main__":
    main()
