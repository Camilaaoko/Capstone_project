"""Landing page view for KEMSA Healthcare Supply Chain Intelligence Platform."""

from dash import html, dcc
import dash_bootstrap_components as dbc


def render_landing_page():
    """Constructs the elevated KEMSA institutional landing page layout."""
    return html.Div([
        # 1. Hero Section with KEMSA Navy Gradient & Ambient Glows
        html.Div([
            dbc.Container([
                # Headline and Action Buttons Row
                dbc.Row([
                    dbc.Col([
                        # Main Headline (Positioned at the top of the hero section)
                        html.H1(
                            "Next-Generation Healthcare Supply Chain Intelligence",
                            className="font-hero-title display-4 fw-bolder text-white mb-3 mt-0",
                            style={
                                "fontFamily": "'Plus Jakarta Sans', var(--font-primary)",
                                "fontWeight": "800",
                                "letterSpacing": "-0.025em",
                                "lineHeight": "1.15"
                            }
                        ),
                        
                        # Subheading
                        html.P(
                            "A predictive decision-support system engineered to eliminate life-saving medicine "
                            "stockouts, minimize financial expiry wastage with First-Expiry-First-Out (FEFO) "
                            "intelligence, and orchestrate automated inter-facility redistribution across Kenya's 47 counties.",
                            className="lead text-white text-opacity-90 mb-4 fs-5",
                            style={"maxWidth": "860px", "lineHeight": "1.65"}
                        ),
                        
                        # Action Buttons
                        html.Div([
                            dcc.Link(
                                dbc.Button(
                                    [
                                        html.I(className="bi bi-box-arrow-in-right me-2 fs-5"),
                                        "Launch Dashboard"
                                    ],
                                    color="success",
                                    size="lg",
                                    className="px-4 py-3 fw-bold shadow-lg text-white border-0",
                                    style={
                                        "backgroundColor": "#10B981",
                                        "borderRadius": "12px",
                                        "boxShadow": "0 4px 16px rgba(16, 185, 129, 0.4)"
                                    }
                                ),
                                href="/login"
                            ),
                        ], className="d-flex flex-wrap gap-2 mb-4"),
                    ], lg=11, xl=10)
                ], className="pt-2 pb-3"),

                # Live System Metrics Grid (Full-Width Row Spanning 100% Across Container)
                dbc.Row([
                    # Metric 1: Counties Architecture
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.H3("47", className="font-mono fw-bolder mb-0", style={"color": "#38BDF8", "fontSize": "2.4rem", "lineHeight": "1"}),
                                html.Span("LIVE", className="stat-chip-badge", style={"backgroundColor": "rgba(56, 189, 248, 0.15)", "color": "#38BDF8", "border": "1px solid rgba(56, 189, 248, 0.3)"})
                            ], className="d-flex align-items-center justify-content-between mb-2"),
                            html.Div("Counties Architecture", className="fw-bold text-white mb-1", style={"fontSize": "1.05rem", "letterSpacing": "0.2px"}),
                            html.Small("Full geospatial network tracking", className="text-white-50", style={"fontSize": "0.82rem"})
                        ], className="p-4 glass-stat-chip h-100 d-flex flex-column justify-content-between")
                    ], xs=12, sm=6, lg=3, className="mb-3 mb-lg-0"),

                    # Metric 2: Health Facilities
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.H3("150+", className="font-mono fw-bolder mb-0", style={"color": "#34D399", "fontSize": "2.4rem", "lineHeight": "1"}),
                                html.Span("ACTIVE", className="stat-chip-badge", style={"backgroundColor": "rgba(52, 211, 153, 0.15)", "color": "#34D399", "border": "1px solid rgba(52, 211, 153, 0.3)"})
                            ], className="d-flex align-items-center justify-content-between mb-2"),
                            html.Div("Health Facilities", className="fw-bold text-white mb-1", style={"fontSize": "1.05rem", "letterSpacing": "0.2px"}),
                            html.Small("Level 2 to Level 6 hospital nodes", className="text-white-50", style={"fontSize": "0.82rem"})
                        ], className="p-4 glass-stat-chip h-100 d-flex flex-column justify-content-between")
                    ], xs=12, sm=6, lg=3, className="mb-3 mb-lg-0"),

                    # Metric 3: Essential Commodities
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.H3("45", className="font-mono fw-bolder mb-0", style={"color": "#FBBF24", "fontSize": "2.4rem", "lineHeight": "1"}),
                                html.Span("TRACKED", className="stat-chip-badge", style={"backgroundColor": "rgba(251, 191, 36, 0.15)", "color": "#FBBF24", "border": "1px solid rgba(251, 191, 36, 0.3)"})
                            ], className="d-flex align-items-center justify-content-between mb-2"),
                            html.Div("Essential Commodities", className="fw-bold text-white mb-1", style={"fontSize": "1.05rem", "letterSpacing": "0.2px"}),
                            html.Small("10 critical therapeutic categories", className="text-white-50", style={"fontSize": "0.82rem"})
                        ], className="p-4 glass-stat-chip h-100 d-flex flex-column justify-content-between")
                    ], xs=12, sm=6, lg=3, className="mb-3 mb-lg-0"),

                    # Metric 4: AI Redistribution Match
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.H3("99.4%", className="font-mono fw-bolder mb-0", style={"color": "#A78BFA", "fontSize": "2.4rem", "lineHeight": "1"}),
                                html.Span("AI MATCH", className="stat-chip-badge", style={"backgroundColor": "rgba(167, 139, 250, 0.15)", "color": "#A78BFA", "border": "1px solid rgba(167, 139, 250, 0.3)"})
                            ], className="d-flex align-items-center justify-content-between mb-2"),
                            html.Div("AI Redistribution Match", className="fw-bold text-white mb-1", style={"fontSize": "1.05rem", "letterSpacing": "0.2px"}),
                            html.Small("Surplus-to-deficit rebalance SLA", className="text-white-50", style={"fontSize": "0.82rem"})
                        ], className="p-4 glass-stat-chip h-100 d-flex flex-column justify-content-between")
                    ], xs=12, sm=6, lg=3, className="mb-3 mb-lg-0"),
                ], className="g-3 g-lg-4 pt-3 mt-1 border-top border-white border-opacity-10")

            ], fluid=True, className="px-4 px-md-5")
        ], className="kemsa-hero-banner position-relative text-start mb-5",
           style={"paddingTop": "1.5rem", "paddingBottom": "3.5rem"}),

        # 2. Key Modules / Platform Capabilities Section
        dbc.Container([
            # Section Header
            html.Div([
                html.Span("CORE ARCHITECTURE", className="kemsa-badge-green badge px-3 py-1 mb-2 fw-bold text-uppercase"),
                html.H2("Four-Tier Supply Chain Decision Support", className="fw-bolder mb-2 fs-1", style={"color": "#0B8A62"}),
                html.P(
                    "Real-time visibility and decision support across national, county, and facility levels.",
                    className="text-muted fs-5 mb-5",
                    style={"maxWidth": "820px", "margin": "0 auto"}
                )
            ], className="text-center mx-auto mb-4"),

            # 4 Pillar Feature Cards
            dbc.Row([
                # Card 1: Executive Overview
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("National Executive Overview", className="fw-bold mb-3", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.35rem", "lineHeight": "1.3"}),
                            html.P(
                                "Track medicine shortages, expiry waste, and supplier delivery performance across the country.",
                                className="mb-4",
                                style={"color": "#FFFFFF", "opacity": "1", "fontSize": "1.02rem", "lineHeight": "1.68"}
                            ),
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Medicine Shortage Tracking", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="mb-2 d-flex align-items-center"),
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Expiry Loss & Waste Value", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="mb-2 d-flex align-items-center"),
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Supplier On-Time Delivery", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="d-flex align-items-center")
                            ], className="pt-3 border-top", style={"borderColor": "rgba(255, 255, 255, 0.2)"})
                        ], className="p-4")
                    ], className="h-100 kemsa-pillar-card")
                ], md=6, lg=3, className="mb-4"),

                # Card 2: County Intelligence
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("County & GIS Intelligence", className="fw-bold mb-3", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.35rem", "lineHeight": "1.3"}),
                            html.P(
                                "Interactive map showing stock levels and shortages across 150 clinics and hospitals in 10 counties.",
                                className="mb-4",
                                style={"color": "#FFFFFF", "opacity": "1", "fontSize": "1.02rem", "lineHeight": "1.68"}
                            ),
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Interactive Facility Map", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="mb-2 d-flex align-items-center"),
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("County Shortage Rankings", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="mb-2 d-flex align-items-center"),
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Local Medicine Deficits", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="d-flex align-items-center")
                            ], className="pt-3 border-top", style={"borderColor": "rgba(255, 255, 255, 0.2)"})
                        ], className="p-4")
                    ], className="h-100 kemsa-pillar-card")
                ], md=6, lg=3, className="mb-4"),

                # Card 3: Facility Operations
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Facility & FEFO Operations", className="fw-bold mb-3", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.35rem", "lineHeight": "1.3"}),
                            html.P(
                                "Check daily stock levels at each facility and track medicine expiry dates to use older batches first.",
                                className="mb-4",
                                style={"color": "#FFFFFF", "opacity": "1", "fontSize": "1.02rem", "lineHeight": "1.68"}
                            ),
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Daily Stock Level Gauges", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="mb-2 d-flex align-items-center"),
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("First-Expiry-First-Out (FEFO)", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="mb-2 d-flex align-items-center"),
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Batch Expiry Countdowns", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="d-flex align-items-center")
                            ], className="pt-3 border-top", style={"borderColor": "rgba(255, 255, 255, 0.2)"})
                        ], className="p-4")
                    ], className="h-100 kemsa-pillar-card")
                ], md=6, lg=3, className="mb-4"),

                # Card 4: AI Redistribution
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("AI Redistribution Engine", className="fw-bold mb-3", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.35rem", "lineHeight": "1.3"}),
                            html.P(
                                "Smart matching that moves extra stock from well-supplied clinics to nearby clinics facing shortages.",
                                className="mb-4",
                                style={"color": "#FFFFFF", "opacity": "1", "fontSize": "1.02rem", "lineHeight": "1.68"}
                            ),
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Surplus-to-Shortage Matching", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="mb-2 d-flex align-items-center"),
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Fast & Low-Cost Routes", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="mb-2 d-flex align-items-center"),
                                html.Div([
                                    html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.25rem"}),
                                    html.Span("Prevent Emergency Orders", style={"color": "#FFFFFF", "opacity": "1", "fontSize": "0.96rem", "fontWeight": "500"})
                                ], className="d-flex align-items-center")
                            ], className="pt-3 border-top", style={"borderColor": "rgba(255, 255, 255, 0.2)"})
                        ], className="p-4")
                    ], className="h-100 kemsa-pillar-card")
                ], md=6, lg=3, className="mb-4"),
            ], className="mb-5"),

            # 3. Stakeholder Alignment (Persona Cards)
            html.Div([
                html.Div([
                    html.Span("TARGET ROLES", className="kemsa-badge-navy badge px-3 py-1 mb-2 fw-bold text-uppercase")
                ], className="text-center"),
                html.H3("Tailored for Kenya's Healthcare Hierarchy", className="fw-bold text-center mb-4", style={"color": "#0B8A62"}),
                
                dbc.Row([
                    # Persona 1
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Executive Leadership", className="fw-bold mb-2", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.35rem", "lineHeight": "1.3"}),
                                html.Div("KEMSA CEO / MoH Policy Makers", className="mb-3 fw-semibold", style={"color": "#38BDF8", "fontSize": "0.85rem"}),
                                html.P(
                                    "View national supply performance, reduce medicine waste, and track healthcare budgets.",
                                    className="mb-0",
                                    style={"color": "#FFFFFF", "opacity": "1", "fontSize": "1.02rem", "lineHeight": "1.68"}
                                )
                            ], className="p-4")
                        ], className="h-100 kemsa-pillar-card")
                    ], md=6, lg=3, className="mb-4"),

                    # Persona 2
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("County Health Directors", className="fw-bold mb-2", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.35rem", "lineHeight": "1.3"}),
                                html.Div("Counties CEC / Chief Officers", className="mb-3 fw-semibold", style={"color": "#38BDF8", "fontSize": "0.85rem"}),
                                html.P(
                                    "Identify shortage hotspots in rural clinics and ensure fair medicine distribution across the county.",
                                    className="mb-0",
                                    style={"color": "#FFFFFF", "opacity": "1", "fontSize": "1.02rem", "lineHeight": "1.68"}
                                )
                            ], className="p-4")
                        ], className="h-100 kemsa-pillar-card")
                    ], md=6, lg=3, className="mb-4"),

                    # Persona 3
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Facility In-Charges", className="fw-bold mb-2", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.35rem", "lineHeight": "1.3"}),
                                html.Div("Hospital Pharmacists & Clinicians", className="mb-3 fw-semibold", style={"color": "#38BDF8", "fontSize": "0.85rem"}),
                                html.P(
                                    "Track local stock counts, prevent medicine expiry, and request or share extra supplies.",
                                    className="mb-0",
                                    style={"color": "#FFFFFF", "opacity": "1", "fontSize": "1.02rem", "lineHeight": "1.68"}
                                )
                            ], className="p-4")
                        ], className="h-100 kemsa-pillar-card")
                    ], md=6, lg=3, className="mb-4"),

                    # Persona 4
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Logistics Planners", className="fw-bold mb-2", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.35rem", "lineHeight": "1.3"}),
                                html.Div("Supply Chain Dispatch Officers", className="mb-3 fw-semibold", style={"color": "#38BDF8", "fontSize": "0.85rem"}),
                                html.P(
                                    "Review transfer recommendations, plan delivery routes, and track shipments in real time.",
                                    className="mb-0",
                                    style={"color": "#FFFFFF", "opacity": "1", "fontSize": "1.02rem", "lineHeight": "1.68"}
                                )
                            ], className="p-4")
                        ], className="h-100 kemsa-pillar-card")
                    ], md=6, lg=3, className="mb-4"),
                ], className="mb-5")
            ]),

        ], fluid=True, className="px-4 px-md-5"),

        # 4. Uniform Institutional Footer & Capstone Team Section (Ironclad Group)
        html.Footer([
            dbc.Container([
                # Capstone Project Header Row (Compact & Streamlined)
                html.Div([
                    html.Div([
                        html.Span("CAPSTONE PROJECT", className="stat-chip-badge me-2", style={"backgroundColor": "rgba(56, 189, 248, 0.15)", "color": "#38BDF8", "border": "1px solid rgba(56, 189, 248, 0.3)", "fontSize": "0.74rem", "letterSpacing": "1px", "padding": "2px 8px"}),
                        html.Span("IRONCLAD GROUP", className="fw-bolder", style={"color": "#FF5A1F", "fontSize": "1.9rem", "fontWeight": "900", "letterSpacing": "1.5px", "lineHeight": "1"}),
                    ], className="d-flex align-items-center mb-1"),
                    html.P(
                        "Healthcare Supply Chain Intelligence Platform for Optimizing Medical Commodity Distribution in Kenya",
                        className="text-white text-opacity-90 mb-2",
                        style={"fontSize": "1.02rem", "fontWeight": "500", "letterSpacing": "0.1px"}
                    ),
                    
                    # Compact Team Members Heading
                    html.Div([
                        html.Span("TEAM MEMBERS", className="fw-bold text-white text-uppercase", style={"fontSize": "0.82rem", "letterSpacing": "1.2px", "borderBottom": "2px solid #FF5A1F", "paddingBottom": "2px"})
                    ], className="mb-3")
                ]),

                # Team Member Cards Grid (Compact & Sleek Pillar Style)
                dbc.Row([
                    # Member 1: Deborah Omae
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Deborah Omae", className="fw-bold mb-1", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.15rem"}),
                                html.Div("Data Engineering & DevOps Lead", className="mb-2 fw-semibold", style={"color": "#38BDF8", "fontSize": "0.80rem"}),
                                html.P(
                                    "Data ingestion pipelines, Star Schema warehouse models, and deployment readiness.",
                                    className="mb-2",
                                    style={"color": "#FFFFFF", "opacity": "0.95", "fontSize": "0.88rem", "lineHeight": "1.45"}
                                ),
                                html.Div([
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("ETL Pipelines & Ingestion", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="mb-1 d-flex align-items-center"),
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("Star Schema Data Structuring", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="mb-1 d-flex align-items-center"),
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("DevOps & Deployment Readiness", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="d-flex align-items-center")
                                ], className="pt-2 border-top", style={"borderColor": "rgba(255, 255, 255, 0.2)"})
                            ], className="p-3")
                        ], className="h-100 kemsa-pillar-card")
                    ], md=6, lg=3, className="mb-3 mb-lg-0"),

                    # Member 2: Camila Aoko
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Camila Aoko", className="fw-bold mb-1", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.15rem"}),
                                html.Div("Modelling, ML & QA Lead", className="mb-2 fw-semibold", style={"color": "#38BDF8", "fontSize": "0.80rem"}),
                                html.P(
                                    "Predictive demand forecasting, stockout-risk modelling, and QA system validation.",
                                    className="mb-2",
                                    style={"color": "#FFFFFF", "opacity": "0.95", "fontSize": "0.88rem", "lineHeight": "1.45"}
                                ),
                                html.Div([
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("Stockout-Risk Modelling", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="mb-1 d-flex align-items-center"),
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("Demand Forecasting Models", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="mb-1 d-flex align-items-center"),
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("System Testing & UAT Validation", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="d-flex align-items-center")
                                ], className="pt-2 border-top", style={"borderColor": "rgba(255, 255, 255, 0.2)"})
                            ], className="p-3")
                        ], className="h-100 kemsa-pillar-card")
                    ], md=6, lg=3, className="mb-3 mb-lg-0"),

                    # Member 3: Michael Munga
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Michael Munga", className="fw-bold mb-1", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.15rem"}),
                                html.Div("Modelling & ML Co-Lead", className="mb-2 fw-semibold", style={"color": "#38BDF8", "fontSize": "0.80rem"}),
                                html.P(
                                    "AI allocation algorithms for surplus-to-deficit rebalancing and redistribution orders.",
                                    className="mb-2",
                                    style={"color": "#FFFFFF", "opacity": "0.95", "fontSize": "0.88rem", "lineHeight": "1.45"}
                                ),
                                html.Div([
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("Surplus-Deficit Optimization", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="mb-1 d-flex align-items-center"),
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("Predictive Demand Analytics", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="mb-1 d-flex align-items-center"),
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("Allocation Recommendation Model", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="d-flex align-items-center")
                                ], className="pt-2 border-top", style={"borderColor": "rgba(255, 255, 255, 0.2)"})
                            ], className="p-3")
                        ], className="h-100 kemsa-pillar-card")
                    ], md=6, lg=3, className="mb-3 mb-lg-0"),

                    # Member 4: Brian Sigei
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Brian Sigei", className="fw-bold mb-1", style={"color": "#FF5A1F", "fontWeight": "800", "fontSize": "1.15rem"}),
                                html.Div("Dashboard & Visualization Lead", className="mb-2 fw-semibold", style={"color": "#38BDF8", "fontSize": "0.80rem"}),
                                html.P(
                                    "Interactive Dash/Plotly dashboards and GIS geospatial maps across healthcare tiers.",
                                    className="mb-2",
                                    style={"color": "#FFFFFF", "opacity": "0.95", "fontSize": "0.88rem", "lineHeight": "1.45"}
                                ),
                                html.Div([
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("Stakeholder Analytics Dashboards", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="mb-1 d-flex align-items-center"),
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("Geospatial GIS Network Maps", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="mb-1 d-flex align-items-center"),
                                    html.Div([
                                        html.I(className="bi bi-check2-circle me-2", style={"color": "#FF5A1F", "fontSize": "1.05rem"}),
                                        html.Span("Real-Time FEFO Inventory Monitors", style={"color": "#FFFFFF", "fontSize": "0.86rem", "fontWeight": "500"})
                                    ], className="d-flex align-items-center")
                                ], className="pt-2 border-top", style={"borderColor": "rgba(255, 255, 255, 0.2)"})
                            ], className="p-3")
                        ], className="h-100 kemsa-pillar-card")
                    ], md=6, lg=3, className="mb-3 mb-lg-0"),
                ], className="g-3"),

            ], fluid=True, className="px-4 px-md-5")
        ], className="kemsa-unified-footer text-start pt-4 pb-4 mt-4")

    ], className="landing-page-wrapper bg-white")

