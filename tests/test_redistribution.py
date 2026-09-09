"""Unit and integration tests for Smart Redistribution Engine (Batch 4)."""

import sqlite3
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.redistribution import (
    haversine_km,
    find_surplus_matches_for_facility,
    create_transfer_request,
    get_pending_requests_by_county,
    update_request_status,
    get_redistribution_activity_summary
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


def test_haversine_distance_calculation():
    """Verify real geodesic distance calculation."""
    # Nairobi (-1.2921, 36.8219) to Kiambu (-1.1714, 36.8356) is approx 13-14 km
    d = haversine_km(-1.2921, 36.8219, -1.1714, 36.8356)
    assert 12.0 <= d <= 16.0
    # Same point should be 0.0
    assert haversine_km(-1.2921, 36.8219, -1.2921, 36.8219) == 0.0


def test_surplus_matches_returns_real_distances(db_conn):
    """Verify matches for FAC0001 return real distances without 50/200km placeholders."""
    result = find_surplus_matches_for_facility(db_conn, "FAC0001")
    assert result is not None
    assert result["matches_found"] > 0
    top = result["matches"][0]
    assert top["distance_km"] not in (50.0, 200.0)
    assert top["distance_km"] > 0.0
    assert "surplus" in top["reason"]
    assert "stock out in" in top["reason"]


def test_transfer_request_lifecycle(db_conn):
    """Verify full transactional state machine: create -> pending -> approve/reject."""
    # 1. Create request
    rec = create_transfer_request(
        db=db_conn,
        source_facility_id="FAC0023",
        destination_facility_id="FAC0001",
        commodity_id="COM015",
        requested_quantity=50.0,
        requested_by="Test Pharmacist",
        reason="Clinical stockout prevention test"
    )
    req_id = rec["request_id"]
    assert rec["status"] == "pending"
    assert rec["distance_km"] not in (50.0, 200.0)

    # 2. Query county pending queue
    pending = get_pending_requests_by_county(db_conn, "Nairobi")
    assert any(r["request_id"] == req_id for r in pending["requests"])

    # 3. Approve request
    approved = update_request_status(db_conn, req_id, "approved", reviewed_by="County Director")
    assert approved["status"] == "approved"
    assert approved["reviewed_by"] == "County Director"

    # 4. Confirm it leaves pending queue
    pending_after = get_pending_requests_by_county(db_conn, "Nairobi")
    assert not any(r["request_id"] == req_id for r in pending_after["requests"])


def test_api_redistribution_workflow_end_to_end(client):
    """Verify complete API workflow chain end-to-end via REST endpoints."""
    # Step 1: Query matches
    r_matches = client.get("/api/redistribution/matches/FAC0001")
    assert r_matches.status_code == 200
    matches = r_matches.json()["matches"]
    assert len(matches) > 0
    match = matches[0]

    # Step 2: Post transfer request
    payload = {
        "source_facility_id": match["source_facility_id"],
        "destination_facility_id": match["destination_facility_id"],
        "commodity_id": match["commodity_id"],
        "requested_quantity": match["recommended_quantity"],
        "recommended_quantity": match["recommended_quantity"],
        "requested_by": "Test Pharmacist",
        "reason": match["reason"]
    }
    r_post = client.post("/api/redistribution/request", json=payload)
    assert r_post.status_code == 201
    created = r_post.json()
    req_id = created["request_id"]
    assert created["status"] == "pending"

    # Step 3: Check county pending
    r_pending = client.get(f"/api/redistribution/pending/{match['destination_county']}")
    assert r_pending.status_code == 200
    req_ids = [r["request_id"] for r in r_pending.json()["requests"]]
    assert req_id in req_ids

    # Step 4: Approve
    r_app = client.post(f"/api/redistribution/request/{req_id}/approve", json={"reviewed_by": "Dr. Director"})
    assert r_app.status_code == 200
    assert r_app.json()["status"] == "approved"

    # Step 5: Check activity summary
    r_act = client.get("/api/redistribution/activity")
    assert r_act.status_code == 200
    act_data = r_act.json()
    assert act_data["approved_transfers_count"] >= 85000  # Includes historical baseline
    assert act_data["total_units_transferred"] > 5_000_000
    assert act_data["combined_total_savings_kes"] >= 49_000_000.0
    assert act_data["historical_baseline"]["total_transfers"] == 85115
    assert act_data["historical_baseline"]["total_value_kes"] == 49200900.0
    assert act_data["live_activity"]["approved_transfers_count"] >= 1
    assert "top_reallocated_commodities" in act_data
    assert len(act_data["top_reallocated_commodities"]) == 5
    top_first = act_data["top_reallocated_commodities"][0]
    assert top_first["total_units"] > 500_000
    assert top_first["commodity_name"] is not None
    assert top_first["transfer_count"] > 0

