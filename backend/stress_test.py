from typing import Dict, Any, List
from models import Assets, StressScenario

# ─── SCENARIO DEFINITIONS ─────────────────────────────
# Each scenario defines % change per asset class
# Based on historical data and economic modeling

SCENARIOS = {
    StressScenario.MARKET_CRASH_2008: {
        "name": "2008 Global Financial Crisis",
        "description": (
            "Simulates the 2008 Lehman Brothers collapse. "
            "Global equity markets fell 50-60%. Gold initially dropped then surged. "
            "Real estate fell sharply in metros. FDs remained safe."
        ),
        "impacts": {
            "equity": -52.0,
            "gold": -15.0,
            "real_estate": -25.0,
            "liquid_cash": 0.0,
            "fd_value": 0.0
        },
        "recovery_years": 4.5,
        "severity": "EXTREME"
    },

    StressScenario.COVID_CRASH_2020: {
        "name": "COVID-19 Market Crash (March 2020)",
        "description": (
            "Simulates the March 2020 COVID crash. "
            "NIFTY fell 38% in 40 days. Gold surged as safe haven. "
            "Real estate demand froze temporarily. Recovery was unusually fast."
        ),
        "impacts": {
            "equity": -38.0,
            "gold": +12.0,
            "real_estate": -8.0,
            "liquid_cash": 0.0,
            "fd_value": 0.0
        },
        "recovery_years": 1.2,
        "severity": "SEVERE"
    },

    StressScenario.INFLATION_SURGE: {
        "name": "Inflation Surge (CPI > 10%)",
        "description": (
            "Simulates a sustained high inflation environment (CPI > 10%). "
            "Cash and FD real returns turn negative. "
            "Gold and real estate benefit as inflation hedges. "
            "Equity valuations compress."
        ),
        "impacts": {
            "equity": -20.0,
            "gold": +22.0,
            "real_estate": +8.0,
            "liquid_cash": -10.0,
            "fd_value": -5.0
        },
        "recovery_years": 2.5,
        "severity": "MODERATE"
    },

    StressScenario.RUPEE_COLLAPSE: {
        "name": "Rupee Collapse (-30% vs USD)",
        "description": (
            "Simulates a severe rupee depreciation scenario (₹/USD crosses 110+). "
            "Imports become expensive, inflation surges. "
            "Gold (dollar-denominated) rises sharply in rupee terms. "
            "Domestic equity and real estate face pressure."
        ),
        "impacts": {
            "equity": -25.0,
            "gold": +28.0,
            "real_estate": -5.0,
            "liquid_cash": -8.0,
            "fd_value": -3.0
        },
        "recovery_years": 3.0,
        "severity": "SEVERE"
    },

    StressScenario.REAL_ESTATE_CORRECTION: {
        "name": "Real Estate Correction (-35%)",
        "description": (
            "Simulates a sustained real estate market correction. "
            "Metro property prices fall 35% over 3 years. "
            "This scenario is particularly impactful for India where "
            "real estate is often 60-80% of household net worth."
        ),
        "impacts": {
            "equity": -5.0,
            "gold": +5.0,
            "real_estate": -35.0,
            "liquid_cash": 0.0,
            "fd_value": 0.0
        },
        "recovery_years": 6.0,
        "severity": "SEVERE"
    },

    StressScenario.RATE_HIKE_SHOCK: {
        "name": "RBI Emergency Rate Hike (+300bps)",
        "description": (
            "Simulates an emergency RBI rate hike of 300 basis points "
            "(similar to US Fed 2022-23). "
            "Bond prices fall sharply. Equity valuations compress. "
            "FD rates become very attractive. "
            "Real estate demand drops as home loan EMIs surge."
        ),
        "impacts": {
            "equity": -30.0,
            "gold": -8.0,
            "real_estate": -15.0,
            "liquid_cash": 0.0,
            "fd_value": +12.0
        },
        "recovery_years": 2.0,
        "severity": "MODERATE"
    }
}


