"""County & Geographic Intelligence View for County Health Directors."""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.data_service import get_county_summary, get_facility_locations

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


def render_county_view(county: str = "ALL", theme: str = "light"):
    """Renders maps and charts for the County & Geographic View with KEMSA styling."""
    layout = get_chart_layout(theme)
    is_dark = theme == "dark"
    grid_color = "rgba(255, 255, 255, 0.10)" if is_dark else "#F1F5F9"

    # 1. County Stockout Summary
    df_county = get_county_summary()
    if not df_county.empty:
        fig_county = px.bar(
            df_county,
            x="county",
            y="stockout_days",
            color="facilities_with_stockouts",
            text="stockout_days",
            color_continuous_scale=["#FCA5A5", "#EF4444", "#991B1B"],
            title="<b>Stockout Days by County (Color = Impacted Facilities Count)</b>",
            labels={"stockout_days": "Stockout Days", "county": "County", "facilities_with_stockouts": "Impacted Facilities"}
        )
        fig_county.update_layout(**layout, height=380)
        fig_county.update_traces(textposition="outside")
    else:
        fig_county = go.Figure().add_annotation(text="No County Data", showarrow=False)

    # 2. Geospatial Facility Distribution Map
    df_loc = get_facility_locations(county=county)
    if not df_loc.empty:
        fig_map = px.scatter(
            df_loc,
            x="longitude",
            y="latitude",
            color="total_stockout_days",
            size="average_daily_patient_visits",
            hover_name="facility_name",
            hover_data=["county", "sub_county", "facility_type", "facility_size_tier", "total_stockout_days"],
            color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
            title="<b>Geospatial Health Facility Network (Size = Daily Visits, Color = Stockout Days)</b>",
            labels={"longitude": "Longitude", "latitude": "Latitude", "total_stockout_days": "Stockout Days"}
        )
        fig_map.update_layout(**layout, height=380)
        fig_map.update_xaxes(showgrid=True, zeroline=False, gridcolor=grid_color)
        fig_map.update_yaxes(showgrid=True, zeroline=False, gridcolor=grid_color)
    else:
        fig_map = go.Figure().add_annotation(text="No GPS Coordinates Available", showarrow=False)

    # 3. County Summary Table
    county_table = dbc.Table.from_dataframe(
        df_county.head(15).rename(columns={
            "county": "County Name",
            "stockout_days": "Total Stockout Days",
            "facilities_with_stockouts": "Facilities with Stockouts",
            "commodities_impacted": "Commodities Affected",
            "units_short": "Estimated Units Short"
        }),
        striped=True,
        bordered=False,
        hover=True,
        responsive=True,
        className="table align-middle mb-0"
    )

    return html.Div([
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #EF4444 0%, #F87171 100%)"}),
                    dbc.CardBody(dcc.Graph(figure=fig_county, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card kemsa-chart-card mb-4 shadow-sm"),
                lg=6, sm=12
            ),
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #0EA5E9 0%, #38BDF8 100%)"}),
                    dbc.CardBody(dcc.Graph(figure=fig_map, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card kemsa-chart-card mb-4 shadow-sm"),
                lg=6, sm=12
            ),
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #003399 0%, #10B981 100%)"}),
                    dbc.CardHeader(
                        html.Div([
                            html.Span("County Stockout & Commodity Deficit Breakdown", className="fw-bold fs-6"),
                            html.Span("REGIONAL AUDIT", className="badge kemsa-badge-navy small fw-semibold")
                        ], className="d-flex justify-content-between align-items-center"),
                        className="py-3 px-4 border-bottom bg-transparent"
                    ),
                    dbc.CardBody(county_table, className="p-0")
                ], className="kemsa-card mb-4 overflow-hidden shadow-sm"),
                lg=12
            )
        ])
    ])
