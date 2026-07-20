"""Injury severity classifier over structured MSHA fields (Step 2)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.data.config import (
    ACCIDENTS_CLEAN_CSV,
    CLASSIFIER_TARGET_COLUMN,
    OUT_OF_TIME_TEST_MIN_YEAR,
    OUT_OF_TIME_TRAIN_MAX_YEAR,
    PROCESSED_DIR,
    RANDOM_SEED,
    TEST_CSV,
    TRAIN_CSV,
)
from src.data.features import select_classifier_features, select_classifier_target

CLASSIFIER_REPORT_JSON = PROCESSED_DIR / "classifier_evaluation.json"
CLASSIFIER_MODEL_PATH = PROCESSED_DIR / "injury_risk_classifier.joblib"

# RandomForest with 100 trees — standard baseline for tabular MSHA severity modeling.
DEFAULT_N_ESTIMATORS = 100


def normalize_target_labels(series: pd.Series) -> pd.Series:
    """Normalize injury degree codes to zero-padded strings (01 to 10)."""
    return series.astype(str).str.strip().str.zfill(2)


@dataclass
class EvaluationResult:
    split_name: str
    n_train: int
    n_test: int
    accuracy: float
    macro_f1: float
    weighted_f1: float
    per_class_recall: dict[str, float]
    per_class_support: dict[str, int]
    confusion_matrix: list[list[int]]
    labels: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _build_pipeline(feature_columns: list[str], random_state: int) -> Pipeline:
    encoder = ColumnTransformer(
        transformers=[
            (
                "codes",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                feature_columns,
            )
        ],
        remainder="drop",
    )
    model = RandomForestClassifier(
        n_estimators=DEFAULT_N_ESTIMATORS,
        random_state=random_state,
        n_jobs=-1,
        class_weight="balanced",
    )
    return Pipeline(
        steps=[
            ("encoder", encoder),
            ("classifier", model),
        ]
    )


class InjuryRiskClassifier:
    """
    Random forest classifier predicting MSHA injury degree (DEGREE_INJURY_CD).

    Uses only columns from select_classifier_features(); leakage columns in the
    cleaned dataframe are never passed to the model.
    """

    def __init__(
        self,
        include_mine_context: bool = False,
        random_state: int = RANDOM_SEED,
    ) -> None:
        self.include_mine_context = include_mine_context
        self.random_state = random_state
        self.pipeline: Pipeline | None = None
        self.feature_columns_: list[str] = []
        self.labels_: list[str] = []

    def fit(self, train_frame: pd.DataFrame) -> InjuryRiskClassifier:
        features = select_classifier_features(train_frame, include_mine_context=self.include_mine_context)
        target = normalize_target_labels(select_classifier_target(train_frame))
        self.feature_columns_ = list(features.columns)
        self.pipeline = _build_pipeline(self.feature_columns_, self.random_state)
        self.pipeline.fit(features.astype(str), target)
        self.labels_ = sorted(target.unique())
        return self

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        if self.pipeline is None:
            raise RuntimeError("Classifier is not fitted. Call fit() first.")
        features = select_classifier_features(frame, include_mine_context=self.include_mine_context)
        return self.pipeline.predict(features.astype(str))

    def evaluate(self, test_frame: pd.DataFrame, split_name: str, n_train: int) -> EvaluationResult:
        predictions = self.predict(test_frame)
        target = normalize_target_labels(select_classifier_target(test_frame))
        labels = sorted(set(target.unique()) | set(predictions))
        matrix = confusion_matrix(target, predictions, labels=labels)
        recall_values = recall_score(target, predictions, labels=labels, average=None, zero_division=0)
        support = target.value_counts().reindex(labels, fill_value=0).astype(int)
        return EvaluationResult(
            split_name=split_name,
            n_train=n_train,
            n_test=len(test_frame),
            accuracy=float(accuracy_score(target, predictions)),
            macro_f1=float(f1_score(target, predictions, labels=labels, average="macro", zero_division=0)),
            weighted_f1=float(f1_score(target, predictions, labels=labels, average="weighted", zero_division=0)),
            per_class_recall={label: float(rec) for label, rec in zip(labels, recall_values)},
            per_class_support={label: int(support[label]) for label in labels},
            confusion_matrix=matrix.tolist(),
            labels=labels,
        )

    def save(self, path: Path = CLASSIFIER_MODEL_PATH) -> None:
        if self.pipeline is None:
            raise RuntimeError("Classifier is not fitted. Call fit() first.")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "pipeline": self.pipeline,
                "feature_columns": self.feature_columns_,
                "labels": self.labels_,
                "include_mine_context": self.include_mine_context,
            },
            path,
        )

    @classmethod
    def load(cls, path: Path = CLASSIFIER_MODEL_PATH) -> InjuryRiskClassifier:
        payload = joblib.load(path)
        instance = cls(include_mine_context=payload["include_mine_context"])
        instance.pipeline = payload["pipeline"]
        instance.feature_columns_ = payload["feature_columns"]
        instance.labels_ = payload["labels"]
        return instance


def load_train_test_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not TRAIN_CSV.exists() or not TEST_CSV.exists():
        raise FileNotFoundError("Missing train/test CSV. Run python -m src.data.ingest first.")
    train = pd.read_csv(TRAIN_CSV, low_memory=False)
    test = pd.read_csv(TEST_CSV, low_memory=False)
    return train, test


def load_clean_frame() -> pd.DataFrame:
    if not ACCIDENTS_CLEAN_CSV.exists():
        raise FileNotFoundError("Missing cleaned CSV. Run python -m src.data.ingest first.")
    return pd.read_csv(ACCIDENTS_CLEAN_CSV, low_memory=False)


def split_out_of_time(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    years = pd.to_numeric(frame["CAL_YR"], errors="coerce")
    train = frame[years <= OUT_OF_TIME_TRAIN_MAX_YEAR].copy()
    test = frame[years >= OUT_OF_TIME_TEST_MIN_YEAR].copy()
    return train, test


def train_and_evaluate(
    include_mine_context: bool = False,
    save_model: bool = True,
    report_path: Path = CLASSIFIER_REPORT_JSON,
) -> dict[str, Any]:
    """Train on the stratified split and run primary plus out-of-time evaluation."""
    train, test = load_train_test_frames()
    classifier = InjuryRiskClassifier(include_mine_context=include_mine_context)
    classifier.fit(train)
    primary = classifier.evaluate(test, split_name="stratified_holdout", n_train=len(train))

    clean = load_clean_frame()
    oot_train, oot_test = split_out_of_time(clean)
    oot_classifier = InjuryRiskClassifier(include_mine_context=include_mine_context)
    oot_classifier.fit(oot_train)
    out_of_time = oot_classifier.evaluate(
        oot_test,
        split_name="out_of_time_2021_plus",
        n_train=len(oot_train),
    )

    if save_model:
        classifier.save()

    report = {
        "model": "RandomForestClassifier",
        "n_estimators": DEFAULT_N_ESTIMATORS,
        "class_weight": "balanced",
        "include_mine_context": include_mine_context,
        "feature_source": "select_classifier_features",
        "evaluations": [primary.to_dict(), out_of_time.to_dict()],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return report


def print_evaluation_report(report: dict[str, Any]) -> None:
    print("\n=== Injury Risk Classifier Evaluation ===\n")
    print(f"Model: {report['model']} (n_estimators={report['n_estimators']}, class_weight={report['class_weight']})")
    print(f"Mine context features: {report['include_mine_context']}\n")
    for evaluation in report["evaluations"]:
        print(f"--- {evaluation['split_name']} ---")
        print(f"Train rows: {evaluation['n_train']:,}  Test rows: {evaluation['n_test']:,}")
        print(f"Accuracy:    {evaluation['accuracy']:.4f}")
        print(f"Macro F1:    {evaluation['macro_f1']:.4f}")
        print(f"Weighted F1: {evaluation['weighted_f1']:.4f}")
        print("Per-class recall (support):")
        for label in sorted(evaluation["per_class_recall"].keys()):
            recall = evaluation["per_class_recall"][label]
            support = evaluation["per_class_support"][label]
            print(f"  {label}: recall={recall:.3f}  support={support:,}")
        print("Confusion matrix (rows=true, cols=pred) labels:", evaluation["labels"])
        for row in evaluation["confusion_matrix"]:
            print(" ", row)
        print()
