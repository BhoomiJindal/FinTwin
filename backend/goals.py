from typing import Dict, Any, List
from models import Goal

# Assumed annual return rate for goal calculations
# Conservative blended rate across asset classes
ASSUMED_ANNUAL_RETURN = 9.0


def calculate_required_monthly(target_amount: float, current_saved: float, years: float, annual_return: float = ASSUMED_ANNUAL_RETURN) -> float:
    """
    Calculate monthly SIP needed to reach target_amount in `years`,
    given current_saved as starting point and assumed annual return.
    Uses future value of annuity formula.
    """
    if years <= 0:
        return max(0, target_amount - current_saved)

    monthly_rate = annual_return / 100 / 12
    months = years * 12

    # Future value of current savings
    fv_current = current_saved * ((1 + monthly_rate) ** months)

    remaining_target = target_amount - fv_current

    if remaining_target <= 0:
        return 0.0

    # Future value of annuity formula solved for payment
    if monthly_rate == 0:
        required_monthly = remaining_target / months
    else:
        required_monthly = remaining_target * monthly_rate / (((1 + monthly_rate) ** months) - 1)

    return max(0, round(required_monthly, 2))


def project_completion_time(target_amount: float, current_saved: float, monthly_contribution: float, annual_return: float = ASSUMED_ANNUAL_RETURN) -> float:
    """
    Given current contribution rate, how many years until target is reached.
    Returns a large number if it will never be reached.
    """
    if monthly_contribution <= 0:
        if current_saved >= target_amount:
            return 0.0
        return 99.0  # effectively "never"

    monthly_rate = annual_return / 100 / 12
    balance = current_saved
    months = 0
    max_months = 99 * 12  # cap at 99 years

    while balance < target_amount and months < max_months:
        balance = balance * (1 + monthly_rate) + monthly_contribution
        months += 1

    return round(months / 12, 1)


def generate_status_message(goal: Goal, required_monthly: float, projected_years: float) -> tuple[str, str]:
    """Returns (status, ai_message)"""

    gap = required_monthly - goal.monthly_contribution

    if goal.current_saved >= goal.target_amount:
        return "AHEAD", (
            f"Goal already achieved! You have ₹{goal.current_saved:,.0f} "
            f"saved against a target of ₹{goal.target_amount:,.0f}."
        )

    if projected_years <= goal.target_years:
        if gap < -100:  # contributing more than needed
            surplus_years = goal.target_years - projected_years
            return "AHEAD", (
                f"You're ahead of schedule. At your current contribution of "
                f"₹{goal.monthly_contribution:,.0f}/month, you'll reach "
                f"₹{goal.target_amount:,.0f} in {projected_years} years — "
                f"{surplus_years:.1f} years earlier than your {goal.target_years}-year target."
            )
        return "ON_TRACK", (
            f"On track. Your current contribution of ₹{goal.monthly_contribution:,.0f}/month "
            f"will reach ₹{goal.target_amount:,.0f} in approximately {projected_years} years, "
            f"within your {goal.target_years}-year target."
        )
    else:
        delay_years = projected_years - goal.target_years
        return "BEHIND", (
            f"Behind schedule. At ₹{goal.monthly_contribution:,.0f}/month, "
            f"you'll reach this goal in {projected_years} years — "
            f"{delay_years:.1f} years later than your {goal.target_years}-year target. "
            f"Increasing your monthly contribution to ₹{required_monthly:,.0f} "
            f"(an increase of ₹{gap:,.0f}) would get you back on track."
        )


def calculate_goal_progress(goal: Goal) -> Dict[str, Any]:

    required_monthly = calculate_required_monthly(
        goal.target_amount, goal.current_saved, goal.target_years
    )

    projected_years = project_completion_time(
        goal.target_amount, goal.current_saved, goal.monthly_contribution
    )

    progress_pct = min(100, round((goal.current_saved / goal.target_amount) * 100, 1)) if goal.target_amount > 0 else 0

    status, ai_message = generate_status_message(goal, required_monthly, projected_years)

    monthly_gap = max(0, required_monthly - goal.monthly_contribution)

    return {
        "name": goal.name,
        "category": goal.category.value if hasattr(goal.category, 'value') else goal.category,
        "target_amount": goal.target_amount,
        "current_saved": goal.current_saved,
        "progress_pct": progress_pct,
        "target_years": goal.target_years,
        "required_monthly_contribution": required_monthly,
        "current_monthly_contribution": goal.monthly_contribution,
        "monthly_gap": round(monthly_gap, 2),
        "projected_completion_years": projected_years,
        "status": status,
        "ai_status_message": ai_message
    }


def analyze_all_goals(goals: List[Goal]) -> Dict[str, Any]:

    results = [calculate_goal_progress(g) for g in goals]

    on_track = sum(1 for r in results if r["status"] in ["ON_TRACK", "AHEAD"])
    behind = sum(1 for r in results if r["status"] == "BEHIND")

    if behind == 0:
        overall = f"All {len(results)} goals are on track or ahead of schedule. Excellent financial planning."
    elif behind == len(results):
        total_gap = sum(r["monthly_gap"] for r in results)
        overall = (
            f"All {len(results)} goals are currently behind schedule. "
            f"An additional ₹{total_gap:,.0f}/month across all goals would bring everything on track."
        )
    else:
        behind_goals = [r["name"] for r in results if r["status"] == "BEHIND"]
        overall = (
            f"{on_track} of {len(results)} goals are on track. "
            f"{behind} goal(s) need attention: {', '.join(behind_goals)}."
        )

    return {
        "goals": results,
        "total_goals": len(results),
        "goals_on_track": on_track,
        "goals_behind": behind,
        "overall_message": overall
    }