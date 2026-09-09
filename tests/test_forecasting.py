"""Unit and integration tests for Stockout Forecasting Engine (Batch 3)."""

import sqlite3
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.forecasting import (
    project_pair_stockout,
    get_facility_stockout_forecast,
    get_county_stockout_forecast,
    get_national_stockout_forecast,
    get_category_stockout_forecast,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "analytics" / "analytics.db"


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_conn():
    """Provides connection to analytics.db."""
    if not DB_PATH.exists():
        pytest.skip("analytics.db not found.")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_project_pair_stockout_critical():
    """Verify Critical stockout projection (<= 30 days)."""
    res = project_pair_stockout(
        closing_stock=100.0,
        recent_daily_consumption=10.0,
        inventory_date_str="2024-03-31",
        horizon_days=90
    )
    assert res["risk_flag"] == "Critical"
    assert res["days_until_stockout"] is not None
    assert res["days_until_stockout"] <= 30
    assert res["predicted_stockout_date"] is not None
    assert res["risk_color"] == "#EF4444"
    assert "will be exhausted in" in res["explanation"]


def test_project_pair_stockout_warning():
    """Verify Warning stockout projection (31-60 days)."""
    res = project_pair_stockout(
        closing_stock=400.0,
        recent_daily_consumption=10.0,
        inventory_date_str="2024-03-31",
        horizon_days=90
    )
    assert res["risk_flag"] == "Warning"
    assert 31 <= res["days_until_stockout"] <= 60
    assert res["risk_color"] == "#F59E0B"


def test_project_pair_stockout_watch():
    """Verify Watch stockout projection (61-90 days)."""
    res = project_pair_stockout(
        closing_stock=700.0,
        recent_daily_consumption=10.0,
        inventory_date_str="2024-03-31",
        horizon_days=90
    )
    assert res["risk_flag"] == "Watch"
    assert 61 <= res["days_until_stockout"] <= 90
    assert res["risk_color"] == "#3B82F6"


def test_project_pair_stockout_healthy():
    """Verify Healthy projection (no stockout within 90 days)."""
    res = project_pair_stockout(
        closing_stock=2000.0,
        recent_daily_consumption=10.0,
        inventory_date_str="2024-03-31",
        horizon_days=90
    )
    assert res["risk_flag"] == "Healthy"
    assert res["days_until_stockout"] is None
    assert res["predicted_stockout_date"] is None
    assert res["stockout_date_display"] == "No stockout predicted within 90 days"
    assert res["risk_color"] == "#10B981"


def test_get_facility_forecast_service(db_conn):
    """Verify facility forecasting service returns commodities with complete attributes."""
    data = get_facility_stockout_forecast(db_conn, "FAC0001")
    assert data is not None
    assert data["facility_id"] == "FAC0001"
    assert len(data["forecasts"]) == 15
    assert data["risk_counts"]["total"] == 15
    flags = {f["risk_flag"] for f in data["forecasts"]}
    assert "Critical" in flags
    assert "Healthy" in flags


def test_get_county_forecast_service(db_conn):
    """Verify county forecast aggregates across facilities and generates alert feed."""
    data = get_county_stockout_forecast(db_conn, "Nairobi")
    assert data is not None
    assert data["county"] == "Nairobi"
    assert data["facilities_monitored"] > 0
    assert len(data["critical_alerts"]) > 0
    assert "alert_message" in data["critical_alerts"][0]


def test_get_national_forecast_service(db_conn):
    """Verify national forecast computes 30/60/90 horizons and top urgent pairs."""
    data = get_national_stockout_forecast(db_conn, top_n=5)
    assert data is not None
    assert data["total_facilities_monitored"] == 100
    assert data["total_pairs_monitored"] == 1500
    assert len(data["horizon_projections"]) == 3
    assert len(data["most_urgent_pairs"]) == 5


def test_api_facility_endpoint(client):
    """Verify GET /api/forecast/facility/{facility_id} endpoint."""
    resp = client.get("/api/forecast/facility/FAC0001")
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data["facility_id"] == "FAC0001"
    assert len(json_data["forecasts"]) == 15


def test_api_facility_not_found(client):
    """Verify 404 for invalid facility ID."""
    resp = client.get("/api/forecast/facility/FAC9999")
    assert resp.status_code == 404


def test_api_county_endpoint(client):
    """Verify GET /api/forecast/county/{county} endpoint."""
    resp = client.get("/api/forecast/county/Nairobi")
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data["county"] == "Nairobi"
    assert json_data["facilities_monitored"] == 3
    assert json_data["total_pairs"] == 45


def test_api_county_not_found(client):
    """Verify 404 for invalid county name."""
    resp = client.get("/api/forecast/county/NonExistentCounty")
    assert resp.status_code == 404


def test_api_national_endpoint(client):
    """Verify GET /api/forecast/national endpoint."""
    resp = client.get("/api/forecast/national?top_n=10")
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data["total_facilities_monitored"] == 100
    assert len(json_data["most_urgent_pairs"]) == 10
    assert len(json_data["horizon_projections"]) == 3


def test_get_category_stockout_forecast_service(db_conn):
    """Verify category forecasting service aggregates 30-day deficit by therapeutic category."""
    data = get_category_stockout_forecast(db_conn)
    assert data is not None
    assert "categories" in data
    assert len(data["categories"]) >= 3
    assert data["total_critical_pairs"] > 0
    assert data["total_deficit_value_kes"] > 0.0

    # Ensure categories are sorted by deficit value descending
    cats = data["categories"]
    for i in range(len(cats) - 1):
        assert cats[i]["estimated_deficit_value_kes"] >= cats[i + 1]["estimated_deficit_value_kes"]

    # Verify category attributes
    first = cats[0]
    assert first["category"] in ("Analgesics", "Antimalarials", "Antibiotics")
    assert first["critical_pairs"] > 0
    assert first["affected_facilities_count"] > 0
    assert first["unmet_demand_units"] > 0
    assert len(first["top_commodities"]) > 0


def test_api_categories_endpoint(client):
    """Verify GET /api/forecast/categories endpoint."""
    resp = client.get("/api/forecast/categories")
    assert resp.status_code == 200
    json_data = resp.json()
    assert "categories" in json_data
    assert len(json_data["categories"]) >= 3
    assert json_data["total_critical_pairs"] > 0
    assert json_data["total_deficit_value_kes"] > 0.0


def test_api_national_categories_endpoint(client):
    """Verify GET /api/forecast/national/categories alias endpoint."""
    resp = client.get("/api/forecast/national/categories")
    assert resp.status_code == 200
    json_data = resp.json()
    assert "categories" in json_data
    assert len(json_data["categories"]) >= 3

