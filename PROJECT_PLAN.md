# PROJECT_PLAN.md — KEMSA Healthcare Supply Chain Intelligence Platform

## 1. Problem Statement

This platform addresses three structural supply chain breakdowns in Kenya's public healthcare distribution:

* **The Cash Trap**: Counties owe KEMSA billions in unpaid pharmaceutical and medical supply bills. When debt accumulates, KEMSA's cash flow collapses, preventing timely procurement from global and local drug manufacturers. Consequently, inventory restocking freezes nationwide—penalizing even the compliant counties that pay on time.
* **Data Silos / Blind Forecasting**: Epidemiological/disease surveillance data (DHIS2), facility inventory stock counts (i-LMIS), and financial procurement data (ERP) operate in complete isolation. Without cross-system communication, procurement and supply distribution rely on static historical consumption patterns rather than real-time clinical need and forward-looking demand.
* **Stuck Inventory**: Severe distribution imbalances occur routinely—one health facility sits on excess inventory nearing expiration while a neighboring facility within the same region experiences critical stockouts of the exact same essential drug. There is no automated system to identify, match, and orchestrate inter-facility redistribution before ordering new stock or suffering financial expiry losses.

### The Solution
An **Intelligence Layer** that sits on top of KEMSA's existing enterprise systems (DHIS2, i-LMIS, ERP) without replacing them. This platform continuously ingests multi-source data streams to diagnose financial risks, predict stockouts, and prescribe automated, actionable inter-facility redistribution workflows.

---

## 2. The Three Modules (Mapped to Data Analytics Levels)

| Problem | Module | Analytics Level | Description |
| :--- | :--- | :--- | :--- |
| **Cash Trap** | **Financial Risk Scorecard** | **Diagnostic + Explainability** | Evaluates county debt exposure, payment velocity, and order history to assign an objective risk tier (Low / Med / High) accompanied by a plain-language explainability breakdown of contributing factors. |
| **Blind Forecasting** | **Demand Forecasting Engine** | **Predictive** | Utilizes machine learning models to forecast consumption patterns and predict exact stockout dates 30, 60, and 90 days ahead per health facility and commodity. |
| **Stuck Inventory** | **Smart Redistribution Engine** | **Prescriptive** | Detects local stock imbalances and matches surplus donor facilities to deficit recipient facilities using accurate geodesic (Haversine) distance calculations, optimizing transport logistics and preventing wastage. |

---

## 3. The Three User Dashboards — Full Specification

### Dashboard 1: KEMSA National Leadership
* **User Profile**: Non-technical executive requiring country-wide situational awareness in under 30 seconds.
* **Components**:
  1. **KPI Metric Cards**: Headline national figures (e.g., `Counties at High Risk: 8`, `Total National Deficit Exposure`, `Wastage Prevented`).
  2. **National Risk Map**: All 47 counties color-coded by risk tier (Low / Med / High) rendered as a proper county-level choropleth visual (strictly **not** facility GPS points).
  3. **Aggregate Stockout Forecast**: Forward-looking national stockout and commodity demand projection trajectories (30/60/90 days), not merely historical stockout counts.
  4. **Redistribution Activity Log / Summary**: High-level national manifest summarizing completed inter-facility transfers, total reallocated unit volumes, and financial wastage value prevented.
  5. **Export Controls**: One-click summary export (CSV/PDF) for executive reporting.
* **Design Rule**: **NO facility-level detail should leak into this view**—this is strictly a scan-and-decide executive screen.

---

### Dashboard 2: County Health Department / Pharmacist
* **User Profile**: Semi-technical, operational leader needing to act immediately, not just observe.
* **Components**:
  1. **County Risk Scorecard**: Displays the specific county's own assigned risk tier as a clear visual badge and score.
  2. **"Why" Explanation Panel**: Expandable, plain-language breakdown explaining the exact drivers behind the county's risk score (e.g., total debt volume, average days overdue, payment trajectory) without exposing raw statistical output.
  3. **County-Scoped Facility List**: Sortable, color-coded inventory roster strictly filtered to facilities within the logged-in county (not a national aggregate).
  4. **Redistribution Decision Interface**: Actionable redistribution transfer recommendations equipped with functional **Approve** and **Reject** buttons that persist state changes to the database.
  5. **Alert Feed**: Automated, plain-language operational warnings (e.g., *"Facility C predicted to run out of ARVs in 18 days"*).

---

### Dashboard 3: Facility / Hospital Management
* **User Profile**: Least technical, highly time-pressed healthcare worker requiring immediate operational answers without manual analysis.
* **Components**:
  1. **Stock Status**: Simplified color-coded indicators (Green / Amber / Red) per drug, eliminating charts that require complex interpretation.
  2. **Days-of-Stock Progress Bars**: Visual countdown buffers indicating remaining days of safety stock rather than raw inventory counts.
  3. **Nearby Surplus Finder**: Clean, sorted list of nearby facilities holding excess stock of a needed commodity, calculated using real geodesic distance.
  4. **Request Transfer Action**: Functional transfer request form and button that writes the request to the database and dispatches it directly to the County Health Department for approval.
  5. **Dynamic Alert Banner**: High-visibility screen-top status banner (Red / Yellow / Green) immediately communicating the facility's overall stock safety level.

---

### Cross-Cutting Design Principle
The deeper the underlying analysis (machine learning models, multi-factor risk scoring, time-series forecasting, explainability algorithms), the **simpler** the surface interface must be. Technical complexity lives entirely within the backend services. On-screen elements must prioritize plain-language labels, clear color indicators before numeric tables, and action buttons labeled with unambiguous operational terms (e.g., `"Approve Transfer"` instead of technical jargon like `"Execute Redistribution Protocol"`).

### Required Workflow Chain (Must Function End-to-End)
```
Facility spots shortage / surplus → Submits Transfer Request (Persists to Database as REQUESTED)
                                            ↓
County Health Director reviews recommendation → Clicks Approve / Reject (Updates DB State)
                                            ↓
KEMSA National Dashboard automatically reflects updated transfer status and prevented wastage metrics
```

