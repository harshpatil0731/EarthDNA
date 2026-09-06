# Wildfire Risk and Three-Region Study Design

## Fixed Scope

EarthDNA studies one environmental risk factor: **wildfire risk**. The study uses the same satellite, weather, historical-fire, and evidence-retrieval pipeline across three geographically and climatically distinct regions:

| Region ID | Study Region | Operational AOI | Climate and vegetation context |
|---|---|---|---|
| `uttarakhand` | Uttarakhand, India | Rajaji landscape | Himalayan/Shivalik forest; monsoon-influenced with a pre-monsoon fire season |
| `california` | Southern California, USA | San Bernardino Mountains | Mediterranean climate; chaparral and mixed forest; Santa Ana wind-driven fire conditions |
| `australia` | Southeastern Australia | East Gippsland, Victoria | Temperate eucalyptus forest with dry-season fire behaviour |

The operational AOIs are stored as WGS 84 GeoJSON polygons in `datasets/aoi/`. They are intentionally bounded study footprints rather than an entire state, province, or country, keeping later satellite processing and spatial-block evaluation tractable.

## Why Wildfire Risk

Wildfire is the fixed target because a consistent global label family can be used across all three regions: NASA FIRMS active-fire observations or a MODIS/VIIRS burned-area product. The shared target also supports a consistent feature story: rainfall deficit and temperature anomaly, together with Sentinel-2 NDVI/NDWI and historical fire or vegetation-trend features.

Adding regions while keeping one target lets EarthDNA test generalization without building separate label, feature, and scientific-literature systems for multiple unrelated risks.

## Why These Regions

- **Uttarakhand** provides India-based relevance and a monsoon-influenced forest-fire context.
- **Southern California** provides a Mediterranean, wind-driven wildfire environment with extensive wildfire literature for comparison and evidence retrieval.
- **Southeastern Australia** provides a temperate eucalyptus-fire environment distinct from the other two regions.

Together, the regions test whether multi-source wildfire-risk prediction and its SHAP-identified drivers transfer across monsoon-Himalayan, Mediterranean, and temperate-eucalyptus settings, or remain region-specific.

## AOI Definitions

All coordinates use longitude, latitude order in WGS 84 (`EPSG:4326`). Each file contains one rectangular operational boundary selected as a manageable research footprint.

| Region ID | File | Bounding box: west, south, east, north |
|---|---|---|
| `uttarakhand` | `datasets/aoi/uttarakhand.geojson` | `77.90, 29.95, 78.25, 30.25` |
| `california` | `datasets/aoi/california.geojson` | `-117.85, 34.10, -117.35, 34.45` |
| `australia` | `datasets/aoi/australia.geojson` | `147.00, -37.55, 147.55, -37.15` |

## Selection Checklist

The study design requires the following checks for every AOI before subsequent data work is considered complete:

- FIRMS/MODIS labels must contain both fire and non-fire periods in the study time range.
- Sentinel-2 coverage must be usable without persistent cloud obstruction.
- NASA POWER or Open-Meteo coverage must be adequate for the selected footprint.
- The fixed boundary must remain a manageable size for satellite processing and spatial-block cross-validation.

Milestone 1.2 defines and versions the study scope and boundaries only. It does not collect, inspect, or validate satellite, weather, or fire-label data; those activities begin in Milestone 1.3.

## Research Design Consequences

Later milestones must run single-source and fusion models per region, evaluate each with spatial-block cross-validation and a temporal holdout, and compare pooled and Leave-One-Region-Out (LORO) results. SHAP feature-importance rankings will be compared across the three in-region models. The Hybrid RAG corpus will combine shared wildfire literature with region-specific guidance and fire-history documents.
