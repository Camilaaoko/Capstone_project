"""Smart Redistribution Service for KEMSA Intelligence Platform.

Handles dynamic surplus/shortage matching, geodesic logistics optimization,
and the transactional Request/Approve/Reject state machine in transfer_requests.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import math
import uuid
import sqlite3

from backend.services.forecasting import project_pair_stockout


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance between two latitude/longitude coordinates on Earth in km."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return round(2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)), 1)


def find_surplus_matches_for_facility(
    db: sqlite3.Connection,
    destination_facility_id: str,
    commodity_id: Optional[str] = None,
    max_distance_km: float = 400.0,
    limit_per_commodity: int = 5
) -> Dict[str, Any]:
    """Finds nearby facilities holding verified excess stock of commodities experiencing shortage.
    Powers the Facility Dashboard's 'Nearby Surplus Finder'.
    """
    cursor = db.cursor()

    # 1. Fetch destination facility info
    cursor.execute("""
        SELECT facility_id, facility_name, county, sub_county, latitude, longitude, facility_key
        FROM DIM_FACILITY
        WHERE facility_id = ?
        LIMIT 1
    """, (destination_facility_id.strip(),))
    dest_fac = cursor.fetchone()
    if not dest_fac:
        return None

    dest_lat = float(dest_fac["latitude"])
    dest_lon = float(dest_fac["longitude"])
    dest_fac_key = dest_fac["facility_key"]

    # 2. Get latest inventory date
    cursor.execute("SELECT MAX(date_key) as max_date_key FROM FACT_INVENTORY")
    max_date_key = cursor.fetchone()["max_date_key"]

    cursor.execute("SELECT date FROM DIM_DATE WHERE date_key = ?", (max_date_key,))
    d_row = cursor.fetchone()
    inv_date_str = d_row["date"] if d_row else "2024-03-31"

    # 3. Fetch commodities at destination experiencing shortage (days of stock <= 60 or Critical/Warning)
    com_filter = "AND com.commodity_id = ?" if commodity_id else ""
    params = [dest_fac_key, max_date_key]
    if commodity_id:
        params.append(commodity_id.strip())

    cursor.execute(f"""
        SELECT 
            com.commodity_id,
            com.commodity_name,
            com.category,
            com.pack_size,
            com.unit_cost,
            com.safety_stock_days,
            i.closing_stock as dest_stock,
            i.expected_daily_demand as dest_demand,
            i.days_of_stock as dest_dofs
        FROM FACT_INVENTORY i
        JOIN DIM_COMMODITY com ON com.commodity_key = i.commodity_key
        WHERE i.facility_key = ? AND i.date_key = ? {com_filter}
        ORDER BY i.days_of_stock ASC
    """, params)
    dest_commodities = cursor.fetchall()

    shortage_items = []
    matches = []

    for dc in dest_commodities:
        d_stock = float(dc["dest_stock"])
        d_demand = float(dc["dest_demand"] or 1.0)
        safety_days = float(dc["safety_stock_days"] or 30.0)
        pack_size = float(dc["pack_size"] or 1.0)
        unit_cost = float(dc["unit_cost"] or 0.0)
        cid = dc["commodity_id"]
        cname = dc["commodity_name"]

        # Run forecast to establish urgency
        fc = project_pair_stockout(d_stock, d_demand, inv_date_str, horizon_days=90)
        risk_flag = fc["risk_flag"]
        days_to_stockout = fc["days_until_stockout"] or 999

        # Target shortage: Critical, Warning, or stock lower than safety stock threshold
        if risk_flag in ("Critical", "Warning") or d_stock < (safety_days * d_demand):
            deficit_units = max(pack_size, round((safety_days * d_demand) - d_stock, 1))
            shortage_items.append({
                "commodity_id": cid,
                "commodity_name": cname,
                "current_stock": d_stock,
                "days_until_stockout": days_to_stockout,
                "deficit_units": deficit_units,
                "risk_flag": risk_flag,
            })

            # Find potential donor facilities holding genuine surplus
            cursor.execute("""
                SELECT 
                    f.facility_id as src_facility_id,
                    f.facility_name as src_facility_name,
                    f.county as src_county,
                    f.latitude as src_lat,
                    f.longitude as src_lon,
                    i.closing_stock as src_stock,
                    i.expected_daily_demand as src_demand,
                    i.days_of_stock as src_dofs
                FROM FACT_INVENTORY i
                JOIN DIM_FACILITY f ON f.facility_key = i.facility_key
                JOIN DIM_COMMODITY com ON com.commodity_key = i.commodity_key
                WHERE i.date_key = ? 
                  AND com.commodity_id = ?
                  AND f.facility_id != ?
                  AND i.days_of_stock >= 45.0
                  AND i.closing_stock > (? * i.expected_daily_demand)
            """, (max_date_key, cid, destination_facility_id, safety_days))
            donors = cursor.fetchall()

            commodity_matches = []
            for d in donors:
                src_lat = float(d["src_lat"])
                src_lon = float(d["src_lon"])
                src_stock = float(d["src_stock"])
                src_demand = float(d["src_demand"] or 1.0)
                src_safe_level = safety_days * src_demand

                dist = haversine_km(src_lat, src_lon, dest_lat, dest_lon)
                if dist > max_distance_km:
                    continue

                available_surplus = max(0.0, src_stock - src_safe_level)
                if available_surplus < pack_size:
                    continue

                # Recommend minimum of surplus and deficit, rounded to pack size
                recommended = min(available_surplus, deficit_units)
                recommended = max(pack_size, math.floor(recommended / pack_size) * pack_size)

                # Prioritize: high surplus + short distance
                # Closer distance heavily boosted
                proximity_score = round((available_surplus / math.sqrt(dist + 1.0)) * (1.0 + 25.0 / (dist + 5.0)), 2)

                reason = (
                    f"{d['src_facility_name']} ({d['src_county']}) has {available_surplus:.0f} units surplus of "
                    f"{cname} ({dist} km away), while {dest_fac['facility_name']} is predicted to stock out in {days_to_stockout} days."
                )

                commodity_matches.append({
                    "source_facility_id": d["src_facility_id"],
                    "source_facility_name": d["src_facility_name"],
                    "source_county": d["src_county"],
                    "destination_facility_id": destination_facility_id,
                    "destination_facility_name": dest_fac["facility_name"],
                    "destination_county": dest_fac["county"],
                    "commodity_id": cid,
                    "commodity_name": cname,
                    "category": dc["category"],
                    "distance_km": dist,
                    "available_surplus_units": round(available_surplus, 1),
                    "required_deficit_units": round(deficit_units, 1),
                    "recommended_quantity": round(recommended, 1),
                    "unit_cost_kes": unit_cost,
                    "transfer_value_kes": round(recommended * unit_cost, 2),
                    "source_days_of_stock": round(float(d["src_dofs"]), 1),
                    "destination_days_of_stock": round(float(dc["dest_dofs"]), 1),
                    "priority_score": proximity_score,
                    "reason": reason
                })

            # Sort donors for this commodity: highest priority score first
            commodity_matches.sort(key=lambda m: m["priority_score"], reverse=True)
            matches.extend(commodity_matches[:limit_per_commodity])

    # Overall sort across all matched commodities
    matches.sort(key=lambda m: (m["distance_km"], -m["priority_score"]))

    return {
        "destination_facility_id": destination_facility_id,
        "destination_facility_name": dest_fac["facility_name"],
        "county": dest_fac["county"],
        "shortage_commodities_count": len(shortage_items),
        "matches_found": len(matches),
        "matches": matches
    }


def create_transfer_request(
    db: sqlite3.Connection,
    source_facility_id: str,
    destination_facility_id: str,
    commodity_id: str,
    requested_quantity: float,
    recommended_quantity: Optional[float] = None,
    requested_by: Optional[str] = None,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """Persists a new transfer request in 'pending' state into transfer_requests table.
    Powers the Facility Dashboard's 'Request Transfer' button.
    """
    cursor = db.cursor()

    # Lookup facilities
    cursor.execute("SELECT facility_id, facility_name, county, latitude, longitude FROM DIM_FACILITY WHERE facility_id = ?", (source_facility_id.strip(),))
    src = cursor.fetchone()
    if not src:
        raise ValueError(f"Source facility '{source_facility_id}' not found.")

    cursor.execute("SELECT facility_id, facility_name, county, latitude, longitude FROM DIM_FACILITY WHERE facility_id = ?", (destination_facility_id.strip(),))
    dst = cursor.fetchone()
    if not dst:
        raise ValueError(f"Destination facility '{destination_facility_id}' not found.")

    # Lookup commodity
    cursor.execute("SELECT commodity_id, commodity_name, unit_cost FROM DIM_COMMODITY WHERE commodity_id = ?", (commodity_id.strip(),))
    com = cursor.fetchone()
    if not com:
        raise ValueError(f"Commodity '{commodity_id}' not found.")

    # Calculate real distance
    dist = haversine_km(float(src["latitude"]), float(src["longitude"]), float(dst["latitude"]), float(dst["longitude"]))

    req_id = f"TR-{uuid.uuid4().hex[:8].upper()}"
    rec_qty = float(recommended_quantity) if recommended_quantity is not None else float(requested_quantity)
    req_by = requested_by.strip() if requested_by else f"Pharmacist ({dst['facility_name']})"
    req_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if not reason:
        reason = (
            f"Inter-facility stock redistribution: {src['facility_name']} ({src['county']}) "
            f"transferring {requested_quantity} units of {com['commodity_name']} to "
            f"{dst['facility_name']} ({dst['county']}) over {dist} km."
        )

    cursor.execute("""
        INSERT INTO transfer_requests (
            request_id,
            source_facility_id,
            destination_facility_id,
            commodity_id,
            requested_quantity,
            recommended_quantity,
            distance_km,
            status,
            requested_by,
            requested_at,
            reviewed_by,
            reviewed_at,
            reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, NULL, NULL, ?)
    """, (
        req_id,
        source_facility_id,
        destination_facility_id,
        commodity_id,
        float(requested_quantity),
        rec_qty,
        dist,
        req_by,
        req_at,
        reason
    ))
    db.commit()

    return {
        "request_id": req_id,
        "source_facility_id": source_facility_id,
        "source_facility_name": src["facility_name"],
        "source_county": src["county"],
        "destination_facility_id": destination_facility_id,
        "destination_facility_name": dst["facility_name"],
        "destination_county": dst["county"],
        "commodity_id": commodity_id,
        "commodity_name": com["commodity_name"],
        "requested_quantity": float(requested_quantity),
        "recommended_quantity": rec_qty,
        "distance_km": dist,
        "status": "pending",
        "requested_by": req_by,
        "requested_at": req_at,
        "reviewed_by": None,
        "reviewed_at": None,
        "reason": reason
    }


def get_pending_requests_by_county(db: sqlite3.Connection, county: str) -> Dict[str, Any]:
    """Retrieves all pending transfer requests where source or destination resides in specified county.
    Powers the County Pharmacist / Health Department review queue.
    """
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            tr.request_id,
            tr.source_facility_id,
            sf.facility_name as source_facility_name,
            sf.county as source_county,
            tr.destination_facility_id,
            df.facility_name as destination_facility_name,
            df.county as destination_county,
            tr.commodity_id,
            com.commodity_name,
            com.unit_cost,
            tr.requested_quantity,
            tr.recommended_quantity,
            tr.distance_km,
            tr.status,
            tr.requested_by,
            tr.requested_at,
            tr.reviewed_by,
            tr.reviewed_at,
            tr.reason
        FROM transfer_requests tr
        JOIN DIM_FACILITY sf ON sf.facility_id = tr.source_facility_id
        JOIN DIM_FACILITY df ON df.facility_id = tr.destination_facility_id
        JOIN DIM_COMMODITY com ON com.commodity_id = tr.commodity_id
        WHERE tr.status = 'pending'
          AND (LOWER(sf.county) = LOWER(?) OR LOWER(df.county) = LOWER(?))
        ORDER BY tr.requested_at DESC
    """, (county.strip(), county.strip()))
    rows = cursor.fetchall()

    items = []
    for r in rows:
        unit_cost = float(r["unit_cost"] or 0.0)
        qty = float(r["requested_quantity"])
        items.append({
            "request_id": r["request_id"],
            "source_facility_id": r["source_facility_id"],
            "source_facility_name": r["source_facility_name"],
            "source_county": r["source_county"],
            "destination_facility_id": r["destination_facility_id"],
            "destination_facility_name": r["destination_facility_name"],
            "destination_county": r["destination_county"],
            "commodity_id": r["commodity_id"],
            "commodity_name": r["commodity_name"],
            "requested_quantity": qty,
            "recommended_quantity": float(r["recommended_quantity"]),
            "transfer_value_kes": round(qty * unit_cost, 2),
            "distance_km": float(r["distance_km"]),
            "status": r["status"],
            "requested_by": r["requested_by"],
            "requested_at": r["requested_at"],
            "reviewed_by": r["reviewed_by"],
            "reviewed_at": r["reviewed_at"],
            "reason": r["reason"],
        })

    return {
        "county": county.title(),
        "pending_count": len(items),
        "requests": items
    }


