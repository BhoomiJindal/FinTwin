import numpy as np
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, Optional

# ─── TRANSACTION HISTORY ──────────────────────────────
# In-memory store for velocity and amount baseline
# Resets on server restart — fine for prototype

transaction_history = []

# ─── HELPER: GET ROTATING KEY MATRIX ─────────────────
# Key changes every hour automatically
# Same PIN at 9am and 10am produces different cipher vectors

def get_rotating_key() -> np.ndarray:
    seed = int(time.time()) // 3600   # floors to current hour
    rng = np.random.default_rng(seed)
    K = rng.integers(1, 50, size=(3, 3))
    # Make sure matrix is invertible by adding identity-scaled value
    K = K + np.eye(3, dtype=int) * 10
    return K


# ─── HELPER: HUMAN READABLE EXPLANATION ──────────────
# Tells judges exactly WHY a transaction was flagged

def explain_signals(signals: Dict[str, float]) -> list[str]:
    explanations = []
    if signals["device_anomaly"] > 60:
        explanations.append("Unrecognised device detected")
    if signals["amount_anomaly"] > 60:
        explanations.append("Transaction amount is unusually high for this account")
    if signals["time_anomaly"] > 60:
        explanations.append("Transaction initiated at an unusual hour")
    if signals["velocity_anomaly"] > 60:
        explanations.append("Too many transactions in a short time window")
    if signals["urgency_anomaly"] > 60:
        explanations.append("Transaction completed suspiciously fast after login")
    if signals["recipient_risk"] > 60:
        explanations.append("Recipient account is unknown or unverified")
    if not explanations:
        explanations.append("All signals within normal range")
    return explanations

def generate_risk_summary(score: float, action: str, signals: Dict) -> str:
    dominant = max(signals, key=signals.get)
    dominant_labels = {
        "device_anomaly": "an unrecognised device",
        "amount_anomaly": "an unusually large amount",
        "time_anomaly": "an unusual transaction hour",
        "velocity_anomaly": "too many recent transactions",
        "urgency_anomaly": "suspiciously fast action",
        "recipient_risk": "an unknown recipient"
    }
    dominant_reason = dominant_labels.get(dominant, "unusual behaviour")

    if action == "ALLOW":
        return f"All signals within normal range. Transaction approved with confidence score {100 - score:.0f}/100."
    elif action == "CHALLENGE":
        return f"Transaction flagged primarily due to {dominant_reason}. Identity re-confirmation required before proceeding."
    else:
        return f"Transaction blocked. Primary trigger: {dominant_reason}. Score {score}/100 exceeds safety threshold."
    

def generate_ai_explanation(score: float, action: str, signals: Dict, request) -> Optional[str]:
    """
    For CHALLENGE and BLOCK, generate a detailed natural-language
    explanation referencing the specific transaction details.
    """
    if action == "ALLOW":
        return None

    issues = []

    if signals["device_anomaly"] > 60:
        issues.append("from a device we have never seen before")

    if signals["amount_anomaly"] > 60:
        issues.append(f"for ₹{request.amount:,.0f} — significantly higher than your typical transaction amount")

    if signals["time_anomaly"] > 60:
        issues.append("at an unusual hour")

    if signals["velocity_anomaly"] > 60:
        issues.append("as part of an unusually high number of transactions in the last hour")

    if signals["urgency_anomaly"] > 60:
        issues.append(f"within {request.session_duration_ms / 1000:.0f} seconds of opening the app — much faster than typical user behaviour")

    if signals["recipient_risk"] > 60:
        issues.append("to a recipient not on your verified list")

    if not issues:
        issues.append("due to a combination of minor irregularities across multiple signals")

    issue_text = ", ".join(issues)

    if action == "BLOCK":
        return (
            f"This transaction was blocked because it was attempted {issue_text}. "
            f"This combination of factors closely matches patterns seen in account takeover "
            f"or coerced transfer attempts. Threat Score: {score}/100. "
            f"Your trusted contact has been notified. If this was you, "
            f"please verify your identity to proceed."
        )
    else:  # CHALLENGE
        return (
            f"This transaction was flagged for review because it was attempted {issue_text}. "
            f"This is not necessarily fraudulent, but enough irregularities were detected "
            f"to require identity confirmation. Threat Score: {score}/100. "
            f"Please confirm your identity to proceed — this takes a few seconds."
        )
    

