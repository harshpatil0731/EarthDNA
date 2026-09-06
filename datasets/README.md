# Data Storage and Collection

Milestone 1.3 keeps all downloaded observations outside Git under this layout:

```text
datasets/
├── aoi/                         # Versioned GeoJSON study boundaries
└── raw/
    ├── uttarakhand/
    │   ├── satellite/
    │   ├── weather/
    │   └── labels/firms/
    ├── california/
    │   ├── satellite/
    │   ├── weather/
    │   └── labels/firms/
    └── australia/
        ├── satellite/
        ├── weather/
        └── labels/firms/
```

`datasets/raw/` is ignored by Git. This keeps downloaded API responses, Sentinel-derived scene summaries, and FIRMS CSV files out of the repository while retaining the collection code, AOI definitions, command arguments, and output metadata needed to reproduce them.

## Collection Commands

Install the collection dependencies once:

```powershell
python -m venv ai/.venv
.\ai\.venv\Scripts\python.exe -m pip install -r ai/requirements.txt
```

Run every command from the repository root and replace the dates with the study period approved for an experiment:

```powershell
.\ai\.venv\Scripts\python.exe ai\features\weather_collection.py --region uttarakhand --start-date 2024-01-01 --end-date 2024-12-31
.\ai\.venv\Scripts\python.exe ai\features\satellite_collection.py --region uttarakhand --start-date 2024-01-01 --end-date 2024-12-31
.\ai\.venv\Scripts\python.exe ai\features\label_collection.py --region uttarakhand --start-date 2024-01-01 --end-date 2024-12-31
```

Use `california` or `australia` in the same commands for the other operational AOIs. The scripts load the matching boundary from `datasets/aoi/`; no collection script contains a duplicated region boundary.

## External Access

Weather collection uses the Open-Meteo Archive API and does not require a key. The weather response is an AOI-centroid daily series; spatial aggregation or feature merging is deliberately deferred to Milestone 1.4.

Satellite collection uses Google Earth Engine and the Sentinel-2 Surface Reflectance Harmonized collection. Set `EE_PROJECT` in the ignored repository-root `.env` after authenticating an Earth Engine-enabled Google account and choosing a Google Cloud project.

FIRMS label collection uses the NASA FIRMS Area API. Set its free `FIRMS_MAP_KEY` in `.env`; it is never committed. The script downloads CSV files in ten-day chunks and writes a manifest describing the run.