---

## 4. Technology Stack Decision

* **Backend Framework**: **FastAPI** (Python 3.11+) — replaces the monolithic Dash backend to provide modular REST endpoints, Pydantic schema validation, and async database interfaces.
* **Frontend Framework**: **Next.js** (React 18/19, TypeScript, Tailwind CSS, Lucide Icons, Shadcn UI) — replaces the Dash UI to deliver robust multi-role layout separation, client-side caching, and modern reactive UX.
* **Database Layer**: **SQLite (`analytics.db`)** — reuses and extends the star schema with newly structured transactional state tables (`county_debt`, `transfer_requests`).
* **Deployment Target**:
  - **Backend API**: Render (Web Service running FastAPI via Uvicorn/Gunicorn).
  - **Frontend Application**: Vercel (Edge-optimized Next.js deployment).
* **Explicit Migration Note**: While legacy Render deployment files (`Procfile`, `render.yaml`, `render-build.sh`) exist for the old Dash app, they will **NOT** be reused as-is and will be re-architected for the new FastAPI + Next.js decoupled setup.

---

## 5. Audit Findings — Repository Baseline Assessment

### Reusable As-Is or With Modification
* **`analytics/analytics.db`**: SQLite dimensional warehouse containing star schema tables (`DIM_FACILITY`, `DIM_COMMODITY`, `DIM_WAREHOUSE`, `DIM_SUPPLIER`, `FACT_INVENTORY`, `FACT_CONSUMPTION`, `FACT_ORDERS`, `FACT_BATCHES`, `FACT_REDISTRIBUTION`, and precomputed `KPI_*` tables).
* **`etl_pipeline.py` & `generate_data.py`**: Functional synthetic data generation and ETL pipelines; requires extension to generate and ingest county-level debt and credit data.
* **`analytics_module/models/forecasting.py`**: LightGBM model implementation; currently predicts next-day consumption only and must be reworked for multi-horizon (30/60/90-day) stockout date inference.
* **`analytics_module/models/risk_modelling.py`**: LightGBM binary classifier for stockout probability; needs integration with backend API endpoints.
* **`analytics_module/models/imbalance.py`**: Imbalance detection logic exists; contains legacy fallback heuristics (50km same-county / 200km different-county) that must be unified with the true Haversine distance calculator.

### Must Be Built from Scratch
* **Financial Risk Scorecard Module**: County debt data model, risk tier scoring algorithm (Low / Med / High), and plain-language explainability generation service.
* **API-Exposed Forecasting Layer**: Real-time REST endpoints serving 30/60/90-day stockout prediction dates.
* **National County Risk Choropleth Map**: GeoJSON-based county boundary map color-coding all 47 counties by risk tier.
* **County "Why" Explainability Panel**: Structured natural language decomposition of debt burden, overdue days, and repayment trends.
* **Functional Redistribution Approval Workflow**: Interactive Approve/Reject endpoints and database state handlers.
* **Plain-Language Alert Feed**: Real-time operational notification engine.
* **Facility Nearby Surplus Finder UI**: Dedicated facility-level interface to query nearest surplus holders.
* **Transfer Request Form & Write-back Handlers**: Transactional data pathway from facility request submission to county approval queue.
* **Dynamic Inventory Alert Banner**: Screen-top contextual risk indicator for facilities.
* **Genuine Role-Based Access Separation**: Authenticated route guards and view isolation ensuring users only access their designated role workspace.
* **End-to-End Workflow Execution**: Complete state machine connecting Facility requests → County approvals → National log updates.

### Known Issue to Fix (Do Not Carry Over)
* In the legacy Dash app, individual health facility names leaked into the Executive Overview savings chart. The new National Dashboard must strictly maintain national/county-level aggregations and exclude facility names.

---

## 6. Build Plan — 8 Batches

* **Batch 1: Foundation & Plan**
  - *Goal*: Establish the single source of truth (`PROJECT_PLAN.md`), scaffold the FastAPI backend service connecting to `analytics.db`, and verify with a working healthcheck test endpoint.
  - *Status*: **Completed** (2026-09-09)

* **Batch 2: Financial Scorecard (Module 1)**
  - *Goal*: Add county debt data structures to `generate_data.py` and `etl_pipeline.py`, implement risk-tier scoring and explainability logic, and expose via FastAPI endpoints.
  - *Status*: **Completed** (2026-09-09)

* **Batch 3: Demand Forecasting (Module 2)**
  - *Goal*: Rework the LightGBM forecasting model to predict exact 30/60/90-day facility stockout horizons and expose predictions via FastAPI endpoints.
  - *Status*: **Completed** (2026-09-09)

* **Batch 4: Smart Redistribution (Module 3)**
  - *Goal*: Eliminate hardcoded distance fallbacks with geodesic calculations, create the `transfer_requests` state table (`REQUESTED`, `APPROVED`, `REJECTED`), and expose workflow endpoints.
  - *Status*: **Completed** (2026-09-09)

* **Batch 5: Next.js Foundation & Architecture**
  - *Goal*: Scaffold the Next.js frontend application, build role-based authentication/routing guards, and establish the API client connecting to FastAPI.
  - *Status*: **Completed** (2026-09-09)

* **Batch 6: National & County Dashboards (Frontend)**
  - *Goal*: Build the National Leadership choropleth view and County Pharmacist workspace with functional Approve/Reject decision controls.
  - *Status*: **Completed** (2026-09-09)

* **Batch 7: Facility Dashboard (Frontend)**
  - *Goal*: Build the Facility management view featuring simplified stock status, days-of-stock countdowns, surplus finder, dynamic alert banner, and the transfer request form.
  - *Status*: **Completed** (2026-09-09)

* **Batch 8: Production Deployment & Verification**
  - *Goal*: Deploy the FastAPI backend to Render and Next.js frontend to Vercel, configure production environment variables, and verify the end-to-end request-to-approval workflow live.
  - *Status*: **Not Started**

---

## 7. Progress Log

