"""Feature engineering for demand forecasting and stockout risk."""

import numpy as np
import pandas as pd
from analytics_module.config import TEST_HORIZON_DAYS, MIN_TRAIN_DAYS


def add_calendar_features(df, date_col="date_key"):
    df = df.copy()
    df["date"] = pd.to_datetime(df[date_col].astype(str), format="%Y%m%d")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["dayofweek"] = df["date"].dt.dayofweek
    df["dayofyear"] = df["date"].dt.dayofyear
    df["weekofyear"] = df["date"].dt.isocalendar().week
    df["quarter"] = df["date"].dt.quarter
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    df["is_month_start"] = df["date"].dt.is_month_start.astype(int)
    df["is_month_end"] = df["date"].dt.is_month_end.astype(int)
    df["days_since_start"] = (df["date"] - df["date"].min()).dt.days
    return df


def add_lag_features(df, target_col, lags=[1, 2, 3, 7, 14, 30]):
    df = df.copy()
    for lag in lags:
        df[f"{target_col}_lag{lag}"] = df[target_col].shift(lag)
    return df


def add_rolling_features(df, target_col, windows=[7, 14, 30, 60]):
    df = df.copy()
    for w in windows:
        df[f"{target_col}_roll_mean_{w}"] = df[target_col].rolling(w, min_periods=1).mean()
        df[f"{target_col}_roll_std_{w}"] = df[target_col].rolling(w, min_periods=1).std()
        df[f"{target_col}_roll_min_{w}"] = df[target_col].rolling(w, min_periods=1).min()
        df[f"{target_col}_roll_max_{w}"] = df[target_col].rolling(w, min_periods=1).max()
    return df


def add_trend_features(df, target_col, windows=[7, 30]):
    df = df.copy()
    for w in windows:
        roll = df[target_col].rolling(w, min_periods=2)
        df[f"{target_col}_trend_{w}"] = roll.apply(
            lambda x: np.polyfit(np.arange(len(x)), x, 1)[0] if len(x) == w else 0, raw=True
        )
    return df


def add_inventory_features(inv_df, cons_df):
    inv = inv_df.copy()
    inv["dofs"] = np.where(inv["expected_daily_demand"] > 0,
                           inv["closing_stock"] / inv["expected_daily_demand"], 0)
    inv["stockout_flag"] = (inv["stock_status"] == "STOCKOUT").astype(int)
    inv["critical_flag"] = (inv["stock_status"] == "CRITICAL").astype(int)
    inv["overstock_flag"] = (inv["stock_status"] == "OVERSTOCKED").astype(int)
    inv["days_since_received"] = inv.groupby(["facility_key", "commodity_key"])["quantity_received"].transform(
        lambda x: (x > 0).cumsum()
    )
    return inv


def load_pair_features_from_db(fac_key, com_key, conn=None):
    """Direct fast SQL extraction for a single facility-commodity pair."""
    close_conn = False
    if conn is None:
        from analytics_module.data.loader import get_connection
        conn = get_connection()
        close_conn = True

    cons_df = pd.read_sql(
        "SELECT * FROM FACT_CONSUMPTION WHERE facility_key = ? AND commodity_key = ? ORDER BY date_key",
        conn, params=(int(fac_key), int(com_key))
    )
    inv_df = pd.read_sql(
        "SELECT * FROM FACT_INVENTORY WHERE facility_key = ? AND commodity_key = ? ORDER BY date_key",
        conn, params=(int(fac_key), int(com_key))
    )
    if close_conn:
        conn.close()

    if len(cons_df) < MIN_TRAIN_DAYS or len(inv_df) < MIN_TRAIN_DAYS:
        return None

    return build_demand_features(fac_key, com_key, inv_df, cons_df)


def build_demand_features(fac_key, com_key, inv_df, cons_df, max_lag=30):
    cons_pair = cons_df[(cons_df.facility_key == fac_key) & (cons_df.commodity_key == com_key)].copy()
    inv_pair = inv_df[(inv_df.facility_key == fac_key) & (inv_df.commodity_key == com_key)].copy()

    if len(cons_pair) < MIN_TRAIN_DAYS:
        return None

    cons_pair = add_calendar_features(cons_pair)
    cons_pair = add_lag_features(cons_pair, "quantity_consumed", lags=[1,2,3,7,14,30])
    cons_pair = add_rolling_features(cons_pair, "quantity_consumed", windows=[7,14,30,60])
    cons_pair = add_trend_features(cons_pair, "quantity_consumed", windows=[7,30])

    inv_pair = add_calendar_features(inv_pair, "date_key")
    inv_pair = add_inventory_features(inv_pair, cons_pair)

    merged = cons_pair.merge(
        inv_pair[["date_key", "closing_stock", "dofs", "stockout_flag", "critical_flag",
                  "overstock_flag", "quantity_received", "quantity_issued",
                  "expected_daily_demand"]],
        on="date_key", how="left"
    )

    merged["facility_key"] = fac_key
    merged["commodity_key"] = com_key
    merged["target_next_day"] = merged["quantity_consumed"].shift(-1)
    merged["stockout_next_7"] = merged["stockout_flag"].rolling(7, min_periods=1).max().shift(-7)

    return merged.dropna(subset=["target_next_day"])


def build_training_dataset(pairs_df, inv_df=None, cons_df=None, sample_pairs=2000, conn=None):
    all_features = []
    close_conn = False
    if inv_df is None or cons_df is None:
        from analytics_module.data.loader import get_connection
        if conn is None:
            conn = get_connection()
            close_conn = True

    for _, row in pairs_df.head(sample_pairs).iterrows():
        fac_key = int(row.facility_key)
        com_key = int(row.commodity_key)
        if inv_df is not None and cons_df is not None:
            feats = build_demand_features(fac_key, com_key, inv_df, cons_df)
        else:
            feats = load_pair_features_from_db(fac_key, com_key, conn=conn)

        if feats is not None and len(feats) > 100:
            all_features.append(feats)

    if close_conn and conn:
        conn.close()

    if not all_features:
        return pd.DataFrame()
    return pd.concat(all_features, ignore_index=True)