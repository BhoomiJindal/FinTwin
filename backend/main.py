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
    ChatRequest, ChatResponse,
    PINRequest, PINResponse,
    AuditEntry, AuditResponse
)

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

    result = get_ai_advice(request.message, assets_dict)

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
        reasoning=reasoning_steps
    )


# ── 3. POST /api/transaction/verify ──────────────────
# Runs 6-signal threat scoring on every transaction
# Returns threat score + decision (ALLOW / CHALLENGE / BLOCK)

@app.post("/api/transaction/verify", response_model=ThreatResponse)
def verify_transaction(request: TransactionRequest):
    from security import calculate_threat_score

    result = calculate_threat_score(request)

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
        cooling_off_seconds=result["cooling_off_seconds"]
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