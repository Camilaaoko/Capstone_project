"""Stockout risk classification models."""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (roc_auc_score, precision_recall_fscore_support,
                             confusion_matrix, classification_report)
import lightgbm as lgb
import warnings
warnings.filterwarnings("ignore")

from analytics_module.config import MODEL_DIR, RANDOM_SEED, TEST_HORIZON_DAYS


EXCLUDE_COLS = ["date_key", "date", "facility_key", "commodity_key",
                "target_next_day", "stockout_next_7", "stockout_flag",
                "quantity_consumed"]


def prepare_risk_features(df, horizon=7):
    df = df.copy()
    df["stockout_risk"] = df["stockout_flag"].rolling(horizon, min_periods=1).max().shift(-horizon)
    df = df.dropna(subset=["stockout_risk"])
    feature_cols = [c for c in df.columns if c not in EXCLUDE_COLS + ["stockout_risk"]]
    X = df[feature_cols].fillna(0)
    # Keep only numeric columns
    X = X.select_dtypes(include=[np.number])
    feature_cols = X.columns.tolist()
    y = df["stockout_risk"].astype(int)
    return X, y, feature_cols


def train_risk_model(X_train, y_train, X_val=None, y_val=None, params=None):
    if params is None:
        params = {
            "objective": "binary",
            "metric": "auc",
            "boosting_type": "gbdt",
            "num_leaves": 63,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "random_state": RANDOM_SEED,
            "n_estimators": 500,
            "scale_pos_weight": len(y_train[y_train==0]) / max(1, len(y_train[y_train==1])),
        }
    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_val, label=y_val, reference=train_data) if X_val is not None else None
    callbacks = [lgb.early_stopping(50), lgb.log_evaluation(100)] if valid_data else [lgb.log_evaluation(100)]
    model = lgb.train(params, train_data, valid_sets=[valid_data] if valid_data else None,
                      callbacks=callbacks)
    return model


def evaluate_risk_model(model, X_test, y_test, threshold=0.5):
    probs = model.predict(X_test, num_iteration=model.best_iteration)
    preds = (probs >= threshold).astype(int)
    auc = roc_auc_score(y_test, probs)
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, preds, average="binary", zero_division=0)
    cm = confusion_matrix(y_test, preds)
    return {"auc": auc, "precision": prec, "recall": rec, "f1": f1,
            "confusion_matrix": cm, "probs": probs, "preds": preds}


def find_optimal_threshold(model, X_val, y_val):
    probs = model.predict(X_val, num_iteration=model.best_iteration)
    best_f1, best_thresh = 0, 0.5
    for t in np.arange(0.1, 0.9, 0.05):
        preds = (probs >= t).astype(int)
        _, _, f1, _ = precision_recall_fscore_support(y_val, preds, average="binary", zero_division=0)
        if f1 > best_f1:
            best_f1, best_thresh = f1, t
    return best_thresh, best_f1


def train_risk_per_pair(pairs_df, inv_df, cons_df, n_pairs=200, save_dir=None):
    from analytics_module.features.engineering import build_training_dataset

    results = {}
    save_path = Path(save_dir) if save_dir else MODEL_DIR / "risk_models"
    save_path.mkdir(parents=True, exist_ok=True)

    for i, (_, row) in enumerate(pairs_df.head(n_pairs).iterrows()):
        fac_key, com_key = row.facility_key, row.commodity_key
        train_df = build_training_dataset(pd.DataFrame([row]), inv_df, cons_df)
        if train_df is None or len(train_df) < 200:
            continue

        split_idx = int(len(train_df) * 0.8)
        train, test = train_df.iloc[:split_idx], train_df.iloc[split_idx:]

        X_train, y_train, feat_cols = prepare_risk_features(train)
        X_test, y_test, _ = prepare_risk_features(test)

        if y_train.sum() == 0 or y_test.sum() == 0:
            continue

        model = train_risk_model(X_train, y_train, X_test, y_test)
        threshold, _ = find_optimal_threshold(model, X_test, y_test)
        metrics = evaluate_risk_model(model, X_test, y_test, threshold)

        key = f"{row.facility_id}_{row.commodity_id}"
        results[key] = {"model": model, "metrics": metrics, "features": feat_cols,
                        "threshold": threshold,
                        "facility_key": fac_key, "commodity_key": com_key,
                        "facility_id": row.facility_id, "commodity_id": row.commodity_id}

        with open(save_path / f"risk_{key}.pkl", "wb") as f:
            pickle.dump({"model": model, "features": feat_cols, "metrics": metrics, "threshold": threshold}, f)

        if i % 20 == 0:
            print(f"  Trained {i+1}/{min(n_pairs, len(pairs_df))}: {key} AUC={metrics['auc']:.3f} F1={metrics['f1']:.3f}")

    return results


def predict_risk(model, feature_cols, threshold, current_features):
    X = pd.DataFrame([current_features])[feature_cols].fillna(0)
    prob = model.predict(X, num_iteration=model.best_iteration)[0]
    return {"probability": prob, "risk_flag": int(prob >= threshold), "threshold": threshold}