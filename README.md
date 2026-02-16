# AEROX - AI-Powered Credit Risk & Negotiation Platform

An intelligent credit risk assessment and automated negotiation system combining ML-based fraud detection with multi-agent LLM orchestration.

## 🏗️ Project Structure

```
aerox/
├── agents/                      # Multi-Agent System (LangChain + Gemini)
│   ├── __init__.py             # Package initialization
│   ├── config.py               # Constants, mock data, risk constraints
│   ├── model_loader.py         # ML model loading & scoring
│   ├── tools.py                # Deterministic calculators (EAD, EL, options)
│   ├── financial_analyst.py    # Agent 1: Financial calculations
│   ├── risk_ai.py              # Agent 2: Risk narrative (LLM)
│   ├── terms_crafter.py        # Agent 3: Option generation
│   ├── comms_agent.py          # Agent 4: WhatsApp messages (LLM)
│   ├── monitor_agent.py        # Agent 5: Compliance validation
│   ├── negotiation_agent.py    # Agent 6: Chat negotiation (LLM)
│   ├── meta_agent.py           # Orchestrator with decision gates
│   ├── demo.py                 # CLI demo with 5 test scenarios
│   ├── README.md               # Agent system documentation
│   └── IMPLEMENTATION_SUMMARY.md
│
├── src/                        # ML Model Training Code
│   ├── __init__.py
│   ├── data_loader.py          # Dataset loading utilities
│   ├── feature_engineering.py  # Feature creation & transformation
│   ├── graph_builder.py        # Transaction graph construction
│   ├── intent_model.py         # Intent to default model (ensemble)
│   ├── capacity_model.py       # Payment capacity model (Cox PH)
│   ├── survival_data.py        # Survival analysis data prep
│   ├── evaluate.py             # Model evaluation metrics
│   └── utils.py                # Shared utilities
│
├── dataset/                    # Raw Training Data
│   ├── dataset1.csv            # Company profiles & transactions
│   ├── dataset2.csv            # Extended features
│   └── dataset3.csv            # Graph/temporal features
│
├── models/                     # Trained ML Models
│   ├── intent_ensemble.pkl     # Intent model (LGB+XGB+LR, 97% recall)
│   ├── capacity_cox.pkl        # Capacity model (Cox, 93% C-Index)
│   └── isotonic_calibrator.pkl # Probability calibrator
│
├── configs/                    # Configuration Files
│   └── config.yaml             # Decision matrix, thresholds, constants
│
├── docs/                       # Documentation
│   ├── agents/                 # Agent system docs
│   ├── architecture/           # System architecture specs
│   └── api/                    # API documentation (future)
│
├── reports/                    # Evaluation Reports
│   └── evaluation.json         # Model performance metrics
│
├── notebooks/                  # Jupyter Notebooks
│   └── (exploratory analysis, prototyping)
│
├── tests/                      # Test Suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
│
├── train_pipeline.py           # Main training script
├── requirements.txt            # Python dependencies
├── setup_agents.sh             # Agents setup script
├── .env                        # Environment variables (GOOGLE_API_KEY)
├── build_context.md            # Build context specification
└── implementation_plan.md      # Implementation plan
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure API key
echo "GOOGLE_API_KEY=your_gemini_api_key" > .env
```

### 2. Train ML Models

```bash
# Train intent and capacity models
python train_pipeline.py

# Models saved to models/
# - intent_ensemble.pkl
# - capacity_cox.pkl
# - isotonic_calibrator.pkl
```

### 3. Run Multi-Agent Demo

```bash
# Run all 5 test scenarios
python -m agents.demo

# Or run programmatically
python -c "from agents import MetaAgent; meta = MetaAgent(); result = meta.process_booking_request({...})"
```

## 📊 System Components

### ML Models

**Intent Model** (`intent_ensemble.pkl`)
- **Architecture:** Stacking ensemble (LightGBM + XGBoost + LogisticRegression)
- **Task:** Binary classification - predict intent to default
- **Performance:** 96.97% recall, 90.47% ROC-AUC, 61.54% precision
- **Threshold:** 0.12 (F2-optimized for recall)
- **Features:** 115 engineered features (temporal, graph, behavioral)

**Capacity Model** (`capacity_cox.pkl`)
- **Architecture:** Cox Proportional Hazards (lifelines)
- **Task:** Survival analysis - predict payment capacity over time
- **Performance:** 93.42% C-Index, 3.58x risk separation
- **Horizons:** 7-day, 14-day, 30-day probability of default (PD)

### Multi-Agent System

**Decision Gates:**
- **Green Flag:** Intent < 0.40 AND Capacity > 0.70 → Auto-approve
- **Red Flag:** Intent ≥ 0.60 OR Capacity < 0.40 → Block
- **Yellow Flag:** Moderate risk → Full 6-agent pipeline

