"""AI Redistribution & Allocation Engine View with KEMSA theme."""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.data_service import get_redistribution_recommendations

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
        yaxis=grid_color and dict(gridcolor=grid_color, zerolinecolor=grid_color, color=text_color, tickfont=dict(color=text_color)),
        hoverlabel=dict(bgcolor="#020617" if is_dark else "#0F172A", font_size=12, font_family="Plus Jakarta Sans, sans-serif", font_color="#FFFFFF")
    )


def render_redistribution_view(county: str = "ALL", category: str = "ALL", theme: str = "light"):
    """Renders active surplus-to-shortage transfer recommendations and logistics cost analysis."""
    layout = get_chart_layout(theme)
    df_chains = get_redistribution_recommendations(county=county, category=category, top_n=50)

    # 1. Logistics Distance vs Cost Scatter
    if not df_chains.empty:
        fig_scatter = px.scatter(
            df_chains,
            x="avg_distance_km",
            y="total_transport_cost",
            size="total_recommended_units",
            color="dest_stockout_days",
            hover_name="commodity_name",
            hover_data=["source_facility_name", "destination_facility_name", "total_recommended_units"],
            color_continuous_scale=["#10B981", "#0EA5E9", "#6366F1"],
            title="<b>Redistribution Logistics (Size = Recommended Units, Color = Averted Stockout Days)</b>",
            labels={"avg_distance_km": "Transfer Distance (km)", "total_transport_cost": "Total Transport Cost (KES)", "dest_stockout_days": "Averted Days"}
        )
        fig_scatter.update_layout(**layout, height=360)

        # 2. Top Commodity Transfer Volumes
        top_com = df_chains.groupby("commodity_name")["total_recommended_units"].sum().reset_index()
        fig_bar = px.bar(
            top_com.sort_values("total_recommended_units", ascending=False).head(10),
            x="total_recommended_units",
            y="commodity_name",
            orientation="h",
            text="total_recommended_units",
            color="total_recommended_units",
            color_continuous_scale=["#E0F2FE", "#0EA5E9", "#0F172A"] if theme != "dark" else ["#0F172A", "#0EA5E9", "#38BDF8"],
            title="<b>Top 10 Reallocated Commodities by Unit Volume</b>",
            labels={"total_recommended_units": "Recommended Transfer Units", "commodity_name": "Commodity"}
        )
        fig_bar.update_layout(**layout, height=360)
        fig_bar.update_yaxes(categoryorder="total ascending")
        fig_bar.update_traces(textposition="outside")

        # 3. Chains Table
        chains_table = dbc.Table.from_dataframe(
            df_chains.head(20).rename(columns={
                "commodity_name": "Commodity",
                "source_facility_name": "Surplus Source Facility",
                "source_county": "Source County",
                "destination_facility_name": "Shortage Destination Facility",
                "destination_county": "Dest County",
                "total_recommended_units": "Units to Transfer",
                "avg_distance_km": "Distance (km)",
                "total_transport_cost": "Transport Cost (KES)",
                "dest_stockout_days": "Averted Stockout Days"
            }),
            striped=True,
            bordered=False,
            hover=True,
            responsive=True,
            className="table align-middle mb-0 font-sans"
        )
    else:
        fig_scatter = go.Figure().add_annotation(text="No Redistribution Recommendations Matching Filters", showarrow=False)
        fig_bar = go.Figure().add_annotation(text="No Data", showarrow=False)
        chains_table = html.P("No active surplus-to-shortage transfer chains for the selected filters.", className="text-muted p-3 mb-0")

    return html.Div([
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #10B981 0%, #0EA5E9 100%)"}),
                    dbc.CardBody(dcc.Graph(figure=fig_scatter, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card kemsa-chart-card mb-4 shadow-sm"),
                lg=6, sm=12
            ),
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #6366F1 0%, #38BDF8 100%)"}),
                    dbc.CardBody(dcc.Graph(figure=fig_bar, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card kemsa-chart-card mb-4 shadow-sm"),
                lg=6, sm=12
            ),
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #10B981 0%, #003399 100%)"}),
                    dbc.CardHeader([
                        html.Div([
                            html.Span("Active AI Allocation & Inter-Facility Redistribution Transfer Orders", className="fw-bold fs-6 me-2"),
                            html.Span("OPTIMIZATION ENGINE", className="badge kemsa-badge-green small fw-semibold")
                        ], className="d-flex align-items-center"),
                        dbc.Button(
                            [html.I(className="bi bi-download me-2"), "Export Manifest (CSV)"],
                            id="btn-export-redistribution",
                            color="success",
                            size="sm",
                            className="shadow-sm font-sans fw-semibold"
                        )
                    ], className="py-3 px-4 border-bottom bg-transparent d-flex justify-content-between align-items-center"),
                    dbc.CardBody(chains_table, className="p-0")
                ], className="kemsa-card mb-4 overflow-hidden shadow-sm"),
                lg=12
            )
        ]),
        dcc.Download(id="download-redistribution-csv")
    ])
