"""Tests for Inventory Imbalance Detection and Allocation Optimization."""

import pytest
import numpy as np
import pandas as pd

from analytics_module.models.imbalance import (
    haversine_distance_km,
    detect_imbalances,
    find_matching_pairs,
    optimize_allocation,
    generate_allocation_plan
)


def test_haversine_distance_computation():
    """Verify Haversine distance matches expected Nairobi-to-Mombasa distance (~440-480km)."""
    # Nairobi: -1.286389, 36.817223
    # Mombasa: -4.043477, 39.668206
    nbi_lat, nbi_lon = -1.286389, 36.817223
    msa_lat, msa_lon = -4.043477, 39.668206
    
    dist = haversine_distance_km(nbi_lat, nbi_lon, msa_lat, msa_lon)
    assert 430 < dist < 500, f"Unexpected calculated distance: {dist:.1f} km"

    # Same location should yield 0 km
    assert haversine_distance_km(nbi_lat, nbi_lon, nbi_lat, nbi_lon) == pytest.approx(0.0, abs=1e-5)


def test_detect_imbalances():
    """Verify imbalance detection accurately categorizes overstocked vs understocked pairs."""
    imbalances = detect_imbalances(threshold_dofs=7)
    assert isinstance(imbalances, dict)
    assert "overstocked" in imbalances
    assert "understocked" in imbalances
    assert "summary" in imbalances

    overstocked = imbalances["overstocked"]
    understocked = imbalances["understocked"]
    assert not overstocked.empty
    assert not understocked.empty
    assert (overstocked["excess_units"] > 0).all()
    assert (understocked["deficit_units"] > 0).all()


def test_find_matching_pairs():
    """Verify matching pairs generates valid transfer opportunities within max distance."""
    imbalances = detect_imbalances(threshold_dofs=7)
    matches = find_matching_pairs(
        imbalances["overstocked"],
        imbalances["understocked"],
        max_distance_km=400
    )
    assert isinstance(matches, pd.DataFrame)
    if not matches.empty:
        assert (matches["source_facility_id"] != matches["dest_facility_id"]).all()
        assert (matches["distance_km"] <= 400).all()
        assert (matches["transferable_units"] > 0).all()
        assert "priority_score" in matches.columns


def test_optimize_allocation():
    """Verify allocation optimization respects budget constraints."""
    imbalances = detect_imbalances(threshold_dofs=7)
    matches = find_matching_pairs(imbalances["overstocked"], imbalances["understocked"], max_distance_km=400)
    
    if not matches.empty:
        budget_limit = 1000000.0  # 1M KES
        optimized = optimize_allocation(matches, budget_kes=budget_limit, max_distance_km=300)
        assert isinstance(optimized, pd.DataFrame)
        assert (optimized["distance_km"] <= 300).all()
        assert optimized["estimated_transport_cost"].sum() <= budget_limit

        plan = generate_allocation_plan(optimized)
        assert "recommendation" in plan.columns
        assert set(plan["recommendation"].unique()).issubset({"RECOMMEND", "SKIP"})

