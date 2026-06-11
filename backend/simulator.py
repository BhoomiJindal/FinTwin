from typing import Dict, Any, List

# ─── HISTORICAL RETURNS DATA ──────────────────────────
# Annual returns by asset class (approximate Indian market data)

HISTORICAL_RETURNS = {
    "nifty50": {
        2019: 12.0, 2020: 15.0, 2021: 24.0,
        2022: 4.0,  2023: 20.0, 2024: 9.0
    },
    "gold": {
        2019: 25.0, 2020: 28.0, 2021: -5.0,
        2022: 12.0, 2023: 15.0, 2024: 14.0
    },
    "fd": {
        2019: 7.0,  2020: 6.5,  2021: 5.5,
        2022: 6.0,  2023: 7.0,  2024: 7.2
    },
    "real_estate": {
        2019: 5.0,  2020: 2.0,  2021: 7.0,
        2022: 8.0,  2023: 9.0,  2024: 10.0
    },
    "mutual_funds_debt": {
        2019: 9.0,  2020: 11.0, 2021: 4.0,
        2022: 4.5,  2023: 7.0,  2024: 7.5
    }
}

ASSET_LABELS = {
    "nifty50": "NIFTY 50 Index",
    "gold": "Physical Gold",
    "fd": "Fixed Deposit",
    "real_estate": "Real Estate",
    "mutual_funds_debt": "Debt Mutual Funds"
}


def run_counterfactual(
    initial_amount: float,
    asset_class: str,
    from_year: int,
    to_year: int
) -> Dict[str, Any]:

    if asset_class not in HISTORICAL_RETURNS:
        return {"error": f"Unknown asset class: {asset_class}"}

    if from_year not in HISTORICAL_RETURNS[asset_class]:
        return {"error": f"No data available for {from_year}"}

    returns = HISTORICAL_RETURNS[asset_class]
    value = initial_amount
    yearly_breakdown = []

    for year in range(from_year, to_year + 1):
        if year in returns:
            rate = returns[year]
            gain = value * (rate / 100)
            value += gain
            yearly_breakdown.append({
                "year": year,
                "return_pct": rate,
                "gain": round(gain, 2),
                "value_at_end": round(value, 2)
            })

    total_gain = value - initial_amount
    total_return_pct = (total_gain / initial_amount) * 100

    return {
        "asset_class": asset_class,
        "asset_label": ASSET_LABELS[asset_class],
        "initial_amount": initial_amount,
        "from_year": from_year,
        "to_year": to_year,
        "final_value": round(value, 2),
        "total_gain": round(total_gain, 2),
        "total_return_pct": round(total_return_pct, 2),
        "yearly_breakdown": yearly_breakdown,
        "insight": _generate_insight(asset_class, total_return_pct, from_year, to_year)
    }


def compare_all_assets(
    initial_amount: float,
    from_year: int,
    to_year: int
) -> Dict[str, Any]:
    results = {}
    for asset in HISTORICAL_RETURNS:
        results[asset] = run_counterfactual(initial_amount, asset, from_year, to_year)

    # Rank by final value
    ranked = sorted(
        results.items(),
        key=lambda x: x[1].get("final_value", 0),
        reverse=True
    )

    best_asset = ranked[0][0]
    worst_asset = ranked[-1][0]

    return {
        "initial_amount": initial_amount,
        "period": f"{from_year} to {to_year}",
        "results": results,
        "best_performer": {
            "asset": best_asset,
            "label": ASSET_LABELS[best_asset],
            "final_value": results[best_asset]["final_value"],
            "total_return_pct": results[best_asset]["total_return_pct"]
        },
        "worst_performer": {
            "asset": worst_asset,
            "label": ASSET_LABELS[worst_asset],
            "final_value": results[worst_asset]["final_value"],
            "total_return_pct": results[worst_asset]["total_return_pct"]
        },
        "summary": (
            f"If you had invested ₹{initial_amount:,.0f} in {ASSET_LABELS[best_asset]} "
            f"in {from_year}, it would be worth ₹{results[best_asset]['final_value']:,.0f} today "
            f"— a {results[best_asset]['total_return_pct']:.1f}% total return."
        )
    }


def _generate_insight(asset: str, total_return: float, from_year: int, to_year: int) -> str:
    years = to_year - from_year + 1
    annual = total_return / years

    if annual > 15:
        return f"Exceptional performance — {annual:.1f}% average annual return over {years} years."
    elif annual > 10:
        return f"Strong performance — {annual:.1f}% average annual return, beating inflation comfortably."
    elif annual > 6:
        return f"Moderate performance — {annual:.1f}% average annual return, roughly matching inflation."
    else:
        return f"Underperformed — {annual:.1f}% average annual return. Other asset classes did better in this period."