# FinTwin Demo Script
## PSB Hackathon — Team Code Nova

Total demo time: 4 minutes

---

## Setup Before Demo

1. Start backend: `cd backend && python -m uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm start`
3. Pre-set PINs via /docs:
   - Real PIN: POST /api/pin/set → {"pin": "1234"}
   - Duress PIN: POST /api/pin/set-duress → {"pin": "9999"}
4. Keep audit trail tab open in a second browser tab

---

## Scene 1 — The Problem (20 seconds)

Say: "Most Indians have money in 4 different places —
bank, gold, property, mutual funds.
No single view. No intelligence. No protection."

Show: The fragmented state — 4 separate apps open side by side.

Then open FinTwin. Point to the net worth figure in the top bar.

Say: "FinTwin gives you one number. ₹40,90,000.
That's your complete financial reality in real time."

---

## Scene 2 — Brain 01: AI Intelligence (90 seconds)

Point to the gold alert banner (shift logic is already firing).

Say: "The system has already detected that FD rates crossed 7.2%
while NIFTY PE is elevated. It flagged this proactively —
the user didn't ask anything."

Type in the advisor chat: "Should I buy more gold right now?"

While it responds, say: "This isn't a generic tip.
Watch what it references."

Point to the response — highlight the specific numbers:
8.8% allocation, 14.2% gold return, 5.1% inflation.

Click "Explain AI Logic" to show the reasoning panel.

Say: "Every recommendation shows exactly which data points
drove it. This is explainable AI — not a black box."

Now show the counterfactual simulator result.

Say: "If this user had put ₹2,50,000 in gold in 2019,
it would be worth ₹5,57,962 today — 123% return.
Compare that to FD — only ₹3,65,435.
This is the intelligence gap we are closing."

---

## Scene 3 — Brain 02: Threat Protection (90 seconds)

Say: "Now the security layer. Every transaction
is scored in real time across 6 behavioral signals."

Simulate a normal transaction:
- Amount: 5000, known device, 120 seconds session

Say: "Score: 21. ALLOW. Reactor stays calm."

Now simulate a suspicious transaction:
- Amount: 150000, unknown device, 8 seconds session, no recipient

Say: "Same user. Different behavior.
Unknown device. Large amount. Completed in 8 seconds."

Show the BLOCK response. Point to triggered signals.

Say: "Score: 74. BLOCK.
The system tells you exactly why —
unrecognised device, suspiciously fast, unknown recipient."

Now demonstrate duress detection.

Say: "But what if the user is being forced?
Traditional banking has no answer for this."

Enter duress PIN 9999.

Say: "The screen shows success. The coercer sees nothing wrong.
But watch the audit trail."

Switch to audit trail tab — show DURESS_TRIGGERED entry.

Say: "Silently logged. Trusted contact notified.
Transaction frozen in the background.
No Indian bank has built this."

---

## Scene 4 — Matrix Security (30 seconds)

Show the PIN set response — cipher vector and SHA-256 hash.

Say: "The PIN 1234 was never stored anywhere.
What was stored is this — a mathematical transformation
using a rotating private matrix that changes every hour.
A stolen credential from 9am is useless by 10am."

---

## Scene 5 — Close (20 seconds)

Say: "FinTwin is not a banking app with AI features.
AI is the core — one brain that grows your wealth,
one brain that protects it,
and a mathematical layer that secures it.

Wealth growth is an intelligence game.
We just changed the rules."

---

## Likely Judge Questions

**Q: Is this using real bank data?**
A: For the prototype we use the RBI Account Aggregator framework architecture.
MCP fetches anonymized context — raw account data never touches our servers.
In production this connects to live AA APIs.

**Q: What if the AI gives wrong advice?**
A: Every recommendation shows its reasoning chain — the exact data points
that drove it. Users can audit every decision.
We also constrain the model with a strict system prompt —
it cannot speculate beyond the data it receives.

**Q: How is this different from existing robo-advisors?**
A: Three ways. One — it knows your complete portfolio across all asset
classes, not just mutual funds. Two — it detects behavioral fraud,
not just credential theft. Three — it protects against coercion,
which no existing product does.

**Q: What does the matrix encryption add over SHA-256?**
A: SHA-256 alone is vulnerable to dictionary attacks because similar
inputs produce predictable outputs. The matrix transformation adds
confusion and diffusion at the input level — two similar PINs produce
completely different cipher vectors before hashing.
The rotating key means even a stolen vector expires in under an hour.