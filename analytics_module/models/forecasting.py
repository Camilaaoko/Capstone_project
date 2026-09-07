"""Demand forecasting models."""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
import lightgbm as lgb
import warnings
warnings.filterwarnings("ignore")

from analytics_module.config import MODEL_DIR, RANDOM_SEED, FORECAST_HORIZON_DAYS, TEST_HORIZON_DAYS


EXCLUDE_COLS = ["date_key", "date", "facility_key", "commodity_key",
                "target_next_day", "stockout_next_7", "stockout_flag"]


def prepare_features(df):
    feature_cols = [c for c in df.columns if c not in EXCLUDE_COLS]
    X = df[feature_cols].fillna(0)
    # Keep only numeric columns
    X = X.select_dtypes(include=[np.number])
    feature_cols = X.columns.tolist()
    y = df["target_next_day"].fillna(0)
    return X, y, feature_cols


def train_demand_model(X_train, y_train, X_val=None, y_val=None, params=None):
    if params is None:
        params = {
            "objective": "regression",
            "metric": "mae",
            "boosting_type": "gbdt",
            "num_leaves": 63,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "random_state": RANDOM_SEED,
            "n_estimators": 500,
        }
    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_val, label=y_val, reference=train_data) if X_val is not None else None

    callbacks = [lgb.early_stopping(50), lgb.log_evaluation(100)] if valid_data else [lgb.log_evaluation(100)]
    model = lgb.train(params, train_data, valid_sets=[valid_data] if valid_data else None,
                      callbacks=callbacks)
    return model


def evaluate_forecast(model, X_test, y_test, baseline_preds=None):
    preds = model.predict(X_test, num_iteration=model.best_iteration)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    mape = mean_absolute_percentage_error(y_test + 1e-6, preds + 1e-6)

    # Compute baseline benchmark (Lag-1 Naive / 7-day Moving Average)
    if baseline_preds is None:
        if "quantity_consumed_lag1" in X_test.columns:
            baseline_preds = X_test["quantity_consumed_lag1"].values
        elif "quantity_consumed_roll_mean_7" in X_test.columns:
            baseline_preds = X_test["quantity_consumed_roll_mean_7"].values
        else:
            baseline_preds = np.full_like(preds, y_test.mean())

    base_mae = mean_absolute_error(y_test, baseline_preds)
    base_rmse = np.sqrt(mean_squared_error(y_test, baseline_preds))
    mae_improvement_pct = max(0.0, (base_mae - mae) / (base_mae + 1e-6) * 100.0)

    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "preds": preds,
        "baseline_mae": base_mae,
        "baseline_rmse": base_rmse,
        "mae_improvement_pct": mae_improvement_pct,
    }


def train_per_pair(pairs_df, inv_df, cons_df, n_pairs=100, save_dir=None):
    from analytics_module.features.engineering import build_training_dataset

    results = {}
    save_path = Path(save_dir) if save_dir else MODEL_DIR / "demand_models"
    save_path.mkdir(parents=True, exist_ok=True)

    for i, (_, row) in enumerate(pairs_df.head(n_pairs).iterrows()):
        fac_key, com_key = row.facility_key, row.commodity_key
        train_df = build_training_dataset(pd.DataFrame([row]), inv_df, cons_df)
        if train_df is None or len(train_df) < 200:
            continue

        split_idx = int(len(train_df) * 0.8)
        train, test = train_df.iloc[:split_idx], train_df.iloc[split_idx:]

        X_train, y_train, feat_cols = prepare_features(train)
        X_test, y_test, _ = prepare_features(test)

        model = train_demand_model(X_train, y_train, X_test, y_test)
        metrics = evaluate_forecast(model, X_test, y_test)

        key = f"{row.facility_id}_{row.commodity_id}"
        results[key] = {"model": model, "metrics": metrics, "features": feat_cols,
                        "facility_key": fac_key, "commodity_key": com_key,
                        "facility_id": row.facility_id, "commodity_id": row.commodity_id}

        with open(save_path / f"demand_{key}.pkl", "wb") as f:
            pickle.dump({"model": model, "features": feat_cols, "metrics": metrics}, f)

        if i % 20 == 0:
            print(f"  Trained {i+1}/{min(n_pairs, len(pairs_df))}: {key} MAE={metrics['mae']:.2f}")

    return results


def forecast_next_period(model, feature_cols, last_known_features, horizon=FORECAST_HORIZON_DAYS):
    preds = []
    current = last_known_features.copy()
    for _ in range(horizon):
        X = pd.DataFrame([current])[feature_cols].fillna(0)
        pred = max(0, model.predict(X, num_iteration=model.best_iteration)[0])
        preds.append(pred)
        for lag in [30, 14, 7, 3, 2, 1]:
            col = f"quantity_consumed_lag{lag}"
            if col in current:
                if lag == 1:
                    current[col] = pred
                else:
                    current[col] = current.get(f"quantity_consumed_lag{lag-1}", pred)
        for w in [60, 30, 14, 7]:
            mean_col = f"quantity_consumed_roll_mean_{w}"
            if mean_col in current:
                current[mean_col] = np.mean([pred] + [current.get(f"quantity_consumed_lag{l}", pred) for l in range(1, min(w, 30))])
    return np.array(preds)


def load_model(model_path):
    with open(model_path, "rb") as f:
        return pickle.load(f)