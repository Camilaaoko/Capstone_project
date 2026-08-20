"""Visualization utilities for exploratory analysis and model evaluation."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import sqlite3
from pathlib import Path

from analytics_module.config import FIG_DIR


def set_style():
    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["font.size"] = 11


def save_fig(name, dpi=150):
    path = FIG_DIR / f"{name}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close()
    return path


def plot_demand_distribution(cons_df=None, top_n=20):
    set_style()
    
    conn = sqlite3.connect("analytics/analytics.db")
    
    # Daily aggregation via SQL
    daily = pd.read_sql("""
        SELECT date_key, SUM(quantity_consumed) as total_consumed
        FROM FACT_CONSUMPTION
        GROUP BY date_key
        ORDER BY date_key
    """, conn)
    daily["date"] = pd.to_datetime(daily["date_key"].astype(str), format="%Y%m%d")
    
    # Top commodities via SQL
    top_com = pd.read_sql("""
        SELECT commodity_key, SUM(quantity_consumed) as total_consumed
        FROM FACT_CONSUMPTION
        GROUP BY commodity_key
        ORDER BY total_consumed DESC
        LIMIT ?
    """, conn, params=(top_n,))
    
    # County consumption via SQL
    county_cons = pd.read_sql("""
        SELECT f.county, SUM(fc.quantity_consumed) as total_consumed
        FROM FACT_CONSUMPTION fc
        JOIN DIM_FACILITY f ON f.facility_key = fc.facility_key
        GROUP BY f.county
        ORDER BY total_consumed DESC
    """, conn)
    
    # Sample for histogram (100k rows max)
    sample = pd.read_sql("""
        SELECT quantity_consumed FROM FACT_CONSUMPTION
        ORDER BY RANDOM() LIMIT 100000
    """, conn)
    
    conn.close()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0, 0].plot(daily["date"], daily["total_consumed"], alpha=0.7, linewidth=0.5)
    axes[0, 0].set_title("Total Daily Consumption (All Facilities)")
    axes[0, 0].set_ylabel("Units")
    axes[0, 0].tick_params(axis="x", rotation=45)

    axes[0, 1].barh(range(len(top_com)), top_com["total_consumed"])
    axes[0, 1].set_yticks(range(len(top_com)))
    axes[0, 1].set_yticklabels(top_com["commodity_key"])
    axes[0, 1].set_title(f"Top {top_n} Commodities by Total Consumption")
    axes[0, 1].set_xlabel("Total Units")

    axes[1, 0].bar(county_cons["county"], county_cons["total_consumed"])
    axes[1, 0].set_title("Total Consumption by County")
    axes[1, 0].tick_params(axis="x", rotation=45)

    sns.histplot(sample["quantity_consumed"], bins=50, ax=axes[1, 1], log_scale=(False, True))
    axes[1, 1].set_title("Distribution of Daily Consumption (log-count, sampled)")

    return save_fig("demand_distribution")


def plot_stockout_patterns(kpi_stockout, top_n=20):
    set_style()
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    top = kpi_stockout.nlargest(top_n, "stockout_days")
    axes[0, 0].barh(range(len(top)), top["stockout_days"])
    axes[0, 0].set_yticks(range(len(top)))
    axes[0, 0].set_yticklabels([f"{r.facility_name} - {r.commodity_name}" for _, r in top.iterrows()], fontsize=8)
    axes[0, 0].set_title(f"Top {top_n} Stockout Facility-Commodity Pairs")

    monthly = kpi_stockout.groupby("year_month")["stockout_days"].sum().reset_index()
    monthly["date"] = pd.to_datetime(monthly["year_month"].astype(str) + "01", format="%Y%m%d")
    axes[0, 1].plot(monthly["date"], monthly["stockout_days"], marker="o")
    axes[0, 1].set_title("Monthly Stockout Days (All Facilities)")
    axes[0, 1].tick_params(axis="x", rotation=45)

    by_county = kpi_stockout.groupby("county")["stockout_days"].sum().sort_values(ascending=False)
    axes[1, 0].bar(by_county.index, by_county.values)
    axes[1, 0].set_title("Stockout Days by County")
    axes[1, 0].tick_params(axis="x", rotation=45)

    by_cat = kpi_stockout.groupby("category")["stockout_days"].sum().sort_values(ascending=False)
    axes[1, 1].bar(by_cat.index, by_cat.values)
    axes[1, 1].set_title("Stockout Days by Commodity Category")
    axes[1, 1].tick_params(axis="x", rotation=45)

    return save_fig("stockout_patterns")


def plot_overstock_analysis(kpi_overstock):
    set_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    by_cat = kpi_overstock.groupby("category")["overstocked_days"].sum().sort_values(ascending=False)
    axes[0].bar(by_cat.index, by_cat.values)
    axes[0].set_title("Overstocked Facility-Days by Category")
    axes[0].tick_params(axis="x", rotation=45)

    axes[1].scatter(kpi_overstock["max_days_of_stock"], kpi_overstock["overstocked_days"], alpha=0.3, s=5)
    axes[1].set_xlabel("Max Days of Stock")
    axes[1].set_ylabel("Overstocked Days in Month")
    axes[1].set_title("Overstock Intensity vs Max Days of Stock")

    return save_fig("overstock_analysis")


def plot_supplier_performance(kpi_supplier):
    set_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(kpi_supplier["supplier_name"], kpi_supplier["on_time_delivery_rate"])
    axes[0].set_title("On-Time Delivery Rate by Supplier")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].set_ylabel("OTD Rate")

    axes[1].bar(kpi_supplier["supplier_name"], kpi_supplier["orders_delayed"])
    axes[1].set_title("Delayed Orders by Supplier")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].set_ylabel("Delayed Orders")

    return save_fig("supplier_performance")


def plot_expiry_waste(kpi_expiry):
    set_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    top = kpi_expiry.nlargest(15, "wastage_value_kes")
    axes[0].barh(range(len(top)), top["wastage_value_kes"])
    axes[0].set_yticks(range(len(top)))
    axes[0].set_yticklabels([f"{r.facility_name} - {r.commodity_name}" for _, r in top.iterrows()], fontsize=8)
    axes[0].set_title("Top 15 Expiry Waste by Value (KES)")

    by_cat = kpi_expiry.groupby("commodity_name")["wastage_value_kes"].sum().nlargest(15)
    axes[1].barh(range(len(by_cat)), by_cat.values)
    axes[1].set_yticks(range(len(by_cat)))
    axes[1].set_yticklabels(by_cat.index, fontsize=8)
    axes[1].set_title("Top 15 Commodities by Expiry Waste Value")

    return save_fig("expiry_waste")


def plot_redistribution_chains(kpi_chains):
    set_style()
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    top = kpi_chains.nlargest(15, "dest_stockout_days")
    axes[0, 0].barh(range(len(top)), top["dest_stockout_days"])
    axes[0, 0].set_yticks(range(len(top)))
    axes[0, 0].set_yticklabels([f"{r.commodity_name}: {r.source_facility_name} -> {r.destination_facility_name}" for _, r in top.iterrows()], fontsize=7)
    axes[0, 0].set_title("Chains by Destination Stockout Days")

    axes[0, 1].barh(range(len(top)), top["total_recommended_units"])
    axes[0, 1].set_yticks(range(len(top)))
    axes[0, 1].set_yticklabels([f"{r.commodity_name}: {r.source_facility_name} -> {r.destination_facility_name}" for _, r in top.iterrows()], fontsize=7)
    axes[0, 1].set_title("Total Recommended Units per Chain")

    axes[1, 0].scatter(kpi_chains["avg_distance_km"], kpi_chains["total_transport_cost"], alpha=0.6)
    axes[1, 0].set_xlabel("Avg Distance (km)")
    axes[1, 0].set_ylabel("Total Transport Cost (KES)")
    axes[1, 0].set_title("Distance vs Transport Cost")

    axes[1, 1].scatter(kpi_chains["avg_source_dofs"], kpi_chains["avg_dest_dofs"], alpha=0.6)
    axes[1, 1].set_xlabel("Source Avg Days of Stock")
    axes[1, 1].set_ylabel("Dest Avg Days of Stock")
    axes[1, 1].set_title("Source vs Destination Stock Levels")

    return save_fig("redistribution_chains")


def plot_forecast_vs_actual(y_true, y_pred, title="Forecast vs Actual", max_points=500):
    set_style()
    n = min(len(y_true), max_points)
    idx = np.random.choice(len(y_true), n, replace=False)
    plt.figure(figsize=(10, 5))
    plt.scatter(y_true[idx], y_pred[idx], alpha=0.5, s=10)
    lim = max(y_true.max(), y_pred.max())
    plt.plot([0, lim], [0, lim], "r--", alpha=0.5)
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.title(title)
    return save_fig("forecast_vs_actual".replace(" ", "_"))


def plot_feature_importance(model, feature_cols, top_n=20, title="Feature Importance"):
    set_style()
    imp = pd.DataFrame({"feature": feature_cols, "importance": model.feature_importance()})
    imp = imp.nlargest(top_n, "importance")
    plt.figure(figsize=(8, 8))
    plt.barh(range(len(imp)), imp["importance"])
    plt.yticks(range(len(imp)), imp["feature"])
    plt.xlabel("Importance (split count)")
    plt.title(title)
    return save_fig("feature_importance".replace(" ", "_"))


def plot_model_comparison(metrics_df, metric="mae"):
    set_style()
    plt.figure(figsize=(10, 5))
    metrics_df.sort_values(metric).plot(kind="barh", y=metric, x="model", ax=plt.gca())
    plt.title(f"Model Comparison: {metric.upper()}")
    return save_fig(f"model_comparison_{metric}")


def plot_inventory_imbalance(imbalances, top_n=20):
    """Plot inventory imbalance analysis results."""
    set_style()
    overstocked = imbalances["overstocked"]
    understocked = imbalances["understocked"]
    summary = imbalances["summary"]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Top overstocked by excess value
    top_over = overstocked.nlargest(top_n, "excess_value")
    labels = [f"{r.facility_id}-{r.commodity_id}" for _, r in top_over.iterrows()]
    axes[0, 0].barh(range(len(top_over)), top_over["excess_value"])
    axes[0, 0].set_yticks(range(len(top_over)))
    axes[0, 0].set_yticklabels(labels, fontsize=8)
    axes[0, 0].set_title(f"Top {top_n} Overstocked Pairs by Excess Value (KES)")
    axes[0, 0].set_xlabel("Excess Value (KES)")
    
    # Top understocked by deficit value
    top_under = understocked.nlargest(top_n, "deficit_value")
    labels = [f"{r.facility_id}-{r.commodity_id}" for _, r in top_under.iterrows()]
    axes[0, 1].barh(range(len(top_under)), top_under["deficit_value"])
    axes[0, 1].set_yticks(range(len(top_under)))
    axes[0, 1].set_yticklabels(labels, fontsize=8)
    axes[0, 1].set_title(f"Top {top_n} Understocked Pairs by Deficit Value (KES)")
    axes[0, 1].set_xlabel("Deficit Value (KES)")
    
    # Overstocked by county
    if "county" in overstocked.columns:
        by_county = overstocked.groupby("county")["excess_value"].sum().sort_values(ascending=False)
        axes[1, 0].bar(by_county.index, by_county.values)
        axes[1, 0].set_title("Excess Value by County")
        axes[1, 0].tick_params(axis="x", rotation=45)
    
    # Understocked by county
    if "county" in understocked.columns:
        by_county = understocked.groupby("county")["deficit_value"].sum().sort_values(ascending=False)
        axes[1, 1].bar(by_county.index, by_county.values)
        axes[1, 1].set_title("Deficit Value by County")
        axes[1, 1].tick_params(axis="x", rotation=45)
    
    return save_fig("inventory_imbalance")


def plot_allocation_plan(allocation_plan, top_n=20):
    """Plot allocation plan recommendations."""
    set_style()
    recommended = allocation_plan[allocation_plan["recommendation"] == "RECOMMEND"]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Top recommendations by priority
    top_rec = recommended.nlargest(top_n, "priority_score")
    labels = [f"{r.source_facility_id}->{r.dest_facility_id} ({r.commodity_id})" for _, r in top_rec.iterrows()]
    axes[0, 0].barh(range(len(top_rec)), top_rec["priority_score"])
    axes[0, 0].set_yticks(range(len(top_rec)))
    axes[0, 0].set_yticklabels(labels, fontsize=7)
    axes[0, 0].set_title(f"Top {top_n} Allocation Recommendations by Priority")
    axes[0, 0].set_xlabel("Priority Score")
    
    # Distance vs Transfer Units
    axes[0, 1].scatter(recommended["distance_km"], recommended["transferable_units"], alpha=0.5, s=10)
    axes[0, 1].set_xlabel("Distance (km)")
    axes[0, 1].set_ylabel("Transferable Units")
    axes[0, 1].set_title("Distance vs Transfer Volume")
    
    # ROI distribution
    axes[1, 0].hist(recommended["roi"], bins=30, edgecolor="black", alpha=0.7)
    axes[1, 0].set_xlabel("ROI")
    axes[1, 0].set_ylabel("Count")
    axes[1, 0].set_title("ROI Distribution of Recommendations")
    
    # By commodity category
    if "category" in recommended.columns:
        by_cat = recommended.groupby("category")["transferable_units"].sum().sort_values(ascending=False)
        axes[1, 1].barh(by_cat.index, by_cat.values)
        axes[1, 1].set_title("Transfer Units by Commodity Category")
        axes[1, 1].set_xlabel("Units")
    
    return save_fig("allocation_plan")