"""Facility & Inventory Operations View for Health Facility In-Charges."""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional, Dict, Any

from dashboard.data_service import (
    get_facility_inventory_status,
    get_facility_batch_expiry,
    get_filter_options,
    get_connection
)


def get_chart_layout(theme: str = "light") -> dict:
    """Generates theme-aware Plotly layout properties for high visual contrast."""
    is_dark = theme == "dark"
    text_color = "#FFFFFF" if is_dark else "#1E293B"
    grid_color = "rgba(255, 255, 255, 0.12)" if is_dark else "#E2E8F0"
    plot_bg = "#1E293B" if is_dark else "#FFFFFF"
    
    return dict(
        font=dict(family="Plus Jakarta Sans, Inter, -apple-system, sans-serif", color=text_color, size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=plot_bg,
        margin=dict(l=20, r=30, t=50, b=30),
        xaxis=dict(
            gridcolor=grid_color,
            zerolinecolor=grid_color,
            color=text_color,
            tickfont=dict(color=text_color, size=11),
            title_font=dict(size=12, color=text_color)
        ),
        yaxis=dict(
            gridcolor=grid_color,
            zerolinecolor=grid_color,
            color=text_color,
            tickfont=dict(color=text_color, size=11),
            title_font=dict(size=12, color=text_color)
        ),
        hoverlabel=dict(
            bgcolor="#020617" if is_dark else "#0F172A",
            font_size=12,
            font_family="Plus Jakarta Sans, sans-serif",
            font_color="#FFFFFF"
        )
    )


def get_facility_info(facility_id: str) -> Dict[str, Any]:
    """Fetches facility metadata attributes."""
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM DIM_FACILITY WHERE facility_id = ?", conn, params=(facility_id,))
        conn.close()
        if not df.empty:
            return df.iloc[0].to_dict()
    except Exception:
        pass
    return {}


def create_facility_dos_figure(facility_id: str, theme: str = "light") -> go.Figure:
    """Renders high-contrast horizontal bar chart of commodity Days-of-Stock with safety benchmarks."""
    layout = get_chart_layout(theme)
    is_dark = theme == "dark"
    text_color = "#FFFFFF" if is_dark else "#1E293B"
    
    df_inv = get_facility_inventory_status(facility_id) if facility_id else pd.DataFrame()
    
    if df_inv.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="<b>No Inventory Data Available for Selected Facility</b>",
            showarrow=False,
            font=dict(size=14, color=text_color)
        )
        fig.update_layout(**layout, height=380)
        return fig

    # Focus on top 20 commodities sorted by lowest days of stock (highest urgency first)
    df_chart = df_inv.head(20).copy()
    df_chart = df_chart.sort_values("days_of_stock", ascending=True)

    status_color_map = {
        "STOCKOUT": "#EF4444",      # Crimson
        "CRITICAL": "#F97316",      # Bright Orange
        "LOW": "#F59E0B",           # Amber
        "NORMAL": "#10B981",        # Emerald Green
        "OVERSTOCKED": "#6366F1"    # Indigo Blue
    }

    colors = [status_color_map.get(s, "#0EA5E9") for s in df_chart["stock_status"]]

    customdata = df_chart[[
        "category",
        "closing_stock",
        "safety_stock_days",
        "stock_status",
        "total_stockout_days"
    ]].values

    hovertemplate = (
        "<b>%{y}</b><br>"
        "📂 Category: <b>%{customdata[0]}</b><br>"
        "⏳ Days of Stock: <b>%{x:.1f} days</b><br>"
        "📦 Current Closing Stock: <b>%{customdata[1]:,.0f} units</b><br>"
        "🛡️ Safety Threshold: <b>%{customdata[2]} days</b><br>"
        "🏷️ Status: <b>%{customdata[3]}</b><br>"
        "⚠️ Historical Stockout Days: <b>%{customdata[4]} days</b>"
        "<extra></extra>"
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_chart["days_of_stock"],
        y=df_chart["commodity_name"],
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(width=1, color="rgba(255, 255, 255, 0.2)" if is_dark else "rgba(0, 0, 0, 0.1)")
        ),
        customdata=customdata,
        hovertemplate=hovertemplate,
        name="Days of Stock",
        showlegend=False
    ))

    # Reference Threshold Line: 14 Days Safety Buffer
    fig.add_vline(
        x=14,
        line_width=1.5,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text="Safety Buffer (14d)",
        annotation_position="top right",
        annotation_font=dict(size=10, color="#F59E0B", family="Plus Jakarta Sans, sans-serif")
    )

    # Reference Threshold Line: 60 Days Max Operating Stock
    fig.add_vline(
        x=60,
        line_width=1.5,
        line_dash="dot",
        line_color="#6366F1",
        annotation_text="Max Operating (60d)",
        annotation_position="top right",
        annotation_font=dict(size=10, color="#6366F1", family="Plus Jakarta Sans, sans-serif")
    )

    chart_height = max(420, len(df_chart) * 22 + 80)

    fig.update_layout(
        **layout,
        height=chart_height,
        title=dict(
            text="<b>Days-of-Stock (DOS) & Safety Threshold Buffer</b> <span style='font-size:12px; font-weight:normal; color:#64748B;'>(Top 20 Critical Commodities)</span>",
            font=dict(size=14, color=text_color)
        ),
        xaxis_title="Days of Stock (Days)",
        yaxis_title="",
        bargap=0.25
    )

    return fig


