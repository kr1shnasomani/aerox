"""Agent 1: Financial Analyst - Calculate EAD and Expected Loss"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.tools import calculate_ead, calculate_expected_loss
from agents.config import MAX_EXPECTED_LOSS, LGD
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class FinancialAnalystAgent:
    """Agent 1: Calculate Exposure-at-Default and Expected Loss"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    def analyze(self, booking_request: dict, ml_scores: dict) -> dict:
        """
        Analyze financial exposure and expected loss
        
        Args:
            booking_request: Dict with booking_amount, current_outstanding
            ml_scores: Dict with pd_7d, pd_14d, pd_30d
        
        Returns:
            Dict with total_exposure, baseline_el_30d, exceeds_risk_appetite, exceeds_by
        """
        outstanding = booking_request['current_outstanding']
        booking_amount = booking_request['booking_amount']
        pd_30d = ml_scores['pd_30d']
        
        # Calculate EAD (no upfront for baseline)
        total_exposure = calculate_ead(outstanding, booking_amount, upfront=0)
        
        # Calculate baseline EL at 30-day horizon
        baseline_el_30d = calculate_expected_loss(pd_30d, total_exposure, LGD)
        
        # Check risk appetite
        exceeds_risk_appetite = baseline_el_30d > MAX_EXPECTED_LOSS
        exceeds_by = max(0, baseline_el_30d - MAX_EXPECTED_LOSS)
        
        result = {
            "total_exposure": total_exposure,
            "baseline_el_30d": round(baseline_el_30d, 2),
            "exceeds_risk_appetite": exceeds_risk_appetite,
            "exceeds_by": round(exceeds_by, 2),
            "breakdown": {
                "outstanding": outstanding,
                "booking_amount": booking_amount,
                "pd_30d": pd_30d,
                "lgd": LGD,
                "max_acceptable_el": MAX_EXPECTED_LOSS
            }
        }
        
        logger.info(f"[Financial Analyst] EAD: ₹{total_exposure:,.0f}, " +
                   f"EL(30d): ₹{baseline_el_30d:,.2f}, " +
                   f"Exceeds: {exceeds_risk_appetite}")
        
        return result
