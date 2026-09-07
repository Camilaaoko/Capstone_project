"""Data service layer providing cached SQL queries over analytics.db."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

# Path resolving to project root analytics database
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "analytics" / "analytics.db"


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection to analytics.db."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Analytics database not found at {DB_PATH}. "
            "Please run 'python etl_pipeline.py' first to generate analytics.db."
        )
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=60.0)
    conn.execute("PRAGMA busy_timeout = 60000;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def get_filter_options() -> Dict[str, List[Dict[str, str]]]:
    """Fetches unique values for dashboard dropdown filters."""
    conn = get_connection()
    
    # Counties
    counties_df = pd.read_sql(
        "SELECT DISTINCT county FROM DIM_FACILITY WHERE county IS NOT NULL ORDER BY county", 
        conn
    )
    counties = [{"label": "All Counties (National)", "value": "ALL"}] + [
        {"label": c, "value": c} for c in counties_df["county"].tolist()
    ]
    
    # Commodity Categories
    cats_df = pd.read_sql(
        "SELECT DISTINCT category FROM DIM_COMMODITY WHERE category IS NOT NULL ORDER BY category", 
        conn
    )
    categories = [{"label": "All Categories", "value": "ALL"}] + [
        {"label": c.replace("_", " ").title(), "value": c} for c in cats_df["category"].tolist()
    ]

    # Facility tiers
    tiers_df = pd.read_sql(
        "SELECT DISTINCT facility_size_tier FROM DIM_FACILITY WHERE facility_size_tier IS NOT NULL ORDER BY facility_size_tier", 
        conn
    )
    tiers = [{"label": "All Facility Sizes", "value": "ALL"}] + [
        {"label": t, "value": t} for t in tiers_df["facility_size_tier"].tolist()
    ]

    # Facility list
    fac_df = pd.read_sql(
        "SELECT facility_id, facility_name, county FROM DIM_FACILITY ORDER BY facility_name",
        conn
    )
    facilities = [{"label": f"{r['facility_name']} ({r['county']})", "value": r["facility_id"]} 
                  for _, r in fac_df.iterrows()]

    conn.close()
    return {
        "counties": counties,
        "categories": categories,
        "tiers": tiers,
        "facilities": facilities
    }


def get_executive_kpis(county: str = "ALL", category: str = "ALL") -> Dict[str, Any]:
    """Calculates top-level KPI metrics for executive overview."""
    conn = get_connection()

    # Stockouts
    q_sout = "SELECT SUM(stockout_days) as total_stockout_days, SUM(units_short) as total_units_short FROM KPI_STOCKOUT WHERE 1=1"
    p_sout = []
    if county != "ALL":
        q_sout += " AND county = ?"
        p_sout.append(county)
    if category != "ALL":
        q_sout += " AND category = ?"
        p_sout.append(category)
    df_sout = pd.read_sql(q_sout, conn, params=p_sout)

    # Expiry Wastage
    q_exp = """
        SELECT SUM(e.expired_units) as total_expired_units, SUM(e.wastage_value_kes) as total_wastage_kes
        FROM KPI_EXPIRY e
        JOIN DIM_FACILITY f ON f.facility_id = e.facility_id
        JOIN DIM_COMMODITY c ON c.commodity_id = e.commodity_id
        WHERE 1=1
    """
    p_exp = []
    if county != "ALL":
        q_exp += " AND f.county = ?"
        p_exp.append(county)
    if category != "ALL":
        q_exp += " AND c.category = ?"
        p_exp.append(category)
    df_exp = pd.read_sql(q_exp, conn, params=p_exp)

    # Redistribution Savings
    q_sav = """
        SELECT SUM(b.savings_kes) as total_savings_kes, 
               SUM(b.redistributed_units) as total_redistributed_units,
               SUM(b.redistribution_events) as total_redistribution_events
        FROM KPI_BASELINE_VS_INTELLIGENT b
        JOIN DIM_COMMODITY c ON c.commodity_key = b.commodity_key
        WHERE 1=1
    """
    p_sav = []
    if county != "ALL":
        q_sav += " AND b.county = ?"
        p_sav.append(county)
    if category != "ALL":
        q_sav += " AND c.category = ?"
        p_sav.append(category)
    df_sav = pd.read_sql(q_sav, conn, params=p_sav)

    # Suppliers (National)
    df_sup = pd.read_sql(
        "SELECT AVG(on_time_delivery_rate) as avg_otd, AVG(fill_rate) as avg_fill FROM KPI_SUPPLIER", 
        conn
    )

    conn.close()

    return {
        "stockout_days": float(df_sout["total_stockout_days"].fillna(0).iloc[0]),
        "units_short": float(df_sout["total_units_short"].fillna(0).iloc[0]),
        "wastage_kes": float(df_exp["total_wastage_kes"].fillna(0).iloc[0]),
        "expired_units": float(df_exp["total_expired_units"].fillna(0).iloc[0]),
        "savings_kes": float(df_sav["total_savings_kes"].fillna(0).iloc[0]),
        "redistributed_units": float(df_sav["total_redistributed_units"].fillna(0).iloc[0]),
        "redistribution_events": int(df_sav["total_redistribution_events"].fillna(0).iloc[0]),
        "avg_otd_rate": float(df_sup["avg_otd"].fillna(0).iloc[0]) * 100.0,
        "avg_fill_rate": float(df_sup["avg_fill"].fillna(0).iloc[0]) * 100.0,
    }


def get_stockout_breakdown(county: str = "ALL", category: str = "ALL", top_n: int = 15) -> pd.DataFrame:
    """Returns top stockout facility-commodity pairs."""
    conn = get_connection()
    q = "SELECT facility_name, county, commodity_name, category, stockout_days, units_short, avg_days_of_stock FROM KPI_STOCKOUT WHERE 1=1"
    params = []
    if county != "ALL":
        q += " AND county = ?"
        params.append(county)
    if category != "ALL":
        q += " AND category = ?"
        params.append(category)
    q += f" ORDER BY stockout_days DESC LIMIT {int(top_n)}"
    df = pd.read_sql(q, conn, params=params)
    conn.close()
    return df


def get_category_stockout_summary(county: str = "ALL") -> pd.DataFrame:
    """Aggregates stockout days by commodity category."""
    conn = get_connection()
    q = "SELECT category, SUM(stockout_days) as total_stockout_days, SUM(units_short) as total_units_short FROM KPI_STOCKOUT WHERE 1=1"
    params = []
    if county != "ALL":
        q += " AND county = ?"
        params.append(county)
    q += " GROUP BY category ORDER BY total_stockout_days DESC"
    df = pd.read_sql(q, conn, params=params)
    conn.close()
    return df


def get_expiry_waste_by_commodity(county: str = "ALL", category: str = "ALL", top_n: int = 15) -> pd.DataFrame:
    """Fetches highest expiry wastage commodities."""
    conn = get_connection()
    q = """
        SELECT e.commodity_name, c.category, SUM(e.expired_units) as total_expired_units, 
               SUM(e.wastage_value_kes) as total_wastage_kes
        FROM KPI_EXPIRY e
        JOIN DIM_FACILITY f ON f.facility_id = e.facility_id
        JOIN DIM_COMMODITY c ON c.commodity_id = e.commodity_id
        WHERE 1=1
    """
    params = []
    if county != "ALL":
        q += " AND f.county = ?"
        params.append(county)
    if category != "ALL":
        q += " AND c.category = ?"
        params.append(category)
    q += f" GROUP BY e.commodity_name, c.category ORDER BY total_wastage_kes DESC LIMIT {int(top_n)}"
    df = pd.read_sql(q, conn, params=params)
    conn.close()
    return df


def get_supplier_performance() -> pd.DataFrame:
    """Returns supplier performance ratings."""
    conn = get_connection()
    df = pd.read_sql("""
        SELECT supplier_name, orders_placed, orders_delayed, orders_cancelled,
               quantity_ordered, quantity_fulfilled, avg_delay_days,
               on_time_delivery_rate, fill_rate
        FROM KPI_SUPPLIER
        ORDER BY orders_delayed DESC
    """, conn)
    conn.close()
    return df


def get_county_summary(county: str = "ALL", category: str = "ALL", tier: str = "ALL") -> pd.DataFrame:
    """Returns county or sub-county level aggregation of stockouts, facilities, and consumption."""
    conn = get_connection()
    is_single_county = county != "ALL"
    group_col = "f.sub_county as location_name, f.county" if is_single_county else "s.county as location_name, s.county"
    
    q = f"""
        SELECT {group_col},
               SUM(s.stockout_days) as stockout_days,
               COUNT(DISTINCT s.facility_id) as facilities_with_stockouts,
               COUNT(DISTINCT s.commodity_id) as commodities_impacted,
               SUM(s.units_short) as units_short
        FROM KPI_STOCKOUT s
        JOIN DIM_FACILITY f ON f.facility_id = s.facility_id
        JOIN DIM_COMMODITY c ON c.commodity_id = s.commodity_id
        WHERE 1=1
    """
    if county != "ALL":
        q += f" AND s.county = '{county}'"
    if category != "ALL":
        q += f" AND c.category = '{category}'"
    if tier != "ALL":
        q += f" AND f.facility_size_tier = '{tier}'"
        
    q += f" GROUP BY location_name ORDER BY stockout_days DESC"
    df = pd.read_sql(q, conn)
    conn.close()
    return df


def get_facility_locations(county: str = "ALL", category: str = "ALL", tier: str = "ALL") -> pd.DataFrame:
    """Fetches facility coordinates and attributes for geospatial mapping with multi-filter support."""
    conn = get_connection()
    
    where_clauses = ["f.latitude IS NOT NULL", "f.longitude IS NOT NULL"]
    if county != "ALL":
        where_clauses.append(f"f.county = '{county}'")
    if tier != "ALL":
        where_clauses.append(f"f.facility_size_tier = '{tier}'")
        
    sout_where = "1=1"
    if category != "ALL":
        sout_where += f" AND s.category = '{category}'"
        
    where_str = " AND ".join(where_clauses)
    
    q = f"""
        SELECT f.facility_id, f.facility_name, f.county, f.sub_county, f.facility_type,
               f.facility_level, f.facility_size_tier, f.latitude, f.longitude, 
               f.bed_capacity, f.average_daily_patient_visits,
               COALESCE(SUM(s.stockout_days), 0) as total_stockout_days,
               COALESCE(SUM(s.units_short), 0) as total_units_short,
               COUNT(DISTINCT s.commodity_id) as commodities_short_count
        FROM DIM_FACILITY f
        LEFT JOIN (
            SELECT facility_id, commodity_id, stockout_days, units_short, category 
            FROM KPI_STOCKOUT s 
            WHERE {sout_where}
        ) s ON s.facility_id = f.facility_id
        WHERE {where_str}
        GROUP BY f.facility_id 
        ORDER BY total_stockout_days DESC
    """
    df = pd.read_sql(q, conn)
    conn.close()
    return df


def get_warehouse_locations() -> pd.DataFrame:
    """Fetches KEMSA central and regional supply depot locations for network mapping."""
    conn = get_connection()
    df = pd.read_sql("""
        SELECT warehouse_id, warehouse_name, region, county, latitude, longitude,
               storage_capacity_units, warehouse_status
        FROM DIM_WAREHOUSE
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY storage_capacity_units DESC
    """, conn)
    conn.close()
    return df


def get_warehouse_detail_stats(warehouse_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves operational and supply network statistics for a selected KEMSA depot."""
    conn = get_connection()
    wh = pd.read_sql("SELECT * FROM DIM_WAREHOUSE WHERE warehouse_id = ?", conn, params=(warehouse_id,))
    if wh.empty:
        conn.close()
        return None
    info = wh.iloc[0].to_dict()
    w_key = info.get("warehouse_key")
    
    # Count facilities in region/county
    fac_count = pd.read_sql(
        "SELECT COUNT(*) as c FROM DIM_FACILITY WHERE county = ?", 
        conn, params=(info.get("county", ""),)
    )['c'].iloc[0]
    
    orders_stat = pd.read_sql("""
        SELECT COUNT(*) as total_orders, 
               COALESCE(SUM(quantity_ordered), 0) as total_qty_ordered,
               COALESCE(SUM(quantity_fulfilled), 0) as total_qty_fulfilled,
               COALESCE(SUM(CASE WHEN order_status = 'DELAYED' THEN 1 ELSE 0 END), 0) as delayed_orders
        FROM FACT_ORDERS
        WHERE warehouse_key = ?
    """, conn, params=(w_key,))
    
    conn.close()
    return {
        "info": info,
        "facilities_served": int(fac_count),
        "orders": orders_stat.iloc[0].to_dict() if not orders_stat.empty else {}
    }