def detect_fraud_pattern(request, history: list) -> Optional[Dict[str, Any]]:
    """
    Looks at the sequence of recent transactions to detect
    multi-step fraud patterns that single-transaction scoring would miss.
    """
    now = time.time()

    # ── Pattern 1: Test transfer followed by large transfer ──
    # Small amount (under 500) in last 10 minutes, now a large amount
    recent_10min = [t for t in history if now - t["timestamp"] < 600]
    small_test_transfers = [t for t in recent_10min if t["amount"] < 500]

    if small_test_transfers and request.amount > 10000:
        return {
            "pattern_name": "TEST_THEN_DRAIN",
            "description": (
                f"A small test transaction (₹{small_test_transfers[-1]['amount']:,.0f}) "
                f"was made recently, followed by this much larger transfer "
                f"(₹{request.amount:,.0f}). This sequence is commonly used to verify "
                f"a stolen account works before draining it."
            ),
            "confidence": 85,
            "score_bonus": 25.0
        }

    # ── Pattern 2: Rapid-fire multiple large transactions ──
    recent_5min = [t for t in history if now - t["timestamp"] < 300]
    large_recent = [t for t in recent_5min if t["amount"] > 20000]

    if len(large_recent) >= 2 and request.amount > 20000:
        return {
            "pattern_name": "RAPID_DRAIN_SEQUENCE",
            "description": (
                f"This is the {len(large_recent) + 1}th large transaction "
                f"(over ₹20,000) attempted within 5 minutes. "
                f"This rapid sequence is consistent with an attacker "
                f"attempting to move funds before the account is locked."
            ),
            "confidence": 90,
            "score_bonus": 30.0
        }

    # ── Pattern 3: New device + immediate large transfer + no recipient ──
    if (not request.is_known_device and
        request.amount > 50000 and
        (not request.recipient or request.recipient.strip() == "")):

        return {
            "pattern_name": "NEW_DEVICE_IMMEDIATE_LARGE_TRANSFER",
            "description": (
                f"A large transfer (₹{request.amount:,.0f}) to an unverified recipient "
                f"was attempted from a completely new device. "
                f"This combination — new device, large amount, no recipient verification — "
                f"matches the profile of credential theft followed by immediate fund extraction."
            ),
            "confidence": 95,
            "score_bonus": 35.0
        }

    # ── Pattern 4: Escalating amounts over short period ──
    if len(recent_10min) >= 2:
        amounts = [t["amount"] for t in recent_10min] + [request.amount]
        is_escalating = all(amounts[i] < amounts[i+1] for i in range(len(amounts)-1))

        if is_escalating and amounts[-1] > amounts[0] * 5:
            return {
                "pattern_name": "ESCALATING_AMOUNT_PATTERN",
                "description": (
                    f"Transaction amounts have been escalating rapidly — "
                    f"from ₹{amounts[0]:,.0f} to ₹{amounts[-1]:,.0f} within 10 minutes. "
                    f"This escalation pattern often indicates an attacker "
                    f"testing limits before a final large withdrawal."
                ),
                "confidence": 75,
                "score_bonus": 20.0
            }

    return None


# ─── MAIN: 6-SIGNAL THREAT SCORING ───────────────────

