"""Reusable KPI metric card components with KEMSA design tokens and JetBrains Mono metrics."""

from dash import html
import dash_bootstrap_components as dbc
from typing import Dict, Any


def create_kpi_card(
    title: str,
    value: str,
    subtitle: str,
    color_theme: str,
    badge_text: str = "",
    progress_val: int = 75
) -> dbc.Col:
    """Generates an elevated, icon-free KPI statistic card with JetBrains Mono typography and status chip."""
    theme_map = {
        "danger": {
            "text": "#EF4444",
            "bg_gradient": "linear-gradient(180deg, #FFFFFF 0%, #FEF2F2 100%)",
            "border_top": "linear-gradient(90deg, #EF4444 0%, #F87171 100%)",
            "border_color": "rgba(239, 68, 68, 0.25)",
            "badge_color": "#DC2626",
            "badge_bg": "#FEE2E2",
            "badge_border": "rgba(239, 68, 68, 0.35)",
            "progress_color": "danger"
        },
        "warning": {
            "text": "#D97706",
            "bg_gradient": "linear-gradient(180deg, #FFFFFF 0%, #FFFBEB 100%)",
            "border_top": "linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%)",
            "border_color": "rgba(245, 158, 11, 0.25)",
            "badge_color": "#B45309",
            "badge_bg": "#FEF3C7",
            "badge_border": "rgba(245, 158, 11, 0.35)",
            "progress_color": "warning"
        },
        "success": {
            "text": "#059669",
            "bg_gradient": "linear-gradient(180deg, #FFFFFF 0%, #ECFDF5 100%)",
            "border_top": "linear-gradient(90deg, #10B981 0%, #34D399 100%)",
            "border_color": "rgba(16, 185, 129, 0.25)",
            "badge_color": "#047857",
            "badge_bg": "#D1FAE5",
            "badge_border": "rgba(16, 185, 129, 0.35)",
            "progress_color": "success"
        },
        "cyan": {
            "text": "#0284C7",
            "bg_gradient": "linear-gradient(180deg, #FFFFFF 0%, #E0F2FE 100%)",
            "border_top": "linear-gradient(90deg, #0EA5E9 0%, #38BDF8 100%)",
            "border_color": "rgba(14, 165, 233, 0.25)",
            "badge_color": "#0369A1",
            "badge_bg": "#BAE6FD",
            "badge_border": "rgba(14, 165, 233, 0.35)",
            "progress_color": "info"
        },
        "navy": {
            "text": "#0F172A",
            "bg_gradient": "linear-gradient(180deg, #FFFFFF 0%, #F1F5F9 100%)",
            "border_top": "linear-gradient(90deg, #334155 0%, #64748B 100%)",
            "border_color": "rgba(51, 65, 85, 0.25)",
            "badge_color": "#1E293B",
            "badge_bg": "#E2E8F0",
            "badge_border": "rgba(51, 65, 85, 0.35)",
            "progress_color": "primary"
        }
    }
    theme = theme_map.get(color_theme, theme_map["navy"])

    return dbc.Col(
        dbc.Card(
            [
                # Gradient accent bar at top
                html.Div(style={"height": "4px", "background": theme["border_top"]}),
                dbc.CardBody([
                    # Title & Badge Row
                    html.Div([
                        html.Span(
                            title,
                            className="kpi-card-title fw-bolder text-uppercase",
                            style={"fontSize": "0.74rem", "letterSpacing": "0.9px", "fontWeight": "800"}
                        ),
                        html.Span(
                            badge_text or "LIVE",
                            className="stat-chip-badge",
                            style={
                                "backgroundColor": theme["badge_bg"],
                                "color": theme["badge_color"],
                                "border": f"1px solid {theme['badge_border']}",
                                "fontSize": "0.68rem",
                                "fontWeight": "700",
                                "padding": "2px 8px",
                                "borderRadius": "9999px",
                                "letterSpacing": "0.5px"
                            }
                        )
                    ], className="d-flex align-items-center justify-content-between mb-2"),

                    # Main Stat Metric
                    html.H3(
                        value,
                        className="font-mono fw-bolder mb-1 kpi-value-metric",
                        style={
                            "color": theme["text"],
                            "letterSpacing": "-0.5px",
                            "fontSize": "1.85rem",
                            "lineHeight": "1.15"
                        }
                    ),

                    # Subtitle / Context
                    html.Small(
                        subtitle,
                        className="kpi-card-subtitle d-block mb-3 fw-semibold",
                        style={"fontSize": "0.85rem"}
                    ),

                    # Micro Progress Bar
                    dbc.Progress(
                        value=progress_val,
                        style={"height": "6px", "backgroundColor": "rgba(0, 0, 0, 0.06)"},
                        className="rounded-pill",
                        color=theme["progress_color"]
                    )
                ], className="p-3 d-flex flex-column justify-content-between h-100")
            ],
            className=f"kpi-metric-card kpi-theme-{color_theme} kemsa-card h-100 position-relative overflow-hidden shadow-sm",
            style={
                "background": theme["bg_gradient"],
                "borderColor": theme["border_color"]
            }
        ),
        lg=3, md=6, sm=12, className="mb-3"
    )


def create_kpi_deck(kpi_data: Dict[str, Any]) -> dbc.Row:
    """Generates the full row of executive KPI cards with JetBrains Mono numbers and no icons."""
    stockout_days = kpi_data.get("stockout_days", 0)
    units_short = kpi_data.get("units_short", 0)
    wastage_kes = kpi_data.get("wastage_kes", 0)
    savings_kes = kpi_data.get("savings_kes", 0)
    otd_rate = kpi_data.get("avg_otd_rate", 0)
    events = kpi_data.get("redistribution_events", 0)

    card1 = create_kpi_card(
        title="TOTAL STOCKOUT DAYS",
        value=f"{stockout_days:,.0f}",
        subtitle=f"{units_short:,.0f} units deficit estimated",
        color_theme="danger",
        badge_text="CRITICAL",
        progress_val=min(100, int((stockout_days / 1000) * 100)) if stockout_days else 65
    )

    card2 = create_kpi_card(
        title="EXPIRY WASTAGE VALUE",
        value=f"KES {wastage_kes:,.0f}",
        subtitle=f"{kpi_data.get('expired_units', 0):,.0f} units expired in batches",
        color_theme="warning",
        badge_text="BATCH AUDIT",
        progress_val=min(100, int((wastage_kes / 50000000) * 100)) if wastage_kes else 45
    )

    card3 = create_kpi_card(
        title="INTELLIGENT SAVINGS",
        value=f"KES {savings_kes:,.0f}",
        subtitle=f"{events:,} active redistribution transfers",
        color_theme="success",
        badge_text="REALLOCATED",
        progress_val=min(100, int(events * 5)) if events else 80
    )

    card4 = create_kpi_card(
        title="SUPPLIER ON-TIME RATE",
        value=f"{otd_rate:.1f}%",
        subtitle=f"Fill Rate: {kpi_data.get('avg_fill_rate', 0):.1f}% Target",
        color_theme="cyan",
        badge_text="SLA 90%",
        progress_val=int(otd_rate) if otd_rate else 88
    )

    return dbc.Row([card1, card2, card3, card4], className="g-3 mb-4")