def run_stress_test(assets: Assets, scenario: StressScenario, market_data: Dict) -> Dict[str, Any]:

    scenario_config = SCENARIOS[scenario]
    impacts = scenario_config["impacts"]

    gold_price = market_data.get("gold_price_per_gram", 7200)
    gold_value = assets.gold_grams * gold_price

    current_values = {
        "equity": assets.mutual_funds,
        "gold": gold_value,
        "real_estate": assets.real_estate,
        "liquid_cash": assets.liquid_cash,
        "fd_value": 0
    }

    current_net_worth = sum(current_values.values()) - assets.liabilities

    # Apply stress impacts
    stressed_values = {}
    asset_impacts = []

    labels = {
        "equity": "Equity / Mutual Funds",
        "gold": "Gold",
        "real_estate": "Real Estate",
        "liquid_cash": "Liquid Cash",
        "fd_value": "FD / Debt"
    }

    for asset_class, current_val in current_values.items():
        impact_pct = impacts.get(asset_class, 0)
        stressed_val = current_val * (1 + impact_pct / 100)
        change = stressed_val - current_val

        stressed_values[asset_class] = stressed_val

        asset_impacts.append({
            "asset_class": labels[asset_class],
            "current_value": round(current_val, 2),
            "stressed_value": round(stressed_val, 2),
            "change_amount": round(change, 2),
            "change_pct": impact_pct
        })

    stressed_net_worth = sum(stressed_values.values()) - assets.liabilities
    total_impact = stressed_net_worth - current_net_worth
    impact_pct = (total_impact / current_net_worth * 100) if current_net_worth != 0 else 0

    ai_assessment = _generate_assessment(
        scenario_config, total_impact, impact_pct, current_values, stressed_values
    )

    protective_actions = _generate_protective_actions(
        scenario, impact_pct, current_values, assets
    )
    
    most_impacted = min(asset_impacts, key=lambda x: x["change_amount"])
    most_impacted_asset = most_impacted["asset_class"]

    return {
        "scenario": scenario_config["name"],
        "scenario_description": scenario_config["description"],
        "current_net_worth": round(current_net_worth, 2),
        "stressed_net_worth": round(stressed_net_worth, 2),
        "total_impact": round(total_impact, 2),
        "impact_pct": round(impact_pct, 2),
        "asset_impacts": asset_impacts,
        "recovery_estimate_years": scenario_config["recovery_years"],
        "severity": scenario_config["severity"],
        "ai_assessment": ai_assessment,
        "protective_actions": protective_actions,
        "most_impacted_asset": most_impacted_asset
    }


def _generate_assessment(config: Dict, total_impact: float, impact_pct: float,
                          current: Dict, stressed: Dict) -> str:

    worst_asset = min(
        current.keys(),
        key=lambda k: (stressed[k] - current[k]) / (current[k] + 1)
    )

    labels = {
        "equity": "Equity",
        "gold": "Gold",
        "real_estate": "Real Estate",
        "liquid_cash": "Cash",
        "fd_value": "FDs"
    }

    return (
        f"Under the {config['name']} scenario, your portfolio would lose "
        f"₹{abs(total_impact):,.0f} ({abs(impact_pct):.1f}% of net worth). "
        f"{labels.get(worst_asset, worst_asset)} would be your most exposed asset. "
        f"Historical recovery from this scenario took approximately "
        f"{config['recovery_years']} years. "
        f"Severity rating: {config['severity']}."
    )


def _generate_protective_actions(scenario: StressScenario, impact_pct: float,
                                  current_values: Dict, assets: Assets) -> List[str]:
    actions = []

    real_estate_pct = current_values["real_estate"] / (sum(current_values.values()) + 1) * 100

    if scenario == StressScenario.MARKET_CRASH_2008:
        actions.append("Maintain 6-month emergency fund in liquid cash or short-term FDs before market events.")
        actions.append("Avoid panic selling — 2008 recovery rewarded those who held equity for 4+ years.")
        if current_values["gold"] < current_values["equity"] * 0.3:
            actions.append("Increase gold allocation to at least 15% as a crisis hedge.")

    elif scenario == StressScenario.COVID_CRASH_2020:
        actions.append("COVID crash recovered in under 18 months — SIP continuity was key to capturing the recovery.")
        actions.append("Keep emergency fund separate from investment portfolio to avoid forced selling at lows.")

    elif scenario == StressScenario.INFLATION_SURGE:
        actions.append("Increase gold allocation — it has historically outperformed during high-inflation periods.")
        actions.append("Avoid long-duration FDs during inflation spikes — lock in short-term only.")
        actions.append("Consider inflation-linked bonds (RBI Floating Rate Bonds) for the cash portion.")

    elif scenario == StressScenario.REAL_ESTATE_CORRECTION:
        if real_estate_pct > 50:
            actions.append(
                f"Your real estate is {real_estate_pct:.0f}% of your portfolio — "
                f"highly concentrated. Consider diversifying into liquid assets to reduce this risk."
            )
        actions.append("Real estate is illiquid — ensure you have enough liquid assets to cover EMIs without selling property at a loss.")
        actions.append("Rental income provides a buffer — if property is rented, factor that into your stress scenario.")

    elif scenario == StressScenario.RATE_HIKE_SHOCK:
        actions.append("Rate hike scenarios benefit FD holders — lock in current rates for 1-3 years before any hike reversal.")
        actions.append("Floating rate home loans will see EMI increases — ensure your monthly surplus can absorb a 20-25% EMI rise.")

    if impact_pct < -30:
        actions.append(
            "This scenario causes severe damage to your portfolio. "
            "Consider stress-testing your emergency fund — ensure it covers 12 months of expenses, not just 6."
        )

    return actions