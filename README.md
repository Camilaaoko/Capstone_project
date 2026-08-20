# Healthcare Supply-Chain Intelligence Platform — Synthetic Dataset Generator

A fellowship capstone project. This repository generates a **fully synthetic**,
relational healthcare supply-chain dataset that imitates realistic behaviour for
Kenya's public health supply chain (KEMSA warehouses, counties, facilities,
suppliers, orders, shipments, inventory, expiry batches and redistribution
opportunities).

> **IMPORTANT DISCLAIMER**
> All data produced by this generator is **synthetic** — created from statistical
> models with a fixed random seed. It is **not** real KEMSA operational data, does
> not contain real patient information, and must not be presented as, or claimed
> to reproduce, confidential KEMSA records. Prices, names, lead times and
> facilities are invented for academic research and system development only.

---

## 1. Data architecture

```
                    ┌──────────────────────────────────────────────────────────┐
                    │                      MASTER DATA                        │
                    │  FACILITIES(150)  KEMSA_WAREHOUSES(6)  SUPPLIERS(12)    │
                    │  COMMODITIES(45)                    DEMAND_EVENTS(~10)  │
                    └──────────────────────────────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼──────────────────────────────────┐
        ▼                                 ▼                                  ▼
 CONSUMPTION                        INVENTORY (daily)                   ORDERS
 (daily, facility×commodity)   ←drives→  (daily balance)    ←placed when→  (reorder point)
   driven by:                            opening+received                  each order →
   • facility size                       -issued+adjusted = closing          warehouse + supplier
   • county factor                       FEFO batch draw-down
   • commodity seasonality         ┌─────┤ (status: NORMAL/LOW/CRITICAL/
   • demand events                  │     │  STOCKOUT/OVERSTOCKED)
   • trend + noise                  ▼     ▼
                              BATCHES  SHIPMENTS(per order, delays)
                              (expiry)       │
                                             ▼
                              REDISTRIBUTION_EVENTS (network matching:
                              surplus source → shortage destination)
                                             │
                              DATA_QUALITY_ISSUES (controlled noise for a
                              data-cleaning pipeline demo)
```

### Table relationships (referential integrity)

| Table | Foreign keys |
|---|---|
| `INVENTORY` | `facility_id → FACILITIES`, `commodity_id → COMMODITIES` |
| `CONSUMPTION` | `facility_id → FACILITIES`, `commodity_id → COMMODITIES` |
| `ORDERS` | `facility_id → FACILITIES`, `warehouse_id → KEMSA_WAREHOUSES`, `commodity_id → COMMODITIES`, `supplier_id → SUPPLIERS` |
| `SHIPMENTS` | `order_id → ORDERS`, `commodity_id → COMMODITIES` |
| `BATCHES` | `commodity_id → COMMODITIES`, `facility_id → FACILITIES` |
| `REDISTRIBUTION_EVENTS` | `commodity_id → COMMODITIES`, `source/destination_facility_id → FACILITIES` |

Every facility consumes a subset of commodities daily. Consumption drives the
daily inventory balance, which triggers reorder-point orders. Orders are shipped
(possibly delayed/partial) and arrive as expiry-tracked batches that are consumed
first-to-expire. Redistribution matches surplus facilities to projected-shortage
facilities after the simulation. Demand events (outbreaks, campaigns, seasons,
disruptions) modulate consumption and delivery delays.

## 2. Generated tables / files

Output directory `output/` (or `--output-dir`):

| File | Rows (approx.) | Description |
|---|---|---|
| `FACILITIES.csv` | 150 | 10 counties, 5 facility levels, coords, visits |
| `KEMSA_WAREHOUSES.csv` | 6 | 1 national + 5 regional warehouses |
| `COMMODITIES.csv` | 45 | 10 categories with synthetic costs / lead times / levels |
| `SUPPLIERS.csv` | 12 | Synthetic suppliers incl. 2 unreliable ones |
| `CONSUMPTION.csv` | ~4.93M | Daily consumption per facility–commodity (24 months) |
| `INVENTORY.csv` | ~4.93M | Daily balance; `closing = opening + received - issued + adjusted` |
| `ORDERS.csv` | ~61k | Reorder-point replenishment orders |
| `SHIPMENTS.csv` | ~59k | One shipment per delivered order |
| `BATCHES.csv` | ~66k | Received batches with manufacturing/expiry, FEFO draw-down |
| `REDISTRIBUTION_EVENTS.csv` | ~1.8M | Surplus→shortage matching; recommended + rejected |
| `DEMAND_EVENTS.csv` | 10 | Seasonal, outbreak, campaign, disruption, spike events |
| `DATA_QUALITY_ISSUES.csv` | 7 | Catalogue of intentionally introduced issues |
| `SCENARIO_LABELS.csv` | 49 | Ground-truth mapping of designed scenarios to facilities |
| `supply_chain.db` | — | SQLite database containing every table |

