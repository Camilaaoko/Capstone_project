"""FastAPI application entrypoint for KEMSA Healthcare Supply Chain Intelligence Platform."""

from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

from backend.database import get_db, get_db_connection, init_db_tables
from contextlib import asynccontextmanager
from backend.routers.financial import router as financial_router
from backend.routers.forecasting import router as forecasting_router
from backend.routers.redistribution import router as redistribution_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database tables on startup once."""
    conn = get_db_connection()
    init_db_tables(conn)
    conn.close()
    yield


app = FastAPI(
    title="KEMSA Healthcare Supply Chain Intelligence Platform API",
    description="REST API backend powering predictive stockout analytics, financial risk scoring, and smart redistribution.",
    version="1.0.0",
    lifespan=lifespan
)

# -----------------------------------------------------------------------------
# CORS Middleware Configuration
# -----------------------------------------------------------------------------
# Supports local development, Render (https://*.onrender.com), Vercel, and custom domains.
import os

raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.vercel\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Include Modular Routers
# -----------------------------------------------------------------------------
app.include_router(financial_router)
app.include_router(forecasting_router)
app.include_router(redistribution_router)


# -----------------------------------------------------------------------------
# Pydantic Response Models
# -----------------------------------------------------------------------------
class HealthCheckResponse(BaseModel):
    status: str
    message: str


class FacilitySummary(BaseModel):
    facility_id: str
    facility_name: str
    county: str
    sub_county: Optional[str] = None
    facility_type: Optional[str] = None
    facility_level: Optional[str] = None
    facility_size_tier: Optional[str] = None
    bed_capacity: Optional[int] = None
    average_daily_patient_visits: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/", response_model=HealthCheckResponse, tags=["Health"])
def root_health_check():
    """Root health-check endpoint confirming API availability."""
    return {
        "status": "ok",
        "message": "KEMSA Intelligence Platform API"
    }


@app.get("/api/facilities", response_model=List[FacilitySummary], tags=["Facilities"])
def get_facilities(
    county: Optional[str] = Query(None, description="Optional county filter"),
    db: sqlite3.Connection = Depends(get_db)
):
    """Fetches list of monitored health facilities from DIM_FACILITY in analytics.db.
    Optionally filters by county (case-insensitive) to minimize network payload.
    """
    try:
        cursor = db.cursor()
        if county:
            cursor.execute("""
                SELECT 
                    facility_id,
                    facility_name,
                    county,
                    sub_county,
                    facility_type,
                    facility_level,
                    facility_size_tier,
                    bed_capacity,
                    average_daily_patient_visits,
                    latitude,
                    longitude
                FROM DIM_FACILITY
                WHERE LOWER(county) = LOWER(?)
                ORDER BY facility_name
            """, (county.strip(),))
        else:
            cursor.execute("""
                SELECT 
                    facility_id,
                    facility_name,
                    county,
                    sub_county,
                    facility_type,
                    facility_level,
                    facility_size_tier,
                    bed_capacity,
                    average_daily_patient_visits,
                    latitude,
                    longitude
                FROM DIM_FACILITY
                ORDER BY county, facility_name
            """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query error while retrieving facilities: {str(e)}"
        )

