# Healthcare Supply-Chain Intelligence Platform for KEMSA

An end-to-end, AI-powered healthcare supply-chain intelligence and redistribution platform designed for Kenya's public health logistics network (KEMSA). The platform combines synthetic big-data generation across **all 47 Kenyan counties**, an automated Star-Schema ETL pipeline with query acceleration, predictive machine learning (demand forecasting, stockout risk classification, FEFO expiry tracking), an inventory imbalance optimization engine, and an interactive Dash web application.

> [!IMPORTANT]
> **SYNTHETIC DATA DISCLAIMER**  
> All data produced by this generator is **synthetic** — created from statistical models with a fixed random seed (`RANDOM_SEED = 42`). It is **not** real KEMSA operational data, does not contain real patient records, and must not be presented as confidential government data. Facilities, coordinates, commodity specs, and prices are designed for academic research, system benchmarking, and demonstration purposes.

---

## 1. System Architecture & Directory Structure

```
Capstone_project/
├── generate_data.py             # 47-County Synthetic Big-Data Generator
├── etl_pipeline.py              # Extract-Transform-Load Pipeline (Star Schema & SQLite DB)
├── run_analytics_main.py        # CLI Entrypoint for ML Modeling & Allocation Engine
├── app_main.py                  # CLI Entrypoint for Interactive Dash Web Application
├── pyproject.toml               # Python Package Build & Pytest Configuration
├── requirements.txt             # Python Dependencies
├── .github/workflows/ci.yml     # GitHub Actions Continuous Integration Pipeline
│
├── output/                      # Raw Synthetic CSV Outputs (13 Relational Tables)
│   ├── FACILITIES.csv           # 235 facilities across all 47 Kenyan counties
│   ├── COMMODITIES.csv          # 45 essential healthcare commodities
│   ├── INVENTORY.csv            # ~4.9M–7.7M daily inventory balance records
│   ├── CONSUMPTION.csv          # ~4.9M–7.7M daily patient consumption records
│   ├── ORDERS.csv, SHIPMENTS.csv, BATCHES.csv, REDISTRIBUTION_EVENTS.csv ...
│
├── analytics/                   # Analytics-Ready Data Warehouse
│   ├── analytics.db             # Indexed SQLite Database (~1 GB)
│   ├── DIM_FACILITY.csv, DIM_COMMODITY.csv, DIM_DATE.csv, DIM_SUPPLIER.csv ...
│   ├── FACT_INVENTORY, FACT_CONSUMPTION, FACT_ORDERS, FACT_BATCHES ...
│   └── KPI_STOCKOUT, KPI_EXPIRY, KPI_REDISTRIBUTION_CHAINS, KPI_BASELINE_VS_INTELLIGENT ...
│
├── analytics_module/            # Machine Learning & Optimization Engine
│   ├── config.py                # Analytics Paths, Seeds, and Horizons
│   ├── data/loader.py           # SQL Data Extractors & Stratified Sampling
│   ├── features/engineering.py  # Lag, Rolling, Trend, and Calendar Feature Transforms
│   ├── models/
│   │   ├── forecasting.py       # LightGBM Demand Forecasting with Naive Baselines
│   │   ├── risk_modelling.py    # Random Forest Stockout & Supply Risk Classifiers
│   │   ├── predictive.py        # Expiry Risk Scoring & Supplier Delay Predictors
│   │   └── imbalance.py         # Haversine Geodesic Matching & Budget-Constrained Allocation
│   ├── reports/figures/         # Generated Publication-Ready Visualization Figures
│   └── visualization/plots.py   # Seaborn/Matplotlib Chart Generators
│
├── dashboard/                   # Interactive Plotly Dash Web Application
│   ├── app.py                   # Dash Application Factory & Tab Layout
│   ├── data_service.py          # Parameterized SQL Query Layer with SQLite Indexing
│   ├── components/              # Navbar, Filter Bar, and Reusable UI Widgets
│   ├── callbacks/               # Reactive Callbacks & CSV Manifest Downloader
│   └── views/
│       ├── executive_view.py    # KEMSA Executive Summary & Financial KPIs
│       ├── county_view.py       # Nationwide Mapbox Tile Map & County Comparisons
│       ├── facility_view.py     # Facility Inventory Balances & FEFO Expiry Timeline
│       └── redistribution_view.py # AI Transfer Matrix & Manifest Export
│
└── tests/                       # Automated Test Suite (20 Pytest Test Cases)
    ├── test_etl.py              # Schema Integrity, Invariants & Non-Negativity Tests
    ├── test_data_service.py     # SQL Parameterization & Data Access Tests
    ├── test_imbalance.py        # Haversine Geodesic Distance & Allocation Tests
    └── test_models.py           # Feature Pipeline, LightGBM & Expiry Risk Tests
```

