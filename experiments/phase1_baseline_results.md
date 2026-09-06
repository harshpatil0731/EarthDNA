# Phase 1 Single-Source Baseline Results

## Prototype Scope

These are 2024 daily AOI-level validation-prototype results, not final research claims. Each region is trained independently; no pooled or cross-region model is used.

## Reproducible Model and Split Settings

- Algorithm: `StandardScaler` + class-weighted `LogisticRegression`.
- Logistic Regression: `solver=liblinear`, `class_weight=balanced`, `max_iter=1000`, `random_state=42`.
- Calendar window: `2024-01-01` through `2024-12-31`.
- Chronological split: train `2024-01-01` through `2024-10-18` (80% of the 366 calendar days); test `2024-10-19` through `2024-12-31`.
- The same fixed calendar cutoff is retained for every region and source group. Rows lacking a source group's required features are excluded only from that group's baseline; no values are imputed.
- `fire_label=1` means one or more FIRMS detections occurred within the finalized AOI on the date.

## Source-Group Policy and Leakage Check

- Satellite-only uses `ndvi_mean`, `ndwi_mean`, and `cloud_cover_percent_mean`. Cloud cover is retained as a Sentinel-2 acquisition-condition input, not a weather or historical feature. This is a same-day detection/prototype framing, not forward-looking wildfire prediction.
- Weather-only uses `temperature_2m_mean`, `precipitation_sum`, and `relative_humidity_2m_mean`.
- Historical-only uses only prior fire activity and shifted prior vegetation statistics. Milestone 1.4 shifted every fire and vegetation value before rolling, so target-day fire labels and target-day vegetation values are excluded.
- The script validates that feature groups are disjoint and exclude the target, date, and provenance columns.

## Uttarakhand, India (Rajaji landscape)

- Feature table: `datasets\processed\uttarakhand\daily_aoi_features_2024-01-01_2024-12-31.csv`
- Milestone 1.4 metadata: `datasets\processed\uttarakhand\daily_aoi_features_2024-01-01_2024-12-31.metadata.json`
- Source coverage: 366 calendar days, 366 complete weather days, 62 satellite days, and 56 positive-label days.

| Source baseline | Usable / dropped rows | Train (+ / -) | Test (+ / -) | Precision | Recall | F1 | PR-AUC | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Satellite-only | 62 / 304 | 9 / 38 | 0 / 15 | unavailable | unavailable | unavailable | unavailable | unavailable |
| Weather-only | 366 / 0 | 46 / 246 | 10 / 64 | 0.3043 | 0.7000 | 0.4242 | 0.4148 | evaluated |
| Historical-only | 296 / 70 | 44 / 178 | 10 / 64 | 0.0000 | 0.0000 | 0.0000 | 0.2399 | evaluated |

### Satellite-only details

- Features: `ndvi_mean, ndwi_mean, cloud_cover_percent_mean`
- Input framing: Same-day detection/prototype framing. Sentinel-2 observations acquired on the target date are not forward-looking wildfire predictors.
- Missingness before source-specific filtering: ndvi_mean: 304, ndwi_mean: 304, cloud_cover_percent_mean: 304.
- Missing-data policy: Use only dates with complete same-day NDVI, NDWI, and cloud-cover values; never impute or silently include missing satellite days.
- Metric note: The fixed test split contains only one target class; precision, recall, F1, and PR-AUC are not meaningful and are reported unavailable.

### Weather-only details

- Features: `temperature_2m_mean, precipitation_sum, relative_humidity_2m_mean`
- Input framing: Daily AOI-centroid weather conditions aligned to the target date.
- Missingness before source-specific filtering: temperature_2m_mean: 0, precipitation_sum: 0, relative_humidity_2m_mean: 0.
- Missing-data policy: Use only rows with complete weather values; no imputation is applied.

### Historical-only details

