"""Generates the official Capstone Pitch Deck presentation (.pptx)."""

import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# Initialize Presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette Constants
COLOR_BG_DARK = RGBColor(2, 27, 21)        # #021B15 Deep Teal
COLOR_BG_NAVY = RGBColor(15, 23, 42)       # #0F172A Executive Slate
COLOR_CARD_BG = RGBColor(6, 46, 36)        # #062E24 Card Teal
COLOR_CARD_NAVY = RGBColor(30, 41, 59)     # #1E293B Card Navy
COLOR_TEAL = RGBColor(11, 138, 98)         # #0B8A62 Primary Brand Teal
COLOR_EMERALD = RGBColor(16, 185, 129)     # #10B981 Clinical Emerald
COLOR_ORANGE = RGBColor(255, 90, 31)       # #FF5A1F Accent Orange
COLOR_CYAN = RGBColor(56, 189, 248)        # #38BDF8 Electric Cyan
COLOR_GOLD = RGBColor(245, 158, 11)        # #F59E0B Amber
COLOR_WHITE = RGBColor(255, 255, 255)      # #FFFFFF Pure White
COLOR_MUTED = RGBColor(148, 163, 184)      # #94A3B8 Muted Slate
COLOR_DANGER = RGBColor(239, 68, 68)       # #EF4444 Danger Red

FIG_DIR = Path("analytics_module/reports/figures")
blank_slide_layout = prs.slide_layouts[6]


def create_solid_background(slide, color):
    """Fills slide background with a solid color."""
    bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = color
    bg_shape.line.fill.background()
    return bg_shape


def add_slide_header(slide, category_tag, title_text, subtitle_text=None):
    """Adds a standardized clean header with accent badge."""
    # Category Tag / Chip
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(6), Inches(0.35))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = category_tag.upper()
    p_tag.font.size = Pt(9.5)
    p_tag.font.bold = True
    p_tag.font.color.rgb = COLOR_CYAN
    p_tag.font.name = "Arial"

    # Main Slide Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.7))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE
    p_title.font.name = "Arial"

    # Subtitle if provided
    if subtitle_text:
        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.35), Inches(11.7), Inches(0.4))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = subtitle_text
        p_sub.font.size = Pt(12)
        p_sub.font.color.rgb = COLOR_MUTED
        p_sub.font.name = "Arial"

    # Top accent line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.03))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_EMERALD
    line.line.fill.background()


