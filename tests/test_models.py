"""Tests for ML models, feature engineering, and predictive utilities."""

import pytest
import numpy as np
import pandas as pd

from analytics_module.features.engineering import (
    add_calendar_features,
    add_lag_features,
    add_rolling_features,
    build_training_dataset
)
from analytics_module.models.forecasting import (
    prepare_features,
    train_demand_model,
    evaluate_forecast
)
from analytics_module.models.predictive import predict_expiry_risk
from analytics_module.data.loader import sample_pairs


def test_calendar_features():
    df = pd.DataFrame({"date_key": [20250101, 20250102, 20250103]})
    out = add_calendar_features(df)
    assert "year" in out.columns
    assert "month" in out.columns
    assert "dayofweek" in out.columns
    assert "is_weekend" in out.columns
    assert out["year"].iloc[0] == 2025


def test_lag_and_rolling_features():
    df = pd.DataFrame({"quantity_consumed": np.arange(10, dtype=float)})
    lags = add_lag_features(df, "quantity_consumed", lags=[1, 2])
    assert "quantity_consumed_lag1" in lags.columns
    assert "quantity_consumed_lag2" in lags.columns
    assert lags["quantity_consumed_lag1"].iloc[1] == 0.0

    rolls = add_rolling_features(df, "quantity_consumed", windows=[3])
    assert "quantity_consumed_roll_mean_3" in rolls.columns


def test_demand_model_training_and_evaluation():
    # Synthetic mini-dataset for smoke testing model train & evaluate
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({
        "quantity_consumed_lag1": np.random.uniform(5, 50, n),
        "quantity_consumed_roll_mean_7": np.random.uniform(5, 50, n),
        "days_of_stock": np.random.uniform(1, 30, n),
    })
    y = X["quantity_consumed_lag1"] * 1.05 + np.random.normal(0, 1, n)

    X_train, X_test = X.iloc[:80], X.iloc[80:]
    y_train, y_test = y.iloc[:80], y.iloc[80:]

    model = train_demand_model(X_train, y_train, X_test, y_test)
    metrics = evaluate_forecast(model, X_test, y_test)

    assert "mae" in metrics
    assert "rmse" in metrics
    assert "baseline_mae" in metrics
    assert "mae_improvement_pct" in metrics
    assert metrics["mae"] >= 0.0
    assert len(metrics["preds"]) == len(X_test)


def test_predict_expiry_risk():
    batches = pd.DataFrame({
        "batch_id": ["B1", "B2"],
        "received_date": ["2025-01-01", "2025-02-01"],
        "expiry_date": ["2025-03-01", "2026-06-01"],
        "manufacturing_date": ["2024-01-01", "2024-02-01"],
        "initial_quantity": [1000, 2000],
        "remaining_quantity": [500, 1500]
    })
    risk_df = predict_expiry_risk(batches, horizon_days=90, reference_date="2025-02-15")
    assert "expiry_risk" in risk_df.columns
    assert "expiry_risk_score" in risk_df.columns
    # B1 expires in ~14 days from ref date -> risk = 1
    assert risk_df.loc[risk_df["batch_id"] == "B1", "expiry_risk"].iloc[0] == 1

