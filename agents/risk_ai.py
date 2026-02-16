"""Agent 2: Risk AI - Interpret ML scores and provide risk assessment"""

import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class RiskAssessment(BaseModel):
    """Structured risk assessment output"""
    risk_summary: str = Field(description="One-paragraph risk summary")
    key_risk_factors: List[str] = Field(description="List of key risk factors")
    mitigating_factors: List[str] = Field(description="List of mitigating factors")
    recommendation: str = Field(description="Recommendation for credit terms")

class RiskAIAgent:
    """Agent 2: Interpret Intent/Capacity scores and provide risk summary"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.3,  # Slight creativity for narrative
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        self.parser = PydanticOutputParser(pydantic_object=RiskAssessment)
        
        self.prompt = PromptTemplate(
            template="""You are AEROX's Risk AI specialist. Analyze the following company profile and provide a risk assessment.

**ML Model Scores:**
- Intent Score (Fraud Risk): {intent_score:.2f} (0=safe, 1=fraud)
- Capacity Score (Credit Quality): {capacity_score:.2f} (0=poor, 1=excellent)
- Probability of Default (7 days): {pd_7d:.2%}
- Probability of Default (30 days): {pd_30d:.2%}

**Company Profile:**
- Segment: {segment}
- Credit Utilization: {credit_utilization:.1%}
- On-time Payment Rate: {on_time_payment_rate:.1%}
- Avg Late Payment: {avg_late_payment_days} days
- Chargeback Rate: {chargeback_rate:.2%}
- Business Age: {business_age_months} months
- Years with Platform: {years_with_platform:.1f} years

**External Data:**
- GST Revenue Trend: {gst_revenue_trend:.1%}
- GST Filing Status: {gst_filing_status}
- Cash Flow (7d): ₹{cash_flow_7d:,.0f}
- CIBIL Score: {cibil_score}
- CIBIL Trend: {cibil_trend}

Provide a comprehensive risk assessment following this format:

{format_instructions}

Focus on actionable insights for credit decision-making.""",
            input_variables=[
                "intent_score", "capacity_score", "pd_7d", "pd_30d",
                "segment", "credit_utilization", "on_time_payment_rate",
                "avg_late_payment_days", "chargeback_rate", "business_age_months",
                "years_with_platform", "gst_revenue_trend", "gst_filing_status",
                "cash_flow_7d", "cibil_score", "cibil_trend"
            ],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def assess(self, ml_scores: dict, company_data: dict, external_data: dict) -> dict:
        """
        Generate risk assessment from ML scores and company data
        
        Returns:
            Dict with risk_summary, key_risk_factors, mitigating_factors, recommendation
        """
        try:
            # Format prompt
            formatted_prompt = self.prompt.format(
                intent_score=ml_scores['intent_score'],
                capacity_score=ml_scores['capacity_score'],
                pd_7d=ml_scores['pd_7d'],
                pd_30d=ml_scores['pd_30d'],
                segment=company_data['segment'],
                credit_utilization=company_data['credit_utilization'],
                on_time_payment_rate=company_data['on_time_payment_rate'],
                avg_late_payment_days=company_data['avg_late_payment_days'],
                chargeback_rate=company_data['chargeback_rate'],
                business_age_months=company_data['business_age_months'],
                years_with_platform=company_data['years_with_platform'],
                gst_revenue_trend=external_data['gst_revenue_trend'],
                gst_filing_status=external_data['gst_filing_status'],
                cash_flow_7d=external_data['cash_flow_7d'],
                cibil_score=external_data['cibil_score'],
                cibil_trend=external_data['cibil_trend']
            )
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse structured output
            assessment = self.parser.parse(response.content)
            
            result = {
                "risk_summary": assessment.risk_summary,
                "key_risk_factors": assessment.key_risk_factors,
                "mitigating_factors": assessment.mitigating_factors,
                "recommendation": assessment.recommendation
            }
            
            logger.info(f"[Risk AI] Assessment complete - {len(assessment.key_risk_factors)} risks, " +
                       f"{len(assessment.mitigating_factors)} mitigating factors")
            
            return result
            
        except Exception as e:
            logger.error(f"Risk AI assessment failed: {e}")
            # Fallback to simple assessment
            return self._fallback_assessment(ml_scores, company_data, external_data)
    
    def _fallback_assessment(self, ml_scores, company_data, external_data):
        """Fallback assessment if LLM fails"""
        return {
            "risk_summary": f"Intent score {ml_scores['intent_score']:.2f} indicates " +
                           f"{'low' if ml_scores['intent_score'] < 0.4 else 'moderate'} fraud risk. " +
                           f"Capacity score {ml_scores['capacity_score']:.2f} shows " +
                           f"{'good' if ml_scores['capacity_score'] > 0.6 else 'moderate'} credit quality.",
            "key_risk_factors": [
                f"Credit utilization: {company_data['credit_utilization']:.1%}",
                f"Late payments: {company_data['avg_late_payment_days']} days avg",
                f"GST revenue declining {external_data['gst_revenue_trend']:.1%}"
            ],
            "mitigating_factors": [
                f"Intent score {ml_scores['intent_score']:.2f} (low fraud risk)",
                f"{company_data['years_with_platform']:.1f} years relationship",
                f"{company_data['on_time_payment_rate']:.1%} on-time payment rate"
            ],
            "recommendation": "Consider shortened settlement or partial upfront to reduce exposure window."
        }
