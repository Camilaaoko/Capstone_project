# Walkthrough: Healthcare Supply Chain Intelligence Dashboard (Dash Framework)

We have implemented a **Landing Page**, a **Mock Login Authentication Portal**, and **Multi-Page Routing** for the KEMSA Healthcare Supply Chain Intelligence Platform using the **Plotly Dash** framework.

---

## 1. Modular Package Architecture

The application is structured under [`dashboard/`](file:///d:/emtech/PLP/Capstone/Capstone_project/dashboard) with clear separation of authentication, data services, reusable components, stakeholder views, and reactive callbacks:

```
Capstone_project/
├── run_dashboard.py                 # 🚀 Root execution script: "python run_dashboard.py"
├── requirements.txt                 # dash, dash-bootstrap-components, plotly, pandas, numpy
└── dashboard/
    ├── app.py                       # Core Dash instance with URL location router & session store
    ├── auth.py                      # 🛡️ Mock user authentication repository & validator
    ├── data_service.py              # Cached SQLite query layer reading from analytics.db
    ├── assets/
    │   └── custom.css               # Custom styling (hero banners, card hover effects, clean tables)
    ├── components/
    │   ├── navbar.py                # Dynamic navigation bar (public vs. authenticated state + logout)
    │   ├── filters.py               # Dropdown filters: County, Commodity Category, Facility Tier
    │   └── cards.py                 # Styled KPI metric cards with status indicator badges
    ├── views/
    │   ├── landing_page.py          # 🌟 Public Landing Page: Hero, Feature Cards, Metrics, Personas
    │   ├── login_page.py            # 🔐 Login Portal: Auth form + 1-Click Quick Demo Accounts
    │   ├── dashboard_view.py        # 📊 Authenticated multi-tab analytics dashboard container
    │   ├── executive_view.py        # 📊 View 1: KEMSA National KPIs, Wastage, Supplier Reliability
    │   ├── county_view.py           # 🗺️ View 2: Geographic Map, County Heatmap, Impacted Facilities
    │   ├── facility_view.py         # 🏥 View 3: Facility DOS Gauges, FEFO Batch Expiry Tracker
    │   └── redistribution_view.py   # 🔄 View 4: AI Surplus-to-Shortage Matching & Logistics Costs
    └── callbacks/
        └── main_callbacks.py        # Reactive callbacks for routing, auth, cross-filtering & drilldowns
```

---

## 2. Application Pages & Features

### **Page 1: Platform Landing Page (`/`)**
* **Hero Banner**: Healthcare gradient background, national impact metrics (47 Counties, 150+ Facilities, 45 Commodities, 99.4% AI Match Rate).
* **Core Capabilities Showcase**: 4 feature cards detailing the Executive Overview, County GIS Tracking, Facility Operations, and AI Redistribution.
* **Stakeholder Personas**: Clear alignment for Executive Leadership, County Health Directors, Facility In-Charges, and Logistics Planners.
* **Call-to-Action**: "Access Dashboard" button routing directly to the Login page.

### **Page 2: Mock Authentication Portal (`/login`)**
* **Authentication Form**: Validates mock credentials with instant error feedback.
* **⚡ 1-Click Quick Demo Buttons**: Instant login without typing for 5 roles:
  * **Super Admin**: `admin` / `admin` (or `admin@kemsa.go.ke`)
  * **KEMSA Executive**: `executive` / `executive` (or `executive@kemsa.go.ke`)
  * **County Health Director**: `director` / `director` (or `county@health.go.ke`)
  * **Facility Pharmacist**: `facility` / `facility` (or `facility@clinic.go.ke`)
  * **Logistics Planner**: `planner` / `planner` (or `planner@logistics.go.ke`)

### **Page 3: Authenticated Analytics Dashboard (`/dashboard`)**
* **Session Guard**: Protects analytical views, redirecting unauthenticated traffic to login.
* **Dynamic Header**: Displays logged-in user profile, role badge, and a **"Sign Out"** button.
* **Multi-Tier Tabs**:
  * **View 1: Executive Overview (KEMSA National)**: Stockout days, expiry financial loss, supplier delay matrix, redistribution savings.
  * **View 2: County & Geographic Intelligence**: Facility geospatial scatter map, county severity ranking, deficit breakdown.
  * **View 3: Facility & Inventory Operations**: Days-of-Stock (DOS) monitors, FEFO batch expiry tracker with countdown.
  * **View 4: AI Redistribution & Allocation Engine**: Surplus-to-shortage transfer orders, route distance vs. transport cost analysis.

---

## 3. How to Run the Application

```bash
# 1. From the project root directory:
.\venv\Scripts\python.exe run_dashboard.py
```

### Accessing the Web Application:
* Open your browser and navigate to: **`http://127.0.0.1:8050/`**
* Click **"Access Dashboard"** or **"Sign In"** to open the login portal.
* Use any mock credentials or click a **1-Click Demo Persona** to access the dashboard.
* Click **"Sign Out"** in the top navigation bar to return to the landing page.
