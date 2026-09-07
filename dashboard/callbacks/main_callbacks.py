"""Main reactive callbacks connecting routing, authentication, filters, tabs, and data views."""
import dash
from dash import Input, Output, State, ctx, html, dcc, ALL
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.auth import authenticate_user
from dashboard.components.navbar import create_navbar
from dashboard.components.cards import create_kpi_deck
from dashboard.views.landing_page import render_landing_page
from dashboard.views.login_page import render_login_page
from dashboard.views.dashboard_view import render_dashboard_view
from dashboard.views.executive_view import render_executive_view
from dashboard.views.county_view import render_county_view, render_facility_dossier_panel
from dashboard.views.facility_view import (
    render_facility_view,
    create_facility_dos_figure,
    create_facility_summary_cards,
    create_fefo_batch_table
)
from dashboard.views.redistribution_view import render_redistribution_view
from dashboard.data_service import (
    get_executive_kpis,
    get_facility_inventory_status,
    get_facility_batch_expiry,
    get_redistribution_recommendations
)


def register_callbacks(app: dash.Dash):
    """Registers all reactive Dash callbacks to the app instance."""

    # -------------------------------------------------------------------------
    # 1. Dynamic Top Navbar (Public vs. Authenticated state & Theme)
    # -------------------------------------------------------------------------
    @app.callback(
        Output("navbar-container", "children"),
        [
            Input("url", "pathname"),
            Input("session-auth", "data"),
            Input("theme-store", "data")
        ]
    )
    def update_navbar(pathname, auth_data, theme_data):
        theme = theme_data if theme_data in ["light", "dark"] else "light"
        return create_navbar(auth_data=auth_data, current_path=pathname or "/", theme=theme)

    # -------------------------------------------------------------------------
    # 1B. Theme Toggle Handler
    # -------------------------------------------------------------------------
    @app.callback(
        [
            Output("theme-store", "data"),
            Output("app-root-container", "className")
        ],
        [Input("theme-toggle-btn", "n_clicks")],
        [State("theme-store", "data")],
        prevent_initial_call=True
    )
    def toggle_theme(n_clicks, current_theme):
        if not n_clicks:
            return dash.no_update, dash.no_update
        current_theme = current_theme if current_theme in ["light", "dark"] else "light"
        new_theme = "dark" if current_theme == "light" else "light"
        return new_theme, f"theme-{new_theme}"

    # -------------------------------------------------------------------------
    # 2. Multi-Page URL Router
    # -------------------------------------------------------------------------
    @app.callback(
        Output("page-content", "children"),
        [
            Input("url", "pathname"),
            Input("session-auth", "data")
        ]
    )
    def render_page_content(pathname, auth_data):
        clean_path = (pathname or "/").rstrip("/")
        if not clean_path:
            clean_path = "/"

        is_auth = bool(auth_data and isinstance(auth_data, dict) and auth_data.get("authenticated"))

        if clean_path == "/login":
            if is_auth:
                return render_dashboard_view(user_info=auth_data)
            return render_login_page()
        elif clean_path == "/dashboard":
            if is_auth:
                return render_dashboard_view(user_info=auth_data)
            else:
                # If attempting to view dashboard unauthenticated, show login with banner
                return html.Div([
                    dbc.Container([
                        dbc.Alert(
                            [
                                html.I(className="bi bi-shield-lock-fill me-2"),
                                "Authentication Required: Please sign in with mock credentials to access the live dashboard."
                            ],
                            color="info",
                            className="my-3 text-center shadow-sm"
                        ),
                        render_login_page()
                    ], fluid=True)
                ])
        else:
            # Default root / landing page
            return render_landing_page()

    # -------------------------------------------------------------------------
    # 3. Authentication: Login Form Submission & 1-Click Demo Personas
    # -------------------------------------------------------------------------
    @app.callback(
        [
            Output("session-auth", "data", allow_duplicate=True),
            Output("url", "pathname", allow_duplicate=True),
            Output("login-feedback", "children"),
            Output("login-username", "value"),
            Output("login-password", "value")
        ],
        [
            Input("login-submit-btn", "n_clicks"),
            Input("demo-btn-admin", "n_clicks"),
            Input("demo-btn-executive", "n_clicks"),
            Input("demo-btn-director", "n_clicks"),
            Input("demo-btn-facility", "n_clicks"),
            Input("demo-btn-planner", "n_clicks")
        ],
        [
            State("login-username", "value"),
            State("login-password", "value")
        ],
        prevent_initial_call=True
    )
    def handle_login_and_demos(login_click, admin_click, exec_click, dir_click, fac_click, plan_click,
                               username, password):
        triggered_id = ctx.triggered_id
        if not triggered_id:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        demo_credentials = {
            "demo-btn-admin": ("admin", "admin"),
            "demo-btn-executive": ("executive", "executive"),
            "demo-btn-director": ("director", "director"),
            "demo-btn-facility": ("facility", "facility"),
            "demo-btn-planner": ("planner", "planner"),
        }

        # 1-Click Demo Persona Clicked
        if triggered_id in demo_credentials:
            u_name, u_pass = demo_credentials[triggered_id]
            user = authenticate_user(u_name, u_pass)
            if user:
                return user, "/dashboard", None, u_name, u_pass

        # Standard Form Login Clicked
        if triggered_id == "login-submit-btn":
            if not username or not password:
                feedback = dbc.Alert(
                    [
                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                        "Please enter both username/email and password."
                    ],
                    color="warning",
                    dismissable=True,
                    className="py-2 small shadow-sm"
                )
                return dash.no_update, dash.no_update, feedback, dash.no_update, dash.no_update

            user = authenticate_user(username, password)
            if user:
                return user, "/dashboard", None, username, password
            else:
                feedback = dbc.Alert(
                    [
                        html.I(className="bi bi-x-circle-fill me-2"),
                        "Invalid credentials. Please use demo accounts (e.g. admin / admin) or click a 1-Click persona below."
                    ],
                    color="danger",
                    dismissable=True,
                    className="py-2 small shadow-sm"
                )
                return dash.no_update, dash.no_update, feedback, dash.no_update, dash.no_update

        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # -------------------------------------------------------------------------
    # 4. Authentication: Logout Action
    # -------------------------------------------------------------------------
    @app.callback(
        [
            Output("session-auth", "data", allow_duplicate=True),
            Output("url", "pathname", allow_duplicate=True)
        ],
        [Input("logout-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def handle_logout(logout_click):
        if logout_click:
            return None, "/"
        return dash.no_update, dash.no_update

    # -------------------------------------------------------------------------
    # 5. Update Executive KPI Cards (when on Dashboard view)
    # -------------------------------------------------------------------------
    @app.callback(
        Output("kpi-deck-container", "children"),
        [
            Input("global-county-filter", "value"),
            Input("global-category-filter", "value")
        ],
        prevent_initial_call=False
    )
    def update_kpi_deck(county, category):
        kpi_data = get_executive_kpis(county=county or "ALL", category=category or "ALL")
        return create_kpi_deck(kpi_data)

    # -------------------------------------------------------------------------
    # 6. Update Main Content based on Active Tab, Filters & Theme
    # -------------------------------------------------------------------------
    @app.callback(
        Output("active-view-container", "children"),
        [
            Input("main-dashboard-tabs", "active_tab"),
            Input("global-county-filter", "value"),
            Input("global-category-filter", "value"),
            Input("global-tier-filter", "value"),
            Input("theme-store", "data")
        ],
        prevent_initial_call=False
    )
    def render_active_tab_content(active_tab, county, category, tier, theme_data):
        county = county or "ALL"
        category = category or "ALL"
        tier = tier or "ALL"
        active_tab = active_tab or "tab-executive"
        theme = theme_data if theme_data in ["light", "dark"] else "light"

        if active_tab == "tab-executive":
            return render_executive_view(county=county, category=category, theme=theme)
        elif active_tab == "tab-county":
            return render_county_view(county=county, category=category, tier=tier, theme=theme)
        elif active_tab == "tab-facility":
            return render_facility_view(theme=theme)
        elif active_tab == "tab-redistribution":
            return render_redistribution_view(county=county, category=category, theme=theme)

        return render_executive_view(county=county, category=category, theme=theme)

    # -------------------------------------------------------------------------
    # 6B. Reactive Callback for Tapping Facilities on the Map of Kenya
    # -------------------------------------------------------------------------
    @app.callback(
        Output("facility-dossier-container", "children"),
        [
            Input("county-map-graph", "clickData"),
            Input({"type": "btn-reset-dossier", "index": ALL}, "n_clicks"),
            Input("global-county-filter", "value"),
            Input("global-category-filter", "value"),
            Input("global-tier-filter", "value"),
            Input("theme-store", "data")
        ],
        prevent_initial_call=True
    )
    def handle_map_click_and_dossier(click_data, reset_clicks, county, category, tier, theme_data):
        triggered_id = ctx.triggered_id
        county = county or "ALL"
        category = category or "ALL"
        tier = tier or "ALL"
        theme = theme_data if theme_data in ["light", "dark"] else "light"

        # Check if reset button was triggered
        if isinstance(triggered_id, dict) and triggered_id.get("type") == "btn-reset-dossier":
            return render_facility_dossier_panel(facility_id=None, county=county, category=category, tier=tier, theme=theme)

        # Revert to scope overview if filters change
        if triggered_id in ["global-county-filter", "global-category-filter", "global-tier-filter"]:
            return render_facility_dossier_panel(facility_id=None, county=county, category=category, tier=tier, theme=theme)

        # Handle map point tap / click
        if click_data and "points" in click_data and len(click_data["points"]) > 0:
            pt = click_data["points"][0]
            customdata = pt.get("customdata")
            selected_id = None
            if customdata is not None:
                if isinstance(customdata, (list, tuple)) and len(customdata) > 0:
                    selected_id = customdata[0]
                elif isinstance(customdata, str):
                    selected_id = customdata
            
            if selected_id:
                return render_facility_dossier_panel(facility_id=str(selected_id), county=county, category=category, tier=tier, theme=theme)

        return render_facility_dossier_panel(facility_id=None, county=county, category=category, tier=tier, theme=theme)

    # -------------------------------------------------------------------------
    # 7. Update Facility Drilldown (DOS, Batches, KPIs) when facility dropdown or theme changes
    # -------------------------------------------------------------------------
    @app.callback(
        [
            Output("facility-dos-graph", "figure"),
            Output("facility-batch-table-container", "children"),
            Output("facility-summary-cards-container", "children")
        ],
        [
            Input("facility-selector-dropdown", "value"),
            Input("theme-store", "data")
        ],
        prevent_initial_call=True
    )
    def update_facility_drilldown(facility_id, theme_data):
        theme = theme_data if theme_data in ["light", "dark"] else "light"
        if not facility_id:
            return go.Figure(), html.P("No facility selected."), html.Div()

        fig_dos = create_facility_dos_figure(facility_id, theme=theme)
        batch_table = create_fefo_batch_table(facility_id, theme=theme)
        summary_cards = create_facility_summary_cards(facility_id, theme=theme)

        return fig_dos, batch_table, summary_cards
    # Export Redistribution Manifest as CSV
    @app.callback(
        Output("download-redistribution-csv", "data"),
        [Input("btn-export-redistribution", "n_clicks")],
        [
            State("global-county-filter", "value"),
            State("global-category-filter", "value")
        ],
        prevent_initial_call=True
    )
    def export_redistribution_csv(n_clicks, county, category):
        if not n_clicks:
            return None
        df_chains = get_redistribution_recommendations(county=county or "ALL", category=category or "ALL", top_n=500)
        return dcc.send_data_frame(df_chains.to_csv, "kemsa_redistribution_manifest.csv", index=False)
