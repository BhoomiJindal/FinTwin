from typing import Dict, Any
from models import UserProfile, Archetype, ArchetypeResponse

# ─── ARCHETYPE DEFINITIONS ────────────────────────────

ARCHETYPES = {
    Archetype.ACCUMULATOR: {
        "label": "The Accumulator",
        "description": (
            "You are in wealth-building mode. Your long investment horizon "
            "and high risk tolerance mean you can ride out market volatility "
            "and should prioritise growth assets over safe ones."
        ),
        "recommended_allocation": {
            "equity_mutual_funds": 50,
            "gold": 10,
            "real_estate": 20,
            "liquid_cash": 10,
            "fd_debt": 10
        },
        "advisor_style": (
            "Give aggressive growth-oriented advice. "
            "Prioritise long-term compounding over short-term safety. "
            "Be direct and specific with numbers. "
            "Do not over-warn about risks — this user understands them."
        ),
        "key_priorities": [
            "Maximise long-term returns",
            "Build equity exposure systematically via SIPs",
            "Keep emergency fund lean but present"
        ]
    },

    Archetype.PROTECTOR: {
        "label": "The Protector",
        "description": (
            "Your family's financial security comes first. "
            "You prefer stable, predictable returns over high-risk growth. "
            "Insurance, emergency funds, and low-volatility assets are your priority."
        ),
        "recommended_allocation": {
            "equity_mutual_funds": 20,
            "gold": 20,
            "real_estate": 30,
            "liquid_cash": 20,
            "fd_debt": 10
        },
        "advisor_style": (
            "Give conservative, safety-first advice. "
            "Always mention insurance and emergency fund adequacy. "
            "Reassure before recommending. "
            "Flag downside risks clearly. "
            "Prefer capital preservation over growth."
        ),
        "key_priorities": [
            "Adequate insurance coverage",
            "6-month emergency fund always maintained",
            "Low-volatility asset allocation"
        ]
    },

    Archetype.OPTIMIZER: {
        "label": "The Optimizer",
        "description": (
            "You treat your portfolio like a system to be fine-tuned. "
            "Tax efficiency, rebalancing, and maximising post-tax returns "
            "matter more to you than chasing raw returns."
        ),
        "recommended_allocation": {
            "equity_mutual_funds": 35,
            "gold": 10,
            "real_estate": 25,
            "liquid_cash": 10,
            "fd_debt": 20
        },
        "advisor_style": (
            "Give analytical, tax-aware advice. "
            "Always calculate post-tax returns. "
            "Mention 80C, ELSS, NPS opportunities when relevant. "
            "Use precise numbers and percentages. "
            "This user appreciates complexity — do not oversimplify."
        ),
        "key_priorities": [
            "Maximise post-tax returns",
            "Fully utilise 80C and other deductions",
            "Regular portfolio rebalancing"
        ]
    },

    Archetype.PRESERVER: {
        "label": "The Preserver",
        "description": (
            "Capital protection is your top priority. "
            "You are approaching or in retirement and cannot afford "
            "significant drawdowns. Steady income and inflation protection matter most."
        ),
        "recommended_allocation": {
            "equity_mutual_funds": 10,
            "gold": 20,
            "real_estate": 20,
            "liquid_cash": 25,
            "fd_debt": 25
        },
        "advisor_style": (
            "Give capital-preservation focused advice. "
            "Prioritise income-generating assets and inflation hedges. "
            "Warn strongly against high-risk moves. "
            "Always consider withdrawal needs and liquidity. "
            "Mention Senior Citizen FD rates and SCSS when relevant."
        ),
        "key_priorities": [
            "Capital protection above all",
            "Stable monthly income generation",
            "Inflation-proof asset allocation"
        ]
    }
}


# ─── CLASSIFICATION LOGIC ─────────────────────────────

def classify_archetype(profile: UserProfile) -> Archetype:

    score = {
        Archetype.ACCUMULATOR: 0,
        Archetype.PROTECTOR: 0,
        Archetype.OPTIMIZER: 0,
        Archetype.PRESERVER: 0
    }

    # Age signal
    if profile.age < 30:
        score[Archetype.ACCUMULATOR] += 3
    elif profile.age < 45:
        score[Archetype.ACCUMULATOR] += 1
        score[Archetype.OPTIMIZER] += 2
    elif profile.age < 55:
        score[Archetype.OPTIMIZER] += 2
        score[Archetype.PROTECTOR] += 1
    else:
        score[Archetype.PRESERVER] += 4

    # Risk appetite signal
    if profile.risk_appetite == "high":
        score[Archetype.ACCUMULATOR] += 3
    elif profile.risk_appetite == "medium":
        score[Archetype.OPTIMIZER] += 2
        score[Archetype.PROTECTOR] += 1
    else:
        score[Archetype.PROTECTOR] += 2
        score[Archetype.PRESERVER] += 2

    # Dependents signal
    if profile.dependents >= 3:
        score[Archetype.PROTECTOR] += 3
    elif profile.dependents >= 1:
        score[Archetype.PROTECTOR] += 1
        score[Archetype.OPTIMIZER] += 1
    else:
        score[Archetype.ACCUMULATOR] += 1

    # Primary goal signal
    goal_map = {
        "growth": Archetype.ACCUMULATOR,
        "preservation": Archetype.PRESERVER,
        "income": Archetype.PROTECTOR,
        "tax_saving": Archetype.OPTIMIZER
    }
    if profile.primary_goal in goal_map:
        score[goal_map[profile.primary_goal]] += 3

    # Investment horizon signal
    if profile.investment_horizon_years >= 15:
        score[Archetype.ACCUMULATOR] += 2
    elif profile.investment_horizon_years >= 7:
        score[Archetype.OPTIMIZER] += 2
    elif profile.investment_horizon_years >= 3:
        score[Archetype.PROTECTOR] += 1
    else:
        score[Archetype.PRESERVER] += 2

    # Return the archetype with highest score
    return max(score, key=score.get)


def get_archetype_response(profile: UserProfile) -> Dict[str, Any]:
    archetype = classify_archetype(profile)
    data = ARCHETYPES[archetype]

    return {
        "archetype": archetype,
        "label": data["label"],
        "description": data["description"],
        "recommended_allocation": data["recommended_allocation"],
        "advisor_style": data["advisor_style"],
        "key_priorities": data["key_priorities"]
    }


def get_archetype_context(archetype: Archetype) -> str:
    """
    Returns a string injected into the LLM system prompt
    so every response is calibrated to this user's archetype
    """
    if archetype not in ARCHETYPES:
        return ""

    data = ARCHETYPES[archetype]
    allocation = data["recommended_allocation"]

    return (
        f"\nUSER ARCHETYPE: {data['label']}\n"
        f"Advisor style: {data['advisor_style']}\n"
        f"Ideal allocation for this user: "
        f"Equity {allocation['equity_mutual_funds']}%, "
        f"Gold {allocation['gold']}%, "
        f"Real Estate {allocation['real_estate']}%, "
        f"Cash {allocation['liquid_cash']}%, "
        f"FD/Debt {allocation['fd_debt']}%\n"
        f"Key priorities: {', '.join(data['key_priorities'])}\n"
    )