import os
import anthropic
from dotenv import load_dotenv
from typing import Dict, Any

# Stores last 6 messages per session (3 exchanges)
# Resets on server restart — fine for prototype
conversation_history = []

load_dotenv()

# ─── CLIENT SETUP ─────────────────────────────────────

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ─── MOCK MARKET DATA ─────────────────────────────────
# Replace with live NSE/BSE API calls in production

def get_market_context() -> Dict[str, float]:
    return {
        "gold_price_per_gram": 7200.0,
        "repo_rate": 6.50,
        "inflation_rate": 5.10,
        "nifty_pe": 22.4,
        "fd_rate": 7.20,
        "gold_1yr_return": 14.2,
        "nifty_1yr_return": 11.8
    }


# ─── SHIFT LOGIC RULES ────────────────────────────────
# Rules that trigger proactive AI advice
# LLM reasons over the trigger + user context
# Returns (triggered: bool, rule_name: str, rule_description: str)

def check_shift_logic(market: Dict[str, float]) -> tuple[bool, str, str]:

    if market["fd_rate"] > 7.0 and market["nifty_pe"] > 22:
        return (
            True,
            "HIGH_FD_RATE_HIGH_VOLATILITY",
            f"FD rates are at {market['fd_rate']}% while NIFTY PE is elevated at {market['nifty_pe']}. "
            f"This suggests shifting equity exposure to high-yield FDs may reduce risk."
        )

    if market["inflation_rate"] > 6.0 and market["gold_1yr_return"] > 10:
        return (
            True,
            "INFLATION_GOLD_HEDGE",
            f"Inflation at {market['inflation_rate']}% with gold returning {market['gold_1yr_return']}% "
            f"over the past year. Gold may be a useful inflation hedge right now."
        )

    if market["repo_rate"] > 6.0 and market["fd_rate"] > 7.0:
        return (
            True,
            "HIGH_REPO_RATE_FD_OPPORTUNITY",
            f"RBI repo rate at {market['repo_rate']}% has pushed FD rates to {market['fd_rate']}%. "
            f"Locking in FDs now before rate cuts may be beneficial."
        )

    return (False, "", "")


# ─── BUILD PORTFOLIO CONTEXT ──────────────────────────
# Formats user assets + market data into clean context
# This is what gets sent to Claude instead of raw account data

def build_context(assets: Dict, market: Dict) -> str:
    gold_value = assets.get("gold_grams", 0) * market["gold_price_per_gram"]
    total_assets = (
        assets.get("liquid_cash", 0) +
        assets.get("mutual_funds", 0) +
        gold_value +
        assets.get("real_estate", 0)
    )
    net_worth = total_assets - assets.get("liabilities", 0)

    return f"""
USER PORTFOLIO SNAPSHOT:
- Liquid Cash: ₹{assets.get('liquid_cash', 0):,.0f}
- Mutual Funds: ₹{assets.get('mutual_funds', 0):,.0f}
- Gold: {assets.get('gold_grams', 0)}g (current value: ₹{gold_value:,.0f} at ₹{market['gold_price_per_gram']}/gram)
- Real Estate: ₹{assets.get('real_estate', 0):,.0f}
- Liabilities: ₹{assets.get('liabilities', 0):,.0f}
- Net Worth: ₹{net_worth:,.0f}
- Total Assets: ₹{total_assets:,.0f}

CURRENT MARKET CONDITIONS:
- RBI Repo Rate: {market['repo_rate']}%
- CPI Inflation: {market['inflation_rate']}%
- NIFTY 50 PE Ratio: {market['nifty_pe']}
- FD Rate (1yr): {market['fd_rate']}%
- Gold 1-Year Return: {market['gold_1yr_return']}%
- NIFTY 1-Year Return: {market['nifty_1yr_return']}%
"""


# ─── SYSTEM PROMPT ────────────────────────────────────

SYSTEM_PROMPT = """You are FinTwin's embedded AI wealth advisor for Indian users.

YOUR RULES:
1. Only give advice based on the portfolio and market data provided to you. Never speculate beyond it.
2. Always mention at least one specific number from the portfolio in your response.
3. Keep responses under 4 sentences. Be direct and actionable.
4. Always explain your reasoning briefly — one sentence on WHY.
5. If the user asks something outside finance, politely redirect them.
6. You are SEBI-aware — never promise guaranteed returns.
7. Format: Lead with the recommendation, then the reasoning, then the key number.

TONE: Confident, clear, professional. Like a smart friend who happens to be a financial advisor."""


# ─── FALLBACK: RULE-BASED SMART RESPONSES ────────────
# Used when API credits are unavailable
# Responses are personalized using actual portfolio numbers