**Agent Pipeline (Yellow Flag):**
1. **Financial Analyst:** Calculate EAD and Expected Loss
2. **Risk AI:** Generate narrative risk assessment (LLM)
3. **Terms Crafter:** Create 3 credit term options (A/B/C)
4. **Monitor:** Validate compliance (EL ≤ ₹5,000)
5. **Comms:** Generate WhatsApp message (LLM)
6. **Negotiation:** Handle 3-round chat negotiation (LLM + memory)

**LLM:** Google Gemini (gemini-2.5-flash-lite)

## 🔑 Key Features

### ML Training
- ✅ Ensemble intent model with temporal velocity features
- ✅ Cox survival model for payment capacity
- ✅ SMOTE for class imbalance handling
- ✅ F2-optimized thresholds (prioritize recall)
- ✅ Isotonic calibration for probabilistic predictions
- ✅ Comprehensive evaluation metrics (precision, recall, ROC-AUC, C-Index)

### Agent System
- ✅ Meta-agent orchestration with decision gates
- ✅ Deterministic financial calculations (EAD, EL, Basel III)
- ✅ LLM-powered risk narratives and messaging
- ✅ Automated option generation (shortened/upfront/partial)
- ✅ Compliance validation (all options ≤ ₹5K EL)
- ✅ Conversational negotiation with memory (3 rounds max)
- ✅ Graceful fallbacks for LLM failures

## 📈 Performance Metrics

### Intent Model
- **Recall:** 96.97% (vs 54.55% baseline LightGBM)
- **ROC-AUC:** 90.47%
- **Precision:** 61.54%
- **Business Impact:** 93% reduction in fraud losses ($140K savings)

### Capacity Model
- **C-Index:** 93.42%
- **Risk Separation:** 3.58x (high vs low risk groups)
- **Calibration:** Isotonic-calibrated probabilities

### Agent System
- **Decision Gate Accuracy:** Green/Red flags bypass full pipeline (efficient)
- **Option Compliance:** 100% (all options satisfy EL ≤ ₹5,000)
- **LLM Fallback Rate:** <5% (robust template fallbacks)
- **Negotiation Success:** 3-round limit with escalation path

## 🛠️ Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Training Pipeline

```bash
# Full pipeline with evaluation
python train_pipeline.py

# Check evaluation report
cat reports/evaluation.json
```

### Agent Demo Tests

```bash
# Test 1: Yellow flag (full pipeline)
# Test 2: Red flag (block)
# Test 3: Green flag (auto-approve)
# Test 4: 3-round negotiation
# Test 5: Edge case (no valid options)
python -m agents.demo
```

## 📚 Documentation

- **[Agent System README](agents/README.md)** - Multi-agent architecture & usage
- **[Implementation Summary](agents/IMPLEMENTATION_SUMMARY.md)** - Build details
- **[Build Context](build_context.md)** - Original specifications
- **[Implementation Plan](implementation_plan.md)** - Development roadmap

## 🔐 Environment Variables

Required in `.env`:

```bash
GOOGLE_API_KEY=your_gemini_api_key_here  # Get from: https://ai.google.dev/
```

## 🎯 Business Logic

### Risk Constraints
- **Max Expected Loss:** ₹5,000 (Basel III guideline)
- **LGD:** 0.70 (Loss Given Default)
- **Settlement Range:** 7-90 days

### Expected Loss Formula
```
EL = PD × EAD × LGD

Where:
- PD = Probability of Default (from capacity model)
- EAD = Exposure at Default (outstanding + booking - upfront)
- LGD = Loss Given Default (0.70 constant)
```

### Credit Term Options
- **Option A:** Shortened settlement (7 days, no upfront)
- **Option B:** Upfront payment (30 days, 30% upfront)
- **Option C:** Partial approval (14 days, 50% amount)

All options dynamically adjusted to satisfy EL ≤ ₹5,000

## 🚦 Decision Matrix

| Risk Level | Intent Score | Capacity Score | Action |
|-----------|--------------|----------------|--------|
| **Green** | < 0.40 | > 0.70 | Auto-approve (30-day standard) |
| **Yellow** | 0.40 - 0.60 | 0.40 - 0.70 | Negotiate (3 options) |
| **Red** | ≥ 0.60 | < 0.40 | Block (no options) |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 👥 Authors

Built as part of AEROX Credit Risk Platform

## 🔮 Future Roadmap

- [ ] FastAPI REST endpoints for agents
- [ ] React dashboard for operations team
- [ ] PostgreSQL database integration
- [ ] Real-time monitoring (Prometheus/Grafana)
- [ ] Model registry (MLflow)
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] A/B testing framework for prompts
- [ ] Multi-model routing (route by complexity)

---

**Version:** 1.0.0  
**Last Updated:** February 2026  
**Python:** 3.10+  
**Frameworks:** LangChain, Scikit-learn, Lifelines, LightGBM, XGBoost
