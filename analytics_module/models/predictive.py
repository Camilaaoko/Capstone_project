"""Predictive analytics: redistribution, expiry, supplier delays."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, roc_auc_score
import pickle
import warnings
warnings.filterwarnings("ignore")

from analytics_module.config import MODEL_DIR, RANDOM_SEED


def predict_expiry_risk(batches_df, horizon_days=90, reference_date=None):
    df = batches_df.copy()
    df["received_date"] = pd.to_datetime(df["received_date"])
    df["expiry_date"] = pd.to_datetime(df["expiry_date"])
    df["manufacturing_date"] = pd.to_datetime(df["manufacturing_date"])
    
    if reference_date is None:
        reference_date = df["received_date"].max() if df["received_date"].notna().any() else pd.Timestamp("2025-12-31")
    else:
        reference_date = pd.to_datetime(reference_date)
        
    df["days_to_expiry"] = (df["expiry_date"] - reference_date).dt.days
    df["shelf_life_remaining_pct"] = np.where(
        df["initial_quantity"] > 0,
        df["remaining_quantity"] / df["initial_quantity"], 0
    )
    df["expiry_risk"] = ((df["days_to_expiry"] <= horizon_days) & (df["remaining_quantity"] > 0)).astype(int)
    df["expiry_risk_score"] = np.where(
        df["days_to_expiry"] > 0,
        df["remaining_quantity"] / (df["days_to_expiry"] / 30 + 1), 0
    )
    return df.sort_values("expiry_risk_score", ascending=False)


def optimize_redistribution(redis_df, inventory_df, max_distance_km=400):
    redis = redis_df[redis_df["redistribution_status"] == "RECOMMENDED"].copy()
    redis["cost_per_unit"] = np.where(
        redis["recommended_quantity"] > 0,
        redis["transport_cost"] / redis["recommended_quantity"], 0
    )
    redis["value_density"] = redis["recommended_quantity"] / (redis["distance_km"] + 1)
    return redis.sort_values(["cost_per_unit", "distance_km"]).reset_index(drop=True)


def predict_supplier_delays(orders_df, supplier_df, horizon_days=30):
    df = orders_df.merge(supplier_df[["supplier_key", "supplier_id", "on_time_delivery_rate"]], on="supplier_key")
    df = df[df["order_status"].isin(["FULFILLED", "DELAYED", "PARTIALLY_FULFILLED"])].copy()
    df["delayed"] = (df["order_status"] == "DELAYED").astype(int)
    df["delay_days"] = df["delay_days"].fillna(0)
    df["lead_time_ratio"] = df["lead_time_actual_days"] / df["delay_days"].replace(0, np.nan)
    return df


def build_redistribution_optimizer(redis_df, inventory_df, facility_df, commodity_df):
    redis = redis_df[redis_df["redistribution_status"] == "RECOMMENDED"].copy()
    redis = redis.merge(facility_df[["facility_key", "facility_id", "county"]].add_prefix("source_"),
                        left_on="source_facility_id", right_on="source_facility_id", how="left")
    redis = redis.merge(facility_df[["facility_key", "facility_id", "county"]].add_prefix("dest_"),
                        left_on="destination_facility_id", right_on="dest_facility_id", how="left")
    redis = redis.merge(commodity_df[["commodity_key", "unit_cost"]], on="commodity_key", how="left")
    redis["commodity_value"] = redis["recommended_quantity"] * redis["unit_cost"]
    redis["roi"] = np.where(redis["transport_cost"] > 0,
                            redis["commodity_value"] / redis["transport_cost"], 0)
    redis["priority_score"] = redis["roi"] * redis["destination_days_of_stock"].fillna(0)
    return redis.sort_values("priority_score", ascending=False)


def train_supplier_delay_model(orders_df, supplier_df):
    df = orders_df.merge(supplier_df[["supplier_key", "on_time_delivery_rate", "reliability_score"]], on="supplier_key")
    df["delayed"] = (df["order_status"] == "DELAYED").astype(int)
    features = ["on_time_delivery_rate", "reliability_score", "quantity_ordered", "priority_level"]
    df = df.dropna(subset=features + ["delayed"])
    X = pd.get_dummies(df[features], columns=["priority_level"], drop_first=True)
    y = df["delayed"]
    model = RandomForestClassifier(n_estimators=200, random_state=RANDOM_SEED, class_weight="balanced")
    model.fit(X, y)
    return model, X.columns.tolist()


def train_expiry_model(batches_df, reference_date=None):
    df = batches_df.copy()
    rec_dates = pd.to_datetime(df["received_date"]) if "received_date" in df.columns else None
    if reference_date is None:
        reference_date = rec_dates.max() if rec_dates is not None and rec_dates.notna().any() else pd.Timestamp("2025-12-31")
    else:
        reference_date = pd.to_datetime(reference_date)
        
    df["days_to_expiry"] = (pd.to_datetime(df["expiry_date"]) - reference_date).dt.days
    df["expiry_risk"] = ((df["days_to_expiry"] <= 90) & (df["remaining_quantity"] > 0)).astype(int)
    features = ["initial_quantity", "remaining_quantity", "days_to_expiry", "batch_status"]
    df = df.dropna(subset=features + ["expiry_risk"])
    X = pd.get_dummies(df[features], columns=["batch_status"], drop_first=True)
    y = df["expiry_risk"]
    model = RandomForestClassifier(n_estimators=200, random_state=RANDOM_SEED, class_weight="balanced")
    model.fit(X, y)
    return model, X.columns.tolist()


def save_model(model, feature_cols, path):
    with open(path, "wb") as f:
        pickle.dump({"model": model, "features": feature_cols}, f)


def load_model(path):
    with open(path, "rb") as f:
        return pickle.load(f)