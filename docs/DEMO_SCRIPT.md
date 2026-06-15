# FinTwin Demo Script
## PSB Hackathon — Team Code Nova
**Total demo time: 5 minutes**

---

## Pre-Demo Setup (do this before judges arrive)

```
cd backend
python -m uvicorn main:app --reload
cd frontend && npm start
```

Then in /docs, run in order:
1. POST /api/profile/classify → Accumulator profile
2. POST /api/pin/set → {"pin": "1234"}
3. POST /api/pin/set-duress → {"pin": "9999"}
4. POST /api/goals/add → Car goal (behind schedule)
5. POST /api/goals/add → Retirement goal (ahead)
6. GET /api/ai/summary → confirm everything loads

Keep two browser tabs open:
- Tab 1: The FinTwin dashboard
- Tab 2: /api/audit-trail (refresh to show live events)

---

## Scene 1 — The Problem (20 seconds)

**Say:**
"Most Indians have money in four different places —
bank, gold, property, mutual funds.
No single view. No intelligence. No protection against fraud."

**Show:** Four separate apps side by side.

**Then open FinTwin. Point to net worth in the top bar.**

**Say:**
"FinTwin gives you one number. ₹40,90,000.
Your complete financial reality in real time."

---

## Scene 2 — Brain 01: Intelligence (90 seconds)

**Point to the active shift logic banner.**

**Say:**
"Before the user asked anything, the system already flagged this —
FD rates crossed 7.2% while NIFTY PE is elevated.
Proactive intelligence."

**Type in advisor chat:**
"Should I buy more gold right now?"

**While it responds, say:**
"Watch what it references — not generic advice."

**Point to the response. Highlight specific numbers:**
8.8% allocation, ₹3,60,000 value, 14.2% gold return, 5.1% inflation.

**Click Explain AI Logic. Show reasoning panel.**

**Say:**
"Every recommendation shows exactly which data points drove it.
Explainable AI — not a black box."

**Switch to the counterfactual simulator.**

**Say:**
"If this user had put ₹2,50,000 in gold in 2019,
it would be worth ₹5,57,962 today — 123% return.
FD? Only ₹3,65,435.
This is the intelligence gap we are closing."

**Show stress test — 2008 scenario.**

**Say:**
"What happens if 2008 happens again?
Portfolio drops ₹12,72,600 — a 31% loss.
Real estate is the most exposed asset.
FinTwin tells you this before it happens, not after."

---

## Scene 3 — Personality Profiling (20 seconds)

**Show the archetype card.**

**Say:**
"This is not generic advice for everyone.
FinTwin classifies each user into one of four financial archetypes.
The Accumulator, at 25, gets told to increase SIPs.
The Preserver, at 58, gets told to move to Senior Citizen FDs.
Same portfolio. Same question. Different advice."

---

## Scene 4 — Brain 02: Threat Protection (90 seconds)

**Say:**
"Now the security layer.
Every transaction is scored across 8 behavioral signals in real time."

**Simulate normal transaction:**
```json
{"amount": 5000, "transaction_type": "transfer",
 "recipient": "savings_account", "session_duration_ms": 120000,
 "is_known_device": true, "recipient_is_whitelisted": true,
 "otp_keypress_intervals_ms": [145, 203, 178, 220, 165]}
```

**Say:** "Score 21. ALLOW. Reactor stays calm."

**Simulate suspicious transaction:**
```json
{"amount": 150000, "transaction_type": "transfer", "recipient": "",
 "session_duration_ms": 8000, "is_known_device": false,
 "otp_keypress_intervals_ms": [50, 51, 49, 50, 51],
 "recipient_account_age_days": 3, "recipient_is_whitelisted": false}
```

**Say:**
"Same user. Different behavior.
Unknown device. ₹1,50,000. Done in 8 seconds.
Robotic OTP entry — all keypresses exactly 50ms apart.
3-day-old recipient account."

**Point to the BLOCK response. Show triggered signals.**

**Say:**
"Score 81. BLOCK.
The system explains exactly why — in plain English.
OTP entry pattern suggests coercion or automation.
Recipient account is newly created."

