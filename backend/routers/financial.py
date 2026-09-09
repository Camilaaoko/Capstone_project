"""Financial Risk Scorecard API Router for KEMSA Intelligence Platform."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import sqlite3

from backend.database import get_db
from backend.services.financial_scoring import calculate_county_financial_risk

router = APIRouter(
    prefix="/api/financial",
    tags=["Financial Risk Scorecard"]
)


class RiskFactorDetail(BaseModel):
    factor: str
    factor_name: str
    value: float
    formatted_value: str
    weight_pct: int
    contribution: str
    score_contribution: float
    description: str


class CountyScorecardSummary(BaseModel):
    county: str
    risk_score: float
    risk_tier: str
    tier_color: str
    tier_badge: str
    amount_owed_kes: float
    days_overdue: int
    payment_history_score: float
    primary_driver: str
    month: str


class CountyScorecardDetail(CountyScorecardSummary):
    factors: List[RiskFactorDetail]
    plain_language_summary: str


class NationalDebtTrendItem(BaseModel):
    month: str
    total_debt: float
    avg_days_overdue: float
    counties_count: int


class CountyHistoryItem(BaseModel):
    county: str
    month: str
    amount_owed_kes: float
    days_overdue: int
    payment_history_score: float
    risk_score: float
    risk_tier: str
    tier_color: str
    tier_badge: str
    primary_driver: str


@router.get("/national-debt-trend", response_model=List[NationalDebtTrendItem])
def get_national_debt_trend(
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns 24-month national debt exposure trend across all counties.
    Powers Dashboard 1 (KEMSA National Leadership macro debt exposure trend chart).
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                month, 
                SUM(amount_owed_kes) as total_debt, 
                AVG(days_overdue) as avg_days_overdue,
                COUNT(*) as counties_count
            FROM FACT_COUNTY_DEBT 
            GROUP BY month 
            ORDER BY month ASC
        """)
        rows = cursor.fetchall()
        return [
            {
                "month": r["month"],
                "total_debt": round(float(r["total_debt"] or 0.0), 2),
                "avg_days_overdue": round(float(r["avg_days_overdue"] or 0.0), 1),
                "counties_count": int(r["counties_count"] or 0),
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying national debt trend: {str(e)}"
        )


@router.get("/scorecard", response_model=List[CountyScorecardSummary])
def get_all_county_scorecards(
    month: Optional[str] = Query(None, description="Optional filter month in YYYY-MM format (defaults to latest available)"),
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns financial risk tier, composite score, and key metrics for all 47 counties.
    Powers the National Leadership risk map and executive cards.
    """
    try:
        cursor = db.cursor()

        # Determine latest month if not specified
        if not month:
            cursor.execute("SELECT MAX(month) as latest_month FROM FACT_COUNTY_DEBT")
            row = cursor.fetchone()
            month = row["latest_month"] if row and row["latest_month"] else "2025-12"

        cursor.execute("""
            SELECT 
                county,
                month,
                amount_owed_kes,
                days_overdue,
                payment_history_score
            FROM FACT_COUNTY_DEBT
            WHERE month = ?
            ORDER BY county ASC
        """, (month,))
        rows = cursor.fetchall()

        results = []
        for r in rows:
            scored = calculate_county_financial_risk(
                amount_owed_kes=float(r["amount_owed_kes"]),
                days_overdue=int(r["days_overdue"]),
                payment_history_score=float(r["payment_history_score"]),
                county_name=r["county"]
            )
            results.append({
                "county": r["county"],
                "risk_score": scored["risk_score"],
                "risk_tier": scored["risk_tier"],
                "tier_color": scored["tier_color"],
                "tier_badge": scored["tier_badge"],
                "amount_owed_kes": scored["amount_owed_kes"],
                "days_overdue": scored["days_overdue"],
                "payment_history_score": scored["payment_history_score"],
                "primary_driver": scored["primary_driver"],
                "month": r["month"]
            })

        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying county financial scorecards: {str(e)}"
        )


@router.get("/scorecard/{county}/history", response_model=List[CountyHistoryItem])
def get_county_scorecard_history(
    county: str,
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns 24-month financial risk trajectory and monthly scores for a specific county.
    Powers Dashboard 2 ('Why' explainability velocity trend chart).
    """
    try:
        cursor = db.cursor()

        # Case-insensitive county lookup
        cursor.execute("""
            SELECT DISTINCT county FROM FACT_COUNTY_DEBT
            WHERE LOWER(county) = LOWER(?)
            LIMIT 1
        """, (county.strip(),))
        match = cursor.fetchone()

        if not match:
            raise HTTPException(
                status_code=404,
                detail=f"County '{county}' not found in financial records."
            )

        matched_county = match["county"]

        cursor.execute("""
            SELECT 
                county,
                month,
                amount_owed_kes,
                days_overdue,
                payment_history_score
            FROM FACT_COUNTY_DEBT
            WHERE LOWER(county) = LOWER(?)
            ORDER BY month ASC
        """, (matched_county,))
        rows = cursor.fetchall()

        results = []
        for r in rows:
            scored = calculate_county_financial_risk(
                amount_owed_kes=float(r["amount_owed_kes"]),
                days_overdue=int(r["days_overdue"]),
                payment_history_score=float(r["payment_history_score"]),
                county_name=matched_county
            )
            results.append({
                "county": matched_county,
                "month": r["month"],
                "amount_owed_kes": scored["amount_owed_kes"],
                "days_overdue": scored["days_overdue"],
                "payment_history_score": scored["payment_history_score"],
                "risk_score": scored["risk_score"],
                "risk_tier": scored["risk_tier"],
                "tier_color": scored["tier_color"],
                "tier_badge": scored["tier_badge"],
                "primary_driver": scored["primary_driver"],
            })

        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying financial history for county '{county}': {str(e)}"
        )


@router.get("/scorecard/{county}", response_model=CountyScorecardDetail)
def get_county_scorecard(
    county: str,
    month: Optional[str] = Query(None, description="Optional filter month in YYYY-MM format (defaults to latest available)"),
    db: sqlite3.Connection = Depends(get_db)
):
    """Returns detailed financial scorecard with full explainability factor breakdown
    and plain-language diagnostic summary for a specific county.
    Powers the County Health Department dashboard and 'Why' panel.
    """
    try:
        cursor = db.cursor()

        # Case-insensitive county lookup
        cursor.execute("""
            SELECT county FROM FACT_COUNTY_DEBT
            WHERE LOWER(county) = LOWER(?)
            LIMIT 1
        """, (county.strip(),))
        match = cursor.fetchone()

        if not match:
            raise HTTPException(
                status_code=404,
                detail=f"County '{county}' not found in financial records."
            )

        matched_county = match["county"]

        if not month:
            cursor.execute("""
                SELECT MAX(month) as latest_month FROM FACT_COUNTY_DEBT
                WHERE county = ?
            """, (matched_county,))
            row = cursor.fetchone()
            month = row["latest_month"] if row and row["latest_month"] else "2025-12"

        cursor.execute("""
            SELECT 
                county,
                month,
                amount_owed_kes,
                days_overdue,
                payment_history_score
            FROM FACT_COUNTY_DEBT
            WHERE county = ? AND month = ?
            LIMIT 1
        """, (matched_county, month))
        r = cursor.fetchone()

        if not r:
            raise HTTPException(
                status_code=404,
                detail=f"Financial record for '{matched_county}' in month '{month}' not found."
            )

        scored = calculate_county_financial_risk(
            amount_owed_kes=float(r["amount_owed_kes"]),
            days_overdue=int(r["days_overdue"]),
            payment_history_score=float(r["payment_history_score"]),
            county_name=r["county"]
        )

        return {
            "county": r["county"],
            "risk_score": scored["risk_score"],
            "risk_tier": scored["risk_tier"],
            "tier_color": scored["tier_color"],
            "tier_badge": scored["tier_badge"],
            "amount_owed_kes": scored["amount_owed_kes"],
            "days_overdue": scored["days_overdue"],
            "payment_history_score": scored["payment_history_score"],
            "primary_driver": scored["primary_driver"],
            "month": r["month"],
            "factors": scored["factors"],
            "plain_language_summary": scored["plain_language_summary"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating scorecard for county '{county}': {str(e)}"
        )
