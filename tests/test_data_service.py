"""Tests for Dashboard Data Service layer and SQL query methods."""

import pytest
import pandas as pd
from pathlib import Path

from dashboard.data_service import (
    get_filter_options,
    get_executive_kpis,
    get_stockout_breakdown,
    get_category_stockout_summary,
    get_expiry_waste_by_commodity,
    get_supplier_performance,
    get_county_summary,
    get_facility_locations,
    get_redistribution_recommendations,
    get_savings_comparison,
    get_facility_inventory_status,
    get_facility_batch_expiry
)


def test_get_filter_options():
    options = get_filter_options()
    assert isinstance(options, dict)
    assert "counties" in options and len(options["counties"]) > 1
    assert "categories" in options and len(options["categories"]) > 1
    assert "facilities" in options and len(options["facilities"]) > 1


def test_get_executive_kpis():
    # Test national aggregate
    kpis = get_executive_kpis(county="ALL", category="ALL")
    assert isinstance(kpis, dict)
    assert "stockout_days" in kpis
    assert "wastage_kes" in kpis
    assert "savings_kes" in kpis
    assert "avg_otd_rate" in kpis
    assert kpis["stockout_days"] >= 0

    # Test filtered aggregate (Nairobi)
    kpis_nairobi = get_executive_kpis(county="Nairobi", category="ALL")
    assert isinstance(kpis_nairobi, dict)


def test_get_stockout_breakdown():
    df = get_stockout_breakdown(county="ALL", category="ALL", top_n=10)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "facility_name" in df.columns
    assert "stockout_days" in df.columns


def test_get_category_stockout_summary():
    df = get_category_stockout_summary(county="ALL")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "category" in df.columns
    assert "total_stockout_days" in df.columns


def test_get_facility_locations():
    df = get_facility_locations(county="ALL")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert "facility_name" in df.columns
    # Verify GPS coordinates are in Kenya region
    assert df["latitude"].between(-5.0, 5.5).all()
    assert df["longitude"].between(33.0, 42.5).all()


def test_get_redistribution_recommendations():
    df = get_redistribution_recommendations(county="ALL", category="ALL", top_n=20)
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "commodity_name" in df.columns
        assert "total_recommended_units" in df.columns
        assert "total_transport_cost" in df.columns


def test_get_facility_inventory_status():
    options = get_filter_options()
    facility_id = options["facilities"][0]["value"]
    df = get_facility_inventory_status(facility_id)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "commodity_name" in df.columns
    assert "avg_days_of_stock" in df.columns