## 3. Getting started

```bash
pip install -r requirements.txt

# full dataset (default: 150 facilities, 45 commodities, 24 months)
python generate_data.py

# quick / reduced run for development
python generate_data.py --facilities 30 --commodities 10 --months 6 --output-dir output_quick

# skip the SQLite database (CSV only, faster)
python generate_data.py --no-sqlite

# reproducible: pass the same --seed
python generate_data.py --seed 42
```

The script prints a dataset summary and runs a full validation suite
(foreign keys, no negative inventory, inventory arithmetic, date ordering,
expiry-after-manufacturing, redistribution availability) at the end.

## 4. Built-in synthetic scenarios

| Scenario | How it is embedded | Where to look |
|---|---|---|
| S1 Stockout | "STRESS" pairs: rising demand (+45% over 24 mo), under-ordering, slow unreliable supplier | `INVENTORY.stock_status = STOCKOUT`; `SCENARIO_LABELS` role `shortage_destination` |
| S2 Surplus | "SURPLUS" pairs: over-ordering (factor 1.5) vs. stable demand | `INVENTORY.stock_status = OVERSTOCKED`; role `surplus_source` |
| S3 Redistribution | Designed surplus→shortage chains (12 chains across Amoxicillin, ORS, Paracetamol, Artemether-Lumefantrine, Mebendazole, Metformin, Ceftriaxone) | `REDISTRIBUTION_EVENTS` with `RECOMMENDED` |
| S4 Expiry risk | "EXPIRY" pairs: high stock, low consumption, short remaining shelf-life batches | `BATCHES.batch_status = APPROACHING_EXPIRY / EXPIRED` |
| S5 Supplier delay | Low `on_time_delivery_rate` suppliers (SUP006, SUP009) + a transport-strike event | `ORDERS.order_status = DELAYED`, `SHIPMENTS.delay_days` |
| S6 Demand spike | `EVA008 Flood_2025_Demand_Spike`, cholera outbreak, malaria seasons | `CONSUMPTION` under `DEMAND_EVENTS` |
| S7 Simultaneous surplus/shortage/normal | Amoxicillin in Nairobi: County Referral (surplus), Sub-County Hospital (shortage), Health Centre (normal) | `SCENARIO_LABELS` for `COM001` |

## 5. Baseline vs. intelligent-system experiment

The dataset is designed so you compute the comparison yourself:

- **Baseline:** a shortage facility places a new order and waits for delivery.
- **Intelligent:** predict shortage → search network → identify surplus → recommend
  redistribution → procure only if redistribution is insufficient.

Suggested metrics (SQLite / pandas):

```sql
-- stockout days
SELECT COUNT(*) FROM INVENTORY WHERE stock_status='STOCKOUT';

-- surplus units (units above maximum_stock_level)
-- join INVENTORY with COMMODITIES scaled by facility size

-- delayed orders
SELECT COUNT(*) FROM ORDERS WHERE order_status='DELAYED';

-- recommended redistribution vs new procurement
SELECT commodity_id, COUNT(*), SUM(recommended_quantity)
FROM REDISTRIBUTION_EVENTS WHERE redistribution_status='RECOMMENDED'
GROUP BY commodity_id;

-- expired / wasted quantity
SELECT commodity_id, SUM(initial_quantity - remaining_quantity)
FROM BATCHES WHERE batch_status='EXPIRED' GROUP BY commodity_id;
```

Example: for a designed chain (see `SCENARIO_LABELS`), take the destination's
`ORDERS` (baseline procurement cost) and compare against the source's
`REDISTRIBUTION_EVENTS.recommended_quantity * transport_cost` to show the
logistics cost of redistribution vs. emergency procurement.

## 6. Reproducibility & randomness

