"""Inventory imbalance detection and allocation optimization."""

import numpy as np
import pandas as pd
from pathlib import Path
import pickle
import sqlite3
import warnings
warnings.filterwarnings("ignore")

from analytics_module.config import MODEL_DIR, ANALYTICS_DB


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth in km."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    return 6371.0 * c


def get_latest_inventory():
    """Load latest inventory snapshot with facility and commodity details."""
    conn = sqlite3.connect(ANALYTICS_DB)
    query = """
        SELECT i.*, f.facility_id, f.facility_name, f.county, f.facility_type,
               f.latitude, f.longitude,
               c.commodity_id, c.commodity_name, c.category, c.unit_cost
        FROM FACT_INVENTORY i
        JOIN DIM_FACILITY f ON f.facility_key = i.facility_key
        JOIN DIM_COMMODITY c ON c.commodity_key = i.commodity_key
        WHERE i.date_key = (SELECT MAX(date_key) FROM FACT_INVENTORY)
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def detect_imbalances(inventory_df=None, commodity_df=None, facility_df=None, threshold_dofs=7):
    """Detect overstocked and understocked facility-commodity pairs."""
    if inventory_df is None:
        inv = get_latest_inventory()
    else:
        inv = inventory_df.copy()
        if commodity_df is not None:
            inv = inv.merge(commodity_df[["commodity_key", "commodity_id", "commodity_name", "unit_cost", "category"]], on="commodity_key", how="left")
        if facility_df is not None:
            fac_cols = [c for c in ["facility_key", "facility_id", "facility_name", "county", "facility_type", "latitude", "longitude"] if c in facility_df.columns]
            inv = inv.merge(facility_df[fac_cols], on="facility_key", how="left")
    
    inv["days_of_stock"] = np.where(
        inv["expected_daily_demand"] > 0,
        inv["closing_stock"] / inv["expected_daily_demand"],
        0
    )
    
    inv["stock_status"] = inv["stock_status"].fillna("NORMAL")
    inv["is_overstocked"] = (inv["stock_status"] == "OVERSTOCKED").astype(int)
    inv["is_understocked"] = inv["stock_status"].isin(["STOCKOUT", "CRITICAL"]).astype(int)
    inv["is_low"] = (inv["days_of_stock"] < threshold_dofs).astype(int)
    inv["is_high"] = (inv["days_of_stock"] > 60).astype(int)
    
    overstocked = inv[inv["is_overstocked"] == 1].copy()
    understocked = inv[inv["is_low"] == 1].copy()
    
    overstocked["excess_units"] = np.maximum(0.0, overstocked["closing_stock"] - (overstocked["expected_daily_demand"] * 30))
    overstocked["excess_value"] = overstocked["excess_units"] * overstocked.get("unit_cost", 0)
    overstocked = overstocked[overstocked["excess_units"] > 0].copy()
    
    understocked["deficit_units"] = np.maximum(0.0, (understocked["expected_daily_demand"] * threshold_dofs) - understocked["closing_stock"])
    understocked["deficit_value"] = understocked["deficit_units"] * understocked.get("unit_cost", 0)
    understocked = understocked[understocked["deficit_units"] > 0].copy()
    
    return {
        "overstocked": overstocked.sort_values("excess_value", ascending=False),
        "understocked": understocked.sort_values("deficit_value", ascending=False),
        "summary": {
            "total_overstocked_pairs": len(overstocked),
            "total_understocked_pairs": len(understocked),
            "total_excess_units": overstocked["excess_units"].sum(),
            "total_deficit_units": understocked["deficit_units"].sum(),
            "total_excess_value": overstocked["excess_value"].sum(),
            "total_deficit_value": understocked["deficit_value"].sum(),
        }
    }


def find_matching_pairs(overstocked_df, understocked_df, facility_df=None, max_distance_km=400):
    """Find potential redistribution matches between overstocked and understocked pairs."""
    if "facility_name" not in overstocked_df.columns and facility_df is not None:
        fac_cols = [c for c in ["facility_key", "facility_id", "facility_name", "county", "latitude", "longitude"] if c in facility_df.columns]
        overstocked_df = overstocked_df.merge(facility_df[fac_cols], on="facility_key", how="left")
        understocked_df = understocked_df.merge(facility_df[fac_cols], on="facility_key", how="left")
    
    # Rename columns to ensure proper suffixing on merge
    over_cols = {c: f"{c}_src" for c in ["excess_units", "excess_value", "deficit_units", "deficit_value"] if c in overstocked_df.columns}
    under_cols = {c: f"{c}_dst" for c in ["excess_units", "excess_value", "deficit_units", "deficit_value"] if c in understocked_df.columns}
    
    overstocked_df = overstocked_df.rename(columns=over_cols)
    understocked_df = understocked_df.rename(columns=under_cols)
    
    # Merge on commodity_key to find matching commodity pairs
    merged = overstocked_df.merge(
        understocked_df,
        on="commodity_key",
        suffixes=("_src", "_dst")
    )
    
    # Filter out same facility
    merged = merged[merged["facility_key_src"] != merged["facility_key_dst"]]
    
    # Calculate distance using real geodesic Haversine formula if coordinates available
    if "latitude_src" in merged.columns and "latitude_dst" in merged.columns and merged["latitude_src"].notna().any():
        merged["distance_km"] = haversine_distance_km(
            merged["latitude_src"].astype(float),
            merged["longitude_src"].astype(float),
            merged["latitude_dst"].astype(float),
            merged["longitude_dst"].astype(float)
        ).round(1)
        merged["distance_km"] = merged["distance_km"].clip(lower=10.0)
    else:
        # Fallback to county heuristic
        merged["distance_km"] = np.where(
            merged["county_src"] == merged["county_dst"],
            50.0,
            200.0
        )
    
    # Filter by max distance
    merged = merged[merged["distance_km"] <= max_distance_km]
    
    # Calculate transferable units
    merged["transferable_units"] = np.minimum(merged["excess_units_src"], merged["deficit_units_dst"])
    merged = merged[merged["transferable_units"] > 0]
    
    if len(merged) == 0:
        return pd.DataFrame()
    
    # Build matches dataframe
    matches_df = pd.DataFrame({
        "source_facility_id": merged["facility_id_src"],
        "source_facility_name": merged["facility_name_src"],
        "source_county": merged["county_src"],
        "dest_facility_id": merged["facility_id_dst"],
        "dest_facility_name": merged["facility_name_dst"],
        "dest_county": merged["county_dst"],
        "commodity_key": merged["commodity_key"],
        "commodity_id": merged["commodity_id_src"],
        "commodity_name": merged["commodity_name_src"],
        "category": merged["category_src"],
        "distance_km": merged["distance_km"],
        "available_excess": merged["excess_units_src"],
        "required_deficit": merged["deficit_units_dst"],
        "transferable_units": merged["transferable_units"],
        "unit_cost": merged["unit_cost_src"],
        "transfer_value": merged["transferable_units"] * merged["unit_cost_src"],
        "source_days_of_stock": merged["days_of_stock_src"],
        "dest_days_of_stock": merged["days_of_stock_dst"],
    })
    
    matches_df["cost_per_km_per_unit"] = 2.5
    matches_df["estimated_transport_cost"] = matches_df["distance_km"] * matches_df["transferable_units"] * matches_df["cost_per_km_per_unit"] / 1000
    matches_df["roi"] = matches_df["transfer_value"] / (matches_df["estimated_transport_cost"] + 1)
    matches_df["priority_score"] = matches_df["roi"] * matches_df["dest_days_of_stock"].clip(upper=30)
    matches_df = matches_df.sort_values("priority_score", ascending=False)
    
    return matches_df


def estimate_distance(source_row, dest_row, facility_df):
    """Estimate distance between facilities (simplified: same county=50km, different=200km)."""
    if "county" in source_row and "county" in dest_row:
        if source_row["county"] == dest_row["county"]:
            return 50.0
        return 200.0
    return 150.0


def optimize_allocation(matches_df, budget_kes=None, max_distance_km=None):
    """Optimize allocation recommendations based on budget and constraints."""
    optimized = matches_df.copy()
    
    if max_distance_km:
        optimized = optimized[optimized["distance_km"] <= max_distance_km]
    
    if budget_kes:
        optimized = optimized.sort_values("priority_score", ascending=False)
        optimized["cumulative_cost"] = optimized["estimated_transport_cost"].cumsum()
        optimized = optimized[optimized["cumulative_cost"] <= budget_kes]
    
    return optimized.reset_index(drop=True)


def generate_allocation_plan(matches_df, forecast_dict=None, risk_dict=None):
    """Generate detailed allocation plan with forecast and risk adjustments."""
    plan = matches_df.copy()
    
    if forecast_dict:
        plan["dest_forecast_30d"] = plan["commodity_key"].map(
            {k: sum(v.get("preds", [0])[:30]) if isinstance(v, dict) else 0 for k, v in forecast_dict.items()}
        )
        plan["adjusted_deficit"] = plan["required_deficit"] + plan["dest_forecast_30d"]
        plan["transferable_units"] = np.minimum(plan["available_excess"], plan["adjusted_deficit"])
    
    if risk_dict:
        plan["dest_risk_score"] = plan["commodity_key"].map(
            {k: v.get("probability", 0) if isinstance(v, dict) else 0 for k, v in risk_dict.items()}
        )
        plan["priority_score"] = plan["priority_score"] * (1 + plan["dest_risk_score"])
    
    plan = plan.sort_values("priority_score", ascending=False)
    
    plan["recommendation"] = np.where(
        plan["transferable_units"] > 0,
        "RECOMMEND",
        "SKIP"
    )
    
    return plan


def save_allocation_plan(plan_df, path=None):
    """Save allocation plan to CSV and pickle."""
    if path is None:
        path = MODEL_DIR / "allocation_plan"
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    
    plan_df.to_csv(path / "allocation_plan.csv", index=False)
    
    with open(path / "allocation_plan.pkl", "wb") as f:
        pickle.dump(plan_df, f)
    
    return path


def load_allocation_plan(path=None):
    """Load allocation plan from pickle."""
    if path is None:
        path = MODEL_DIR / "allocation_plan" / "allocation_plan.pkl"
    with open(path, "rb") as f:
        return pickle.load(f)