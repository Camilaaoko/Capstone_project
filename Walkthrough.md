# Walkthrough: Healthcare Supply Chain Intelligence Dashboard (Dash Framework)

We have implemented an interactive, multi-tier **Dash (Plotly)** web application with a modular package architecture for the Healthcare Supply Chain Intelligence Platform.

---

## 1. Modular Package Architecture

The dashboard is structured under [`dashboard/`](file:///d:/emtech/PLP/Capstone/Capstone_project/dashboard) with clear separation of data services, reusable components, stakeholder views, and reactive callbacks:

```
Capstone_project/
├── run_dashboard.py            # 🚀 Root execution script: "python run_dashboard.py"
├── requirements.txt            # Updated with dash, dash-bootstrap-components, plotly
└── dashboard/
    ├── app.py                  # Core Dash instance with Bootstrap 'FLATLY' theme
    ├── data_service.py         # Cached SQLite query layer reading from analytics.db
    ├── assets/
    │   └── custom.css          # Custom styling (card hover effects, tabs, clean tables)
    ├── components/
    │   ├── navbar.py           # Header navigation with KEMSA branding & live status badges
    │   ├── filters.py          # Dropdown filters: County, Commodity Category, Facility Tier
    │   └── cards.py            # Styled KPI metric cards with status indicator badges
    ├── views/
    │   ├── executive_view.py   # 📊 View 1: KEMSA National KPIs, Wastage, Supplier Reliability
    │   ├── county_view.py      # 🗺️ View 2: Geographic Map, County Heatmap, Impacted Facilities
    │   ├── facility_view.py    # 🏥 View 3: Facility DOS Gauges, FEFO Batch Expiry Tracker
    │   └── redistribution_view.py # 🔄 View 4: AI Surplus-to-Shortage Matching & Logistics Costs
    └── callbacks/
        └── main_callbacks.py   # Reactive callbacks for instant cross-filtering & drilldowns
```

---

## 2. Four Multi-Tier Stakeholder Views

### **View 1: Executive Overview (KEMSA National)**
* **Stockout by Category**: Horizontal bar chart comparing stockout days across categories (Antibiotics, Maternal Health, Antimalarials, etc.).
* **Expiry Wastage (KES)**: Highlights top commodities contributing to financial expiry loss.
* **Supplier Performance Matrix**: Bubble scatter plot charting supplier delay days against on-time delivery rates vs. KEMSA's 90% target.
* **Redistribution Savings vs. Transport Cost**: Quantifies economic savings achieved by local redistribution over emergency procurement.

### **View 2: County & Geographic Intelligence (County Health Directors)**
* **Geospatial Map**: Scatter plot of health facilities across Kenya sized by daily patient visits and colored by stockout intensity.
* **County Stockout Severity Ranking**: Compares stockout days and the number of affected health centers per county.
* **County Deficit Table**: Granular breakdown of estimated commodity unit shortages.

### **View 3: Facility & Inventory Operations (Health Facility In-Charges)**
* **Interactive Facility Selector**: Filter by any health facility in the network.
* **Days-of-Stock (DOS) Monitor**: Color-coded horizontal bars indicating `STOCKOUT`, `CRITICAL`, `LOW`, `NORMAL`, and `OVERSTOCKED` status against safety stock thresholds.
* **FEFO Batch Expiry Tracker**: Live table of active batches with manufacturing dates, expiry dates, remaining quantities, and days-to-expiry countdown.

### **View 4: AI Redistribution & Allocation Engine (Logistics Planners)**
* **Active Surplus-to-Shortage Recommendations**: Live transfer orders matching surplus source facilities to shortage destination facilities.
* **Distance vs. Transport Cost Analysis**: Visualizes transfer routes with bubble sizes representing recommended units to transfer.
* **Commodity Unit Volume Reallocation**: Identifies which commodities have the highest network redistribution potential.

---

## 3. How to Run the Dashboard

```bash
# 1. Ensure you are in the project root directory
cd d:\emtech\PLP\Capstone\Capstone_project

# 2. Run the dashboard
python run_dashboard.py
```

### Optional Command-Line Flags:
* Custom Port: `python run_dashboard.py --port 8080`
* Custom Host: `python run_dashboard.py --host 0.0.0.0`
* Debug Mode: `python run_dashboard.py --debug`

Access the web interface in your browser at **`http://127.0.0.1:8050/`**.

---

## 4. Validation & Verification Results

* **Dependency Installation**: `dash`, `dash-bootstrap-components`, `plotly`, `pandas`, `numpy` installed and verified.
* **ETL Pipeline**: Ingested raw synthetic records, cleaned 7 data-quality anomalies, constructed the star schema, and populated [`analytics/analytics.db`](file:///d:/emtech/PLP/Capstone/Capstone_project/analytics/analytics.db) (`PASS`).
* **Data Service Verification**: All SQL queries in `data_service.py` executed cleanly against `analytics.db` without missing columns or syntax errors.
* **View Smoke Tests**: All 4 stakeholder views rendered and returned valid Dash component trees (`PASS`).
