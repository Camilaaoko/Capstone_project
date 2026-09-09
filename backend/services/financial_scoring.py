"""Financial Risk Scoring & Explainability Service for KEMSA Intelligence Platform.

This module evaluates county pharmaceutical credit exposure and computes an objective
financial risk tier (Low / Medium / High) along with plain-language explainability factor
breakdowns for executive and county dashboards.
"""

from typing import Dict, Any, List, Optional


def calculate_county_financial_risk(
    amount_owed_kes: float,
    days_overdue: int,
    payment_history_score: float,
    county_name: Optional[str] = None
) -> Dict[str, Any]:
    """Computes a composite financial risk score and explainability breakdown.

    Risk Model Weighting & Rationale:
    --------------------------------
    1. Days Overdue (Weight: 40%):
       Direct measure of chronic arrears age and cash flow delinquency. Overdue days
       scale linearly up to a severe delinquency threshold of 180+ days.
       Formula: overdue_score = min(100.0, (days_overdue / 180.0) * 100.0)

    2. Amount Owed (Weight: 35%):
       Measures absolute debt magnitude relative to county procurement scale. Scaled
       against a benchmark ceiling of KES 400M.
       Formula: debt_score = min(100.0, (amount_owed_kes / 400_000_000.0) * 100.0)

    3. Payment History / Reliability (Weight: 25%):
       Evaluates historical payment consistency and treasury release frequency (0-100 scale).
       Inverted to represent risk (100 = perfect payment, 0 = non-payer).
       Formula: payment_risk_score = max(0.0, 100.0 - payment_history_score)

    Composite Score Formula:
    ------------------------
    composite_score = (0.40 * overdue_score) + (0.35 * debt_score) + (0.25 * payment_risk_score)

    Risk Tiers:
    -----------
    - Low Risk:    Score < 35.0  (Healthy credit standing, prompt releases)
    - Medium Risk: 35.0 <= Score < 65.0 (Moderate delays or manageable balances)
    - High Risk:   Score >= 65.0 (Critical debt accumulation, chronic non-payment)
    """
    # 1. Normalize individual factor scores (0 - 100)
    overdue_score = min(100.0, (max(0, days_overdue) / 180.0) * 100.0)
    debt_score = min(100.0, (max(0.0, amount_owed_kes) / 400_000_000.0) * 100.0)
    payment_risk_score = min(100.0, max(0.0, 100.0 - float(payment_history_score)))

    # 2. Compute composite weighted risk score
    raw_composite = (0.40 * overdue_score) + (0.35 * debt_score) + (0.25 * payment_risk_score)
    risk_score = round(max(0.0, min(100.0, raw_composite)), 1)

    # 3. Determine Risk Tier
    if risk_score >= 65.0:
        risk_tier = "High"
        tier_color = "#EF4444"  # Red
        tier_badge = "CRITICAL DEBT RISK"
    elif risk_score >= 35.0:
        risk_tier = "Medium"
        tier_color = "#F59E0B"  # Amber
        tier_badge = "MODERATE RISK"
    else:
        risk_tier = "Low"
        tier_color = "#10B981"  # Green
        tier_badge = "HEALTHY STANDING"

    # 4. Generate Explainability Factor Breakdown (Plain Language Ready)
    # Debt factor assessment
    if amount_owed_kes >= 180_000_000:
        debt_contrib = "critical" if amount_owed_kes >= 300_000_000 else "high"
        debt_text = f"High outstanding debt of KES {amount_owed_kes:,.0f} places severe fiscal strain on supply continuity."
    elif amount_owed_kes >= 50_000_000:
        debt_contrib = "moderate"
        debt_text = f"Moderate balance of KES {amount_owed_kes:,.0f} remains within manageable procurement limits."
    else:
        debt_contrib = "low"
        debt_text = f"Low debt exposure of KES {amount_owed_kes:,.0f} reflects disciplined credit utilization."

    # Overdue factor assessment
    if days_overdue >= 90:
        overdue_contrib = "critical" if days_overdue >= 180 else "high"
        overdue_text = f"Invoices are {days_overdue} days overdue, signaling severe payment bottlenecks."
    elif days_overdue >= 30:
        overdue_contrib = "moderate"
        overdue_text = f"Payment delays averaging {days_overdue} days require structured disbursement scheduling."
    else:
        overdue_contrib = "low"
        overdue_text = f"Prompt settlement timeline with oldest invoice at {days_overdue} days overdue."

    # Payment history assessment
    if payment_history_score < 45:
        history_contrib = "high"
        history_text = f"Historical payment score of {payment_history_score:.0f}/100 indicates chronic non-payment risks."
    elif payment_history_score < 75:
        history_contrib = "moderate"
        history_text = f"Payment reliability rating of {payment_history_score:.0f}/100 shows intermittent quarterly settlements."
    else:
        history_contrib = "low"
        history_text = f"Excellent payment record rating of {payment_history_score:.0f}/100 demonstrating dependable settlement."

    factors = [
        {
            "factor": "days_overdue",
            "factor_name": "Arrears Age / Days Overdue",
            "value": days_overdue,
            "formatted_value": f"{days_overdue} days",
            "weight_pct": 40,
            "contribution": overdue_contrib,
            "score_contribution": round(0.40 * overdue_score, 1),
            "description": overdue_text
        },
        {
            "factor": "amount_owed",
            "factor_name": "Outstanding Debt Volume",
            "value": amount_owed_kes,
            "formatted_value": f"KES {amount_owed_kes:,.0f}",
            "weight_pct": 35,
            "contribution": debt_contrib,
            "score_contribution": round(0.35 * debt_score, 1),
            "description": debt_text
        },
        {
            "factor": "payment_history",
            "factor_name": "Payment Reliability History",
            "value": payment_history_score,
            "formatted_value": f"{payment_history_score:.0f}/100",
            "weight_pct": 25,
            "contribution": history_contrib,
            "score_contribution": round(0.25 * payment_risk_score, 1),
            "description": history_text
        }
    ]

    # Sort factors by severity contribution
    severity_rank = {"critical": 4, "high": 3, "moderate": 2, "low": 1}
    sorted_factors = sorted(factors, key=lambda f: severity_rank.get(f["contribution"], 0), reverse=True)

    # 5. Build Synthesized Plain-Language Summary
    county_display = county_name or "This county"
    if risk_tier == "High":
        plain_summary = (
            f"{county_display} is in the High Risk Tier (Score: {risk_score}/100). "
            f"The primary driver is {sorted_factors[0]['factor_name'].lower()} ({sorted_factors[0]['formatted_value']}), "
            f"compounded by {sorted_factors[1]['factor_name'].lower()} ({sorted_factors[1]['formatted_value']}). "
            f"KEMSA credit exposure is critical and requires treasury intervention before next delivery cycle."
        )
    elif risk_tier == "Medium":
        plain_summary = (
            f"{county_display} is in the Medium Risk Tier (Score: {risk_score}/100). "
            f"Financial standing is stable but monitored due to {sorted_factors[0]['factor_name'].lower()} "
            f"({sorted_factors[0]['formatted_value']}). Structured invoice settlement is recommended."
        )
    else:
        plain_summary = (
            f"{county_display} maintains a Low Risk Tier (Score: {risk_score}/100) with healthy financial standing. "
            f"Prompt invoice settlement ({days_overdue} days overdue) and dependable payment history ({payment_history_score:.0f}/100) "
            f"qualify this county for prioritized order fulfillment."
        )

    return {
        "risk_score": risk_score,
        "risk_tier": risk_tier,
        "tier_color": tier_color,
        "tier_badge": tier_badge,
        "amount_owed_kes": amount_owed_kes,
        "days_overdue": days_overdue,
        "payment_history_score": payment_history_score,
        "factors": factors,
        "primary_driver": sorted_factors[0]["factor_name"],
        "plain_language_summary": plain_summary
    }
