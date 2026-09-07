"""Main analytics pipeline: EDA, forecasting, risk modelling, predictive analytics."""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

from analytics_module.config import OUTPUT_DIR, FIG_DIR, MAX_SAMPLE_PAIRS
from analytics_module.data.loader import (load_table, load_dims, load_kpis, load_facts,
                                           load_all, sample_pairs)
from analytics_module.features.engineering import build_training_dataset
from analytics_module.models.forecasting import train_demand_model, evaluate_forecast, train_per_pair
from analytics_module.models.risk_modelling import train_risk_model, evaluate_risk_model, train_risk_per_pair
from analytics_module.models.predictive import (predict_expiry_risk, optimize_redistribution,
                                                 build_redistribution_optimizer, train_supplier_delay_model)
from analytics_module.models.imbalance import (detect_imbalances, find_matching_pairs,
                                                 optimize_allocation, generate_allocation_plan,
                                                 save_allocation_plan)
from analytics_module.visualization.plots import (plot_demand_distribution, plot_stockout_patterns,
                                                   plot_overstock_analysis, plot_supplier_performance,
                                                   plot_expiry_waste, plot_redistribution_chains,
                                                   plot_feature_importance, set_style,
                                                   plot_inventory_imbalance, plot_allocation_plan)
import warnings
warnings.filterwarnings("ignore")


def run_eda():
    print("=" * 60)
    print("EXPLORATORY DATA ANALYSIS")
    print("=" * 60)

    kpis = load_kpis()
    dims = load_dims()

    print("\n1. Demand Distribution")
    plot_demand_distribution()
    print("  Saved: demand_distribution.png")

    print("\n2. Stockout Patterns")
    plot_stockout_patterns(kpis["KPI_STOCKOUT"])
    print("  Saved: stockout_patterns.png")

    print("\n3. Overstock Analysis")
    plot_overstock_analysis(kpis["KPI_OVERSTOCK"])
    print("  Saved: overstock_analysis.png")

    print("\n4. Supplier Performance")
    plot_supplier_performance(kpis["KPI_SUPPLIER"])
    print("  Saved: supplier_performance.png")

    print("\n5. Expiry Waste")
    plot_expiry_waste(kpis["KPI_EXPIRY"])
    print("  Saved: expiry_waste.png")

    print("\n6. Redistribution Chains")
    plot_redistribution_chains(kpis["KPI_REDISTRIBUTION_CHAINS"])
    print("  Saved: redistribution_chains.png")

    print("\n7. Summary Statistics")
    # Use SQL for counts to avoid loading large tables
    import sqlite3
    conn = sqlite3.connect("analytics/analytics.db")
    counts = {}
    for table in ["FACT_INVENTORY", "FACT_CONSUMPTION", "FACT_ORDERS", "FACT_SHIPMENTS", "FACT_BATCHES", "FACT_REDISTRIBUTION"]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()

    print(f"  Total facilities: {len(dims['DIM_FACILITY'])}")
    print(f"  Total commodities: {len(dims['DIM_COMMODITY'])}")
    print(f"  Inventory records: {counts['FACT_INVENTORY']:,}")
    print(f"  Consumption records: {counts['FACT_CONSUMPTION']:,}")
    print(f"  Orders: {counts['FACT_ORDERS']:,}")
    print(f"  Shipments: {counts['FACT_SHIPMENTS']:,}")
    print(f"  Batches: {counts['FACT_BATCHES']:,}")
    print(f"  Redistribution events: {counts['FACT_REDISTRIBUTION']:,}")

    # Stockout/overstock rates from KPI tables
    stockout_rate = (kpis['KPI_STOCKOUT']['stockout_days'] > 0).mean() if 'stockout_days' in kpis['KPI_STOCKOUT'].columns else 0
    print(f"  Overall stockout rate (facility-months): {stockout_rate:.2%}")

    return {"eda_complete": True}


def run_demand_forecasting(n_pairs=100):
    print("\n" + "=" * 60)
    print("DEMAND FORECASTING")
    print("=" * 60)

    pairs = sample_pairs(min(MAX_SAMPLE_PAIRS, 500))

    print(f"Building training data for {len(pairs)} pairs...")
    from analytics_module.features.engineering import build_training_dataset
    train_data = build_training_dataset(pairs, sample_pairs=min(n_pairs, 50))

    if len(train_data) == 0:
        print("  No training data available")
        return {}

    print(f"Training data shape: {train_data.shape}")

    from analytics_module.models.forecasting import prepare_features, train_demand_model, evaluate_forecast
    X, y, feat_cols = prepare_features(train_data)

    # Temporal train/test split across dates
    if "date" in train_data.columns:
        dates = train_data["date"].sort_values().unique()
        split_date = dates[int(len(dates) * 0.8)]
        train_mask = train_data["date"] < split_date
        test_mask = train_data["date"] >= split_date
    elif "date_key" in train_data.columns:
        dates = train_data["date_key"].sort_values().unique()
        split_date = dates[int(len(dates) * 0.8)]
        train_mask = train_data["date_key"] < split_date
        test_mask = train_data["date_key"] >= split_date
    else:
        split = int(len(train_data) * 0.8)
        train_mask = train_data.index < split
        test_mask = train_data.index >= split

    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]

    print("Training LightGBM demand model...")
    model = train_demand_model(X_train, y_train, X_test, y_test)
    metrics = evaluate_forecast(model, X_test, y_test)

    print(f"  LightGBM MAE: {metrics['mae']:.2f}")
    print(f"  Baseline MAE: {metrics['baseline_mae']:.2f}")
    print(f"  MAE Improvement: {metrics['mae_improvement_pct']:.1f}%")
    print(f"  RMSE: {metrics['rmse']:.2f}")
    print(f"  MAPE: {metrics['mape']:.2%}")

    from analytics_module.visualization.plots import plot_feature_importance
    plot_feature_importance(model, feat_cols, title="Demand Forecast Feature Importance")

    return {"model": model, "metrics": metrics, "features": feat_cols}


