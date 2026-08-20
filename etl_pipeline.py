#!/usr/bin/env python3
"""End-to-end ETL pipeline for the Healthcare Supply-Chain Intelligence Platform.

Extract  -> raw CSV files exported by generate_data.py (output/)
Transform-> clean the 7 documented data-quality issues, build a star schema
            (dimensions + facts) and compute KPI / aggregate tables
Load     -> analytics/analytics.db (SQLite) plus CSV exports of dimensions,
            aggregates and KPIs

Run:
    python etl_pipeline.py                      # input=output, out=analytics
    python etl_pipeline.py --input-dir output_smoke --output-dir analytics_smoke
"""

import argparse
import math
import os
import sqlite3
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

REFERENCE_VISITS = 350.0
DOF_OVERSTOCK = 70.0
OVERSTOCK_FACTOR = 1.05


def read_csv(path):
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, engine="c")
    raw = raw.replace("", np.nan)
    return raw


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


class Etl:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.log = []
        self.rules = []

    def note(self, msg):
        self.log.append(msg)
        print(msg)

    def log_rule(self, issue_id, table, action, affected):
        self.rules.append({"issue_id": issue_id, "table": table, "action": action, "rows_affected": int(affected)})

    def extract(self):
        self.note(f"Extracting raw CSV files from {os.path.abspath(self.input_dir)}")
        self.d = {}
        for name in ["FACILITIES", "KEMSA_WAREHOUSES", "COMMODITIES", "SUPPLIERS",
                     "CONSUMPTION", "INVENTORY", "ORDERS", "SHIPMENTS", "BATCHES",
                     "REDISTRIBUTION_EVENTS", "DEMAND_EVENTS", "SCENARIO_LABELS"]:
            path = os.path.join(self.input_dir, f"{name}.csv")
            self.d[name] = read_csv(path)
        self.d["DATA_QUALITY_ISSUES"] = read_csv(os.path.join(self.input_dir, "DATA_QUALITY_ISSUES.csv"))
        for name, df in self.d.items():
            self.note(f"  {name:22s} {len(df):>10,} rows")
        return self

    def clean(self):
        self.note("Cleaning data-quality issues (catalogue in DATA_QUALITY_ISSUES.csv)")
        self._clean_facilities()
        self._clean_commodities()
        self._clean_warehouses()
        self._clean_consumption()
        self._clean_inventory()
        return self

    def _clean_facilities(self):
        f = self.d["FACILITIES"]
        n_missing = int(f["sub_county"].isna().sum())
        if n_missing:
            f["sub_county"] = f["sub_county"].fillna(f["county"] + " (unknown)")
        self.d["FACILITIES"] = f
        self.log_rule("ISSUE001", "FACILITIES", "imputed sub_county from county", n_missing)

    def _clean_commodities(self):
        c = self.d["COMMODITIES"]
        c["category"] = c["category"].str.strip().str.lower().str.replace(" ", "_", regex=False)
        c["commodity_name"] = c["commodity_name"].str.strip()
        for col in ["unit_of_measure", "dosage_form", "criticality_level"]:
            c[col] = c[col].str.strip()
        self.d["COMMODITIES"] = c
        self.log_rule("ISSUE002", "COMMODITIES", "normalised category case/whitespace", len(c))

    def _clean_warehouses(self):
        w = self.d["KEMSA_WAREHOUSES"]
        w["warehouse_name"] = w["warehouse_name"].str.strip()
        w["region"] = w["region"].str.strip()
        self.d["KEMSA_WAREHOUSES"] = w
        self.log_rule("ISSUE003", "KEMSA_WAREHOUSES", "stripped warehouse_name whitespace", len(w))

    def _clean_consumption(self):
        con = self.d["CONSUMPTION"]
        n_before = len(con)
        con = con.drop_duplicates(keep="first").reset_index(drop=True)
        n_dup = n_before - len(con)
        self.log_rule("ISSUE006", "CONSUMPTION", f"removed exact duplicates ({n_dup})", n_dup)

        con["quantity_consumed"] = to_num(con["quantity_consumed"])
        con["patient_demand_index"] = to_num(con["patient_demand_index"])
        con["seasonality_factor"] = to_num(con["seasonality_factor"])

        missing = con["quantity_consumed"].isna()
        if missing.any():
            med = con.loc[~missing & (con["data_quality_flag"] == "OK"), "quantity_consumed"].fillna(0)
            grp = con.loc[~missing, ["facility_id", "commodity_id", "quantity_consumed"]]
            med_map = grp.groupby(["facility_id", "commodity_id"])["quantity_consumed"].median()
            key = con.loc[missing, ["facility_id", "commodity_id"]].apply(tuple, axis=1)
            base_median = med_map.reindex(key).to_numpy()
            idx = con.loc[missing, "patient_demand_index"].fillna(1.0).to_numpy()
            imputed = np.round(np.maximum(0.0, base_median * idx), 1)
            con.loc[missing, "quantity_consumed"] = imputed
            con.loc[missing, "data_quality_flag"] = "IMPUTED"
            self.log_rule("ISSUE004", "CONSUMPTION", "imputed quantity_consumed (pdi x facility-commodity median)", int(missing.sum()))
        else:
            self.log_rule("ISSUE004", "CONSUMPTION", "no missing quantity_consumed found", 0)

        con["is_delayed_reporting"] = (con["data_quality_flag"] == "DELAYED_REPORTING").astype(int)
        n_delayed = int(con["is_delayed_reporting"].sum())
        self.log_rule("ISSUE005", "CONSUMPTION", "flagged DELAYED_REPORTING rows (kept values, marked)", n_delayed)
        self.d["CONSUMPTION"] = con
        self.note(f"  consumption cleaned: {n_before:,} -> {len(con):,} rows")

    def _clean_inventory(self):
        inv = self.d["INVENTORY"]
        for col in ["opening_stock", "quantity_received", "quantity_issued",
                    "quantity_adjusted", "closing_stock"]:
            inv[col] = to_num(inv[col])

        self.d["INVENTORY"] = inv

        n_null = int(inv["stock_status"].isna().sum())
        if n_null:
            self.note(f"  re-deriving {n_null:,} missing stock_status values")
        self.log_rule("ISSUE007", "INVENTORY", "re-derived missing stock_status from levels", n_null)

    def model(self):
        self.note("Building star schema (dimensions + facts) and KPI aggregates")
        self._build_dims()
        self._build_facts()
        self._build_aggregates()
        self._build_kpis()
        return self

    def _expected_demand(self):
        con = self.d["CONSUMPTION"]
        ok = con[con["quantity_consumed"].notna()]
        grp = ok.groupby(["facility_id", "commodity_id"])["quantity_consumed"].mean().round(3)
        grp.name = "expected_daily_demand"
        return grp

    def _build_dims(self):
        start, end = date(2024, 1, 1), date(2025, 12, 31)
        days = pd.date_range(start, end)
        self.dim_date = pd.DataFrame({
            "date_key": (days.year * 10000 + days.month * 100 + days.day).astype(int),
            "date": days.date.astype(str),
            "year": days.year,
            "month": days.month,
            "day": days.day,
            "month_name": days.strftime("%B"),
            "quarter": days.quarter,
            "week": days.isocalendar().week.astype(int),
            "day_of_week": days.dayofweek,
            "is_weekend": (days.dayofweek >= 5).astype(int),
        })
        self.d["DIM_DATE"] = self.dim_date

        fac = self.d["FACILITIES"].copy()
        fac["average_daily_patient_visits"] = to_num(fac["average_daily_patient_visits"])
        fac["bed_capacity"] = to_num(fac["bed_capacity"])
        fac["latitude"] = to_num(fac["latitude"])
        fac["longitude"] = to_num(fac["longitude"])
        visits = fac["average_daily_patient_visits"].fillna(0)
        fac["facility_size_tier"] = np.where(visits < 100, "Small",
                                    np.where(visits < 300, "Medium",
                                    np.where(visits < 800, "Large", "Referral")))
        fac["facility_key"] = fac["facility_id"].astype("category").cat.codes
        self.fac_map = dict(zip(fac["facility_id"], fac["facility_key"]))
        self.d["DIM_FACILITY"] = fac
        self.fac = fac

        com = self.d["COMMODITIES"].copy()
        for col in ["pack_size", "unit_cost", "lead_time_days", "minimum_stock_level",
                    "maximum_stock_level", "safety_stock_days", "shelf_life_days"]:
            com[col] = to_num(com[col])
        com["commodity_key"] = com["commodity_id"].astype("category").cat.codes
        self.com_map = dict(zip(com["commodity_id"], com["commodity_key"]))
        self.d["DIM_COMMODITY"] = com
        self.com = com

        sup = self.d["SUPPLIERS"].copy()
        sup["average_lead_time_days"] = to_num(sup["average_lead_time_days"])
        sup["on_time_delivery_rate"] = to_num(sup["on_time_delivery_rate"])
        sup["reliability_score"] = to_num(sup["reliability_score"])
        sup["supplier_key"] = sup["supplier_id"].astype("category").cat.codes
        self.sup_map = dict(zip(sup["supplier_id"], sup["supplier_key"]))
        self.d["DIM_SUPPLIER"] = sup

        wh = self.d["KEMSA_WAREHOUSES"].copy()
        wh["latitude"] = to_num(wh["latitude"])
        wh["longitude"] = to_num(wh["longitude"])
        wh["warehouse_key"] = wh["warehouse_id"].astype("category").cat.codes
        self.wh_map = dict(zip(wh["warehouse_id"], wh["warehouse_key"]))
        self.d["DIM_WAREHOUSE"] = wh

    def _date_key(self, series):
        s = pd.to_datetime(series)
        return (s.dt.year * 10000 + s.dt.month * 100 + s.dt.day).astype(int)

    def _build_facts(self):
        fac, com = self.fac, self.com
        expected = self._expected_demand()

        inv = self.d["INVENTORY"].copy()
        inv["facility_key"] = inv["facility_id"].map(self.fac_map)
        inv["commodity_key"] = inv["commodity_id"].map(self.com_map)
        inv["date_key"] = self._date_key(inv["date"])
        merged = inv[["facility_id", "commodity_id"]].merge(expected.reset_index(), on=["facility_id", "commodity_id"], how="left")
        expected_map = merged["expected_daily_demand"].fillna(1.0).to_numpy()
        inv["expected_daily_demand"] = expected_map
        inv["days_of_stock"] = np.round(np.divide(inv["closing_stock"], inv["expected_daily_demand"],
                                                  out=np.zeros(len(inv), dtype=float),
                                                  where=inv["expected_daily_demand"] > 0), 2)

        null_mask = inv["stock_status"].isna()
        if null_mask.any():
            fac_v = fac.set_index("facility_id")
            com_v = com.set_index("commodity_id")
            ratio = fac_v.loc[inv.loc[null_mask, "facility_id"], "average_daily_patient_visits"].to_numpy() / REFERENCE_VISITS
            min_s = com_v.loc[inv.loc[null_mask, "commodity_id"], "minimum_stock_level"].to_numpy() * ratio
            max_s = com_v.loc[inv.loc[null_mask, "commodity_id"], "maximum_stock_level"].to_numpy() * ratio
            safety = com_v.loc[inv.loc[null_mask, "commodity_id"], "safety_stock_days"].to_numpy()
            exp = inv.loc[null_mask, "expected_daily_demand"].to_numpy()
            min_s = np.maximum(1.0, min_s)
            max_s = np.maximum(2.0, max_s)
            max_s = np.maximum(max_s, min_s * 1.5)
            safety_level = safety * exp
            closing = inv.loc[null_mask, "closing_stock"].to_numpy()
            dofs = inv.loc[null_mask, "days_of_stock"].to_numpy()
            status = np.where(closing <= 0, "STOCKOUT",
                     np.where(closing < safety_level, "CRITICAL",
                     np.where(closing < min_s, "LOW",
                     np.where((closing > max_s * OVERSTOCK_FACTOR) | (dofs > DOF_OVERSTOCK), "OVERSTOCKED", "NORMAL"))))
            inv.loc[null_mask, "stock_status"] = status

        self.fact_inventory = inv[
            ["date_key", "facility_key", "commodity_key", "opening_stock", "quantity_received",
             "quantity_issued", "quantity_adjusted", "closing_stock", "stock_status",
             "expected_daily_demand", "days_of_stock"]]
        self.d["FACT_INVENTORY"] = self.fact_inventory

        con = self.d["CONSUMPTION"].copy()
        con["facility_key"] = con["facility_id"].map(self.fac_map)
        con["commodity_key"] = con["commodity_id"].map(self.com_map)
        con["date_key"] = self._date_key(con["date"])
        self.fact_consumption = con[
            ["date_key", "facility_key", "commodity_key", "quantity_consumed",
             "patient_demand_index", "seasonality_factor", "demand_event",
             "is_delayed_reporting", "data_quality_flag"]]
        self.d["FACT_CONSUMPTION"] = self.fact_consumption

        ords = self.d["ORDERS"].copy()
        ords["facility_key"] = ords["facility_id"].map(self.fac_map)
        ords["commodity_key"] = ords["commodity_id"].map(self.com_map)
        ords["warehouse_key"] = ords["warehouse_id"].map(self.wh_map)
        ords["supplier_key"] = ords["supplier_id"].map(self.sup_map)
        ords["date_key"] = self._date_key(ords["order_date"])
        for col in ["quantity_ordered", "quantity_fulfilled"]:
            ords[col] = to_num(ords[col])
        exp_del = pd.to_datetime(ords["expected_delivery_date"])
        act_del = pd.to_datetime(ords["actual_delivery_date"])
        ords["delay_days"] = ((act_del - exp_del).dt.days).fillna(0).clip(lower=0).astype(int)
        ords["lead_time_actual_days"] = ((act_del - pd.to_datetime(ords["order_date"])).dt.days).fillna(-1).astype(int)
        self.fact_orders = ords[
            ["date_key", "facility_key", "commodity_key", "warehouse_key", "supplier_key",
             "order_id", "quantity_ordered", "quantity_fulfilled", "order_status",
             "expected_delivery_date", "actual_delivery_date", "delay_days",
             "lead_time_actual_days", "priority_level"]]
        self.d["FACT_ORDERS"] = self.fact_orders

        shp = self.d["SHIPMENTS"].copy()
        shp["facility_key"] = shp["destination_id"].map(self.fac_map)
        shp["commodity_key"] = shp["commodity_id"].map(self.com_map)
        shp["date_key"] = self._date_key(shp["dispatch_date"])
        shp["quantity_shipped"] = to_num(shp["quantity_shipped"])
        shp["delay_days"] = to_num(shp["delay_days"]).fillna(0).astype(int)
        self.fact_shipments = shp[
            ["date_key", "facility_key", "commodity_key", "shipment_id", "order_id",
             "origin_type", "origin_id", "destination_type", "destination_id",
             "quantity_shipped", "dispatch_date", "expected_arrival_date",
             "actual_arrival_date", "transport_status", "delay_days"]]
        self.d["FACT_SHIPMENTS"] = self.fact_shipments

        bat = self.d["BATCHES"].copy()
        bat["facility_key"] = bat["facility_id"].map(self.fac_map)
        bat["commodity_key"] = bat["commodity_id"].map(self.com_map)
        for col in ["initial_quantity", "remaining_quantity"]:
            bat[col] = to_num(bat[col])
        bat["received_date"] = pd.to_datetime(bat["received_date"])
        bat["manufacturing_date"] = pd.to_datetime(bat["manufacturing_date"])
        bat["expiry_date"] = pd.to_datetime(bat["expiry_date"])
        end = date(2025, 12, 31)
        bat["days_to_expiry_at_end"] = (bat["expiry_date"] - pd.Timestamp(end)).dt.days
        bat["expired_units"] = np.where(bat["batch_status"] == "EXPIRED",
                                        bat["initial_quantity"] - bat["remaining_quantity"], 0.0)
        self.fact_batches = bat
        self.d["FACT_BATCHES"] = self.fact_batches

        red = self.d["REDISTRIBUTION_EVENTS"].copy()
        red["facility_key"] = red["source_facility_id"].map(self.fac_map)
        red["commodity_key"] = red["commodity_id"].map(self.com_map)
        red["date_key"] = self._date_key(red["date"])
        for col in ["quantity_available", "quantity_requested", "recommended_quantity",
                    "distance_km", "transport_cost", "source_days_of_stock",
                    "destination_days_of_stock"]:
            red[col] = to_num(red[col])
        self.fact_redistribution = red
        self.d["FACT_REDISTRIBUTION"] = self.fact_redistribution

    def _build_aggregates(self):
        inv = self.fact_inventory
        con = self.fact_consumption
        ords = self.fact_orders

        inv["year_month"] = (inv["date_key"] // 100).astype(int)
        con["year_month"] = (con["date_key"] // 100).astype(int)
        ords["year_month"] = (ords["date_key"] // 100).astype(int)

        g = inv.groupby(["facility_key", "commodity_key", "year_month"])
        st = g["stock_status"].value_counts().unstack(fill_value=0).reset_index()
        for col in ["STOCKOUT", "CRITICAL", "LOW", "NORMAL", "OVERSTOCKED"]:
            if col not in st.columns:
                st[col] = 0
        agg = g.agg(
            avg_closing=("closing_stock", "mean"),
            max_closing=("closing_stock", "max"),
            min_closing=("closing_stock", "min"),
            total_issued=("quantity_issued", "sum"),
            total_received=("quantity_received", "sum"),
            total_adjusted=("quantity_adjusted", "sum"),
            max_days_of_stock=("days_of_stock", "max"),
            min_days_of_stock=("days_of_stock", "min"),
            avg_days_of_stock=("days_of_stock", "mean"),
        ).reset_index()
        agg = agg.merge(st, on=["facility_key", "commodity_key", "year_month"], how="left")
        for col in ["STOCKOUT", "CRITICAL", "LOW", "NORMAL", "OVERSTOCKED"]:
            agg[col] = agg[col].fillna(0).astype(int)

        con_s = con.groupby(["facility_key", "commodity_key", "year_month"]).agg(
            total_consumed=("quantity_consumed", "sum")).reset_index()
        ord_s = ords.groupby(["facility_key", "commodity_key", "year_month"]).agg(
            orders_placed=("order_id", "count"),
            orders_delayed=("order_status", lambda s: (s == "DELAYED").sum()),
            orders_cancelled=("order_status", lambda s: (s == "CANCELLED").sum()),
            quantity_ordered=("quantity_ordered", "sum"),
            quantity_fulfilled=("quantity_fulfilled", "sum")).reset_index()

        a = agg.merge(con_s, on=["facility_key", "commodity_key", "year_month"], how="left")
        a = a.merge(ord_s, on=["facility_key", "commodity_key", "year_month"], how="left")
        a = a.fillna({"orders_placed": 0, "orders_delayed": 0, "orders_cancelled": 0,
                      "quantity_ordered": 0, "quantity_fulfilled": 0, "total_consumed": 0})
        self.d["AGG_FACILITY_COMMODITY_MONTH"] = a

        fc = fac_ids = None
        fc = a.groupby(["commodity_key", "year_month"]).agg(
            facility_days=("STOCKOUT", "count"),
            stockout_facility_days=("STOCKOUT", "sum"),
            critical_facility_days=("CRITICAL", "sum"),
            overstocked_facility_days=("OVERSTOCKED", "sum"),
            total_consumed=("total_consumed", "sum"),
            total_issued=("total_issued", "sum"),
            total_received=("total_received", "sum"),
            total_adjusted=("total_adjusted", "sum"),
            orders_placed=("orders_placed", "sum"),
            orders_delayed=("orders_delayed", "sum"),
            quantity_ordered=("quantity_ordered", "sum"),
            quantity_fulfilled=("quantity_fulfilled", "sum"),
            avg_days_of_stock=("avg_days_of_stock", "mean"),
        ).reset_index()
        self.d["AGG_COMMODITY_MONTH"] = fc

        ff = a.groupby(["facility_key", "year_month"]).agg(
            stockout_facility_days=("STOCKOUT", "sum"),
            critical_facility_days=("CRITICAL", "sum"),
            overstocked_facility_days=("OVERSTOCKED", "sum"),
            total_consumed=("total_consumed", "sum"),
            total_issued=("total_issued", "sum"),
            total_received=("total_received", "sum"),
            total_adjusted=("total_adjusted", "sum"),
            orders_placed=("orders_placed", "sum"),
            orders_delayed=("orders_delayed", "sum"),
            avg_days_of_stock=("avg_days_of_stock", "mean"),
        ).reset_index()
        self.d["AGG_FACILITY_MONTH"] = ff

        sup = self.fact_orders.copy()
        sup["year_month"] = (sup["date_key"] // 100).astype(int)
        sp = sup.groupby(["supplier_key", "year_month"]).agg(
            orders_placed=("order_id", "count"),
            orders_delayed=("order_status", lambda s: (s == "DELAYED").sum()),
            orders_cancelled=("order_status", lambda s: (s == "CANCELLED").sum()),
            orders_partial=("order_status", lambda s: (s == "PARTIALLY_FULFILLED").sum()),
            quantity_ordered=("quantity_ordered", "sum"),
            quantity_fulfilled=("quantity_fulfilled", "sum"),
            avg_delay_days=("delay_days", "mean"),
        ).reset_index()
        sp["on_time_delivery_rate"] = (1 - sp["orders_delayed"] / sp["orders_placed"].replace(0, np.nan)).round(3)
        sp["fill_rate"] = (sp["quantity_fulfilled"] / sp["quantity_ordered"].replace(0, np.nan)).round(3)
        self.d["AGG_SUPPLIER_MONTH"] = sp

    def _build_kpis(self):
        fac = self.d["DIM_FACILITY"][["facility_key", "facility_id", "facility_name", "facility_type", "county"]]
        com = self.d["DIM_COMMODITY"][["commodity_key", "commodity_id", "commodity_name", "category", "unit_cost"]]

        a = self.d["AGG_FACILITY_COMMODITY_MONTH"].merge(fac, on="facility_key").merge(com, on="commodity_key")
        a["units_short"] = (a["STOCKOUT"] * a["total_consumed"] / (a["STOCKOUT"] + a["NORMAL"] + a["LOW"] + a["CRITICAL"] + a["OVERSTOCKED"]).replace(0, np.nan)).round(0)
        a["units_short"] = a["units_short"].fillna(0)
        self.kpi_stockout = a[a["STOCKOUT"] > 0][
            ["year_month", "facility_id", "facility_name", "county", "commodity_id",
             "commodity_name", "category", "STOCKOUT", "units_short",
             "avg_days_of_stock", "orders_delayed"]].rename(
            columns={"STOCKOUT": "stockout_days", "avg_days_of_stock": "avg_days_of_stock"})
        self.kpi_stockout = self.kpi_stockout.sort_values("stockout_days", ascending=False).reset_index(drop=True)
        self.d["KPI_STOCKOUT"] = self.kpi_stockout

        self.kpi_overstock = a[a["OVERSTOCKED"] > 0][
            ["year_month", "facility_id", "facility_name", "county", "commodity_id",
             "commodity_name", "category", "OVERSTOCKED", "max_days_of_stock",
             "max_closing", "total_consumed"]].rename(columns={"OVERSTOCKED": "overstocked_days"})
        self.kpi_overstock = self.kpi_overstock.sort_values("overstocked_days", ascending=False).reset_index(drop=True)
        self.d["KPI_OVERSTOCK"] = self.kpi_overstock

        b = self.fact_batches.merge(com, on="commodity_key")
        be = b[b["batch_status"] == "EXPIRED"].groupby(["commodity_key", "facility_key"]).agg(
            expired_batches=("batch_id", "count"),
            expired_units=("expired_units", "sum")).reset_index()
        ba = b.groupby(["commodity_key", "facility_key"]).agg(
            total_batches=("batch_id", "count"),
            approaching_expiry=("batch_status", lambda s: (s == "APPROACHING_EXPIRY").sum())).reset_index()
        self.kpi_expiry = ba.merge(be, on=["commodity_key", "facility_key"], how="left").merge(fac, on="facility_key").merge(com, on="commodity_key")
        self.kpi_expiry["expired_batches"] = self.kpi_expiry["expired_batches"].fillna(0).astype(int)
        self.kpi_expiry["expired_units"] = self.kpi_expiry["expired_units"].fillna(0)
        self.kpi_expiry["wastage_value_kes"] = (self.kpi_expiry["expired_units"] * self.kpi_expiry["unit_cost"]).round(0)
        self.d["KPI_EXPIRY"] = self.kpi_expiry[
            ["facility_id", "facility_name", "commodity_id", "commodity_name",
             "total_batches", "approaching_expiry", "expired_batches",
             "expired_units", "wastage_value_kes"]].sort_values("wastage_value_kes", ascending=False).reset_index(drop=True)

        sp = self.d["AGG_SUPPLIER_MONTH"].merge(
            self.d["DIM_SUPPLIER"][["supplier_key", "supplier_id", "supplier_name"]], on="supplier_key")
        self.kpi_supplier = sp.groupby(["supplier_id", "supplier_name"]).agg(
            orders_placed=("orders_placed", "sum"),
            orders_delayed=("orders_delayed", "sum"),
            orders_cancelled=("orders_cancelled", "sum"),
            orders_partial=("orders_partial", "sum"),
            quantity_ordered=("quantity_ordered", "sum"),
            quantity_fulfilled=("quantity_fulfilled", "sum"),
            avg_delay_days=("avg_delay_days", "mean")).reset_index()
        self.kpi_supplier["on_time_delivery_rate"] = (1 - self.kpi_supplier["orders_delayed"] / self.kpi_supplier["orders_placed"]).round(3)
        self.kpi_supplier["fill_rate"] = (self.kpi_supplier["quantity_fulfilled"] / self.kpi_supplier["quantity_ordered"]).round(3)
        self.d["KPI_SUPPLIER"] = self.kpi_supplier.sort_values("orders_delayed", ascending=False).reset_index(drop=True)

        labels = self.d["SCENARIO_LABELS"]
        s3 = labels[labels["scenario_name"] == "S3_REDISTRIBUTION"]
        pairs = []
        for _, r in s3.iterrows():
            cid, role = r["commodity_id"], r["role"]
            fid = r["facility_id"]
            partners = s3[(s3["commodity_id"] == cid) & (s3["role"] != role)]["facility_id"].tolist()
            for p in partners:
                pairs.append((cid, fid if role == "source" else p, fid if role == "destination" else p))
        pairs = pd.DataFrame(pairs, columns=["commodity_id", "source_facility_id", "destination_facility_id"]).drop_duplicates()
        red = self.fact_redistribution[self.fact_redistribution["redistribution_status"] == "RECOMMENDED"]
        red = red.rename(columns={"source_facility_id": "src", "destination_facility_id": "dst"})
        chains = pairs.merge(red, left_on=["commodity_id", "source_facility_id", "destination_facility_id"],
                             right_on=["commodity_id", "src", "dst"], how="left")
        agg_chain = chains.groupby(["commodity_id", "source_facility_id", "destination_facility_id"]).agg(
            recommended_events=("recommended_quantity", "count"),
            total_recommended_units=("recommended_quantity", "sum"),
            avg_distance_km=("distance_km", "mean"),
            total_transport_cost=("transport_cost", "sum"),
            avg_source_dofs=("source_days_of_stock", "mean"),
            avg_dest_dofs=("destination_days_of_stock", "mean"),
        ).reset_index().merge(fac[["facility_id", "facility_name", "county", "facility_type"]].add_prefix("source_"),
                              left_on="source_facility_id", right_on="source_facility_id", how="left")
        agg_chain = agg_chain.merge(fac[["facility_id", "facility_name", "county", "facility_type"]].add_prefix("destination_"),
                                    left_on="destination_facility_id", right_on="destination_facility_id", how="left")
        agg_chain = agg_chain.merge(com[["commodity_id", "commodity_name", "unit_cost"]], on="commodity_id", how="left")
        dest_sout = self.kpi_stockout.groupby(["facility_id", "commodity_id"])["stockout_days"].sum().reset_index()
        agg_chain = agg_chain.merge(dest_sout.rename(columns={"stockout_days": "dest_stockout_days", "facility_id": "destination_facility_id"}),
                                    on=["destination_facility_id", "commodity_id"], how="left")
        agg_chain["dest_stockout_days"] = agg_chain["dest_stockout_days"].fillna(0)
        self.kpi_redistribution_chains = agg_chain
        self.d["KPI_REDISTRIBUTION_CHAINS"] = agg_chain

        ords = self.fact_orders.copy()
        ords = ords.merge(com[["commodity_key", "unit_cost"]], on="commodity_key")
        ords = ords.merge(fac[["facility_key", "facility_id"]], on="facility_key")
        ords["fulfilled_cost_kes"] = ords["quantity_fulfilled"] * ords["unit_cost"]
        baseline = ords.groupby(["facility_id", "commodity_key"]).agg(
            baseline_orders=("order_id", "count"),
            baseline_units=("quantity_fulfilled", "sum"),
            baseline_cost_kes=("fulfilled_cost_kes", "sum"),
            baseline_unit_cost=("unit_cost", "first")).reset_index()

        red_dest = self.fact_redistribution[self.fact_redistribution["redistribution_status"] == "RECOMMENDED"].copy()
        red_dest = red_dest.merge(fac[["facility_key", "facility_id"]], on="facility_key")
        intelligent = red_dest.groupby(["facility_id", "commodity_key"]).agg(
            redistributed_units=("recommended_quantity", "sum"),
            transport_cost_kes=("transport_cost", "sum"),
            redistribution_events=("redistribution_id", "count")).reset_index()
        bv = baseline.merge(intelligent, on=["facility_id", "commodity_key"], how="left")
        bv["redistributed_units"] = bv["redistributed_units"].fillna(0)
        bv["transport_cost_kes"] = bv["transport_cost_kes"].fillna(0)
        bv["redistribution_events"] = bv["redistribution_events"].fillna(0).astype(int)
        bv["redistributed_value_kes"] = (bv["redistributed_units"] * bv["baseline_unit_cost"]).round(0)
        bv["intelligent_cost_kes"] = (bv["baseline_cost_kes"] - bv["redistributed_value_kes"] + bv["transport_cost_kes"]).round(0)
        bv["savings_kes"] = (bv["baseline_cost_kes"] - bv["intelligent_cost_kes"]).round(0)
        bv = bv.rename(columns={"baseline_unit_cost": "unit_cost_kes"})
        bv = bv.merge(fac[["facility_key", "facility_id", "facility_name", "county"]],
                      on=["facility_id"], how="left")
        bv = bv.drop(columns=[c for c in bv.columns if c.endswith("_fac")])
        self.kpi_baseline_vs_intelligent = bv.sort_values("savings_kes", ascending=False).reset_index(drop=True)
        self.d["KPI_BASELINE_VS_INTELLIGENT"] = self.kpi_baseline_vs_intelligent

    def load(self):
        os.makedirs(self.output_dir, exist_ok=True)
        db_path = os.path.join(self.output_dir, "analytics.db")
        if os.path.exists(db_path):
            os.remove(db_path)
        conn = sqlite3.connect(db_path)
        self.note(f"Loading to {os.path.abspath(db_path)}")
        order = ["DIM_DATE", "DIM_FACILITY", "DIM_COMMODITY", "DIM_SUPPLIER", "DIM_WAREHOUSE",
                 "FACT_INVENTORY", "FACT_CONSUMPTION", "FACT_ORDERS", "FACT_SHIPMENTS",
                 "FACT_BATCHES", "FACT_REDISTRIBUTION",
                 "AGG_FACILITY_COMMODITY_MONTH", "AGG_COMMODITY_MONTH", "AGG_FACILITY_MONTH",
                 "AGG_SUPPLIER_MONTH", "KPI_STOCKOUT", "KPI_OVERSTOCK", "KPI_EXPIRY",
                 "KPI_SUPPLIER", "KPI_REDISTRIBUTION_CHAINS", "KPI_BASELINE_VS_INTELLIGENT"]
        for name in order:
            df = self.d[name]
            df.to_sql(name, conn, if_exists="replace", index=False, chunksize=200000)
            self.note(f"  {name:28s} {len(df):>10,} rows")

        run_log = pd.DataFrame([{
            "run_id": 1,
            "run_timestamp": datetime.now().isoformat(timespec="seconds"),
            "source_dir": self.input_dir,
            "input_rows": sum(len(v) for k, v in self.d.items() if not k.startswith("DIM") and not k.startswith("FACT") and not k.startswith("AGG") and not k.startswith("KPI")),
        }])
        run_log.to_sql("ETL_RUN_LOG", conn, if_exists="replace", index=False)
        rules = pd.DataFrame(self.rules)
        rules.to_sql("DQ_CLEANING_LOG", conn, if_exists="replace", index=False)
        self.note("  ETL_RUN_LOG          1 rows")
        self.note(f"  DQ_CLEANING_LOG      {len(rules)} rows")
        conn.close()

        small = ["DIM_DATE", "DIM_FACILITY", "DIM_COMMODITY", "DIM_SUPPLIER", "DIM_WAREHOUSE",
                 "AGG_COMMODITY_MONTH", "AGG_FACILITY_MONTH", "AGG_SUPPLIER_MONTH",
                 "KPI_STOCKOUT", "KPI_OVERSTOCK", "KPI_EXPIRY", "KPI_SUPPLIER",
                 "KPI_REDISTRIBUTION_CHAINS", "KPI_BASELINE_VS_INTELLIGENT",
                 "DQ_CLEANING_LOG", "ETL_RUN_LOG"]
        for name in small:
            df = self.d.get(name)
            if df is None:
                if name == "DQ_CLEANING_LOG":
                    df = pd.DataFrame(self.rules)
                else:
                    df = pd.DataFrame({"message": self.log})
            df.to_csv(os.path.join(self.output_dir, f"{name}.csv"), index=False)
        self.note(f"Exported {len(small)} tables as CSV to {self.output_dir}/")
        return self

    def validate(self):
        self.note("Validating analytics layer")
        inv = self.fact_inventory
        bad = int((inv["opening_stock"] + inv["quantity_received"] - inv["quantity_issued"]
                   + inv["quantity_adjusted"] - inv["closing_stock"]).abs().round(1).gt(0.05).sum())
        self.note(f"  inventory arithmetic inconsistent rows: {bad}")

        neg = int(inv[["opening_stock", "closing_stock", "quantity_received"]].lt(0).any(axis=1).sum())
        self.note(f"  negative opening/closing/received rows: {neg}")

        fk = int(self.fact_inventory["facility_key"].isna().sum() + self.fact_inventory["commodity_key"].isna().sum())
        self.note(f"  inventory rows with unresolved FK keys: {fk}")

        con = self.fact_consumption
        fk2 = int(con["facility_key"].isna().sum() + con["commodity_key"].isna().sum())
        self.note(f"  consumption rows with unresolved FK keys: {fk2}")

        red = self.fact_redistribution
        over = int(((red["redistribution_status"] == "RECOMMENDED") & (red["recommended_quantity"] > red["quantity_available"] + 0.01)).sum())
        self.note(f"  recommended redistribution exceeding availability: {over}")

        bat = self.fact_batches
        exp_bad = int((bat["expiry_date"] <= bat["received_date"]).sum())
        self.note(f"  batches expiring before/at received: {exp_bad}")

        ok = (bad == 0 and neg == 0 and fk == 0 and fk2 == 0 and over == 0 and exp_bad == 0)
        self.note(f"  ETL validation: {'PASS' if ok else 'FAIL'}")

    def run(self):
        self.extract().clean().model().load().validate()
        self.note("ETL complete.")


def main():
    ap = argparse.ArgumentParser(description="ETL pipeline for the healthcare supply-chain dataset")
    ap.add_argument("--input-dir", default="output", help="Source directory with raw CSVs (default: output)")
    ap.add_argument("--output-dir", default="analytics", help="Destination directory (default: analytics)")
    args = ap.parse_args()
    Etl(args.input_dir, args.output_dir).run()


if __name__ == "__main__":
    main()