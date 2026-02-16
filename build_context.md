## Prompt for Antigravity - AEROX Multi-Agent System (LangChain Only)

```
# AEROX Multi-Agent Negotiation System - LangChain Implementation

## Goal
Build a working LangChain multi-agent system with 1 Meta-Agent orchestrator and 6 specialized agents. Use mock data (no database connections). Focus ONLY on getting the LangChain agent workflow operational.

---

## Architecture Overview

```
Meta-Agent (Orchestrator)
    ↓
    ├─→ Financial Analyst (computes EAD, EL)
    ├─→ Risk AI (queries Intent/Capacity scores)
    ├─→ Terms Crafter (runs optimization, generates 3 options)
    ├─→ Comms Agent (LLM message generation)
    ├─→ Monitor Agent (tracks compliance)
    └─→ Negotiation Agent (chat-based, conditional)
```

---

## Input Data (Mock - Hardcoded)

```python
# Mock booking request
booking_request = {
    "company_id": "IN-TRV-000567",
    "company_name": "MediumRisk Agency",
    "booking_amount": 50000,
    "current_outstanding": 45000,
    "credit_limit": 80000,
    "route": "Chennai-Dubai",
    "booking_date": "2026-02-15"
}

# Mock ML model outputs (pre-computed)
ml_scores = {
    "intent_score": 0.32,  # Low fraud
    "capacity_score": 0.55,  # Moderate credit
    "pd_7d": 0.02,  # 2% default risk at 7 days
    "pd_14d": 0.08,  # 8% at 14 days
    "pd_30d": 0.15,  # 15% at 30 days
    "risk_category": "yellow"
}

# Mock company profile
company_data = {
    "segment": "small_medium",
    "credit_utilization": 0.87,
    "on_time_payment_rate": 0.78,
    "avg_late_payment_days": 12,
    "chargeback_rate": 0.023,
    "business_age_months": 36,
    "years_with_platform": 2.1
}

# Mock external data
external_data = {
    "gst_revenue_trend": -0.15,  # Declining 15%
    "gst_filing_status": "delayed",
    "bank_balance": 185000,
    "cash_flow_7d": -45000,  # Negative
    "cibil_score": 6.4,
    "cibil_trend": -0.8,
    "news_sentiment_score": -0.3
}

# Risk constraints
risk_constraints = {
    "max_expected_loss": 5000,  # INR
    "lgd": 0.70  # Loss Given Default
}
```

---

## Agent 1: Financial Analyst

**Role**: Calculate Exposure-at-Default (EAD) and Expected Loss (EL)

**Tools Needed**:
```python
def calculate_ead(outstanding, booking_amount, upfront=0):
    """Calculate Exposure at Default"""
    return outstanding + booking_amount - upfront

def calculate_expected_loss(pd, ead, lgd):
    """Basel III Expected Loss Formula"""
    return pd * ead * lgd
