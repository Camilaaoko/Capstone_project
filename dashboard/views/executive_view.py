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


def render_executive_view(county: str = "ALL", category: str = "ALL", theme: str = "light"):
    """Renders charts and tables for the KEMSA Executive Overview tab."""
    layout = get_chart_layout(theme)
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
            color_continuous_scale=["#FCA5A5", "#EF4444", "#991B1B"],
            title="<b>Stockout Days by Commodity Category</b>",
            labels={"total_stockout_days": "Total Stockout Days", "category": "Category"}
        )
        fig_cat.update_layout(**layout, height=350)
        fig_cat.update_yaxes(categoryorder="total ascending")
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
            color_continuous_scale=["#FDE68A", "#F59E0B", "#B45309"],
            title="<b>Top 10 Commodities by Expiry Waste Value (KES)</b>",
            labels={"total_wastage_kes": "Wastage Value (KES)", "commodity_name": "Commodity"}
        )
        fig_exp.update_layout(**layout, height=350)
        fig_exp.update_yaxes(categoryorder="total ascending")
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
            color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
            title="<b>Supplier Reliability Matrix (Bubble Size = Total Orders Placed)</b>",
            labels={"orders_delayed": "Delayed Orders Count", "on_time_delivery_rate": "On-Time Delivery Rate (0-1)"}
        )
        fig_sup.update_layout(**layout, height=360)
        fig_sup.add_hline(y=0.90, line_dash="dash", line_color="#10B981", annotation_text="KEMSA 90% Target")
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
            color_discrete_map={"savings_kes": "#10B981", "transport_cost_kes": "#EF4444"}
        )
        fig_sav.update_layout(**layout, height=360, legend_title="")
    else:
        fig_sav = go.Figure().add_annotation(text="No Savings Data", showarrow=False)

    return html.Div([
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #EF4444 0%, #F87171 100%)"}),
                    dbc.CardBody(dcc.Graph(figure=fig_cat, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card kemsa-chart-card mb-4 shadow-sm"),
                lg=6, sm=12
            ),
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%)"}),
                    dbc.CardBody(dcc.Graph(figure=fig_exp, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card kemsa-chart-card mb-4 shadow-sm"),
                lg=6, sm=12
            ),
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #0EA5E9 0%, #38BDF8 100%)"}),
                    dbc.CardBody(dcc.Graph(figure=fig_sup, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card kemsa-chart-card mb-4 shadow-sm"),
                lg=6, sm=12
            ),
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #10B981 0%, #34D399 100%)"}),
                    dbc.CardBody(dcc.Graph(figure=fig_sav, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card kemsa-chart-card mb-4 shadow-sm"),
                lg=6, sm=12
            ),
        ])
    ])
