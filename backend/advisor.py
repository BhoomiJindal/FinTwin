import os
import anthropic
from dotenv import load_dotenv
from typing import Dict, Any
from sentiment import get_market_sentiment

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


def extract_reasoning(message: str, assets: Dict, market: Dict) -> list:
    msg = message.lower()
    gold_value = assets.get("gold_grams", 0) * market["gold_price_per_gram"]
    net_worth = (
        assets.get("liquid_cash", 0) +
        assets.get("mutual_funds", 0) +
        gold_value +
        assets.get("real_estate", 0) -
        assets.get("liabilities", 0)
    )
    gold_pct = round((gold_value / (net_worth + 1)) * 100, 1)
    cash_pct = round((assets.get("liquid_cash", 0) / (net_worth + 1)) * 100, 1)
    post_tax_fd = round(market["fd_rate"] * 0.7, 2)

    reasoning = []

    # Always include net worth context
    reasoning.append({
        "factor": "Net Worth",
        "value": f"₹{net_worth:,.0f}",
        "impact": "Base reference for all allocation advice"
    })

    if any(w in msg for w in ["gold"]):
        reasoning.append({
            "factor": "Gold Allocation",
            "value": f"{gold_pct}% of portfolio",
            "impact": "Compared against 10-15% recommended range"
        })
        reasoning.append({
            "factor": "Gold 1yr Return",
            "value": f"{market['gold_1yr_return']}%",
            "impact": "Assessed against inflation rate as hedge effectiveness"
        })
        reasoning.append({
            "factor": "Inflation Rate",
            "value": f"{market['inflation_rate']}%",
            "impact": "Higher inflation increases gold hedge value"
        })

    if any(w in msg for w in ["fd", "fixed deposit", "fixed"]):
        reasoning.append({
            "factor": "FD Rate",
            "value": f"{market['fd_rate']}%",
            "impact": "Gross return before tax"
        })
        reasoning.append({
            "factor": "Post-Tax FD Return",
            "value": f"{post_tax_fd}%",
            "impact": "Effective return assuming 30% tax bracket"
        })
        reasoning.append({
            "factor": "Liabilities",
            "value": f"₹{assets.get('liabilities', 0):,.0f}",
            "impact": "Loan cost compared against FD return to find better option"
        })

    if any(w in msg for w in ["mutual fund", "equity", "stock", "nifty"]):
        reasoning.append({
            "factor": "NIFTY PE Ratio",
            "value": str(market["nifty_pe"]),
            "impact": "Above 22 signals caution for lump-sum investments"
        })
        reasoning.append({
            "factor": "NIFTY 1yr Return",
            "value": f"{market['nifty_1yr_return']}%",
            "impact": "Recent market performance context"
        })
        reasoning.append({
            "factor": "Mutual Fund Holdings",
            "value": f"₹{assets.get('mutual_funds', 0):,.0f}",
            "impact": "Current equity exposure assessed"
        })

    if any(w in msg for w in ["cash", "savings", "liquid"]):
        reasoning.append({
            "factor": "Liquid Cash",
            "value": f"₹{assets.get('liquid_cash', 0):,.0f}",
            "impact": f"{cash_pct}% of net worth — checked against 6-month emergency fund rule"
        })
        reasoning.append({
            "factor": "FD Rate",
            "value": f"{market['fd_rate']}%",
            "impact": "Excess cash beyond emergency fund earns this if deployed"
        })

    return reasoning


def calculate_confidence(assets: Dict, archetype: str = None) -> Dict[str, Any]:
    """
    Confidence is based on how complete the user's data is.
    More complete data = higher confidence in the advice.
    """
    fields = ["liquid_cash", "mutual_funds", "gold_grams", "real_estate", "liabilities"]
    filled = sum(1 for f in fields if assets.get(f, 0) > 0)
    total = len(fields)

    base_confidence = int((filled / total) * 70)  # max 70 from data completeness

    # Archetype adds confidence — personalization improves advice quality
    archetype_bonus = 20 if archetype else 0

    # Always have market data, so base 10 points guaranteed
    market_bonus = 10

    confidence = min(base_confidence + archetype_bonus + market_bonus, 100)

    # Generate note if confidence is not full
    note = None
    if confidence < 100:
        missing = [f.replace("_", " ").title() for f in fields if assets.get(f, 0) == 0]
        if missing and not archetype:
            note = f"Add {', '.join(missing)} and complete your profile for more precise advice."
        elif missing:
            note = f"Add {', '.join(missing)} for more precise advice."
        elif not archetype:
            note = "Complete your profile for more personalized advice."

    return {"confidence": confidence, "note": note}



