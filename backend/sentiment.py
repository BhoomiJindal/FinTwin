from typing import Dict, Any, List

# ─── MOCK HEADLINES ───────────────────────────────────
# In production: replace with live RSS feed from
# Economic Times, Mint, or Moneycontrol
# For demo: realistic recent-style headlines

MOCK_HEADLINES = [
    {"text": "RBI holds repo rate steady amid inflation concerns", "date": "2025-06-10"},
    {"text": "NIFTY 50 hits all-time high on strong FII inflows", "date": "2025-06-09"},
    {"text": "Gold prices surge as global uncertainty rises", "date": "2025-06-09"},
    {"text": "Inflation eases to 4.8% in May, below RBI target", "date": "2025-06-08"},
    {"text": "FD rates expected to fall after next RBI meeting", "date": "2025-06-08"},
    {"text": "Real estate demand slows in metro cities", "date": "2025-06-07"},
    {"text": "Mutual fund SIP inflows hit record high in May", "date": "2025-06-07"},
    {"text": "Rupee weakens against dollar on global cues", "date": "2025-06-06"},
]

# ─── SENTIMENT KEYWORDS ───────────────────────────────

POSITIVE_KEYWORDS = [
    "high", "rise", "surge", "record", "strong", "growth",
    "rally", "gains", "bull", "inflows", "eases", "recovery",
    "boom", "profit", "positive", "upgrade"
]

NEGATIVE_KEYWORDS = [
    "fall", "drop", "decline", "concern", "risk", "slow",
    "weak", "uncertainty", "crash", "sell", "inflation",
    "loss", "bearish", "outflows", "cut", "fears", "slump"
]

ASSET_KEYWORDS = {
    "gold": ["gold", "precious metals", "safe haven"],
    "equity": ["nifty", "sensex", "stock", "equity", "market", "fii", "mutual fund", "sip"],
    "real_estate": ["real estate", "property", "housing", "realty"],
    "fd_debt": ["fd", "fixed deposit", "repo rate", "rbi", "interest rate", "bond"],
    "cash": ["rupee", "currency", "inflation", "cpi"]
}


def analyze_headline_sentiment(headline: str) -> Dict[str, Any]:
    text = headline.lower()

    positive_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    negative_hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)

    if positive_hits > negative_hits:
        sentiment = "POSITIVE"
        score = min(positive_hits * 20, 100)
    elif negative_hits > positive_hits:
        sentiment = "NEGATIVE"
        score = -min(negative_hits * 20, 100)
    else:
        sentiment = "NEUTRAL"
        score = 0

    # Detect which asset class this headline affects
    affected_asset = "general"
    for asset, keywords in ASSET_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            affected_asset = asset
            break

    return {
        "headline": headline,
        "sentiment": sentiment,
        "score": score,
        "affected_asset": affected_asset
    }


def get_market_sentiment() -> Dict[str, Any]:
    results = [analyze_headline_sentiment(h["text"]) for h in MOCK_HEADLINES]

    # Overall sentiment score: average of all headline scores
    total_score = sum(r["score"] for r in results)
    avg_score = round(total_score / len(results), 1) if results else 0

    # Sentiment by asset class
    asset_sentiment = {}
    for asset in ASSET_KEYWORDS:
        asset_headlines = [r for r in results if r["affected_asset"] == asset]
        if asset_headlines:
            asset_avg = sum(r["score"] for r in asset_headlines) / len(asset_headlines)
            asset_sentiment[asset] = {
                "score": round(asset_avg, 1),
                "sentiment": "POSITIVE" if asset_avg > 10 else "NEGATIVE" if asset_avg < -10 else "NEUTRAL",
                "headline_count": len(asset_headlines)
            }

    # Overall market mood
    if avg_score > 15:
        overall_mood = "BULLISH"
        mood_description = "Market sentiment is broadly positive. Risk appetite is elevated."
    elif avg_score < -15:
        overall_mood = "BEARISH"
        mood_description = "Market sentiment is broadly negative. Caution is warranted."
    else:
        overall_mood = "NEUTRAL"
        mood_description = "Market sentiment is mixed. No strong directional signal."

    # Generate sentiment-based advisory note
    advisory = _generate_sentiment_advisory(asset_sentiment, overall_mood)

    return {
        "overall_score": avg_score,
        "overall_mood": overall_mood,
        "mood_description": mood_description,
        "asset_sentiment": asset_sentiment,
        "headlines_analyzed": len(results),
        "advisory": advisory,
        "top_headlines": [r["headline"] for r in results[:3]]
    }


def _generate_sentiment_advisory(asset_sentiment: Dict, mood: str) -> str:
    notes = []

    gold = asset_sentiment.get("gold", {})
    equity = asset_sentiment.get("equity", {})
    fd = asset_sentiment.get("fd_debt", {})

    if gold.get("sentiment") == "POSITIVE":
        notes.append("Gold sentiment is positive — current headlines support holding or adding gold as a hedge.")

    if equity.get("sentiment") == "POSITIVE":
        notes.append("Equity sentiment is positive — market mood supports continued SIP investments.")
    elif equity.get("sentiment") == "NEGATIVE":
        notes.append("Equity sentiment is negative — consider pausing lump-sum equity investments until sentiment improves.")

    if fd.get("sentiment") == "NEGATIVE":
        notes.append("Interest rate sentiment suggests FD rates may fall — locking in FDs now could be beneficial.")

    if not notes:
        notes.append("No strong asset-specific sentiment signals detected. Maintain current allocation.")

    return " ".join(notes)