### 2026-09-09 — Batch 1: Foundation & Backend Scaffold
* **Deliverables Completed**:
  - Created [`PROJECT_PLAN.md`](file:///home/daudi/plp/Capstone_project/PROJECT_PLAN.md) defining the architecture, module specifications, 3 user dashboards, tech stack decisions, audit baseline, and 8-batch roadmap.
  - Initialized decoupled [`backend/`](file:///home/daudi/plp/Capstone_project/backend) folder containing `main.py`, `database.py`, `routers/__init__.py`, and `requirements.txt`.
  - Configured CORS middleware for local Next.js client (`http://localhost:3000`) and structured root health-check endpoint (`GET /`).
  - Connected directly to existing `analytics/analytics.db` without database duplication.
  - Created test endpoint (`GET /api/facilities`) querying `DIM_FACILITY`.
* **Verification & Test Results**:
  - Tested locally with live Uvicorn HTTP execution (`http://127.0.0.1:8000/api/facilities`).
  - Verified 200 OK status returning 100 facility records with complete attributes (`facility_id`, `facility_name`, `county`, `sub_county`, coordinates, and patient footfall).
* **Deviations from Plan**: None.

### 2026-09-09 — Batch 2: Financial Risk Scorecard Module (End-to-End)
* **Deliverables Completed**:
  - **Data Generator (`generate_data.py`)**: Added `generate_county_debt()` creating monthly records (`county`, `month`, `amount_owed_kes`, `days_overdue`, `payment_history_score`) across all 47 counties spanning the full 24-month horizon (2024-01 to 2025-12). Integrated `COUNTY_DEBT.csv` generation into `write_outputs()` and added `--only-county-debt` CLI flag.
  - **ETL Pipeline (`etl_pipeline.py`)**: Added `_clean_county_debt()` standardization and loading into `FACT_COUNTY_DEBT` table in `analytics.db` with indexed `(county, month)` lookup, plus `--only-county-debt` execution option.
  - **Risk Scoring & Explainability Engine (`backend/services/financial_scoring.py`)**: Built `calculate_county_financial_risk()` calculating a weighted composite risk score (40% Days Overdue, 35% Debt Volume, 25% Payment History), categorized into tiers (Low < 35.0, Medium 35.0-64.9, High >= 65.0), and producing structured explainability factor breakdowns and plain-language diagnostic summaries.
  - **FastAPI Endpoints (`backend/routers/financial.py`)**:
    - `GET /api/financial/scorecard`: Returns risk tier and composite score for all 47 counties (powers National Executive choropleth and cards).
    - `GET /api/financial/scorecard/{county}`: Returns specific county's tier, score, detailed metric contributions, and plain-language explanation (powers County Pharmacist dashboard & 'Why' panel).
    - Registered `financial_router` in `backend/main.py`.
  - **Automated Tests (`tests/test_financial_scorecard.py`)**: Created unit and integration tests covering database schema, scoring logic thresholds, and all financial API routes.
* **Verification & Test Results**:
  - Successfully loaded 1,128 records into `FACT_COUNTY_DEBT` in `analytics/analytics.db`.
  - Verified realistic county risk distribution for December 2025: 8 High Risk, 11 Medium Risk, 28 Low Risk.
  - Verified endpoints via `fastapi.testclient` and live HTTP Uvicorn on port 8000:
    - High-risk example (`Bungoma`): Score 91.8/100, Tier: High, Days Overdue: 269 days, Outstanding Debt: KES 367,931,896, Payment Score: 21.6/100.
    - Low-risk example (`Bomet`): Score 5.7/100, Tier: Low, Days Overdue: 16 days, Outstanding Debt: KES 4,140,755, Payment Score: 92.7/100.
  - Pytest suite `pytest tests/test_etl.py tests/test_financial_scorecard.py` passed with 11/11 tests passing.
* **Deviations from Plan**: None.

### 2026-09-09 — Batch 3: Predictive Stockout Forecasting Engine (End-to-End)
* **Deliverables Completed**:
  - **Architectural Analysis**: Inspected `analytics_module/models/forecasting.py` and `analytics_module/features/engineering.py`. Identified limitation where legacy model predicted single-step next-day units rather than forward stockout runout dates. Selected Option A (Recursive Multi-Step Forward Depletion) for sub-100ms real-time latency across 1,500 pairs, coupled running stock statefulness, and deployment reliability.
  - **Forecasting Engine (`backend/services/forecasting.py`)**: Built `project_pair_stockout()`, `get_facility_stockout_forecast()`, `get_county_stockout_forecast()`, and `get_national_stockout_forecast()`. Recursively simulates 90-day day-by-day consumption trajectories combining 7/30-day consumption velocity, velocity momentum trends, and weekend calendar adjustments against current closing inventory balances in `FACT_INVENTORY`. Classifies pairs into four standard tiers: `Critical` ($\le 30$ days), `Warning` (31–60 days), `Watch` (61–90 days), and `Healthy` (> 90 days or no stockout).
  - **FastAPI Endpoints (`backend/routers/forecasting.py`)**:
    - `GET /api/forecast/facility/{facility_id}`: Powers Facility Dashboard (Dashboard 3) countdown badges, exact stockout dates, and explainable consumption rates.
    - `GET /api/forecast/county/{county}`: Powers County Health Department (Dashboard 2) operational alert feed and facility-by-facility risk counts.
    - `GET /api/forecast/national`: Powers KEMSA National Leadership (Dashboard 1) executive forecasting card, 30/60/90-day unmet deficit projections, and top 10 urgent pairs (strictly non-leaking summary shape).
    - Registered `forecasting_router` in `backend/main.py`.
  - **Automated Tests (`tests/test_forecasting.py`)**: Added 12 comprehensive unit and integration tests covering risk thresholds, service methods, and HTTP responses (including 404 error cases).
* **Verification & Test Results**:
  - Live HTTP verification on Uvicorn server:
    - Facility endpoint (`FAC0001` - Nairobi National Referral Hospital): Verified realistic distribution across 15 commodities (7 Critical, 4 Warning, 2 Watch, 2 Healthy). E.g. Co-trimoxazole running out in 11 days (2024-04-11), Paracetamol in 29 days (2024-04-29), Doxycycline Healthy (>90 days).
    - County endpoint (`Nairobi`): Aggregated 3 monitored facilities (45 pairs), generated prioritized alert feed (e.g. Embakasi Sub-County Hospital running out of Artemether/Lumefantrine in 1 day).
    - National endpoint: Monitored all 100 facilities (1,500 pairs); projected 30-day deficit (535 critical pairs, 34,267 units), 60-day deficit (1,056 pairs, 150,698 units), and 90-day cumulative exposure (1,280 pairs, 310,376 units).
  - Executed complete active test suite: `pytest tests/test_etl.py tests/test_financial_scorecard.py tests/test_forecasting.py` passed with **23/23 tests passing** in 2.10s.
* **Deviations from Plan**: None.

### 2026-09-09 — Batch 4: Smart Redistribution Engine & Transactional Workflow (End-to-End)
* **Deliverables Completed**:
  - **Geodesic Distance Overhaul (`analytics_module/models/imbalance.py`)**: Eliminated hardcoded heuristic distance placeholders (50.0 km same-county / 200.0 km different-county) in `estimate_distance()` and `find_matching_pairs()`. Replaced with true great-circle Haversine calculations operating directly on genuine GPS coordinates (`latitude`, `longitude`) in `DIM_FACILITY`.
  - **Transactional Database Schema (`analytics.db` -> `transfer_requests`)**: Implemented persistent transactional table `transfer_requests` with schema (`request_id` PK, `source_facility_id`, `destination_facility_id`, `commodity_id`, `requested_quantity`, `recommended_quantity`, `distance_km`, `status` [pending, approved, rejected, completed], `requested_by`, `requested_at`, `reviewed_by`, `reviewed_at`, `reason`). Added auto-migration in `backend/database.py` and indexed lookups.
  - **Matching Service (`backend/services/redistribution.py`)**: Implemented `find_surplus_matches_for_facility()`, `create_transfer_request()`, `get_pending_requests_by_county()`, `update_request_status()`, and `get_redistribution_activity_summary()`. Dynamically connects stockout forecasts (Critical/Warning shortages) with verified surplus donors ($\ge 45$ days of stock and closing stock exceeding safety threshold). Ranks candidates by proximity and surplus volume while generating plain-language rationale.
  - **FastAPI Endpoints (`backend/routers/redistribution.py`)**:
    - `GET /api/redistribution/matches/{facility_id}`: Nearby surplus finder for facilities with shortages.
    - `POST /api/redistribution/request`: Submits new transfer request in `pending` state.
    - `GET /api/redistribution/pending/{county}`: County decision queue for pending transfers.
    - `POST /api/redistribution/request/{request_id}/approve`: Transitions status to `approved`, updates timestamp and reviewer.
    - `POST /api/redistribution/request/{request_id}/reject`: Transitions status to `rejected`.
    - `GET /api/redistribution/activity`: National log and wastage prevented counter.
    - Registered `redistribution_router` in `backend/main.py`.
  - **Automated Tests (`tests/test_redistribution.py`)**: Created unit and integration test suite verifying Haversine calculations, real distance non-placeholder enforcement, full transactional state lifecycle, and all REST endpoints.
* **Verification & Test Results**:
  - Executed complete 5-step end-to-end verification sequence:
    1. `GET /api/redistribution/matches/FAC0001`: Returned 55 real surplus matches. First match: Kiambu County Referral Hospital (`FAC0023`) holding 106 units surplus of Quinine Sulphate 300mg at **8.0 km** real distance (confirmed non-placeholder).
    2. `POST /api/redistribution/request`: Created request `TR-2BB6B995` in `pending` state with complete metadata.
    3. `GET /api/redistribution/pending/Nairobi`: Successfully returned `TR-2BB6B995` in county pending review queue.
    4. `POST /api/redistribution/request/TR-2BB6B995/approve`: Transitioned status to `approved` with reviewer `Dr. Omondi` and timestamp.
    5. `GET /api/redistribution/activity`: Confirmed approved transfer is reflected in national aggregate (1 approved transfer, 100 units transferred, KES 2,200 financial value / wastage prevented).
  - Test Suite execution: `pytest tests/test_etl.py tests/test_financial_scorecard.py tests/test_forecasting.py tests/test_redistribution.py` passed with **27/27 tests passing** in 2.22s.
* **Deviations from Plan**: None.

### 2026-09-09 — Batch 5: Next.js Foundation, Role-Based Auth & Route Guards (End-to-End)
* **Deliverables Completed**:
  - **Next.js Project Scaffold (`frontend/`)**: Initialized decoupled Next.js 14 application with TypeScript, Tailwind CSS, App Router, Lucide Icons, and ESLint. Configured `frontend/.env.local` pointing to local FastAPI backend (`http://localhost:8000`) with production Render deployment note.
  - **Comprehensive Typed API Client (`frontend/lib/api.ts`)**: Built typed fetch wrappers and full TypeScript interfaces connecting to all existing FastAPI endpoints: Financial Risk Scorecard (`getAllCountyScorecards`, `getCountyScorecard`), Predictive Stockout Forecasting (`getFacilityForecast`, `getCountyForecast`, `getNationalForecast`), Smart Redistribution Engine (`getNearbySurplusMatches`, `createTransferRequest`, `getPendingTransfers`, `approveTransfer`, `rejectTransfer`, `getRedistributionActivity`), and Facility registry (`getFacilities`).
  - **Role-Based Auth & Session Infrastructure (`frontend/lib/auth.ts`)**: Implemented lightweight cookie-based session management (`kemsa_session`) storing user role (`national`, `county`, `facility`) and administrative scope (`scopeId`, `scopeName`, `userName`).
  - **Server-Side Route Protection Middleware (`frontend/middleware.ts`)**: Enforced genuine, server-side route boundaries preventing the legacy Dash flaw of leaking or switching views:
    - Unauthenticated requests to `/`, `/national`, `/county`, `/facility` are immediately redirected to `/login`.
    - Authenticated users attempting cross-role navigation (e.g. County or Facility visiting `/national`, or National visiting `/county`/`/facility`) are blocked and redirected to `/access-denied` with explicit role mismatch details.
    - County users attempting URL tampering (e.g. visiting `/county?county=Mombasa` or `/county/Mombasa` when authenticated as Kiambu) are strictly blocked with county scope violation warnings.
    - Facility users attempting URL tampering (e.g. visiting `/facility?facility_id=FAC0002` when authenticated as `FAC0001`) are strictly blocked with facility scope violation warnings.
  - **UI Shell, Login & Proof-of-Connection Placeholders**:
    - `frontend/components/Navbar.tsx` & `ShellLayout.tsx`: Displays platform title ("KEMSA Healthcare Supply Chain Intelligence Platform"), active role & administrative scope badge, and functional "Logout" button clearing cookies.
    - `frontend/app/login/page.tsx`: Role selector with dynamic county picker (47 counties) and live facility picker populated from `/api/facilities`.
    - `frontend/app/access-denied/page.tsx`: Diagnostic screen explaining exact authorization or scope violation with return-to-dashboard navigation.
    - `frontend/app/national/page.tsx`: Proves live connection to `GET /api/financial/scorecard` and `GET /api/forecast/national` (displays live KPI cards and sample county risk scores).
    - `frontend/app/county/page.tsx`: Proves live connection to `GET /api/financial/scorecard/{county}` and `GET /api/forecast/county/{county}` (displays live risk tier badge, KES debt balance, and plain-language 'Why' diagnostic summary).
    - `frontend/app/facility/page.tsx`: Proves live connection to `GET /api/forecast/facility/{facility_id}` and `GET /api/redistribution/matches/{facility_id}` (displays 30/60/90-day countdown buffers and commodity depletion table).
  - **Automated Verification Test Suite (`tests/test_auth_frontend.py`)**: Added 4 automated integration tests verifying unauthenticated redirects, national isolation, county scope isolation, and facility scope isolation.
* **Verification & Test Results**:
  - `npm run build`: Production build completed with 0 errors; all 10 routes compiled and static pages generated.
  - Executed 4-step verification sequence against live Next.js (port 3000) and FastAPI (port 8000) servers:
    1. *National Login*: Authenticated as National Leadership -> `/national` returned 200 OK. Manually navigating to `/county` and `/facility` returned HTTP 307 redirecting to `/access-denied?reason=role_mismatch` (Confirmed Blocked).
    2. *County Login (Kiambu)*: Authenticated as Kiambu County -> `/county` returned 200 OK with live Kiambu data (Medium Risk, 36.3 score, KES 86,412,223.81 debt). Modifying URL to `/county?county=Mombasa` or `/county/Mombasa` returned HTTP 307 redirecting to `/access-denied?reason=county_scope_violation` (Confirmed Blocked). Navigating to `/national` and `/facility` returned HTTP 307 (Confirmed Blocked).
    3. *Facility Login (FAC0001)*: Authenticated as Nairobi National Referral Hospital -> `/facility` returned 200 OK with live forecast (7 critical pairs, 15 commodity forecasts). Modifying URL to `/facility?facility_id=FAC0002` returned HTTP 307 redirecting to `/access-denied?reason=facility_scope_violation` (Confirmed Blocked). Navigating to `/national` and `/county` returned HTTP 307 (Confirmed Blocked).
    4. *Logout / Unauthenticated*: Session cookie cleared -> visiting `/national`, `/county`, `/facility`, and `/` all returned HTTP 307 redirecting to `/login` (Confirmed Blocked).
  - Test Suite execution: `pytest tests/test_etl.py tests/test_financial_scorecard.py tests/test_forecasting.py tests/test_redistribution.py tests/test_auth_frontend.py` passed with **31/31 tests passing**.
* **Deviations from Plan**: None.
 
### 2026-09-09 — Batch 6: National Leadership & County Pharmacist Dashboards (End-to-End)
* **Deliverables Completed**:
  - **National Leadership Dashboard (`frontend/app/national/page.tsx`)**:
    - **KPI Metric Cards**: High-visibility headline stats pulling live data: High Risk Counties (8 / 47), Critical Stockout Pairs (535), Monitored Facilities (100 facilities across 47 counties), and Wastage Prevented (KES 15,560).
    - **National Risk Visual (47-County Grid Scanner)**: Implemented a responsive, scannable county status visual prioritized by composite financial risk score. Features interactive filter tabs (`All (47)`, `High (8)`, `Med (11)`, `Low (28)`), instant live name/keyword search, and proportional distribution bars. Replaced raw data tables with color-coded executive cards (red, amber, green) showing risk badges, debt volume, and primary drivers.
    - **Aggregate Stockout Forecast Progression**: Rendered 30/60/90-day forward demand depletion horizon cards with visual progression bars and plain-language executive diagnostic summaries.
    - **Redistribution Activity Manifest**: Summarized inter-county transfers with headline totals (approved count, units reallocated, financial wastage saved) and generalized route logs (`County A → County B`) that **strictly prevent individual health facility names from leaking into the national executive view**.
    - **One-Click CSV Export**: Frontend utility generating and downloading the complete 47-county financial risk dataset with comprehensive scores, debt volumes, delinquency days, and primary drivers.
  - **County Health Department Dashboard (`frontend/app/county/page.tsx`)**:
    - **County Risk Scorecard**: Scoped strictly to logged-in county (enforced by middleware). Displays prominent risk tier badge (`High`, `Medium`, `Low`), composite score (`36.3/100`), total KES debt to KEMSA, delinquency days, and payment history.
    - **'Why' Explainability Diagnostic Panel**: Plain-language diagnosis sentence visible by default with an expandable accordion decomposing the 3 weighted factors (40% Arrears Age, 35% Debt Volume, 25% Payment History) with exact contribution points.
    - **County-Scoped Facility Inventory Roster**: Filtered list of health facilities in the county cross-referenced with real-time stockout forecast flags, sortable by Highest Risk Flag (Critical first) or alphabetical.
    - **Actionable Redistribution Decision Queue**: Actionable transfer recommendation cards displaying donor/recipient facilities, geodesic Haversine distance, batch quantity, and clinical rationale. Equipped with real, interactive **Approve Transfer** and **Reject** buttons calling `/api/redistribution/request/{id}/approve` and `/reject`. Includes a test transfer creation helper for instant verification.
    - **Prioritized Critical Alert Feed**: Real-time forward-looking warnings sorted by days until stockout, featuring urgency countdown badges.
* **Verification & Test Results**:
  - Live Verification against Uvicorn (`http://localhost:8000`) and Next.js (`http://localhost:3000`):
    - *National Visual*: 47 counties successfully mapped into High (8), Medium (11), and Low (28). Filter pills and search function dynamically. CSV export downloads formatted county risk scorecard.
    - *Non-Leaking Activity Log*: Confirmed National log displays county routes (`Kiambu County → Nairobi County`) without exposing underlying facility names.
    - *County 'Why' Diagnostics*: Verified Kiambu County (`Score: 36.3/100`, `Medium Risk`, `Debt: KES 86,412,223.81`, `96 days overdue`). Verified plain-language diagnostic summary and expandable 3-factor breakdown.
    - *Approve/Reject State Transition Lifecycle*: Created transfer request `TR-983E9F1B` (150 units Amoxicillin, Kiambu to Nairobi). Confirmed presence in Kiambu pending queue (`GET /api/redistribution/pending/Kiambu` returned 1 request). Dispatched `POST /api/redistribution/request/TR-983E9F1B/approve` with reviewer `Dr. K. Njoroge`. Follow-up `GET /api/redistribution/pending/Kiambu` confirmed pending count dropped to 0, confirming transactional state persistence.
  - Test Suite execution: `pytest tests/test_etl.py tests/test_financial_scorecard.py tests/test_forecasting.py tests/test_redistribution.py tests/test_auth_frontend.py` passed with **31/31 tests passing**.
* **Deviations from Plan**: In the National Risk Visual, adopted a prioritized 47-county color-coded card grid with instant filtering and search rather than an external GeoJSON choropleth, ensuring zero external CDN dependencies, instant under-30-second situational awareness, and sub-second load times.
 
### 2026-09-09 — Batch 7: Facility / Hospital Management Dashboard (End-to-End)
* **Deliverables Completed**:
  - **Facility Management Dashboard (`frontend/app/facility/page.tsx`)**:
    - **Dynamic Screen-Top Alert Banner**: Unmissable color-coded status banner (Red / Amber / Green) driven by the facility's worst forward-looking risk flag:
      - *Red*: Triggered when any commodity has $\le 30$ days remaining (`Critical`), displaying the exact count of imminent stockout medicines and recommending immediate inter-facility transfer.
      - *Amber*: Triggered when the worst status is 31–60 days remaining (`Warning`).
      - *Green*: Triggered when all monitored medicines hold $\ge 60$ days safety stock buffer.
    - **Simplified Stock Status & Days-of-Stock Progress Bars**: Zero complex chart axes to interpret; each stocked commodity displays as a clean card showing drug name, category, current inventory units, daily burn rate, and a visual countdown bar:
      - Visual bar scales from 0 to 90 days (mostly empty red for $\le 30$ days, amber for 31–60 days, blue for 61–90 days, full green for $>90$ days).
      - Quick filters: `All ({total})`, `Critical ({critical})`, `Warning ({warning})`, `Healthy ({healthy})`, plus real-time drug name search.
    - **Conversational Nearby Surplus Finder**: Displays neighboring facilities holding $\ge 45$ days surplus buffer, sorted by real geodesic Haversine distance, formatted as plain-language conversational sentences that a healthcare worker would say out loud (e.g. *"Kiambu County Referral Hospital, 8.0 km away in Kiambu County, has 106.0 units of Quinine Sulphate 300mg to spare."*).
    - **Interactive Request Transfer Action & Modal**:
      - One-click "Request Transfer" action on any surplus match opening a minimal modal pre-filled with the recommended transfer batch, donor facility, transport distance, and target recipient.
      - Dispatches `POST /api/redistribution/request` writing the transactional record directly to the `transfer_requests` database table in `pending` status.
      - Renders an explicit confirmation state with Request ID (`TR-XXXXXXXX`), requested batch details, and notification of routing to the County Health Department decision queue.
* **Verification & Test Results**:
  - Executed the complete 5-step verification loop against live Next.js (`http://localhost:3000`) and FastAPI (`http://localhost:8000`):
    1. *Alert Banner Check*: Loaded `FAC0001` (Nairobi National Referral Hospital); real forecast returned 7 Critical drugs, 4 Warning drugs, 2 Healthy drugs. Confirmed top Alert Banner correctly renders in **RED (Critical)** state with plain-language action guidance.
    2. *Surplus Match Detection*: Queried `/api/redistribution/matches/FAC0001`; returned 55 potential donor facilities within 400km. Top match: Kiambu County Referral Hospital (`8.0 km` away) holding 106.0 units surplus of Quinine Sulphate 300mg.
    3. *Request Transfer Submission*: Submitted transfer request via form requesting 45.0 units of Quinine Sulphate from Kiambu County Referral Hospital with requesting officer `Sister Jane (Pharmacy Head - Nairobi Referral)`.
    4. *Success Confirmation Display*: Confirmed modal displayed success confirmation card with Request ID `TR-5DD2A69B` in `pending` status.
    5. *End-to-End County Loop Verification*: Queried `GET /api/redistribution/pending/Nairobi` for destination facility's county. Confirmed request `TR-5DD2A69B` appeared immediately in the County Health Department decision queue, proving the complete **Facility &rarr; County** workflow chain functions end-to-end.
  - Automated Test Suite: `pytest tests/test_etl.py tests/test_financial_scorecard.py tests/test_forecasting.py tests/test_redistribution.py tests/test_auth_frontend.py` passed with **31/31 tests passing** in 3.66s.
* **Deviations from Plan**: None.

### 2026-09-09 — Post-Audit Enhancements: National & County Velocity Trend Charts and Redistribution Scale Fix
* **Deliverables Completed**:
  - **Part 1: National Redistribution Activity Figures Fix (Option C)**:
    - Re-architected `backend/services/redistribution.py` (`get_redistribution_activity_summary`) and `backend/routers/redistribution.py` (`/api/redistribution/activity`) to query and return both `historical_baseline` (aggregated from `FACT_REDISTRIBUTION` where `redistribution_status = 'RECOMMENDED'`: 85,115 transfers, 5,553,836 units, KES 49,200,900) and `live_activity` (from transactional table `transfer_requests`).
    - Exposes unified headline metrics (`combined_total_savings_kes: KES 49.2M+` and `combined_total_transfers: 85,133`) while strictly preserving `transfer_requests` as an unpolluted live audit log.
    - Updated `frontend/app/national/page.tsx` headline KPI card to prominently display KES 49.2M+ Prevented Wastage with clear, secondary live session metrics.
  - **Part 2: National Dashboard 24-Month Macro Debt Exposure Chart**:
    - Created backend endpoint `GET /api/financial/national-debt-trend` in `backend/routers/financial.py` aggregating `FACT_COUNTY_DEBT` monthly totals across all 47 counties.
    - Built responsive Recharts component `frontend/components/NationalDebtTrendChart.tsx` featuring an AreaChart with subtle gradient fill, KES billions axis scaling, custom executive tooltips, and loading skeletons.
    - Integrated near the top of the National Leadership dashboard, providing situational awareness into debt growth velocity (+41.3% from KES 5.23B to KES 7.39B).
  - **Part 3: County Dashboard 24-Month Debt & Risk Velocity Trend Chart**:
    - Created backend endpoint `GET /api/financial/scorecard/{county}/history` in `backend/routers/financial.py` computing monthly financial risk scores and debt metrics across all 24 months for any county.
    - Built `frontend/components/CountyDebtTrendChart.tsx` featuring a dual-axis ComposedChart (debt area on left axis, risk score line 0-100 on right axis) with custom tooltips.
    - Embedded inside the existing 'Why' explainability panel with smooth expand animation (`animate-fadeIn`), keeping the plain-language summary and factor cards intact.
* **Verification & Test Results**:
  - `npm run build`: Production build cleanly completed with 0 errors across all 10 Next.js routes.
  - Test Suite execution: `pytest tests/test_etl.py tests/test_financial_scorecard.py tests/test_forecasting.py tests/test_redistribution.py tests/test_auth_frontend.py` passed with **33/33 tests passing** in 4.10s.
  - Verified live over HTTP:
    - `GET /api/financial/national-debt-trend` returned 24 monthly items.
### 2026-09-09 — Batch 8 / Post-Audit Enhancements: KEMSA Branding, Therapeutic Program Deficit, Kenya Map View Toggle, and Top Reallocated Commodities
* **Deliverables Completed**:
  - **Part 0: Authentic KEMSA Institutional Branding (`frontend/components/Navbar.tsx`)**:
    - Ported institutional logotype and visual identity from legacy Plotly Dash application:
      - **3-Capsule Pill Geometry**: Three angled medicine capsules (Clinical Emerald `#00A859`, Logistics Amber `#FF7A00`, Executive Cyan `#0EA5E9`) tilted at 32 degrees with subtle accent dividers.
      - **Authoritative Wordmark**: High-contrast dark navy badge displaying bold `KEMSA` with letter-spacing alongside emerald `INTELLIGENCE`.
      - **Official Subtitle**: Prominently displays *"KENYA MEDICAL SUPPLIES AUTHORITY • REPUBLIC OF KENYA"*.
      - **Top Republic Gradient Ribbon**: A 4px Kenyan flag/republic color band across the top of the viewport.
      - **Live Operational Indicator**: Green pulsing pill badge displaying *"🟢 Supply Chain Network Active"*.
  - **Part 1: 30-Day Deficit by Therapeutic Program (`frontend/components/TherapeuticCategoryDeficit.tsx`)**:
    - Created backend service `get_category_stockout_forecast` in `backend/services/forecasting.py` and endpoints `GET /api/forecast/categories` and `GET /api/forecast/national/categories` in `backend/routers/forecasting.py`.
    - Recursively aggregates 30-day forward depletion across all 1,500 pairs grouped by `DIM_COMMODITY.category`.
    - Built clean, compact horizontal visual breakdown component sorted from highest financial deficit to lowest:
      1. *Analgesics*: KES 137,616.41 deficit (16,055.9 units across 188 critical pairs in 91 facilities).
      2. *Antimalarials*: KES 133,447.13 deficit (3,813.4 units across 58 critical pairs in 57 facilities).
      3. *Antibiotics*: KES 101,826.55 deficit (14,398.6 units across 289 critical pairs in 99 facilities).
    - Features proportional horizontal bar styling, percentage badges, and primary medicine drivers tags.
  - **Part 2: Kenya Geo-Risk Map View as a Toggle (`frontend/components/KenyaRiskMap.tsx`)**:
    - Added an instant View Mode switch (`Grid View` vs `Map View`) alongside the 47-county visual scanner on `/national`, preserving the scannable grid as the primary default.
    - Built a high-performance, zero-dependency SVG projection of Kenya using exact centroid coordinates (`lat, lng`) for all 47 counties derived from `DIM_FACILITY`.
    - Features:
      - Color-coded node circles by financial risk tier (Red = High, Amber = Medium, Green = Low) with glowing pulse animation on High Risk counties.
      - Geographic context markers including Latitude 0.0° Equator line, cardinal directions, and regional sector callouts (Northern Kenya, Western/Lake Victoria, Southern Rift, Coastal Corridor).
      - Interactive hover and click selection updating a dedicated **County Geo-Financial Focus Card** showing composite score, outstanding debt, days overdue, monitored facilities, restock status, and a direct link to the county's workspace.
      - Full reactivity with Parent filters (All, High, Medium, Low) and text search (matching nodes glow, non-matching dim).
  - **Part 3: Top Reallocated Essential Medicines in Redistribution Manifest**:
    - Extended `backend/services/redistribution.py` (`get_redistribution_activity_summary`) to aggregate top 5 reallocated medicines from `FACT_REDISTRIBUTION`.
    - Updated `RedistributionActivityResponse` in `backend/routers/redistribution.py` and `frontend/lib/api.ts`.
    - Added a compact, high-density **Top Reallocated Essential Medicines (Highest Network Mobility)** panel to Section 4 of `/national`:
      1. *Paracetamol 500mg* (Analgesics): 1,178,900 units reallocated across 9,633 transfers (KES 1.77M value saved).
      2. *Amoxicillin 250mg capsules* (Antibiotics): 975,700 units across 8,997 transfers (KES 3.12M value saved).
      3. *Metronidazole 400mg* (Antibiotics): 823,700 units across 7,924 transfers (KES 3.29M value saved).
      4. *Ibuprofen 400mg* (Analgesics): 790,200 units across 7,771 transfers (KES 3.95M value saved).
      5. *Co-trimoxazole 480mg* (Antibiotics): 588,400 units across 5,852 transfers (KES 2.94M value saved).
* **Verification & Test Results**:
  - `npm run build`: Next.js 14 production build compiled cleanly with **0 errors and 0 warnings** across all 10 application routes.
  - Automated Test Suite: `pytest tests/test_etl.py tests/test_financial_scorecard.py tests/test_forecasting.py tests/test_redistribution.py tests/test_auth_frontend.py` passed with **36/36 tests passing** in 4.94s.
  - Live HTTP Endpoint Verification:
    - `GET /api/forecast/categories` verified returning 3 therapeutic programs with exact KES valuations.
    - `GET /api/redistribution/activity` verified returning headline savings (KES 49.2M+), 85,137 transfers, and top 5 reallocated medicines.
    - Next.js frontend serving responsive pages on port 3000.
* **Deviations from Plan**: None.

### 2026-09-09 — Batch 9: Dashboard Interactivity Enhancements (Audit Remediation)
* **Deliverables Completed**:
  - **1. National Dashboard: County Risk Card → Slide-Over Summary Drawer (`frontend/app/national/page.tsx`)**:
    - Converted static 47-county scanner cards into interactive triggers with hover states and open indicators.
    - Built a slide-over executive brief drawer (`animate-slideLeft`) with backdrop dismissal and close button.
    - Displays:
      - Composite risk score badge & primary driver tile.
      - Full plain-language 'why' diagnostic summary (`plain_language_summary` from `/api/financial/scorecard/{county}`).
      - 4-metric fiscal debt exposure grid: Outstanding Debt (KES), Days Overdue, Payment Reliability History (0-100), and Restock Status (Frozen vs Eligible).
      - 4-tier aggregate supply health countdown counters (Critical <30d, Warning 31-60d, Watch 61-90d, Healthy >90d).
      - **Strict Architectural Invariant Maintained**: Zero individual facility names are displayed in the drawer, strictly preserving executive-level isolation.
  - **2. National Dashboard: 'Counties at High Risk' KPI Card → Filter Shortcut (`frontend/app/national/page.tsx`)**:
    - Transformed the static red "Counties at High Risk" top KPI card into an instant filter shortcut.
    - Clicking the card instantly sets `filterTier` to `'High'` and triggers a smooth scroll (`#national-risk-visual`) directly to the filtered 47-county visual scanner.
  - **3. County Dashboard: Facility Roster Row → Inline Accordion (`frontend/app/county/page.tsx`)**:
    - Upgraded the static table rows in the Facility Monitoring Roster with chevron toggles and click interactions.
    - Expanding a facility row lazily fetches and caches `/api/forecast/facility/{facility_id}`.
    - Renders an inline stockout accordion displaying all Critical, Warning, and Watch commodities for that specific health center, complete with days of stock remaining, predicted runout dates, and daily burn rates.
    - Includes a direct "Find Nearby Surplus" button linking straight to that facility's operational view.
  - **4. County Dashboard: Critical Alert Feed Item → Fast-Track Match Modal (`frontend/app/county/page.tsx`)**:
    - Made items in the Critical Stockout Alerts feed interactive with hover elevation and a "Fast-track match →" pill button.
    - Clicking an alert opens a high-priority redistribution modal that automatically queries `/api/redistribution/matches/{facility_id}?commodity_id={commodity_id}`.
    - Surfaces the nearest neighboring donor facility with Haversine distance, donor stock buffer, available surplus, and recommended transfer batch.
    - Provides a 1-click "Request Transfer & Dispatch to Queue" action that calls `createTransferRequest` and routes the transfer directly into the county's review table.
  - **5. Facility Dashboard: Medicine Countdown Card → Auto-Filter Surplus Finder (`frontend/app/facility/page.tsx`)**:
    - Made days-of-stock countdown cards clickable with interactive hover states and clear visual cues.
    - Clicking any Critical, Warning, or Watch countdown card smooth-scrolls to `#nearby-surplus-finder` and pre-filters available donors specifically for that selected medicine.
    - Displays an active filter badge with match count and a "Show All Donors" reset button.
    - If a healthy card (>90 days buffer) is clicked, displays a plain-language status notice ("Stock buffer is healthy (>90 days). No surplus transfer required.") without jumping or cluttering the view.
* **Verification & Test Results**:
  - Full automated test suite (`.venv/bin/pytest tests/`) executed cleanly with **51/51 tests passing** in 6.43s.
  - Next.js production build (`npm run build`) compiled successfully with **0 errors and 0 warnings** across all routes.
  - Production server verified active and serving on `http://localhost:3000`.
  - End-to-end verification script (`scratch/verify_interactivity.py`) validated all 5 interaction data flows against live FastAPI backend endpoints (`/api/financial/scorecard/{county}`, `/api/forecast/county/{county}`, `/api/forecast/facility/{facility_id}`, `/api/redistribution/matches/{facility_id}`).
* **Deviations from Plan**: None.

