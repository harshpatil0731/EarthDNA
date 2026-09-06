"""FastAPI endpoints for the Milestone 1.6 region switcher."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.repositories.regions import get_region, list_regions
from app.schemas import RegionDetail, RegionSummary


router = APIRouter(prefix="/api/regions", tags=["regions"])


@router.get("", response_model=list[RegionSummary])
def regions() -> list[RegionSummary]:
    return list_regions()


@router.get("/{region_id}", response_model=RegionDetail)
def region_detail(region_id: str) -> RegionDetail:
    region = get_region(region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")
    return region