def detect_language(message: str) -> str:
    """
    Detects if the message is in Hindi (Devanagari script)
    or contains common Hindi romanized keywords.
    Returns "hi" or "en".
    """
    # Check for Devanagari Unicode range
    devanagari_chars = sum(1 for c in message if '\u0900' <= c <= '\u097F')
    if devanagari_chars > 2:
        return "hi"

    # Check for common romanized Hindi financial keywords
    hindi_keywords = [
        "mera", "meri", "kitna", "paisa", "paise", "rupaye", "sona",
        "nivesh", "bachat", "loan", "karj", "sampatti", "kya", "kaise",
        "chahiye", "batao", "bolo", "hindi", "हिंदी"
    ]
    msg_lower = message.lower()
    if sum(1 for kw in hindi_keywords if kw in msg_lower) >= 2:
        return "hi"

    return "en"


HINDI_SYSTEM_PROMPT = """Aap FinTwin ke embedded AI wealth advisor hain Indian users ke liye.

AAPKE NIYAM:
1. Sirf us portfolio aur market data ke aadhar par salah dein jo aapko diya gaya hai.
2. Hamesha apne jawab mein portfolio se kam se kam ek specific number zaroor mention karein.
3. Jawab 4 sentences se zyada nahi hona chahiye. Direct aur actionable rahein.
4. Apna reasoning briefly explain karein — ek sentence mein KYUN.
5. Agar user finance se bahar ki baat kare, politely redirect karein.
6. Aap SEBI-aware hain — guaranteed returns ka vaada kabhi mat karein.

TONE: Confident, clear, professional. Jaise ek samajhdar dost jo financial advisor bhi ho.
Hinglish mein jawab dein (Hindi + simple English mix) — pure Hindi avoid karein."""


def get_hindi_fallback(message: str, assets: Dict, market: Dict) -> str:
    msg = message.lower()
    gold_value = assets.get("gold_grams", 0) * market["gold_price_per_gram"]
    net_worth = (
        assets.get("liquid_cash", 0) +
        assets.get("mutual_funds", 0) +
        gold_value +
        assets.get("real_estate", 0) -
        assets.get("liabilities", 0)
    )
    gold_pct = round((gold_value / (net_worth + 1)) * 100, 1)

    if any(w in msg for w in ["sona", "gold", "सोना"]):
        return (
            f"Aapke paas abhi {assets.get('gold_grams', 0)}g sona hai "
            f"jiska value ₹{gold_value:,.0f} hai — yeh aapki net worth ka {gold_pct}% hai. "
            f"Inflation {market['inflation_rate']}% par hai aur sone ne last year "
            f"{market['gold_1yr_return']}% return diya. "
            f"{'Thoda aur sona lena reasonable hai kyunki aap 10-15% target se neeche hain.' if gold_pct < 10 else 'Aap already recommended range mein hain — aur zyada lene ki zaroorat nahi.'}"
        )

    if any(w in msg for w in ["mutual fund", "share", "equity", "nifty", "nivesh"]):
        return (
            f"Aapka mutual fund allocation ₹{assets.get('mutual_funds', 0):,.0f} hai. "
            f"NIFTY PE abhi {market['nifty_pe']} par hai — moderate valuation. "
            f"Inflation {market['inflation_rate']}% ke saath, equity abhi bhi real returns de raha hai. "
            f"Lump-sum se bachein — SIP continue karna zyada samajhdari hai."
        )

    if any(w in msg for w in ["net worth", "kitna", "total", "sampatti", "paisa"]):
        return (
            f"Aapki abhi ki net worth ₹{net_worth:,.0f} hai. "
            f"Cash ₹{assets.get('liquid_cash', 0):,.0f} | "
            f"Mutual Funds ₹{assets.get('mutual_funds', 0):,.0f} | "
            f"Sona ₹{gold_value:,.0f} | "
            f"Property ₹{assets.get('real_estate', 0):,.0f} | "
            f"Karj ₹{assets.get('liabilities', 0):,.0f}. "
            f"Repo rate {market['repo_rate']}% aur inflation {market['inflation_rate']}% hai."
        )

    if any(w in msg for w in ["fd", "fixed deposit", "bachat"]):
        post_tax = round(market["fd_rate"] * 0.7, 2)
        return (
            f"Abhi FD rate {market['fd_rate']}% hai — tax ke baad effective return {post_tax}% hoga. "
            f"Agar aapka home loan rate {post_tax}% se zyada hai, "
            f"toh FD ki jagah loan prepay karna zyada faydemand hai. "
            f"₹{assets.get('liabilities', 0):,.0f} liabilities ko dhyan mein rakhein."
        )

    return (
        f"Aapki net worth ₹{net_worth:,.0f} hai. "
        f"Market conditions: Repo rate {market['repo_rate']}%, "
        f"Inflation {market['inflation_rate']}%, FD rate {market['fd_rate']}%. "
        f"Sona, FD, mutual funds, ya apni overall portfolio ke baare mein poochh sakte hain."
    )

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

    # Get live sentiment
    sentiment = get_market_sentiment()

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

