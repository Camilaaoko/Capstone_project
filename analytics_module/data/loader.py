"""Data loading utilities for analytics module."""

import sqlite3
from pathlib import Path
import pandas as pd
from analytics_module.config import ANALYTICS_DB, RANDOM_SEED, MAX_SAMPLE_PAIRS


def get_connection():
    return sqlite3.connect(ANALYTICS_DB)


def load_table(table_name, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    if close_conn:
        conn.close()
    return df


def load_facts():
    conn = get_connection()
    facts = {}
    for name in ["FACT_INVENTORY", "FACT_CONSUMPTION", "FACT_ORDERS",
                 "FACT_SHIPMENTS", "FACT_BATCHES", "FACT_REDISTRIBUTION"]:
        facts[name] = pd.read_sql(f"SELECT * FROM {name}", conn)
    conn.close()
    return facts


def load_dims():
    conn = get_connection()
    dims = {}
    for name in ["DIM_DATE", "DIM_FACILITY", "DIM_COMMODITY", "DIM_SUPPLIER", "DIM_WAREHOUSE"]:
        dims[name] = pd.read_sql(f"SELECT * FROM {name}", conn)
    conn.close()
    return dims


def load_kpis():
    conn = get_connection()
    kpis = {}
    for name in ["KPI_STOCKOUT", "KPI_OVERSTOCK", "KPI_EXPIRY", "KPI_SUPPLIER",
                 "KPI_REDISTRIBUTION_CHAINS", "KPI_BASELINE_VS_INTELLIGENT"]:
        kpis[name] = pd.read_sql(f"SELECT * FROM {name}", conn)
    conn.close()
    return kpis


def load_aggs():
    conn = get_connection()
    aggs = {}
    for name in ["AGG_FACILITY_COMMODITY_MONTH", "AGG_COMMODITY_MONTH",
                 "AGG_FACILITY_MONTH", "AGG_SUPPLIER_MONTH"]:
        aggs[name] = pd.read_sql(f"SELECT * FROM {name}", conn)
    conn.close()
    return aggs


def load_all():
    return {"facts": load_facts(), "dims": load_dims(), "kpis": load_kpis(), "aggs": load_aggs()}


def get_pair_time_series(facility_id, commodity_id, metric="quantity_consumed", conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    q = f"""
        SELECT date_key, {metric}
        FROM FACT_CONSUMPTION fc
        JOIN DIM_FACILITY f ON f.facility_key = fc.facility_key
        JOIN DIM_COMMODITY c ON c.commodity_key = fc.commodity_key
        WHERE f.facility_id = ? AND c.commodity_id = ?
        ORDER BY date_key
    """
    df = pd.read_sql(q, conn, params=(facility_id, commodity_id))
    if close_conn:
        conn.close()
    return df


def get_all_pairs():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT f.facility_id, f.facility_name, f.county, f.facility_type,
               c.commodity_id, c.commodity_name, c.category,
               fc.facility_key, fc.commodity_key
        FROM DIM_FACILITY f
        JOIN DIM_COMMODITY c ON 1=1
        JOIN FACT_INVENTORY fc ON fc.facility_key = f.facility_key AND fc.commodity_key = c.commodity_key
        GROUP BY f.facility_id, c.commodity_id
    """, conn)
    conn.close()
    return df


def sample_pairs(n=MAX_SAMPLE_PAIRS, stratify_by="county"):
    pairs = get_all_pairs()
    if stratify_by in pairs.columns:
        n_counties = max(1, len(pairs[stratify_by].unique()))
        samples_per_county = max(1, n // n_counties)
        return pairs.groupby(stratify_by, group_keys=False).apply(
            lambda x: x.sample(min(len(x), samples_per_county), random_state=RANDOM_SEED)
        ).reset_index(drop=True)
    return pairs.sample(min(n, len(pairs)), random_state=RANDOM_SEED)