def update_request_status(
    db: sqlite3.Connection,
    request_id: str,
    target_status: str,
    reviewed_by: Optional[str] = None
) -> Dict[str, Any]:
    """Transitions transfer request state to 'approved' or 'rejected'.
    Powers County Dashboard Approve / Reject decision buttons.
    """
    if target_status not in ("approved", "rejected", "completed"):
        raise ValueError(f"Invalid target status: {target_status}")

    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM transfer_requests WHERE request_id = ?
    """, (request_id.strip(),))
    existing = cursor.fetchone()
    if not existing:
        return None

    reviewer = reviewed_by.strip() if reviewed_by else "County Health Director"
    reviewed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE transfer_requests
        SET status = ?, reviewed_by = ?, reviewed_at = ?
        WHERE request_id = ?
    """, (target_status, reviewer, reviewed_at, request_id.strip()))
    db.commit()

    # Re-fetch full details
    cursor.execute("""
        SELECT 
            tr.request_id,
            tr.source_facility_id,
            sf.facility_name as source_facility_name,
            sf.county as source_county,
            tr.destination_facility_id,
            df.facility_name as destination_facility_name,
            df.county as destination_county,
            tr.commodity_id,
            com.commodity_name,
            tr.requested_quantity,
            tr.recommended_quantity,
            tr.distance_km,
            tr.status,
            tr.requested_by,
            tr.requested_at,
            tr.reviewed_by,
            tr.reviewed_at,
            tr.reason
        FROM transfer_requests tr
        JOIN DIM_FACILITY sf ON sf.facility_id = tr.source_facility_id
        JOIN DIM_FACILITY df ON df.facility_id = tr.destination_facility_id
        JOIN DIM_COMMODITY com ON com.commodity_id = tr.commodity_id
        WHERE tr.request_id = ?
    """, (request_id.strip(),))
    updated = cursor.fetchone()

    return dict(updated)


