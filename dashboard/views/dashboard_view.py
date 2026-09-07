"""Dashboard view layout housing global filters, KPI cards, and analytical tabs with KEMSA theme."""

from dash import html, dcc
import dash_bootstrap_components as dbc
from dashboard.components.filters import create_filter_bar


def render_dashboard_view(user_info=None):
    """Constructs the authenticated analytics dashboard workspace with KEMSA branding."""
    default_tab = "tab-executive"
    if user_info and isinstance(user_info, dict) and "default_tab" in user_info:
        default_tab = user_info["default_tab"]

    user_welcome = []
    if user_info and isinstance(user_info, dict) and user_info.get("name"):
        user_welcome = [
            dbc.Alert(
                [
                    html.Strong(f"Welcome, {user_info.get('name')}! ", className="welcome-user-name fs-6 fw-bolder"),
                    html.Span(
                        f"Authenticated as {user_info.get('title', user_info.get('role', 'Authorized User'))}. ",
                        className="welcome-user-title small fw-medium"
                    ),
                    html.Span(
                        "AI Decision Support Active",
                        className="badge kemsa-badge-green ms-2 px-2 py-1 small fw-bold"
                    )
                ],
                color="light",
                dismissable=True,
                className="dashboard-welcome-alert shadow-sm mb-4 py-2 px-3 rounded-4"
            )
        ]

    return dbc.Container([
        # Welcome banner if available
        html.Div(user_welcome, id="dashboard-welcome-banner"),

        # Global Filter Bar
        create_filter_bar(),

        # Dynamic KPI Metric Cards
        html.Div(id="kpi-deck-container", className="mb-2"),

        # Main View Navigation Tabs (Pill & Segmented Design)
        dbc.Tabs(
            [
                dbc.Tab(
                    label="Executive Overview",
                    tab_id="tab-executive",
                    tab_class_name="dashboard-tab-link fw-bold",
                    active_tab_class_name="dashboard-tab-active fw-bold"
                ),
                dbc.Tab(
                    label="County & Geographic Intelligence",
                    tab_id="tab-county",
                    tab_class_name="dashboard-tab-link fw-bold",
                    active_tab_class_name="dashboard-tab-active fw-bold"
                ),
                dbc.Tab(
                    label="Facility & Inventory Operations",
                    tab_id="tab-facility",
                    tab_class_name="dashboard-tab-link fw-bold",
                    active_tab_class_name="dashboard-tab-active fw-bold"
                ),
                dbc.Tab(
                    label="AI Redistribution & Allocation Engine",
                    tab_id="tab-redistribution",
                    tab_class_name="dashboard-tab-link fw-bold",
                    active_tab_class_name="dashboard-tab-active fw-bold"
                ),
            ],
            id="main-dashboard-tabs",
            active_tab=default_tab,
            className="main-dashboard-tabs mb-4 shadow-sm p-2 rounded-4"
        ),

        # Dynamic Content Area for Active View
        dcc.Loading(
            id="loading-active-view",
            type="circle",
            color="#10B981",
            children=html.Div(id="active-view-container")
        )
    ], fluid=True, className="px-4 pb-5 pt-2")
