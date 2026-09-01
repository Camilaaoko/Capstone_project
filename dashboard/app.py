"""Dash application factory and main layout definition."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from dashboard.components.navbar import create_navbar
from dashboard.components.filters import create_filter_bar
from dashboard.callbacks.main_callbacks import register_callbacks


def create_app() -> dash.Dash:
    """Instantiates and configures the Dash application."""
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.FLATLY,
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"
        ],
        suppress_callback_exceptions=True,
        title="KEMSA Healthcare Supply Chain Intelligence Platform"
    )

    # Base Layout
    app.layout = html.Div([
        # 1. Top Navbar
        create_navbar(),

        # 2. Main Content Container
        dbc.Container([
            # Global Filters
            create_filter_bar(),

            # Dynamic KPI Metric Cards
            html.Div(id="kpi-deck-container", className="mb-2"),

            # Main View Navigation Tabs
            dbc.Tabs(
                [
                    dbc.Tab(label="📊 Executive Overview (KEMSA)", tab_id="tab-executive", tab_class_name="fw-semibold"),
                    dbc.Tab(label="🗺️ County & Geographic Intelligence", tab_id="tab-county", tab_class_name="fw-semibold"),
                    dbc.Tab(label="🏥 Facility & Inventory Operations", tab_id="tab-facility", tab_class_name="fw-semibold"),
                    dbc.Tab(label="🔄 AI Redistribution & Allocation Engine", tab_id="tab-redistribution", tab_class_name="fw-semibold"),
                ],
                id="main-dashboard-tabs",
                active_tab="tab-executive",
                className="mb-4 shadow-sm bg-white p-2 rounded"
            ),

            # Dynamic Content Area for Active View
            dcc.Loading(
                id="loading-active-view",
                type="circle",
                children=html.Div(id="active-view-container")
            )
        ], fluid=True, className="px-4 pb-5")
    ], style={"backgroundColor": "#f8f9fa", "minHeight": "100vh"})

    # Register callbacks
    register_callbacks(app)

    return app


# Expose Flask server for production WSGI deployments (e.g., Gunicorn)
app = create_app()
server = app.server

