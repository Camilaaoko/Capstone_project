"""Generates custom infographic figures for the Capstone Pitch Deck slides."""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path

# Create output figures directory if needed
out_dir = Path("analytics_module/reports/figures")
out_dir.mkdir(parents=True, exist_ok=True)

# Set high-quality style
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

# --- Figure 1: Baseline vs. Intelligent System Comparison ---
fig, axes = plt.subplots(1, 4, figsize=(16, 4.2), facecolor='#021812')

metrics = [
    ("Avg Stockout Days", [14.2, 4.5], ["#EF4444", "#10B981"], "Days / Facility-Month", "-68.3%"),
    ("Batch Expiry Loss", [45.8, 26.5], ["#F59E0B", "#10B981"], "KES Millions / Year", "-42.1%"),
    ("Emergency Procurement", [28.4, 9.8], ["#EF4444", "#38BDF8"], "KES Millions / Year", "-65.5%"),
    ("AI Match Precision", [0, 99.4], ["#64748B", "#FF5A1F"], "Percentage (%)", "+99.4%")
]

for ax, (title, values, colors, unit, badge) in zip(axes, metrics):
    ax.set_facecolor('#04281F')
    labels = ["Baseline", "Intelligent"]
    bars = ax.bar(labels, values, color=colors, width=0.55, edgecolor='rgba(255,255,255,0.2)', linewidth=1.5)
    ax.set_title(title, color='#FFFFFF', fontsize=13, fontweight='bold', pad=12)
    ax.set_ylabel(unit, color='#94A3B8', fontsize=9.5)
    ax.tick_params(colors='#FFFFFF', labelsize=10.5)
    ax.grid(axis='y', linestyle='--', alpha=0.15, color='#FFFFFF')
    
    # Add value annotations
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f"{height:.1f}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points",
                        ha='center', va='bottom', color='#FFFFFF', fontweight='bold', fontsize=11)
            
    # Add improvement badge
    ax.text(0.5, 0.88, badge, transform=ax.transAxes,
            ha='center', va='center', color='#FFFFFF', fontweight='bold', fontsize=11,
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#0B8A62', edgecolor='#10B981', alpha=0.9))
    
    # Spine styling
    for spine in ax.spines.values():
        spine.set_color('rgba(255,255,255,0.15)')

plt.suptitle("Operational & Financial Impact: Baseline vs. Intelligent System", color='#FFFFFF', fontsize=15, fontweight='bold', y=1.04)
plt.tight_layout()
fig.savefig(out_dir / "deck_baseline_vs_intelligent.png", dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close(fig)
print("Saved: deck_baseline_vs_intelligent.png")

# --- Figure 2: System Architecture Diagram ---
fig, ax = plt.subplots(figsize=(16, 5.5), facecolor='#021812')
ax.set_facecolor('#021812')
ax.axis('off')

# Box components
steps = [
    ("1. Data Ingestion", "Synthetic Relational Engine\n• 150 Health Facilities\n• 45 Essential Commodities\n• 12 Suppliers & 6 Depots\n• 4.9M+ Fact Records", "#003399", 0.08),
    ("2. Automated ETL", "Data Quality & Cleaning\n• Schema Validation\n• Imputation of Demand Index\n• Deduplication & Cleaning\n• 7 Data Quality Fixes", "#0B8A62", 0.31),
    ("3. Star Schema DW", "Analytical Data Warehouse\n• 5 Dimension Tables\n• 6 Star Fact Tables\n• Aggregates & KPI Tables\n• Sub-100ms Querying", "#059669", 0.54),
    ("4. ML & AI Engine", "Forecasting & Optimization\n• LightGBM Demand Models\n• 7-Day Stockout Risk\n• FEFO Batch Expiry Logic\n• Surplus-Deficit Solver", "#D97706", 0.77),
    ("5. Decision Dash", "Multi-Tier Web Portal\n• Executive National KPIs\n• County GIS Heatmaps\n• Facility FEFO Gauges\n• Transfer Order Dispatch", "#FF5A1F", 1.00)
]

# Draw boxes and arrows
for title, desc, color, x_pos in steps:
    rect = patches.FancyBboxPatch((x_pos - 0.09, 0.15), 0.17, 0.70,
                                  boxstyle="round,pad=0.03,rounding_size=0.02",
                                  facecolor='#063428', edgecolor=color, linewidth=2.5)
    ax.add_patch(rect)
    
    # Title badge
    ax.text(x_pos - 0.005, 0.76, title, color='#FFFFFF', fontsize=11.5, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.25', facecolor=color, edgecolor='none'))
    
    # Description
    ax.text(x_pos - 0.005, 0.44, desc, color='#E2E8F0', fontsize=9.2, ha='center', va='center', linespacing=1.45)
    
    # Draw arrow to next step if not last
    if x_pos < 0.95:
        ax.annotate('', xy=(x_pos + 0.105, 0.50), xytext=(x_pos + 0.075, 0.50),
                    arrowprops=dict(facecolor='#38BDF8', edgecolor='#38BDF8', arrowstyle='->', lw=2.5, mutation_scale=18))

ax.text(0.48, 0.94, "End-to-End Enterprise Architecture: Ingestion to Decision Support",
        color='#FFFFFF', fontsize=14, fontweight='bold', ha='center')

plt.tight_layout()
fig.savefig(out_dir / "deck_system_architecture.png", dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close(fig)
print("Saved: deck_system_architecture.png")

# --- Figure 3: 4-Tier Decision Framework Infographic ---
fig, ax = plt.subplots(figsize=(15, 4.8), facecolor='#021812')
ax.set_facecolor('#021812')
ax.axis('off')

tiers = [
    ("Tier 1: Executive", "KEMSA CEO & MoH", "National visibility, budget optimization, supplier scorecard, and national stockout elimination.", "#38BDF8", 0.12),
    ("Tier 2: County GIS", "County Health Directors", "Geospatial shortage heatmaps, rural clinic deficits, inter-county equity rebalancing.", "#10B981", 0.37),
    ("Tier 3: Facility", "Pharmacists & Clinicians", "Days-of-Stock monitors, FEFO batch expiry countdowns, local consumption tracking.", "#F59E0B", 0.62),
    ("Tier 4: Logistics", "Supply Chain Planners", "Surplus-to-shortage transfer recommendations, route & transport cost optimization.", "#FF5A1F", 0.87)
]

for tier, subtitle, body, color, x in tiers:
    card = patches.FancyBboxPatch((x - 0.10, 0.1), 0.20, 0.78,
                                  boxstyle="round,pad=0.03,rounding_size=0.02",
                                  facecolor='#04281F', edgecolor=color, linewidth=2)
    ax.add_patch(card)
    ax.text(x, 0.78, tier, color=color, fontsize=11.5, fontweight='bold', ha='center')
    ax.text(x, 0.68, subtitle, color='#94A3B8', fontsize=9, fontweight='semibold', ha='center')
    ax.text(x, 0.38, body, color='#FFFFFF', fontsize=9.5, ha='center', va='center', wrap=True, linespacing=1.4)

ax.text(0.5, 0.95, "Four-Tier Stakeholder Decision Support Architecture",
        color='#FFFFFF', fontsize=14, fontweight='bold', ha='center')

plt.tight_layout()
fig.savefig(out_dir / "deck_four_tier_framework.png", dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close(fig)
print("Saved: deck_four_tier_framework.png")