MARKET SENTIMENT (from recent headlines):
- Overall Mood: {sentiment['overall_mood']} (Score: {sentiment['overall_score']}/100)
- {sentiment['mood_description']}
- Sentiment Advisory: {sentiment['advisory']}
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

def get_fallback_advice(message: str, assets: Dict, market: Dict, archetype: str = None) -> str:
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
    mutual_fund_allocation = (assets.get("mutual_funds", 0) / (net_worth + 1)) * 100
    post_tax_fd = round(market["fd_rate"] * 0.7, 2)

    # ── Archetype-aware equity advice ─────────────────
    if any(word in msg for word in ["mutual fund", "equity", "stock", "nifty"]):

        if archetype == "accumulator":
            return (
                f"Your mutual fund allocation is ₹{assets.get('mutual_funds', 0):,.0f} "
                f"({mutual_fund_allocation:.1f}% of net worth). "
                f"As an Accumulator with a long horizon, your ideal equity allocation is 50%. "
                f"You are currently {'under' if mutual_fund_allocation < 50 else 'at or above'} that target. "
                f"At NIFTY PE of {market['nifty_pe']}, avoid lump-sum — "
                f"increase your SIP amount by ₹{int(assets.get('liquid_cash', 0) * 0.05):,} monthly to build position gradually."
            )

        elif archetype == "preserver":
            return (
                f"Your mutual fund allocation is ₹{assets.get('mutual_funds', 0):,.0f} "
                f"({mutual_fund_allocation:.1f}% of net worth). "
                f"As a Preserver, your recommended equity exposure is just 10% — "
                f"you are {'over-exposed' if mutual_fund_allocation > 10 else 'within range'}. "
                f"At this stage, consider shifting equity gains to Senior Citizen FDs at {market['fd_rate']}% "
                f"or SCSS for stable, protected income. "
                f"Do not increase equity exposure further."
            )

        elif archetype == "protector":
            return (
                f"Your mutual fund allocation is ₹{assets.get('mutual_funds', 0):,.0f} "
                f"({mutual_fund_allocation:.1f}% of net worth). "
                f"As a Protector, keep equity at 20% of your portfolio. "
                f"Before adding more equity, confirm your emergency fund covers "
                f"6 months of expenses and your family has adequate term insurance. "
                f"If both are in place, a small SIP increase is reasonable at current PE of {market['nifty_pe']}."
            )

        elif archetype == "optimizer":
            return (
                f"Your mutual fund allocation is ₹{assets.get('mutual_funds', 0):,.0f} "
                f"({mutual_fund_allocation:.1f}% of net worth). "
                f"As an Optimizer, check if your equity funds are ELSS — "
                f"if not, consider switching a portion to ELSS to claim 80C benefits. "
                f"Post-tax FD return is only {post_tax_fd}% vs NIFTY's {market['nifty_1yr_return']}% last year. "
                f"At PE {market['nifty_pe']}, SIP is preferred over lump-sum."
            )

        else:
            # No archetype set — generic response
            return (
                f"Your mutual fund allocation is ₹{assets.get('mutual_funds', 0):,.0f}. "
                f"NIFTY PE is currently at {market['nifty_pe']}, which is moderately valued. "
                f"NIFTY has returned {market['nifty_1yr_return']}% over the past year. "
                f"With inflation at {market['inflation_rate']}%, equity still offers real returns — "
                f"continuing SIPs makes sense rather than lump-sum at current PE levels."
            )

    # ── Gold advice ────────────────────────────────────
    if any(word in msg for word in ["gold", "buy gold", "invest gold"]):

        if archetype == "accumulator":
            return (
                f"Your gold is {gold_allocation:.1f}% of net worth (₹{gold_value:,.0f}). "
                f"As an Accumulator, keep gold at 10% — it is a hedge, not a growth engine. "
                f"Gold returned {market['gold_1yr_return']}% last year but equity historically "
                f"outperforms long-term. "
                f"{'You are under the 10% target — a small addition is fine.' if gold_allocation < 10 else 'You are at target — no need to add more.'}"
            )

        elif archetype == "preserver":
            return (
                f"Your gold is {gold_allocation:.1f}% of net worth (₹{gold_value:,.0f}). "
                f"As a Preserver, gold is an important inflation hedge — target is 20%. "
                f"With inflation at {market['inflation_rate']}% and gold returning "
                f"{market['gold_1yr_return']}% last year, "
                f"{'increasing your gold allocation makes sense.' if gold_allocation < 20 else 'you are at or above target — hold.'}"
            )

        else:
            return (
                f"Your current gold holding is {assets.get('gold_grams', 0)}g "
                f"worth ₹{gold_value:,.0f}, which is {gold_allocation:.1f}% of your net worth. "
                f"With inflation at {market['inflation_rate']}% and gold returning "
                f"{market['gold_1yr_return']}% over the past year, gold is performing well as a hedge. "
                f"Financial advisors recommend keeping gold between 10-15% of your portfolio — "
                f"{'you are within range, a small addition is reasonable.' if gold_allocation < 15 else 'you are above the recommended range, hold off for now.'}"
            )

    # ── FD advice ──────────────────────────────────────
    if any(word in msg for word in ["fd", "fixed deposit", "fixed"]):

        if archetype in ["preserver", "protector"]:
            return (
                f"FD rates are at {market['fd_rate']}% — attractive for your profile. "
                f"Post-tax return is {post_tax_fd}% (at 30% bracket). "
                f"As a {'Preserver' if archetype == 'preserver' else 'Protector'}, "
                f"FDs form a core part of your recommended allocation. "
                f"Consider laddering FDs across 1, 2, and 3 year tenures "
                f"to balance liquidity and rate lock-in."
            )

        elif archetype == "optimizer":
            return (
                f"FD rates at {market['fd_rate']}% give post-tax return of {post_tax_fd}%. "
                f"As an Optimizer, compare this against your home loan rate from "
                f"liabilities of ₹{assets.get('liabilities', 0):,.0f}. "
                f"If loan rate exceeds {post_tax_fd}%, prepaying beats FD mathematically. "
                f"Also consider debt mutual funds — more tax-efficient for your bracket."
            )

        else:
            return (
                f"Current FD rates are at {market['fd_rate']}%, giving post-tax return of "
                f"~{post_tax_fd}% at 30% tax bracket. "
                f"Your liabilities are ₹{assets.get('liabilities', 0):,.0f}. "
                f"If your loan rate exceeds {post_tax_fd}%, prepaying the loan "
                f"gives a better guaranteed return than an FD."
            )

    # ── Net worth / portfolio ──────────────────────────
    if any(word in msg for word in ["net worth", "portfolio", "total", "wealth"]):
        return (
            f"Your current net worth is ₹{net_worth:,.0f}. "
            f"Breakdown: Cash ₹{assets.get('liquid_cash', 0):,.0f} | "
            f"Mutual Funds ₹{assets.get('mutual_funds', 0):,.0f} | "
            f"Gold ₹{gold_value:,.0f} | "
            f"Real Estate ₹{assets.get('real_estate', 0):,.0f} | "
            f"Liabilities ₹{assets.get('liabilities', 0):,.0f}. "
            f"{'As a ' + archetype.title() + ', focus on ' if archetype else ''}"
            f"{'growing equity exposure.' if archetype == 'accumulator' else 'protecting capital and generating income.' if archetype == 'preserver' else 'optimising post-tax returns.' if archetype == 'optimizer' else 'maintaining adequate insurance and emergency fund.' if archetype == 'protector' else 'balancing growth and safety.'}"
        )

    # ── Cash advice ────────────────────────────────────
    if any(word in msg for word in ["cash", "savings", "liquid"]):
        return (
            f"You have ₹{assets.get('liquid_cash', 0):,.0f} in liquid cash "
            f"({cash_allocation:.1f}% of net worth). "
            f"Ideal emergency fund is 6 months of expenses. "
            f"{'As an Accumulator, keep it lean — excess cash beyond emergency fund should go to SIPs.' if archetype == 'accumulator' else 'As a Preserver, keep 25% liquid for withdrawal needs.' if archetype == 'preserver' else 'With FD rates at ' + str(market['fd_rate']) + '%, deploy excess cash into short-term FDs.'}"
        )

    # ── Default ────────────────────────────────────────
    return (
        f"Based on your net worth of ₹{net_worth:,.0f} "
        f"{'and your profile as ' + archetype.title() + ', ' if archetype else ', '}"
        f"current market conditions are: Repo rate {market['repo_rate']}%, "
        f"Inflation {market['inflation_rate']}%, FD rate {market['fd_rate']}%. "
        f"Ask me about gold, FDs, mutual funds, cash, or your overall portfolio for specific advice."
    )