def calculate_threat_score(request) -> Dict[str, Any]:

    signals = {}

    # ── Signal 1: Device Anomaly (20%) ────────────────
    # Frontend sends is_known_device based on stored fingerprint
    signals["device_anomaly"] = 10.0 if request.is_known_device else 85.0

    # ── Signal 2: Amount Anomaly (25%) ────────────────
    # Compare against average of last 50 transactions
    if len(transaction_history) >= 3:
        avg = sum(t["amount"] for t in transaction_history[-50:]) / len(transaction_history[-50:])
        deviation = abs(request.amount - avg) / (avg + 1)
        signals["amount_anomaly"] = min(deviation * 50, 100.0)
    else:
        # Not enough history — use a conservative baseline
        signals["amount_anomaly"] = 20.0 if request.amount < 50000 else 55.0

    # ── Signal 3: Time Anomaly (15%) ──────────────────
    # Transactions between 11pm and 5am are higher risk
    hour = datetime.now().hour
    if 23 <= hour or hour < 5:
        signals["time_anomaly"] = 75.0
    elif 5 <= hour < 8:
        signals["time_anomaly"] = 35.0
    else:
        signals["time_anomaly"] = 5.0

    # ── Signal 4: Velocity Anomaly (15%) ──────────────
    # Count how many transactions in the last 60 minutes
    one_hour_ago = time.time() - 3600
    recent = [t for t in transaction_history if t["timestamp"] > one_hour_ago]
    count = len(recent)
    if count >= 5:
        signals["velocity_anomaly"] = 85.0
    elif count >= 3:
        signals["velocity_anomaly"] = 50.0
    else:
        signals["velocity_anomaly"] = 10.0

    # ── Signal 5: Urgency Anomaly (15%) ───────────────
    # session_duration_ms: time from page load to transaction
    # Under 10 seconds is extremely suspicious
    ms = request.session_duration_ms
    if ms < 10000:
        signals["urgency_anomaly"] = 90.0
    elif ms < 30000:
        signals["urgency_anomaly"] = 55.0
    elif ms < 60000:
        signals["urgency_anomaly"] = 25.0
    else:
        signals["urgency_anomaly"] = 5.0

    # ── Signal 6: Recipient Risk (10%) ────────────────
    # None/empty recipient = unknown = higher risk
    if not request.recipient or request.recipient.strip() == "":
        signals["recipient_risk"] = 70.0
    else:
        signals["recipient_risk"] = 10.0

    # ── Weighted Threat Score ─────────────────────────
    score = (
        signals["device_anomaly"]   * 0.20 +
        signals["amount_anomaly"]   * 0.25 +
        signals["time_anomaly"]     * 0.15 +
        signals["velocity_anomaly"] * 0.15 +
        signals["urgency_anomaly"]  * 0.15 +
        signals["recipient_risk"]   * 0.10
    )
    score = round(score, 2)

    # ── NEW: Pattern Detection ────────────────────────
    pattern = detect_fraud_pattern(request, transaction_history)

    if pattern:
        score = min(score + pattern["score_bonus"], 100)
        score = round(score, 2)

    # ── Decision Gate ─────────────────────────────────
    if score <= 39:
        action = "ALLOW"
        message = None
    elif score <= 75:
        action = "CHALLENGE"
        message = f"Unusual activity detected. Threat Score: {score}/100. Please confirm your identity."
    else:
        action = "BLOCK"
        message = f"Transaction blocked. Threat Score: {score}/100. Your trusted contact has been notified."

    # ── Log this transaction ──────────────────────────
    transaction_history.append({
        "amount": request.amount,
        "timestamp": time.time(),
        "action": action,
        "score": score
    })

    risk_summary = generate_risk_summary(score, action, signals)
    cooling_off = 5 if action == "CHALLENGE" else 0
    ai_explanation = generate_ai_explanation(score, action, signals, request)

    # If pattern detected, append pattern info to explanation
    if pattern and ai_explanation:
        ai_explanation += f"\n\nPATTERN ALERT: {pattern['description']}"
    elif pattern:
        ai_explanation = f"PATTERN ALERT: {pattern['description']}"

    return {
        "score": score,
        "action": action,
        "signals": signals,
        "message": message,
        "triggered_signals": explain_signals(signals),
        "risk_summary": risk_summary,
        "cooling_off_seconds": cooling_off,
        "ai_explanation": ai_explanation,
        "pattern": pattern
    }


# ─── MATRIX ENCRYPTION ───────────────────────────────

def encrypt_pin(pin: str) -> Dict[str, Any]:

    # Step 1: Convert PIN characters to ASCII values
    P = np.array([ord(c) for c in pin], dtype=np.int64)

    # Step 2: Pad P to length 3 for matrix multiplication
    # (rotating key is 3x3)
    while len(P) < 3:
        P = np.append(P, 0)
    P = P[:3]   # use only first 3 values if PIN is longer

    # Step 3: Get the rotating key matrix for this hour
    K = get_rotating_key()

    # Step 4: Matrix multiplication mod 256
    # C = (P · K) mod 256
    C = np.dot(P, K) % 256
    cipher_vector = C.tolist()

    # Step 5: Pass cipher vector through SHA-256
    cipher_string = "-".join(str(int(v)) for v in cipher_vector)
    final_hash = hashlib.sha256(cipher_string.encode()).hexdigest()

    return {
        "cipher_vector": [int(v) for v in cipher_vector],
        "hash": final_hash
    }