def run_stockout_risk(n_pairs=100):
    print("\n" + "=" * 60)
    print("STOCKOUT RISK MODELLING")
    print("=" * 60)

    pairs = sample_pairs(min(MAX_SAMPLE_PAIRS, 500))

    from analytics_module.features.engineering import build_training_dataset
    train_data = build_training_dataset(pairs, sample_pairs=min(n_pairs, 50))

    if len(train_data) == 0:
        print("  No training data")
        return {}

    from analytics_module.models.risk_modelling import (prepare_risk_features,
                                                         train_risk_model, evaluate_risk_model,
                                                         find_optimal_threshold)
    X, y, feat_cols = prepare_risk_features(train_data, horizon=7)

    # Temporal train/test split across dates
    if "date" in train_data.columns:
        dates = train_data["date"].sort_values().unique()
        split_date = dates[int(len(dates) * 0.8)]
        train_mask = train_data["date"] < split_date
        test_mask = train_data["date"] >= split_date
    elif "date_key" in train_data.columns:
        dates = train_data["date_key"].sort_values().unique()
        split_date = dates[int(len(dates) * 0.8)]
        train_mask = train_data["date_key"] < split_date
        test_mask = train_data["date_key"] >= split_date
    else:
        split = int(len(train_data) * 0.8)
        train_mask = train_data.index < split
        test_mask = train_data.index >= split

    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]

    print("Training LightGBM stockout risk model...")
    model = train_risk_model(X_train, y_train, X_test, y_test)
    threshold, _ = find_optimal_threshold(model, X_test, y_test)
    metrics = evaluate_risk_model(model, X_test, y_test, threshold)

    print(f"  AUC: {metrics['auc']:.3f}")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall: {metrics['recall']:.3f}")
    print(f"  F1: {metrics['f1']:.3f}")
    print(f"  Optimal threshold: {threshold:.2f}")

    from analytics_module.visualization.plots import plot_feature_importance
    plot_feature_importance(model, feat_cols, title="Stockout Risk Feature Importance")

    return {"model": model, "metrics": metrics, "threshold": threshold, "features": feat_cols}


def run_predictive_analytics():
    print("\n" + "=" * 60)
    print("PREDICTIVE ANALYTICS")
    print("=" * 60)

    facts = load_facts()
    dims = load_dims()

    print("\n1. Expiry Risk Analysis")
    expiry_risk = predict_expiry_risk(facts["FACT_BATCHES"])
    high_risk = expiry_risk[expiry_risk["expiry_risk"] == 1]
    print(f"  Batches at risk (within 90 days): {len(high_risk)}")
    print(f"  Total units at risk: {high_risk['remaining_quantity'].sum():,.0f}")
    print(f"  Top 5 at-risk batches:")
    for _, r in high_risk.head(5).iterrows():
        print(f"    {r['batch_id']}: {r['remaining_quantity']:.0f} units, {r['days_to_expiry']} days to expiry")

    print("\n2. Redistribution Optimization")
    optimized = optimize_redistribution(facts["FACT_REDISTRIBUTION"], facts["FACT_INVENTORY"])
    print(f"  Recommended redistributions: {len(optimized)}")
    print(f"  Total recommended units: {optimized['recommended_quantity'].sum():,.0f}")
    print(f"  Total transport cost: {optimized['transport_cost'].sum():,.0f} KES")
    print(f"  Avg cost per unit: {optimized['cost_per_unit'].mean():.2f} KES")
    top = optimized.nlargest(5, "value_density")
    print("  Top 5 by value density:")
    for _, r in top.iterrows():
        print(f"    {r['redistribution_id']}: {r['recommended_quantity']:.0f} units, {r['distance_km']:.1f} km, {r['cost_per_unit']:.2f} KES/unit")

    print("\n3. Redistribution Priority Scoring")
    priority = build_redistribution_optimizer(facts["FACT_REDISTRIBUTION"],
                                               facts["FACT_INVENTORY"],
                                               load_table("DIM_FACILITY"),
                                               load_table("DIM_COMMODITY"))
    print(f"  Scored {len(priority)} recommended events")
    top5 = priority.head(5)
    for _, r in top5.iterrows():
        print(f"    {r['redistribution_id']}: ROI={r['roi']:.2f}, priority={r['priority_score']:.1f}")

    print("\n4. Supplier Delay Prediction")
    try:
        delay_model, delay_features = train_supplier_delay_model(load_table("FACT_ORDERS"), load_table("DIM_SUPPLIER"))
        print(f"  Trained delay prediction model with features: {delay_features}")
        print(f"  Feature importances: {dict(zip(delay_features, delay_model.feature_importances_))}")
    except Exception as e:
        print(f"  Could not train supplier delay model: {e}")

    return {"expiry_risk": len(high_risk), "optimized_redistribution": len(optimized)}