def get_facility_detail_stats(facility_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves deep-dive operational, stockout, expiry, and redistribution intelligence for a selected facility."""
    conn = get_connection()
    fac = pd.read_sql("SELECT * FROM DIM_FACILITY WHERE facility_id = ?", conn, params=(facility_id,))
    if fac.empty:
        conn.close()
        return None
    info = fac.iloc[0].to_dict()
    facility_name = info.get("facility_name", "")

    # Stockouts breakdown
    stockouts = pd.read_sql("""
        SELECT commodity_name, category, SUM(stockout_days) as stockout_days, 
               SUM(units_short) as units_short, AVG(avg_days_of_stock) as avg_dos,
               MAX(orders_delayed) as orders_delayed
        FROM KPI_STOCKOUT 
        WHERE facility_id = ?
        GROUP BY commodity_name, category
        ORDER BY stockout_days DESC
    """, conn, params=(facility_id,))

    # Expiry wastage
    expiry = pd.read_sql("""
        SELECT commodity_name, SUM(expired_units) as expired_units, 
               SUM(wastage_value_kes) as wastage_value_kes,
               SUM(approaching_expiry) as approaching_expiry_batches
        FROM KPI_EXPIRY 
        WHERE facility_id = ?
        GROUP BY commodity_name
        ORDER BY wastage_value_kes DESC
    """, conn, params=(facility_id,))

    # AI Redistribution chains (incoming & outgoing)
    redist_out = pd.read_sql("""
        SELECT commodity_name, destination_facility_name as partner_facility, destination_county as partner_county,
               total_recommended_units, avg_distance_km, total_transport_cost, 'SURPLUS DONOR' as role
        FROM KPI_REDISTRIBUTION_CHAINS
        WHERE source_facility_id = ? OR source_facility_name = ?
    """, conn, params=(facility_id, facility_name))

    redist_in = pd.read_sql("""
        SELECT commodity_name, source_facility_name as partner_facility, source_county as partner_county,
               total_recommended_units, avg_distance_km, total_transport_cost, 'SHORTAGE RECIPIENT' as role
        FROM KPI_REDISTRIBUTION_CHAINS
        WHERE destination_facility_id = ? OR destination_facility_name = ?
    """, conn, params=(facility_id, facility_name))

    redist = pd.concat([redist_out, redist_in], ignore_index=True)
    conn.close()

    return {
        "info": info,
        "stockouts": stockouts,
        "expiry": expiry,
        "redistribution": redist,
        "total_stockout_days": int(stockouts["stockout_days"].sum()) if not stockouts.empty else 0,
        "total_units_short": int(stockouts["units_short"].sum()) if not stockouts.empty else 0,
        "total_wastage_kes": float(expiry["wastage_value_kes"].sum()) if not expiry.empty else 0.0,
        "approaching_batches": int(expiry["approaching_expiry_batches"].sum()) if not expiry.empty else 0,
        "total_transfers_count": len(redist)
    }


def get_redistribution_recommendations(county: str = "ALL", category: str = "ALL", top_n: int = 50) -> pd.DataFrame:
    """Fetches recommended redistribution transfer events and chains."""
    conn = get_connection()
    q = """
        SELECT r.commodity_name, r.category, r.source_facility_name, r.source_county,
               r.destination_facility_name, r.destination_county,
               r.total_recommended_units, r.avg_distance_km, r.total_transport_cost,
               r.dest_stockout_days, r.unit_cost
        FROM KPI_REDISTRIBUTION_CHAINS r
        WHERE r.total_recommended_units > 0
    """
    params = []
    if county != "ALL":
        q += " AND (r.source_county = ? OR r.destination_county = ?)"
        params.extend([county, county])
    if category != "ALL":
        q += " AND r.category = ?"
        params.append(category)
    q += f" ORDER BY r.total_recommended_units DESC, r.dest_stockout_days DESC LIMIT {int(top_n)}"
    df = pd.read_sql(q, conn, params=params)
    conn.close()
    return df


def get_savings_comparison(county: str = "ALL", category: str = "ALL", top_n: int = 30) -> pd.DataFrame:
    """Fetches Baseline procurement vs Intelligent redistribution savings."""
    conn = get_connection()
    q = """
        SELECT b.facility_name, b.county, c.commodity_name, c.category,
               b.baseline_cost_kes, b.intelligent_cost_kes, b.savings_kes,
               b.redistributed_units, b.transport_cost_kes
        FROM KPI_BASELINE_VS_INTELLIGENT b
        JOIN DIM_COMMODITY c ON c.commodity_key = b.commodity_key
        WHERE 1=1
    """
    params = []
    if county != "ALL":
        q += " AND b.county = ?"
        params.append(county)
    if category != "ALL":
        q += " AND c.category = ?"
        params.append(category)
    q += f" ORDER BY b.savings_kes DESC LIMIT {int(top_n)}"
    df = pd.read_sql(q, conn, params=params)
    conn.close()
    return df


def get_facility_inventory_status(facility_id: str) -> pd.DataFrame:
    """Fetches current inventory levels, safety thresholds, and days of stock for a specific facility."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT facility_key FROM DIM_FACILITY WHERE facility_id = ?", (facility_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return pd.DataFrame()
    f_key = row[0]

    cur.execute("SELECT MAX(date_key) FROM FACT_INVENTORY WHERE facility_key = ?", (f_key,))
    max_date_row = cur.fetchone()
    max_date = max_date_row[0] if max_date_row and max_date_row[0] else 20251231

    q = """
        SELECT c.commodity_name, c.category,
               ROUND(i.closing_stock, 0) as closing_stock,
               ROUND(i.closing_stock, 0) as avg_closing_stock,
               ROUND(i.days_of_stock, 1) as days_of_stock,
               ROUND(i.days_of_stock, 1) as avg_days_of_stock,
               c.safety_stock_days,
               c.minimum_stock_level,
               c.maximum_stock_level,
               CASE 
                   WHEN i.closing_stock <= 0 OR i.days_of_stock <= 0 THEN 'STOCKOUT'
                   WHEN i.days_of_stock <= c.safety_stock_days THEN 'CRITICAL'
                   WHEN i.days_of_stock <= c.safety_stock_days * 2 THEN 'LOW'
                   WHEN i.days_of_stock <= c.safety_stock_days * 6 THEN 'NORMAL'
                   ELSE 'OVERSTOCKED'
               END as stock_status,
               ROUND(avg_tab.avg_dos, 1) as historical_avg_dos,
               avg_tab.total_stockout_days
        FROM FACT_INVENTORY i
        JOIN DIM_COMMODITY c ON c.commodity_key = i.commodity_key
        JOIN (
            SELECT commodity_key, 
                   AVG(days_of_stock) as avg_dos,
                   SUM(CASE WHEN stock_status = 'STOCKOUT' THEN 1 ELSE 0 END) as total_stockout_days
            FROM FACT_INVENTORY
            WHERE facility_key = ?
            GROUP BY commodity_key
        ) avg_tab ON avg_tab.commodity_key = i.commodity_key
        WHERE i.facility_key = ? AND i.date_key = ?
        ORDER BY i.days_of_stock ASC
    """
    df = pd.read_sql(q, conn, params=(f_key, f_key, max_date))
    conn.close()
    return df


def get_facility_batch_expiry(facility_id: str) -> pd.DataFrame:
    """Fetches active and at-risk batch details prioritized by FEFO (First Expiry First Out)."""
    conn = get_connection()
    q = """
        SELECT b.batch_id as batch_number, c.commodity_name, c.category,
               b.initial_quantity, b.remaining_quantity,
               b.manufacturing_date, b.expiry_date, b.batch_status,
               b.days_to_expiry_at_end
        FROM FACT_BATCHES b
        JOIN DIM_FACILITY f ON f.facility_key = b.facility_key
        JOIN DIM_COMMODITY c ON c.commodity_key = b.commodity_key
        WHERE f.facility_id = ?
        ORDER BY 
            CASE 
                WHEN b.remaining_quantity > 0 AND b.days_to_expiry_at_end BETWEEN 0 AND 90 THEN 1
                WHEN b.remaining_quantity > 0 AND b.batch_status = 'APPROACHING_EXPIRY' THEN 2
                WHEN b.remaining_quantity > 0 THEN 3
                WHEN b.batch_status = 'EXPIRED' THEN 4
                ELSE 5
            END ASC,
            b.expiry_date ASC
    """
    df = pd.read_sql(q, conn, params=(facility_id,))
    conn.close()
    return df
