"""Collect NASA FIRMS active-fire detections for a configured EarthDNA AOI."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from collection_common import (
    add_collection_arguments,
    environment_value,
    load_aoi,
    load_project_environment,
    output_directory,
    validate_date_range,
    write_json,
)


FIRMS_AREA_API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


def date_chunks(start_date: date, end_date: date, chunk_days: int):
    current = start_date
    while current <= end_date:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end_date)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def collect_labels(
    region: str,
    start_date: date,
    end_date: date,
    source: str,
    chunk_days: int,
) -> str:
    """Download FIRMS CSV chunks that cover the requested AOI and dates."""

    validate_date_range(start_date, end_date)
    if not 1 <= chunk_days <= 5:
        raise ValueError("--chunk-days must be between 1 and 5 for the FIRMS area API.")

    map_key = environment_value("FIRMS_MAP_KEY")
    aoi = load_aoi(region)
    west, south, east, north = aoi.bounding_box
    bounding_box = f"{west},{south},{east},{north}"
    directory = output_directory(region, "labels" ) / "firms"
    directory.mkdir(parents=True, exist_ok=True)
    downloads: list[dict[str, str | int]] = []

    for chunk_start, chunk_end in date_chunks(start_date, end_date, chunk_days):
        day_count = (chunk_end - chunk_start).days + 1
        request_url = (
            f"{FIRMS_AREA_API}/{map_key}/{source}/{bounding_box}/{day_count}/"
            f"{chunk_start.isoformat()}"
        )
        output_path = directory / (
            f"firms_{source.lower()}_{chunk_start.isoformat()}_{chunk_end.isoformat()}.csv"
        )
        try:
            with urlopen(request_url, timeout=90) as response:
                content = response.read().decode("utf-8")
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"FIRMS request failed for {chunk_start}: HTTP {error.code} {detail[:300]}"
            ) from error
        except URLError as error:
            raise RuntimeError(f"FIRMS request failed for {chunk_start}: {error}") from error

        if not content.lstrip().startswith("latitude,"):
            raise RuntimeError(
                f"FIRMS returned an unexpected response for {chunk_start}; no file was saved."
            )
        output_path.write_text(content, encoding="utf-8")
        downloads.append(
            {
                "start_date": chunk_start.isoformat(),
                "end_date": chunk_end.isoformat(),
                "days": day_count,
                "file": str(output_path.relative_to(directory.parent.parent.parent)),
            }
        )

    manifest_path = directory / (
        f"manifest_{source.lower()}_{start_date.isoformat()}_{end_date.isoformat()}.json"
    )
    write_json(
        manifest_path,
        {
            "source": "NASA FIRMS Area API",
            "product": source,
            "region_id": aoi.region_id,
            "bounding_box": [west, south, east, north],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "downloads": downloads,
        },
    )
    return str(manifest_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_collection_arguments(parser)
    parser.add_argument(
        "--source",
        default="VIIRS_NOAA20_SP",
        help="FIRMS product identifier (default: VIIRS_NOAA20_SP).",
    )
    parser.add_argument(
        "--chunk-days",
        type=int,
        default=5,
        help="Days per FIRMS API request, from 1 to 5 (default: 5).",
    )
    return parser


def main() -> None:
    load_project_environment()
    args = build_parser().parse_args()
    try:
        output_path = collect_labels(
            args.region,
            args.start_date,
            args.end_date,
            args.source,
            args.chunk_days,
        )
    except (RuntimeError, ValueError) as error:
        raise SystemExit(f"FIRMS collection failed: {error}") from error
    print(f"FIRMS label data saved to {output_path}")


if __name__ == "__main__":
    main()
