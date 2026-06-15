# FinTwin API Reference
## For Frontend Team
**Base URL:** `http://127.0.0.1:8000`
All POST/PUT requests use `Content-Type: application/json`

---

## Quick Reference — All Endpoints

| Method | Endpoint | What It Does |
|---|---|---|
| GET | /api/twin | Full portfolio + market data |
| GET | /api/ai/summary | One-paragraph financial state summary |
| POST | /api/chat | Ask Brain 01 a financial question |
| POST | /api/chat/reset | Clear conversation memory |
| GET | /api/shift-logic/status | Active market alerts |
| GET | /api/market/sentiment | Headline sentiment analysis |
| POST | /api/profile/classify | Set user personality archetype |
| GET | /api/profile/current | Get current archetype |
| POST | /api/transaction/verify | Brain 02 threat scoring |
| POST | /api/pin/set | Matrix encrypt a PIN |
| POST | /api/pin/set-duress | Set coercion detection PIN |
| POST | /api/pin/verify | Verify PIN (handles duress silently) |
| POST | /api/tax/optimize | Tax saving analysis |
| POST | /api/goals/add | Add a financial goal |
| GET | /api/goals/progress | Goal progress with AI status |
| GET | /api/goals/list | List all goals with indices |
| PUT | /api/goals/update/{index} | Update a specific goal |
| DELETE | /api/goals/delete/{index} | Delete a specific goal |
| DELETE | /api/goals/clear | Clear all goals |
| GET | /api/portfolio/divergence | Shadow portfolio divergence score |
| GET | /api/simulator/what-if | Counterfactual single asset |
| GET | /api/simulator/compare-all | Compare all asset classes |
| POST | /api/simulator/stress-test | Crisis scenario simulation |
| GET | /api/simulator/scenarios | List all stress scenarios |
| POST | /api/property/analyze | Property appreciation projection |
| GET | /api/property/lookup/{zip} | ZIP code neighborhood data |
| GET | /api/security/velocity-heatmap | 24-hour transaction heatmap |
| GET | /api/audit-trail | Full event log |
| GET | /api/audit/summary | Security intelligence summary |
| DELETE | /api/session/clear | Reset session and profile |

---

## Endpoint Details

---

### 1. GET /api/twin
Returns the full digital twin. Call on dashboard load.

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

### 2. GET /api/ai/summary
One-paragraph summary of the user's complete financial state.
Call on dashboard load to populate the header card.

**Response:**
```json
{
  "summary": "Your current net worth is ₹4,090,000...",
  "net_worth": 4090000,
  "divergence_score": 73,
  "divergence_urgency": "HIGH",
  "shift_triggered": true,
  "shift_rule": "HIGH_FD_RATE_HIGH_VOLATILITY",
  "market_mood": "NEUTRAL",
  "goals_tracked": 2,
  "transactions_blocked_this_session": 0,
  "archetype": "The Accumulator"
}
```

**UI Notes:**
- Show `summary` as the dashboard header paragraph
- Use `divergence_urgency` to color a badge: LOW=green, MEDIUM=yellow, HIGH=red
- If `shift_triggered` is true show a persistent alert banner

---

