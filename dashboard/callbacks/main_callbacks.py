"""Main reactive callbacks connecting filters, tabs, and data views."""

from dash import Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.data_service import (
    get_executive_kpis,
    get_facility_inventory_status,
    get_facility_batch_expiry,
    get_redistribution_recommendations
)
from dashboard.components.cards import create_kpi_deck
from dashboard.views.executive_view import render_executive_view
from dashboard.views.county_view import render_county_view
from dashboard.views.facility_view import render_facility_view
from dashboard.views.redistribution_view import render_redistribution_view


def register_callbacks(app):
    """Registers all reactive Dash callbacks to the app instance."""

    # 1. Update Executive KPI Cards
    @app.callback(
        Output("kpi-deck-container", "children"),
        [
            Input("global-county-filter", "value"),
            Input("global-category-filter", "value")
        ]
    )
    def update_kpi_deck(county, category):
        kpi_data = get_executive_kpis(county=county or "ALL", category=category or "ALL")
        return create_kpi_deck(kpi_data)

    # 2. Update Main Content based on Active Tab & Filters
    @app.callback(
        Output("active-view-container", "children"),
        [
            Input("main-dashboard-tabs", "active_tab"),
            Input("global-county-filter", "value"),
            Input("global-category-filter", "value")
        ]
    )
    def render_active_tab_content(active_tab, county, category):
        county = county or "ALL"
        category = category or "ALL"

        if active_tab == "tab-executive":
            return render_executive_view(county=county, category=category)
        elif active_tab == "tab-county":
            return render_county_view(county=county)
        elif active_tab == "tab-facility":
            return render_facility_view()
        elif active_tab == "tab-redistribution":
            return render_redistribution_view(county=county, category=category)
        
        return render_executive_view(county=county, category=category)

    # 3. Update Facility Drilldown (DOS and Batches) when facility dropdown changes
    @app.callback(
        [
            Output("facility-dos-graph", "figure"),
            Output("facility-batch-table-container", "children")
        ],
        [Input("facility-selector-dropdown", "value")],
        prevent_initial_call=True
    )
    def update_facility_drilldown(facility_id):
        if not facility_id:
            return go.Figure(), html.P("No facility selected.")

        # Inventory DOS
        df_inv = get_facility_inventory_status(facility_id)
        if not df_inv.empty:
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
                title=f"<b>Commodity Days-of-Stock (DOS) for Facility: {facility_id}</b>",
                labels={"avg_days_of_stock": "Average Days of Stock", "commodity_name": "Commodity", "stock_status": "Status"}
            )
            fig_dos.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=400)
        else:
            fig_dos = go.Figure().add_annotation(text="No Inventory Data for Selected Facility", showarrow=False)

        # Batch Expiry
        df_batches = get_facility_batch_expiry(facility_id)
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

        return fig_dos, batch_table

    # 4. Export Redistribution Manifest as CSV
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


