"""Facility & Inventory Operations View for Health Facility In-Charges."""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.data_service import get_facility_inventory_status, get_facility_batch_expiry, get_filter_options


def render_facility_view(facility_id: str = None):
    """Renders facility-specific inventory levels and FEFO batch expiry tables."""
    options = get_filter_options()
    facility_list = options["facilities"]
    
    if not facility_id and facility_list:
        facility_id = facility_list[0]["value"]

    # 1. Inventory Status
    df_inv = get_facility_inventory_status(facility_id) if facility_id else pd.DataFrame()
    if not df_inv.empty:
        # Sort by days of stock
        df_inv = df_inv.sort_values("avg_days_of_stock")
        fig_dos = px.bar(
            df_inv.head(20),
            x="avg_days_of_stock",
            y="commodity_name",
            orientation="h",
            color="stock_status",
            color_discrete_map={
                "STOCKOUT": "#e74c3c",
                "CRITICAL": "#e67e22",
                "LOW": "#f1c40f",
                "NORMAL": "#2ecc71",
                "OVERSTOCKED": "#9b59b6"
            },
            title="<b>Commodity Days-of-Stock (DOS) & Stock Status</b>",
            labels={"avg_days_of_stock": "Average Days of Stock", "commodity_name": "Commodity", "stock_status": "Status"}
        )
        fig_dos.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=400)
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
            bordered=True,
            hover=True,
            responsive=True,
            className="small shadow-sm"
        )
    else:
        batch_table = html.P("No active batches found for this facility.", className="text-muted")

    return html.Div([
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("🏥 Select Health Facility for Local Drilldown:", className="fw-bold text-muted small text-uppercase"),
                        dcc.Dropdown(
                            id="facility-selector-dropdown",
                            options=facility_list,
                            value=facility_id,
                            clearable=False,
                            className="shadow-sm"
                        )
                    ], md=6, sm=12)
                ])
            ]),
            className="mb-4 shadow-sm border-0 bg-light"
        ),
        
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("📦 Facility Days-of-Stock (DOS) Monitor", className="fw-bold bg-white"),
                    dbc.CardBody(dcc.Graph(id="facility-dos-graph", figure=fig_dos, config={"displayModeBar": False}))
                ], className="shadow-sm border-0 mb-4"),
                lg=12
            )
        ]),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("⏳ FEFO Batch Expiry & Shelf-Life Tracker", className="fw-bold bg-white"),
                    dbc.CardBody(html.Div(id="facility-batch-table-container", children=batch_table))
                ], className="shadow-sm border-0 mb-4"),
                lg=12
            )
        ])
    ])