```

**Input**: Booking request + ML scores
**Output**: 
```python
{
    "total_exposure": 95000,
    "baseline_el_30d": 9975,  # 0.15 × 95000 × 0.70
    "exceeds_risk_appetite": True,
    "exceeds_by": 4975
}
```

---

## Agent 2: Risk AI

**Role**: Interpret Intent/Capacity scores and provide risk summary

**Input**: ML scores + company data + external data
**Output**:
```python
{
    "risk_summary": "Low fraud probability (32%) but declining credit capacity. Cash flow stress evident from negative 7-day cash flow and declining GST revenue. Safe for short-term credit (7 days), risky for 30+ days.",
    "key_risk_factors": [
        "Revenue declining 15% (GST trend)",
        "Negative cash flow ₹45K last week",
        "Late payments averaging 12 days",
        "CIBIL declining to 6.4 from 7.2"
    ],
    "mitigating_factors": [
        "Low fraud intent (0.32)",
        "2.1 year relationship",
        "78% on-time payment rate",
        "Low chargeback rate (2.3%)"
    ],
    "recommendation": "Offer shortened settlement (7-day) to reduce exposure window"
}
```

---

## Agent 3: Terms Crafter (Most Complex)

**Role**: Generate 3 mathematically valid options that satisfy EL ≤ ₹5,000

**Algorithm**:
```python
def generate_options(exposure, pd_7d, pd_14d, pd_30d, lgd, max_el):
    options = []
    
    # Option A: Shortened Settlement
    el_7d = pd_7d * exposure * lgd
    if el_7d <= max_el:
        options.append({
            "type": "shortened_settlement",
            "settlement_days": 7,
            "upfront": 0,
            "approved_amount": booking_amount,
            "expected_loss": el_7d,
            "friction_score": 4.0
        })
    
    # Option B: Upfront Payment
    # Solve: pd_30d × (exposure - upfront) × lgd ≤ max_el
    # upfront = exposure - (max_el / (pd_30d × lgd))
    required_upfront = exposure - (max_el / (pd_30d * lgd))
    if required_upfront > 0 and required_upfront < booking_amount:
        options.append({
            "type": "upfront_payment",
            "settlement_days": 30,
            "upfront": round(required_upfront, 0),
            "approved_amount": booking_amount,
            "expected_loss": round(pd_30d * (exposure - required_upfront) * lgd, 0),
            "friction_score": 7.0
        })
    
    # Option C: Partial Approval with moderate settlement
    # Try 14-day settlement with reduced booking
    for partial_pct in [0.5, 0.4, 0.3]:
        partial_booking = booking_amount * partial_pct
        partial_exposure = outstanding + partial_booking
        el_partial = pd_14d * partial_exposure * lgd
        if el_partial <= max_el:
            options.append({
                "type": "partial_approval",
                "settlement_days": 14,
                "upfront": 0,
                "approved_amount": partial_booking,
                "expected_loss": el_partial,
                "friction_score": 8.0 + (1 - partial_pct) * 2
            })
            break
    
    return sorted(options, key=lambda x: x["friction_score"])[:3]
```

**Input**: Financial Analyst output + Risk constraints
**Output**:
```python
[
    {
        "option_id": "A",
        "type": "shortened_settlement",
        "settlement_days": 7,
        "upfront_amount": 0,
        "approved_amount": 50000,
        "expected_loss": 1330,
        "friction_score": 4.0,
        "description": "Settle within 7 days"
    },
    {
        "option_id": "B",
        "type": "upfront_payment",
        "settlement_days": 30,
        "upfront_amount": 25000,
        "approved_amount": 50000,
        "expected_loss": 4935,
        "friction_score": 7.0,
        "description": "Pay ₹25,000 upfront, ₹25,000 in 30 days"
    },
    {
        "option_id": "C",
        "type": "partial_approval",
        "settlement_days": 14,
        "upfront_amount": 0,
        "approved_amount": 20000,
        "expected_loss": 3640,
        "friction_score": 8.5,
        "description": "Approve ₹20,000 with 14-day settlement"
    }
]
```

---

## Agent 4: Comms Agent

**Role**: Generate natural language WhatsApp message using LLM

**LLM Prompt**:
```python
prompt = f"""
You are AEROX's customer communication specialist. Write a professional WhatsApp message.

Company: {company_name}
Situation: Requested ₹{booking_amount}, but exceeds credit limit by ₹{exceeds_by}

Risk Summary: {risk_summary}

3 Options Available:
{json.dumps(options, indent=2)}

Guidelines:
- Empathetic, professional tone
- Acknowledge their 2+ year relationship
- Present all 3 options clearly with labels A/B/C
- Recommend Option A (lowest friction)
- Clear CTA: Reply A, B, or C
- 150-200 words max

Output format:
Subject: [subject line]
Body: [message text]
"""
```

**Output**:
```python
{
    "subject": "Credit Options for ₹50,000 Booking",
    "body": "Hi MediumRisk Agency,\n\nYour ₹50,000 booking (Chennai → Dubai) is ready! However, it exceeds your available credit by ₹15,000.\n\nWe've reviewed your account - you've been a valued partner for 2+ years with strong payment history. We can approve this with one of these options:\n\n**Option A** ⚡ Recommended\nSettle within **7 days** (no upfront)\n→ Full ₹50,000 approved\n\n**Option B** 📅 Standard timeline\nPay **₹25,000 upfront**\n→ Remaining ₹25,000 in 30 days\n\n**Option C** 💰 Reduced amount\nApprove **₹20,000** with 14-day settlement\n→ Request more credit later\n\nReply **A**, **B**, or **C** to proceed.\nNeed help? Click 'Support' below.\n\n— AEROX Credit Team",
    "cta_buttons": ["Select A", "Select B", "Select C", "Support"]
}
```

---

## Agent 5: Monitor Agent

**Role**: Ensure all options satisfy compliance rules

**Checks**:
```python
def validate_compliance(options, max_el):
    violations = []
    
    for opt in options:
        # Check 1: Expected Loss within limit
        if opt["expected_loss"] > max_el:
            violations.append(f"Option {opt['option_id']}: EL {opt['expected_loss']} exceeds {max_el}")
        
        # Check 2: Upfront not exceeding booking amount
        if opt.get("upfront_amount", 0) > opt["approved_amount"]:
            violations.append(f"Option {opt['option_id']}: Upfront exceeds approved amount")
        
        # Check 3: Settlement days reasonable (7-90 days)
        if not (7 <= opt["settlement_days"] <= 90):
            violations.append(f"Option {opt['option_id']}: Settlement days {opt['settlement_days']} out of range")
    
    return {
        "compliant": len(violations) == 0,
        "violations": violations,
        "options_count": len(options)
    }
