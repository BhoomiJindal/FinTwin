from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime
from property_advisor import analyze_property, get_neighborhood_data
from simulator import run_counterfactual, compare_all_assets
from models import (
    Assets, MarketData, NetWorthResponse,
    TransactionRequest, ThreatResponse, ThreatSignals, DecisionAction,
    ChatRequest, ChatResponse, ReasoningStep,
    PINRequest, PINResponse,
    AuditEntry, AuditResponse,
    UserProfile, ArchetypeResponse, Archetype,
    TaxProfile, TaxOptimizationResponse,
    PatternMatch,
    Goal, GoalProgress, GoalsResponse,
    DivergenceResponse, AllocationBreakdown,
    AuditIntelligenceSummary
)
from profiler import get_archetype_response, get_archetype_context, classify_archetype
from tax_engine import optimize_tax
from goals import analyze_all_goals
from typing import List
from shadow_portfolio import calculate_divergence
from sentiment import get_market_sentiment


# ─── SETUP ────────────────────────────────────────────

load_dotenv()
app = FastAPI(title="FinTwin API", version="1.0.0")

# Allow React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory audit log (resets on server restart — fine for prototype)
audit_log = []

# ─── MOCK MARKET DATA ─────────────────────────────────
# Replace with live API calls in production

def get_market_data() -> MarketData:
    return MarketData(
        gold_price_per_gram=7200.0,
        repo_rate=6.50,
        inflation_rate=5.10,
        nifty_pe=22.4,
        fd_rate=7.20
    )

# ─── ROUTES ───────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "FinTwin API is running", "version": "1.0.0"}


# ── 1. GET /api/twin ──────────────────────────────────
# Returns the current Digital Twin status
# Frontend calls this on load to populate the dashboard

@app.get("/api/twin", response_model=NetWorthResponse)
def get_twin():
    # Sample starting portfolio — will come from DB/localStorage sync later
    assets = Assets(
        liquid_cash=250000,
        mutual_funds=180000,
        gold_grams=50,
        real_estate=4500000,
        liabilities=1200000
    )

    market = get_market_data()
    gold_value = assets.gold_grams * market.gold_price_per_gram
    total_assets = (
        assets.liquid_cash +
        assets.mutual_funds +
        gold_value +
        assets.real_estate
    )
    net_worth = total_assets - assets.liabilities

    return NetWorthResponse(
        assets=assets,
        market_data=market,
        net_worth=net_worth,
        gold_value=gold_value,
        total_assets=total_assets
    )


# ── 2. POST /api/chat ─────────────────────────────────
# Processes user financial questions
# Returns AI advice (mock for now, real Claude in Stage 5)

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    from advisor import get_ai_advice
    from models import ReasoningStep

    assets_dict = {
        "liquid_cash": request.assets.liquid_cash or 0,
        "mutual_funds": request.assets.mutual_funds or 0,
        "gold_grams": request.assets.gold_grams or 0,
        "real_estate": request.assets.real_estate or 0,
        "liabilities": request.assets.liabilities or 0,
    }

    if not request.message or request.message.strip() == "":
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Pass archetype if profile has been set
    archetype = current_user_profile.get("archetype")
    if archetype and hasattr(archetype, 'value'):
        archetype = archetype.value
    result = get_ai_advice(request.message, assets_dict, archetype)

    reasoning_steps = [
        ReasoningStep(**step) for step in result.get("reasoning", [])
    ]

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="CHAT",
        outcome=f"Query: {request.message[:50]}"
    ))

    return ChatResponse(
        reply=result["reply"],
        shift_logic_triggered=result["shift_logic_triggered"],
        shift_logic_rule=result["shift_logic_rule"],
        reasoning=reasoning_steps,
        confidence=result["confidence"],
        confidence_note=result["confidence_note"]
    )


# ── 3. POST /api/transaction/verify ──────────────────
# Runs 6-signal threat scoring on every transaction
# Returns threat score + decision (ALLOW / CHALLENGE / BLOCK)

@app.post("/api/transaction/verify", response_model=ThreatResponse)
def verify_transaction(request: TransactionRequest):
    from security import calculate_threat_score
    from models import PatternMatch

    result = calculate_threat_score(request)

    pattern_match = None
    if result["pattern"]:
        pattern_match = PatternMatch(
            pattern_name=result["pattern"]["pattern_name"],
            description=result["pattern"]["description"],
            confidence=result["pattern"]["confidence"],
            score_bonus=result["pattern"]["score_bonus"]
        )

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="TRANSACTION",
        threat_score=result["score"],
        amount=request.amount,
        outcome=result["action"]
    ))

    return ThreatResponse(
        threat_score=result["score"],
        action=DecisionAction(result["action"]),
        signals=ThreatSignals(**result["signals"]),
        message=result["message"],
        triggered_signals=result["triggered_signals"],
        risk_summary=result["risk_summary"],
        cooling_off_seconds=result["cooling_off_seconds"],
        ai_explanation=result["ai_explanation"],
        pattern_detected=pattern_match
    )


