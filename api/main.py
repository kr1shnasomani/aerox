"""AEROX FastAPI Backend - Wraps existing multi-agent system"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from api.models import BookingRequest, NegotiationRequest
from api.dependencies import get_meta_agent, get_dataset1
from agents.config import (
    MOCK_BOOKING_REQUEST, GREEN_FLAG_BOOKING, RED_FLAG_BOOKING,
    MOCK_ML_SCORES, GREEN_FLAG_SCORES, RED_FLAG_SCORES,
    NEGOTIATION_TEST_MESSAGES, DECISION_MATRIX, RISK_CONSTRAINTS
)

app = FastAPI(
    title="AEROX API",
    description="Adaptive Exposure & Risk Orchestrator - Multi-Agent Credit Negotiation",
    version="1.0.0"
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize MetaAgent on startup
@app.on_event("startup")
async def startup():
    get_meta_agent()


# --- Core Endpoints ---

@app.post("/api/booking/process")
async def process_booking(request: BookingRequest):
    """
    Process a booking request through the full AEROX pipeline.
    Runs Layers 0-4: scoring, decision gate, financial analysis,
    risk AI, terms crafting, compliance, and communication.
    """
    meta = get_meta_agent()
    booking = request.model_dump()

    try:
        result = meta.process_booking_request(booking)
        # Ensure all values are JSON-serializable (convert numpy types)
        return _sanitize(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/negotiate")
async def negotiate(request: NegotiationRequest):
    """
    Handle one round of negotiation (max 3 rounds).
    Takes the customer's message and returns a counter-offer.
    """
    meta = get_meta_agent()

    try:
        result = meta.handle_negotiation(
            user_message=request.user_message,
            round_number=request.round_number,
            booking_request=request.booking_request,
            ml_scores=request.ml_scores,
            initial_options=request.initial_options
        )
        return _sanitize(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/negotiate/reset")
async def reset_negotiation():
    """Reset negotiation conversation memory for a new session."""
    meta = get_meta_agent()
    meta.reset_negotiation_memory()
    return {"status": "ok", "message": "Negotiation memory cleared"}


# --- Data Endpoints ---

@app.get("/api/scenarios")
async def get_scenarios():
    """Return 3 pre-built test scenarios (green, yellow, red)."""
    return {
        "scenarios": [
            {
                "id": "green",
                "label": "Low Risk (Auto-Approve)",
                "booking": GREEN_FLAG_BOOKING,
                "expected_scores": GREEN_FLAG_SCORES,
                "description": "Established agency with strong credit - should auto-approve"
            },
            {
                "id": "yellow",
                "label": "Medium Risk (Negotiate)",
                "booking": MOCK_BOOKING_REQUEST,
                "expected_scores": MOCK_ML_SCORES,
                "description": "Moderate risk agency - triggers negotiation with 3 options"
            },
            {
                "id": "red",
                "label": "High Risk (Block)",
                "booking": RED_FLAG_BOOKING,
                "expected_scores": RED_FLAG_SCORES,
                "description": "High fraud intent - should be hard blocked"
            }
        ],
        "negotiation_messages": NEGOTIATION_TEST_MESSAGES
    }


@app.get("/api/agencies")
async def get_agencies(
    page: int = 1,
    page_size: int = 50,
    segment: str = None,
    region: str = None,
    search: str = None
):
    """Return paginated agency list from dataset1.csv."""
    df = get_dataset1()

    # Filters
    if segment:
        df = df[df['segment'] == segment]
    if region:
        df = df[df['region'] == region]
    if search:
        df = df[df['company_id'].str.contains(search, case=False, na=False)]

    total = len(df)

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    # Select key columns
    columns = [
        'company_id', 'segment', 'region', 'business_age_months',
        'credit_limit_inr', 'current_outstanding_inr', 'credit_utilization',
        'on_time_payment_rate', 'avg_late_payment_days', 'chargeback_rate',
        'fraud_flag', 'default_flag', 'risk_score', 'annual_revenue_inr',
        'total_bookings_lifetime'
    ]
    available_cols = [c for c in columns if c in page_df.columns]

    records = page_df[available_cols].replace({np.nan: None}).to_dict(orient='records')

    return {
        "agencies": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@app.get("/api/agencies/{company_id}")
async def get_agency(company_id: str):
    """Return detailed data for a single agency."""
    df = get_dataset1()
    row = df[df['company_id'] == company_id]

    if row.empty:
        raise HTTPException(status_code=404, detail=f"Agency {company_id} not found")

    record = row.iloc[0].replace({np.nan: None}).to_dict()
    return {"agency": record}


@app.get("/api/config")
async def get_config():
    """Return decision matrix thresholds and risk constraints."""
    return {
        "decision_matrix": DECISION_MATRIX,
        "risk_constraints": RISK_CONSTRAINTS
    }


@app.get("/api/stats")
async def get_stats():
    """Return aggregate statistics from the dataset."""
    df = get_dataset1()

    stats = {
        "total_agencies": len(df),
        "segments": df['segment'].value_counts().to_dict() if 'segment' in df.columns else {},
        "regions": df['region'].value_counts().to_dict() if 'region' in df.columns else {},
        "avg_credit_utilization": float(df['credit_utilization'].mean()) if 'credit_utilization' in df.columns else 0,
        "avg_on_time_payment_rate": float(df['on_time_payment_rate'].mean()) if 'on_time_payment_rate' in df.columns else 0,
        "fraud_rate": float(df['fraud_flag'].mean()) if 'fraud_flag' in df.columns else 0,
        "default_rate": float(df['default_flag'].mean()) if 'default_flag' in df.columns else 0,
    }

    return stats


def _sanitize(obj):
    """Convert numpy types to Python native for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj
