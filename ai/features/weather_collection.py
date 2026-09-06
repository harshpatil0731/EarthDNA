"""Collect daily Open-Meteo weather observations for an EarthDNA AOI centroid."""

from __future__ import annotations

import argparse
import json
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

from collection_common import (
    add_collection_arguments,
    load_aoi,
    load_project_environment,
    output_directory,
    validate_date_range,
    write_json,
)


OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARIABLES = "temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean"


def collect_weather(region: str, start_date: date, end_date: date) -> str:
    """Fetch one daily weather series for the centroid of the selected AOI."""

    validate_date_range(start_date, end_date)
    aoi = load_aoi(region)
    latitude, longitude = aoi.centroid
    parameters = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": DAILY_VARIABLES,
        "timezone": "UTC",
    }
    request_url = f"{OPEN_METEO_ARCHIVE_URL}?{urlencode(parameters)}"
    with urlopen(request_url, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if "daily" not in payload or not payload["daily"].get("time"):
        raise RuntimeError("Open-Meteo returned no daily observations for this request.")

    output_path = output_directory(region, "weather") / (
        f"open_meteo_daily_{start_date.isoformat()}_{end_date.isoformat()}.json"
    )
    write_json(
        output_path,
        {
            "source": "Open-Meteo Archive API",
            "aoi": {
                "region_id": aoi.region_id,
                "study_region": aoi.study_region,
                "operational_aoi": aoi.operational_aoi,
                "centroid": {"latitude": latitude, "longitude": longitude},
                "bounding_box": list(aoi.bounding_box),
            },
            "request": parameters,
            "response": payload,
        },
    )
    return str(output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_collection_arguments(parser)
    return parser


def main() -> None:
    load_project_environment()
    args = build_parser().parse_args()
    try:
        output_path = collect_weather(args.region, args.start_date, args.end_date)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"Weather collection failed: {error}") from error
    print(f"Weather data saved to {output_path}")


if __name__ == "__main__":
    main()
