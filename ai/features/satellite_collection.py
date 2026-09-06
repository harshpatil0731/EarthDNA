"""Collect Sentinel-2 scene summaries and AOI mean NDVI/NDWI via Earth Engine."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Any

from collection_common import (
    add_collection_arguments,
    environment_value,
    load_aoi,
    load_project_environment,
    output_directory,
    validate_date_range,
    write_json,
)


SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"


def initialize_earth_engine() -> Any:
    try:
        import ee
    except ImportError as error:
        raise RuntimeError(
            "Earth Engine client is missing. Install ai/requirements.txt before running this script."
        ) from error

    project = environment_value("EE_PROJECT")
    try:
        ee.Initialize(project=project)
    except Exception as error:
        raise RuntimeError(
            "Earth Engine initialization failed. A user must authenticate a Google account "
            "with Earth Engine access and provide an EE_PROJECT before collection can run."
        ) from error
    return ee


def add_indices(image: Any) -> Any:
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("ndvi")
    ndwi = image.normalizedDifference(["B3", "B8"]).rename("ndwi")
    return image.addBands([ndvi, ndwi])


def image_to_feature(image: Any, geometry: Any, ee: Any) -> Any:
    values = image.select(["ndvi", "ndwi"]).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10,
        maxPixels=1_000_000_000,
    )
    return ee.Feature(
        None,
        values.combine(
            ee.Dictionary(
                {
                    "scene_id": image.get("system:index"),
                    "acquired_at": image.date().format("YYYY-MM-dd'T'HH:mm:ss'Z'"),
                    "cloud_cover_percent": image.get("CLOUDY_PIXEL_PERCENTAGE"),
                }
            ),
            overwrite=True,
        ),
    )


def collect_satellite(
    region: str, start_date: date, end_date: date, max_cloud_cover: float
) -> str:
    """Collect per-scene mean NDVI and NDWI for one configured AOI."""

    validate_date_range(start_date, end_date)
    if not 0 <= max_cloud_cover <= 100:
        raise ValueError("--max-cloud-cover must be between 0 and 100.")

    ee = initialize_earth_engine()
    aoi = load_aoi(region)
    geometry = ee.Geometry(aoi.geometry)
    end_exclusive = end_date + timedelta(days=1)
    collection = (
        ee.ImageCollection(SENTINEL2_COLLECTION)
        .filterBounds(geometry)
        .filterDate(start_date.isoformat(), end_exclusive.isoformat())
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", max_cloud_cover))
        .map(add_indices)
    )
    feature_collection = ee.FeatureCollection(
        collection.map(lambda image: image_to_feature(image, geometry, ee))
    )
    result = feature_collection.getInfo()
    output_path = output_directory(region, "satellite") / (
        f"sentinel2_ndvi_ndwi_{start_date.isoformat()}_{end_date.isoformat()}.geojson"
    )
    write_json(
        output_path,
        {
            "type": "FeatureCollection",
            "metadata": {
                "source": SENTINEL2_COLLECTION,
                "region_id": aoi.region_id,
                "operational_aoi": aoi.operational_aoi,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "max_cloud_cover_percent": max_cloud_cover,
                "index_definitions": {
                    "ndvi": "normalizedDifference(B8, B4)",
                    "ndwi": "normalizedDifference(B3, B8)",
                },
            },
            "features": result["features"],
        },
    )
    return str(output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_collection_arguments(parser)
    parser.add_argument(
        "--max-cloud-cover",
        type=float,
        default=60.0,
        help="Maximum Sentinel-2 scene cloud percentage (default: 60).",
    )
    return parser


def main() -> None:
    load_project_environment()
    args = build_parser().parse_args()
    try:
        output_path = collect_satellite(
            args.region, args.start_date, args.end_date, args.max_cloud_cover
        )
    except (RuntimeError, ValueError) as error:
        raise SystemExit(f"Satellite collection failed: {error}") from error
    print(f"Satellite data saved to {output_path}")


if __name__ == "__main__":
    main()
