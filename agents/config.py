"""Configuration and mock data for AEROX multi-agent system"""

import os
import yaml
from pathlib import Path

# Load decision matrix from config.yaml
CONFIG_PATH = Path(__file__).parent.parent / "configs" / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config_data = yaml.safe_load(f)

# Risk thresholds from config
DECISION_MATRIX = config_data.get('decision_matrix', {
    'block_intent_threshold': 0.60,
    'approve_intent_threshold': 0.40,
    'approve_capacity_threshold': 0.70,
    'negotiate_capacity_min': 0.40,
    'negotiate_capacity_max': 0.70
})

# Risk constraints (Basel III)
LGD = 0.70  # Loss Given Default (70%)
MAX_EXPECTED_LOSS = 5000  # INR

RISK_CONSTRAINTS = {
    'max_expected_loss': MAX_EXPECTED_LOSS,
    'lgd': LGD
}

# Mock booking request (as per build_context.md)
MOCK_BOOKING_REQUEST = {
    "company_id": "IN-TRV-000567",
    "company_name": "MediumRisk Agency",
    "booking_amount": 50000,
    "current_outstanding": 45000,
    "credit_limit": 80000,
    "route": "Chennai-Dubai",
    "booking_date": "2026-02-15"
}

# Mock ML model outputs (fallback if real model unavailable)
MOCK_ML_SCORES = {
    "intent_score": 0.32,  # Low fraud
    "capacity_score": 0.55,  # Moderate credit
    "pd_7d": 0.02,  # 2% default risk at 7 days
    "pd_14d": 0.08,  # 8% at 14 days
    "pd_30d": 0.15,  # 15% at 30 days
    "risk_category": "yellow"
}

# Mock company profile
MOCK_COMPANY_DATA = {
    "segment": "small_medium",
    "credit_utilization": 0.87,
    "on_time_payment_rate": 0.78,
    "avg_late_payment_days": 12,
    "chargeback_rate": 0.023,
    "business_age_months": 36,
    "years_with_platform": 2.1
}

# Mock external data
MOCK_EXTERNAL_DATA = {
    "gst_revenue_trend": -0.15,  # Declining 15%
    "gst_filing_status": "delayed",
    "bank_balance": 185000,
    "cash_flow_7d": -45000,  # Negative
    "cibil_score": 6.4,
    "cibil_trend": -0.8,
    "news_sentiment_score": -0.3
}

# Additional test scenarios
GREEN_FLAG_BOOKING = {
    "company_id": "IN-TRV-000123",
    "company_name": "LowRisk Travels",
    "booking_amount": 30000,
    "current_outstanding": 20000,
    "credit_limit": 100000,
    "route": "Mumbai-Singapore",
    "booking_date": "2026-02-15"
}

GREEN_FLAG_SCORES = {
    "intent_score": 0.15,  # Very low fraud
    "capacity_score": 0.85,  # High capacity
    "pd_7d": 0.005,
    "pd_14d": 0.01,
    "pd_30d": 0.03,
    "risk_category": "green"
}

RED_FLAG_BOOKING = {
    "company_id": "IN-TRV-000999",
    "company_name": "HighRisk Agency",
    "booking_amount": 100000,
    "current_outstanding": 150000,
    "credit_limit": 120000,
    "route": "Delhi-London",
    "booking_date": "2026-02-15"
}

RED_FLAG_SCORES = {
    "intent_score": 0.85,  # Very high fraud
    "capacity_score": 0.25,  # Low capacity
    "pd_7d": 0.25,
    "pd_14d": 0.40,
    "pd_30d": 0.60,
    "risk_category": "red"
}

# Negotiation test messages
NEGOTIATION_TEST_MESSAGES = [
    "Can't do 7 days, and ₹25K upfront is too much.",
    "What about ₹15,000 upfront with 20 days?",
    "This doesn't work for us, can you do better?"
]
