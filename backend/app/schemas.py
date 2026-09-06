"""API response schemas for the Phase 1 region dashboard."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PlaceholderDashboard(BaseModel):
    phase_label: str
    risk_status: str
    health_status: str
    status_note: str


class RegionSummary(BaseModel):
    region_id: str
    study_region_name: str
    aoi_name: str
    risk_target: str
    placeholder: PlaceholderDashboard


class RegionDetail(RegionSummary):
    geometry_version: str
    aoi_geometry: dict[str, Any]