```

**Output**:
```python
{
    "compliant": True,
    "violations": [],
    "options_count": 3,
    "all_checks_passed": True
}
```

---

## Agent 6: Negotiation Agent (Conditional)

**Role**: Handle chat-based negotiation if user clicks "Support"

**LLM Prompt with Memory**:
```python
negotiation_prompt = f"""
You are AEROX's credit negotiation specialist. A customer declined initial options and wants to negotiate.

Context:
- Company: {company_name}
- Booking: ₹{booking_amount}
- Initial Options Offered: {options}
- Risk Constraint: Expected Loss must be ≤ ₹{max_el}

Conversation History:
{conversation_history}

Customer's Latest Message: {user_message}

Your Task:
1. Acknowledge their concern
2. Propose a modified offer (blend options, adjust amounts)
3. Calculate new Expected Loss (must be ≤ ₹{max_el})
4. If no valid offer exists, escalate to manual review

Rules:
- Max 3 negotiation rounds (this is round {round_number})
- Cannot approve if EL > ₹{max_el}
- Cannot change Intent/Capacity scores
- Must show calculation: "EL = PD × Exposure × LGD = ..."

Output JSON:
{{
    "response": "your message",
    "offer": {{"upfront": X, "days": Y}},
    "expected_loss": Z,
    "escalate": false
}}
"""
```

**Example Flow**:
```python
# Round 1
User: "Can't do 7 days, and ₹25K upfront is too much."
Agent: {
    "response": "I understand. How about ₹15,000 upfront with standard 30-day terms? EL = 0.15 × 80,000 × 0.70 = ₹8,400... Actually that exceeds our limit. Let me try ₹18,000 upfront: EL = 0.15 × 77,000 × 0.70 = ₹8,085, still too high. Best I can do is ₹20,000 upfront: EL = 0.15 × 75,000 × 0.70 = ₹7,875... Hmm, still exceeds. Would you consider 10-day settlement with ₹10K upfront? That keeps EL at ₹4,200.",
    "offer": {"upfront": 10000, "days": 10},
    "expected_loss": 4200,
    "escalate": False
}

# Round 3 (last attempt)
Agent: {
    "response": "I've tried multiple combinations but can't find one that both fits your needs and our risk limits. I'm escalating this to our senior credit team for manual review. They'll contact you within 2 hours. Reference: AERO-2026-02-15-0567",
    "offer": None,
    "expected_loss": None,
    "escalate": True
}
```

---

## Meta-Agent (Orchestrator)

**Role**: Coordinate all agents in correct sequence

**Workflow**:
```python
class MetaAgent:
    def __init__(self):
        self.financial_analyst = FinancialAnalystAgent()
        self.risk_ai = RiskAIAgent()
        self.terms_crafter = TermsCrafterAgent()
        self.comms_agent = CommsAgent()
        self.monitor_agent = MonitorAgent()
        self.negotiation_agent = NegotiationAgent()
    
    def process_booking_request(self, booking_request, ml_scores):
        # Step 1: Financial Analysis
        financial_analysis = self.financial_analyst.analyze(
            booking_request, ml_scores
        )
        
        # Step 2: Risk Assessment
        risk_assessment = self.risk_ai.assess(
            ml_scores, company_data, external_data
        )
        
        # Step 3: Generate Options
        options = self.terms_crafter.generate_options(
            financial_analysis, ml_scores, risk_constraints
        )
        
        # Step 4: Compliance Check
        compliance = self.monitor_agent.validate(options, risk_constraints)
        
        if not compliance["compliant"]:
            return {"status": "error", "violations": compliance["violations"]}
        
        # Step 5: Generate Message
        message = self.comms_agent.compose_message(
            booking_request, options, risk_assessment
        )
        
        return {
            "status": "success",
            "decision": "negotiate",
            "options": options,
            "message": message,
            "risk_summary": risk_assessment["risk_summary"],
            "compliance_check": compliance
        }
    
    def handle_negotiation(self, session_id, user_message, round_number):
        # Triggered if user clicks "Support"
        return self.negotiation_agent.negotiate(
            session_id, user_message, round_number
        )
