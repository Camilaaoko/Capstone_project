"""Facility & Inventory Operations View for Health Facility In-Charges."""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.data_service import get_facility_inventory_status, get_facility_batch_expiry, get_filter_options

def get_chart_layout(theme: str = "light") -> dict:
    """Generates theme-aware Plotly layout properties for high visual contrast."""
    is_dark = theme == "dark"
    text_color = "#FFFFFF" if is_dark else "#000000"
    grid_color = "rgba(255, 255, 255, 0.10)" if is_dark else "#E2E8F0"
    plot_bg = "#1E293B" if is_dark else "#FFFFFF"
    
    return dict(
        font=dict(family="Plus Jakarta Sans, Inter, -apple-system, sans-serif", color=text_color, size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=plot_bg,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color, color=text_color, tickfont=dict(color=text_color)),
        yaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color, color=text_color, tickfont=dict(color=text_color)),
        hoverlabel=dict(bgcolor="#020617" if is_dark else "#0F172A", font_size=12, font_family="Plus Jakarta Sans, sans-serif", font_color="#FFFFFF")
    )


def render_facility_view(facility_id: str = None, theme: str = "light"):
    """Renders facility-specific inventory levels and FEFO batch expiry tables with KEMSA styling."""
    layout = get_chart_layout(theme)
    options = get_filter_options()
    facility_list = options["facilities"]
    
    if not facility_id and facility_list:
        facility_id = facility_list[0]["value"]

    # 1. Inventory Status
    df_inv = get_facility_inventory_status(facility_id) if facility_id else pd.DataFrame()
    if not df_inv.empty:
        df_inv = df_inv.sort_values("avg_days_of_stock")
        fig_dos = px.bar(
            df_inv.head(20),
            x="avg_days_of_stock",
            y="commodity_name",
            orientation="h",
            color="stock_status",
            color_discrete_map={
                "STOCKOUT": "#EF4444",
                "CRITICAL": "#F97316",
                "LOW": "#F59E0B",
                "NORMAL": "#10B981",
                "OVERSTOCKED": "#6366F1"
            },
            title="<b>Commodity Days-of-Stock (DOS) & Safety Threshold Status</b>",
            labels={"avg_days_of_stock": "Average Days of Stock", "commodity_name": "Commodity", "stock_status": "Status"}
        )
        fig_dos.update_layout(**layout, height=400)
    else:
        fig_dos = go.Figure().add_annotation(text="No Inventory Data for Selected Facility", showarrow=False)

    # 2. Batch Expiry Table
    df_batches = get_facility_batch_expiry(facility_id) if facility_id else pd.DataFrame()
    if not df_batches.empty:
        batch_table = dbc.Table.from_dataframe(
            df_batches.head(20).rename(columns={
                "batch_number": "Batch No",
                "commodity_name": "Commodity",
                "category": "Category",
                "initial_quantity": "Initial Qty",
                "remaining_quantity": "Remaining Qty",
                "manufacturing_date": "Mfg Date",
                "expiry_date": "Expiry Date",
                "batch_status": "Batch Status",
                "days_to_expiry_at_end": "Days to Expiry"
            }),
            striped=True,
            bordered=False,
            hover=True,
            responsive=True,
            className="table align-middle mb-0 font-sans"
        )
    else:
        batch_table = html.P("No active batches found for this facility.", className="text-muted p-3 mb-0")

    return html.Div([
        dbc.Card([
            html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #10B981 0%, #0EA5E9 100%)"}),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Label(
                                "Select Health Facility for Local Drilldown:",
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
                    ], md=6, sm=12, style={"position": "relative", "zIndex": 100})
                ], style={"overflow": "visible"})
            ], className="p-3", style={"overflow": "visible"}),
        ],
            className="kemsa-card mb-4 shadow-sm",
            style={"position": "relative", "zIndex": 100, "overflow": "visible"}
        ),
        
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #0EA5E9 0%, #6366F1 100%)"}),
                    dbc.CardHeader(
                        html.Div([
                            html.Span("Facility Days-of-Stock (DOS) Monitor", className="fw-bold fs-6"),
                            html.Span("STOCK BUFFER", className="badge kemsa-badge-cyan small fw-semibold")
                        ], className="d-flex justify-content-between align-items-center"),
                        className="py-3 px-4 border-bottom bg-transparent"
                    ),
                    dbc.CardBody(dcc.Graph(id="facility-dos-graph", figure=fig_dos, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card mb-4 overflow-hidden shadow-sm"),
                lg=12
            )
        ]),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #F59E0B 0%, #EF4444 100%)"}),
                    dbc.CardHeader(
                        html.Div([
                            html.Span("FEFO Batch Expiry & Shelf-Life Tracker", className="fw-bold fs-6"),
                            html.Span("FIRST-EXPIRY-FIRST-OUT", className="badge kemsa-badge-gold small fw-semibold")
                        ], className="d-flex justify-content-between align-items-center"),
                        className="py-3 px-4 border-bottom bg-transparent"
                    ),
                    dbc.CardBody(html.Div(id="facility-batch-table-container", children=batch_table), className="p-0")
                ], className="kemsa-card mb-4 overflow-hidden shadow-sm"),
                lg=12
            )
        ])
    ])
