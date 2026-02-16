# AEROX Multi-Agent Negotiation System

A production-ready LangChain-based multi-agent system for automated credit negotiation using Google Gemini and ML-driven risk scoring.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        META-AGENT                            │
│              (Orchestrator + Decision Gates)                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │   ML MODEL LOADER   │
        │  (Intent + Capacity) │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │   DECISION GATES    │
        │  Green│Yellow│Red   │
        └─┬────────┬────────┬─┘
          │        │        │
    GREEN│  YELLOW│   RED  │
    ┌─────▼──┐ ┌──▼──────┐ │
    │Auto-   │ │Full     │ │
    │Approve │ │Pipeline │ │Block
    └────────┘ └──┬──────┘ │
                  │         │
         ┌────────┴─────┐   │
         │  6 AGENTS    │   │
         │              │   │
         │  1. Financial│   │
         │  2. Risk AI  │   │
         │  3. Terms    │   │
         │  4. Comms    │   │
         │  5. Monitor  │   │
         │  6. Negotiate│   │
         └──────────────┘   │
```

## 🤖 Agent Details

### Meta-Agent (`meta_agent.py`)
**Role:** Orchestrator  
**Function:** Routes requests through decision gates, coordinates all 6 agents  
**Logic:**
- Green flag (Intent < 0.40 & Capacity > 0.70) → Auto-approve
- Red flag (Intent ≥ 0.60 OR Capacity < 0.40) → Block
- Yellow flag → Full negotiation pipeline (Agents 1-6)

### Agent 1: Financial Analyst (`financial_analyst.py`)
**Type:** Deterministic + LLM verification  
**Function:** Calculates Exposure at Default (EAD) and Expected Loss (EL)  
**Formula:** `EL = PD × EAD × LGD`  
**Output:** Total exposure, baseline EL, risk appetite breach status

### Agent 2: Risk AI (`risk_ai.py`)
**Type:** LLM (Google Gemini)  
**Function:** Narrative risk assessment with structured output  
**Features:**
- PydanticOutputParser for structured results
- Analyzes ML scores, company data, external data
- Generates risk summary + key factors + mitigating factors + recommendation
- Fallback to template if LLM fails

### Agent 3: Terms Crafter (`terms_crafter.py`)
**Type:** Deterministic  
**Function:** Generate 3 credit term options  
**Options:**
- **A:** Shortened settlement (7 days, no upfront)
- **B:** Partial upfront (30% upfront, 30 days)
- **C:** Partial approval (50% amount, 14 days)
  
**Constraint:** All options must satisfy EL ≤ ₹5,000

### Agent 4: Comms Agent (`comms_agent.py`)
**Type:** LLM (Google Gemini, creative)  
**Function:** Generate WhatsApp messages  
**Features:**
- Temperature=0.7 for creativity
- Formats 3 options with emojis (⚡ 📅 💰)
- 150-200 word guideline
- JSON output with subject, body, CTA buttons
- Fallback template if LLM fails

### Agent 5: Monitor Agent (`monitor_agent.py`)
**Type:** Deterministic  
**Function:** Validate compliance of all options  
**Checks:**
- EL ≤ ₹5,000
- Upfront ≤ approved amount
- Settlement days in [7, 90]
  
**Output:** Compliant flag, violations list

### Agent 6: Negotiation Agent (`negotiation_agent.py`)
**Type:** LLM (Google Gemini) + Conversation Memory  
**Function:** Handle 3-round chat negotiation  
**Features:**
- `ConversationBufferMemory` for chat history
- Dynamic offer adjustment (blend days, upfront)
- Real-time EL calculation
- Round 3: Escalate if no agreement
- Fallback to simple counter-offer if LLM fails

## 📊 ML Models

### Intent Model (`intent_ensemble.pkl`)
- **Architecture:** Stacking ensemble (LightGBM + XGBoost + LogisticRegression)
- **Task:** Binary classification (intent to default)
- **Performance:** 96.97% recall, ROC-AUC 90.47%
- **Threshold:** 0.12 (F2-optimized)

### Capacity Model (`capacity_cox.pkl`)
- **Architecture:** Cox Proportional Hazards (lifelines)
- **Task:** Survival analysis (payment capacity over time)
- **Performance:** C-Index 93.42%, 3.58x risk separation
- **Horizons:** 7-day, 14-day, 30-day PD values

## 🚀 Quick Start

### 1. Environment Setup

```bash
cd aerox

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp agents/.env.example agents/.env

# Add your Google API key
echo "GOOGLE_API_KEY=your_key_here" > agents/.env
```

### 2. Run Demo

```bash
# Activate virtual environment (if exists)
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Run all 5 test scenarios
python -m agents.demo
```

### 3. Expected Output

```
╔════════════════════════════════════════╗
║      AEROX MULTI-AGENT SYSTEM DEMO     ║
╚════════════════════════════════════════╝

TEST 1: YELLOW FLAG - Full Negotiation Pipeline
[Meta-Agent] Processing booking: IN-TRV-000567
  Intent: 0.450, Capacity: 0.550, Category: YELLOW
[Financial Analyst] Total Exposure: ₹80,000
[Risk AI] Risk Summary: Moderate risk profile...
[Terms Crafter] Generated 3 options
[Monitor Agent] ✓ All 3 options compliant
[Comms Agent] Message subject: Credit Approval: 3...

