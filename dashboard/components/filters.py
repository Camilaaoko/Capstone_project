"""Reusable filter controls component with KEMSA styling."""

from dash import dcc, html
import dash_bootstrap_components as dbc
from dashboard.data_service import get_filter_options


def create_filter_bar():
    """Builds global interactive filter bar with high z-index to prevent dropdown clipping."""
    options = get_filter_options()
    
    return dbc.Card([
        html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #10B981 0%, #0EA5E9 50%, #6366F1 100%)"}),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Label(
                            "County / Jurisdiction:",
                            className="filter-label fw-bolder small text-uppercase mb-1",
                            style={"fontSize": "0.76rem", "letterSpacing": "0.6px", "fontWeight": "800"}
                        )
                    ], className="d-flex align-items-center mb-1"),
                    dcc.Dropdown(
                        id="global-county-filter",
                        options=options["counties"],
                        value="ALL",
                        clearable=False,
                        className="shadow-sm kemsa-dropdown"
                    )
                ], md=4, sm=12, className="mb-2 mb-md-0", style={"position": "relative", "zIndex": 1050}),
                
                dbc.Col([
                    html.Div([
                        html.Label(
                            "Commodity Category:",
                            className="filter-label fw-bolder small text-uppercase mb-1",
                            style={"fontSize": "0.76rem", "letterSpacing": "0.6px", "fontWeight": "800"}
                        )
                    ], className="d-flex align-items-center mb-1"),
                    dcc.Dropdown(
                        id="global-category-filter",
                        options=options["categories"],
                        value="ALL",
                        clearable=False,
                        className="shadow-sm kemsa-dropdown"
                    )
                ], md=4, sm=12, className="mb-2 mb-md-0", style={"position": "relative", "zIndex": 1049}),

                dbc.Col([
                    html.Div([
                        html.Label(
                            "Facility Size Tier:",
                            className="filter-label fw-bolder small text-uppercase mb-1",
                            style={"fontSize": "0.76rem", "letterSpacing": "0.6px", "fontWeight": "800"}
                        )
                    ], className="d-flex align-items-center mb-1"),
                    dcc.Dropdown(
                        id="global-tier-filter",
                        options=options["tiers"],
                        value="ALL",
                        clearable=False,
                        className="shadow-sm kemsa-dropdown"
                    )
                ], md=4, sm=12, className="mb-2 mb-md-0", style={"position": "relative", "zIndex": 1048}),
            ], align="center", style={"overflow": "visible"})
        ], className="p-3", style={"overflow": "visible"}),
    ],
        className="kemsa-card filter-bar-card mb-4 shadow-sm",
        style={"position": "relative", "zIndex": 1050, "overflow": "visible"}
    )