def create_facility_summary_cards(facility_id: str, theme: str = "light") -> html.Div:
    """Renders 4 top-level KPI metric cards summarizing facility stockouts and batch shelf-life."""
    is_dark = theme == "dark"
    card_bg = "#1E293B" if is_dark else "#FFFFFF"
    border_color = "rgba(255, 255, 255, 0.1)" if is_dark else "#E2E8F0"
    text_muted_class = "text-light-50" if is_dark else "text-muted"

    df_inv = get_facility_inventory_status(facility_id) if facility_id else pd.DataFrame()
    df_batches = get_facility_batch_expiry(facility_id) if facility_id else pd.DataFrame()
    fac_info = get_facility_info(facility_id)

    stockouts_count = len(df_inv[df_inv["stock_status"] == "STOCKOUT"]) if not df_inv.empty else 0
    critical_count = len(df_inv[df_inv["stock_status"].isin(["CRITICAL", "LOW"])]) if not df_inv.empty else 0
    
    if not df_batches.empty:
        active_batches = len(df_batches[df_batches["remaining_quantity"] > 0])
        urgent_expiring = len(df_batches[(df_batches["remaining_quantity"] > 0) & (df_batches["days_to_expiry_at_end"].between(0, 60))])
    else:
        active_batches = 0
        urgent_expiring = 0

    facility_name = fac_info.get("facility_name", "Health Facility")
    county_name = fac_info.get("county", "Kenya")
    facility_level = fac_info.get("facility_level", "Level 4")
    facility_tier = fac_info.get("facility_size_tier", "Sub-County")

    return html.Div([
        # Facility Header Banner
        html.Div([
            html.Div([
                html.H4(
                    f"🏥 {facility_name}",
                    className="fw-bold mb-1",
                    style={"color": "#FFFFFF" if is_dark else "#0F172A"}
                ),
                html.Div([
                    html.Span(f"📍 {county_name} County", className="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25 me-2 px-2 py-1"),
                    html.Span(f"🏷️ {facility_level}", className="badge bg-info bg-opacity-10 text-info border border-info border-opacity-25 me-2 px-2 py-1"),
                    html.Span(f"🏢 {facility_tier} Tier", className="badge bg-secondary bg-opacity-10 text-secondary border border-secondary border-opacity-25 px-2 py-1")
                ], className="d-flex flex-wrap align-items-center gap-1 mt-1")
            ]),
            html.Div([
                html.Span("LIVE INVENTORY SNAPSHOT", className="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 px-3 py-2 fw-bold")
            ], className="d-none d-md-block")
        ], className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom", style={"borderColor": border_color}),

        # 4 Metric Cards Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Span("Stockout Commodities", className=f"small text-uppercase fw-bold {text_muted_class}"),
                            html.I(className="bi bi-exclamation-octagon-fill text-danger fs-5")
                        ], className="d-flex justify-content-between align-items-center mb-2"),
                        html.H3(f"{stockouts_count}", className="fw-bolder mb-0 text-danger"),
                        html.Small("Immediate replenishment required", className="text-danger small mt-1 d-block")
                    ], className="p-3")
                ], className="shadow-sm border-0 h-100", style={"backgroundColor": card_bg, "borderRadius": "10px", "borderLeft": "4px solid #EF4444"})
            ], md=3, sm=6, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Span("Critical / Low Stock", className=f"small text-uppercase fw-bold {text_muted_class}"),
                            html.I(className="bi bi-exclamation-triangle-fill text-warning fs-5")
                        ], className="d-flex justify-content-between align-items-center mb-2"),
                        html.H3(f"{critical_count}", className="fw-bolder mb-0 text-warning"),
                        html.Small("Stock level below safety buffer", className="text-warning small mt-1 d-block")
                    ], className="p-3")
                ], className="shadow-sm border-0 h-100", style={"backgroundColor": card_bg, "borderRadius": "10px", "borderLeft": "4px solid #F59E0B"})
            ], md=3, sm=6, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Span("Active FEFO Batches", className=f"small text-uppercase fw-bold {text_muted_class}"),
                            html.I(className="bi bi-box-seam-fill text-success fs-5")
                        ], className="d-flex justify-content-between align-items-center mb-2"),
                        html.H3(f"{active_batches}", className="fw-bolder mb-0 text-success"),
                        html.Small("Monitored on site", className="text-success small mt-1 d-block")
                    ], className="p-3")
                ], className="shadow-sm border-0 h-100", style={"backgroundColor": card_bg, "borderRadius": "10px", "borderLeft": "4px solid #10B981"})
            ], md=3, sm=6, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Span("Expiring < 60 Days", className=f"small text-uppercase fw-bold {text_muted_class}"),
                            html.I(className="bi bi-hourglass-split text-info fs-5")
                        ], className="d-flex justify-content-between align-items-center mb-2"),
                        html.H3(f"{urgent_expiring}", className="fw-bolder mb-0 text-info"),
                        html.Small("Priority dispensing candidates", className="text-info small mt-1 d-block")
                    ], className="p-3")
                ], className="shadow-sm border-0 h-100", style={"backgroundColor": card_bg, "borderRadius": "10px", "borderLeft": "4px solid #0EA5E9"})
            ], md=3, sm=6, className="mb-3")
        ])
    ])