---

## 2. End-to-End Workflow & Quick Start

### Installation
```bash
# 1. Clone repository and install dependencies
git clone https://github.com/Camilaaoko/Capstone_project.git
cd Capstone_project
pip install -r requirements.txt
pip install -e .
```

### Execution Pipeline

```bash
# Step 1: Generate synthetic raw data across all 47 counties
python generate_data.py

# Step 2: Run the ETL pipeline (cleans data, builds star schema, creates indexes)
python etl_pipeline.py

# Step 3: Run the automated test suite
pytest tests/ -v

# Step 4: Train ML models, run allocation engine, and generate figures
python run_analytics_main.py

# Step 5: Launch the interactive Dash web dashboard (http://127.0.0.1:8050)
python app_main.py
```

---

## 3. Nationwide 47-County Synthetic Data Generator

The generator (`generate_data.py`) produces a deterministic, relational supply-chain dataset spanning 24 months (731 days from `2024-01-01` to `2025-12-31`):

* **All 47 Kenyan Counties**: Every county is configured with its geographic centroid `(latitude, longitude)`, regional disease burden multipliers, and official sub-county divisions.
* **Tiered Facility Generation**: Interleaved round-robin distribution ensuring every county has:
  * 1 Level 5 County Referral Hospital
  * 1–3 Level 4 Sub-County Hospitals
  * 1–4 Level 3 Health Centres
  * 1–4 Level 2 Dispensaries
  * 1 Level 6 National Referral Hospital in Nairobi
* **45 Essential Healthcare Commodities**: Spanning 10 therapeutic categories (*Antibiotics, Analgesics, Antimalarials, IV Fluids, Maternal Health, Pediatric Medicines, Diabetes, Hypertension, Vaccines, Emergency*).
* **Realistic Dynamics**: Seasonality waves, disease outbreaks (Cholera, Malaria), deworming campaigns, supplier delivery delays, transport strikes, and FEFO inventory depletion.

```bash
# Custom generation options
python generate_data.py --facilities 235 --commodities 45 --months 24
python generate_data.py --facilities 470 --output-dir output_expanded
```

---

## 4. Analytics ETL Pipeline & Database Optimization

The ETL pipeline (`etl_pipeline.py`) transforms raw CSV files into an analytics-ready warehouse:

1. **Data Cleaning & Auditing**:
   * Imputes missing sub-counties from county metadata.
   * Standardizes commodity category case and whitespace formatting.
   * Eliminates duplicate consumption records and imputes missing consumption values using $PatientDemandIndex \times \text{Facility-Commodity Median}$.
   * Enforces non-negativity ($\ge 0$) on all stock and consumption series.
   * Reconciles inventory balance conservation: $\text{Closing} = \text{Opening} + \text{Received} - \text{Issued} \pm \text{Adjusted}$.
   * Logs every cleaning event into `DQ_CLEANING_LOG` for complete auditability.

2. **Star Schema Architecture**:
   * **Dimensions**: `DIM_FACILITY`, `DIM_COMMODITY`, `DIM_DATE`, `DIM_SUPPLIER`, `DIM_WAREHOUSE`.
   * **Facts**: `FACT_INVENTORY`, `FACT_CONSUMPTION`, `FACT_ORDERS`, `FACT_SHIPMENTS`, `FACT_BATCHES`, `FACT_REDISTRIBUTION`.
   * **KPIs & Aggregates**: `KPI_STOCKOUT`, `KPI_OVERSTOCK`, `KPI_EXPIRY`, `KPI_SUPPLIER`, `KPI_REDISTRIBUTION_CHAINS`, `KPI_BASELINE_VS_INTELLIGENT`.

3. **Query Acceleration (17 B-Tree Indexes)**:
   SQLite indexes on `(facility_key, commodity_key)`, `date_key`, `facility_id`, `county`, and `category` deliver a **10x–50x speedup** on dashboard queries.