_cached_historical_baseline: Optional[Dict[str, Any]] = None
_cached_top_reallocated: Optional[List[Dict[str, Any]]] = None


def _get_cached_historical_redistribution(db: sqlite3.Connection):
    """Computes static historical metrics from 85k-row FACT_REDISTRIBUTION once and caches in-memory."""
    global _cached_historical_baseline, _cached_top_reallocated
    if _cached_historical_baseline is not None and _cached_top_reallocated is not None:
        return _cached_historical_baseline, _cached_top_reallocated

    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_transfers,
            COALESCE(SUM(fr.recommended_quantity), 0.0) as total_units,
            COALESCE(SUM(fr.recommended_quantity * com.unit_cost), 0.0) as total_value_kes
        FROM FACT_REDISTRIBUTION fr
        JOIN DIM_COMMODITY com ON com.commodity_id = fr.commodity_id
        WHERE fr.redistribution_status = 'RECOMMENDED'
    """)
    hist_row = cursor.fetchone()
    historical_transfers = int(hist_row["total_transfers"] or 0)
    historical_units = round(float(hist_row["total_units"] or 0.0), 1)
    historical_value_kes = round(float(hist_row["total_value_kes"] or 0.0), 2)

    _cached_historical_baseline = {
        "total_transfers": historical_transfers,
        "total_units": historical_units,
        "total_value_kes": historical_value_kes,
    }

    cursor.execute("""
        SELECT 
            c.commodity_id,
            c.commodity_name,
            c.category,
            c.unit_cost,
            COUNT(*) as transfer_count,
            SUM(fr.recommended_quantity) as total_units,
            SUM(fr.recommended_quantity * c.unit_cost) as total_value_kes
        FROM FACT_REDISTRIBUTION fr
        JOIN DIM_COMMODITY c ON fr.commodity_id = c.commodity_id
        WHERE fr.redistribution_status = 'RECOMMENDED'
        GROUP BY c.commodity_id, c.commodity_name, c.category, c.unit_cost
        ORDER BY total_units DESC
        LIMIT 5
    """)
    top_rows = cursor.fetchall()
    _cached_top_reallocated = [
        {
            "commodity_id": r["commodity_id"],
            "commodity_name": r["commodity_name"],
            "category": (r["category"] or "").title(),
            "transfer_count": int(r["transfer_count"]),
            "total_units": round(float(r["total_units"] or 0.0), 1),
            "total_value_kes": round(float(r["total_value_kes"] or 0.0), 2),
        }
        for r in top_rows
    ]

    return _cached_historical_baseline, _cached_top_reallocated


def get_redistribution_activity_summary(db: sqlite3.Connection) -> Dict[str, Any]:
    """Aggregates transfer request status counts, transferred quantities, and prevented wastage.
    Combines simulated 24-month network baseline (FACT_REDISTRIBUTION) with live interactive requests (transfer_requests).
    Powers Dashboard 1 (KEMSA National Leadership).
    """
    cursor = db.cursor()

    # 1. Live activity from transfer_requests (genuine audit trail)
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            SUM(requested_quantity) as total_units
        FROM transfer_requests
        GROUP BY status
    """)
    rows = cursor.fetchall()
    status_counts = {"pending": 0, "approved": 0, "rejected": 0, "completed": 0, "total": 0}
    live_approved_units = 0.0

    for r in rows:
        st = r["status"]
        c = r["count"]
        status_counts[st] = c
        status_counts["total"] += c
        if st in ("approved", "completed"):
            live_approved_units += float(r["total_units"] or 0.0)

    # Compute financial value and estimated wastage savings for live transfers
    cursor.execute("""
        SELECT 
            SUM(tr.requested_quantity * com.unit_cost) as total_approved_value
        FROM transfer_requests tr
        JOIN DIM_COMMODITY com ON com.commodity_id = tr.commodity_id
        WHERE tr.status IN ('approved', 'completed')
    """)
    val_row = cursor.fetchone()
    live_value_kes = round(float(val_row["total_approved_value"] or 0.0), 2)

    live_approved_count = status_counts["approved"] + status_counts["completed"]
    live_activity = {
        "status_counts": status_counts,
        "approved_transfers_count": live_approved_count,
        "total_units_transferred": round(live_approved_units, 1),
        "estimated_financial_value_kes": live_value_kes,
        "estimated_wastage_prevented_kes": live_value_kes,
    }

    # 2. Historical baseline from FACT_REDISTRIBUTION (status = 'RECOMMENDED', cached in-memory)
    historical_baseline, top_reallocated_commodities = _get_cached_historical_redistribution(db)
    historical_transfers = historical_baseline["total_transfers"]
    historical_units = historical_baseline["total_units"]
    historical_value_kes = historical_baseline["total_value_kes"]

    # 3. Combined total headline metrics
    combined_total_transfers = historical_transfers + live_approved_count
    combined_total_units = round(historical_units + live_approved_units, 1)
    combined_total_savings_kes = round(historical_value_kes + live_value_kes, 2)

    # Fetch recent transfer requests activity log (live audit trail)
    cursor.execute("""
        SELECT 
            tr.request_id,
            sf.facility_name as source_facility_name,
            sf.county as source_county,
            df.facility_name as destination_facility_name,
            df.county as destination_county,
            com.commodity_name,
            tr.requested_quantity,
            tr.distance_km,
            tr.status,
            tr.requested_at,
            tr.reviewed_at
        FROM transfer_requests tr
        JOIN DIM_FACILITY sf ON sf.facility_id = tr.source_facility_id
        JOIN DIM_FACILITY df ON df.facility_id = tr.destination_facility_id
        JOIN DIM_COMMODITY com ON com.commodity_id = tr.commodity_id
        ORDER BY tr.requested_at DESC
        LIMIT 15
    """)
    recent = [dict(row) for row in cursor.fetchall()]

    return {
        "status_counts": status_counts,
        "approved_transfers_count": combined_total_transfers,
        "total_units_transferred": combined_total_units,
        "estimated_financial_value_kes": combined_total_savings_kes,
        "estimated_wastage_prevented_kes": combined_total_savings_kes,
        "historical_baseline": historical_baseline,
        "live_activity": live_activity,
        "combined_total_savings_kes": combined_total_savings_kes,
        "combined_total_transfers": combined_total_transfers,
        "combined_total_units": combined_total_units,
        "recent_activity": recent,
        "top_reallocated_commodities": top_reallocated_commodities,
    }