# ── 4. POST /api/pin/set ──────────────────────────────
# Encrypts PIN using matrix transformation + SHA-256
# Returns cipher vector and final hash for transparency

@app.post("/api/pin/set", response_model=PINResponse)
def set_pin(request: PINRequest):
    from security import encrypt_pin

    if len(request.pin) < 4:
        raise HTTPException(status_code=400, detail="PIN must be at least 4 digits")

    result = encrypt_pin(request.pin)

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="PIN_SET",
        outcome="PIN encrypted and stored successfully"
    ))

    return PINResponse(
        success=True,
        hash_stored=result["hash"],
        cipher_vector=result["cipher_vector"]
    )


# ── 5. GET /api/audit-trail ───────────────────────────
# Returns full transaction and action log

@app.get("/api/audit-trail", response_model=AuditResponse)
def get_audit_trail():
    return AuditResponse(
        entries=audit_log,
        total_count=len(audit_log)
    )


@app.get("/api/shift-logic/status")
def get_shift_logic_status():
    from advisor import get_market_context, check_shift_logic
    
    market = get_market_context()
    triggered, rule, description = check_shift_logic(market)
    
    return {
        "shift_triggered": triggered,
        "rule": rule if triggered else None,
        "description": description if triggered else None,
        "market_snapshot": market
    }


@app.post("/api/chat/reset")
def reset_conversation():
    from advisor import conversation_history
    conversation_history.clear()
    return {"status": "Conversation history cleared"}


# Store duress PIN hash separately from real PIN
duress_pin_store = {"hash": None}
real_pin_store = {"hash": None}

@app.post("/api/pin/set-duress")
def set_duress_pin(request: PINRequest):
    from security import encrypt_pin

    if len(request.pin) < 4:
        raise HTTPException(status_code=400, detail="Duress PIN must be at least 4 digits")

    result = encrypt_pin(request.pin)
    duress_pin_store["hash"] = result["hash"]

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="DURESS_PIN_SET",
        outcome="Duress PIN configured successfully"
    ))

    return {"success": True, "message": "Duress PIN set successfully"}


@app.post("/api/pin/verify")
def verify_pin(request: PINRequest):
    from security import encrypt_pin

    result = encrypt_pin(request.pin)
    entered_hash = result["hash"]

    # Check if it matches the duress PIN
    if duress_pin_store["hash"] and entered_hash == duress_pin_store["hash"]:
        # DURESS DETECTED
        # Show success to user but log the alert silently
        audit_log.append(AuditEntry(
            timestamp=datetime.now().isoformat(),
            action="DURESS_TRIGGERED",
            outcome="SILENT ALERT — Coercion detected. Trusted contact notified."
        ))
        # Return fake success — coercer sees nothing wrong
        return {
            "verified": True,
            "duress": True,
            "message": "PIN verified successfully"  # coercer sees this
        }

    # Check real PIN
    if real_pin_store["hash"] and entered_hash == real_pin_store["hash"]:
        return {"verified": True, "duress": False, "message": "PIN verified successfully"}

    raise HTTPException(status_code=401, detail="Invalid PIN")



# ── Property ZIP Analysis ─────────────────────────────

@app.post("/api/property/analyze")
def analyze_property_endpoint(
    property_value: float,
    zip_code: str,
    years: int = 5
):
    if property_value <= 0:
        raise HTTPException(status_code=400, detail="Property value must be positive")
    if len(zip_code) < 5:
        raise HTTPException(status_code=400, detail="Enter a valid ZIP or PIN code")

    result = analyze_property(property_value, zip_code, years)

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="PROPERTY_ANALYSIS",
        outcome=f"ZIP {zip_code} analyzed — {result['area_name']}"
    ))

    return result


# ── ZIP Code Lookup ───────────────────────────────────

@app.get("/api/property/lookup/{zip_code}")
def lookup_zip(zip_code: str):
    data = get_neighborhood_data(zip_code)
    if not data:
        return {
            "found": False,
            "message": f"ZIP {zip_code} not in database. Using national average of 7% appreciation.",
            "fallback_rate": 7.0
        }
    return {"found": True, **data}


# ── Counterfactual Simulator ──────────────────────────

