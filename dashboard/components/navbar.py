"""Top navigation bar component featuring official KEMSA branding and responsive states."""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_kemsa_logo():
    """Builds the authentic KEMSA institutional logotype with 3 pill capsules and no plus icon."""
    return html.Div([
        # Brand Text & Tagline
        html.Div([
            html.Div([
                html.Span(
                    "KEMSA",
                    className="kemsa-brand-wordmark text-white",
                    style={"fontSize": "1.55rem", "letterSpacing": "2.8px", "fontWeight": "900"}
                ),
                html.Span(
                    " INTELLIGENCE",
                    className="fw-bold ms-1",
                    style={"fontSize": "1.08rem", "letterSpacing": "0.8px", "color": "#34D399"}
                ),
            ], className="d-flex align-items-baseline"),

            # 3 Angled Capsule Pills with Divider Accents (Official Brand Geometry)
            html.Div([
                html.Div(className="kemsa-logo-divider me-2"),
                html.Div([
                    html.Span(className="kemsa-pill kemsa-pill-green me-1", style={"width": "5px", "height": "11px"}),
                    html.Span(className="kemsa-pill kemsa-pill-orange me-1", style={"width": "5px", "height": "11px"}),
                    html.Span(className="kemsa-pill kemsa-pill-blue", style={"width": "5px", "height": "11px"}),
                ], className="d-inline-flex align-items-center"),
                html.Div(className="kemsa-logo-divider ms-2"),
            ], className="d-flex align-items-center my-1", style={"maxWidth": "230px"}),

            html.Small(
                "KENYA MEDICAL SUPPLIES AUTHORITY • YOUR PARTNER IN HEALTHCARE",
                className="text-white text-opacity-75 d-block",
                style={"fontSize": "0.60rem", "fontWeight": "700", "letterSpacing": "0.8px"}
            )
        ])
    ], className="d-flex align-items-center py-1")


def create_navbar(auth_data=None, current_path="/", theme="light"):
    """Builds the top navigation bar tailored to public or authenticated states and light/dark theme."""
    is_authenticated = bool(auth_data and isinstance(auth_data, dict) and auth_data.get("authenticated"))
    is_dark = theme == "dark"

    theme_btn = dbc.Col(
        dbc.Button(
            [
                html.I(className="bi bi-sun-fill me-1 text-warning" if is_dark else "bi bi-moon-stars-fill me-1 text-light"),
                html.Span("Light Mode" if is_dark else "Dark Mode", className="fw-semibold")
            ],
            id="theme-toggle-btn",
            color="outline-light",
            size="sm",
            className="px-3 py-1 small border-opacity-50 text-white me-1",
            style={"borderRadius": "8px", "fontSize": "0.82rem"}
        ),
        width="auto"
    )

    # Public Nav items
    if not is_authenticated:
        nav_actions = [
            theme_btn,
            dbc.Col(
                dcc.Link(
                    dbc.Button(
                        [html.I(className="bi bi-house-door me-1"), "Home"],
                        color="link",
                        className="text-white text-decoration-none me-2 fw-semibold"
                    ),
                    href="/"
                ),
                width="auto"
            ),
            dbc.Col(
                dcc.Link(
                    dbc.Button(
                        [
                            html.I(className="bi bi-box-arrow-in-right me-1"),
                            html.Span("Portal Login", className="fw-bold")
                        ],
                        color="success",
                        size="sm",
                        className="px-3 shadow text-white border-0",
                        style={
                            "backgroundColor": "#008751",
                            "borderRadius": "8px",
                            "boxShadow": "0 2px 8px rgba(0, 135, 81, 0.3)"
                        }
                    ),
                    href="/login"
                ),
                width="auto"
            )
        ]
    else:
        # Authenticated Nav items
        user_name = auth_data.get("name", "User")
        user_role = auth_data.get("role", "Staff")
        user_avatar = auth_data.get("avatar", "👤")

        nav_actions = [
            dbc.Col(
                html.Span(
                    "🟢 Supply Chain Network Active",
                    className="kemsa-badge-green badge px-3 py-2 me-2 d-none d-lg-inline-block font-monospace fw-bold",
                    style={"fontSize": "0.75rem", "borderRadius": "8px"}
                ),
                width="auto"
            ),
            theme_btn,
            dbc.Col(
                dcc.Link(
                    dbc.Button(
                        [html.I(className="bi bi-grid-1x2 me-1"), "Dashboard"],
                        color="link",
                        className="text-white text-decoration-none me-2 small fw-semibold"
                    ),
                    href="/dashboard"
                ),
                width="auto"
            ),
            dbc.Col(
                dcc.Link(
                    dbc.Button(
                        [html.I(className="bi bi-house me-1"), "Overview"],
                        color="link",
                        className="text-white text-opacity-75 text-decoration-none me-2 small"
                    ),
                    href="/"
                ),
                width="auto"
            ),
            dbc.Col(
                html.Div([
                    html.Span(user_avatar, className="me-2 fs-5"),
                    html.Span(f"{user_name} ", className="fw-bold text-white small d-none d-sm-inline"),
                    dbc.Badge(user_role, color="warning", className="ms-1 small text-dark fw-bold")
                ], className="d-flex align-items-center bg-white bg-opacity-10 px-3 py-1 rounded-3 me-2 border border-white border-opacity-15"),
                width="auto"
            ),
            dbc.Col(
                dbc.Button(
                    [
                        html.I(className="bi bi-box-arrow-right me-1"),
                        html.Span("Sign Out", className="fw-semibold")
                    ],
                    id="logout-btn",
                    color="outline-danger",
                    size="sm",
                    className="text-white border-danger border-opacity-50",
                    style={"borderRadius": "8px"}
                ),
                width="auto"
            )
        ]

    return dbc.Navbar(
        dbc.Container([
            # Brand & Logo
            dbc.Row([
                dbc.Col(
                    dcc.Link(
                        create_kemsa_logo(),
                        href="/dashboard" if is_authenticated else "/",
                        className="text-decoration-none"
                    ),
                    width="auto"
                ),
            ], align="center", className="g-0"),

            # Right actions
            dbc.Row(nav_actions, align="center", className="g-2")
        ], fluid=True),
        dark=True,
        className="kemsa-navbar mb-0 shadow-sm sticky-top py-2"
    )