def create_fefo_batch_table(facility_id: str, theme: str = "light") -> html.Div:
    """Renders styled FEFO batch tracker table with shelf-life urgency indicators and action badges."""
    is_dark = theme == "dark"
    df_batches = get_facility_batch_expiry(facility_id) if facility_id else pd.DataFrame()

    if df_batches.empty:
        return html.P("No active batches found for this facility.", className="text-muted p-4 mb-0 text-center")

    rows = []
    for _, r in df_batches.head(25).iterrows():
        rem_qty = float(r.get("remaining_quantity", 0))
        init_qty = float(r.get("initial_quantity", 1))
        days_to_exp = int(r.get("days_to_expiry_at_end", 0))
        status = str(r.get("batch_status", ""))

        # Determine shelf-life countdown badge & action
        if rem_qty <= 0 or status == "FULLY_CONSUMED":
            badge = html.Span("Fully Consumed", className="badge bg-secondary bg-opacity-25 text-secondary px-2 py-1")
            action = html.Span("—", className="text-muted small")
        elif status == "EXPIRED" or days_to_exp < 0:
            badge = html.Span(f"Expired ({abs(days_to_exp)}d ago)", className="badge bg-danger px-2 py-1")
            action = html.Span("🚨 Quarantined / Disposal", className="text-danger small fw-bold")
        elif days_to_exp <= 30:
            badge = html.Span(f"🚨 {days_to_exp}d remaining", className="badge bg-danger px-2 py-1 fw-bold")
            action = html.Span("⚡ Expedite Dispensing / AI Transfer", className="text-danger small fw-bold")
        elif days_to_exp <= 60:
            badge = html.Span(f"⚠️ {days_to_exp}d remaining", className="badge bg-warning text-dark px-2 py-1 fw-bold")
            action = html.Span("📋 Prioritize First-Line Consumption", className="text-warning small fw-bold")
        elif days_to_exp <= 90:
            badge = html.Span(f"⏳ {days_to_exp}d remaining", className="badge bg-info bg-opacity-25 text-info px-2 py-1")
            action = html.Span("👀 Standard FEFO Rotation", className="text-info small")
        else:
            badge = html.Span(f"✅ {days_to_exp}d remaining", className="badge bg-success bg-opacity-25 text-success px-2 py-1")
            action = html.Span("🛡️ Healthy Shelf-Life", className="text-success small")

        # Category badge style
        cat_name = str(r.get("category", "")).replace("_", " ").title()

        rows.append(html.Tr([
            html.Td(
                html.Code(str(r.get("batch_number", "")), className="fw-bold text-primary", style={"fontSize": "0.85rem"}),
                className="align-middle"
            ),
            html.Td(
                html.Div([
                    html.Span(str(r.get("commodity_name", "")), className="fw-semibold d-block"),
                    html.Span(cat_name, className="badge bg-secondary bg-opacity-10 text-secondary small", style={"fontSize": "0.72rem"})
                ]),
                className="align-middle"
            ),
            html.Td(
                html.Div([
                    html.Span(f"{rem_qty:,.0f}", className="fw-bold d-block"),
                    html.Small(f"of {init_qty:,.0f} units", className="text-muted")
                ]),
                className="align-middle text-end"
            ),
            html.Td(str(r.get("expiry_date", "")), className="align-middle text-center small"),
            html.Td(badge, className="align-middle text-center"),
            html.Td(action, className="align-middle")
        ]))

    table_header = html.Thead(
        html.Tr([
            html.Th("Batch Lot No", className="border-0 small text-uppercase fw-bold"),
            html.Th("Commodity & Category", className="border-0 small text-uppercase fw-bold"),
            html.Th("Remaining Stock", className="border-0 small text-uppercase fw-bold text-end"),
            html.Th("Expiry Date", className="border-0 small text-uppercase fw-bold text-center"),
            html.Th("Shelf-Life Countdown", className="border-0 small text-uppercase fw-bold text-center"),
            html.Th("FEFO Operational Action", className="border-0 small text-uppercase fw-bold")
        ]),
        className="bg-light bg-opacity-50 border-bottom" if not is_dark else "bg-dark bg-opacity-50 border-bottom border-secondary"
    )

    table_body = html.Tbody(rows)

    return html.Div([
        dbc.Table(
            [table_header, table_body],
            striped=True,
            bordered=False,
            hover=True,
            responsive=True,
            className="table align-middle mb-0"
        )
    ], style={"maxHeight": "460px", "overflowY": "auto"})


