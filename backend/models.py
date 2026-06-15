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
    session_duration_ms: int
    is_known_device: bool = True
    otp_keypress_intervals_ms: Optional[List[int]] = None
    recipient_account_age_days: Optional[int] = None
    recipient_is_whitelisted: bool = False

class ThreatSignals(BaseModel):
    device_anomaly: float
    amount_anomaly: float
    time_anomaly: float
    velocity_anomaly: float
    urgency_anomaly: float
    recipient_risk: float
    otp_latency_anomaly: float = 0.0
    recipient_account_risk: float = 0.0

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
    language: Optional[str] = "en"   # "en" or "hi"

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
    language_detected: Optional[str] = "en"

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


# ─── GOAL-BASED WEALTH TRACKING ───────────────────────

class GoalCategory(str, Enum):
    HOME = "home"
    CAR = "car"
    EDUCATION = "education"
    RETIREMENT = "retirement"
    EMERGENCY_FUND = "emergency_fund"
    TRAVEL = "travel"
    OTHER = "other"

class Goal(BaseModel):
    name: str
    category: GoalCategory
    target_amount: float
    current_saved: float = 0
    target_years: float           # years remaining to achieve this goal
    monthly_contribution: float = 0   # what user currently puts toward this goal

class GoalProgress(BaseModel):
    name: str
    category: str
    target_amount: float
    current_saved: float
    progress_pct: float
    target_years: float
    required_monthly_contribution: float
    current_monthly_contribution: float
    monthly_gap: float
    projected_completion_years: float
    status: str              # "ON_TRACK", "AHEAD", "BEHIND"
    ai_status_message: str

class GoalsResponse(BaseModel):
    goals: List[GoalProgress]
    total_goals: int
    goals_on_track: int
    goals_behind: int
    overall_message: str


    # ─── SHADOW PORTFOLIO DIVERGENCE ──────────────────────

class AllocationBreakdown(BaseModel):
    asset_class: str
    current_pct: float
    ideal_pct: float
    difference: float        # positive = overweight, negative = underweight

class DivergenceResponse(BaseModel):
    divergence_score: int           # 0-100, higher = more divergence
    urgency: str                     # "LOW", "MEDIUM", "HIGH"
    breakdown: List[AllocationBreakdown]
    biggest_gap: AllocationBreakdown
    ai_summary: str
    archetype_used: Optional[str] = None


    # ─── AUDIT INTELLIGENCE ───────────────────────────────

class AuditIntelligenceSummary(BaseModel):
    total_events: int
    chat_queries: int
    transactions_attempted: int
    transactions_blocked: int
    transactions_challenged: int
    transactions_allowed: int
    duress_events: int
    highest_threat_score: float
    most_common_trigger: Optional[str]
    security_rating: str          # "SECURE", "MONITORING", "ALERT"
    security_score: int           # 0-100
    summary_message: str
    recommendations: List[str]



# ─── VELOCITY HEATMAP ─────────────────────────────────

class HourlyBucket(BaseModel):
    hour: int                    # 0-23
    hour_label: str              # "12 AM", "1 AM" etc
    transaction_count: int
    total_amount: float
    avg_threat_score: float
    risk_level: str              # "LOW", "MEDIUM", "HIGH", "NONE"

class VelocityHeatmapResponse(BaseModel):
    buckets: List[HourlyBucket]
    peak_hour: Optional[int]
    peak_hour_label: Optional[str]
    safest_hour: Optional[int]
    safest_hour_label: Optional[str]
    total_transactions: int
    insight: str


    # ─── STRESS TESTING ───────────────────────────────────

class StressScenario(str, Enum):
    MARKET_CRASH_2008 = "market_crash_2008"
    COVID_CRASH_2020 = "covid_crash_2020"
    INFLATION_SURGE = "inflation_surge"
    RUPEE_COLLAPSE = "rupee_collapse"
    REAL_ESTATE_CORRECTION = "real_estate_correction"
    RATE_HIKE_SHOCK = "rate_hike_shock"

class StressTestRequest(BaseModel):
    assets: Assets
    scenario: StressScenario

class AssetImpact(BaseModel):
    asset_class: str
    current_value: float
    stressed_value: float
    change_amount: float
    change_pct: float

class AssetStressResult(BaseModel):
    asset_class: str
    current_value: float
    stressed_value: float
    change_amount: float
    change_pct: float

class StressTestResponse(BaseModel):
    scenario: str
    scenario_description: str
    current_net_worth: float
    stressed_net_worth: float
    total_impact: float
    impact_pct: float
    asset_impacts: List[AssetStressResult]
    most_impacted_asset: str
    recovery_estimate_years: float
    severity: str
    ai_assessment: str
    protective_actions: List[str]