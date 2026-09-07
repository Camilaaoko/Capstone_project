"""County & Geographic Intelligence View with Interactive Map of Kenya and Tappable Location Dossier."""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional

from dashboard.data_service import (
    get_county_summary,
    get_facility_locations,
    get_warehouse_locations,
    get_facility_detail_stats,
    get_warehouse_detail_stats
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


def create_kenya_map_figure(county: str = "ALL", category: str = "ALL", tier: str = "ALL", theme: str = "light") -> go.Figure:
    """Renders high-resolution Map of Kenya with OpenStreetMap tiles, warehouses, and tappable facility points."""
    df_loc = get_facility_locations(county=county, category=category, tier=tier)
    df_wh = get_warehouse_locations()
    
    is_dark = theme == "dark"
    map_style = "carto-darkmatter" if is_dark else "open-street-map"
    
    if county != "ALL" and not df_loc.empty:
        center_lat = float(df_loc["latitude"].mean())
        center_lon = float(df_loc["longitude"].mean())
        zoom = 8.2
    else:
        # Default center of Kenya
        center_lat = 0.35
        center_lon = 37.85
        zoom = 5.6
        
    fig = go.Figure()
    
    # 1. KEMSA Supply Depots / Warehouses Layer (Gold/Amber Markers)
    if not df_wh.empty:
        wh_hover = []
        for _, r in df_wh.iterrows():
            try:
                cap_str = f"{float(r['storage_capacity_units']):,.0f} units"
            except Exception:
                cap_str = f"{r['storage_capacity_units']} units"
            wh_hover.append(
                f"<b>🏢 {r['warehouse_name']}</b><br>"
                f"Region: {r['region']} ({r['county']} County)<br>"
                f"Storage Capacity: {cap_str}<br>"
                f"Status: {r['warehouse_status']}<br>"
                f"<span style='color:#F59E0B; font-weight:bold;'>👉 Click depot marker to load depot dossier</span>"
                f"<extra></extra>"
            )
            
        fig.add_trace(go.Scattermap(
            lat=df_wh["latitude"],
            lon=df_wh["longitude"],
            mode="markers+text",
            marker=dict(
                size=16,
                color="#F59E0B"
            ),
            customdata=df_wh[["warehouse_id", "warehouse_name", "region", "county"]].values,
            text=df_wh["warehouse_name"].apply(lambda x: "📦 " + str(x).replace(" Regional Warehouse", "").replace(" National Central Warehouse", "")),
            textposition="top right",
            textfont=dict(size=10, color="#FFFFFF" if is_dark else "#1E293B", family="Plus Jakarta Sans, sans-serif"),
            name="KEMSA Warehouses / Depots",
            hovertext=wh_hover,
            hoverinfo="text"
        ))
        
    # 2. Health Facilities Layer (Tappable circles sized by visits, color by stockouts)
    if not df_loc.empty:
        df_loc["average_daily_patient_visits"] = pd.to_numeric(df_loc["average_daily_patient_visits"], errors="coerce").fillna(0)
        df_loc["total_stockout_days"] = pd.to_numeric(df_loc["total_stockout_days"], errors="coerce").fillna(0)
        df_loc["total_units_short"] = pd.to_numeric(df_loc["total_units_short"], errors="coerce").fillna(0)
        df_loc["commodities_short_count"] = pd.to_numeric(df_loc["commodities_short_count"], errors="coerce").fillna(0)
        
        max_visits = max(df_loc["average_daily_patient_visits"].max(), 1)
        sizes = 10 + (df_loc["average_daily_patient_visits"] / max_visits) * 24
        
        customdata = df_loc[[
            "facility_id", "facility_name", "county", "sub_county", 
            "facility_type", "facility_level", "facility_size_tier", 
            "bed_capacity", "average_daily_patient_visits", 
            "total_stockout_days", "total_units_short", "commodities_short_count"
        ]].values
        
        hovertemplate = (
            "<b>🏥 %{customdata[1]}</b><br>"
            "📍 %{customdata[2]} County | %{customdata[3]}<br>"
            "🏷️ Level: %{customdata[5]} (%{customdata[6]})<br>"
            "👥 Daily Patient Footfall: %{customdata[8]:,.0f}<br>"
            "🛏️ Beds: %{customdata[7]}<br>"
            "<hr style='margin:4px 0'>"
            "⚠️ <b>Total Stockout Days: %{customdata[9]}</b><br>"
            "📦 Units Short: %{customdata[10]:,.0f}<br>"
            "💊 Deficit Items: %{customdata[11]}<br>"
            "<span style='color:#0EA5E9; font-weight:bold;'>👉 Click marker to load live statistics dossier</span>"
            "<extra></extra>"
        )
        
        fig.add_trace(go.Scattermap(
            lat=df_loc["latitude"],
            lon=df_loc["longitude"],
            mode="markers",
            marker=dict(
                size=sizes,
                color=df_loc["total_stockout_days"],
                colorscale=[
                    [0.0, "#10B981"],   # Green (low stockouts)
                    [0.35, "#F59E0B"],  # Amber (moderate)
                    [0.7, "#EF4444"],   # Red (high)
                    [1.0, "#7F1D1D"]    # Dark Crimson (severe)
                ],
                cmin=0,
                cmax=max(df_loc["total_stockout_days"].max(), 1),
                colorbar=dict(
                    title=dict(text="Stockout<br>Days", font=dict(size=11, color="#FFFFFF" if is_dark else "#1E293B")),
                    thickness=12,
                    len=0.7,
                    x=1.02,
                    tickfont=dict(size=10, color="#FFFFFF" if is_dark else "#1E293B")
                ),
                opacity=0.92
            ),
            customdata=customdata,
            hovertemplate=hovertemplate,
            name="Health Facilities"
        ))
        
    fig.update_layout(
        map=dict(
            style=map_style,
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=480,
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.02,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(15, 23, 42, 0.85)" if is_dark else "rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(255,255,255,0.2)" if is_dark else "#E2E8F0",
            borderwidth=1,
            font=dict(size=11, color="#FFFFFF" if is_dark else "#0F172A")
        ),
        hoverlabel=dict(
            bgcolor="#0F172A" if is_dark else "#1E293B",
            font_size=12,
            font_family="Plus Jakarta Sans, sans-serif",
            font_color="#FFFFFF"
        )
    )
    return fig


def render_facility_dossier_panel(facility_id: Optional[str] = None, county: str = "ALL", category: str = "ALL", tier: str = "ALL", theme: str = "light"):
    """Builds the interactive location intelligence dossier panel for tapped facilities or default overview."""
    is_dark = theme == "dark"
    bg_subtle = "#1E293B" if is_dark else "#F8FAFC"
    border_color = "rgba(255, 255, 255, 0.1)" if is_dark else "#E2E8F0"
    
    if not facility_id:
        # Default Overview State (No facility tapped yet)
        df_facs = get_facility_locations(county=county, category=category, tier=tier)
        total_facs = len(df_facs)
        total_visits = df_facs["average_daily_patient_visits"].sum() if not df_facs.empty else 0
        total_sout = df_facs["total_stockout_days"].sum() if not df_facs.empty else 0
        facs_with_sout = len(df_facs[df_facs["total_stockout_days"] > 0]) if not df_facs.empty else 0
        
        scope_title = f"{county} County" if county != "ALL" else "Kenya National Overview (47 Counties)"
        
        return dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.Div([
                        html.I(className="bi bi-geo-alt-fill text-primary me-2 fs-5"),
                        html.Span("Location Intelligence Dossier", className="fw-bold fs-6"),
                    ], className="d-flex align-items-center"),
                    html.Span("TAP INTERACTION READY", className="badge kemsa-badge-green small fw-semibold")
                ], className="d-flex justify-content-between align-items-center"),
                className="py-3 px-4 border-bottom bg-transparent"
            ),
            dbc.CardBody([
                html.Div([
                    html.Div([
                        html.I(className="bi bi-hand-index-thumb-fill text-info fs-1 mb-2 d-block"),
                        html.H5("Tap Any Facility on the Map", className="fw-bold mb-1"),
                        html.P(
                            "Click or tap any circular marker on the Map of Kenya to inspect live stockout diagnostics, "
                            "patient footfall volume, critical commodity shortages, expiry exposure, and AI redistribution transfers.",
                            className="small mb-3 text-muted"
                        ),
                    ], className="text-center p-3 rounded-3 mb-3", style={"background": bg_subtle, "border": f"1px dashed {border_color}"}),
                    
                    html.Div([
                        html.Span(f"Active Scope: {scope_title}", className="fw-bold small text-uppercase text-muted d-block mb-2"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Span("Monitored Facilities", className="small text-muted d-block", style={"fontSize": "0.75rem"}),
                                    html.Span(f"{total_facs:,}", className="fs-5 fw-bolder text-primary"),
                                ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                            ], xs=6, className="mb-2"),
                            dbc.Col([
                                html.Div([
                                    html.Span("Daily Patient Footfall", className="small text-muted d-block", style={"fontSize": "0.75rem"}),
                                    html.Span(f"{total_visits:,.0f}", className="fs-5 fw-bolder text-info"),
                                ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                            ], xs=6, className="mb-2"),
                            dbc.Col([
                                html.Div([
                                    html.Span("Stockout Days Burden", className="small text-muted d-block", style={"fontSize": "0.75rem"}),
                                    html.Span(f"{total_sout:,.0f} d", className="fs-5 fw-bolder text-danger"),
                                ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                            ], xs=6, className="mb-2"),
                            dbc.Col([
                                html.Div([
                                    html.Span("Facilities with Stockouts", className="small text-muted d-block", style={"fontSize": "0.75rem"}),
                                    html.Span(f"{facs_with_sout} / {total_facs}", className="fs-5 fw-bolder text-warning"),
                                ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                            ], xs=6, className="mb-2"),
                        ])
                    ])
                ])
            ], className="p-3")
        ], className="kemsa-card shadow-sm h-100")

    # Warehouse Depot Tapped
    if str(facility_id).startswith("WH"):
        wh_stats = get_warehouse_detail_stats(facility_id)
        if wh_stats and wh_stats.get("info"):
            w_info = wh_stats["info"]
            orders = wh_stats.get("orders", {})
            return dbc.Card([
                dbc.CardHeader(
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-box-seam text-warning me-2 fs-5"),
                            html.Span(w_info.get("warehouse_name", "KEMSA Depot"), className="fw-bold fs-6 text-truncate", style={"maxWidth": "230px"}),
                        ], className="d-flex align-items-center"),
                        dbc.Button(
                            [html.I(className="bi bi-arrow-counterclockwise me-1"), "Reset"],
                            id={"type": "btn-reset-dossier", "index": 0},
                            size="sm",
                            color="outline-secondary",
                            className="py-0 px-2 small"
                        )
                    ], className="d-flex justify-content-between align-items-center"),
                    className="py-2 px-3 border-bottom bg-transparent"
                ),
                dbc.CardBody([
                    html.Div([
                        dbc.Badge(f"{w_info.get('region', '')} Region", color="warning", className="me-1 px-2 py-1"),
                        dbc.Badge(f"{w_info.get('county', '')} Hub", color="primary", className="me-1 px-2 py-1"),
                        dbc.Badge(f"{w_info.get('warehouse_status', 'ACTIVE')}", color="success", className="px-2 py-1")
                    ], className="d-flex flex-wrap gap-1 mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Span("Storage Capacity", className="small text-muted d-block", style={"fontSize": "0.72rem"}),
                                html.Span(f"{float(w_info.get('storage_capacity_units', 0)):,.0f}", className="fw-bold text-warning fs-6"),
                            ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                        ], xs=6, className="mb-2"),
                        dbc.Col([
                            html.Div([
                                html.Span("Local Facilities Served", className="small text-muted d-block", style={"fontSize": "0.72rem"}),
                                html.Span(f"{wh_stats.get('facilities_served', 0)} Facilities", className="fw-bold text-info fs-6"),
                            ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                        ], xs=6, className="mb-2"),
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Span("Orders Fulfilled", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                                html.Span(f"{orders.get('total_orders', 0):,}", className="fw-bolder text-primary fs-6"),
                            ], className="p-2 rounded-2 text-center border-start border-3 border-primary", style={"background": bg_subtle})
                        ], xs=6, className="mb-2"),
                        dbc.Col([
                            html.Div([
                                html.Span("Units Dispatched", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                                html.Span(f"{orders.get('total_qty_fulfilled', 0):,}", className="fw-bolder text-success fs-6"),
                            ], className="p-2 rounded-2 text-center border-start border-3 border-success", style={"background": bg_subtle})
                        ], xs=6, className="mb-2"),
                    ])
                ], className="p-3")
            ], className="kemsa-card shadow-sm h-100")

    # Specific Facility Tapped
    stats = get_facility_detail_stats(facility_id)
    if not stats or not stats.get("info"):
        return html.Div("Facility data not found.", className="p-3 text-muted")
        
    info = stats["info"]
    stockouts_df = stats["stockouts"]
    expiry_df = stats["expiry"]
    redist_df = stats["redistribution"]
    
    # Header badges
    level_badge = dbc.Badge(f"{info.get('facility_level', 'Health Facility')}", color="primary", className="me-1 px-2 py-1")
    tier_badge = dbc.Badge(f"{info.get('facility_size_tier', 'Tier')} Tier", color="info", className="me-1 px-2 py-1")
    county_badge = dbc.Badge(f"{info.get('county', '')} County", color="secondary", className="me-1 px-2 py-1")
    
    # Shortages list/table
    shortages_view = []
    if not stockouts_df.empty:
        shortages_rows = []
        for _, row in stockouts_df.head(4).iterrows():
            shortages_rows.append(
                html.Tr([
                    html.Td([
                        html.Span(row["commodity_name"], className="fw-semibold small d-block"),
                        html.Span(str(row["category"]).replace("_", " ").title(), className="text-muted", style={"fontSize": "0.72rem"})
                    ]),
                    html.Td(f"{int(row['stockout_days'])}d", className="text-danger fw-bold small text-end"),
                    html.Td(f"{int(row['units_short']):,}", className="text-warning fw-bold small text-end"),
                ])
            )
        shortages_view = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Deficit Item", className="small text-muted py-1"),
                html.Th("Stockout", className="small text-muted py-1 text-end"),
                html.Th("Units Short", className="small text-muted py-1 text-end"),
            ])),
            html.Tbody(shortages_rows)
        ], hover=True, responsive=True, size="sm", className="mb-0")
    else:
        shortages_view = html.Div([
            html.I(className="bi bi-check-circle-fill text-success me-2"),
            html.Span("Zero Active Stockouts Reported", className="small text-success fw-semibold")
        ], className="p-2 text-center rounded-2", style={"background": bg_subtle})

    # AI Redistribution section
    redist_view = []
    if not redist_df.empty:
        r_items = []
        for _, r in redist_df.head(2).iterrows():
            is_donor = r["role"] == "SURPLUS DONOR"
            arrow_icon = "bi bi-arrow-up-right-circle-fill text-primary" if is_donor else "bi bi-arrow-down-left-circle-fill text-success"
            role_text = f"Supplying {r['partner_facility']}" if is_donor else f"Receiving from {r['partner_facility']}"
            
            # Safe formatting for units and distance
            units_val = r.get("total_recommended_units")
            units_str = f"{int(float(units_val)):,}" if units_val is not None and not pd.isna(units_val) else "0"
            dist_val = r.get("avg_distance_km")
            dist_str = f"{float(dist_val):.1f} km" if dist_val is not None and not pd.isna(dist_val) else "Regional"
            
            r_items.append(
                html.Div([
                    html.Div([
                        html.I(className=f"{arrow_icon} me-2 fs-6"),
                        html.Span(r["commodity_name"], className="fw-bold small"),
                    ], className="d-flex align-items-center"),
                    html.Div([
                        html.Span(f"{role_text} ({r['partner_county']})", className="text-muted small d-block", style={"fontSize": "0.74rem"}),
                        html.Span(f"Reallocated: {units_str} units • {dist_str}", className="fw-semibold small text-primary", style={"fontSize": "0.74rem"})
                    ], className="ps-4")
                ], className="p-2 mb-1 rounded-2 border", style={"background": bg_subtle})
            )
        redist_view = html.Div(r_items)
    else:
        redist_view = html.Div([
            html.Span("No active transfer chains currently routed for this facility.", className="small text-muted")
        ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})

    return dbc.Card([
        dbc.CardHeader(
            html.Div([
                html.Div([
                    html.I(className="bi bi-hospital-fill text-primary me-2 fs-5"),
                    html.Span(info.get("facility_name", "Facility Dossier"), className="fw-bold fs-6 text-truncate", style={"maxWidth": "230px"}),
                ], className="d-flex align-items-center"),
                dbc.Button(
                    [html.I(className="bi bi-arrow-counterclockwise me-1"), "Reset"],
                    id={"type": "btn-reset-dossier", "index": 0},
                    size="sm",
                    color="outline-secondary",
                    className="py-0 px-2 small"
                )
            ], className="d-flex justify-content-between align-items-center"),
            className="py-2 px-3 border-bottom bg-transparent"
        ),
        dbc.CardBody([
            # Meta tags
            html.Div([
                level_badge,
                tier_badge,
                county_badge,
                dbc.Badge(f"{info.get('sub_county', '')}", color="dark" if is_dark else "light", className="text-muted px-2 py-1 border")
            ], className="d-flex flex-wrap gap-1 mb-2"),
            
            # Operational capacity
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("Daily Patient Visits", className="small text-muted d-block", style={"fontSize": "0.72rem"}),
                        html.Span(f"{float(info.get('average_daily_patient_visits', 0)):,.0f}", className="fw-bold text-info fs-6"),
                    ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Span("Bed Capacity", className="small text-muted d-block", style={"fontSize": "0.72rem"}),
                        html.Span(f"{info.get('bed_capacity', 0)} Beds", className="fw-bold text-primary fs-6"),
                    ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
            ]),

            # 4 KPI Chips
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("Stockout Days", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                        html.Span(f"{stats['total_stockout_days']} d", className="fw-bolder text-danger fs-6"),
                    ], className="p-2 rounded-2 text-center border-start border-3 border-danger", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Span("Units Short", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                        html.Span(f"{stats['total_units_short']:,}", className="fw-bolder text-warning fs-6"),
                    ], className="p-2 rounded-2 text-center border-start border-3 border-warning", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Span("Expiry Risk", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                        html.Span(f"KES {stats['total_wastage_kes']:,.0f}", className="fw-bolder text-secondary fs-6"),
                    ], className="p-2 rounded-2 text-center border-start border-3 border-secondary", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Span("AI Transfers", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                        html.Span(f"{stats['total_transfers_count']} Chains", className="fw-bolder text-success fs-6"),
                    ], className="p-2 rounded-2 text-center border-start border-3 border-success", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
            ]),

            # Critical Shortages Table
            html.Div([
                html.Span("Top Deficit Commodities:", className="fw-bold small text-uppercase text-muted d-block mb-1", style={"fontSize": "0.75rem"}),
                shortages_view
            ], className="mb-2"),

            # AI Redistribution Corridor
            html.Div([
                html.Span("AI Redistribution Corridors:", className="fw-bold small text-uppercase text-muted d-block mb-1", style={"fontSize": "0.75rem"}),
                redist_view
            ])

        ], className="p-3")
    ], className="kemsa-card shadow-sm h-100")


    # Specific Facility Tapped
    stats = get_facility_detail_stats(facility_id)
    if not stats or not stats.get("info"):
        return html.Div("Facility data not found.", className="p-3 text-muted")
        
    info = stats["info"]
    stockouts_df = stats["stockouts"]
    expiry_df = stats["expiry"]
    redist_df = stats["redistribution"]
    
    # Header badges
    level_badge = dbc.Badge(f"{info.get('facility_level', 'Health Facility')}", color="primary", className="me-1 px-2 py-1")
    tier_badge = dbc.Badge(f"{info.get('facility_size_tier', 'Tier')} Tier", color="info", className="me-1 px-2 py-1")
    county_badge = dbc.Badge(f"{info.get('county', '')} County", color="secondary", className="me-1 px-2 py-1")
    
    # Shortages list/table
    shortages_view = []
    if not stockouts_df.empty:
        shortages_rows = []
        for _, row in stockouts_df.head(4).iterrows():
            shortages_rows.append(
                html.Tr([
                    html.Td([
                        html.Span(row["commodity_name"], className="fw-semibold small d-block"),
                        html.Span(str(row["category"]).replace("_", " ").title(), className="text-muted", style={"fontSize": "0.72rem"})
                    ]),
                    html.Td(f"{int(row['stockout_days'])}d", className="text-danger fw-bold small text-end"),
                    html.Td(f"{int(row['units_short']):,}", className="text-warning fw-bold small text-end"),
                ])
            )
        shortages_view = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Deficit Item", className="small text-muted py-1"),
                html.Th("Stockout", className="small text-muted py-1 text-end"),
                html.Th("Units Short", className="small text-muted py-1 text-end"),
            ])),
            html.Tbody(shortages_rows)
        ], hover=True, responsive=True, size="sm", className="mb-0")
    else:
        shortages_view = html.Div([
            html.I(className="bi bi-check-circle-fill text-success me-2"),
            html.Span("Zero Active Stockouts Reported", className="small text-success fw-semibold")
        ], className="p-2 text-center rounded-2", style={"background": bg_subtle})

    # AI Redistribution section
    redist_view = []
    if not redist_df.empty:
        r_items = []
        for _, r in redist_df.head(2).iterrows():
            is_donor = r["role"] == "SURPLUS DONOR"
            arrow_icon = "bi bi-arrow-up-right-circle-fill text-primary" if is_donor else "bi bi-arrow-down-left-circle-fill text-success"
            role_text = f"Supplying {r['partner_facility']}" if is_donor else f"Receiving from {r['partner_facility']}"
            r_items.append(
                html.Div([
                    html.Div([
                        html.I(className=f"{arrow_icon} me-2 fs-6"),
                        html.Span(r["commodity_name"], className="fw-bold small"),
                    ], className="d-flex align-items-center"),
                    html.Div([
                        html.Span(f"{role_text} ({r['partner_county']})", className="text-muted small d-block", style={"fontSize": "0.74rem"}),
                        html.Span(f"Reallocated: {int(r['total_recommended_units']):,} units • {r['avg_distance_km']:.1f} km", className="fw-semibold small text-primary", style={"fontSize": "0.74rem"})
                    ], className="ps-4")
                ], className="p-2 mb-1 rounded-2 border", style={"background": bg_subtle})
            )
        redist_view = html.Div(r_items)
    else:
        redist_view = html.Div([
            html.Span("No active transfer chains currently routed for this facility.", className="small text-muted")
        ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})

    return dbc.Card([
        dbc.CardHeader(
            html.Div([
                html.Div([
                    html.I(className="bi bi-hospital-fill text-primary me-2 fs-5"),
                    html.Span(info.get("facility_name", "Facility Dossier"), className="fw-bold fs-6 text-truncate", style={"maxWidth": "230px"}),
                ], className="d-flex align-items-center"),
                dbc.Button(
                    [html.I(className="bi bi-arrow-counterclockwise me-1"), "Reset"],
                    id={"type": "btn-reset-dossier", "index": 0},
                    size="sm",
                    color="outline-secondary",
                    className="py-0 px-2 small"
                )
            ], className="d-flex justify-content-between align-items-center"),
            className="py-2 px-3 border-bottom bg-transparent"
        ),
        dbc.CardBody([
            # Meta tags
            html.Div([
                level_badge,
                tier_badge,
                county_badge,
                dbc.Badge(f"{info.get('sub_county', '')}", color="dark" if is_dark else "light", className="text-muted px-2 py-1 border")
            ], className="d-flex flex-wrap gap-1 mb-2"),
            
            # Operational capacity
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("Daily Patient Visits", className="small text-muted d-block", style={"fontSize": "0.72rem"}),
                        html.Span(f"{float(info.get('average_daily_patient_visits', 0)):,.0f}", className="fw-bold text-info fs-6"),
                    ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Span("Bed Capacity", className="small text-muted d-block", style={"fontSize": "0.72rem"}),
                        html.Span(f"{info.get('bed_capacity', 0)} Beds", className="fw-bold text-primary fs-6"),
                    ], className="p-2 rounded-2 text-center", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
            ]),

            # 4 KPI Chips
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("Stockout Days", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                        html.Span(f"{stats['total_stockout_days']} d", className="fw-bolder text-danger fs-6"),
                    ], className="p-2 rounded-2 text-center border-start border-3 border-danger", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Span("Units Short", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                        html.Span(f"{stats['total_units_short']:,}", className="fw-bolder text-warning fs-6"),
                    ], className="p-2 rounded-2 text-center border-start border-3 border-warning", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Span("Expiry Risk", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                        html.Span(f"KES {stats['total_wastage_kes']:,.0f}", className="fw-bolder text-secondary fs-6"),
                    ], className="p-2 rounded-2 text-center border-start border-3 border-secondary", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Span("AI Transfers", className="small text-muted d-block", style={"fontSize": "0.7rem"}),
                        html.Span(f"{stats['total_transfers_count']} Chains", className="fw-bolder text-success fs-6"),
                    ], className="p-2 rounded-2 text-center border-start border-3 border-success", style={"background": bg_subtle})
                ], xs=6, className="mb-2"),
            ]),

            # Critical Shortages Table
            html.Div([
                html.Span("Top Deficit Commodities:", className="fw-bold small text-uppercase text-muted d-block mb-1", style={"fontSize": "0.75rem"}),
                shortages_view
            ], className="mb-2"),

            # AI Redistribution Corridor
            html.Div([
                html.Span("AI Redistribution Corridors:", className="fw-bold small text-uppercase text-muted d-block mb-1", style={"fontSize": "0.75rem"}),
                redist_view
            ])

        ], className="p-3")
    ], className="kemsa-card shadow-sm h-100")


