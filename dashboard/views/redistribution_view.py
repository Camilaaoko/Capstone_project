"""AI Redistribution & Allocation Engine View."""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.data_service import get_redistribution_recommendations


def render_redistribution_view(county: str = "ALL", category: str = "ALL"):
    """Renders active surplus-to-shortage transfer recommendations and logistics cost analysis."""
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
            color_continuous_scale="Viridis",
            title="<b>Redistribution Logistics (Size = Recommended Units, Color = Averted Stockout Days)</b>",
            labels={"avg_distance_km": "Transfer Distance (km)", "total_transport_cost": "Total Transport Cost (KES)", "dest_stockout_days": "Averted Days"}
        )
        fig_scatter.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=360)

        # 2. Top Commodity Transfer Volumes
        top_com = df_chains.groupby("commodity_name")["total_recommended_units"].sum().reset_index()
        fig_bar = px.bar(
            top_com.sort_values("total_recommended_units", ascending=False).head(10),
            x="total_recommended_units",
            y="commodity_name",
            orientation="h",
            text="total_recommended_units",
            color="total_recommended_units",
            color_continuous_scale="Blues",
            title="<b>Top 10 Reallocated Commodities by Unit Volume</b>",
            labels={"total_recommended_units": "Recommended Transfer Units", "commodity_name": "Commodity"}
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=40, b=20), height=360)
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
            bordered=True,
            hover=True,
            responsive=True,
            className="small shadow-sm"
        )
    else:
        fig_scatter = go.Figure().add_annotation(text="No Redistribution Recommendations Matching Filters", showarrow=False)
        fig_bar = go.Figure().add_annotation(text="No Data", showarrow=False)
        chains_table = html.P("No active surplus-to-shortage transfer chains for the selected filters.", className="text-muted")

    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_scatter, config={"displayModeBar": False}))], className="shadow-sm border-0 mb-4"), lg=6, sm=12),
            dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_bar, config={"displayModeBar": False}))], className="shadow-sm border-0 mb-4"), lg=6, sm=12),
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.Span("🔄 Active AI Allocation & Inter-Facility Redistribution Transfer Orders", className="fw-bold"),
                        dbc.Button(
                            [html.I(className="bi bi-download me-2"), "Export Manifest (CSV)"],
                            id="btn-export-redistribution",
                            color="success",
                            size="sm",
                            className="shadow-sm"
                        )
                    ], className="bg-white d-flex justify-content-between align-items-center"),
                    dbc.CardBody(chains_table)
                ], className="shadow-sm border-0 mb-4"),
                lg=12
            )
        ]),
        dcc.Download(id="download-redistribution-csv")
    ])