### 3. POST /api/chat
Brain 01 — financial question answering with reasoning.

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
  },
  "language": "en"
}
```

Set `"language": "hi"` for Hindi response.
Language is also auto-detected from Devanagari script.

**Response:**
```json
{
  "reply": "Your gold holding is 8.8% of net worth...",
  "shift_logic_triggered": true,
  "shift_logic_rule": "HIGH_FD_RATE_HIGH_VOLATILITY",
  "reasoning": [
    {
      "factor": "Gold Allocation",
      "value": "8.8% of portfolio",
      "impact": "Compared against 10-15% recommended range"
    }
  ],
  "confidence": 100,
  "confidence_note": null,
  "language_detected": "en"
}
```

**UI Notes:**
- Show `reasoning` array as expandable "Explain AI Logic" panel
- If `shift_logic_triggered` is true, show gold banner above reply
- If `confidence` < 80, show `confidence_note` as a soft prompt to complete profile
- Show loading spinner while waiting — call takes 1-2 seconds
- `language_detected` tells you which language the response is in

---

### 4. POST /api/chat/reset
Clears conversation memory. Call when user starts a new session.

**Response:** `{"status": "Conversation history cleared"}`

---

### 5. GET /api/shift-logic/status
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

**Rules that can fire:**
- `HIGH_FD_RATE_HIGH_VOLATILITY` — FD rate > 7% and NIFTY PE > 22
- `FD_RATE_RISING_TREND` — FD rate rising 3 consecutive readings
- `INFLATION_GOLD_HEDGE` — Inflation > 6% and gold returning > 10%
- `INFLATION_RISING_TREND` — Inflation rising 3 consecutive readings
- `NIFTY_PE_RISING_TREND` — PE rising 3 consecutive readings
- `HIGH_REPO_RATE_FD_OPPORTUNITY` — Repo rate > 6% and FD > 7%

---

### 6. GET /api/market/sentiment
Headline sentiment analysis across 5 asset classes.

**Response:**
```json
{
  "overall_score": 10,
  "overall_mood": "NEUTRAL",
  "mood_description": "Market sentiment is mixed...",
  "asset_sentiment": {
    "gold": { "score": 40, "sentiment": "POSITIVE", "headline_count": 1 },
    "equity": { "score": 60, "sentiment": "POSITIVE", "headline_count": 2 }
  },
  "advisory": "Gold sentiment is positive...",
  "top_headlines": ["RBI holds repo rate...", "NIFTY hits all-time high..."],
  "data_source": "mock_headlines_demo",
  "disclaimer": "Headlines are representative mock data for demo purposes..."
}
```

---

### 7. POST /api/profile/classify
Classifies user into one of 4 financial archetypes.
Call during onboarding. Profile persists across server restarts.

**Request:**
```json
{
  "age": 25,
  "annual_income": 800000,
  "dependents": 0,
  "risk_appetite": "high",
  "primary_goal": "growth",
  "investment_horizon_years": 20
}
```

`risk_appetite` options: `"low"`, `"medium"`, `"high"`
`primary_goal` options: `"growth"`, `"preservation"`, `"income"`, `"tax_saving"`

**Response:**
```json
{
  "archetype": "accumulator",
  "label": "The Accumulator",
  "description": "You are in wealth-building mode...",
  "recommended_allocation": {
    "equity_mutual_funds": 50,
    "gold": 10,
    "real_estate": 20,
    "liquid_cash": 10,
    "fd_debt": 10
  },
  "advisor_style": "...",
  "key_priorities": ["Maximise long-term returns", ...]
}
```

**Archetypes:**
- `accumulator` — Young, growth-focused, high risk tolerance
- `protector` — Family-first, low risk, stability focused
- `optimizer` — Tax and returns focused, analytical
- `preserver` — Near retirement, capital protection first

---

### 8. POST /api/transaction/verify
Brain 02 — behavioral threat scoring on every transaction.

**Request:**
```json
{
  "amount": 150000,
  "transaction_type": "transfer",
  "recipient": "savings_account",
  "note": "monthly",
  "session_duration_ms": 45000,
  "is_known_device": true,
  "otp_keypress_intervals_ms": [145, 203, 178, 220, 165],
  "recipient_account_age_days": 365,
  "recipient_is_whitelisted": false
}
```

**How to get `session_duration_ms`:**
```javascript
window.sessionStart = Date.now(); // set on page load
session_duration_ms: Date.now() - window.sessionStart
```

**How to get `is_known_device`:**
```javascript
const fingerprint = navigator.userAgent + screen.width + screen.height;
localStorage.setItem('deviceFingerprint', fingerprint);
is_known_device: localStorage.getItem('deviceFingerprint') ===
                 navigator.userAgent + screen.width + screen.height