@app.get("/api/simulator/what-if")
def what_if(
    amount: float,
    asset: str,
    from_year: int = 2019,
    to_year: int = 2024
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if from_year > to_year:
        raise HTTPException(status_code=400, detail="from_year must be before to_year")

    result = run_counterfactual(amount, asset, from_year, to_year)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.get("/api/simulator/compare-all")
def compare_all(
    amount: float,
    from_year: int = 2019,
    to_year: int = 2024
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    return compare_all_assets(amount, from_year, to_year)


# ── User Personality Profiling ────────────────────────

# Store current user profile in memory
current_user_profile = {"archetype": None, "profile": None}

@app.post("/api/profile/classify", response_model=ArchetypeResponse)
def classify_user(profile: UserProfile):
    result = get_archetype_response(profile)

    # Store archetype so advisor uses it in all future responses
    current_user_profile["archetype"] = result["archetype"]
    current_user_profile["profile"] = profile.model_dump()

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="PROFILE_CLASSIFIED",
        outcome=f"Archetype: {result['label']}"
    ))

    return ArchetypeResponse(**result)


@app.get("/api/profile/current")
def get_current_profile():
    if not current_user_profile["archetype"]:
        return {"archetype": None, "message": "No profile set yet"}
    return current_user_profile


# ── Tax Optimisation ──────────────────────────────────

@app.post("/api/tax/optimize", response_model=TaxOptimizationResponse)
def tax_optimize(profile: TaxProfile):
    if profile.annual_income <= 0:
        raise HTTPException(status_code=400, detail="Annual income must be positive")

    result = optimize_tax(profile)

    reasoning_steps = [ReasoningStep(**step) for step in result["reasoning"]]

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="TAX_OPTIMIZATION",
        outcome=f"Savings identified: ₹{result['total_savings']:,.0f}"
    ))

    return TaxOptimizationResponse(
        tax_regime=result["tax_regime"],
        current_taxable_income=result["current_taxable_income"],
        current_tax_payable=result["current_tax_payable"],
        optimized_tax_payable=result["optimized_tax_payable"],
        total_savings=result["total_savings"],
        recommendations=result["recommendations"],
        deduction_breakdown=result["deduction_breakdown"],
        reasoning=reasoning_steps
    )


# ── Goal-Based Wealth Tracking ────────────────────────

# In-memory goal storage
user_goals: List[Goal] = []

@app.post("/api/goals/add")
def add_goal(goal: Goal):
    if goal.target_amount <= 0:
        raise HTTPException(status_code=400, detail="Target amount must be positive")
    if goal.target_years <= 0:
        raise HTTPException(status_code=400, detail="Target years must be positive")

    user_goals.append(goal)

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="GOAL_ADDED",
        outcome=f"{goal.name} — Target ₹{goal.target_amount:,.0f} in {goal.target_years} years"
    ))

    return {"success": True, "message": f"Goal '{goal.name}' added", "total_goals": len(user_goals)}


@app.get("/api/goals/progress", response_model=GoalsResponse)
def get_goals_progress():
    if not user_goals:
        return GoalsResponse(
            goals=[],
            total_goals=0,
            goals_on_track=0,
            goals_behind=0,
            overall_message="No goals set yet. Add a goal to start tracking progress."
        )

    result = analyze_all_goals(user_goals)

    return GoalsResponse(
        goals=[GoalProgress(**g) for g in result["goals"]],
        total_goals=result["total_goals"],
        goals_on_track=result["goals_on_track"],
        goals_behind=result["goals_behind"],
        overall_message=result["overall_message"]
    )


@app.delete("/api/goals/clear")
def clear_goals():
    user_goals.clear()
    return {"success": True, "message": "All goals cleared"}


# ── Shadow Portfolio Divergence ───────────────────────

@app.get("/api/portfolio/divergence", response_model=DivergenceResponse)
def get_divergence():
    twin = get_twin()  # reuse existing twin endpoint logic
    market = get_market_data()

    assets_dict = twin.assets.model_dump()

    # Use archetype's ideal allocation if available
    ideal_allocation = None
    archetype_label = None

    if current_user_profile.get("archetype"):
        from profiler import ARCHETYPES, Archetype
        archetype = current_user_profile["archetype"]
        if hasattr(archetype, 'value'):
            archetype = Archetype(archetype.value)
        else:
            archetype = Archetype(archetype)

        ideal_allocation = ARCHETYPES[archetype]["recommended_allocation"]
        archetype_label = ARCHETYPES[archetype]["label"]

    result = calculate_divergence(assets_dict, market.model_dump(), ideal_allocation)

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="DIVERGENCE_CHECK",
        outcome=f"Score: {result['divergence_score']}/100 — {result['urgency']}"
    ))

    return DivergenceResponse(
        divergence_score=result["divergence_score"],
        urgency=result["urgency"],
        breakdown=[AllocationBreakdown(**b) for b in result["breakdown"]],
        biggest_gap=AllocationBreakdown(**result["biggest_gap"]),
        ai_summary=result["ai_summary"],
        archetype_used=archetype_label
    )


# ── Audit Trail Intelligence ──────────────────────────

