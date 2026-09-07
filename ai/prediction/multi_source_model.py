"""Load validated per-region fusion data and build reproducible model configurations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIRECTORY = REPOSITORY_ROOT / "datasets" / "processed"
REGION_IDS = ("uttarakhand", "california", "australia")
DATE_COLUMN = "date"
TARGET_COLUMN = "fire_label"
FUSION_FEATURES = (
    "ndvi_mean",
    "ndwi_mean",
    "cloud_cover_percent_mean",
    "temperature_2m_mean",
    "precipitation_sum",
    "relative_humidity_2m_mean",
    "prior_fire_days_7d",
    "prior_fire_days_30d",
    "days_since_prior_fire",
    "ndvi_prior_7d_mean",
    "ndvi_prior_30d_mean",
    "ndvi_prior_30d_trend",
    "ndwi_prior_7d_mean",
    "ndwi_prior_30d_mean",
    "ndwi_prior_30d_trend",
)
PROVENANCE_COLUMNS = {
    DATE_COLUMN,
    "region_id",
    "study_region",
    "operational_aoi",
    "aoi_file",
    "run_start_date",
    "run_end_date",
    "source_input_filename",
    "fusion_start_date",
    "fusion_end_date",
    "fusion_feature_configuration",
}


@dataclass(frozen=True)
class ModelSpec:
    name: str
    is_baseline: bool
    configuration: dict[str, Any]


MODEL_SPECS = (
    ModelSpec(
        name="Fusion Logistic Regression",
        is_baseline=True,
        configuration={
            "pipeline": "StandardScaler + LogisticRegression",
            "solver": "liblinear",
            "class_weight": "balanced",
            "max_iter": 1000,
        },
    ),
    ModelSpec(
        name="Random Forest",
        is_baseline=False,
        configuration={
            "n_estimators": 300,
            "max_depth": None,
            "class_weight": "balanced",
            "n_jobs": -1,
        },
    ),
    ModelSpec(
        name="XGBoost",
        is_baseline=False,
        configuration={
            "n_estimators": 200,
            "max_depth": 3,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "scale_pos_weight": "computed from each training split",
            "objective": "binary:logistic",
        },
    ),
    ModelSpec(
        name="LightGBM",
        is_baseline=False,
        configuration={
            "n_estimators": 200,
            "num_leaves": 15,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "scale_pos_weight": "computed from each training split",
            "objective": "binary",
        },
    ),
)


def fusion_path(region: str) -> Path:
    filename = "fusion_ready_daily_aoi_features_2024-01-01_2024-12-31.csv"
    return PROCESSED_DATA_DIRECTORY / region / filename


def load_fusion_dataset(region: str) -> pd.DataFrame:
    """Load one region only and enforce the approved complete-case fusion schema."""

    if region not in REGION_IDS:
        raise ValueError(f"Unknown region: {region}")
    path = fusion_path(region)
    if not path.exists():
        raise FileNotFoundError(f"Fusion dataset not found: {path}")

    frame = pd.read_csv(path, parse_dates=[DATE_COLUMN])
    missing_columns = sorted({DATE_COLUMN, TARGET_COLUMN, *FUSION_FEATURES} - set(frame.columns))
    if missing_columns:
        raise ValueError(f"Fusion dataset is missing required columns: {', '.join(missing_columns)}")
    if frame.empty:
        raise ValueError("Fusion dataset is empty")
    if not frame["region_id"].eq(region).all():
        raise ValueError(f"Fusion data provenance does not match requested region '{region}'")
    if frame[DATE_COLUMN].isna().any() or frame.duplicated(DATE_COLUMN).any():
        raise ValueError("Fusion dataset has invalid or duplicate date values")
    if frame[TARGET_COLUMN].isna().any() or not frame[TARGET_COLUMN].isin([0, 1]).all():
        raise ValueError("fire_label must be complete and binary")
    if TARGET_COLUMN in FUSION_FEATURES or PROVENANCE_COLUMNS.intersection(FUSION_FEATURES):
        raise ValueError("Target or provenance leakage detected in fusion feature schema")
    if frame.loc[:, FUSION_FEATURES].isna().any().any():
        raise ValueError("Fusion dataset contains missing input features; no imputation is permitted")

    return frame.sort_values(DATE_COLUMN).reset_index(drop=True)


def training_scale_pos_weight(labels: pd.Series) -> float:
    positives = int(labels.sum())
    negatives = int(len(labels) - positives)
    if positives == 0 or negatives == 0:
        raise ValueError("Training partition must contain both classes")
    return negatives / positives


def build_model(spec: ModelSpec, seed: int, training_labels: pd.Series) -> Any:
    """Instantiate one fixed, class-aware fusion model for a reproducible seed."""

    scale_pos_weight = training_scale_pos_weight(training_labels)
    if spec.name == "Fusion Logistic Regression":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=1000,
                        random_state=seed,
                        solver="liblinear",
                    ),
                ),
            ]
        )
    if spec.name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            n_jobs=-1,
            random_state=seed,
        )
    if spec.name == "XGBoost":
        return XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            random_state=seed,
            n_jobs=-1,
        )
    if spec.name == "LightGBM":
        return LGBMClassifier(
            objective="binary",
            n_estimators=200,
            num_leaves=15,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            random_state=seed,
            n_jobs=-1,
            verbosity=-1,
        )
    raise ValueError(f"Unknown model specification: {spec.name}")
