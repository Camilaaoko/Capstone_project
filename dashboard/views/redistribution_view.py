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
    text_color = "#FFFFFF" if is_dark else "#1E293B"
    grid_color = "rgba(255, 255, 255, 0.12)" if is_dark else "#E2E8F0"
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


def render_redistribution_view(county: str = "ALL", category: str = "ALL", theme: str = "light"):
    """Renders active surplus-to-shortage transfer recommendations, KPIs, and logistics analysis."""
    layout = get_chart_layout(theme)
    is_dark = theme == "dark"
    card_bg = "#1E293B" if is_dark else "#FFFFFF"
    border_color = "rgba(255, 255, 255, 0.1)" if is_dark else "#E2E8F0"
    text_muted_class = "text-light-50" if is_dark else "text-muted"

    df_chains = get_redistribution_recommendations(county=county, category=category, top_n=100)

    # 1. KPI Summary Cards
    if not df_chains.empty:
        total_corridors = len(df_chains)
        total_units = df_chains["total_recommended_units"].sum()
        total_cost = df_chains["total_transport_cost"].sum()
        avg_dist = df_chains["avg_distance_km"].mean()
        averted_days = int(df_chains["dest_stockout_days"].sum())
    else:
        total_corridors = 0
        total_units = 0
        total_cost = 0
        avg_dist = 0
        averted_days = 0

    kpi_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Span("Active Transfer Corridors", className=f"small text-uppercase fw-bold {text_muted_class}"),
                        html.I(className="bi bi-shuffle text-primary fs-5")
                    ], className="d-flex justify-content-between align-items-center mb-2"),
                    html.H3(f"{total_corridors:,}", className="fw-bolder mb-0 text-primary"),
                    html.Small("Surplus-to-shortage pairs", className="text-primary small mt-1 d-block")
                ], className="p-3")
            ], className="shadow-sm border-0 h-100", style={"backgroundColor": card_bg, "borderRadius": "10px", "borderLeft": "4px solid #0EA5E9"})
        ], md=3, sm=6, className="mb-3"),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Span("Units to Reallocate", className=f"small text-uppercase fw-bold {text_muted_class}"),
                        html.I(className="bi bi-box-arrow-right text-success fs-5")
                    ], className="d-flex justify-content-between align-items-center mb-2"),
                    html.H3(f"{total_units:,.0f}", className="fw-bolder mb-0 text-success"),
                    html.Small("Diverted from expiry risk", className="text-success small mt-1 d-block")
                ], className="p-3")
            ], className="shadow-sm border-0 h-100", style={"backgroundColor": card_bg, "borderRadius": "10px", "borderLeft": "4px solid #10B981"})
        ], md=3, sm=6, className="mb-3"),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Span("Stockout Days Averted", className=f"small text-uppercase fw-bold {text_muted_class}"),
                        html.I(className="bi bi-shield-check text-warning fs-5")
                    ], className="d-flex justify-content-between align-items-center mb-2"),
                    html.H3(f"{averted_days:,} days", className="fw-bolder mb-0 text-warning"),
                    html.Small("Cumulative patient protection", className="text-warning small mt-1 d-block")
                ], className="p-3")
            ], className="shadow-sm border-0 h-100", style={"backgroundColor": card_bg, "borderRadius": "10px", "borderLeft": "4px solid #F59E0B"})
        ], md=3, sm=6, className="mb-3"),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Span("Avg Transfer Distance", className=f"small text-uppercase fw-bold {text_muted_class}"),
                        html.I(className="bi bi-geo-alt-fill text-info fs-5")
                    ], className="d-flex justify-content-between align-items-center mb-2"),
                    html.H3(f"{avg_dist:.1f} km", className="fw-bolder mb-0 text-info"),
                    html.Small(f"Est. Total Cost: KES {total_cost:,.0f}", className="text-info small mt-1 d-block")
                ], className="p-3")
            ], className="shadow-sm border-0 h-100", style={"backgroundColor": card_bg, "borderRadius": "10px", "borderLeft": "4px solid #6366F1"})
        ], md=3, sm=6, className="mb-3")
    ])

    # 2. Logistics Distance vs Cost Scatter
    if not df_chains.empty:
        fig_scatter = px.scatter(
            df_chains,
            x="avg_distance_km",
            y="total_transport_cost",
            size="total_recommended_units",
            color="dest_stockout_days",
            hover_name="commodity_name",
            hover_data={
                "source_facility_name": True,
                "destination_facility_name": True,
                "total_recommended_units": ":,.0f",
                "avg_distance_km": ":.1f",
                "total_transport_cost": ":,.0f",
                "dest_stockout_days": True
            },
            color_continuous_scale=["#10B981", "#0EA5E9", "#6366F1", "#EF4444"],
            title="<b>Redistribution Logistics (Size = Recommended Units, Color = Averted Stockout Days)</b>",
            labels={
                "avg_distance_km": "Transfer Distance (km)",
                "total_transport_cost": "Transport Cost (KES)",
                "dest_stockout_days": "Averted Days",
                "source_facility_name": "Source Facility",
                "destination_facility_name": "Dest Facility"
            }
        )
        fig_scatter.update_layout(**layout, height=360)

        # 3. Top Commodity Transfer Volumes
        top_com = df_chains.groupby("commodity_name")["total_recommended_units"].sum().reset_index()
        fig_bar = px.bar(
            top_com.sort_values("total_recommended_units", ascending=True).tail(10),
            x="total_recommended_units",
            y="commodity_name",
            orientation="h",
            text="total_recommended_units",
            color="total_recommended_units",
            color_continuous_scale=["#0EA5E9", "#10B981"],
            title="<b>Top 10 Reallocated Commodities by Unit Volume</b>",
            labels={"total_recommended_units": "Recommended Transfer Units", "commodity_name": "Commodity"}
        )
        fig_bar.update_layout(**layout, height=360)
        fig_bar.update_traces(texttemplate="%{text:,.0f} units", textposition="outside")

        # 4. Chains Table
        rows = []
        for _, r in df_chains.head(25).iterrows():
            rows.append(html.Tr([
                html.Td(
                    html.Div([
                        html.Span(str(r.get("commodity_name", "")), className="fw-semibold d-block"),
                        html.Span(str(r.get("category", "")).replace("_", " ").title(), className="badge bg-secondary bg-opacity-10 text-secondary small", style={"fontSize": "0.72rem"})
                    ]),
                    className="align-middle"
                ),
                html.Td(
                    html.Div([
                        html.Span(f"🟢 {r.get('source_facility_name', '')}", className="fw-semibold small d-block"),
                        html.Small(f"📍 {r.get('source_county', '')} County", className="text-muted")
                    ]),
                    className="align-middle"
                ),
                html.Td(
                    html.Div([
                        html.Span(f"🔴 {r.get('destination_facility_name', '')}", className="fw-semibold small d-block"),
                        html.Small(f"📍 {r.get('destination_county', '')} County", className="text-muted")
                    ]),
                    className="align-middle"
                ),
                html.Td(
                    html.Span(f"{float(r.get('total_recommended_units', 0)):,.0f}", className="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 px-2 py-1 fw-bold"),
                    className="align-middle text-center"
                ),
                html.Td(f"{float(r.get('avg_distance_km', 0)):.1f} km", className="align-middle text-center small"),
                html.Td(f"KES {float(r.get('total_transport_cost', 0)):,.0f}", className="align-middle text-end small fw-semibold"),
                html.Td(
                    html.Span(f"{int(r.get('dest_stockout_days', 0))} days", className="badge bg-warning bg-opacity-10 text-warning border border-warning border-opacity-25 px-2 py-1 fw-semibold"),
                    className="align-middle text-center"
                )
            ]))

        table_header = html.Thead(
            html.Tr([
                html.Th("Commodity & Category", className="border-0 small text-uppercase fw-bold"),
                html.Th("Surplus Source Facility", className="border-0 small text-uppercase fw-bold"),
                html.Th("Shortage Destination Facility", className="border-0 small text-uppercase fw-bold"),
                html.Th("Units to Transfer", className="border-0 small text-uppercase fw-bold text-center"),
                html.Th("Distance", className="border-0 small text-uppercase fw-bold text-center"),
                html.Th("Transport Cost", className="border-0 small text-uppercase fw-bold text-end"),
                html.Th("Averted Stockout", className="border-0 small text-uppercase fw-bold text-center")
            ]),
            className="bg-light bg-opacity-50 border-bottom" if not is_dark else "bg-dark bg-opacity-50 border-bottom border-secondary"
        )

        chains_table = html.Div([
            dbc.Table(
                [table_header, html.Tbody(rows)],
                striped=True,
                bordered=False,
                hover=True,
                responsive=True,
                className="table align-middle mb-0"
            )
        ], style={"maxHeight": "460px", "overflowY": "auto"})
    else:
        fig_scatter = go.Figure().add_annotation(text="No Redistribution Recommendations Matching Filters", showarrow=False)
        fig_bar = go.Figure().add_annotation(text="No Data", showarrow=False)
        chains_table = html.P("No active surplus-to-shortage transfer chains for the selected filters.", className="text-muted p-4 mb-0 text-center")

    return html.Div([
        # Metric Cards Deck
        kpi_cards,

        # Charts Row
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

        # Recommendations Table Card
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

