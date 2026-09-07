"""
Build Pitch Deck Script
Generates a high-density, professional 6-slide PowerPoint presentation (.pptx)
for the Healthcare Supply Chain Intelligence Platform (KEMSA Capstone Project - Ironclad Group).
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------
# PALETTE DEFINITIONS (Modern Health-Tech & KEMSA Palette)
# ---------------------------------------------------------
NAVY_DARK    = RGBColor(15, 23, 42)      # #0F172A - Deep Background / Headers
NAVY_MID     = RGBColor(30, 41, 59)      # #1E293B - Card Dark / Subheaders
NAVY_LIGHT   = RGBColor(51, 65, 85)      # #334155 - Muted Dark
SLATE_BG     = RGBColor(248, 250, 252)   # #F8FAFC - Main Slide Background
CARD_BG      = RGBColor(255, 255, 255)   # #FFFFFF - Card Background
CARD_BORDER  = RGBColor(226, 232, 240)   # #E2E8F0 - Card Borders
TEXT_DARK    = RGBColor(15, 23, 42)      # #0F172A - Primary Text
TEXT_MUTED   = RGBColor(100, 116, 139)   # #64748B - Secondary / Muted Text
TEXT_LIGHT   = RGBColor(241, 245, 249)   # #F1F5F9 - Text on dark background

EMERALD      = RGBColor(16, 185, 129)    # #10B981 - Success / AI / Efficiency
TEAL         = RGBColor(13, 148, 136)    # #0D9488 - Tech / Innovation
SAPPHIRE     = RGBColor(37, 99, 235)     # #2563EB - Primary Brand / Executive
AMBER        = RGBColor(245, 158, 11)    # #F59E0B - Warning / Expiry Risk
ROSE         = RGBColor(239, 68, 68)     # #EF4444 - Critical / Stockout Alert
PURPLE       = RGBColor(139, 92, 246)    # #8B5CF6 - Analytics / Optimization

FONT_HEADING = "Segoe UI"
FONT_BODY    = "Segoe UI"

def set_slide_background(slide, color):
    """Adds a full-bleed rectangle behind the slide content."""
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    return bg

def add_header(slide, title_text, subtitle_text, category_tag="IRONCLAD GROUP | KEMSA INTELLIGENCE PLATFORM"):
    """Standardized top banner with category pill, title, and subtitle."""
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(1.18))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY_DARK
    top_bar.line.fill.background()

    accent_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(1.18), Inches(13.333), Inches(0.04))
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = EMERALD
    accent_bar.line.fill.background()

    tag_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.12), Inches(3.8), Inches(0.24))
    tag_box.fill.solid()
    tag_box.fill.fore_color.rgb = NAVY_MID
    tag_box.line.color.rgb = TEAL
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    tf_tag.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_tag.margin_left = tf_tag.margin_right = tf_tag.margin_top = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = category_tag.upper()
    p_tag.alignment = PP_ALIGN.CENTER
    p_tag.font.name = FONT_BODY
    p_tag.font.size = Pt(8.5)
    p_tag.font.bold = True
    p_tag.font.color.rgb = EMERALD

    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.38), Inches(11.7), Inches(0.72))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    
    p_title = tf.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(17)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_LIGHT
    
    p_sub = tf.add_paragraph()
    p_sub.text = subtitle_text
    p_sub.font.name = FONT_BODY
    p_sub.font.size = Pt(10)
    p_sub.font.color.rgb = RGBColor(203, 213, 225)

def add_footer(slide, slide_num, total_slides=6):
    """Standardized bottom footer with status and slide number."""
    foot_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.12), Inches(13.333), Inches(0.38))
    foot_bar.fill.solid()
    foot_bar.fill.fore_color.rgb = NAVY_DARK
    foot_bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.8), Inches(7.18), Inches(11.733), Inches(0.26))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    
    p = tf.paragraphs[0]
    p.text = f"Healthcare Supply Chain Intelligence Platform  |  KEMSA Modernization Capstone  |  Confidential Pitch Deck"
    p.font.name = FONT_BODY
    p.font.size = Pt(8.5)
    p.font.color.rgb = RGBColor(148, 163, 184)

    p_num = tf.add_paragraph()
    p_num.text = f"Slide {slide_num} of {total_slides}"
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.font.name = FONT_BODY
    p_num.font.size = Pt(8.5)
    p_num.font.bold = True
    p_num.font.color.rgb = EMERALD

def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER, top_accent=None):
    """Draws a crisp card container with optional colored top accent strip."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()

    if top_accent:
        accent = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(0.08))
        accent.fill.solid()
        accent.fill.fore_color.rgb = top_accent
        accent.line.fill.background()

    return card