def run_inventory_imbalance():
    print("\n" + "=" * 60)
    print("INVENTORY IMBALANCE DETECTION & ALLOCATION OPTIMIZATION")
    print("=" * 60)

    dims = load_dims()
    facility_df = dims["DIM_FACILITY"]
    commodity_df = dims["DIM_COMMODITY"]

    print("\n1. Detecting Inventory Imbalances...")
    imbalances = detect_imbalances(
        inventory_df=None,  # Use optimized SQL query
        commodity_df=commodity_df,
        facility_df=facility_df,
        threshold_dofs=7
    )

    overstocked = imbalances["overstocked"]
    understocked = imbalances["understocked"]
    summary = imbalances["summary"]

    print(f"  Overstocked pairs: {summary['total_overstocked_pairs']}")
    print(f"  Understocked pairs: {summary['total_understocked_pairs']}")
    print(f"  Total excess units: {summary['total_excess_units']:,.0f}")
    print(f"  Total deficit units: {summary['total_deficit_units']:,.0f}")
    print(f"  Total excess value: {summary['total_excess_value']:,.0f} KES")
    print(f"  Total deficit value: {summary['total_deficit_value']:,.0f} KES")

    print("\n  Top 5 Overstocked:")
    for _, r in overstocked.head(5).iterrows():
        print(f"    {r['facility_id']} - {r['commodity_id']}: {r['excess_units']:,.0f} excess units, {r['excess_value']:,.0f} KES")

    print("\n  Top 5 Understocked:")
    for _, r in understocked.head(5).iterrows():
        print(f"    {r['facility_id']} - {r['commodity_id']}: {r['deficit_units']:,.0f} deficit units, {r['deficit_value']:,.0f} KES")

    print("\n2. Finding Matching Pairs for Redistribution...")
    matches = find_matching_pairs(overstocked, understocked, facility_df, max_distance_km=400)
    print(f"  Found {len(matches)} potential matches")

    if len(matches) > 0:
        print("  Top 5 by Priority Score:")
        for _, r in matches.head(5).iterrows():
            print(f"    {r['source_facility_id']} -> {r['dest_facility_id']} ({r['commodity_id']}): "
                  f"{r['transferable_units']:,.0f} units, {r['distance_km']:.0f}km, "
                  f"ROI={r['roi']:.2f}, Priority={r['priority_score']:.1f}")

    print("\n3. Optimizing Allocation Plan...")
    allocation_plan = optimize_allocation(matches, budget_kes=5000000, max_distance_km=300)
    print(f"  Optimized recommendations: {len(allocation_plan)}")
    print(f"  Total transport cost: {allocation_plan['estimated_transport_cost'].sum():,.0f} KES")
    print(f"  Total units to transfer: {allocation_plan['transferable_units'].sum():,.0f}")

    print("\n4. Generating Detailed Allocation Plan...")
    detailed_plan = generate_allocation_plan(allocation_plan)
    recommended = detailed_plan[detailed_plan["recommendation"] == "RECOMMEND"]
    print(f"  Final recommendations: {len(recommended)}")
    print(f"  Total units: {recommended['transferable_units'].sum():,.0f}")
    print(f"  Total value: {recommended['transfer_value'].sum():,.0f} KES")

    save_allocation_plan(detailed_plan)
    print("  Allocation plan saved to models/allocation_plan/")

    print("\n5. Generating Visualizations...")
    plot_inventory_imbalance(imbalances)
    print("  Saved: inventory_imbalance.png")
    plot_allocation_plan(detailed_plan)
    print("  Saved: allocation_plan.png")

    return {
        "imbalances": imbalances,
        "matches": matches,
        "allocation_plan": allocation_plan,
        "detailed_plan": detailed_plan,
    }


def run_full_pipeline():
    print("=" * 60)
    print("HEALTHCARE SUPPLY-CHAIN INTELLIGENCE PLATFORM - ANALYTICS")
    print("=" * 60)

    results = {}
    results["eda"] = run_eda()
    results["forecasting"] = run_demand_forecasting()
    results["risk"] = run_stockout_risk()
    results["predictive"] = run_predictive_analytics()
    results["imbalance"] = run_inventory_imbalance()

    print("\n" + "=" * 60)
    print("ANALYTICS PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Figures saved to: {FIG_DIR}")
    print(f"Models saved to: analytics_module/models/")

    return results


if __name__ == "__main__":
    run_full_pipeline()