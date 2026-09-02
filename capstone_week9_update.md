# Capstone Week 9 Update

## ML Algorithm Choice

**LightGBM (Gradient Boosting Decision Trees)** was selected as the primary algorithm for both demand forecasting and stockout risk classification.

**Why LightGBM?**
- Handles tabular time-series data efficiently with native categorical support
- Fast training with GPU/histogram-based optimization—critical for per-facility-commodity pair models (100s of models)
- Built-in handling of missing values and automatic feature selection via `feature_fraction`/`bagging_fraction`
- `scale_pos_weight` parameter provides native class imbalance handling for the stockout risk task
- Proven strong performance on structured/tabular data in supply-chain forecasting benchmarks

*Secondary models*: RandomForest (with `class_weight="balanced"`) used for supplier delay prediction and expiry risk classification—simpler, robust baselines for smaller datasets.

---

## Class Imbalance Handling

**Yes, class imbalance was present and explicitly addressed:**

1. **Stockout Risk Model** (`analytics_module/models/risk_modelling.py:49`):
   - Used LightGBM's `scale_pos_weight = n_negative / n_positive` 
   - Automatically weights the minority (stockout) class during training
   - Optimal threshold selection via F1 maximization on validation set (`find_optimal_threshold`)

2. **Supplier Delay & Expiry Models** (`analytics_module/models/predictive.py:72,85`):
   - RandomForest with `class_weight="balanced"` 
   - Inversely proportional to class frequencies

3. **Evaluation**: AUC-ROC and Precision/Recall/F1 reported (not accuracy) to properly assess minority-class performance.

---

## Surprising Feature Importance Insight

**Inventory-level features (`days_of_stock`, `closing_stock`, `expected_daily_demand`) ranked higher than consumption lag features for stockout risk prediction.**

Initially expected recent consumption lags (`quantity_consumed_lag1`, `lag7`, `lag14`) to dominate since they capture demand trends. However, the model learned that *current inventory position relative to demand rate* (days of stock) is a stronger immediate signal of impending stockout than historical consumption patterns alone. This aligns with operational reality: a facility with 2 days of stock is at high risk regardless of whether last week's consumption was high or low.