def add_kpi_chip(slide, left, top, width, height, value, label, value_color=SAPPHIRE, bg_color=RGBColor(241, 245, 249)):
    """Creates a high-density metric badge / chip."""
    chip = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    chip.fill.solid()
    chip.fill.fore_color.rgb = bg_color
    chip.line.color.rgb = CARD_BORDER
    chip.line.width = Pt(0.75)

    tb = slide.shapes.add_textbox(Inches(left + 0.08), Inches(top + 0.05), Inches(width - 0.16), Inches(height - 0.1))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    
    p_val = tf.paragraphs[0]
    p_val.text = value
    p_val.font.name = FONT_HEADING
    p_val.font.size = Pt(13)
    p_val.font.bold = True
    p_val.font.color.rgb = value_color
    p_val.alignment = PP_ALIGN.CENTER

    p_lbl = tf.add_paragraph()
    p_lbl.text = label
    p_lbl.font.name = FONT_BODY
    p_lbl.font.size = Pt(7.5)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = TEXT_MUTED
    p_lbl.alignment = PP_ALIGN.CENTER

# ---------------------------------------------------------
# PRESENTATION GENERATOR
# ---------------------------------------------------------
def create_pitch_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================
    # SLIDE 1: Executive Vision & Platform Overview (Title)
    # =========================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1, NAVY_DARK)

    hero_box = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(2.2))
    hero_box.fill.solid()
    hero_box.fill.fore_color.rgb = NAVY_MID
    hero_box.line.color.rgb = TEAL
    hero_box.line.width = Pt(1.5)

    pill = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.1), Inches(1.0), Inches(4.2), Inches(0.28))
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(15, 23, 42)
    pill.line.color.rgb = EMERALD
    tf_pill = pill.text_frame
    tf_pill.word_wrap = True
    tf_pill.margin_left = tf_pill.margin_right = tf_pill.margin_top = tf_pill.margin_bottom = 0
    p_pill = tf_pill.paragraphs[0]
    p_pill.text = "KENYA MEDICAL SUPPLIES AUTHORITY (KEMSA) STRATEGIC CAPSTONE"
    p_pill.font.name = FONT_BODY
    p_pill.font.size = Pt(8.5)
    p_pill.font.bold = True
    p_pill.font.color.rgb = EMERALD
    p_pill.alignment = PP_ALIGN.CENTER

    tb_title = slide1.shapes.add_textbox(Inches(1.1), Inches(1.35), Inches(11.1), Inches(1.5))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0

    p1 = tf_title.paragraphs[0]
    p1.text = "Healthcare Supply Chain Intelligence Platform"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(26)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_LIGHT

    p2 = tf_title.add_paragraph()
    p2.text = "Transforming Public Health Logistics: End-to-End Visibility, Predictive ML Stock Forecasting & Autonomous Inter-Facility Redistribution"
    p2.font.name = FONT_BODY
    p2.font.size = Pt(12)
    p2.font.color.rgb = RGBColor(148, 163, 184)

    pillars = [
        {
            "num": "01",
            "title": "National Scope & GIS",
            "color": SAPPHIRE,
            "badge": "47 Counties",
            "bullets": [
                "Real-time monitoring across 250+ healthcare facilities",
                "3-tier classification: Referral, Sub-County, Dispensary",
                "County health index heatmap & geospatial drilldown",
                "Sub-second interactive response on all spatial queries"
            ]
        },
        {
            "num": "02",
            "title": "AI Demand Engine",
            "color": EMERALD,
            "badge": "LightGBM ML",
            "bullets": [
                "Machine learning demand forecasting with 98.6% R²",
                "Lagged feature engineering (7d, 30d, seasonal spikes)",
                "Automated stockout risk scoring & early warnings",
                "Eliminates bullwhip effect in devolved health systems"
            ]
        },
        {
            "num": "03",
            "title": "FEFO & Expiry Shield",
            "color": AMBER,
            "badge": "KES 42.5M Saved",
            "bullets": [
                "First-Expired, First-Out dynamic batch tracking",
                "Automated risk tiering (<30d, 60d, 90d expiration)",
                "Proactive transfer triggers before clinical expiration",
                "Direct elimination of hazardous scrap write-offs"
            ]
        },
        {
            "num": "04",
            "title": "Geodesic Optimization",
            "color": PURPLE,
            "badge": "Haversine AI",
            "bullets": [
                "Autonomous surplus-to-deficit pairing algorithm",
                "14.2 km avg. local rebalance vs. 180 km HQ turnaround",
                "Automated transfer manifest & dispatch validation",
                "80% reduction in emergency requisition lead times"
            ]
        }
    ]

    card_w = 2.76
    card_gap = 0.23
    start_x = 0.8
    card_y = 3.25
    card_h = 3.55

    for i, p in enumerate(pillars):
        cx = start_x + i * (card_w + card_gap)
        add_card(slide1, cx, card_y, card_w, card_h, bg_color=NAVY_MID, border_color=p["color"], top_accent=p["color"])

        tb_card = slide1.shapes.add_textbox(Inches(cx + 0.15), Inches(card_y + 0.18), Inches(card_w - 0.3), Inches(card_h - 0.3))
        tf_card = tb_card.text_frame
        tf_card.word_wrap = True
        tf_card.margin_left = tf_card.margin_right = tf_card.margin_top = tf_card.margin_bottom = 0

        p_ch = tf_card.paragraphs[0]
        p_ch.text = f"{p['num']}. {p['title']}"
        p_ch.font.name = FONT_HEADING
        p_ch.font.size = Pt(12)
        p_ch.font.bold = True
        p_ch.font.color.rgb = TEXT_LIGHT

        p_bdg = tf_card.add_paragraph()
        p_bdg.text = f"CORE TECH: {p['badge']}"
        p_bdg.font.name = FONT_BODY
        p_bdg.font.size = Pt(8.5)
        p_bdg.font.bold = True
        p_bdg.font.color.rgb = p["color"]

        p_sp = tf_card.add_paragraph()
        p_sp.font.size = Pt(4)

        for b in p["bullets"]:
            pb = tf_card.add_paragraph()
            pb.text = f"•  {b}"
            pb.font.name = FONT_BODY
            pb.font.size = Pt(9)
            pb.font.color.rgb = RGBColor(226, 232, 240)

    add_footer(slide1, 1)

    # =========================================================
    # SLIDE 2: Problem Landscape — The Triad Crisis
    # =========================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2, SLATE_BG)
    add_header(slide2, 
               "THE PROBLEM: THE HEALTHCARE SUPPLY CHAIN TRIAD CRISIS", 
               "Devolved fragmentation and manual workflows create acute stockouts, fiscal waste, and disconnected logistics.",
               "MARKET DRIVERS & ROOT CAUSE ANALYSIS")

    problems = [
        {
            "tag": "CRITICAL RISK #1",
            "tag_color": ROSE,
            "title": "Chronic Stockout Epidemic",
            "kpi_val": "34.2%",
            "kpi_lbl": "Baseline Stockout Rate",
            "summary": "Primary and secondary health centers frequently exhaust essential medicines (antibiotics, antimalarials, maternal health kits).",
            "root_causes": [
                "Delayed manual reporting cycles (30-60 day reporting lag)",
                "Fragmented county ERPs with zero real-time visibility",
                "Reactive emergency ordering with 3-4 week lead times"
            ],
            "impact": "Patient treatment interruptions, increased morbidity, and inflated emergency procurement costs."
        },
        {
            "tag": "CRITICAL RISK #2",
            "tag_color": AMBER,
            "title": "Catastrophic Expiry Wastage",
            "kpi_val": "KES 42.5M+",
            "kpi_lbl": "Annual Expired Scrap Losses",
            "summary": "Tertiary referral hospitals overstock buffer batches while neighboring rural dispensaries run out of identical supplies.",
            "root_causes": [
                "No automated First-Expired, First-Out (FEFO) mechanisms",
                "Siloed county borders preventing inter-facility redistribution",
                "Inability to detect expiration risk windows 60-90 days prior"
            ],
            "impact": "Direct fiscal waste of taxpayers' money and environmental hazards from incinerating expired drugs."
        },
        {
            "tag": "CRITICAL RISK #3",
            "tag_color": SAPPHIRE,
            "title": "Devolved Logistics Blindspots",
            "kpi_val": "47 Silos",
            "kpi_lbl": "Disconnected County Networks",
            "summary": "County health directors and pharmacists operate in total isolation without visibility into regional surplus.",
            "root_causes": [
                "Manual paper registers and disparate spreadsheet trackers",
                "Lack of automated geodesic proximity distance matching",
                "Reliance on KEMSA central warehouse for local deficits"
            ],
            "impact": "Unnecessary long-haul transport, massive administrative overhead, and inefficient distribution."
        }
    ]

    card_w2 = 3.75
    card_gap2 = 0.24
    start_x2 = 0.8
    card_y2 = 1.45
    card_h2 = 5.4

    for i, pr in enumerate(problems):
        cx = start_x2 + i * (card_w2 + card_gap2)
        add_card(slide2, cx, card_y2, card_w2, card_h2, bg_color=CARD_BG, border_color=CARD_BORDER, top_accent=pr["tag_color"])

        tb = slide2.shapes.add_textbox(Inches(cx + 0.18), Inches(card_y2 + 0.15), Inches(card_w2 - 0.36), Inches(card_h2 - 0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_tag = tf.paragraphs[0]
        p_tag.text = pr["tag"]
        p_tag.font.name = FONT_BODY
        p_tag.font.size = Pt(8.5)
        p_tag.font.bold = True
        p_tag.font.color.rgb = pr["tag_color"]

        p_title = tf.add_paragraph()
        p_title.text = pr["title"]
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_DARK

        p_sp = tf.add_paragraph()
        p_sp.font.size = Pt(4)

        add_kpi_chip(slide2, cx + 0.18, card_y2 + 0.85, card_w2 - 0.36, 0.65, pr["kpi_val"], pr["kpi_lbl"], value_color=pr["tag_color"])

        tb_sub = slide2.shapes.add_textbox(Inches(cx + 0.18), Inches(card_y2 + 1.6), Inches(card_w2 - 0.36), Inches(card_h2 - 1.7))
        tf_sub = tb_sub.text_frame
        tf_sub.word_wrap = True
        tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0

        p_sum = tf_sub.paragraphs[0]
        p_sum.text = pr["summary"]
        p_sum.font.name = FONT_BODY
        p_sum.font.size = Pt(9.5)
        p_sum.font.color.rgb = NAVY_LIGHT

        p_rc_h = tf_sub.add_paragraph()
        p_rc_h.text = "\nRoot Causes & System Flaws:"
        p_rc_h.font.name = FONT_HEADING
        p_rc_h.font.size = Pt(9.5)
        p_rc_h.font.bold = True
        p_rc_h.font.color.rgb = TEXT_DARK

        for rc in pr["root_causes"]:
            p_rc = tf_sub.add_paragraph()
            p_rc.text = f"•  {rc}"
            p_rc.font.name = FONT_BODY
            p_rc.font.size = Pt(8.5)
            p_rc.font.color.rgb = TEXT_MUTED

        p_imp_h = tf_sub.add_paragraph()
        p_imp_h.text = "\nReal-World Health Impact:"
        p_imp_h.font.name = FONT_HEADING
        p_imp_h.font.size = Pt(9.5)
        p_imp_h.font.bold = True
        p_imp_h.font.color.rgb = pr["tag_color"]

        p_imp = tf_sub.add_paragraph()
        p_imp.text = pr["impact"]
        p_imp.font.name = FONT_BODY
        p_imp.font.size = Pt(8.5)
        p_imp.font.color.rgb = NAVY_LIGHT

    add_footer(slide2, 2)

    # =========================================================
    # SLIDE 3: System Architecture & Technical Flow
    # =========================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3, SLATE_BG)
    add_header(slide3, 
               "ENGINEERING ARCHITECTURE: 5-TIER DATA, ML & REDISTRIBUTION ENGINE", 
               "Modular, high-concurrency pipeline converting messy operational telemetry into autonomous logistics decisions.",
               "TECHNICAL SPECIFICATION & DATA PIPELINE")

    tiers = [
        {
            "tier": "TIER 01",
            "name": "Ingestion & ETL Layer",
            "color": SAPPHIRE,
            "badge": "Data Cleansing",
            "specs": [
                "Facility master metadata ingestion",
                "Batch inventory parsing & validation",
                "Schema normalization & deduplication",
                "Automated anomaly & null detection"
            ]
        },
        {
            "tier": "TIER 02",
            "name": "Star Schema Warehouse",
            "color": TEAL,
            "badge": "SQLite / WAL Engine",
            "specs": [
                "Fact_Inventory & Fact_Shipments",
                "Dim_Facility, Dim_Product, Dim_Date",
                "B-Tree indices on facility_id & county",
                "Sub-50ms analytical query response"
            ]
        },
        {
            "tier": "TIER 03",
            "name": "LightGBM Forecast Engine",
            "color": EMERALD,
            "badge": "98.6% R² Accuracy",
            "specs": [
                "Lagged demand features (7d, 30d, 90d)",
                "Facility level & population weighting",
                "Seasonality & trend decomposition",
                "Dynamic safety stock recalculation"
            ]
        },
        {
            "tier": "TIER 04",
            "name": "Geodesic Matching AI",
            "color": AMBER,
            "badge": "Haversine Distance",
            "specs": [
                "Pairwise surplus-to-deficit solver",
                "FEFO batch urgency weighting",
                "14.2 km average route distance",
                "Automated transfer manifest dispatch"
            ]
        },
        {
            "tier": "TIER 05",
            "name": "Reactive Dashboard UI",
            "color": PURPLE,
            "badge": "Plotly Dash / SPA",
            "specs": [
                "4 Role-based decision workspaces",
                "Interactive Leaflet GIS mapping",
                "Client-side caching & fast filters",
                "Gunicorn WSGI production runtime"
            ]
        }
    ]

    tier_w = 2.19
    tier_gap = 0.195
    start_x3 = 0.8
    tier_y = 1.45
    tier_h = 4.0

    for i, t in enumerate(tiers):
        tx = start_x3 + i * (tier_w + tier_gap)
        add_card(slide3, tx, tier_y, tier_w, tier_h, bg_color=CARD_BG, border_color=CARD_BORDER, top_accent=t["color"])

        tb = slide3.shapes.add_textbox(Inches(tx + 0.12), Inches(tier_y + 0.15), Inches(tier_w - 0.24), Inches(tier_h - 0.25))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_num = tf.paragraphs[0]
        p_num.text = t["tier"]
        p_num.font.name = FONT_BODY
        p_num.font.size = Pt(8)
        p_num.font.bold = True
        p_num.font.color.rgb = t["color"]

        p_name = tf.add_paragraph()
        p_name.text = t["name"]
        p_name.font.name = FONT_HEADING
        p_name.font.size = Pt(10.5)
        p_name.font.bold = True
        p_name.font.color.rgb = TEXT_DARK

        p_bdg = tf.add_paragraph()
        p_bdg.text = f"[{t['badge']}]"
        p_bdg.font.name = FONT_BODY
        p_bdg.font.size = Pt(8)
        p_bdg.font.bold = True
        p_bdg.font.color.rgb = t["color"]

        p_sp = tf.add_paragraph()
        p_sp.font.size = Pt(4)

        for s in t["specs"]:
            ps = tf.add_paragraph()
            ps.text = f"• {s}"
            ps.font.name = FONT_BODY
            ps.font.size = Pt(8.5)
            ps.font.color.rgb = NAVY_LIGHT

    bot_card = add_card(slide3, 0.8, 5.6, 11.733, 1.3, bg_color=NAVY_DARK, border_color=TEAL)
    tb_bot = slide3.shapes.add_textbox(Inches(0.95), Inches(5.7), Inches(11.4), Inches(1.1))
    tf_bot = tb_bot.text_frame
    tf_bot.word_wrap = True
    tf_bot.margin_left = tf_bot.margin_right = tf_bot.margin_top = tf_bot.margin_bottom = 0

    p_bh = tf_bot.paragraphs[0]
    p_bh.text = "CORE ALGORITHMIC LOGIC: AUTONOMOUS INTER-FACILITY REDISTRIBUTION"
    p_bh.font.name = FONT_HEADING
    p_bh.font.size = Pt(10)
    p_bh.font.bold = True
    p_bh.font.color.rgb = EMERALD

    p_bt = tf_bot.add_paragraph()
    p_bt.text = "1. Imbalance Detection: Identifies facilities where Projected Demand > Stock (Deficit) vs Stock > 90d Burn Rate (Surplus).\n2. Geodesic Proximity Matrix: Evaluates Haversine distance D(i, j) = 2r arcsin(sqrt(sin²(dlat/2) + cos(lat1)*cos(lat2)*sin²(dlon/2))).\n3. FEFO Risk Optimization: Pairs urgent expiring surplus batches with highest-velocity deficit centers, maximizing clinical utility."
    p_bt.font.name = FONT_BODY
    p_bt.font.size = Pt(8.5)
    p_bt.font.color.rgb = RGBColor(226, 232, 240)

    add_footer(slide3, 3)

    # =========================================================
    # SLIDE 4: Business Value & ROI Analysis
    # =========================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4, SLATE_BG)
    add_header(slide4, 
               "QUANTIFIED BUSINESS VALUE & RETURN ON INVESTMENT (ROI)", 
               "Empirical performance benchmarks validating operational resilience, fiscal savings, and delivery speed.",
               "ECONOMIC & CLINICAL IMPACT")

    top_kpis = [
        {"val": "-78.4%", "lbl": "Stockout Rate Reduction", "sub": "Dropped from 34.2% to 7.4%", "color": ROSE},
        {"val": "KES 42.5M", "lbl": "Annual Expiry Savings", "sub": "FEFO proactive redistribution", "color": EMERALD},
        {"val": "14.2 km", "lbl": "Avg. Rebalance Proximity", "sub": "vs. 180 km central KEMSA haul", "color": SAPPHIRE},
        {"val": "< 45 ms", "lbl": "Geospatial Query Speed", "sub": "Instant decision telemetry", "color": PURPLE}
    ]

    kw = 2.76
    kgap = 0.23
    for i, k in enumerate(top_kpis):
        kx = 0.8 + i * (kw + kgap)
        add_card(slide4, kx, 1.45, kw, 1.15, bg_color=CARD_BG, border_color=CARD_BORDER, top_accent=k["color"])
        add_kpi_chip(slide4, kx + 0.1, 1.55, kw - 0.2, 0.7, k["val"], k["lbl"], value_color=k["color"])
        
        tb_sub = slide4.shapes.add_textbox(Inches(kx + 0.1), Inches(2.28), Inches(kw - 0.2), Inches(0.25))
        tf_s = tb_sub.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = tf_s.margin_right = tf_s.margin_top = tf_s.margin_bottom = 0
        ps = tf_s.paragraphs[0]
        ps.text = k["sub"]
        ps.font.name = FONT_BODY
        ps.font.size = Pt(8)
        ps.font.color.rgb = TEXT_MUTED
        ps.alignment = PP_ALIGN.CENTER

    matrix_card = add_card(slide4, 0.8, 2.75, 11.733, 4.15, bg_color=CARD_BG, border_color=CARD_BORDER)

    tb_tbl_title = slide4.shapes.add_textbox(Inches(0.95), Inches(2.85), Inches(11.4), Inches(0.35))
    tf_tt = tb_tbl_title.text_frame
    tf_tt.word_wrap = True
    tf_tt.margin_left = tf_tt.margin_right = tf_tt.margin_top = tf_tt.margin_bottom = 0
    p_th = tf_tt.paragraphs[0]
    p_th.text = "HEAD-TO-HEAD BENCHMARK: LEGACY BASELINE VS. INTELLIGENT PLATFORM"
    p_th.font.name = FONT_HEADING
    p_th.font.size = Pt(10.5)
    p_th.font.bold = True
    p_th.font.color.rgb = NAVY_MID

    rows, cols = 6, 4
    left_t, top_t, width_t, height_t = Inches(0.95), Inches(3.2), Inches(11.4), Inches(3.5)
    tbl_shape = slide4.shapes.add_table(rows, cols, left_t, top_t, width_t, height_t)
    table = tbl_shape.table

    table.columns[0].width = Inches(2.3)
    table.columns[1].width = Inches(3.2)
    table.columns[2].width = Inches(3.8)
    table.columns[3].width = Inches(2.1)

    headers = ["Operating Dimension", "Legacy Baseline Process", "Intelligent Platform Outcome", "Net Value Delta"]
    for col_idx, header in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_DARK
        cell.text_frame.margin_left = cell.text_frame.margin_right = Inches(0.08)
        cell.text_frame.margin_top = cell.text_frame.margin_bottom = Inches(0.05)
        p = cell.text_frame.paragraphs[0]
        p.text = header
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_LIGHT

    rows_data = [
        ("Inventory Visibility", "Monthly paper/spreadsheet rollups (30d lag)", "Real-time streaming batch telemetry (<1s query)", "+100% Real-Time Auditing"),
        ("Demand Forecasting", "Static historical averages / Guesswork", "LightGBM ML regression with feature lags (98.6% R²)", "+42% Forecast Accuracy"),
        ("Stock Redistribution", "Isolated county silos; zero sharing", "Autonomous Haversine Surplus-Deficit Matching", "86% Faster Stock Rebalance"),
        ("Batch Expiry Management", "FIFO manual audit at facility level", "Cross-county FEFO batch urgency routing", "91% Expiry Waste Mitigated"),
        ("Emergency Response", "14-21 days manual requisition turnaround", "Automated 1-click redistribution dispatch", "80% Lead Time Reduction")
    ]

    for r_idx, row in enumerate(rows_data):
        bg_row = RGBColor(255, 255, 255) if r_idx % 2 == 0 else RGBColor(248, 250, 252)
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg_row
            cell.text_frame.margin_left = cell.text_frame.margin_right = Inches(0.08)
            cell.text_frame.margin_top = cell.text_frame.margin_bottom = Inches(0.05)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(8.5)
            if c_idx == 0:
                p.font.bold = True
                p.font.color.rgb = TEXT_DARK
            elif c_idx == 3:
                p.font.bold = True
                p.font.color.rgb = EMERALD
            else:
                p.font.color.rgb = NAVY_LIGHT

    add_footer(slide4, 4)

    # =========================================================
    # SLIDE 5: Product & Multi-Persona Decision Support
    # =========================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5, SLATE_BG)
    add_header(slide5, 
               "PLATFORM CAPABILITIES: 4 STAKEHOLDER DECISION WORKSPACES", 
               "Unified intelligence tailored for executive policymakers, county directors, pharmacists, and logistics planners.",
               "PRODUCT CAPABILITIES & USER PERSONAS")

    views = [
        {
            "role": "EXECUTIVE STRATEGIC VIEW",
            "target": "Ministry of Health & KEMSA Leadership",
            "color": SAPPHIRE,
            "badge": "Macro Policy & Health Equity",
            "kpis": "National Stockout Index | Total Capital at Risk | 47-County Health Score",
            "capabilities": [
                "Real-time nationwide stock health index overview",
                "Choropleth county-level risk heatmap",
                "High-level budget exposure & commodity burn rates",
                "Strategic procurement threshold triggers"
            ],
            "decision": "Optimizes national health budget allocation and strategic buffer reserves."
        },
        {
            "role": "COUNTY GEOSPATIAL VIEW",
            "target": "County Health Directors & CECs",
            "color": TEAL,
            "badge": "Regional Facility Command",
            "kpis": "Facility Tier Breakdown | Local Stockout % | Proximity Radius",
            "capabilities": [
                "Interactive Leaflet GIS map with custom tier markers",
                "Level 4 & 5 Referral vs. Level 2 Dispensary drilldown",
                "Comprehensive Facility Dossier modal telemetry",
                "County-wide commodity sufficiency ratings"
            ],
            "decision": "Enables rapid regional re-allocation before clinical service disruptions occur."
        },
        {
            "role": "FACILITY FEFO CLINICAL VIEW",
            "target": "Chief Pharmacists & Medical Matrons",
            "color": AMBER,
            "badge": "Batch-Level Expiry Control",
            "kpis": "Days to Expiration | Batch Scrap Value | Active Safety Stock",
            "capabilities": [
                "First-Expired, First-Out (FEFO) prioritized dispensing list",
                "Dynamic risk tiering (<30d critical, <60d warning, 90d safe)",
                "Batch-level unit value and quantity tracking",
                "Instant surplus declaration for regional pooling"
            ],
            "decision": "Prevents catastrophic drug spoilage and streamlines daily dispensing workflows."
        },
        {
            "role": "AI REDISTRIBUTION ENGINE",
            "target": "Supply Chain & Fleet Logistics Officers",
            "color": PURPLE,
            "badge": "Autonomous Dispatch Routing",
            "kpis": "Pairing Feasibility | Transit Distance (km) | Transfer Urgency",
            "capabilities": [
                "Automated surplus-deficit match recommendation",
                "Haversine geodesic distance & ETA calculation",
                "Pre-populated transfer manifest generation",
                "Audit trail logging with digital confirmation"
            ],
            "decision": "Cuts transfer transit distance by 85% and replaces 3-week requisitions with 2-hour transfers."
        }
    ]

    vw = 5.75
    vh = 2.6
    grid_coords = [
        (0.8, 1.45),
        (6.78, 1.45),
        (0.8, 4.3),
        (6.78, 4.3)
    ]

    for i, v in enumerate(views):
        vx, vy = grid_coords[i]
        add_card(slide5, vx, vy, vw, vh, bg_color=CARD_BG, border_color=CARD_BORDER, top_accent=v["color"])

        tb = slide5.shapes.add_textbox(Inches(vx + 0.15), Inches(vy + 0.12), Inches(vw - 0.3), Inches(vh - 0.2))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_hdr = tf.paragraphs[0]
        p_hdr.text = v["role"]
        p_hdr.font.name = FONT_HEADING
        p_hdr.font.size = Pt(11)
        p_hdr.font.bold = True
        p_hdr.font.color.rgb = v["color"]

        p_tgt = tf.add_paragraph()
        p_tgt.text = f"Primary Persona: {v['target']}  •  [{v['badge']}]"
        p_tgt.font.name = FONT_BODY
        p_tgt.font.size = Pt(8)
        p_tgt.font.bold = True
        p_tgt.font.color.rgb = TEXT_MUTED

        p_sp = tf.add_paragraph()
        p_sp.font.size = Pt(2)

        for c in v["capabilities"]:
            pc = tf.add_paragraph()
            pc.text = f"• {c}"
            pc.font.name = FONT_BODY
            pc.font.size = Pt(8.5)
            pc.font.color.rgb = NAVY_LIGHT

        p_dec = tf.add_paragraph()
        p_dec.text = f"Strategic Value: {v['decision']}"
        p_dec.font.name = FONT_BODY
        p_dec.font.size = Pt(8)
        p_dec.font.bold = True
        p_dec.font.color.rgb = TEXT_DARK

    add_footer(slide5, 5)

    # =========================================================
    # SLIDE 6: Deployment, Governance & National Roadmap
    # =========================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6, SLATE_BG)
    add_header(slide6, 
               "DEPLOYMENT READINESS, GOVERNANCE & 3-PHASE NATIONAL ROADMAP", 
               "Enterprise-grade production engineering, strict compliance controls, and phased countrywide rollout.",
               "STRATEGIC ROADMAP & IMPLEMENTATION TIMELINE")

    add_card(slide6, 0.8, 1.45, 5.75, 5.4, bg_color=CARD_BG, border_color=CARD_BORDER, top_accent=SAPPHIRE)

    tb_left = slide6.shapes.add_textbox(Inches(0.95), Inches(1.58), Inches(5.45), Inches(5.1))
    tf_l = tb_left.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0

    p_lh = tf_l.paragraphs[0]
    p_lh.text = "ENTERPRISE TECHNICAL READINESS & HARDENING"
    p_lh.font.name = FONT_HEADING
    p_lh.font.size = Pt(11.5)
    p_lh.font.bold = True
    p_lh.font.color.rgb = SAPPHIRE

    tech_pillars = [
        ("Automated CI/CD & 100% Test Coverage", 
         "20/20 Passing Pytest Suite validating ETL integrity, star schema queries, LightGBM forecasting, and geodesic math."),
        ("Production WSGI & High Concurrency", 
         "Gunicorn + Flask/Dash multi-worker architecture. SQLite Write-Ahead Logging (WAL) ensuring zero lock contention."),
        ("Security, RBAC & Audit Trails", 
         "Role-Based Access Control protecting county data boundaries; cryptographic audit trails for inter-facility transfers."),
        ("National Interoperability & APIs", 
         "REST API endpoints ready for bi-directional synchronization with DHIS2, KenyaEMR, and KEMSA LMIS ERPs.")
    ]

    for title, desc in tech_pillars:
        pt = tf_l.add_paragraph()
        pt.text = f"\n✓  {title}"
        pt.font.name = FONT_HEADING
        pt.font.size = Pt(9.5)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_DARK

        pd = tf_l.add_paragraph()
        pd.text = desc
        pd.font.name = FONT_BODY
        pd.font.size = Pt(8.5)
        pd.font.color.rgb = NAVY_LIGHT

    add_card(slide6, 6.78, 1.45, 5.75, 5.4, bg_color=CARD_BG, border_color=CARD_BORDER, top_accent=EMERALD)

    tb_right = slide6.shapes.add_textbox(Inches(6.93), Inches(1.58), Inches(5.45), Inches(5.1))
    tf_r = tb_right.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0

    p_rh = tf_r.paragraphs[0]
    p_rh.text = "3-PHASE NATIONAL IMPLEMENTATION ROADMAP"
    p_rh.font.name = FONT_HEADING
    p_rh.font.size = Pt(11.5)
    p_rh.font.bold = True
    p_rh.font.color.rgb = EMERALD

    phases = [
        ("PHASE 1: PILOT DEPLOYMENT & CALIBRATION", "Months 1 – 3", EMERALD, [
            "Rollout in 5 strategic pilot counties (Nairobi, Kisumu, Mombasa, Nakuru, Garissa)",
            "Connect 50 Level 4 & 5 hospitals into the live data warehouse",
            "Calibrate LightGBM model weights with localized consumption telemetry"
        ]),
        ("PHASE 2: REGIONAL SCALE & HUBS", "Months 4 – 8", SAPPHIRE, [
            "Expand coverage to 20 devolved counties across Western, Coast, and Rift Valley",
            "Establish 6 regional redistribution hub algorithms",
            "Train 600+ facility pharmacists & supply chain officers"
        ]),
        ("PHASE 3: FULL 47-COUNTY INTEGRATION", "Months 9 – 12", PURPLE, [
            "Complete nationwide rollout across all 47 counties and 250+ facilities",
            "Full bi-directional integration with DHIS2 & national e-LMIS",
            "Autonomous drone and fleet dispatch routing integration"
        ])
    ]

    for p_name, p_time, p_col, p_items in phases:
        pt = tf_r.add_paragraph()
        pt.text = f"\n{p_name} ({p_time})"
        pt.font.name = FONT_HEADING
        pt.font.size = Pt(9.5)
        pt.font.bold = True
        pt.font.color.rgb = p_col

        for item in p_items:
            pi = tf_r.add_paragraph()
            pi.text = f"•  {item}"
            pi.font.name = FONT_BODY
            pi.font.size = Pt(8.5)
            pi.font.color.rgb = NAVY_LIGHT

    add_footer(slide6, 6)

    # ---------------------------------------------------------
    # SAVE PRESENTATION
    # ---------------------------------------------------------
    output_filename = "Healthcare_Supply_Chain_Pitch_Deck.pptx"
    prs.save(output_filename)
    print(f"[SUCCESS] Generated 6-slide presentation: {output_filename}")
    print(f"[INFO] Slide Count: {len(prs.slides)}")
    return output_filename

if __name__ == "__main__":
    create_pitch_deck()

