# Milestone 2.1 Multi-Source Model Comparison

## Prototype Scope

This report evaluates separate per-region fusion models on the existing 2024 daily AOI-level complete-case datasets. It does not pool regions, compare numerically against Phase 1 single-source results with different usable dates, or claim research-grade spatial or multi-year temporal validation.

## Fixed Evaluation Design

- Inputs: the approved 15-feature satellite + weather + leakage-safe historical fusion schema only.
- Target: `fire_label`; it and all provenance/metadata fields are excluded from model inputs.
- Temporal split: train through `2024-10-18`; test from `2024-10-19` onward. The split is never changed to obtain positives.
- Seeds: `11, 23, 37, 53, 71` for every model configuration.
- Metrics: precision, recall, F1, PR-AUC, and ROC-AUC only when held-out data contains both classes.
- Spatial-block CV: unavailable for this AOI-level dataset; no fabricated blocks are used.

## Uttarakhand, India — Rajaji landscape

- Fusion dataset: `datasets\processed\uttarakhand\fusion_ready_daily_aoi_features_2024-01-01_2024-12-31.csv`
- Dataset: 53 rows; 9 positive / 44 negative; coverage `2024-01-19` to `2024-12-29`.
- Fixed split: train 38 rows (9 positive / 29 negative); test 15 rows (0 positive / 15 negative).
- Feature count: 15 approved fusion features.
- Temporal holdout: prototype-valid only. This fixed within-2024 chronological holdout is not the future required multi-year earlier-years-versus-recent-year temporal safeguard.
- Spatial CV: unavailable. True spatial-block CV is unavailable: the current 2024 dataset contains daily AOI-level rows with no tile IDs, coordinates, pixels, or spatially varying units.

### Model Configurations

- **Fusion Logistic Regression**: `pipeline=StandardScaler + LogisticRegression`, `solver=liblinear`, `class_weight=balanced`, `max_iter=1000`.
- **Random Forest**: `n_estimators=300`, `max_depth=None`, `class_weight=balanced`, `n_jobs=-1`.
- **XGBoost**: `n_estimators=200`, `max_depth=3`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `scale_pos_weight=computed from each training split`, `objective=binary:logistic`.
- **LightGBM**: `n_estimators=200`, `num_leaves=15`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `scale_pos_weight=computed from each training split`, `objective=binary`.

### Five-Seed Aggregate Results

| Model | Precision | Recall | F1 | PR-AUC | ROC-AUC | Status |
|---|---:|---:|---:|---:|---:|---|
| Fusion Logistic Regression | unavailable | unavailable | unavailable | unavailable | unavailable | Held-out test partition has one class only; classification metrics are not mathematically valid. |
| Random Forest | unavailable | unavailable | unavailable | unavailable | unavailable | Held-out test partition has one class only; classification metrics are not mathematically valid. |
| XGBoost | unavailable | unavailable | unavailable | unavailable | unavailable | Held-out test partition has one class only; classification metrics are not mathematically valid. |
| LightGBM | unavailable | unavailable | unavailable | unavailable | unavailable | Held-out test partition has one class only; classification metrics are not mathematically valid. |

### Fusion Logistic Regression Seed-wise Results

Seed-wise metrics unavailable: Held-out test partition has one class only; classification metrics are not mathematically valid.

### Random Forest Seed-wise Results

Seed-wise metrics unavailable: Held-out test partition has one class only; classification metrics are not mathematically valid.

### XGBoost Seed-wise Results

Seed-wise metrics unavailable: Held-out test partition has one class only; classification metrics are not mathematically valid.

### LightGBM Seed-wise Results

Seed-wise metrics unavailable: Held-out test partition has one class only; classification metrics are not mathematically valid.

### Significance Status

- Unavailable: Held-out test partition has one class only; precision, recall, F1, PR-AUC, and ROC-AUC are reported unavailable.

### Limitations

- Same-day satellite observations retain a detection/prototype framing, not a forward-looking wildfire prediction framing.
- Complete-case filtering leaves sparse and non-contiguous observation dates because Sentinel-2 coverage is limited.
- This result does not satisfy future spatial-tile, spatial-block CV, or multi-year temporal-holdout requirements.
- The fixed held-out partition contains zero positive days, so no test metrics or significance result is available.

## Southern California, USA — San Bernardino Mountains

