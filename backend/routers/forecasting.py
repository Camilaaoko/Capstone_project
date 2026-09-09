"""Stockout Forecasting API Router for KEMSA Intelligence Platform."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import sqlite3

from backend.database import get_db
from backend.services.forecasting import (
    get_facility_stockout_forecast,
    get_county_stockout_forecast,
    get_national_stockout_forecast,
    get_category_stockout_forecast,
)

router = APIRouter(
    prefix="/api/forecast",
    tags=["Stockout Forecasting Engine"]
)


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------
class RiskCounts(BaseModel):
    critical: int
    warning: int
    watch: int
    healthy: int
    total: int


class CommodityStockoutForecast(BaseModel):
    facility_id: str
    facility_name: str
    county: str
    commodity_id: str
    commodity_name: str
    category: str
    current_stock_level: float
    recent_daily_consumption: float
    days_until_stockout: Optional[int] = None
    predicted_stockout_date: Optional[str] = None
    stockout_date_display: str
    risk_flag: str
    risk_color: str
    urgency_score: float
    explanation: str


class FacilityForecastResponse(BaseModel):
    facility_id: str
    facility_name: str
    county: str
    inventory_date: str
    risk_counts: RiskCounts
    forecasts: List[CommodityStockoutForecast]


class CountyAlertItem(BaseModel):
    facility_id: str
    facility_name: str
    commodity_id: str
    commodity_name: str
    days_until_stockout: int
    predicted_stockout_date: str
    current_stock_level: float
    risk_flag: str
    alert_message: str


class FacilityRiskSummary(BaseModel):
    facility_id: str
    facility_name: str
    sub_county: Optional[str] = None
    critical_count: int
    warning_count: int
    watch_count: int
    healthy_count: int
    highest_risk_flag: str


class CountyForecastResponse(BaseModel):
    county: str
    inventory_date: str
    facilities_monitored: int
    total_pairs: int
    risk_counts: RiskCounts
    critical_alerts: List[CountyAlertItem]
    facilities: List[FacilityRiskSummary]


class UrgentStockoutPair(BaseModel):
    facility_id: str
    facility_name: str
    county: str
    commodity_id: str
    commodity_name: str
    days_until_stockout: int
    predicted_stockout_date: str
    current_stock_level: float
    recent_daily_consumption: float
    risk_flag: str


class HorizonDeficit(BaseModel):
    horizon_days: int
    label: str
    predicted_stockout_pairs: int
    estimated_unmet_demand_units: float


class NationalForecastResponse(BaseModel):
    inventory_date: str
    total_facilities_monitored: int
    total_counties_monitored: int
    total_commodities_monitored: int
    total_pairs_monitored: int
    risk_counts: RiskCounts
    horizon_projections: List[HorizonDeficit]
    most_urgent_pairs: List[UrgentStockoutPair]


class CategoryTopCommodity(BaseModel):
    commodity_name: str
    unmet_units: float
    deficit_value_kes: float


class CategoryDeficitItem(BaseModel):
    category: str
    critical_pairs: int
    affected_facilities_count: int
    unmet_demand_units: float
    estimated_deficit_value_kes: float
    percentage_of_value: float
    percentage_of_units: float
    top_commodities: List[CategoryTopCommodity]


class CategoryForecastResponse(BaseModel):
    inventory_date: str
    total_critical_pairs: int
    total_unmet_demand_units: float
    total_deficit_value_kes: float
    categories: List[CategoryDeficitItem]


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/facility/{facility_id}", response_model=FacilityForecastResponse)
def get_facility_forecast(
    facility_id: str,
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns 30/60/90-day forward stockout forecasts for every commodity stocked at a specific facility.
    Powers the Facility Dashboard (Dashboard 3) countdown badges and inventory status.
    """
    forecast_data = get_facility_stockout_forecast(db, facility_id)
    if not forecast_data:
        raise HTTPException(
            status_code=404,
            detail=f"Facility '{facility_id}' not found or has no active inventory records."
        )
    return forecast_data


@router.get("/county/{county}", response_model=CountyForecastResponse)
def get_county_forecast(
    county: str,
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns aggregated view of stockout forecasts across all health facilities within a county.
    Powers the County Health Department Dashboard (Dashboard 2) alert feed and facility overview.
    """
    county_data = get_county_stockout_forecast(db, county)
    if not county_data:
        raise HTTPException(
            status_code=404,
            detail=f"County '{county}' not found or contains no monitored facilities."
        )
    return county_data


@router.get("/national", response_model=NationalForecastResponse)
def get_national_forecast(
    top_n: int = Query(10, ge=1, le=50, description="Number of most urgent stockout pairs to highlight"),
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns national aggregate stockout trajectory (30/60/90 days) and top urgent stockout pairs.
    Powers the KEMSA National Leadership Dashboard (Dashboard 1) executive forecasting card.
    Strictly summary-shaped per architectural specification.
    """
    try:
        return get_national_stockout_forecast(db, top_n=top_n)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing national stockout forecast: {str(e)}"
        )


@router.get("/categories", response_model=CategoryForecastResponse)
@router.get("/national/categories", response_model=CategoryForecastResponse)
def get_category_deficit_forecast(
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns 30-day predicted stockout deficit grouped by commodity category (therapeutic program).
    Powers the National Leadership Dashboard category-level resource allocation breakdown.
    """
    try:
        return get_category_stockout_forecast(db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing category stockout deficit: {str(e)}"
        )

