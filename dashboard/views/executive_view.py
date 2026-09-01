"""Executive Overview View for KEMSA National Leadership."""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.data_service import (
    get_category_stockout_summary,
    get_expiry_waste_by_commodity,
    get_supplier_performance,
    get_savings_comparison
)


def render_executive_view(county: str = "ALL", category: str = "ALL"):
    """Renders charts and tables for the KEMSA Executive Overview tab."""
    # 1. Stockout by Category
    df_cat = get_category_stockout_summary(county=county)
    if not df_cat.empty:
        fig_cat = px.bar(
            df_cat,
            x="total_stockout_days",
            y="category",
            orientation="h",
            text="total_stockout_days",
            color="total_stockout_days",
            color_continuous_scale="Reds",
            title="<b>Stockout Days by Commodity Category</b>",
            labels={"total_stockout_days": "Total Stockout Days", "category": "Category"}
        )
        fig_cat.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=40, b=20), height=350)
        fig_cat.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    else:
        fig_cat = go.Figure().add_annotation(text="No Stockout Data", showarrow=False)

    # 2. Expiry Waste
    df_exp = get_expiry_waste_by_commodity(county=county, category=category, top_n=10)
    if not df_exp.empty:
        fig_exp = px.bar(
            df_exp,
            x="total_wastage_kes",
            y="commodity_name",
            orientation="h",
            text="total_wastage_kes",
            color="total_wastage_kes",
            color_continuous_scale="Oranges",
            title="<b>Top 10 Commodities by Expiry Waste Value (KES)</b>",
            labels={"total_wastage_kes": "Wastage Value (KES)", "commodity_name": "Commodity"}
        )
        fig_exp.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=40, b=20), height=350)
        fig_exp.update_traces(texttemplate="KES %{text:,.0f}", textposition="outside")
    else:
        fig_exp = go.Figure().add_annotation(text="No Expiry Data", showarrow=False)

    # 3. Supplier Performance
    df_sup = get_supplier_performance()
    if not df_sup.empty:
        fig_sup = px.scatter(
            df_sup,
            x="orders_delayed",
            y="on_time_delivery_rate",
            size="orders_placed",
            color="on_time_delivery_rate",
            hover_name="supplier_name",
            color_continuous_scale="Viridis",
            title="<b>Supplier Reliability Matrix (Bubble Size = Total Orders Placed)</b>",
            labels={"orders_delayed": "Delayed Orders Count", "on_time_delivery_rate": "On-Time Delivery Rate (0-1)"}
        )
        fig_sup.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=360)
        fig_sup.add_hline(y=0.90, line_dash="dash", line_color="green", annotation_text="KEMSA 90% Target")
    else:
        fig_sup = go.Figure().add_annotation(text="No Supplier Data", showarrow=False)

    # 4. Savings Comparison
    df_sav = get_savings_comparison(county=county, category=category, top_n=15)
    if not df_sav.empty:
        fig_sav = px.bar(
            df_sav,
            x="facility_name",
            y=["savings_kes", "transport_cost_kes"],
            barmode="group",
            title="<b>Intelligent Redistribution Savings vs. Transport Cost by Facility (KES)</b>",
            labels={"value": "Amount (KES)", "facility_name": "Health Facility", "variable": "Metric"},
            color_discrete_map={"savings_kes": "#2ecc71", "transport_cost_kes": "#e74c3c"}
        )
        fig_sav.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=360, legend_title="")
    else:
        fig_sav = go.Figure().add_annotation(text="No Savings Data", showarrow=False)

    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_cat, config={"displayModeBar": False}))], className="shadow-sm border-0 mb-4"), lg=6, sm=12),
            dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_exp, config={"displayModeBar": False}))], className="shadow-sm border-0 mb-4"), lg=6, sm=12),
        ]),
        dbc.Row([
            dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_sup, config={"displayModeBar": False}))], className="shadow-sm border-0 mb-4"), lg=6, sm=12),
            dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_sav, config={"displayModeBar": False}))], className="shadow-sm border-0 mb-4"), lg=6, sm=12),
        ])
    ])