- Features: `prior_fire_days_7d, prior_fire_days_30d, days_since_prior_fire, ndvi_prior_7d_mean, ndvi_prior_30d_mean, ndvi_prior_30d_trend, ndwi_prior_7d_mean, ndwi_prior_30d_mean, ndwi_prior_30d_trend`
- Input framing: Prior fire activity and shifted vegetation history available before the target day.
- Missingness before source-specific filtering: prior_fire_days_7d: 1, prior_fire_days_30d: 1, days_since_prior_fire: 17, ndvi_prior_7d_mean: 57, ndvi_prior_30d_mean: 19, ndvi_prior_30d_trend: 57, ndwi_prior_7d_mean: 57, ndwi_prior_30d_mean: 19, ndwi_prior_30d_trend: 57.
- Missing-data policy: Use only rows with complete historical values; no imputation is applied.

## Southern California, USA (San Bernardino Mountains)

- Feature table: `datasets\processed\california\daily_aoi_features_2024-01-01_2024-12-31.csv`
- Milestone 1.4 metadata: `datasets\processed\california\daily_aoi_features_2024-01-01_2024-12-31.metadata.json`
- Source coverage: 366 calendar days, 366 complete weather days, 69 satellite days, and 155 positive-label days.

| Source baseline | Usable / dropped rows | Train (+ / -) | Test (+ / -) | Precision | Recall | F1 | PR-AUC | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Satellite-only | 69 / 297 | 30 / 27 | 6 / 6 | 0.5000 | 0.5000 | 0.5000 | 0.6656 | evaluated |
| Weather-only | 366 / 0 | 121 / 171 | 34 / 40 | 0.5106 | 0.7059 | 0.5926 | 0.5480 | evaluated |
| Historical-only | 351 / 15 | 117 / 169 | 28 / 37 | 0.4308 | 1.0000 | 0.6022 | 0.4676 | evaluated |

### Satellite-only details

- Features: `ndvi_mean, ndwi_mean, cloud_cover_percent_mean`
- Input framing: Same-day detection/prototype framing. Sentinel-2 observations acquired on the target date are not forward-looking wildfire predictors.
- Missingness before source-specific filtering: ndvi_mean: 297, ndwi_mean: 297, cloud_cover_percent_mean: 297.
- Missing-data policy: Use only dates with complete same-day NDVI, NDWI, and cloud-cover values; never impute or silently include missing satellite days.

### Weather-only details

- Features: `temperature_2m_mean, precipitation_sum, relative_humidity_2m_mean`
- Input framing: Daily AOI-centroid weather conditions aligned to the target date.
- Missingness before source-specific filtering: temperature_2m_mean: 0, precipitation_sum: 0, relative_humidity_2m_mean: 0.
- Missing-data policy: Use only rows with complete weather values; no imputation is applied.

### Historical-only details

- Features: `prior_fire_days_7d, prior_fire_days_30d, days_since_prior_fire, ndvi_prior_7d_mean, ndvi_prior_30d_mean, ndvi_prior_30d_trend, ndwi_prior_7d_mean, ndwi_prior_30d_mean, ndwi_prior_30d_trend`
- Input framing: Prior fire activity and shifted vegetation history available before the target day.
- Missingness before source-specific filtering: prior_fire_days_7d: 1, prior_fire_days_30d: 1, days_since_prior_fire: 2, ndvi_prior_7d_mean: 15, ndvi_prior_30d_mean: 3, ndvi_prior_30d_trend: 15, ndwi_prior_7d_mean: 15, ndwi_prior_30d_mean: 3, ndwi_prior_30d_trend: 15.
- Missing-data policy: Use only rows with complete historical values; no imputation is applied.

## Southeastern Australia (East Gippsland, Victoria)

- Feature table: `datasets\processed\australia\daily_aoi_features_2024-01-01_2024-12-31.csv`
- Milestone 1.4 metadata: `datasets\processed\australia\daily_aoi_features_2024-01-01_2024-12-31.metadata.json`
- Source coverage: 366 calendar days, 366 complete weather days, 95 satellite days, and 14 positive-label days.