def render_county_view(county: str = "ALL", category: str = "ALL", tier: str = "ALL", theme: str = "light", selected_facility_id: Optional[str] = None):
    """Renders the comprehensive County & Geographic View with interactive Map of Kenya and tappable dossier."""
    layout = get_chart_layout(theme)

    # 1. Generate Map of Kenya Figure
    fig_map = create_kenya_map_figure(county=county, category=category, tier=tier, theme=theme)

    # 2. Sub-County or County Stockout Summary Bar Chart
    df_county = get_county_summary(county=county, category=category, tier=tier)
    if not df_county.empty:
        chart_title_scope = f"Sub-Counties in {county}" if county != "ALL" else "Counties Nationally"
        fig_county = px.bar(
            df_county,
            x="location_name",
            y="stockout_days",
            color="facilities_with_stockouts",
            text="stockout_days",
            color_continuous_scale=["#FCA5A5", "#EF4444", "#991B1B"],
            title=f"<b>Stockout Severity by {chart_title_scope}</b>",
            labels={"stockout_days": "Stockout Days", "location_name": "Jurisdiction", "facilities_with_stockouts": "Impacted Facilities"}
        )
        county_chart_layout = dict(**layout)
        county_chart_layout["margin"] = dict(l=20, r=20, t=40, b=80)
        county_chart_layout["height"] = 380
        fig_county.update_layout(**county_chart_layout, xaxis_tickangle=-45)
        fig_county.update_traces(textposition="outside")
    else:
        fig_county = go.Figure().add_annotation(text="No Regional Stockout Data Available", showarrow=False)

    # 3. Regional Audit Deficit Table
    if not df_county.empty:
        col_label = "Sub-County Name" if county != "ALL" else "County Name"
        table_df = df_county.head(15).rename(columns={
            "location_name": col_label,
            "stockout_days": "Total Stockout Days",
            "facilities_with_stockouts": "Facilities Affected",
            "commodities_impacted": "Deficit Commodities",
            "units_short": "Estimated Units Short"
        })
        if "county" in table_df.columns and county != "ALL":
            table_df = table_df.drop(columns=["county"])
            
        county_table = dbc.Table.from_dataframe(
            table_df,
            striped=True,
            bordered=False,
            hover=True,
            responsive=True,
            className="table align-middle mb-0 font-sans"
        )
    else:
        county_table = html.P("No audit data matching the selected filters.", className="text-muted p-3 mb-0")

    return html.Div([
        # Top Row: Interactive Map of Kenya + Location Intelligence Dossier
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #10B981 0%, #0EA5E9 50%, #6366F1 100%)"}),
                    dbc.CardHeader(
                        html.Div([
                            html.Div([
                                html.I(className="bi bi-map-fill text-primary me-2"),
                                html.Span("Geospatial Supply Chain Network • Map of Kenya", className="fw-bold fs-6"),
                            ], className="d-flex align-items-center"),
                            html.Span("OPENSTREETMAP TILES • TAPPABLE DATA POINTS", className="badge kemsa-badge-green small fw-semibold")
                        ], className="d-flex justify-content-between align-items-center"),
                        className="py-2 px-3 border-bottom bg-transparent"
                    ),
                    dbc.CardBody([
                        dcc.Graph(
                            id="county-map-graph",
                            figure=fig_map,
                            config={"displayModeBar": True, "scrollZoom": True, "displaylogo": False}
                        ),
                        html.Div([
                            html.Small(
                                "💡 Interactive Mode: Tap or click any circular health facility marker to inspect live stockout statistics, "
                                "bed capacity, patient footfall, and AI redistribution links in the side dossier.",
                                className="text-muted fst-italic"
                            )
                        ], className="px-2 pt-2")
                    ], className="p-2")
                ], className="kemsa-card mb-4 shadow-sm"),
                lg=7, sm=12
            ),
            dbc.Col(
                html.Div(
                    render_facility_dossier_panel(selected_facility_id, county, category, tier, theme),
                    id="facility-dossier-container",
                    className="h-100 mb-4"
                ),
                lg=5, sm=12
            ),
        ]),

        # Bottom Row: Stockout Burden Ranking + Regional Audit Table
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #EF4444 0%, #F87171 100%)"}),
                    dbc.CardHeader(
                        html.Div([
                            html.Span("Regional Stockout Severity Ranking", className="fw-bold fs-6"),
                            html.Span("SEVERITY INDEX", className="badge kemsa-badge-navy small fw-semibold")
                        ], className="d-flex justify-content-between align-items-center"),
                        className="py-2 px-3 border-bottom bg-transparent"
                    ),
                    dbc.CardBody(dcc.Graph(figure=fig_county, config={"displayModeBar": False}), className="p-3")
                ], className="kemsa-card kemsa-chart-card mb-4 shadow-sm"),
                lg=6, sm=12
            ),
            dbc.Col(
                dbc.Card([
                    html.Div(style={"height": "3px", "background": "linear-gradient(90deg, #003399 0%, #10B981 100%)"}),
                    dbc.CardHeader(
                        html.Div([
                            html.Span("Regional Stockout & Commodity Deficit Audit", className="fw-bold fs-6"),
                            html.Span("REGIONAL AUDIT", className="badge kemsa-badge-navy small fw-semibold")
                        ], className="d-flex justify-content-between align-items-center"),
                        className="py-2 px-3 border-bottom bg-transparent"
                    ),
                    dbc.CardBody(county_table, className="p-0")
                ], className="kemsa-card mb-4 overflow-hidden shadow-sm"),
                lg=6, sm=12
            )
        ])
    ])