def get_fallback_advice(message: str, assets: Dict, market: Dict) -> str:
    msg = message.lower()
    gold_value = assets.get("gold_grams", 0) * market["gold_price_per_gram"]
    net_worth = (
        assets.get("liquid_cash", 0) +
        assets.get("mutual_funds", 0) +
        gold_value +
        assets.get("real_estate", 0) -
        assets.get("liabilities", 0)
    )
    gold_allocation = (gold_value / (net_worth + 1)) * 100
    cash_allocation = (assets.get("liquid_cash", 0) / (net_worth + 1)) * 100

    if any(word in msg for word in ["gold", "buy gold", "invest gold"]):
        return (
            f"Your current gold holding is {assets.get('gold_grams', 0)}g "
            f"worth ₹{gold_value:,.0f}, which is {gold_allocation:.1f}% of your net worth. "
            f"With inflation at {market['inflation_rate']}% and gold returning "
            f"{market['gold_1yr_return']}% over the past year, gold is performing well as a hedge. "
            f"However, financial advisors recommend keeping gold between 10–15% of your portfolio — "
            f"{'you are within range, a small addition is reasonable.' if gold_allocation < 15 else 'you are above the recommended range, hold off for now.'}"
        )

    if any(word in msg for word in ["fd", "fixed deposit", "fixed"]):
        post_tax_fd = market["fd_rate"] * 0.7  # assuming 30% tax bracket
        return (
            f"Current FD rates are at {market['fd_rate']}%, giving you a post-tax return of "
            f"~{post_tax_fd:.1f}% assuming 30% tax bracket. "
            f"Your home loan (from liabilities of ₹{assets.get('liabilities', 0):,.0f}) likely costs more than this. "
            f"If your loan rate exceeds {post_tax_fd:.1f}%, prepaying the loan gives a better guaranteed return than an FD."
        )

    if any(word in msg for word in ["mutual fund", "equity", "stock", "nifty", "market"]):
        return (
            f"Your mutual fund allocation is ₹{assets.get('mutual_funds', 0):,.0f}. "
            f"NIFTY PE is currently at {market['nifty_pe']}, which is moderately valued. "
            f"NIFTY has returned {market['nifty_1yr_return']}% over the past year. "
            f"With inflation at {market['inflation_rate']}%, equity still offers real returns — "
            f"continuing SIPs makes sense rather than lump-sum at current PE levels."
        )

    if any(word in msg for word in ["cash", "savings", "liquid"]):
        return (
            f"You have ₹{assets.get('liquid_cash', 0):,.0f} in liquid cash, "
            f"which is {cash_allocation:.1f}% of your net worth. "
            f"Ideal liquid emergency fund is 6 months of expenses. "
            f"With FD rates at {market['fd_rate']}%, any cash beyond your emergency fund "
            f"is better deployed in a short-term FD or liquid mutual fund."
        )

    if any(word in msg for word in ["net worth", "portfolio", "total", "wealth"]):
        return (
            f"Your current net worth is ₹{net_worth:,.0f}. "
            f"Breakdown: Cash ₹{assets.get('liquid_cash', 0):,.0f} | "
            f"Mutual Funds ₹{assets.get('mutual_funds', 0):,.0f} | "
            f"Gold ₹{gold_value:,.0f} | "
            f"Real Estate ₹{assets.get('real_estate', 0):,.0f} | "
            f"Liabilities ₹{assets.get('liabilities', 0):,.0f}. "
            f"Your asset-to-liability ratio is {((net_worth + assets.get('liabilities', 0)) / (assets.get('liabilities', 0) + 1)):.1f}x — "
            f"{'healthy.' if net_worth > assets.get('liabilities', 0) * 2 else 'consider reducing liabilities.'}"
        )

    if any(word in msg for word in ["real estate", "property", "house"]):
        property_allocation = (assets.get("real_estate", 0) / (net_worth + 1)) * 100
        return (
            f"Your real estate is valued at ₹{assets.get('real_estate', 0):,.0f}, "
            f"representing {property_allocation:.1f}% of your net worth. "
            f"Real estate is illiquid — ensure your liquid assets cover at least "
            f"12 months of EMIs and expenses before considering another property purchase."
        )

    # Default response
    return (
        f"Based on your net worth of ₹{net_worth:,.0f}, your portfolio looks "
        f"{'well-diversified' if gold_allocation < 20 and cash_allocation < 40 else 'concentrated in a few assets'}. "
        f"Current market conditions: Repo rate {market['repo_rate']}%, "
        f"Inflation {market['inflation_rate']}%, FD rate {market['fd_rate']}%. "
        f"Ask me about gold, FDs, mutual funds, cash, or your overall portfolio for specific advice."
    )


# ─── MAIN: GET AI ADVICE ──────────────────────────────

def get_ai_advice(message: str, assets: Dict) -> Dict[str, Any]:

    market = get_market_context()
    shift_triggered, shift_rule, shift_description = check_shift_logic(market)

    portfolio_context = build_context(assets, market)

    if shift_triggered:
        full_message = (
            f"[SYSTEM ALERT — {shift_rule}]: {shift_description}\n\n"
            f"User question: {message}"
        )
    else:
        full_message = message

    # Try Claude API first — fall back to rule-based if unavailable
    try:
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": f"{portfolio_context}\n\nUser question: {full_message}"
        })

        # Keep only last 6 messages to stay within context limits
        trimmed_history = conversation_history[-6:]

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=trimmed_history
        )
        reply = response.content[0].text

        # Add assistant reply to history
        conversation_history.append({
            "role": "assistant",
            "content": reply
        })

    except Exception:
        reply = get_fallback_advice(message, assets, market)

    return {
        "reply": reply,
        "shift_logic_triggered": shift_triggered,
        "shift_logic_rule": shift_rule if shift_triggered else None
    }