# ─── MAIN: GET AI ADVICE ──────────────────────────────

def get_ai_advice(message: str, assets: Dict, archetype: str = None, language: str = "en") -> Dict[str, Any]:

    market = get_market_context()
    shift_triggered, shift_rule, shift_description = check_shift_logic(market)
    portfolio_context = build_context(assets, market)

    # Auto-detect language if not specified
    detected_language = detect_language(message)
    final_language = detected_language if detected_language == "hi" else language

    # Choose system prompt based on language
    if final_language == "hi":
        personalized_system = HINDI_SYSTEM_PROMPT
    else:
        personalized_system = SYSTEM_PROMPT
        if archetype:
            from profiler import get_archetype_context, Archetype
            try:
                archetype_context = get_archetype_context(Archetype(archetype))
                personalized_system = SYSTEM_PROMPT + archetype_context
            except Exception:
                pass

    if shift_triggered:
        full_message = (
            f"[SYSTEM ALERT — {shift_rule}]: {shift_description}\n\n"
            f"User question: {message}"
        )
    else:
        full_message = message

    try:
        conversation_history.append({
            "role": "user",
            "content": f"{portfolio_context}\n\nUser question: {full_message}"
        })

        trimmed_history = conversation_history[-6:]

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=personalized_system,
            messages=trimmed_history
        )
        reply = response.content[0].text

        conversation_history.append({
            "role": "assistant",
            "content": reply
        })

    except Exception:
        if final_language == "hi":
            reply = get_hindi_fallback(message, assets, market)
        else:
            reply = get_fallback_advice(message, assets, market, archetype)

    reasoning = extract_reasoning(message, assets, market)
    confidence_data = calculate_confidence(assets, archetype)

    return {
        "reply": reply,
        "shift_logic_triggered": shift_triggered,
        "shift_logic_rule": shift_rule if shift_triggered else None,
        "reasoning": reasoning,
        "confidence": confidence_data["confidence"],
        "confidence_note": confidence_data["note"],
        "language_detected": final_language
    }