**Now demonstrate the pattern detection.**

**First send a small test transfer (₹100), then immediately the large one.**

**Say:**
"Watch what happens when there's a sequence.
Small test transfer. Then large withdrawal immediately after.
Brain 02 recognizes this as the TEST_THEN_DRAIN pattern —
the exact sequence used to verify a stolen account before draining it.
Score jumps by 25 points from the pattern alone."

**Now demonstrate duress detection.**

**Say:**
"But what if the user is being physically forced?
Traditional banking has no answer to this."

**Enter duress PIN 9999. Show success screen.**

**Say:**
"Success screen. The coercer sees nothing wrong."

**Switch to audit trail tab. Refresh.**

**Point to DURESS_TRIGGERED entry.**

**Say:**
"But here — silently logged.
Trusted contact notified. Transaction frozen in the background.
No Indian bank has built this."

---

## Scene 5 — Matrix Security (20 seconds)

**Show PIN set response — cipher vector and hash.**

**Say:**
"PIN 1234 was never stored anywhere.
What was stored is this — a mathematical transformation
using a rotating private key matrix that changes every hour.
A stolen credential from 9am is useless by 10am.
Brute force requires solving simultaneous congruence equations — not just guessing."

---

## Scene 6 — Close (20 seconds)

**Say:**
"FinTwin is not a banking app with AI features bolted on.
AI is the core.
One brain that grows your wealth.
One brain that protects it.
A mathematical layer that secures it.

Wealth growth is an intelligence game.
We just changed the rules."

---

## Likely Judge Questions — With Answers

**Q: Is user data safe with the LLM?**
A: The MCP layer strips all PII before any data reaches the model.
The LLM only sees anonymized numbers — balance amounts, percentages, market rates.
Raw account data never leaves the user's device in our architecture.

**Q: What if the AI gives wrong advice?**
A: Every recommendation shows its reasoning chain — the exact data points that drove it.
Users can audit every decision. The system prompt also constrains the model
to never speculate beyond the data it receives.

**Q: How is this different from existing robo-advisors?**
A: Three ways. One — it covers all asset classes, not just mutual funds.
Two — it detects behavioral fraud, not just credential theft.
Three — it protects against coercion, which no existing Indian product does.

**Q: What does the matrix encryption add over SHA-256?**
A: SHA-256 alone is vulnerable to dictionary attacks because similar inputs
produce somewhat predictable outputs at the input stage.
Our linear algebra transformation means two similar PINs produce completely
different cipher vectors before hashing.
The rotating key means even a stolen vector expires in under an hour.

**Q: Are the market headlines real?**
A: For the prototype, we use representative mock headlines.
The production version connects to Economic Times and Moneycontrol RSS feeds
via the same sentiment pipeline. The AI reasoning engine is identical —
only the data source changes.

**Q: What happens if someone discovers the duress PIN?**
A: The duress PIN is set by the user and known only to them.
It is encrypted identically to the real PIN — an attacker cannot distinguish them
from the stored hash. The entire point is that the coercer
sees a successful transaction while the alert fires silently.

**Q: How does the personality profiling affect advice?**
A: The archetype is injected directly into the LLM system prompt,
changing the advisor's style, risk tolerance, and priorities.
A 25-year-old Accumulator asking about gold gets told to increase SIPs.
A 58-year-old Preserver asking the same question gets told
to consider Senior Citizen FDs instead. Same portfolio, same question,
fundamentally different answer.

---

## If Something Goes Wrong During Demo

**Backend not starting:**
```
cd backend
python -m uvicorn main:app --reload --port 8001
```
Update BASE_URL in frontend api.js to port 8001.

**Profile lost:**
```
POST /api/profile/classify
```
Takes 5 seconds. Do it live — it's actually a good demo moment.

**AI response slow:**
The fallback advisor responds instantly.
If Claude API has no credits, fallback fires automatically.
Response quality is still good — archetype-aware and number-specific.

**Forgot to set duress PIN:**
```
POST /api/pin/set-duress → {"pin": "9999"}
```
Do it live — explaining what you're doing is part of the demo.