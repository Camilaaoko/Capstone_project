"""Smart Redistribution API Router for KEMSA Intelligence Platform."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field
import sqlite3

from backend.database import get_db
from backend.services.redistribution import (
    find_surplus_matches_for_facility,
    create_transfer_request,
    get_pending_requests_by_county,
    update_request_status,
    get_redistribution_activity_summary,
)

router = APIRouter(
    prefix="/api/redistribution",
    tags=["Smart Redistribution Engine"]
)


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------
class SurplusMatchItem(BaseModel):
    source_facility_id: str
    source_facility_name: str
    source_county: str
    destination_facility_id: str
    destination_facility_name: str
    destination_county: str
    commodity_id: str
    commodity_name: str
    category: str
    distance_km: float
    available_surplus_units: float
    required_deficit_units: float
    recommended_quantity: float
    unit_cost_kes: float
    transfer_value_kes: float
    source_days_of_stock: float
    destination_days_of_stock: float
    priority_score: float
    reason: str


class SurplusMatchesResponse(BaseModel):
    destination_facility_id: str
    destination_facility_name: str
    county: str
    shortage_commodities_count: int
    matches_found: int
    matches: List[SurplusMatchItem]


class CreateTransferRequestPayload(BaseModel):
    source_facility_id: str = Field(..., description="ID of the donor facility holding surplus")
    destination_facility_id: str = Field(..., description="ID of the recipient facility facing stockout")
    commodity_id: str = Field(..., description="ID of the pharmaceutical/medical supply")
    requested_quantity: float = Field(..., gt=0, description="Quantity of units requested for transfer")
    recommended_quantity: Optional[float] = Field(None, description="System-recommended transfer batch quantity")
    requested_by: Optional[str] = Field(None, description="Name or role of the requesting facility officer")
    reason: Optional[str] = Field(None, description="Plain-language clinical/operational transfer rationale")


class TransferRequestRecord(BaseModel):
    request_id: str
    source_facility_id: str
    source_facility_name: str
    source_county: str
    destination_facility_id: str
    destination_facility_name: str
    destination_county: str
    commodity_id: str
    commodity_name: str
    requested_quantity: float
    recommended_quantity: float
    distance_km: float
    status: str
    requested_by: str
    requested_at: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    reason: str


class CountyPendingRequestsResponse(BaseModel):
    county: str
    pending_count: int
    requests: List[Dict[str, Any]]


class ReviewRequestPayload(BaseModel):
    reviewed_by: Optional[str] = Field(None, description="Name of the County Health Director/Pharmacist reviewer")
    notes: Optional[str] = Field(None, description="Optional operational review notes")


class HistoricalBaselineMetrics(BaseModel):
    total_transfers: int
    total_units: float
    total_value_kes: float


class LiveActivityMetrics(BaseModel):
    status_counts: Dict[str, int]
    approved_transfers_count: int
    total_units_transferred: float
    estimated_financial_value_kes: float
    estimated_wastage_prevented_kes: float


class TopReallocatedCommodity(BaseModel):
    commodity_id: str
    commodity_name: str
    category: str
    transfer_count: int
    total_units: float
    total_value_kes: float


class RedistributionActivityResponse(BaseModel):
    status_counts: Dict[str, int]
    approved_transfers_count: int
    total_units_transferred: float
    estimated_financial_value_kes: float
    estimated_wastage_prevented_kes: float
    historical_baseline: HistoricalBaselineMetrics
    live_activity: LiveActivityMetrics
    combined_total_savings_kes: float
    combined_total_transfers: int
    combined_total_units: float
    recent_activity: List[Dict[str, Any]]
    top_reallocated_commodities: Optional[List[TopReallocatedCommodity]] = []


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/matches/{facility_id}", response_model=SurplusMatchesResponse)
def get_surplus_matches(
    facility_id: str,
    commodity_id: Optional[str] = Query(None, description="Optional specific commodity ID filter"),
    max_distance_km: float = Query(400.0, ge=1.0, le=1000.0, description="Maximum transport radius in km"),
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns ranked surplus matches for a facility facing stockout.
    Powers Dashboard 3 (Nearby Surplus Finder).
    Uses true geodesic Haversine distance with real GPS facility coordinates.
    """
    matches_data = find_surplus_matches_for_facility(
        db=db,
        destination_facility_id=facility_id,
        commodity_id=commodity_id,
        max_distance_km=max_distance_km
    )
    if not matches_data:
        raise HTTPException(
            status_code=404,
            detail=f"Facility '{facility_id}' not found in registry."
        )
    return matches_data


@router.post("/request", response_model=TransferRequestRecord, status_code=status.HTTP_201_CREATED)
def submit_transfer_request(
    payload: CreateTransferRequestPayload,
    db: sqlite3.Connection = Depends(get_db)
):
    """Creates a new transfer request in 'pending' status.
    Powers Dashboard 3 ('Request Transfer' button).
    Writes directly to transactional transfer_requests table.
    """
    try:
        record = create_transfer_request(
            db=db,
            source_facility_id=payload.source_facility_id,
            destination_facility_id=payload.destination_facility_id,
            commodity_id=payload.commodity_id,
            requested_quantity=payload.requested_quantity,
            recommended_quantity=payload.recommended_quantity,
            requested_by=payload.requested_by,
            reason=payload.reason
        )
        return record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating transfer request: {str(e)}")


@router.get("/pending/{county}", response_model=CountyPendingRequestsResponse)
def get_pending_transfers(
    county: str,
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns all pending transfer requests where destination or source facility is in this county.
    Powers Dashboard 2 (County Health Department / Pharmacist decision queue).
    """
    return get_pending_requests_by_county(db, county)


@router.post("/request/{request_id}/approve", response_model=TransferRequestRecord)
def approve_transfer(
    request_id: str,
    payload: Optional[ReviewRequestPayload] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    """Approves a pending transfer request.
    Powers Dashboard 2 ('Approve' decision button). Updates status to 'approved' and records reviewed_at.
    """
    reviewer = payload.reviewed_by if payload else None
    updated = update_request_status(db, request_id, target_status="approved", reviewed_by=reviewer)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer request '{request_id}' not found."
        )
    return updated


@router.post("/request/{request_id}/reject", response_model=TransferRequestRecord)
def reject_transfer(
    request_id: str,
    payload: Optional[ReviewRequestPayload] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    """Rejects a pending transfer request.
    Powers Dashboard 2 ('Reject' decision button). Updates status to 'rejected' and records reviewed_at.
    """
    reviewer = payload.reviewed_by if payload else None
    updated = update_request_status(db, request_id, target_status="rejected", reviewed_by=reviewer)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer request '{request_id}' not found."
        )
    return updated


@router.get("/activity", response_model=RedistributionActivityResponse)
def get_activity_log(
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns national redistribution activity metrics and summary log.
    Powers Dashboard 1 (KEMSA National Leadership activity log and prevented wastage counters).
    """
    try:
        return get_redistribution_activity_summary(db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error compiling redistribution activity summary: {str(e)}"
        )
