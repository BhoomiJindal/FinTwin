# FinTwin API Reference
## For Frontend Team

Base URL: `http://127.0.0.1:8000`
All POST requests use `Content-Type: application/json`

---

## 1. GET /api/twin
Returns the full digital twin portfolio and market data.
Call this on dashboard load.

**Response:**
```json
{
  "assets": {
    "liquid_cash": 250000,
    "mutual_funds": 180000,
    "gold_grams": 50,
    "real_estate": 4500000,
    "liabilities": 1200000
  },
  "market_data": {
    "gold_price_per_gram": 7200,
    "repo_rate": 6.5,
    "inflation_rate": 5.1,
    "nifty_pe": 22.4,
    "fd_rate": 7.2
  },
  "net_worth": 4090000,
  "gold_value": 360000,
  "total_assets": 5290000
}
```

---

## 2. POST /api/chat
Sends a user question to Brain 01. Returns AI advice with reasoning.

**Request:**
```json
{
  "message": "Should I buy more gold?",
  "assets": {
    "liquid_cash": 250000,
    "mutual_funds": 180000,
    "gold_grams": 50,
    "real_estate": 4500000,
    "liabilities": 1200000
  }
}
```

**Response:**
```json
{
  "reply": "Your gold is 8.8% of net worth...",
  "shift_logic_triggered": true,
  "shift_logic_rule": "HIGH_FD_RATE_HIGH_VOLATILITY",
  "reasoning": [
    {
      "factor": "Gold Allocation",
      "value": "8.8% of portfolio",
      "impact": "Compared against 10-15% recommended range"
    }
  ]
}
```

**UI Notes:**
- Show `reasoning` array as an "Explain AI Logic" expandable panel
- If `shift_logic_triggered` is true, show a gold banner alert above the reply
- Show a loading spinner while waiting — call takes 1-2 seconds

---

## 3. POST /api/chat/reset
Clears conversation memory. Call when user starts a new session.

**Response:** `{"status": "Conversation history cleared"}`

---

## 4. GET /api/shift-logic/status
Returns currently active market alert. Call on dashboard load.

**Response:**
```json
{
  "shift_triggered": true,
  "rule": "HIGH_FD_RATE_HIGH_VOLATILITY",
  "description": "FD rates at 7.2% while NIFTY PE elevated...",
  "market_snapshot": { ... }
}
```

**UI Notes:**
- If `shift_triggered` is true, show a persistent banner on the dashboard
- This is a proactive alert — user doesn't need to ask anything

---

## 5. POST /api/transaction/verify
Runs Brain 02 threat scoring on every transaction attempt.

**Request:**
```json
{
  "amount": 150000,
  "transaction_type": "transfer",
  "recipient": "savings_account",
  "note": "monthly transfer",
  "session_duration_ms": 45000,
  "is_known_device": true
}
```

**Response:**
```json
{
  "threat_score": 21.5,
  "action": "ALLOW",
  "signals": {
    "device_anomaly": 10,
    "amount_anomaly": 20,
    "time_anomaly": 5,
    "velocity_anomaly": 10,
    "urgency_anomaly": 5,
    "recipient_risk": 10
  },
  "triggered_signals": ["All signals within normal range"],
  "risk_summary": "Transaction approved with confidence score 78/100.",
  "cooling_off_seconds": 0,
  "message": null
}
```

**UI Notes for each action:**
- `ALLOW` → Proceed. Reactor stays cyan.
- `CHALLENGE` → Show biometric confirmation modal. Lock UI for `cooling_off_seconds`. Reactor turns gold.
- `BLOCK` → Show block overlay. Reactor turns crimson and alarm animates. Show `triggered_signals` as bullet list.

**How to get `session_duration_ms`:**
```javascript
// Set this when page loads
window.sessionStart = Date.now();

// Send this with every transaction
session_duration_ms: Date.now() - window.sessionStart
```

**How to get `is_known_device`:**
```javascript
// On first login, save fingerprint
const fingerprint = navigator.userAgent + screen.width + screen.height;
localStorage.setItem('deviceFingerprint', fingerprint);

// On each transaction, compare
const current = navigator.userAgent + screen.width + screen.height;
const known = localStorage.getItem('deviceFingerprint');
is_known_device: current === known
```

---

## 6. POST /api/pin/set
Encrypts and stores a PIN using matrix transformation + SHA-256.

**Request:** `{"pin": "1234"}`

**Response:**
```json
{
  "success": true,
  "hash_stored": "2923352b...",
  "cipher_vector": [88, 111, 36]
}
```

**UI Notes:**
- Show `cipher_vector` and `hash_stored` visually — this demonstrates the Matrix Shield to judges
- Label it: "Your PIN was never stored. Only this mathematical transformation was."

---

## 7. POST /api/pin/set-duress
Sets a secret duress PIN for coercion detection.

**Request:** `{"pin": "9999"}`

**Response:** `{"success": true, "message": "Duress PIN set successfully"}`

---

## 8. POST /api/pin/verify
Verifies a PIN. Silently handles duress detection.

**Request:** `{"pin": "1234"}`

**Response:**
```json
{
  "verified": true,
  "duress": false,
  "message": "PIN verified successfully"
}
```

**UI Notes:**
- If `duress: true` is returned — show normal success UI to the coercer
- Internally flag the session and show a hidden alert indicator only visible after the threat passes
- Never show "duress detected" on screen during the coercion

---

## 9. POST /api/property/analyze
Analyzes property value with ZIP-based appreciation projection.

**Request params:** `?property_value=4500000&zip_code=560037&years=5`

**Response:**
```json
{
  "area_name": "Koramangala, Bangalore",
  "appreciation_rate_pct": 12.1,
  "demand_level": "VERY HIGH",
  "projection": {
    "years": 5,
    "projected_value": 7966005,
    "total_gain": 3466005,
    "annual_gain": 693201
  },
  "recommendation": "Strong appreciation zone. Holding recommended."
}
```

---

## 10. GET /api/simulator/compare-all
Counterfactual simulator — shows what ₹X would be worth today
if invested in each asset class from a given year.

**Request params:** `?amount=250000&from_year=2019&to_year=2024`

**Response includes:**
- Year-by-year breakdown for all 5 asset classes
- Best and worst performer
- One-sentence plain English summary

**UI Notes:**
- Show as a bar chart or comparison table
- Highlight the best performer in cyan, worst in crimson
- The summary sentence is your headline stat for the demo

---

## 11. GET /api/audit-trail
Returns full log of all AI decisions, transactions, and security events.

**UI Notes:**
- Show as a scrolling log in the AUDIT tab
- Highlight DURESS_TRIGGERED entries in crimson
- Show CHAT entries in cyan
- Show BLOCK entries in crimson, ALLOW in emerald

---

## Error Handling

All errors return:
```json
{"detail": "Error message here"}
```

HTTP codes used:
- `400` — Bad request (invalid input)
- `401` — Invalid PIN
- `500` — Server error (check uvicorn terminal)