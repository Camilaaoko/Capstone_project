"""Top navigation bar component."""

from dash import html
import dash_bootstrap_components as dbc


def create_navbar():
    """Builds the top navigation bar."""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(
                    html.Div([
                        html.Span("🏥", style={"fontSize": "2rem", "marginRight": "12px"}),
                        html.Span(
                            "KEMSA Supply Chain Intelligence Platform",
                            style={"fontSize": "1.3rem", "fontWeight": "700", "letterSpacing": "0.5px"}
                        ),
                    ], className="d-flex align-items-center"),
                    width="auto"
                ),
            ], align="center", className="g-0"),
            
            dbc.Row([
                dbc.Col(
                    dbc.Badge(
                        "🟢 Analytics Engine Online",
                        color="success",
                        pill=True,
                        className="p-2 me-2 font-monospace"
                    ),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Badge(
                        "47 Counties Architecture",
                        color="info",
                        pill=True,
                        className="p-2 font-monospace"
                    ),
                    width="auto"
                ),
            ], align="center", className="g-0 d-none d-md-flex")
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-3 shadow-sm border-bottom border-secondary"
    )

