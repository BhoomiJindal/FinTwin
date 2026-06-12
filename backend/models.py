from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

# ─── ENUMS ────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TransactionType(str, Enum):
    TRANSFER = "transfer"
    INVESTMENT = "investment"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"

class DecisionAction(str, Enum):
    ALLOW = "ALLOW"
    CHALLENGE = "CHALLENGE"
    BLOCK = "BLOCK"

# ─── ASSETS ───────────────────────────────────────────

class Assets(BaseModel):
    liquid_cash: float = 0.0
    mutual_funds: float = 0.0
    gold_grams: float = 0.0
    real_estate: float = 0.0
    liabilities: float = 0.0

class MarketData(BaseModel):
    gold_price_per_gram: float = 7200.0
    repo_rate: float = 6.50
    inflation_rate: float = 5.10
    nifty_pe: float = 22.4
    fd_rate: float = 7.20

class NetWorthResponse(BaseModel):
    assets: Assets
    market_data: MarketData
    net_worth: float
    gold_value: float
    total_assets: float

# ─── TRANSACTIONS ─────────────────────────────────────

class TransactionRequest(BaseModel):
    amount: float
    transaction_type: TransactionType
    recipient: Optional[str] = None
    note: Optional[str] = None
    session_duration_ms: int        # how long user has been on page
    is_known_device: bool = True    # frontend sends this

class ThreatSignals(BaseModel):
    device_anomaly: float
    amount_anomaly: float
    time_anomaly: float
    velocity_anomaly: float
    urgency_anomaly: float
    recipient_risk: float

class ThreatResponse(BaseModel):
    threat_score: float
    action: DecisionAction
    signals: ThreatSignals
    message: Optional[str] = None
    triggered_signals: List[str]
    risk_summary: str
    cooling_off_seconds: int = 0
    ai_explanation: Optional[str] = None
    pattern_detected: Optional[PatternMatch] = None

# ─── ADVISOR / CHAT ───────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    assets: Assets

class ReasoningStep(BaseModel):
    factor: str        # what was looked at
    value: str         # the actual number
    impact: str        # how it affected the advice

class ChatResponse(BaseModel):
    reply: str
    shift_logic_triggered: bool = False
    shift_logic_rule: Optional[str] = None
    reasoning: Optional[List[ReasoningStep]] = None
    confidence: int = 100
    confidence_note: Optional[str] = None

# ─── SECURITY ─────────────────────────────────────────

class PINRequest(BaseModel):
    pin: str

class PINResponse(BaseModel):
    success: bool
    hash_stored: str                # shows the final hash (not the PIN)
    cipher_vector: List[int]        # shows the matrix transformation result

# ─── AUDIT ────────────────────────────────────────────

class AuditEntry(BaseModel):
    timestamp: str
    action: str
    threat_score: Optional[float] = None
    amount: Optional[float] = None
    outcome: str

class AuditResponse(BaseModel):
    entries: List[AuditEntry]
    total_count: int


# ─── PERSONALITY PROFILING ────────────────────────────

class RiskAppetite(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class FinancialGoalType(str, Enum):
    GROWTH = "growth"
    PRESERVATION = "preservation"
    INCOME = "income"
    TAX_SAVING = "tax_saving"

class Archetype(str, Enum):
    ACCUMULATOR = "accumulator"       # Young, growth-focused, high risk tolerance
    PROTECTOR = "protector"           # Family-first, low risk, stability focused
    OPTIMIZER = "optimizer"           # Tax and returns focused, analytical
    PRESERVER = "preserver"           # Near retirement, capital protection first

class UserProfile(BaseModel):
    age: int
    annual_income: float
    dependents: int                   # number of financial dependents
    risk_appetite: RiskAppetite
    primary_goal: FinancialGoalType
    investment_horizon_years: int     # how many years they plan to invest

class ArchetypeResponse(BaseModel):
    archetype: Archetype
    label: str                        # human readable name
    description: str                  # what this means for them
    recommended_allocation: dict      # ideal portfolio % by asset class
    advisor_style: str                # how the AI should talk to this user
    key_priorities: List[str]         # top 3 things this archetype cares about


# ─── TAX OPTIMISATION ──────────────────────────────────

class TaxRegime(str, Enum):
    OLD = "old"
    NEW = "new"

class TaxProfile(BaseModel):
    annual_income: float
    regime: TaxRegime = TaxRegime.OLD
    existing_80c: float = 0          # current 80C investments (ELSS, PPF, etc.)
    existing_80d: float = 0          # health insurance premium paid
    home_loan_interest: float = 0    # for 24(b) deduction
    nps_contribution: float = 0      # 80CCD(1B)

class TaxOptimizationResponse(BaseModel):
    tax_regime: str
    current_taxable_income: float
    current_tax_payable: float
    optimized_tax_payable: float
    total_savings: float
    recommendations: List[str]
    deduction_breakdown: dict
    reasoning: List[ReasoningStep]


# ─── PREDICTIVE THREAT PATTERNS ───────────────────────

class PatternMatch(BaseModel):
    pattern_name: str
    description: str
    confidence: int       # 0-100, how confident the pattern match is
    score_bonus: float    # additional points added to threat score