from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime

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
    # Mock response — Claude integration comes in Stage 5
    mock_reply = (
        f"Based on your portfolio, you have ₹{request.assets.liquid_cash:,.0f} "
        f"in liquid cash. I'm analysing your question: '{request.message}'. "
        f"Full AI reasoning will be active in the next stage."
    )

    # Check if any shift-logic rule should trigger
    market = get_market_data()
    shift_triggered = False
    shift_rule = None

    if market.fd_rate > 7.0:
        shift_triggered = True
        shift_rule = f"FD rates at {market.fd_rate}% — above 7% threshold"

    # Log this interaction
    audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="CHAT",
        outcome=f"Query received: {request.message[:50]}"
    ))

    return ChatResponse(
        reply=mock_reply,
        shift_logic_triggered=shift_triggered,
        shift_logic_rule=shift_rule
    )


# ── 3. POST /api/transaction/verify ──────────────────
# Runs 6-signal threat scoring on every transaction
# Returns threat score + decision (ALLOW / CHALLENGE / BLOCK)

@app.post("/api/transaction/verify", response_model=ThreatResponse)
def verify_transaction(request: TransactionRequest):
    from security import calculate_threat_score
    
    result = calculate_threat_score(request)

    # Log this transaction attempt
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
        triggered_signals=result["triggered_signals"]
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