"""Leakage-aware prototype evaluation utilities for EarthDNA fusion models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


DATE_COLUMN = "date"
TARGET_COLUMN = "fire_label"
TEMPORAL_CUTOFF = pd.Timestamp("2024-10-19")
METRIC_NAMES = ("precision", "recall", "f1", "pr_auc", "roc_auc")
SPATIAL_COLUMNS = {"tile_id", "spatial_block", "latitude", "longitude", "geometry", "geometry_id"}


@dataclass(frozen=True)
class ChronologicalSplit:
    train: pd.DataFrame
    test: pd.DataFrame
    cutoff: pd.Timestamp = TEMPORAL_CUTOFF


def class_counts(frame: pd.DataFrame) -> dict[str, int]:
    positives = int(frame[TARGET_COLUMN].sum())
    return {"positive": positives, "negative": int(len(frame) - positives)}


def validate_target(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError("Dataset is empty")
    if TARGET_COLUMN not in frame:
        raise ValueError(f"Dataset is missing {TARGET_COLUMN}")
    if frame[TARGET_COLUMN].isna().any() or not frame[TARGET_COLUMN].isin([0, 1]).all():
        raise ValueError("fire_label must be binary with no missing values")


def chronological_split(frame: pd.DataFrame) -> ChronologicalSplit:
    """Apply the fixed, approved within-2024 calendar split without adjustment."""

    validate_target(frame)
    if DATE_COLUMN not in frame:
        raise ValueError(f"Dataset is missing {DATE_COLUMN}")
    if frame[DATE_COLUMN].isna().any():
        raise ValueError("Temporal key contains missing values")
    ordered = frame.sort_values(DATE_COLUMN).reset_index(drop=True)
    train = ordered[ordered[DATE_COLUMN] < TEMPORAL_CUTOFF].copy()
    test = ordered[ordered[DATE_COLUMN] >= TEMPORAL_CUTOFF].copy()
    if train.empty or test.empty:
        raise ValueError("The fixed chronological split produced an empty partition")
    if train[DATE_COLUMN].max() >= TEMPORAL_CUTOFF or test[DATE_COLUMN].min() < TEMPORAL_CUTOFF:
        raise ValueError("Chronological split enforcement failed")
    return ChronologicalSplit(train=train, test=test)


def spatial_cv_capability(frame: pd.DataFrame) -> dict[str, Any]:
    available = sorted(SPATIAL_COLUMNS.intersection(frame.columns))
    if available:
        return {
            "available": False,
            "reason": (
                "Spatial-looking columns were found, but this Milestone 2.1 prototype is defined "
                "as one AOI-level row per day and does not provide independent spatial sampling units."
            ),
            "spatial_columns": available,
        }
    return {
        "available": False,
        "reason": (
            "True spatial-block CV is unavailable: the current 2024 dataset contains daily "
            "AOI-level rows with no tile IDs, coordinates, pixels, or spatially varying units."
        ),
        "spatial_columns": [],
    }


def evaluation_capabilities(frame: pd.DataFrame, split: ChronologicalSplit) -> dict[str, Any]:
    test_counts = class_counts(split.test)
    train_counts = class_counts(split.train)
    metric_reason = None
    if len(split.test[TARGET_COLUMN].unique()) < 2:
        metric_reason = (
            "Held-out test partition has one class only; precision, recall, F1, PR-AUC, "
            "and ROC-AUC are reported unavailable."
        )
    if metric_reason is not None:
        significance = {"available": False, "reason": metric_reason}
    elif len(split.test) < 20:
        significance = {
            "available": False,
            "reason": (
                "Held-out test partition has fewer than 20 rows; seed-based paired significance "
                "testing is too small to support an interpretable p-value."
            ),
        }
    else:
        significance = {
            "available": True,
            "reason": "Both held-out classes are present and the holdout has at least 20 rows.",
        }
    return {
        "temporal_holdout": {
            "available": True,
            "cutoff": TEMPORAL_CUTOFF.date().isoformat(),
            "status": "prototype-valid only",
            "reason": (
                "This fixed within-2024 chronological holdout is not the future required "
                "multi-year earlier-years-versus-recent-year temporal safeguard."
            ),
        },
        "spatial_block_cv": spatial_cv_capability(frame),
        "train_counts": train_counts,
        "test_counts": test_counts,
        "test_metrics_available": metric_reason is None,
        "test_metrics_unavailable_reason": metric_reason,
        "significance_testing": significance,
    }


def unavailable_metrics(reason: str) -> dict[str, Any]:
    return {"available": False, "reason": reason, "values": {name: None for name in METRIC_NAMES}}


def calculate_metrics(y_true: pd.Series, probabilities: np.ndarray) -> dict[str, Any]:
    if y_true.nunique() < 2:
        return unavailable_metrics(
            "Held-out test partition has one class only; classification metrics are not mathematically valid."
        )
    predictions = (probabilities >= 0.5).astype(int)
    return {
        "available": True,
        "reason": None,
        "values": {
            "precision": float(precision_score(y_true, predictions, zero_division=0)),
            "recall": float(recall_score(y_true, predictions, zero_division=0)),
            "f1": float(f1_score(y_true, predictions, zero_division=0)),
            "pr_auc": float(average_precision_score(y_true, probabilities)),
            "roc_auc": float(roc_auc_score(y_true, probabilities)),
        },
    }


def aggregate_seed_metrics(seed_results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    results = list(seed_results)
    valid = [result for result in results if result["metrics"]["available"]]
    if not valid:
        reason = results[0]["metrics"]["reason"] if results else "No seed results available."
        return {
            "available": False,
            "reason": reason,
            "valid_seed_count": 0,
            "metrics": {name: {"mean": None, "std": None} for name in METRIC_NAMES},
        }
    summary: dict[str, Any] = {}
    for name in METRIC_NAMES:
        values = np.array([result["metrics"]["values"][name] for result in valid], dtype=float)
        summary[name] = {
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        }
    return {"available": True, "reason": None, "valid_seed_count": len(valid), "metrics": summary}


def paired_wilcoxon(
    baseline_results: list[dict[str, Any]],
    candidate_results: list[dict[str, Any]],
    metric_name: str = "pr_auc",
) -> dict[str, Any]:
    """Run only a guarded, exploratory paired test on five valid seed results."""

    baseline = [result for result in baseline_results if result["metrics"]["available"]]
    candidate = [result for result in candidate_results if result["metrics"]["available"]]
    if len(baseline) != len(candidate) or len(baseline) < 5:
        return {
            "available": False,
            "reason": "At least five valid paired seed results are required for significance testing.",
        }
    baseline_by_seed = {result["seed"]: result["metrics"]["values"][metric_name] for result in baseline}
    candidate_by_seed = {result["seed"]: result["metrics"]["values"][metric_name] for result in candidate}
    common_seeds = sorted(set(baseline_by_seed).intersection(candidate_by_seed))
    if len(common_seeds) < 5:
        return {"available": False, "reason": "Fewer than five matched seeds are available."}
    baseline_scores = np.array([baseline_by_seed[seed] for seed in common_seeds], dtype=float)
    candidate_scores = np.array([candidate_by_seed[seed] for seed in common_seeds], dtype=float)
    differences = candidate_scores - baseline_scores
    if not np.isfinite(differences).all() or np.allclose(differences, 0):
        return {
            "available": False,
            "reason": "Paired seed differences are all zero or non-finite; Wilcoxon is unsupported.",
        }
    statistic, p_value = wilcoxon(candidate_scores, baseline_scores, alternative="two-sided", method="auto")
    return {
        "available": True,
        "metric": metric_name,
        "test": "paired Wilcoxon signed-rank",
        "paired_seed_count": len(common_seeds),
        "statistic": float(statistic),
        "p_value": float(p_value),
        "interpretation": (
            "Exploratory only: five algorithm seeds on one small fixed holdout are not independent "
            "data replications and do not establish a research-grade conclusion."
        ),
    }
