"""Reusable KPI metric card components."""

from dash import html
import dash_bootstrap_components as dbc
from typing import Dict, Any


def create_kpi_card(title: str, value: str, subtitle: str, color: str, icon: str) -> dbc.Col:
    """Generates a styled KPI statistic card."""
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.P(title, className="text-muted text-uppercase fw-semibold mb-1", style={"fontSize": "0.78rem"}),
                        html.H3(value, className=f"text-{color} fw-bold mb-1"),
                        html.Small(subtitle, className="text-muted")
                    ], width=9),
                    dbc.Col([
                        html.Div(
                            icon,
                            className=f"text-{color} bg-{color}-subtle rounded-circle d-flex align-items-center justify-content-center",
                            style={"width": "48px", "height": "48px", "fontSize": "1.5rem"}
                        )
                    ], width=3, className="d-flex justify-content-end align-items-start")
                ], align="center")
            ]),
            className=f"shadow-sm border-0 border-start border-4 border-{color} h-100"
        ),
        lg=3, md=6, sm=12, className="mb-3"
    )


def create_kpi_deck(kpi_data: Dict[str, Any]) -> dbc.Row:
    """Generates the full row of executive KPI cards."""
    stockout_days = kpi_data.get("stockout_days", 0)
    units_short = kpi_data.get("units_short", 0)
    wastage_kes = kpi_data.get("wastage_kes", 0)
    savings_kes = kpi_data.get("savings_kes", 0)
    otd_rate = kpi_data.get("avg_otd_rate", 0)
    events = kpi_data.get("redistribution_events", 0)

    card1 = create_kpi_card(
        title="Total Stockout Days",
        value=f"{stockout_days:,.0f}",
        subtitle=f"{units_short:,.0f} units deficit estimated",
        color="danger",
        icon="⚠️"
    )
    
    card2 = create_kpi_card(
        title="Expiry Wastage Value",
        value=f"KES {wastage_kes:,.0f}",
        subtitle=f"{kpi_data.get('expired_units', 0):,.0f} units expired in batches",
        color="warning",
        icon="⏳"
    )

    card3 = create_kpi_card(
        title="Intelligent Savings",
        value=f"KES {savings_kes:,.0f}",
        subtitle=f"{events:,} active redistribution chains",
        color="success",
        icon="💰"
    )

    card4 = create_kpi_card(
        title="Supplier On-Time Rate",
        value=f"{otd_rate:.1f}%",
        subtitle=f"Fill Rate: {kpi_data.get('avg_fill_rate', 0):.1f}%",
        color="primary",
        icon="🚚"
    )

    return dbc.Row([card1, card2, card3, card4], className="g-3 mb-4")