```

**How to get `otp_keypress_intervals_ms`:**
```javascript
// Track time between each keypress during OTP entry
const intervals = [];
let lastKeyTime = null;
otpInput.addEventListener('keydown', () => {
  if (lastKeyTime) intervals.push(Date.now() - lastKeyTime);
  lastKeyTime = Date.now();
});
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
    "recipient_risk": 5,
    "otp_latency_anomaly": 0,
    "recipient_account_risk": 5
  },
  "triggered_signals": ["All signals within normal range"],
  "risk_summary": "Transaction approved with confidence score 78/100.",
  "cooling_off_seconds": 0,
  "ai_explanation": null,
  "pattern_detected": null
}
```

**UI behavior per action:**
- `ALLOW` → Proceed. Reactor stays cyan.
- `CHALLENGE` → Show biometric modal. Lock UI for `cooling_off_seconds`. Reactor turns gold.
- `BLOCK` → Show block overlay with `ai_explanation`. Reactor turns crimson. Show `triggered_signals` as bullet list.

**Pattern detection — if `pattern_detected` is not null:**
```json
{
  "pattern_name": "TEST_THEN_DRAIN",
  "description": "A small test transaction was followed by a large transfer...",
  "confidence": 85,
  "score_bonus": 25
}
```
Show pattern name and description prominently in the block overlay.

---

### 9. POST /api/pin/set
Matrix encryption on a PIN. Shows the math to judges.

**Request:** `{"pin": "1234"}`

**Response:**
```json
{
  "success": true,
  "hash_stored": "2923352bdf...",
  "cipher_vector": [88, 111, 36]
}
```

**UI Notes:**
- Display `cipher_vector` and `hash_stored` visually
- Label: "Your PIN was never stored. Only this mathematical transformation was."

---

### 10. POST /api/pin/set-duress
Sets a secret coercion detection PIN.

**Request:** `{"pin": "9999"}`
**Response:** `{"success": true, "message": "Duress PIN set successfully"}`

---

### 11. POST /api/pin/verify
Verifies PIN. Silently handles duress.

**Request:** `{"pin": "1234"}`

**Response:**
```json
{
  "verified": true,
  "duress": false,
  "message": "PIN verified successfully"
}
```

**Critical UI rule:**
If `duress: true` — show normal success UI. Never reveal duress detection on screen.
Check audit trail in background to confirm the silent alert was logged.

---

### 12. POST /api/tax/optimize
Tax saving analysis for old and new regime.

**Request:**
```json
{
  "annual_income": 1200000,
  "regime": "old",
  "existing_80c": 50000,
  "existing_80d": 0,
  "home_loan_interest": 150000,
  "nps_contribution": 0
}
```

`regime` options: `"old"`, `"new"`

**Response:**
```json
{
  "tax_regime": "Old Regime",
  "current_taxable_income": 950000,
  "current_tax_payable": 106600,
  "optimized_tax_payable": 75400,
  "total_savings": 31200,
  "recommendations": ["You have ₹100,000 of unused 80C limit..."],
  "deduction_breakdown": { "standard_deduction": 50000, "section_80c": 50000 },
  "reasoning": [...]
}
```

---

### 13. Goal Endpoints

**Add a goal:**
```json
POST /api/goals/add
{
  "name": "Buy a Car",
  "category": "car",
  "target_amount": 800000,
  "current_saved": 100000,
  "target_years": 2,
  "monthly_contribution": 5000
}
```

`category` options: `"home"`, `"car"`, `"education"`, `"retirement"`, `"emergency_fund"`, `"travel"`, `"other"`

**Get progress:**
```
GET /api/goals/progress
```

**Response:**
```json
{
  "goals": [
    {
      "name": "Buy a Car",
      "status": "BEHIND",
      "progress_pct": 12.5,
      "required_monthly_contribution": 25979,
      "monthly_gap": 20979,
      "projected_completion_years": 7.2,
      "ai_status_message": "Behind schedule. At ₹5,000/month you'll reach this in 7.2 years..."
    }
  ],
  "overall_message": "1 of 2 goals are on track..."
}
```

**Status values:** `"ON_TRACK"`, `"AHEAD"`, `"BEHIND"`

**UI Notes:**
- Show progress as a bar (use `progress_pct`)
- Color by status: AHEAD=cyan, ON_TRACK=green, BEHIND=red
- Show `ai_status_message` below each bar
- Show `monthly_gap` prominently for BEHIND goals

**Update a goal:**
```json
PUT /api/goals/update/0
{
  "name": "Buy a Car",
  "category": "car",
  "target_amount": 800000,
  "current_saved": 150000,
  "target_years": 2,
  "monthly_contribution": 15000
}
```

**Delete a goal:**
```
DELETE /api/goals/delete/0
```

---

### 14. GET /api/portfolio/divergence
Shadow portfolio comparison vs archetype ideal.
Set profile first via `/api/profile/classify`.

**Response:**
```json
{
  "divergence_score": 87,
  "urgency": "HIGH",
  "breakdown": [
    {
      "asset_class": "Equity / Mutual Funds",
      "current_pct": 3.4,
      "ideal_pct": 50,
      "difference": -46.6
    }
  ],
  "biggest_gap": { ... },
  "ai_summary": "Your portfolio has significant drift...",
  "archetype_used": "The Accumulator"
}
```

**UI Notes:**
- Show as a side-by-side bar chart: current vs ideal per asset class
- Color difference bars: negative=red (underweight), positive=orange (overweight)
- Show `divergence_score` as a gauge (0-100)

---

### 15. Simulator Endpoints

**Counterfactual — single asset:**
```
GET /api/simulator/what-if?amount=250000&asset=gold&from_year=2019&to_year=2024
```

`asset` options: `"nifty50"`, `"gold"`, `"fd"`, `"real_estate"`, `"mutual_funds_debt"`

**Compare all assets:**
```
GET /api/simulator/compare-all?amount=250000&from_year=2019&to_year=2024
```

Response includes `best_performer`, `worst_performer`, and `summary` — a one-sentence headline stat.

**Stress test:**
```json
POST /api/simulator/stress-test
{
  "assets": { ... },
  "scenario": "market_crash_2008"
}
```

`scenario` options:
- `"market_crash_2008"`
- `"covid_crash_2020"`
- `"inflation_surge"`
- `"rupee_crisis"`
- `"rate_hike_shock"`

**List scenarios:**
```
GET /api/simulator/scenarios
```

---

### 16. Property Endpoints

**Analyze property:**
```
POST /api/property/analyze?property_value=4500000&zip_code=560037&years=5
```

**ZIP lookup:**
```
GET /api/property/lookup/560037
```

**Supported ZIP codes:**
Mumbai: 400001, 400051, 400076
Delhi: 110001, 110075, 110092
Bangalore: 560001, 560037, 560103
Hyderabad: 500081, 500032
Chennai: 600001, 600096
Pune: 411001, 411045

---

### 17. Security Endpoints

**Velocity heatmap:**
```
GET /api/security/velocity-heatmap
```

Returns 24 hourly buckets with `transaction_count`, `avg_threat_score`,
and `risk_level` (NONE/LOW/MEDIUM/HIGH) for each hour.

---

### 18. Audit Endpoints

**Full audit trail:**
```
GET /api/audit-trail
```

**Intelligence summary:**
```
GET /api/audit/summary
```

Response includes `security_score` (0-100), `security_rating`
(SECURE/MONITORING/ALERT), and `recommendations`.

**Action types in audit trail:**
- `CHAT` — AI advisor query
- `TRANSACTION` — Brain 02 evaluation
- `DURESS_TRIGGERED` — Coercion detection (show in crimson)
- `PROFILE_CLASSIFIED` — Archetype set
- `TAX_OPTIMIZATION` — Tax analysis run
- `GOAL_ADDED` — New goal created
- `STRESS_TEST` — Scenario simulation run
- `SENTIMENT_CHECK` — Market sentiment fetched
- `DIVERGENCE_CHECK` — Portfolio divergence calculated
- `SHARDED_PIN_SET` — 3-shard encryption used

---

### 19. Session Endpoints

**Clear session:**
```
DELETE /api/session/clear
```

Resets profile and session state. Use when switching demo users.

---

## Error Handling

All errors return:
```json
{"detail": "Error message here"}
```

HTTP codes:
- `400` — Bad request (invalid input)
- `401` — Invalid PIN
- `404` — Goal not found
- `500` — Server error (check uvicorn terminal)

---

## Demo Setup Sequence

Run these in order at the start of every demo session:

**1.** Start backend: `cd backend && python -m uvicorn main:app --reload`

**2.** Set profile (persists across restarts — only needed once):
```json
POST /api/profile/classify
{"age": 25, "annual_income": 800000, "dependents": 0,
 "risk_appetite": "high", "primary_goal": "growth",
 "investment_horizon_years": 20}
```

**3.** Set PINs:
```json
POST /api/pin/set → {"pin": "1234"}
POST /api/pin/set-duress → {"pin": "9999"}
```

**4.** Add demo goals:
```json
POST /api/goals/add → {"name": "Buy a Car", "category": "car",
  "target_amount": 800000, "current_saved": 100000,
  "target_years": 2, "monthly_contribution": 5000}
POST /api/goals/add → {"name": "Retirement Fund", "category": "retirement",
  "target_amount": 20000000, "current_saved": 4090000,
  "target_years": 20, "monthly_contribution": 25000}
```

**5.** Verify everything: `GET /api/ai/summary`