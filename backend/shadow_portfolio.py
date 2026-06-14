from typing import Dict, Any, List, Optional

# Default ideal allocation if no archetype is set
# Balanced moderate profile
DEFAULT_ALLOCATION = {
    "equity_mutual_funds": 30,
    "gold": 15,
    "real_estate": 30,
    "liquid_cash": 15,
    "fd_debt": 10
}


def calculate_current_allocation(assets: Dict, market: Dict) -> Dict[str, float]:
    gold_value = assets.get("gold_grams", 0) * market["gold_price_per_gram"]

    total = (
        assets.get("liquid_cash", 0) +
        assets.get("mutual_funds", 0) +
        gold_value +
        assets.get("real_estate", 0)
    )

    if total == 0:
        return {k: 0 for k in DEFAULT_ALLOCATION}

    return {
        "equity_mutual_funds": round((assets.get("mutual_funds", 0) / total) * 100, 1),
        "gold": round((gold_value / total) * 100, 1),
        "real_estate": round((assets.get("real_estate", 0) / total) * 100, 1),
        "liquid_cash": round((assets.get("liquid_cash", 0) / total) * 100, 1),
        "fd_debt": 0.0  # not tracked separately in current asset model
    }


def calculate_divergence(assets: Dict, market: Dict, ideal_allocation: Dict = None) -> Dict[str, Any]:

    if ideal_allocation is None:
        ideal_allocation = DEFAULT_ALLOCATION

    current = calculate_current_allocation(assets, market)

    breakdown = []
    total_divergence = 0

    labels = {
        "equity_mutual_funds": "Equity / Mutual Funds",
        "gold": "Gold",
        "real_estate": "Real Estate",
        "liquid_cash": "Liquid Cash",
        "fd_debt": "FD / Debt Funds"
    }

    for asset_class, ideal_pct in ideal_allocation.items():
        current_pct = current.get(asset_class, 0)
        diff = round(current_pct - ideal_pct, 1)

        breakdown.append({
            "asset_class": labels.get(asset_class, asset_class),
            "current_pct": current_pct,
            "ideal_pct": ideal_pct,
            "difference": diff
        })

        total_divergence += abs(diff)

    # Divergence score: 0 = perfectly aligned, 100 = maximally diverged
    # Max possible total divergence is 200 (100% in wrong places)
    # but realistically caps around 100-120, so we scale accordingly
    divergence_score = min(100, round(total_divergence / 1.5))

    # Find biggest gap
    biggest_gap = max(breakdown, key=lambda x: abs(x["difference"]))

    # Determine urgency
    if divergence_score < 20:
        urgency = "LOW"
    elif divergence_score < 45:
        urgency = "MEDIUM"
    else:
        urgency = "HIGH"

    # Generate AI summary
    direction = "overweight" if biggest_gap["difference"] > 0 else "underweight"
    summary = _generate_summary(divergence_score, urgency, biggest_gap, direction)

    return {
        "divergence_score": divergence_score,
        "urgency": urgency,
        "breakdown": breakdown,
        "biggest_gap": biggest_gap,
        "ai_summary": summary
    }


def _generate_summary(score: int, urgency: str, biggest_gap: Dict, direction: str) -> str:

    asset = biggest_gap["asset_class"]
    diff = abs(biggest_gap["difference"])

    if urgency == "LOW":
        return (
            f"Your portfolio is well-aligned with your target allocation. "
            f"Divergence score: {score}/100. Minor rebalancing in {asset} "
            f"({direction} by {diff}%) could be addressed at your convenience."
        )
    elif urgency == "MEDIUM":
        return (
            f"Your portfolio has moderate drift from your target allocation. "
            f"Divergence score: {score}/100. "
            f"{asset} is {direction} by {diff} percentage points — "
            f"consider rebalancing within the next few months."
        )
    else:
        return (
            f"Your portfolio has significant drift from your target allocation. "
            f"Divergence score: {score}/100. "
            f"{asset} is {direction} by {diff} percentage points — "
            f"this is the largest gap and should be addressed soon to maintain "
            f"your intended risk profile."
        )