- Fusion dataset: `datasets\processed\california\fusion_ready_daily_aoi_features_2024-01-01_2024-12-31.csv`
- Dataset: 66 rows; 34 positive / 32 negative; coverage `2024-01-08` to `2024-12-23`.
- Fixed split: train 55 rows (29 positive / 26 negative); test 11 rows (5 positive / 6 negative).
- Feature count: 15 approved fusion features.
- Temporal holdout: prototype-valid only. This fixed within-2024 chronological holdout is not the future required multi-year earlier-years-versus-recent-year temporal safeguard.
- Spatial CV: unavailable. True spatial-block CV is unavailable: the current 2024 dataset contains daily AOI-level rows with no tile IDs, coordinates, pixels, or spatially varying units.

### Model Configurations

- **Fusion Logistic Regression**: `pipeline=StandardScaler + LogisticRegression`, `solver=liblinear`, `class_weight=balanced`, `max_iter=1000`.
- **Random Forest**: `n_estimators=300`, `max_depth=None`, `class_weight=balanced`, `n_jobs=-1`.
- **XGBoost**: `n_estimators=200`, `max_depth=3`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `scale_pos_weight=computed from each training split`, `objective=binary:logistic`.
- **LightGBM**: `n_estimators=200`, `num_leaves=15`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `scale_pos_weight=computed from each training split`, `objective=binary`.

### Five-Seed Aggregate Results

| Model | Precision | Recall | F1 | PR-AUC | ROC-AUC | Status |
|---|---:|---:|---:|---:|---:|---|
| Fusion Logistic Regression | 1.0000 ± 0.0000 | 0.6000 ± 0.0000 | 0.7500 ± 0.0000 | 0.9111 ± 0.0000 | 0.8667 ± 0.0000 | prototype-valid metrics |
| Random Forest | 0.4778 ± 0.0304 | 0.9200 ± 0.1095 | 0.6286 ± 0.0522 | 0.9067 ± 0.0061 | 0.8567 ± 0.0224 | prototype-valid metrics |
| XGBoost | 0.5111 ± 0.0248 | 1.0000 ± 0.0000 | 0.6762 ± 0.0213 | 0.9850 ± 0.0335 | 0.9800 ± 0.0447 | prototype-valid metrics |
| LightGBM | 0.6000 ± 0.0000 | 0.6000 ± 0.0000 | 0.6000 ± 0.0000 | 0.7533 ± 0.0000 | 0.7167 ± 0.0000 | prototype-valid metrics |

### Fusion Logistic Regression Seed-wise Results

| Seed | Precision | Recall | F1 | PR-AUC | ROC-AUC |
|---:|---:|---:|---:|---:|---:|
| 11 | 1.0000 | 0.6000 | 0.7500 | 0.9111 | 0.8667 |
| 23 | 1.0000 | 0.6000 | 0.7500 | 0.9111 | 0.8667 |
| 37 | 1.0000 | 0.6000 | 0.7500 | 0.9111 | 0.8667 |
| 53 | 1.0000 | 0.6000 | 0.7500 | 0.9111 | 0.8667 |
| 71 | 1.0000 | 0.6000 | 0.7500 | 0.9111 | 0.8667 |

### Random Forest Seed-wise Results

| Seed | Precision | Recall | F1 | PR-AUC | ROC-AUC |
|---:|---:|---:|---:|---:|---:|
| 11 | 0.5000 | 1.0000 | 0.6667 | 0.9111 | 0.8667 |
| 23 | 0.4444 | 0.8000 | 0.5714 | 0.9000 | 0.8333 |
| 37 | 0.5000 | 1.0000 | 0.6667 | 0.9111 | 0.8667 |
| 53 | 0.5000 | 1.0000 | 0.6667 | 0.9111 | 0.8833 |
| 71 | 0.4444 | 0.8000 | 0.5714 | 0.9000 | 0.8333 |

### XGBoost Seed-wise Results

| Seed | Precision | Recall | F1 | PR-AUC | ROC-AUC |
|---:|---:|---:|---:|---:|---:|
| 11 | 0.5000 | 1.0000 | 0.6667 | 1.0000 | 1.0000 |
| 23 | 0.5000 | 1.0000 | 0.6667 | 1.0000 | 1.0000 |
| 37 | 0.5000 | 1.0000 | 0.6667 | 1.0000 | 1.0000 |
| 53 | 0.5000 | 1.0000 | 0.6667 | 0.9250 | 0.9000 |
| 71 | 0.5556 | 1.0000 | 0.7143 | 1.0000 | 1.0000 |

### LightGBM Seed-wise Results