@app.get("/api/audit/summary", response_model=AuditIntelligenceSummary)
def get_audit_summary():
    if not audit_log:
        return AuditIntelligenceSummary(
            total_events=0,
            chat_queries=0,
            transactions_attempted=0,
            transactions_blocked=0,
            transactions_challenged=0,
            transactions_allowed=0,
            duress_events=0,
            highest_threat_score=0.0,
            most_common_trigger=None,
            security_rating="SECURE",
            security_score=100,
            summary_message="No activity recorded yet.",
            recommendations=["Start using FinTwin to build your security baseline."]
        )

    # Count events by type
    chat_count = sum(1 for e in audit_log if e.action == "CHAT")
    tx_attempted = sum(1 for e in audit_log if e.action == "TRANSACTION")
    tx_blocked = sum(1 for e in audit_log if e.action == "TRANSACTION" and e.outcome == "BLOCK")
    tx_challenged = sum(1 for e in audit_log if e.action == "TRANSACTION" and e.outcome == "CHALLENGE")
    tx_allowed = sum(1 for e in audit_log if e.action == "TRANSACTION" and e.outcome == "ALLOW")
    duress_count = sum(1 for e in audit_log if e.action == "DURESS_TRIGGERED")

    # Highest threat score
    threat_scores = [e.threat_score for e in audit_log if e.threat_score is not None]
    highest_threat = max(threat_scores) if threat_scores else 0.0

    # Security score calculation
    # Start at 100, deduct for bad events
    security_score = 100

    if tx_blocked > 0:
        security_score -= min(tx_blocked * 15, 40)
    if tx_challenged > 0:
        security_score -= min(tx_challenged * 5, 20)
    if duress_count > 0:
        security_score -= min(duress_count * 25, 50)
    if highest_threat > 75:
        security_score -= 10

    security_score = max(0, security_score)

    # Security rating
    if security_score >= 80:
        security_rating = "SECURE"
    elif security_score >= 50:
        security_rating = "MONITORING"
    else:
        security_rating = "ALERT"

    # Most common threat trigger across all transactions
    all_triggers = []
    for e in audit_log:
        if e.action == "TRANSACTION" and e.outcome in ["BLOCK", "CHALLENGE"]:
            # Re-derive what signals were likely high based on outcome
            all_triggers.append(e.outcome)

    most_common = None
    if tx_blocked > 0 and tx_blocked >= tx_challenged:
        most_common = "High-risk transaction attempts blocked"
    elif tx_challenged > 0:
        most_common = "Transactions requiring identity verification"
    elif duress_count > 0:
        most_common = "Coercion detection events"

    # Generate summary message
    if duress_count > 0:
        summary_message = (
            f"ALERT: {duress_count} duress event(s) detected this session. "
            f"Trusted contact has been notified. Security Score: {security_score}/100."
        )
    elif tx_blocked > 0:
        summary_message = (
            f"Brain 02 blocked {tx_blocked} suspicious transaction(s) this session. "
            f"Security Score: {security_score}/100. System is actively protecting your wealth."
        )
    elif tx_challenged > 0:
        summary_message = (
            f"Brain 02 flagged {tx_challenged} transaction(s) for identity verification. "
            f"Security Score: {security_score}/100. All challenges completed successfully."
        )
    else:
        summary_message = (
            f"All {tx_allowed} transaction(s) processed normally. "
            f"No suspicious activity detected. Security Score: {security_score}/100."
        )

    # Generate recommendations
    recommendations = []

    if duress_count > 0:
        recommendations.append(
            "Review all recent transactions and contact your bank immediately. "
            "Consider changing your real PIN and updating your trusted contact."
        )

    if tx_blocked > 0:
        recommendations.append(
            f"{tx_blocked} transaction(s) were blocked. "
            "Review the audit trail to confirm these were not legitimate transactions."
        )

    if highest_threat > 75:
        recommendations.append(
            f"A Threat Score of {highest_threat}/100 was recorded this session — "
            "review the flagged transaction details in the audit trail."
        )

    if not recommendations:
        recommendations.append(
            "No security concerns detected. "
            "Continue monitoring your audit trail regularly."
        )

    return AuditIntelligenceSummary(
        total_events=len(audit_log),
        chat_queries=chat_count,
        transactions_attempted=tx_attempted,
        transactions_blocked=tx_blocked,
        transactions_challenged=tx_challenged,
        transactions_allowed=tx_allowed,
        duress_events=duress_count,
        highest_threat_score=highest_threat,
        most_common_trigger=most_common,
        security_rating=security_rating,
        security_score=security_score,
        summary_message=summary_message,
        recommendations=recommendations
    )


# ── Market Sentiment ──────────────────────────────────

@app.get("/api/market/sentiment")
def market_sentiment():
    result = get_market_sentiment()

    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="SENTIMENT_CHECK",
        outcome=f"Market mood: {result['overall_mood']} — Score: {result['overall_score']}"
    ))

    return result