from typing import Dict, Any

# ─── MOCK NEIGHBORHOOD DATA ───────────────────────────
# In production: replace with a real PropTech API
# Structure: zip_code -> appreciation data

NEIGHBORHOOD_DATA = {
    # Mumbai
    "400001": {"area": "Fort, Mumbai", "avg_appreciation_pct": 8.2, "demand": "HIGH", "tier": 1},
    "400051": {"area": "Bandra, Mumbai", "avg_appreciation_pct": 11.4, "demand": "VERY HIGH", "tier": 1},
    "400076": {"area": "Powai, Mumbai", "avg_appreciation_pct": 9.1, "demand": "HIGH", "tier": 1},
    # Delhi
    "110001": {"area": "Connaught Place, Delhi", "avg_appreciation_pct": 7.8, "demand": "HIGH", "tier": 1},
    "110075": {"area": "Dwarka, Delhi", "avg_appreciation_pct": 9.6, "demand": "HIGH", "tier": 2},
    "110092": {"area": "Preet Vihar, Delhi", "avg_appreciation_pct": 8.4, "demand": "MEDIUM", "tier": 2},
    # Bangalore
    "560001": {"area": "MG Road, Bangalore", "avg_appreciation_pct": 10.2, "demand": "VERY HIGH", "tier": 1},
    "560037": {"area": "Koramangala, Bangalore", "avg_appreciation_pct": 12.1, "demand": "VERY HIGH", "tier": 1},
    "560103": {"area": "Whitefield, Bangalore", "avg_appreciation_pct": 11.8, "demand": "HIGH", "tier": 1},
    # Hyderabad
    "500081": {"area": "Gachibowli, Hyderabad", "avg_appreciation_pct": 13.4, "demand": "VERY HIGH", "tier": 1},
    "500032": {"area": "Banjara Hills, Hyderabad", "avg_appreciation_pct": 10.7, "demand": "HIGH", "tier": 1},
    # Chennai
    "600001": {"area": "Anna Salai, Chennai", "avg_appreciation_pct": 7.2, "demand": "MEDIUM", "tier": 1},
    "600096": {"area": "OMR, Chennai", "avg_appreciation_pct": 9.8, "demand": "HIGH", "tier": 2},
    # Pune
    "411001": {"area": "Pune City", "avg_appreciation_pct": 8.9, "demand": "HIGH", "tier": 2},
    "411045": {"area": "Hinjewadi, Pune", "avg_appreciation_pct": 11.2, "demand": "VERY HIGH", "tier": 2},
}

DEFAULT_APPRECIATION = 7.0  # fallback if ZIP not found


def get_neighborhood_data(zip_code: str) -> Dict:
    return NEIGHBORHOOD_DATA.get(zip_code.strip(), None)


def analyze_property(
    property_value: float,
    zip_code: str,
    years: int = 5
) -> Dict[str, Any]:

    neighborhood = get_neighborhood_data(zip_code)

    if neighborhood:
        appreciation_rate = neighborhood["avg_appreciation_pct"]
        area_name = neighborhood["area"]
        demand = neighborhood["demand"]
        found = True
    else:
        appreciation_rate = DEFAULT_APPRECIATION
        area_name = f"ZIP {zip_code}"
        demand = "UNKNOWN"
        found = False

    # Compound appreciation projection
    projected_value = property_value * ((1 + appreciation_rate / 100) ** years)
    total_gain = projected_value - property_value
    annual_gain = total_gain / years

    # Rental yield estimate (rough rule of thumb for Indian real estate)
    estimated_rental_yield = 2.5 if neighborhood and neighborhood["tier"] == 1 else 3.2

    return {
        "zip_code": zip_code,
        "area_name": area_name,
        "found_in_database": found,
        "current_value": property_value,
        "appreciation_rate_pct": appreciation_rate,
        "demand_level": demand,
        "projection": {
            "years": years,
            "projected_value": round(projected_value, 2),
            "total_gain": round(total_gain, 2),
            "annual_gain": round(annual_gain, 2),
        },
        "estimated_rental_yield_pct": estimated_rental_yield,
        "recommendation": _generate_property_recommendation(
            appreciation_rate, demand, property_value, projected_value
        )
    }


def _generate_property_recommendation(
    rate: float,
    demand: str,
    current: float,
    projected: float
) -> str:
    gain_pct = ((projected - current) / current) * 100

    if rate > 11 and demand == "VERY HIGH":
        return (
            f"Strong appreciation zone. Expected {gain_pct:.0f}% total gain. "
            f"Holding is recommended — this area is outperforming most asset classes."
        )
    elif rate > 8 and demand in ["HIGH", "VERY HIGH"]:
        return (
            f"Good appreciation area. Expected {gain_pct:.0f}% total gain. "
            f"Property is a solid long-term hold alongside liquid investments."
        )
    elif rate > 6:
        return (
            f"Moderate appreciation. Expected {gain_pct:.0f}% total gain. "
            f"Consider whether liquidity needs are met before locking more capital here."
        )
    else:
        return (
            f"Below-average appreciation zone. Expected {gain_pct:.0f}% total gain. "
            f"Evaluate whether redeploying capital to higher-yield assets makes sense."
        )