from typing import Dict, Any, List
from models import TaxProfile

# ─── FY 2024-25 TAX SLABS (OLD REGIME) ────────────────

OLD_REGIME_SLABS = [
    (250000, 0.0),
    (500000, 0.05),
    (1000000, 0.20),
    (float('inf'), 0.30)
]

# ─── FY 2024-25 TAX SLABS (NEW REGIME) ────────────────

NEW_REGIME_SLABS = [
    (300000, 0.0),
    (700000, 0.05),
    (1000000, 0.10),
    (1200000, 0.15),
    (1500000, 0.20),
    (float('inf'), 0.30)
]

# ─── DEDUCTION LIMITS ──────────────────────────────────

LIMIT_80C = 150000       # ELSS, PPF, EPF, life insurance, etc.
LIMIT_80D_SELF = 25000    # health insurance for self/family (under 60)
LIMIT_80D_SENIOR = 50000  # health insurance for senior citizens
LIMIT_80CCD_1B = 50000    # additional NPS contribution
LIMIT_24B_HOME_LOAN = 200000  # home loan interest


def calculate_tax(taxable_income: float, regime: str) -> float:
    """Calculate tax payable for given taxable income and regime"""
    slabs = OLD_REGIME_SLABS if regime == "old" else NEW_REGIME_SLABS

    tax = 0.0
    previous_limit = 0

    for limit, rate in slabs:
        if taxable_income > previous_limit:
            taxable_in_slab = min(taxable_income, limit) - previous_limit
            tax += taxable_in_slab * rate
            previous_limit = limit
        else:
            break

    # Add 4% health and education cess
    tax_with_cess = tax * 1.04

    return round(tax_with_cess, 2)


