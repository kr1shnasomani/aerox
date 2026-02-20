# AEROX - AI Knowledge Base

## System Overview

**AEROX** (Adaptive Exposure & Risk Orchestrator) is a next-generation B2B travel fraud prevention system. Instead of blocking risky transactions, it uses causal AI, survival modeling, and economic optimization to **negotiate safe credit terms in real-time**.

**Core Philosophy**: Don't block risk. Price it, predict it, and negotiate it causally.

**Key Innovation**: Separate **fraud intent** from **credit capacity** — never negotiate with fraudsters, only with honest agencies facing temporary liquidity stress.

---

## Architecture: 5-Layer Pipeline

```
Layer 0 → Layer 1 → Layer 2 → Decision Gate → Layer 3 → Layer 4
(10ms)    (30ms)    (40ms)                     (30ms)    (1-3s async)
```

| Layer | Name | Purpose | Output |
|-------|------|---------|--------|
| **Layer 0** | Access Intelligence | Cybersecurity: session validation, ATO detection | Session Risk Score |
| **Layer 1** | Causal Network Intelligence | Fraud intent detection using Causal GNN + do-calculus | **Intent Score** (0-1) |
| **Layer 2** | Survival-Based Credit Oracle | Cox PH model: when default occurs (not just if) | **Capacity Score** (0-1) + PD(7d/14d/30d) |
| **Layer 3** | Economic Loss Optimizer | SQP constrained optimization: EL = PD × EAD × LGD ≤ ₹5,000 | 3 Credit Term Options |
| **Layer 4** | Agentic Negotiation Engine | LLM-powered multi-agent WhatsApp messaging | Personalized 3-option message |

**Total**: 110ms sync decision + 1-3s async messaging

---

## Decision Matrix (Intent vs Capacity)

| Intent Score | Capacity Score | Decision | Action |
|-------------|---------------|----------|--------|
| > 0.60 | Any | **BLOCK** | Hard block, fraud detected, never negotiate |
| < 0.40 | > 0.70 | **AUTO-APPROVE** | Standard 30-day terms |
| < 0.40 | 0.40 - 0.70 | **NEGOTIATE** | Present 3 term options |
| < 0.40 | < 0.40 | **MANUAL REVIEW** | Human assessment required |

**Thresholds** (from `configs/config.yaml`):
- `block_intent_threshold`: 0.60
- `approve_intent_threshold`: 0.40
- `approve_capacity_threshold`: 0.70

---

## Business Logic

### Expected Loss Formula (Basel III)
```
EL = PD × EAD × LGD

PD  = Probability of Default (from Layer 2, time-dependent)
EAD = Exposure at Default = Outstanding + Booking - Upfront
LGD = Loss Given Default = 0.70 (constant)

Constraint: EL ≤ ₹5,000 (max acceptable expected loss)
```

### 3-Option Generation Rules
| Option | Type | Settlement | Upfront | Amount | Friction |
|--------|------|-----------|---------|--------|----------|
| A | Shortened settlement | 7 days | ₹0 | 100% | 4.0 |
| B | Upfront payment | 30 days | Calculated | 100% | 7.0 |
| C | Partial approval | 14 days | ₹0 | 50% | 8.0+ |

---

## What's Built

### ML Models (Trained & Ready)
| Model | File | Architecture | Performance |
|-------|------|-------------|-------------|
| Intent (Fraud) | `models/intent_ensemble.pkl` | Stacking: LightGBM + XGBoost → LogisticRegression | 96.97% recall, 90.47% AUC |
| Capacity (Credit) | `models/capacity_cox.pkl` | Cox Proportional Hazards (lifelines) | 93.42% C-Index |
| Calibrator | `models/isotonic_calibrator.pkl` | Isotonic regression | Well-calibrated PDs |

### 6 Specialized Agents
| # | Agent | File | Type | Purpose |
|---|-------|------|------|---------|
| 1 | Financial Analyst | `agents/financial_analyst.py` | Deterministic | EAD & EL calculations |
| 2 | Risk AI | `agents/risk_ai.py` | LLM (Gemini) | Risk narrative with structured output |
| 3 | Terms Crafter | `agents/terms_crafter.py` | Deterministic | Generate 3 compliant options |
| 4 | Comms Agent | `agents/comms_agent.py` | LLM (Gemini) | WhatsApp message generation |
| 5 | Monitor | `agents/monitor_agent.py` | Deterministic | Compliance validation |
| 6 | Negotiation | `agents/negotiation_agent.py` | LLM + Memory | 3-round interactive chat |

**Orchestrator**: `agents/meta_agent.py` — routes through decision gates → runs pipeline

### Datasets
| File | Size | Records | Content |
|------|------|---------|---------|
| `dataset/dataset1.csv` | 690 KB | 1,000 companies | Profiles, financials, risk flags |
| `dataset/dataset2.csv` | 13.5 MB | Extended | Payment behavior, GST, CIBIL data |
| `dataset/dataset3.csv` | 10.2 MB | Graph/temporal | Transaction graphs, velocity |

### Training Pipeline
- `src/data_loader.py` — Dataset loading & validation
- `src/feature_engineering.py` — 115 engineered features (RobustScaler, log-transform, SMOTE)
- `src/graph_builder.py` — Heterogeneous graph construction
- `src/intent_model.py` — Ensemble + GNN model training
- `src/capacity_model.py` — Cox PH survival model training
- `src/evaluate.py` — Metrics (precision, recall, C-Index, calibration)
- `train_pipeline.py` — Main training orchestrator