```

---

## LangChain Implementation Requirements

**Use**:
- `langchain.agents` for agent definitions
- `langchain.tools` for calculation tools
- `langchain.memory` for negotiation chat (ConversationBufferMemory)
- `langchain.prompts` for prompt templates
- `langchain_anthropic` or `langchain_openai` for LLM calls

**Structure**:
```python
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_anthropic import ChatAnthropic

# Define tools
tools = [
    Tool(name="calculate_ead", func=calculate_ead, description="..."),
    Tool(name="calculate_el", func=calculate_expected_loss, description="..."),
    # ... more tools
]

# Create each agent with tools and prompts
financial_analyst_agent = create_react_agent(
    llm=ChatAnthropic(model="claude-3-haiku-20240307"),
    tools=tools,
    prompt=financial_analyst_prompt
)

# ... create all 6 agents

# Meta-agent orchestrates
meta_agent = MetaAgent()
result = meta_agent.process_booking_request(booking_request, ml_scores)
```

---

## Expected Output (Demo Run)

```python
# Run the system
result = meta_agent.process_booking_request(booking_request, ml_scores)

print(result)
```

**Output**:
```json
{
    "status": "success",
    "decision": "negotiate",
    "options": [
        {
            "option_id": "A",
            "type": "shortened_settlement",
            "settlement_days": 7,
            "upfront_amount": 0,
            "approved_amount": 50000,
            "expected_loss": 1330,
            "friction_score": 4.0
        },
        {
            "option_id": "B",
            "type": "upfront_payment",
            "settlement_days": 30,
            "upfront_amount": 25000,
            "approved_amount": 50000,
            "expected_loss": 4935,
            "friction_score": 7.0
        },
        {
            "option_id": "C",
            "type": "partial_approval",
            "settlement_days": 14,
            "upfront_amount": 0,
            "approved_amount": 20000,
            "expected_loss": 3640,
            "friction_score": 8.5
        }
    ],
    "message": {
        "subject": "Credit Options for ₹50,000 Booking",
        "body": "Hi MediumRisk Agency,\n\nYour ₹50,000 booking..."
    },
    "risk_summary": "Low fraud probability but declining credit capacity...",
    "compliance_check": {
        "compliant": true,
        "violations": [],
        "all_checks_passed": true
    }
}
```

---

## Testing Requirements

**Create test cases**:
```python
# Test 1: Yellow flag company (negotiate)
test_yellow_flag()

# Test 2: Red flag company (should not generate options)
test_red_flag()  # Intent > 0.60

# Test 3: Green flag company (auto-approve, no options needed)
test_green_flag()

# Test 4: Negotiation flow (3 rounds)
test_negotiation_3_rounds()

# Test 5: Compliance violation (all options exceed EL)
test_no_valid_options()
```

---

## Deliverables

1. **Working Python code** with LangChain agents (6 agents + 1 meta-agent)
2. **Demo script** that runs end-to-end with mock data
3. **Console output** showing each agent's work
4. **3-round negotiation example** (chat flow)
5. **Agent interaction diagram** (Mermaid/ASCII showing flow)

---

## Success Criteria

✅ Meta-agent coordinates all 6 agents sequentially
✅ Terms Crafter generates exactly 3 options
✅ All options satisfy EL ≤ ₹5,000 (Monitor Agent verifies)
✅ Comms Agent produces natural language message
✅ Negotiation Agent conducts 3-round chat with memory
✅ System runs end-to-end with mock data (no database needed)
✅ Code is modular (each agent is separate class/function)

---

**Focus**: Build ONLY the LangChain multi-agent system. No FastAPI, no SQL, no frontend. Just working agent code with mock data that demonstrates the workflow.
```

---

**This prompt gives Antigravity everything to build just the LangChain agent system in isolation.**