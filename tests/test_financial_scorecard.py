"""Unit and integration tests for the Financial Risk Scorecard module (Batch 2)."""

import sqlite3
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.financial_scoring import calculate_county_financial_risk

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
        pytest.skip("analytics.db not found. Run ETL pipeline first.")
    conn = sqlite3.connect(str(DB_PATH))
    yield conn
    conn.close()


def test_fact_county_debt_table_exists(db_conn):
    """Verify FACT_COUNTY_DEBT table exists and has 47 counties."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT count(distinct county), count(*), min(month), max(month) FROM FACT_COUNTY_DEBT")
    row = cursor.fetchone()
    assert row[0] == 47, f"Expected 47 distinct counties, found {row[0]}"
    assert row[1] == 47 * 24, f"Expected 1,128 records, found {row[1]}"
    assert row[2] == "2024-01"
    assert row[3] == "2025-12"


def test_financial_risk_scoring_logic_high():
    """Verify high-risk county scoring and factor breakdown."""
    res = calculate_county_financial_risk(
        amount_owed_kes=350_000_000.0,
        days_overdue=250,
        payment_history_score=20.0,
        county_name="TestHigh"
    )
    assert res["risk_tier"] == "High"
    assert res["risk_score"] >= 65.0
    assert res["tier_color"] == "#EF4444"
    assert len(res["factors"]) == 3
    assert "critical" in [f["contribution"] for f in res["factors"]]
    assert "High Risk Tier" in res["plain_language_summary"]


def test_financial_risk_scoring_logic_low():
    """Verify low-risk county scoring and factor breakdown."""
    res = calculate_county_financial_risk(
        amount_owed_kes=5_000_000.0,
        days_overdue=10,
        payment_history_score=95.0,
        county_name="TestLow"
    )
    assert res["risk_tier"] == "Low"
    assert res["risk_score"] < 35.0
    assert res["tier_color"] == "#10B981"
    assert len(res["factors"]) == 3
    assert all(f["contribution"] == "low" for f in res["factors"])
    assert "Low Risk Tier" in res["plain_language_summary"]


def test_api_financial_scorecard_all(client):
    """Verify GET /api/financial/scorecard returns all 47 counties."""
    resp = client.get("/api/financial/scorecard")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 47
    counties = {c["county"] for c in data}
    assert "Nairobi" in counties
    assert "Bungoma" in counties
    assert "Bomet" in counties
    tiers = {c["risk_tier"] for c in data}
    assert {"Low", "Medium", "High"}.issubset(tiers)


def test_api_financial_scorecard_single_county(client):
    """Verify GET /api/financial/scorecard/{county} returns explainability breakdown."""
    resp = client.get("/api/financial/scorecard/Bungoma")
    assert resp.status_code == 200
    data = resp.json()
    assert data["county"] == "Bungoma"
    assert data["risk_tier"] == "High"
    assert len(data["factors"]) == 3
    assert "plain_language_summary" in data
    assert "primary_driver" in data


def test_api_financial_scorecard_not_found(client):
    """Verify 404 response for non-existent county."""
    resp = client.get("/api/financial/scorecard/NonExistentCounty")
    assert resp.status_code == 404


def test_api_national_debt_trend(client):
    """Verify GET /api/financial/national-debt-trend returns 24 monthly macro trend records."""
    resp = client.get("/api/financial/national-debt-trend")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 24
    assert data[0]["month"] == "2024-01"
    assert data[-1]["month"] == "2025-12"
    for item in data:
        assert "month" in item
        assert "total_debt" in item
        assert item["total_debt"] > 1_000_000_000.0  # National debt is in billions KES
        assert "avg_days_overdue" in item
        assert item["avg_days_overdue"] > 0
        assert item["counties_count"] == 47


def test_api_county_scorecard_history(client):
    """Verify GET /api/financial/scorecard/{county}/history returns 24 monthly trajectory records."""
    resp = client.get("/api/financial/scorecard/Kiambu/history")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 24
    assert data[0]["month"] == "2024-01"
    assert data[-1]["month"] == "2025-12"
    for item in data:
        assert item["county"].lower() == "kiambu"
        assert "amount_owed_kes" in item
        assert "days_overdue" in item
        assert "payment_history_score" in item
        assert "risk_score" in item
        assert "risk_tier" in item
        assert item["risk_tier"] in ("Low", "Medium", "High")

    # Test 404 for non-existent county
    resp_404 = client.get("/api/financial/scorecard/ImaginaryCounty/history")
    assert resp_404.status_code == 404