def optimize_tax(profile: TaxProfile) -> Dict[str, Any]:

    income = profile.annual_income
    regime = profile.regime.value if hasattr(profile.regime, 'value') else profile.regime

    recommendations = []
    reasoning = []

    # ─── NEW REGIME: Limited deductions apply ────────
    if regime == "new":
        # New regime has standard deduction of 75000 (FY24-25) but most other deductions don't apply
        standard_deduction = 75000
        taxable_income = max(0, income - standard_deduction)
        current_tax = calculate_tax(taxable_income, "new")

        reasoning.append({
            "factor": "Tax Regime",
            "value": "New Regime",
            "impact": "Most deductions (80C, 80D, etc.) do not apply except standard deduction"
        })
        reasoning.append({
            "factor": "Standard Deduction",
            "value": f"₹{standard_deduction:,.0f}",
            "impact": "Automatically applied, no action needed"
        })

        # Check if switching to old regime would save more
        old_taxable = max(0, income - 50000 - LIMIT_80C - LIMIT_80D_SELF)
        old_tax = calculate_tax(old_taxable, "old")

        if old_tax < current_tax:
            savings_from_switch = current_tax - old_tax
            recommendations.append(
                f"Switching to the Old Regime and fully utilising 80C (₹{LIMIT_80C:,.0f}) "
                f"and 80D (₹{LIMIT_80D_SELF:,.0f}) could save you ₹{savings_from_switch:,.0f} this year."
            )
            reasoning.append({
                "factor": "Old Regime Comparison",
                "value": f"₹{old_tax:,.0f} vs ₹{current_tax:,.0f}",
                "impact": f"Old regime with full deductions saves ₹{savings_from_switch:,.0f}"
            })
        else:
            recommendations.append(
                "The New Regime is currently better for your income level. "
                "No further deduction-based optimisation is available — focus on increasing income or investments outside tax-saving instruments."
            )

        return {
            "tax_regime": "New Regime",
            "current_taxable_income": taxable_income,
            "current_tax_payable": current_tax,
            "optimized_tax_payable": min(current_tax, old_tax),
            "total_savings": max(0, current_tax - old_tax),
            "recommendations": recommendations,
            "deduction_breakdown": {"standard_deduction": standard_deduction},
            "reasoning": reasoning
        }

    # ─── OLD REGIME: Full deduction optimization ─────

    standard_deduction = 50000
    deductions_used = {
        "standard_deduction": standard_deduction,
        "section_80c": min(profile.existing_80c, LIMIT_80C),
        "section_80d": min(profile.existing_80d, LIMIT_80D_SELF),
        "home_loan_24b": min(profile.home_loan_interest, LIMIT_24B_HOME_LOAN),
        "nps_80ccd_1b": min(profile.nps_contribution, LIMIT_80CCD_1B),
    }

    total_deductions_used = sum(deductions_used.values())
    current_taxable_income = max(0, income - total_deductions_used)
    current_tax = calculate_tax(current_taxable_income, "old")

    reasoning.append({
        "factor": "Annual Income",
        "value": f"₹{income:,.0f}",
        "impact": "Base for tax calculation"
    })
    reasoning.append({
        "factor": "Total Deductions Claimed",
        "value": f"₹{total_deductions_used:,.0f}",
        "impact": f"Reduces taxable income to ₹{current_taxable_income:,.0f}"
    })

    # ─── Find optimization opportunities ─────────────

    optimized_deductions = dict(deductions_used)

    # 80C gap
    gap_80c = LIMIT_80C - profile.existing_80c
    if gap_80c > 0:
        optimized_deductions["section_80c"] = LIMIT_80C
        potential_savings_80c = gap_80c * 0.30 * 1.04  # at highest applicable rate, with cess
        recommendations.append(
            f"You have ₹{gap_80c:,.0f} of unused 80C limit. "
            f"Investing this in ELSS mutual funds (which also grow your wealth) "
            f"could save up to ₹{potential_savings_80c:,.0f} in tax, "
            f"depending on your tax slab."
        )
        reasoning.append({
            "factor": "80C Utilisation Gap",
            "value": f"₹{gap_80c:,.0f} unused",
            "impact": f"Filling this gap could save up to ₹{potential_savings_80c:,.0f}"
        })

    # 80D gap
    gap_80d = LIMIT_80D_SELF - profile.existing_80d
    if gap_80d > 0:
        recommendations.append(
            f"You have ₹{gap_80d:,.0f} of unused 80D health insurance deduction. "
            f"If you don't have health insurance, this is both a tax benefit "
            f"and financial protection — consider a family floater plan."
        )

    # NPS gap (80CCD1B) - additional to 80C
    gap_nps = LIMIT_80CCD_1B - profile.nps_contribution
    if gap_nps > 0:
        optimized_deductions["nps_80ccd_1b"] = LIMIT_80CCD_1B
        potential_savings_nps = gap_nps * 0.30 * 1.04
        recommendations.append(
            f"NPS offers an additional ₹{gap_nps:,.0f} deduction under 80CCD(1B), "
            f"separate from your 80C limit. This could save up to "
            f"₹{potential_savings_nps:,.0f} more, while building a retirement corpus."
        )
        reasoning.append({
            "factor": "NPS 80CCD(1B) Gap",
            "value": f"₹{gap_nps:,.0f} unused",
            "impact": f"Additional deduction beyond 80C — could save up to ₹{potential_savings_nps:,.0f}"
        })

    # Recalculate with optimized deductions
    optimized_total = sum(optimized_deductions.values())
    optimized_taxable_income = max(0, income - optimized_total)
    optimized_tax = calculate_tax(optimized_taxable_income, "old")

    total_savings = current_tax - optimized_tax

    if not recommendations:
        recommendations.append(
            "You are already utilising your major deductions well. "
            "Consider reviewing your investments annually as limits and rates may change."
        )

    reasoning.append({
        "factor": "Optimized Tax Payable",
        "value": f"₹{optimized_tax:,.0f}",
        "impact": f"Total potential savings of ₹{total_savings:,.0f} if all gaps are filled"
    })

    return {
        "tax_regime": "Old Regime",
        "current_taxable_income": current_taxable_income,
        "current_tax_payable": current_tax,
        "optimized_tax_payable": optimized_tax,
        "total_savings": round(total_savings, 2),
        "recommendations": recommendations,
        "deduction_breakdown": deductions_used,
        "reasoning": reasoning
    }