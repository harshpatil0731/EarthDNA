"""Shared AOI, command-line, and file helpers for collection scripts."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AOI_DIRECTORY = REPOSITORY_ROOT / "datasets" / "aoi"
RAW_DATA_DIRECTORY = REPOSITORY_ROOT / "datasets" / "raw"
REGION_IDS = ("uttarakhand", "california", "australia")


@dataclass(frozen=True)
class AoiDefinition:
    """The one-feature GeoJSON boundary used by a collection run."""

    region_id: str
    study_region: str
    operational_aoi: str
    geometry: dict[str, Any]
    bounding_box: tuple[float, float, float, float]
    centroid: tuple[float, float]


def load_project_environment() -> None:
    """Load ignored local configuration without requiring it for public APIs."""

    load_dotenv(REPOSITORY_ROOT / ".env")


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Use dates in YYYY-MM-DD format.") from error


def add_collection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--region", choices=REGION_IDS, required=True)
    parser.add_argument("--start-date", type=parse_iso_date, required=True)
    parser.add_argument("--end-date", type=parse_iso_date, required=True)


def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise ValueError("--start-date must be on or before --end-date.")


def load_aoi(region_id: str) -> AoiDefinition:
    path = AOI_DIRECTORY / f"{region_id}.geojson"
    if not path.exists():
        raise FileNotFoundError(f"AOI boundary not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    features = data.get("features", [])
    if data.get("type") != "FeatureCollection" or len(features) != 1:
        raise ValueError(f"{path} must contain exactly one GeoJSON feature.")

    feature = features[0]
    properties = feature.get("properties", {})
    geometry = feature.get("geometry", {})
    ring = geometry.get("coordinates", [[]])[0]
    if (
        geometry.get("type") != "Polygon"
        or len(ring) < 4
        or ring[0] != ring[-1]
        or properties.get("region_id") != region_id
        or properties.get("risk_target") != "wildfire"
    ):
        raise ValueError(f"{path} is not a valid EarthDNA wildfire AOI.")

    longitudes = [coordinate[0] for coordinate in ring]
    latitudes = [coordinate[1] for coordinate in ring]
    west, east = min(longitudes), max(longitudes)
    south, north = min(latitudes), max(latitudes)
    return AoiDefinition(
        region_id=region_id,
        study_region=properties["study_region"],
        operational_aoi=properties["operational_aoi"],
        geometry=geometry,
        bounding_box=(west, south, east, north),
        centroid=((south + north) / 2, (west + east) / 2),
    )


def output_directory(region_id: str, source: str) -> Path:
    directory = RAW_DATA_DIRECTORY / region_id / source
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def environment_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is required. Set it in the ignored .env file or your environment."
        )
    return value