- Fixed seed: `RANDOM_SEED = 42` (override with `--seed`).
- Same seed ⇒ byte-identical CSV/SQLite output.
- Determinism note: an extra random draw is used to inject missing
  `stock_status`/`quantity_consumed` values; this does not affect reproducibility.

## 7. Validation guarantees

The generator validates and will report any violation of:

- foreign-key integrity across all tables
- no negative inventory quantities
- `closing_stock == opening_stock + quantity_received - quantity_issued + quantity_adjusted`
- no delivery date before order date; no arrival before dispatch
- `expiry_date` after `manufacturing_date` and `received_date`
- `recommended_quantity <= quantity_available` for recommended redistributions
  (by construction the source retains safety stock + lead-time buffer)

## 8. Analytics ETL pipeline

A full extract-transform-load pipeline (`etl_pipeline.py`) is included to turn the
raw synthetic export into an analytics-ready layer:

```bash
# run ETL on the default full dataset (output/ -> analytics/)
python etl_pipeline.py

# run ETL on a custom directory
python etl_pipeline.py --input-dir output_smoke --output-dir analytics_smoke
```

### What the ETL does

| Phase | Action |
|-------|--------|
| **Extract** | Reads all 13 raw CSVs from `output/` |
| **Clean** | Fixes the 7 documented data-quality issues:<br>• `FACILITIES`: impute 3 missing `sub_county` from county<br>• `COMMODITIES`: normalise `category` case & trailing spaces<br>• `KEMSA_WAREHOUSES`: strip `warehouse_name` whitespace<br>• `CONSUMPTION`: drop ~400 exact duplicates; impute ~0.4% missing `quantity_consumed` via `patient_demand_index × facility-commodity median`; flag `DELAYED_REPORTING` rows<br>• `INVENTORY`: re-derive ~0.3% missing `stock_status` from scaled levels & expected demand |
| **Model** | Builds a star schema:<br>• **Dimensions**: `DIM_DATE` (731 days), `DIM_FACILITY` (150), `DIM_COMMODITY` (45), `DIM_SUPPLIER` (12), `DIM_WAREHOUSE` (6)<br>• **Facts**: `FACT_INVENTORY` (4.9M), `FACT_CONSUMPTION` (4.9M), `FACT_ORDERS` (61k), `FACT_SHIPMENTS` (59k), `FACT_BATCHES` (66k), `FACT_REDISTRIBUTION` (1.8M)<br>• **Aggregates**: monthly facility×commodity, commodity, facility, supplier KPIs<br>• **KPI tables** for capstone demos: `KPI_STOCKOUT` (20k), `KPI_OVERSTOCK` (95k), `KPI_EXPIRY` (6.7k), `KPI_SUPPLIER` (9), `KPI_REDISTRIBUTION_CHAINS` (22 designed chains), `KPI_BASELINE_VS_INTELLIGENT` (6.7k) |
| **Load** | Writes `analytics/analytics.db` (SQLite, ~960 MB) + exports dimensions, aggregates & KPIs as CSV |
| **Validate** | Re-runs all FK, arithmetic, non-negative, date-ordering, expiry & redistribution checks on the analytics layer |

### Key analytics tables (query via `analytics/analytics.db`)

```sql
-- Top stockout facilities per commodity
SELECT facility_name, county, commodity_name, stockout_days
FROM KPI_STOCKOUT ORDER BY stockout_days DESC LIMIT 20;

-- Designed redistribution chains with destination stockout context
SELECT commodity_name, source_facility_name, destination_facility_name,
       recommended_events, total_recommended_units, dest_stockout_days
FROM KPI_REDISTRIBUTION_CHAINS ORDER BY dest_stockout_days DESC;

-- Supplier performance
SELECT supplier_name, orders_placed, orders_delayed, on_time_delivery_rate
FROM KPI_SUPPLIER ORDER BY orders_delayed DESC;

-- Expiry waste by commodity
SELECT commodity_name, SUM(expired_units) AS total_expired, SUM(wastage_value_kes)
FROM KPI_EXPIRY GROUP BY 1 ORDER BY 3 DESC;
```

### DQ cleaning log

Every cleaning action is recorded in `DQ_CLEANING_LOG` (also in `analytics.db`) with
issue ID, table, action taken, and rows affected — enabling full auditability.