TEST 2: RED FLAG - Block Decision
[Meta-Agent] ✗ RED FLAG → Blocking
Decision: BLOCKED
Reason: High intent score (0.75)

TEST 3: GREEN FLAG - Auto-Approval
[Meta-Agent] ✓ GREEN FLAG → Auto-approving
Decision: APPROVED
Amount: ₹30,000 (30-day standard terms)

TEST 4: 3-ROUND NEGOTIATION CHAT
Customer: These options are too restrictive...
Agent: I understand. How about ₹8,000 upfront...

TEST 5: EDGE CASE - No Valid Options
[Meta-Agent] ✗ Blocked - all options exceed EL...
```

## 🧪 Test Scenarios

| Test | Scenario | Expected Decision | Agents Used |
|------|----------|-------------------|-------------|
| 1    | Yellow flag (Intent=0.45, Capacity=0.55) | NEGOTIATE | All 6 |
| 2    | Red flag (Intent≥0.60) | BLOCKED | Meta only |
| 3    | Green flag (Intent<0.40, Capacity>0.70) | APPROVED | Meta only |
| 4    | 3-round negotiation chat | Counter-offers | Agent 6 |
| 5    | High exposure (EL always > ₹5K) | BLOCKED | 1-5 |

## 📂 File Structure

```
agents/
├── __init__.py              # Package exports
├── .env.example             # API key template
├── config.py                # Constants, mock data, risk constraints
├── model_loader.py          # Load intent+capacity models
├── tools.py                 # Deterministic functions (EAD, EL, options)
├── meta_agent.py            # Orchestrator
├── financial_analyst.py     # Agent 1: Financial calculations
├── risk_ai.py               # Agent 2: Risk narrative
├── terms_crafter.py         # Agent 3: Option generation
├── comms_agent.py           # Agent 4: Message generation
├── monitor_agent.py         # Agent 5: Compliance validation
├── negotiation_agent.py     # Agent 6: Chat negotiation
└── demo.py                  # CLI demo with 5 tests
```

## 🔧 Configuration

### Risk Constraints (`config.py`)

```python
RISK_CONSTRAINTS = {
    'max_expected_loss': 5000,  # ₹5,000 (Basel III)
    'min_settlement_days': 7,
    'max_settlement_days': 90,
    'lgd': 0.70
}
```

### Decision Matrix Thresholds

Loaded from `configs/config.yaml`:

```yaml
decision_matrix:
  block:
    intent_score: 0.60
  approve:
    intent_score: 0.40
    capacity_score: 0.70
```

## 🔑 API Keys

**Required:** Google Gemini API key

Get from: https://ai.google.dev/

**Set in `.env`:**
```bash
GOOGLE_API_KEY=your_actual_api_key_here
```

## 🛠️ Troubleshooting

### Models Not Found
If `intent_ensemble.pkl` or `capacity_cox.pkl` are missing, the system falls back to mock scores defined in `config.py`. To use real models:

```bash
# Ensure models exist
ls models/intent_ensemble.pkl
ls models/capacity_cox.pkl

# If missing, train models first
python train_intent.py
python train_capacity.py
```

### LLM Failures
All LLM-based agents (Risk AI, Comms, Negotiation) have fallback templates. If Gemini API calls fail:
- Check API key in `.env`
- Check internet connection
- Verify API quota: https://console.cloud.google.com

### Negotiation Memory Issues
Reset conversation memory between test runs:

```python
from agents import MetaAgent
meta = MetaAgent()
meta.reset_negotiation_memory()
```

## 📊 Business Logic

### Expected Loss Formula
```
EL = PD × EAD × LGD

Where:
- PD = Probability of Default (from capacity model)
- EAD = Exposure at Default (current_outstanding + booking_amount - upfront)
- LGD = Loss Given Default (0.70 constant per Basel III)
```

### Option Friction Scores
```python
friction_score = (upfront_ratio * 5) + (30 - settlement_days) / 3

Lower score = Lower friction = Better customer experience
```

## 🎯 Production Considerations

### 1. Model Serving
- Current: Pickle files loaded at startup
- Production: Use model registry (MLflow, Sagemaker, Vertex AI)
- Add model versioning and A/B testing

### 2. Database Integration
Replace mock data in `config.py` with real DB queries:
```python
# Current: MOCK_COMPANY_DATA
# Production: query from PostgreSQL/MySQL
company_data = db.query("SELECT * FROM companies WHERE id = ?", company_id)
```

### 3. Message Queue
For async processing:
```python
# Use RabbitMQ/Kafka for booking requests
@celery.task
def process_booking(booking_request):
    meta = MetaAgent()
    return meta.process_booking_request(booking_request)
```

### 4. Monitoring
Add observability:
```python
import sentry_sdk
from prometheus_client import Counter

booking_counter = Counter('bookings_processed', 'Bookings processed', ['decision'])
booking_counter.labels(decision='APPROVED').inc()
```

### 5. Rate Limiting
Gemini API has rate limits:
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=60, period=60)
def call_gemini(prompt):
    return llm.invoke(prompt)
```

## 📝 License

MIT License - see parent project LICENSE file

## 👥 Contributors

Built as part of AEROX Credit Risk Platform

---

**Last Updated:** February 2026  
**Version:** 0.1.0  
**Dependencies:** LangChain 0.1+, Google Gemini API, Python 3.10+
