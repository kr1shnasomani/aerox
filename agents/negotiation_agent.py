"""Agent 6: Negotiation Agent - Handle chat-based negotiation with memory"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from agents.tools import calculate_ead, calculate_expected_loss
from agents.config import LGD
import json
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class NegotiationAgent:
    """Agent 6: Handle multi-round negotiation with conversation memory"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.5,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # Simple conversation history (replaces ConversationBufferMemory)
        self.conversation_history = []
        
        self.prompt_template = """You are AEROX's credit negotiation specialist. A customer declined initial options and wants to negotiate.

**Context:**
- Company: {company_name}
- Booking Amount: ₹{booking_amount:,.0f}
- Current Outstanding: ₹{outstanding:,.0f}
- Total Exposure: ₹{exposure:,.0f}
- Risk Constraint: Expected Loss must be ≤ ₹{max_el:,.0f}
- LGD: {lgd}
- PD (7d): {pd_7d}, PD (14d): {pd_14d}, PD (30d): {pd_30d}

**Initial Options Offered:**
{initial_options}

**Chat History:**
{chat_history}

**Customer's Message:** {user_message}

**Negotiation Round:** {round_number}/3 (MAX 3 rounds)

**Your Task:**
1. Acknowledge their concern empathetically
2. Propose a modified offer (blend settlement days, adjust upfront)
3. Calculate Expected Loss: EL = PD × (Exposure - Upfront) × LGD
4. Verify EL ≤ ₹{max_el:,.0f}
5. If no valid offer after 3 rounds, escalate to manual review

**Rules:**
- Show calculation explicitly: "EL = {pd} × {ead} × {lgd} = ₹..."
- Cannot approve if EL > ₹{max_el:,.0f}
- Cannot change PD values (they're from ML models)
- Be creative with settlement days (7-30) and upfront amounts

**Output JSON:**
{{
    "response": "your empathetic response with math shown",
    "offer": {{"upfront": X, "settlement_days": Y, "approved_amount": Z}},
    "expected_loss": calculated_EL,
    "escalate": true/false
}}

Generate your response:"""
    
    def negotiate(
        self,
        user_message: str,
        round_number: int,
        booking_request: dict,
        ml_scores: dict,
        initial_options: list,
        risk_constraints: dict
    ) -> dict:
        """
        Conduct one round of negotiation
        
        Args:
            user_message: Customer's negotiation message
            round_number: Current round (1-3)
            booking_request: Original booking details
            ml_scores: ML scores with PD values
            initial_options: Initially offered options
            risk_constraints: Risk constraints
        
        Returns:
            Dict with response, offer, expected_loss, escalate
        """
        # Calculate exposure
        exposure = booking_request['current_outstanding'] + booking_request['booking_amount']
        
        # Format initial options
        options_text = "\n".join([
            f"Option {opt['option_id']}: {opt['settlement_days']} days, " +
            f"₹{opt['upfront_amount']:,.0f} upfront, EL=₹{opt['expected_loss']:,.2f}"
            for opt in initial_options
        ])
        
        # Get chat history from simple list
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_history
        ]) if self.conversation_history else "No previous messages"
        
        try:
            # Format prompt
            prompt = self.prompt_template.format(
                company_name=booking_request['company_name'],
                booking_amount=booking_request['booking_amount'],
                outstanding=booking_request['current_outstanding'],
                exposure=exposure,
                max_el=risk_constraints['max_expected_loss'],
                lgd=LGD,
                pd_7d=ml_scores['pd_7d'],
                pd_14d=ml_scores['pd_14d'],
                pd_30d=ml_scores['pd_30d'],
                initial_options=options_text,
                chat_history=history_text if history_text else "No previous messages",
                user_message=user_message,
                round_number=round_number
            )
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            # Save to conversation history
            self.conversation_history.append({"role": "Customer", "content": user_message})
            self.conversation_history.append({"role": "Agent", "content": result['response']})
            
            logger.info(f"[Negotiation Agent] Round {round_number}: " +
                       f"EL=₹{result.get('expected_loss', 0):,.2f}, " +
                       f"Escalate={result.get('escalate', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Negotiation failed: {e}")
            
            # Fallback escalation on round 3
            if round_number >= 3:
                return {
                    "response": f"I've tried multiple combinations but can't find one that fits both your needs and our risk limits. I'm escalating this to our senior credit team for manual review. They'll contact you within 2 hours. Reference: AERO-2026-02-15-{booking_request['company_id'][-4:]}",
                    "offer": None,
                    "expected_loss": None,
                    "escalate": True
                }
            else:
                # Try simpler offer
                return self._simple_offer(
                    user_message,
                    booking_request,
                    ml_scores,
                    risk_constraints
                )
    
    def _simple_offer(self, user_message, booking_request, ml_scores, risk_constraints):
        """Generate simple counter-offer without LLM"""
        outstanding = booking_request['current_outstanding']
        booking_amount = booking_request['booking_amount']
        
        # Try 10-day settlement with modest upfront
        settlement_days = 10
        pd_10d = (ml_scores['pd_7d'] + ml_scores['pd_14d']) / 2  # Interpolate
        
        # Calculate required upfront to hit max_el
        max_el = risk_constraints['max_expected_loss']
        exposure = outstanding + booking_amount
        
        required_upfront = exposure - (max_el / (pd_10d * LGD))
        required_upfront = max(0, min(booking_amount * 0.5, required_upfront))
        
        el = calculate_expected_loss(pd_10d, exposure - required_upfront, LGD)
        
        return {
            "response": f"I understand. How about ₹{required_upfront:,.0f} upfront with {settlement_days}-day settlement? This keeps Expected Loss at ₹{el:,.2f} (calculation: {pd_10d:.3f} × {exposure - required_upfront:,.0f} × {LGD} = ₹{el:,.2f}).",
            "offer": {
                "upfront": round(required_upfront, 0),
                "settlement_days": settlement_days,
                "approved_amount": booking_amount
            },
            "expected_loss": round(el, 2),
            "escalate": False
        }
    
    def reset_memory(self):
        """Reset conversation memory for new session"""
        self.conversation_history = []