def render_facility_view(facility_id: str = None, theme: str = "light"):
    """Renders complete facility-specific operations view with selector, KPIs, DOS graph, and FEFO tracker."""
    options = get_filter_options()
    facility_list = options.get("facilities", [])
    
    if not facility_id and facility_list:
        facility_id = facility_list[0]["value"]

    fig_dos = create_facility_dos_figure(facility_id, theme=theme)
    batch_table = create_fefo_batch_table(facility_id, theme=theme)
    summary_cards = create_facility_summary_cards(facility_id, theme=theme)

    return html.Div([
        # 1. Facility Selector Header Card
        dbc.Card([
            html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #10B981 0%, #0EA5E9 100%)"}),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Label(
                                "Select Health Facility for Operational Drilldown:",
                                className="filter-label fw-bolder small text-uppercase mb-1",
                                style={"fontSize": "0.76rem", "letterSpacing": "0.6px", "fontWeight": "800"}
                            )
                        ], className="d-flex align-items-center mb-1"),
                        dcc.Dropdown(
                            id="facility-selector-dropdown",
                            options=facility_list,
                            value=facility_id,
                            clearable=False,
                            className="shadow-sm kemsa-dropdown"
                        )
                    ], md=7, sm=12, style={"position": "relative", "zIndex": 100}),
                    dbc.Col([
                        html.Div([
                            html.Small("💡 Select any facility to inspect localized stock availability, safety thresholds, and First-Expiry-First-Out batch schedules.", className="text-muted d-block mt-3 mt-md-0")
                        ])
                    ], md=5, sm=12, className="d-flex align-items-center")
                ], style={"overflow": "visible"})
            ], className="p-3", style={"overflow": "visible"}),
        ],
            className="kemsa-card mb-4 shadow-sm",
            style={"position": "relative", "zIndex": 100, "overflow": "visible"}
        ),

        # 2. Dynamic Facility Header & KPI Cards Container
        html.Div(id="facility-summary-cards-container", children=summary_cards),
        
        # 3. Days of Stock Horizontal Bar Chart
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #0EA5E9 0%, #6366F1 100%)"}),
                    dbc.CardHeader(
                        html.Div([
                            html.Span("Facility Days-of-Stock (DOS) Monitor", className="fw-bold fs-6"),
                            html.Span("SAFETY THRESHOLD MONITOR", className="badge kemsa-badge-cyan small fw-semibold")
                        ], className="d-flex justify-content-between align-items-center"),
                        className="py-3 px-4 border-bottom bg-transparent"
                    ),
                    dbc.CardBody(dcc.Graph(id="facility-dos-graph", figure=fig_dos, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card mb-4 overflow-hidden shadow-sm"),
                lg=12
            )
        ]),

        # 4. FEFO Shelf-Life Countdown Table
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #F59E0B 0%, #EF4444 100%)"}),
                    dbc.CardHeader(
                        html.Div([
                            html.Span("FEFO Batch Expiry & Shelf-Life Tracker", className="fw-bold fs-6"),
                            html.Span("FIRST-EXPIRY-FIRST-OUT SCHEDULE", className="badge kemsa-badge-gold small fw-semibold")
                        ], className="d-flex justify-content-between align-items-center"),
                        className="py-3 px-4 border-bottom bg-transparent"
                    ),
                    dbc.CardBody(html.Div(id="facility-batch-table-container", children=batch_table), className="p-0")
                ], className="kemsa-card mb-4 overflow-hidden shadow-sm"),
                lg=12
            )
        ])
    ])

