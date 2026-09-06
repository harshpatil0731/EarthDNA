"""Database queries for the three finalized EarthDNA AOIs."""

from __future__ import annotations

import json
from typing import Any

from app.database import connection


REGION_ORDER_SQL = "FIELD(r.region_id, 'uttarakhand', 'california', 'australia')"
BASE_SELECT = """
    SELECT
        r.region_id,
        r.study_region_name,
        r.aoi_name,
        r.risk_target,
        r.geometry_version,
        r.aoi_geometry,
        p.phase_label,
        p.risk_status,
        p.health_status,
        p.status_note
    FROM aoi_regions AS r
    INNER JOIN dashboard_placeholders AS p ON p.region_id = r.region_id
"""


def normalize_region(row: dict[str, Any]) -> dict[str, Any]:
    geometry = row.pop("aoi_geometry")
    if isinstance(geometry, (bytes, bytearray)):
        geometry = geometry.decode("utf-8")
    if isinstance(geometry, str):
        geometry = json.loads(geometry)
    row["aoi_geometry"] = geometry
    row["placeholder"] = {
        "phase_label": row.pop("phase_label"),
        "risk_status": row.pop("risk_status"),
        "health_status": row.pop("health_status"),
        "status_note": row.pop("status_note"),
    }
    return row


def list_regions() -> list[dict[str, Any]]:
    with connection() as database_connection:
        cursor = database_connection.cursor(dictionary=True)
        cursor.execute(f"{BASE_SELECT} ORDER BY {REGION_ORDER_SQL}")
        rows = cursor.fetchall()
        cursor.close()
    return [normalize_region(row) for row in rows]


def get_region(region_id: str) -> dict[str, Any] | None:
    with connection() as database_connection:
        cursor = database_connection.cursor(dictionary=True)
        cursor.execute(f"{BASE_SELECT} WHERE r.region_id = %s", (region_id,))
        row = cursor.fetchone()
        cursor.close()
    return normalize_region(row) if row else None
