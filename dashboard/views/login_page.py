"""Login page view with mock credential authentication and demo shortcuts with KEMSA branding."""

from dash import html, dcc
import dash_bootstrap_components as dbc
from dashboard.auth import get_mock_users
from dashboard.components.navbar import create_kemsa_logo


def render_login_page():
    """Renders the authentication portal with KEMSA branding and 1-click demo personas."""
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    # Back to Home link
                    html.Div([
                        dcc.Link(
                            [
                                html.I(className="bi bi-arrow-left me-2"),
                                "Return to Public Portal"
                            ],
                            href="/",
                            className="text-decoration-none text-muted fw-semibold small mb-3 d-inline-flex align-items-center"
                        )
                    ]),

                    # Main High-Contrast Login Card
                    dbc.Card([
                        # Card Header Top Color Accent (Emerald to Cyan Gradient)
                        html.Div(style={"height": "5px", "background": "linear-gradient(90deg, #10B981 0%, #0EA5E9 100%)"}),

                        dbc.CardBody([
                            # Header Branding (Authentic KEMSA Logotype without plus icon)
                            html.Div([
                                # Official KEMSA Wordmark in Royal Corporate Blue
                                html.Div([
                                    html.Span(
                                        "KEMSA",
                                        className="kemsa-brand-wordmark",
                                        style={"color": "#003399", "fontSize": "2.4rem", "fontWeight": "900", "letterSpacing": "3.5px"}
                                    ),
                                    html.Span(
                                        " INTELLIGENCE",
                                        className="fw-bold fs-4 ms-1",
                                        style={"color": "#10B981", "letterSpacing": "1px"}
                                    ),
                                ], className="d-flex justify-content-center align-items-baseline mb-1"),

                                # 3 Angled Capsule Pills with Dividing Accent Lines
                                html.Div([
                                    html.Div(className="kemsa-logo-divider-dark me-2"),
                                    html.Div([
                                        html.Span(className="kemsa-pill kemsa-pill-green me-1", style={"width": "7px", "height": "16px"}),
                                        html.Span(className="kemsa-pill kemsa-pill-orange me-1", style={"width": "7px", "height": "16px"}),
                                        html.Span(className="kemsa-pill kemsa-pill-blue", style={"width": "7px", "height": "16px"}),
                                    ], className="d-inline-flex align-items-center px-1"),
                                    html.Div(className="kemsa-logo-divider-dark ms-2"),
                                ], className="d-flex align-items-center justify-content-center mb-2", style={"maxWidth": "320px", "margin": "0 auto"}),

                                html.Small(
                                    "KENYA MEDICAL SUPPLIES AUTHORITY • YOUR PARTNER IN HEALTHCARE",
                                    className="text-muted d-block fw-bold text-uppercase mb-3",
                                    style={"fontSize": "0.64rem", "letterSpacing": "0.9px"}
                                ),

                                html.H4("Healthcare Decision Support Portal", className="welcome-user-name fw-bolder mb-1", style={"fontSize": "1.3rem"}),
                                html.P(
                                    "Sign in with your credentials to access the healthcare analytics workspace.",
                                    className="kpi-card-subtitle small mb-4"
                                )
                            ], className="text-center mb-2"),

                            # Dynamic Feedback Message Container
                            html.Div(id="login-feedback", className="mb-3"),

                            # Login Form
                            html.Div([
                                # Username or Email field
                                html.Div([
                                    html.Label("Username or Email Address", className="form-label small fw-bold text-dark"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="bi bi-person-fill text-muted"), className="bg-light border-end-0"),
                                        dbc.Input(
                                            id="login-username",
                                            placeholder="e.g. admin or executive@kemsa.go.ke",
                                            type="text",
                                            className="form-control-lg fs-6 border-start-0"
                                        )
                                    ], className="mb-3")
                                ]),

                                # Password field
                                html.Div([
                                    html.Label("Password", className="form-label small fw-bold text-dark"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="bi bi-lock-fill text-muted"), className="bg-light border-end-0"),
                                        dbc.Input(
                                            id="login-password",
                                            placeholder="Enter your password",
                                            type="password",
                                            className="form-control-lg fs-6 border-start-0"
                                        )
                                    ], className="mb-3")
                                ]),

                                # Remember Me & Sandbox Mode
                                html.Div([
                                    dbc.Checkbox(
                                        id="login-remember",
                                        label="Keep me signed in",
                                        value=True,
                                        className="small text-muted"
                                    ),
                                    html.Span("Demo Sandbox Active", className="badge kemsa-badge-green small fw-semibold")
                                ], className="d-flex justify-content-between align-items-center mb-4"),

                                # Submit Button
                                dbc.Button(
                                    [
                                        html.I(className="bi bi-shield-lock-fill me-2"),
                                        "Sign In to Dashboard"
                                    ],
                                    id="login-submit-btn",
                                    size="lg",
                                    className="w-100 fw-bold py-3 shadow text-white border-0",
                                    style={
                                        "background": "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)",
                                        "borderRadius": "12px",
                                        "boxShadow": "0 4px 14px rgba(15, 23, 42, 0.25)"
                                    }
                                )
                            ]),

                            # Divider
                            html.Hr(className="my-4", style={"borderColor": "#E2E8F0"}),

                            # 1-Click Quick Demo Login Section
                            html.Div([
                                html.Div([
                                    html.Span("1-Click Demo Personas", className="fw-bold text-dark small text-uppercase")
                                ], className="d-flex align-items-center mb-2 justify-content-center"),
                                html.P(
                                    "Click any role below to instantly authenticate with mock credentials:",
                                    className="text-muted small text-center mb-3"
                                ),

                                # Quick Login Buttons Grid with soft background accents
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button(
                                            [
                                                html.Span([
                                                    html.Span("Admin Leadership", className="fw-bold text-dark d-block", style={"fontSize": "0.88rem"}),
                                                    html.Small("admin / admin", className="font-mono text-muted", style={"fontSize": "0.76rem"})
                                                ])
                                            ],
                                            id="demo-btn-admin",
                                            className="w-100 kemsa-demo-btn mb-2 d-flex align-items-center justify-content-center text-center"
                                        )
                                    ], xs=12, sm=6),
                                    dbc.Col([
                                        dbc.Button(
                                            [
                                                html.Span([
                                                    html.Span("Executive Officer", className="fw-bold text-dark d-block", style={"fontSize": "0.88rem"}),
                                                    html.Small("executive / executive", className="font-mono text-muted", style={"fontSize": "0.76rem"})
                                                ])
                                            ],
                                            id="demo-btn-executive",
                                            className="w-100 kemsa-demo-btn mb-2 d-flex align-items-center justify-content-center text-center"
                                        )
                                    ], xs=12, sm=6),
                                    dbc.Col([
                                        dbc.Button(
                                            [
                                                html.Span([
                                                    html.Span("County Director", className="fw-bold text-dark d-block", style={"fontSize": "0.88rem"}),
                                                    html.Small("director / director", className="font-mono text-muted", style={"fontSize": "0.76rem"})
                                                ])
                                            ],
                                            id="demo-btn-director",
                                            className="w-100 kemsa-demo-btn mb-2 d-flex align-items-center justify-content-center text-center"
                                        )
                                    ], xs=12, sm=6),
                                    dbc.Col([
                                        dbc.Button(
                                            [
                                                html.Span([
                                                    html.Span("Facility In-Charge", className="fw-bold text-dark d-block", style={"fontSize": "0.88rem"}),
                                                    html.Small("facility / facility", className="font-mono text-muted", style={"fontSize": "0.76rem"})
                                                ])
                                            ],
                                            id="demo-btn-facility",
                                            className="w-100 kemsa-demo-btn mb-2 d-flex align-items-center justify-content-center text-center"
                                        )
                                    ], xs=12, sm=6),
                                    dbc.Col([
                                        dbc.Button(
                                            [
                                                html.Span([
                                                    html.Span("Logistics Planner", className="fw-bold text-dark d-block", style={"fontSize": "0.88rem"}),
                                                    html.Small("planner / planner", className="font-mono text-muted", style={"fontSize": "0.76rem"})
                                                ])
                                            ],
                                            id="demo-btn-planner",
                                            className="w-100 kemsa-demo-btn d-flex align-items-center justify-content-center text-center"
                                        )
                                    ], xs=12),
                                ], className="g-2")
                            ])

                        ], className="p-4 p-md-5")
                    ], className="kemsa-card shadow-lg border-0 rounded-4 overflow-hidden")
                ], md=8, lg=6, xl=5)
            ], className="justify-content-center align-items-center min-vh-100 py-5")
        ], fluid=True, className="px-3")
    ], style={"backgroundColor": "#F8FAFC", "minHeight": "100vh"})

