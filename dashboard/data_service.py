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
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


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
    if county != "ALL":
        q_sout += f" AND county = '{county}'"
    if category != "ALL":
        q_sout += f" AND category = '{category}'"
    df_sout = pd.read_sql(q_sout, conn)

    # Expiry Wastage
    q_exp = """
        SELECT SUM(e.expired_units) as total_expired_units, SUM(e.wastage_value_kes) as total_wastage_kes
        FROM KPI_EXPIRY e
        JOIN DIM_FACILITY f ON f.facility_id = e.facility_id
        JOIN DIM_COMMODITY c ON c.commodity_id = e.commodity_id
        WHERE 1=1
    """
    if county != "ALL":
        q_exp += f" AND f.county = '{county}'"
    if category != "ALL":
        q_exp += f" AND c.category = '{category}'"
    df_exp = pd.read_sql(q_exp, conn)

    # Redistribution Savings
    q_sav = """
        SELECT SUM(b.savings_kes) as total_savings_kes, 
               SUM(b.redistributed_units) as total_redistributed_units,
               SUM(b.redistribution_events) as total_redistribution_events
        FROM KPI_BASELINE_VS_INTELLIGENT b
        JOIN DIM_COMMODITY c ON c.commodity_key = b.commodity_key
        WHERE 1=1
    """
    if county != "ALL":
        q_sav += f" AND b.county = '{county}'"
    if category != "ALL":
        q_sav += f" AND c.category = '{category}'"
    df_sav = pd.read_sql(q_sav, conn)

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
    if county != "ALL":
        q += f" AND county = '{county}'"
    if category != "ALL":
        q += f" AND category = '{category}'"
    q += f" ORDER BY stockout_days DESC LIMIT {top_n}"
    df = pd.read_sql(q, conn)
    conn.close()
    return df


def get_category_stockout_summary(county: str = "ALL") -> pd.DataFrame:
    """Aggregates stockout days by commodity category."""
    conn = get_connection()
    q = "SELECT category, SUM(stockout_days) as total_stockout_days, SUM(units_short) as total_units_short FROM KPI_STOCKOUT WHERE 1=1"
    if county != "ALL":
        q += f" AND county = '{county}'"
    q += " GROUP BY category ORDER BY total_stockout_days DESC"
    df = pd.read_sql(q, conn)
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
    if county != "ALL":
        q += f" AND f.county = '{county}'"
    if category != "ALL":
        q += f" AND c.category = '{category}'"
    q += f" GROUP BY e.commodity_name, c.category ORDER BY total_wastage_kes DESC LIMIT {top_n}"
    df = pd.read_sql(q, conn)
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


def get_county_summary() -> pd.DataFrame:
    """Returns county-level aggregation of stockouts, facilities, and consumption."""
    conn = get_connection()
    df = pd.read_sql("""
        SELECT s.county, 
               SUM(s.stockout_days) as stockout_days,
               COUNT(DISTINCT s.facility_id) as facilities_with_stockouts,
               COUNT(DISTINCT s.commodity_id) as commodities_impacted,
               SUM(s.units_short) as units_short
        FROM KPI_STOCKOUT s
        GROUP BY s.county
        ORDER BY stockout_days DESC
    """, conn)
    conn.close()
    return df


def get_facility_locations(county: str = "ALL") -> pd.DataFrame:
    """Fetches facility coordinates and attributes for geospatial mapping."""
    conn = get_connection()
    q = """
        SELECT f.facility_id, f.facility_name, f.county, f.sub_county, f.facility_type,
               f.facility_size_tier, f.latitude, f.longitude, f.average_daily_patient_visits,
               COALESCE(SUM(s.stockout_days), 0) as total_stockout_days
        FROM DIM_FACILITY f
        LEFT JOIN KPI_STOCKOUT s ON s.facility_id = f.facility_id
        WHERE f.latitude IS NOT NULL AND f.longitude IS NOT NULL
    """
    if county != "ALL":
        q += f" AND f.county = '{county}'"
    q += " GROUP BY f.facility_id ORDER BY total_stockout_days DESC"
    df = pd.read_sql(q, conn)
    conn.close()
    return df


def get_redistribution_recommendations(county: str = "ALL", category: str = "ALL", top_n: int = 50) -> pd.DataFrame:
    """Fetches recommended redistribution transfer events and chains."""
    conn = get_connection()
    q = """
        SELECT r.commodity_name, r.source_facility_name, r.source_county,
               r.destination_facility_name, r.destination_county,
               r.total_recommended_units, r.avg_distance_km, r.total_transport_cost,
               r.dest_stockout_days, r.unit_cost
        FROM KPI_REDISTRIBUTION_CHAINS r
        JOIN DIM_COMMODITY c ON c.commodity_id = r.commodity_id
        WHERE 1=1
    """
    if county != "ALL":
        q += f" AND (r.source_county = '{county}' OR r.destination_county = '{county}')"
    if category != "ALL":
        q += f" AND c.category = '{category}'"
    q += f" ORDER BY r.dest_stockout_days DESC, r.total_recommended_units DESC LIMIT {top_n}"
    df = pd.read_sql(q, conn)
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
    if county != "ALL":
        q += f" AND b.county = '{county}'"
    if category != "ALL":
        q += f" AND c.category = '{category}'"
    q += f" ORDER BY b.savings_kes DESC LIMIT {top_n}"
    df = pd.read_sql(q, conn)
    conn.close()
    return df


def get_facility_inventory_status(facility_id: str) -> pd.DataFrame:
    """Fetches current inventory levels and days of stock for a specific facility."""
    conn = get_connection()
    q = """
        SELECT c.commodity_name, c.category,
               AVG(i.closing_stock) as avg_closing_stock,
               AVG(i.days_of_stock) as avg_days_of_stock,
               i.stock_status,
               c.minimum_stock_level, c.maximum_stock_level, c.safety_stock_days
        FROM FACT_INVENTORY i
        JOIN DIM_FACILITY f ON f.facility_key = i.facility_key
        JOIN DIM_COMMODITY c ON c.commodity_key = i.commodity_key
        WHERE f.facility_id = ?
        GROUP BY c.commodity_name, i.stock_status
        ORDER BY avg_days_of_stock ASC
    """
    df = pd.read_sql(q, conn, params=(facility_id,))
    conn.close()
    return df


def get_facility_batch_expiry(facility_id: str) -> pd.DataFrame:
    """Fetches batch details and expiry status for a facility."""
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
        ORDER BY b.expiry_date ASC
    """
    df = pd.read_sql(q, conn, params=(facility_id,))
    conn.close()
    return df