### FastAPI REST API (`api/`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/booking/process` | POST | Full AEROX pipeline processing |
| `/api/negotiate` | POST | 1 round of negotiation chat |
| `/api/negotiate/reset` | POST | Reset negotiation memory |
| `/api/scenarios` | GET | 3 pre-built test scenarios |
| `/api/agencies` | GET | Paginated agency list (filters, search) |
| `/api/agencies/{id}` | GET | Single agency detail |
| `/api/config` | GET | Decision thresholds |
| `/api/stats` | GET | Aggregate statistics |

### React Frontend (`frontend/`)
| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/` | Risk quadrant chart, decision distribution, metrics |
| Process Booking | `/process` | **Main demo** — form + animated pipeline + decision + options + WhatsApp preview |
| Agencies | `/agencies` | Searchable/filterable/paginated agency table |
| Agency Detail | `/agencies/:id` | Agency profile with risk gauges & metrics |
| Negotiate | `/negotiate` | Interactive 3-round chat with counter-offers |

**Frontend Tech**: React 18 + Vite + TypeScript + Tailwind CSS + Framer Motion + Recharts

---

## What's NOT Built

| Feature | Status | Notes |
|---------|--------|-------|
| Layer 0 (Cybersecurity) | Simulated | Hardcoded "clean session" in frontend pipeline |
| Real GNN Model | Partial | Training code exists, uses ensemble fallback |
| PostgreSQL Database | ❌ | Uses CSV datasets + mock data |
| Real WhatsApp Integration | ❌ | Message generation only (preview in UI) |
| Account Aggregator API | ❌ | Simulated with mock external data |
| GST/CIBIL Integration | ❌ | Simulated with mock values |
| MLflow Model Registry | ❌ | Models stored as .pkl files |
| CI/CD Pipeline | ❌ | Manual deployment |
| Prometheus/Grafana | ❌ | No real-time monitoring |

---

## How to Run

### Prerequisites
- Python 3.10+ | Node.js 18+
- Google API key (optional — falls back to templates)

### Backend (FastAPI)
```bash
cd aerox
pip install -r requirements.txt
pip install fastapi uvicorn
uvicorn api.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### Frontend (React)
```bash
cd aerox/frontend
npm install
npm run dev
```
Opens at: http://localhost:5173

### CLI Demo (no API needed)
```bash
python -m agents.demo
```

### Environment
```bash
# .env (optional)
GOOGLE_API_KEY=your_gemini_api_key
```

---

## Test Scenarios

| Scenario | Company ID | Intent | Capacity | Expected Decision |
|----------|-----------|--------|----------|-------------------|
| Green Flag | IN-TRV-000123 | 0.15 | 0.85 | AUTO-APPROVE (30-day terms) |
| Yellow Flag | IN-TRV-000567 | 0.32 | 0.55 | NEGOTIATE (3 options) |
| Red Flag | IN-TRV-000999 | 0.85 | 0.25 | BLOCK (fraud detected) |

---

## Key File Map

```
aerox/
├── agents/                     # Multi-Agent System
│   ├── meta_agent.py           # Orchestrator (MAIN ENTRY POINT)
│   ├── financial_analyst.py    # Agent 1: EAD/EL calculations
│   ├── risk_ai.py              # Agent 2: LLM risk narrative
│   ├── terms_crafter.py        # Agent 3: 3-option generation
│   ├── comms_agent.py          # Agent 4: WhatsApp messages
│   ├── monitor_agent.py        # Agent 5: Compliance validation
│   ├── negotiation_agent.py    # Agent 6: 3-round chat
│   ├── config.py               # Thresholds, mock data, test scenarios
│   ├── tools.py                # EAD/EL calculators, option gen
│   ├── model_loader.py         # ML model loading + scoring
│   └── demo.py                 # CLI demo (5 scenarios)
├── api/                        # FastAPI REST API
│   ├── main.py                 # All endpoints + CORS
│   ├── models.py               # Pydantic schemas
│   └── dependencies.py         # MetaAgent singleton
├── frontend/                   # React Frontend
│   └── src/
│       ├── pages/              # 5 pages (Dashboard, Process, Agencies, Detail, Negotiate)
│       ├── components/         # Pipeline, Decision, Charts, Negotiation, Layout
│       ├── api/client.ts       # Axios API wrapper
│       └── types/index.ts      # TypeScript interfaces
├── src/                        # ML Training Pipeline
│   ├── data_loader.py
│   ├── feature_engineering.py
│   ├── intent_model.py
│   └── capacity_model.py
├── models/                     # Trained models (.pkl)
├── dataset/                    # CSV datasets (1000 companies)
├── configs/config.yaml         # All configuration
├── train_pipeline.py           # Training orchestrator
└── requirements.txt            # Python dependencies
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| ML - Intent | LightGBM + XGBoost + Logistic Regression (Stacking Ensemble) |
| ML - Capacity | Cox Proportional Hazards (lifelines) |
| ML - Features | 115 features, RobustScaler, SMOTE, F2 threshold |
| Agents | LangChain + Google Gemini (gemini-2.5-flash-lite) |
| API | FastAPI + Uvicorn + Pydantic v2 |
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS v4 |
| Animations | Framer Motion |
| Charts | Recharts (scatter, pie) |
| HTTP Client | Axios |
| Icons | Lucide React |
| Data | Pandas (CSV datasets, 1000 companies) |

---

## Business Impact (Projected)

- **$4.2M** revenue preserved annually (30% declined bookings recovered)
- **35%** chargeback reduction ($1.8M saved)
- **85%** automation rate
- **110ms** decision latency (vs 2-6 hours manual)
- **912% ROI**, 1.2-month payback
