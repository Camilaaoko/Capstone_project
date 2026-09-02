"""Reusable filter controls component."""

from dash import dcc, html
import dash_bootstrap_components as dbc
from dashboard.data_service import get_filter_options


def create_filter_bar():
    """Builds global interactive filter bar."""
    options = get_filter_options()
    
    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("📍 County / Jurisdiction:", className="fw-bold text-muted small text-uppercase"),
                    dcc.Dropdown(
                        id="global-county-filter",
                        options=options["counties"],
                        value="ALL",
                        clearable=False,
                        className="shadow-sm"
                    )
                ], md=4, sm=12, className="mb-2 mb-md-0"),
                
                dbc.Col([
                    html.Label("💊 Commodity Category:", className="fw-bold text-muted small text-uppercase"),
                    dcc.Dropdown(
                        id="global-category-filter",
                        options=options["categories"],
                        value="ALL",
                        clearable=False,
                        className="shadow-sm"
                    )
                ], md=4, sm=12, className="mb-2 mb-md-0"),

                dbc.Col([
                    html.Label("🏢 Facility Size Tier:", className="fw-bold text-muted small text-uppercase"),
                    dcc.Dropdown(
                        id="global-tier-filter",
                        options=options["tiers"],
                        value="ALL",
                        clearable=False,
                        className="shadow-sm"
                    )
                ], md=4, sm=12, className="mb-2 mb-md-0"),
            ], align="center")
        ]),
        className="mb-4 shadow-sm border-0 bg-light"
    )