---

## 5. Machine Learning & Predictive Analytics Engine

Implemented in `analytics_module/` and executed via `run_analytics_main.py`:

* **Feature Engineering**: Automated generation of calendar attributes (day of week, month, quarter, holidays), multi-period consumption lags ($t-1, t-2, t-3, t-7, t-14, t-30$), rolling statistics (mean, std, min, max over 7, 14, 30, 60 days), linear trend slopes, and days-of-stock ratios.
* **LightGBM Demand Forecasting**:
  * Temporal chronological 80/20 train/test splitting.
  * Multi-step autoregressive demand predictions over a 30-day forecast horizon.
  * Benchmark evaluation comparing LightGBM against baseline heuristics (Lag-1 Naive and 7-day Moving Average), reporting % MAE improvement.
* **FEFO Expiry Risk Modeling**: Dynamic expiry risk scoring calculating remaining shelf-life percentage and financial value at risk based on batch manufacturing and expiry dates.
* **Inventory Imbalance & Geodesic Optimization**:
  * Vectorized **Haversine Distance Formula** ($d = 2R \arcsin \sqrt{\dots}$) calculating real road/geodesic distances between facilities.
  * Multi-criteria matching engine prioritizing pairs by urgency (days of stock deficit), commodity criticality, distance, and logistics ROI.
  * Budget-constrained Knapsack optimization allocating transfers within transport cost ceilings.

---

## 6. Interactive Web Dashboard (Plotly Dash)

Launched via `python app_main.py`, providing four role-tailored operational views:

1. **Executive Overview (KEMSA Headquarters)**: National KPI summary cards (Stockout Days, Units Short, Expiry Wastage KES, Intelligent Redistribution Savings KES, Supplier On-Time Delivery Rate) and high-level category breakdowns.
2. **County & Geographic Intelligence (County Health Directors)**:
   * Interactive **Mapbox OpenStreetMap Tile Map** of Kenya (`zoom=5.5`) visualizing all facilities colored by stockout severity and sized by daily patient volume.
   * County stockout comparison bar chart with angled labels and top impacted county ranking tables.
3. **Facility & Inventory Operations (Sub-County Pharmacists)**: Facility-level inventory status, days of stock vs. safety buffer thresholds, and batch expiry chronological tracking.
4. **AI Redistribution & Allocation Engine (Logistics Planners)**: Recommended surplus-to-deficit transfer matrix, transport costs vs. emergency procurement savings comparison, and an **Export Manifest (CSV)** button for dispatch scheduling.

---

## 7. Automated Testing Suite & CI/CD

The platform includes 20 comprehensive unit and integration tests executed with `pytest`:

```bash
# Run test suite
pytest tests/ -v
```

### Test Coverage Summary:
* `tests/test_etl.py`: Database table existence, 17 SQLite indexes, inventory conservation arithmetic ($closing = opening + received - issued \pm adjusted$), non-negativity constraints, and foreign key referential integrity.
* `tests/test_data_service.py`: Parameterized SQL queries, filter options, KPI aggregations, facility coordinate lookups, and SQL injection prevention.
* `tests/test_imbalance.py`: Haversine geodesic calculations (validated against Nairobi-to-Mombasa ~450km distance), imbalance classification, pair matching, and budget optimization.
* `tests/test_models.py`: Calendar/lag/rolling feature transformers, LightGBM demand forecasting with baseline comparisons, and dynamic batch expiry risk scoring.
* **Continuous Integration**: Automated GitHub Actions workflow (`.github/workflows/ci.yml`) testing on Python 3.10, 3.11, 3.12, and 3.13.

---

## 8. Requirements & Tech Stack

* **Language**: Python >= 3.10
* **Data Processing**: Pandas, NumPy, SciPy
* **Machine Learning**: LightGBM, Scikit-Learn
* **Data Storage**: SQLite3
* **Visualization & UI**: Plotly, Dash, Dash Bootstrap Components, Seaborn, Matplotlib
* **Testing & CI**: Pytest, Pytest-Cov, GitHub Actions

---

## 9. License & Attribution

Developed for academic research and capstone demonstration under the **MIT License**. Created by Camila Aoko for the KEMSA Healthcare Supply Chain Intelligence Platform project.