| Source baseline | Usable / dropped rows | Train (+ / -) | Test (+ / -) | Precision | Recall | F1 | PR-AUC | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Satellite-only | 95 / 271 | 5 / 74 | 0 / 16 | unavailable | unavailable | unavailable | unavailable | unavailable |
| Weather-only | 366 / 0 | 13 / 279 | 1 / 73 | 0.0196 | 1.0000 | 0.0385 | 0.1250 | evaluated |
| Historical-only | 263 / 103 | 11 / 185 | 1 / 66 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | evaluated |

### Satellite-only details

- Features: `ndvi_mean, ndwi_mean, cloud_cover_percent_mean`
- Input framing: Same-day detection/prototype framing. Sentinel-2 observations acquired on the target date are not forward-looking wildfire predictors.
- Missingness before source-specific filtering: ndvi_mean: 271, ndwi_mean: 271, cloud_cover_percent_mean: 271.
- Missing-data policy: Use only dates with complete same-day NDVI, NDWI, and cloud-cover values; never impute or silently include missing satellite days.
- Metric note: The fixed test split contains only one target class; precision, recall, F1, and PR-AUC are not meaningful and are reported unavailable.

### Weather-only details

- Features: `temperature_2m_mean, precipitation_sum, relative_humidity_2m_mean`
- Input framing: Daily AOI-centroid weather conditions aligned to the target date.
- Missingness before source-specific filtering: temperature_2m_mean: 0, precipitation_sum: 0, relative_humidity_2m_mean: 0.
- Missing-data policy: Use only rows with complete weather values; no imputation is applied.
- Metric note: The fixed test split has fewer than five positive days; the reported metrics are numerically computable but highly unstable.

### Historical-only details

- Features: `prior_fire_days_7d, prior_fire_days_30d, days_since_prior_fire, ndvi_prior_7d_mean, ndvi_prior_30d_mean, ndvi_prior_30d_trend, ndwi_prior_7d_mean, ndwi_prior_30d_mean, ndwi_prior_30d_trend`
- Input framing: Prior fire activity and shifted vegetation history available before the target day.
- Missingness before source-specific filtering: prior_fire_days_7d: 1, prior_fire_days_30d: 1, days_since_prior_fire: 84, ndvi_prior_7d_mean: 32, ndvi_prior_30d_mean: 12, ndvi_prior_30d_trend: 32, ndwi_prior_7d_mean: 32, ndwi_prior_30d_mean: 12, ndwi_prior_30d_trend: 32.
- Missing-data policy: Use only rows with complete historical values; no imputation is applied.
- Metric note: The fixed test split has fewer than five positive days; the reported metrics are numerically computable but highly unstable.

## Cross-Region Comparison

| Region | Satellite usable rows / positive days | Weather usable rows / positive days | Historical usable rows / positive days |
|---|---:|---:|---:|
| Uttarakhand, India | 62 / 9 | 366 / 56 | 296 / 54 |
| Southern California, USA | 69 / 36 | 366 / 155 | 351 / 145 |
| Southeastern Australia | 95 / 5 | 366 / 14 | 263 / 12 |

## Limitations

- This is a one-year, 2024 AOI-level prototype. It cannot support the later temporal-holdout or spatial-block evaluation claims.
- Satellite coverage is sparse and source-specific complete-case filtering substantially reduces satellite baseline sample sizes.
- Uttarakhand and Southeastern Australia satellite test windows contain no positive days under the fixed split, so their satellite metrics are unavailable rather than altered.
- Southeastern Australia has very few positive days overall, especially for satellite-only rows; any available baseline metrics are unstable.
- FIRMS active-fire detections are an operational proxy for the chosen daily target and do not constitute confirmed wildfire-event labels.
- Phase 2 must add the approved multi-year dataset, spatial-block CV, temporal holdout evaluation, multi-seed runs, model-family comparison, and fusion modelling.