| Seed | Precision | Recall | F1 | PR-AUC | ROC-AUC |
|---:|---:|---:|---:|---:|---:|
| 11 | 0.6000 | 0.6000 | 0.6000 | 0.7533 | 0.7167 |
| 23 | 0.6000 | 0.6000 | 0.6000 | 0.7533 | 0.7167 |
| 37 | 0.6000 | 0.6000 | 0.6000 | 0.7533 | 0.7167 |
| 53 | 0.6000 | 0.6000 | 0.6000 | 0.7533 | 0.7167 |
| 71 | 0.6000 | 0.6000 | 0.6000 | 0.7533 | 0.7167 |

### Significance Status

- Unavailable: Held-out test partition has fewer than 20 rows; seed-based paired significance testing is too small to support an interpretable p-value.

### Limitations

- Same-day satellite observations retain a detection/prototype framing, not a forward-looking wildfire prediction framing.
- Complete-case filtering leaves sparse and non-contiguous observation dates because Sentinel-2 coverage is limited.
- This result does not satisfy future spatial-tile, spatial-block CV, or multi-year temporal-holdout requirements.
- The fixed held-out partition contains fewer than 20 rows; metrics are prototype-only and significance testing is intentionally unavailable.

## Southeastern Australia — East Gippsland, Victoria

- Fusion dataset: `datasets\processed\australia\fusion_ready_daily_aoi_features_2024-01-01_2024-12-31.csv`
- Dataset: 67 rows; 3 positive / 64 negative; coverage `2024-03-27` to `2024-12-29`.
- Fixed split: train 54 rows (3 positive / 51 negative); test 13 rows (0 positive / 13 negative).
- Feature count: 15 approved fusion features.
- Temporal holdout: prototype-valid only. This fixed within-2024 chronological holdout is not the future required multi-year earlier-years-versus-recent-year temporal safeguard.
- Spatial CV: unavailable. True spatial-block CV is unavailable: the current 2024 dataset contains daily AOI-level rows with no tile IDs, coordinates, pixels, or spatially varying units.

### Model Configurations

- **Fusion Logistic Regression**: `pipeline=StandardScaler + LogisticRegression`, `solver=liblinear`, `class_weight=balanced`, `max_iter=1000`.
- **Random Forest**: `n_estimators=300`, `max_depth=None`, `class_weight=balanced`, `n_jobs=-1`.
- **XGBoost**: `n_estimators=200`, `max_depth=3`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `scale_pos_weight=computed from each training split`, `objective=binary:logistic`.
- **LightGBM**: `n_estimators=200`, `num_leaves=15`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `scale_pos_weight=computed from each training split`, `objective=binary`.

### Five-Seed Aggregate Results

| Model | Precision | Recall | F1 | PR-AUC | ROC-AUC | Status |
|---|---:|---:|---:|---:|---:|---|
| Fusion Logistic Regression | unavailable | unavailable | unavailable | unavailable | unavailable | Held-out test partition has one class only; classification metrics are not mathematically valid. |
| Random Forest | unavailable | unavailable | unavailable | unavailable | unavailable | Held-out test partition has one class only; classification metrics are not mathematically valid. |
| XGBoost | unavailable | unavailable | unavailable | unavailable | unavailable | Held-out test partition has one class only; classification metrics are not mathematically valid. |
| LightGBM | unavailable | unavailable | unavailable | unavailable | unavailable | Held-out test partition has one class only; classification metrics are not mathematically valid. |

### Fusion Logistic Regression Seed-wise Results

Seed-wise metrics unavailable: Held-out test partition has one class only; classification metrics are not mathematically valid.

### Random Forest Seed-wise Results

Seed-wise metrics unavailable: Held-out test partition has one class only; classification metrics are not mathematically valid.

### XGBoost Seed-wise Results

Seed-wise metrics unavailable: Held-out test partition has one class only; classification metrics are not mathematically valid.

### LightGBM Seed-wise Results

Seed-wise metrics unavailable: Held-out test partition has one class only; classification metrics are not mathematically valid.

### Significance Status

- Unavailable: Held-out test partition has one class only; precision, recall, F1, PR-AUC, and ROC-AUC are reported unavailable.

### Limitations

- Same-day satellite observations retain a detection/prototype framing, not a forward-looking wildfire prediction framing.
- Complete-case filtering leaves sparse and non-contiguous observation dates because Sentinel-2 coverage is limited.
- This result does not satisfy future spatial-tile, spatial-block CV, or multi-year temporal-holdout requirements.
- The fixed held-out partition contains zero positive days, so no test metrics or significance result is available.

## Cross-Region Limitation

These regional results must not be pooled or interpreted as LORO evidence. LORO and pooled-model evaluation remain Milestone 2.1b.
