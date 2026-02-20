"""Pydantic models for AEROX API request/response schemas"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class BookingRequest(BaseModel):
    company_id: str
    company_name: str
    booking_amount: float
    current_outstanding: float
    credit_limit: float
    route: str
    booking_date: str = "2026-02-15"


class NegotiationRequest(BaseModel):
    user_message: str
    round_number: int
    booking_request: Dict[str, Any]
    ml_scores: Dict[str, Any]
    initial_options: List[Dict[str, Any]]


class OptionResponse(BaseModel):
    option_id: str
    type: str
    settlement_days: int
    upfront_amount: float
    approved_amount: float
    expected_loss: float
    friction_score: float
    description: str


class ProcessingResult(BaseModel):
    decision: str
    risk_category: str
    ml_scores: Dict[str, Any]
    booking_request: Dict[str, Any]
    approved_amount: Optional[float] = None
    settlement_days: Optional[int] = None
    reason: Optional[str] = None
    financial_analysis: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, Any]]] = None
    validation: Optional[Dict[str, Any]] = None
    message: Optional[Any] = None


class NegotiationResult(BaseModel):
    response: str
    offer: Optional[Dict[str, Any]] = None
    expected_loss: Optional[float] = None
    escalate: bool = False


class AgencyResponse(BaseModel):
    company_id: str
    segment: Optional[str] = None
    region: Optional[str] = None
    business_age_months: Optional[float] = None
    credit_limit_inr: Optional[float] = None
    current_outstanding_inr: Optional[float] = None
    credit_utilization: Optional[float] = None
    on_time_payment_rate: Optional[float] = None
    avg_late_payment_days: Optional[float] = None
    chargeback_rate: Optional[float] = None
    fraud_flag: Optional[int] = None
    default_flag: Optional[int] = None
    risk_score: Optional[float] = None
    annual_revenue_inr: Optional[float] = None
    total_bookings_lifetime: Optional[float] = None
