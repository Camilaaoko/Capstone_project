"""County & Geographic Intelligence View for County Health Directors."""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.data_service import get_county_summary, get_facility_locations


def render_county_view(county: str = "ALL"):
    """Renders maps and charts for the County & Geographic View."""
    # 1. County Stockout Summary
    df_county = get_county_summary()
    if not df_county.empty:
        fig_county = px.bar(
            df_county,
            x="county",
            y="stockout_days",
            color="facilities_with_stockouts",
            text="stockout_days",
            color_continuous_scale="Reds",
            title="<b>Stockout Days by County (Color = Impacted Facilities Count)</b>",
            labels={"stockout_days": "Stockout Days", "county": "County", "facilities_with_stockouts": "Impacted Facilities"}
        )
        fig_county.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=380)
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
            color_continuous_scale="Turbo",
            title="<b>Geospatial Health Facility Network (Size = Daily Visits, Color = Stockout Days)</b>",
            labels={"longitude": "Longitude", "latitude": "Latitude", "total_stockout_days": "Stockout Days"}
        )
        fig_map.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            height=380,
            xaxis=dict(showgrid=True, zeroline=False),
            yaxis=dict(showgrid=True, zeroline=False)
        )
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
        bordered=True,
        hover=True,
        responsive=True,
        className="small shadow-sm"
    )

    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_county, config={"displayModeBar": False}))], className="shadow-sm border-0 mb-4"), lg=6, sm=12),
            dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_map, config={"displayModeBar": False}))], className="shadow-sm border-0 mb-4"), lg=6, sm=12),
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("🏛️ County Stockout & Deficit Breakdown", className="fw-bold bg-white"),
                    dbc.CardBody(county_table)
                ], className="shadow-sm border-0 mb-4"),
                lg=12
            )
        ])
    ])