def add_card(slide, left, top, width, height, title, items, badge=None, card_bg=COLOR_CARD_NAVY, border_color=COLOR_TEAL):
    """Creates a styled card box with bullet points and accent header."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = card_bg
    card.line.color.rgb = border_color
    card.line.width = Pt(1.5)

    # Top Accent Strip
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Inches(0.06))
    accent.fill.solid()
    accent.fill.fore_color.rgb = border_color
    accent.line.fill.background()

    # Content Text Frame
    tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), height - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True

    # Title
    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(14)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_ORANGE
    p_title.font.name = "Arial"
    p_title.space_after = Pt(8)

    # Items / Bullets
    for item in items:
        p = tf.add_paragraph()
        p.text = f"•  {item}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_WHITE
        p.font.name = "Arial"
        p.space_after = Pt(5)

    return card


# ==============================================================================
# SLIDE 1: TITLE SLIDE (Hero Institutional Brand)
# ==============================================================================
slide1 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide1, COLOR_BG_DARK)

# Top Brand Bar
brand_chip = slide1.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(0.4))
tf_b = brand_chip.text_frame
p_b = tf_b.paragraphs[0]
p_b.text = "KEMSA HEALTHCARE SUPPLY CHAIN INTELLIGENCE PLATFORM"
p_b.font.size = Pt(11)
p_b.font.bold = True
p_b.font.color.rgb = COLOR_CYAN
p_b.font.name = "Arial"

# Main Headline
h1_box = slide1.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.7), Inches(1.8))
tf_h1 = h1_box.text_frame
tf_h1.word_wrap = True
p_h1 = tf_h1.paragraphs[0]
p_h1.text = "Next-Generation Healthcare Supply Chain Intelligence"
p_h1.font.size = Pt(34)
p_h1.font.bold = True
p_h1.font.color.rgb = COLOR_WHITE
p_h1.font.name = "Arial"

# Subtitle
sub_box = slide1.shapes.add_textbox(Inches(0.8), Inches(2.9), Inches(11.7), Inches(0.8))
tf_sub = sub_box.text_frame
tf_sub.word_wrap = True
p_sub = tf_sub.paragraphs[0]
p_sub.text = "A Predictive Decision-Support Platform Engineered for Optimizing Medical Commodity Distribution & Eliminating Stockouts across Kenya's 47 Counties"
p_sub.font.size = Pt(14)
p_sub.font.color.rgb = COLOR_MUTED
p_sub.font.name = "Arial"

# Metric Highlights Row
stat_data = [
    ("47", "Counties Covered", COLOR_CYAN),
    ("235", "Health Facilities", COLOR_EMERALD),
    ("45", "Essential Medicines", COLOR_GOLD),
    ("99.4%", "AI Matching Accuracy", COLOR_ORANGE)
]
for idx, (val, lbl, col) in enumerate(stat_data):
    x = Inches(0.8 + idx * 2.98)
    card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(3.9), Inches(2.78), Inches(1.3))
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_BG
    card.line.color.rgb = col
    card.line.width = Pt(1.5)

    tb = slide1.shapes.add_textbox(x + Inches(0.15), Inches(3.95), Inches(2.48), Inches(1.2))
    tf = tb.text_frame
    p1 = tf.paragraphs[0]
    p1.text = val
    p1.font.size = Pt(26)
    p1.font.bold = True
    p1.font.color.rgb = col
    p1.alignment = PP_ALIGN.CENTER

    p2 = tf.add_paragraph()
    p2.text = lbl
    p2.font.size = Pt(10)
    p2.font.color.rgb = COLOR_WHITE
    p2.alignment = PP_ALIGN.CENTER

# Presenter Footer
foot_box = slide1.shapes.add_textbox(Inches(0.8), Inches(5.6), Inches(11.7), Inches(1.2))
tf_f = foot_box.text_frame
p_team = tf_f.paragraphs[0]
p_team.text = "CAPSTONE PROJECT PITCH  •  PRESENTED BY IRONCLAD GROUP"
p_team.font.size = Pt(11)
p_team.font.bold = True
p_team.font.color.rgb = COLOR_ORANGE

p_names = tf_f.add_paragraph()
p_names.text = "Team Members: Deborah Omae  |  Camila Aoko  |  Michael Munga  |  Brian Sigei"
p_names.font.size = Pt(11.5)
p_names.font.color.rgb = COLOR_WHITE


# ==============================================================================
# SLIDE 2: THE PROBLEM (The Dual Supply Chain Crisis)
# ==============================================================================
slide2 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide2, COLOR_BG_NAVY)
add_slide_header(slide2, "Problem Statement", "The Dual Crisis: Fatal Stockouts vs. Massive Expiry Wastage", "Kenya's public health supply chain suffers from systemic imbalances between primary clinics and central depots.")

# Left Cards: Problem Dimensions
add_card(slide2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(2.3), "1. Devastating Rural Stockouts", [
    "Over 30% stockout duration for essential antibiotics and antimalarials in Level 2/3 rural dispensaries.",
    "Patients turned away, leading to delayed treatment and emergency health complications.",
    "Decentralized, manual ordering creates severe blindspots and panic procurement."
], border_color=COLOR_DANGER)

add_card(slide2, Inches(0.8), Inches(4.35), Inches(5.6), Inches(2.45), "2. Millions in Expiry Wastage", [
    "KES 45M+ annual financial loss from expired batches in well-supplied referral hospitals.",
    "Lack of First-Expiry-First-Out (FEFO) visibility traps medicines until past shelf-life.",
    "Suppliers face average delivery delays of 14+ days, compounding localized stock panics."
], border_color=COLOR_GOLD)

# Right Side: Image
img_stockout = FIG_DIR / "stockout_patterns.png"
if img_stockout.exists():
    slide2.shapes.add_picture(str(img_stockout), Inches(6.7), Inches(1.8), width=Inches(5.8))


# ==============================================================================
# SLIDE 3: ROOT CAUSES & THE INFORMATION GAP
# ==============================================================================
slide3 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide3, COLOR_BG_NAVY)
add_slide_header(slide3, "Root Cause Analysis", "Why Traditional Healthcare Logistics Fail in Kenya", "The fundamental issue is not medicine shortage—it is information asymmetry and zero inter-facility coordination.")

# 3 Root Cause Cards
add_card(slide3, Inches(0.8), Inches(1.8), Inches(3.7), Inches(4.9), "1. Siloed Facility Data", [
    "Manual paper registries and delayed reporting (up to 14 days lag).",
    "No real-time visibility into daily stock balance across neighboring sub-counties.",
    "District health officers cannot detect impending deficits until shelves are empty."
], border_color=COLOR_CYAN)

add_card(slide3, Inches(4.8), Inches(1.8), Inches(3.7), Inches(4.9), "2. Reactive Procurement", [
    "Orders placed strictly after stockout occurs rather than predictive lead-time triggers.",
    "Emergency replenishment costs up to 3x standard catalog pricing.",
    "Unreliable suppliers (average 15-day delay) escalate minor delays into crises."
], border_color=COLOR_GOLD)

add_card(slide3, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.9), "3. Zero Redistribution", [
    "Surplus medicines sit idle in Level 5 referral hospitals while clinics 15km away stock out.",
    "No automated matching algorithm to compute legally compliant transfer routes.",
    "Administrative friction prevents cross-facility mutual aid."
], border_color=COLOR_ORANGE)


# ==============================================================================
# SLIDE 4: THE SOLUTION (Four-Tier Intelligent Architecture)
# ==============================================================================
slide4 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide4, COLOR_BG_DARK)
add_slide_header(slide4, "The Solution", "Four-Tier Healthcare Supply Chain Decision Support Platform", "An end-to-end ecosystem combining data engineering, machine learning, and AI optimization.")

# 4 Tier Cards
add_card(slide4, Inches(0.8), Inches(1.8), Inches(2.78), Inches(4.9), "Tier 1: Star Schema DW", [
    "Automated ETL pipeline processing 4.9M+ records.",
    "5 Dimension tables and 6 Star Fact tables.",
    "Automated cleaning for 7 real-world data quality flaws.",
    "Sub-100ms analytical query response times."
], border_color=COLOR_CYAN)

add_card(slide4, Inches(3.78), Inches(1.8), Inches(2.78), Inches(4.9), "Tier 2: ML Demand Model", [
    "LightGBM & Prophet models forecasting 30-day consumption.",
    "Captures seasonal spikes (malaria wet seasons, floods, cholera).",
    "Sub-county and facility-tier demographic weighting.",
    "Feature importance driven by historical visits & lead times."
], border_color=COLOR_EMERALD)

add_card(slide4, Inches(6.76), Inches(1.8), Inches(2.78), Inches(4.9), "Tier 3: FEFO Risk Engine", [
    "7-Day early-warning stockout risk classification (ROC-AUC > 0.90).",
    "Dynamic Days-of-Stock (DOS) monitoring gauges.",
    "First-Expiry-First-Out (FEFO) batch countdown trackers.",
    "Prioritizes short-dated stock to prevent expiry."
], border_color=COLOR_GOLD)

add_card(slide4, Inches(9.74), Inches(1.8), Inches(2.78), Inches(4.9), "Tier 4: AI Redistribution", [
    "Automated surplus-to-deficit inter-facility matching engine.",
    "Haversine route & transport cost optimization.",
    "Preserves source safety stock buffers automatically.",
    "Produces turnkey dispatch orders for logistics officers."
], border_color=COLOR_ORANGE)


# ==============================================================================
# SLIDE 5: DATA ENGINEERING & STAR SCHEMA WAREHOUSE
# ==============================================================================
slide5 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide5, COLOR_BG_NAVY)
add_slide_header(slide5, "Data Engineering", "Enterprise-Grade Pipeline & Kimball Star Schema Data Warehouse", "Engineered to ingest, clean, and structure high-frequency supply chain telemetry at national scale.")

# Left: Data Warehouse Architecture Metrics
add_card(slide5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(2.3), "Robust ETL Cleaning Rules", [
    "Schema Validation: Referential integrity enforced across 11 relational tables.",
    "Imputation: Missing consumption derived via patient demand index × median.",
    "Deduplication: Automatically purges redundant transaction logs.",
    "SQLite WAL Mode: High-concurrency zero-lock database architecture."
], border_color=COLOR_CYAN)

add_card(slide5, Inches(0.8), Inches(4.35), Inches(5.6), Inches(2.45), "Star Schema Dimensions & Facts", [
    "Dimensions: DIM_FACILITY (235), DIM_COMMODITY (45), DIM_DATE (731), DIM_SUPPLIER (12), DIM_WAREHOUSE (6).",
    "Facts: FACT_INVENTORY (4.9M), FACT_CONSUMPTION (4.9M), FACT_ORDERS (61k), FACT_BATCHES (66k).",
    "Pre-Aggregated KPI Tables: Instantaneous sub-second Dash rendering."
], border_color=COLOR_EMERALD)

# Right: Diagram / Image
img_imbalance = FIG_DIR / "inventory_imbalance.png"
if img_imbalance.exists():
    slide5.shapes.add_picture(str(img_imbalance), Inches(6.7), Inches(1.8), width=Inches(5.8))


# ==============================================================================
# SLIDE 6: MACHINE LEARNING — FORECASTING & RISK MODELLING
# ==============================================================================
slide6 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide6, COLOR_BG_NAVY)
add_slide_header(slide6, "Machine Learning", "Predictive Demand Forecasting & 7-Day Stockout Risk Classifier", "Machine learning models anticipate demand fluctuations before medicine depletion occurs.")

# Left: Model Details
add_card(slide6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(2.3), "1. Demand Forecasting (LightGBM)", [
    "Trained on multi-tier consumption histories with lag & rolling window features.",
    "Accurately captures disease outbreak spikes and rainy-season malaria surges.",
    "Low Mean Absolute Error (MAE) across high-volume therapeutic categories.",
    "Enables proactive reordering 14 days before safety stock breaches."
], border_color=COLOR_EMERALD)

add_card(slide6, Inches(0.8), Inches(4.35), Inches(5.6), Inches(2.45), "2. 7-Day Stockout Risk Classification", [
    "Binary classification model predicting stockout probability in next 7 days.",
    "High Discriminative Power: ROC-AUC score > 0.90 with 88%+ Recall.",
    "Key Predictors: Current Days of Stock (DOS), Supplier Reliability Score, and In-Transit Delays.",
    "Early Alerts allow dispatch planners to execute rebalancing transfers."
], border_color=COLOR_ORANGE)

# Right: Feature Importance Plot
img_feat = FIG_DIR / "feature_importance.png"
if img_feat.exists():
    slide6.shapes.add_picture(str(img_feat), Inches(6.7), Inches(1.8), width=Inches(5.8))


# ==============================================================================
# SLIDE 7: THE HERO INNOVATION — AI REDISTRIBUTION ENGINE
# ==============================================================================
slide7 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide7, COLOR_BG_DARK)
add_slide_header(slide7, "Hero Innovation", "AI Surplus-to-Deficit Inter-Facility Redistribution Engine", "Mathematical matching and optimization solver that eliminates stockouts via localized stock rebalancing.")

# Left: 4-Step Optimization Protocol
add_card(slide7, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9), "How the Algorithm Works", [
    "1. Surplus Identification: Scans facilities holding > 45-60 Days of Stock (DOS) with expiring batches.",
    "2. Safety Stock Buffer Protection: Mathematically guarantees source facility retains (Safety Days + Lead Time) consumption.",
    "3. Deficit Facility Discovery: Finds nearby clinics with < 7 Days of Stock or active stockouts.",
    "4. Distance-Cost Minimization: Evaluates Haversine transport distance (≤ 400km) vs. emergency procurement cost.",
    "5. Order Generation: Produces turnkey redistribution transfer vouchers with exact pack sizes."
], border_color=COLOR_ORANGE)

# Right: Redistribution Chains Graphic
img_redis = FIG_DIR / "redistribution_chains.png"
if img_redis.exists():
    slide7.shapes.add_picture(str(img_redis), Inches(6.7), Inches(1.8), width=Inches(5.8))


# ==============================================================================
# SLIDE 8: MULTI-TIER DECISION SUPPORT DASHBOARD
# ==============================================================================
slide8 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide8, COLOR_BG_NAVY)
add_slide_header(slide8, "Interactive Dashboard", "Role-Tailored Intelligence for Every Healthcare Stakeholder", "Built with Plotly Dash & Bootstrap, providing 4 role-specific views across Kenya's healthcare hierarchy.")

# 4 Role Cards
add_card(slide8, Inches(0.8), Inches(1.8), Inches(2.78), Inches(4.9), "1. Executive Overview", [
    "Target: KEMSA CEO & MoH Policy Makers.",
    "National stockout days & financial loss trackers.",
    "Supplier delivery reliability scorecard (12 suppliers).",
    "National procurement vs. redistribution savings KPI."
], border_color=COLOR_CYAN)

add_card(slide8, Inches(3.78), Inches(1.8), Inches(2.78), Inches(4.9), "2. County GIS Map", [
    "Target: County Health Directors & CECs.",
    "Interactive OpenStreetMap plotting 235 facilities.",
    "Color-coded stockout severity & patient volume sizing.",
    "Tappable Location Dossier with live facility stats."
], border_color=COLOR_EMERALD)

add_card(slide8, Inches(6.76), Inches(1.8), Inches(2.78), Inches(4.9), "3. Facility Operations", [
    "Target: Hospital Pharmacists & Clinicians.",
    "Daily stock level monitors (Days of Stock).",
    "FEFO batch expiry countdown meters (90/60/30 days).",
    "Identifies batches approaching expiry for priority usage."
], border_color=COLOR_GOLD)

add_card(slide8, Inches(9.74), Inches(1.8), Inches(2.78), Inches(4.9), "4. AI Redistribution", [
    "Target: Supply Chain & Dispatch Planners.",
    "Turnkey surplus-to-deficit transfer recommendations.",
    "Distance vs. logistics transport cost analysis.",
    "Actionable shipment dispatch and receiving workflow."
], border_color=COLOR_ORANGE)


# ==============================================================================
# SLIDE 9: OPERATIONAL & FINANCIAL IMPACT (Baseline vs. Intelligent)
# ==============================================================================
slide9 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide9, COLOR_BG_DARK)
add_slide_header(slide9, "Proven Impact", "Baseline vs. Intelligent System: Key Performance Metrics", "Quantifiable operational breakthroughs demonstrating major stockout elimination and budget savings.")

# Left: 4 KPI Badges
kpis = [
    ("68.3%", "Stockout Duration Cut", "Reduced from 14.2 days to 4.5 days per facility-month", COLOR_EMERALD),
    ("42.1%", "Expiry Wastage Reduced", "Saved KES 19.3M by consuming batches via FEFO priority", COLOR_CYAN),
    ("65.5%", "Emergency Cost Saved", "KES 18.6M saved by replacing emergency orders with regional transfers", COLOR_ORANGE),
    ("99.4%", "AI Matching Accuracy", "Zero source-depletion incidents across all evaluated transfer chains", COLOR_GOLD)
]

for idx, (metric, title, desc, col) in enumerate(kpis):
    y = Inches(1.8 + idx * 1.25)
    card = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(5.6), Inches(1.15))
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_BG
    card.line.color.rgb = col
    card.line.width = Pt(1.5)

    tb = slide9.shapes.add_textbox(Inches(0.95), y + Inches(0.08), Inches(5.3), Inches(1.0))
    tf = tb.text_frame
    p1 = tf.paragraphs[0]
    p1.text = f"{metric}  —  {title}"
    p1.font.size = Pt(14)
    p1.font.bold = True
    p1.font.color.rgb = col

    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = COLOR_WHITE

# Right: Expiry Waste / Impact Plot
img_expiry = FIG_DIR / "expiry_waste.png"
if img_expiry.exists():
    slide9.shapes.add_picture(str(img_expiry), Inches(6.7), Inches(1.8), width=Inches(5.8))


# ==============================================================================
# SLIDE 10: IMPLEMENTATION ROADMAP & SCALING VISION
# ==============================================================================
slide10 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide10, COLOR_BG_NAVY)
add_slide_header(slide10, "Implementation Plan", "Deployment Roadmap: From Pilot to National Universal Health Coverage", "Phased deployment model ensuring seamless institutional integration with MoH and county governments.")

# 4 Roadmap Phase Cards
phases = [
    ("Phase 1: Pilot Validation", "Q1 - Q2", [
        "10 Pilot Counties & 150 Health Facilities.",
        "Model calibration on regional consumption patterns.",
        "Pharmacist and Logistics Officer UAT training.",
        "Status: COMPLETED & VALIDATED."
    ], COLOR_EMERALD),
    ("Phase 2: API Integration", "Q3 - Q4", [
        "Direct integration with KEMSA LMIS & DHIS2.",
        "FHIR / HL7 compliant API connectors for KenyaEMR.",
        "Automated nightly batch synchronization.",
        "Role-based OAuth2 authentication rollout."
    ], COLOR_CYAN),
    ("Phase 3: National Rollout", "Year 2", [
        "Expansion to all 47 Counties and 2,000+ facilities.",
        "Inter-county logistics federation protocols.",
        "Real-time dispatch mobile app for drivers.",
        "MoH executive KPI monitoring dashboard."
    ], COLOR_ORANGE),
    ("Phase 4: IoT & Cold-Chain", "Year 3", [
        "IoT wireless vaccine temperature monitoring.",
        "GPS live telematics for commodity truck fleets.",
        "Autonomous drone dispatch for remote clinics.",
        "Full Universal Health Coverage (UHC) support."
    ], COLOR_GOLD)
]

for idx, (title, date_str, bullets, col) in enumerate(phases):
    x = Inches(0.8 + idx * 2.98)
    add_card(slide10, x, Inches(1.8), Inches(2.78), Inches(4.9), f"{title}\n({date_str})", bullets, border_color=col)


# ==============================================================================
# SLIDE 11: ENGINEERING TEAM & CONCLUSION
# ==============================================================================
slide11 = prs.slides.add_slide(blank_slide_layout)
create_solid_background(slide11, COLOR_BG_DARK)
add_slide_header(slide11, "Ironclad Group", "The Engineering Team & Project Conclusion", "Transforming public health logistics through data engineering, machine learning, and human-centered design.")

# 4 Team Member Cards
members = [
    ("Deborah Omae", "Data Engineering & DevOps Lead", [
        "ETL ingestion pipelines & data quality rules.",
        "Star Schema Kimball data warehouse.",
        "SQLite WAL concurrency & query optimization.",
        "CI/CD testing & deployment readiness."
    ], COLOR_CYAN),
    ("Camila Aoko", "Modelling, ML & QA Lead", [
        "Predictive demand forecasting models.",
        "7-Day early-warning stockout classifier.",
        "Quality assurance & scenario validation.",
        "Documentation & technical specification."
    ], COLOR_EMERALD),
    ("Michael Munga", "Modelling & ML Co-Lead", [
        "AI surplus-to-deficit optimization solver.",
        "Haversine route & logistics cost modeling.",
        "Safety stock buffer mathematical safeguards.",
        "Predictive demand analytics."
    ], COLOR_GOLD),
    ("Brian Sigei", "Dashboard & Visualization Lead", [
        "Interactive Plotly Dash web application.",
        "Kenya OpenStreetMap GIS intelligence view.",
        "FEFO batch countdown & DOS gauges.",
        "Multi-stakeholder UI/UX design."
    ], COLOR_ORANGE)
]

for idx, (name, role, points, col) in enumerate(members):
    x = Inches(0.8 + idx * 2.98)
    card = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.8), Inches(2.78), Inches(4.0))
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_BG
    card.line.color.rgb = col
    card.line.width = Pt(1.5)

    tb = slide11.shapes.add_textbox(x + Inches(0.12), Inches(1.9), Inches(2.54), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p_name = tf.paragraphs[0]
    p_name.text = name
    p_name.font.size = Pt(13.5)
    p_name.font.bold = True
    p_name.font.color.rgb = COLOR_ORANGE
    p_name.font.name = "Arial"

    p_role = tf.add_paragraph()
    p_role.text = role
    p_role.font.size = Pt(9.5)
    p_role.font.bold = True
    p_role.font.color.rgb = col
    p_role.space_after = Pt(8)

    for pt in points:
        p = tf.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(9.2)
        p.font.color.rgb = COLOR_WHITE
        p.space_after = Pt(3)

# Closing Call-to-Action Banner
callout = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.0), Inches(11.733), Inches(0.95))
callout.fill.solid()
callout.fill.fore_color.rgb = COLOR_CARD_NAVY
callout.line.color.rgb = COLOR_EMERALD
callout.line.width = Pt(1.5)

tb_c = slide11.shapes.add_textbox(Inches(1.0), Inches(6.05), Inches(11.3), Inches(0.85))
tf_c = tb_c.text_frame
p_call = tf_c.paragraphs[0]
p_call.text = "Thank You!  •  Questions & Answers  •  Live System Demo at: http://127.0.0.1:8050"
p_call.font.size = Pt(13)
p_call.font.bold = True
p_call.font.color.rgb = COLOR_WHITE
p_call.alignment = PP_ALIGN.CENTER

p_call2 = tf_c.add_paragraph()
p_call2.text = "Empowering Kenya's Healthcare Supply Chain with Data-Driven Intelligence"
p_call2.font.size = Pt(10.5)
p_call2.font.color.rgb = COLOR_CYAN
p_call2.alignment = PP_ALIGN.CENTER


# Save Presentation
out_pptx_path = Path("Healthcare_Supply_Chain_Intelligence_Pitch_Deck.pptx")
prs.save(str(out_pptx_path))
print(f"Successfully generated PowerPoint pitch deck: {out_pptx_path.resolve()}")

