"""Dash application factory and multi-page layout architecture."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from dashboard.components.navbar import create_navbar
from dashboard.callbacks.main_callbacks import register_callbacks


def create_app() -> dash.Dash:
    """Instantiates and configures the Dash multi-page application."""
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.FLATLY,
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"
        ],
        suppress_callback_exceptions=True,
        title="KEMSA Healthcare Supply Chain Intelligence Platform"
    )

    # Base Layout with URL router & Session Store
    app.layout = html.Div([
        # 1. URL Location for SPA Multi-Page Routing
        dcc.Location(id="url", refresh=False),

        # 2. Session Store for Mock Authentication State
        dcc.Store(id="session-auth", storage_type="session"),

        # 3. Local Store for Persistent Light/Dark Theme Preference
        dcc.Store(id="theme-store", storage_type="local", data="light"),

        # 4. Dynamic Top Navbar
        html.Div(id="navbar-container", children=create_navbar()),

        # 5. Main Dynamic Page Content Container
        html.Div(id="page-content", style={"minHeight": "calc(100vh - 70px)"})
    ], id="app-root-container", className="theme-light", style={"minHeight": "100vh"})

    # Register all routing, authentication, and data callbacks
    register_callbacks(app)

    return app


# Expose Flask server for production WSGI deployments (e.g., Gunicorn)
app = create_app()
server = app.server
