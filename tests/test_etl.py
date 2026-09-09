"""Tests for the ETL Pipeline and Data Invariants."""

import os
import sqlite3
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "analytics" / "analytics.db"


@pytest.fixture(scope="module")
def db_conn():
    """Provides a connection to analytics.db."""
    if not DB_PATH.exists():
        pytest.skip("analytics.db not found. Run ETL pipeline first.")
    conn = sqlite3.connect(str(DB_PATH))
    yield conn
    conn.close()


def test_database_tables_exist(db_conn):
    """Verify all critical dimension and fact tables exist in SQLite."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    
    expected_tables = {
        "DIM_DATE", "DIM_FACILITY", "DIM_COMMODITY", "DIM_SUPPLIER", "DIM_WAREHOUSE",
        "FACT_INVENTORY", "FACT_CONSUMPTION", "FACT_ORDERS", "FACT_SHIPMENTS",
        "FACT_BATCHES", "FACT_REDISTRIBUTION", "FACT_COUNTY_DEBT",
        "KPI_STOCKOUT", "KPI_OVERSTOCK", "KPI_EXPIRY", "KPI_SUPPLIER",
        "KPI_REDISTRIBUTION_CHAINS", "KPI_BASELINE_VS_INTELLIGENT"
    }
    
    for table in expected_tables:
        assert table in tables, f"Expected table {table} not found in analytics.db"


def test_database_indexes_exist(db_conn):
    """Verify SQLite query acceleration indexes were created."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
    indexes = {row[0] for row in cursor.fetchall()}
    
    expected_indexes = [
        "idx_inv_fac_com",
        "idx_cons_fac_com",
        "idx_dim_fac_id",
        "idx_dim_com_id",
        "idx_county_debt"
    ]
    for idx in expected_indexes:
        assert idx in indexes, f"Expected index {idx} not found in analytics.db"


def test_inventory_conservation_invariant(db_conn):
    """Verify inventory balance arithmetic: closing = opening + received - issued + adjusted."""
    sample_df = pd.read_sql("""
        SELECT opening_stock, quantity_received, quantity_issued, quantity_adjusted, closing_stock
        FROM FACT_INVENTORY
        LIMIT 10000
    """, db_conn)
    
    calculated_closing = np.maximum(
        0.0,
        sample_df["opening_stock"]
        + sample_df["quantity_received"]
        - sample_df["quantity_issued"]
        + sample_df["quantity_adjusted"].fillna(0.0)
    )
    diff = (sample_df["closing_stock"] - calculated_closing).abs()
    assert (diff < 0.05).all(), "Inventory arithmetic equation violated in FACT_INVENTORY sample"


def test_no_negative_inventory_or_consumption(db_conn):
    """Verify non-negativity constraint on inventory and consumption."""
    neg_inv = pd.read_sql("""
        SELECT COUNT(*) as count FROM FACT_INVENTORY
        WHERE closing_stock < 0 OR opening_stock < 0
    """, db_conn).iloc[0]["count"]
    assert neg_inv == 0, "Found negative stock values in FACT_INVENTORY"

    neg_cons = pd.read_sql("""
        SELECT COUNT(*) as count FROM FACT_CONSUMPTION
        WHERE quantity_consumed < 0
    """, db_conn).iloc[0]["count"]
    assert neg_cons == 0, "Found negative consumption values in FACT_CONSUMPTION"


def test_foreign_key_referential_integrity(db_conn):
    """Verify foreign keys in FACT_INVENTORY resolve to DIM_FACILITY and DIM_COMMODITY."""
    orphan_fac = pd.read_sql("""
        SELECT COUNT(*) as count FROM FACT_INVENTORY i
        LEFT JOIN DIM_FACILITY f ON f.facility_key = i.facility_key
        WHERE f.facility_key IS NULL
    """, db_conn).iloc[0]["count"]
    assert orphan_fac == 0, "Found unresolved facility keys in FACT_INVENTORY"

    orphan_com = pd.read_sql("""
        SELECT COUNT(*) as count FROM FACT_INVENTORY i
        LEFT JOIN DIM_COMMODITY c ON c.commodity_key = i.commodity_key
        WHERE c.commodity_key IS NULL
    """, db_conn).iloc[0]["count"]
    assert orphan_com == 0, "Found unresolved commodity keys in FACT_INVENTORY"

