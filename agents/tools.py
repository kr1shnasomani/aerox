"""Deterministic calculation tools for AEROX agents"""

import numpy as np
from typing import Dict, List, Tuple

def calculate_ead(outstanding: float, booking_amount: float, upfront: float = 0) -> float:
    """
    Calculate Exposure at Default (EAD)
    
    Args:
        outstanding: Current outstanding amount
        booking_amount: New booking amount
        upfront: Upfront payment amount (reduces exposure)
    
    Returns:
        Total exposure at default
    """
    return outstanding + booking_amount - upfront


def calculate_expected_loss(pd: float, ead: float, lgd: float) -> float:
    """
    Calculate Expected Loss using Basel III formula
    
    EL = PD × EAD × LGD
    
    Args:
        pd: Probability of Default (0-1)
        ead: Exposure at Default
        lgd: Loss Given Default (typically 0.7)
    
    Returns:
        Expected Loss in currency units
    """
    return pd * ead * lgd


def generate_options(
    exposure: float,
    outstanding: float,
    booking_amount: float,
    pd_7d: float,
    pd_14d: float,
    pd_30d: float,
    lgd: float,
    max_el: float
) -> List[Dict]:
    """
    Generate 3 credit term options that satisfy EL ≤ max_el
    
    Algorithm per build_context.md:
    - Option A: Shortened settlement (7 days, no upfront)
    - Option B: Upfront payment (30 days with partial upfront)
    - Option C: Partial approval (reduced amount, 14 days)
    
    Args:
        exposure: Total exposure (outstanding + booking)
        outstanding: Current outstanding
        booking_amount: Requested booking amount
        pd_7d, pd_14d, pd_30d: Probability of default at horizons
        lgd: Loss given default
        max_el: Maximum acceptable expected loss
    
    Returns:
        List of up to 3 option dicts, sorted by friction_score
    """
    options = []
    
    # Option A: Shortened Settlement (7 days)
    el_7d = calculate_expected_loss(pd_7d, exposure, lgd)
    if el_7d <= max_el:
        options.append({
            "option_id": "A",
            "type": "shortened_settlement",
            "settlement_days": 7,
            "upfront_amount": 0,
            "approved_amount": booking_amount,
            "expected_loss": round(el_7d, 2),
            "friction_score": 4.0,
            "description": "Settle within 7 days"
        })
    
    # Option B: Upfront Payment (30 days)
    # Solve: pd_30d × (exposure - upfront) × lgd ≤ max_el
    # upfront = exposure - (max_el / (pd_30d × lgd))
    if pd_30d > 0:
        required_upfront = exposure - (max_el / (pd_30d * lgd))
        required_upfront = max(0, required_upfront)  # Can't be negative
        
        if 0 < required_upfront < booking_amount * 1.2:  # Allow up to 120% of booking
            required_upfront = min(required_upfront, booking_amount)  # Cap at booking amount
            el_upfront = calculate_expected_loss(
                pd_30d,
                exposure - required_upfront,
                lgd
            )
            options.append({
                "option_id": "B",
                "type": "upfront_payment",
                "settlement_days": 30,
                "upfront_amount": round(required_upfront, 0),
                "approved_amount": booking_amount,
                "expected_loss": round(el_upfront, 2),
                "friction_score": 7.0,
                "description": f"Pay ₹{round(required_upfront, 0):,.0f} upfront, ₹{round(booking_amount - required_upfront, 0):,.0f} in 30 days"
            })
    
    # Option C: Partial Approval (14 days)
    # Try reducing booking amount with 14-day settlement
    for partial_pct in [0.5, 0.4, 0.3, 0.2]:
        partial_booking = booking_amount * partial_pct
        partial_exposure = outstanding + partial_booking
        el_partial = calculate_expected_loss(pd_14d, partial_exposure, lgd)
        
        if el_partial <= max_el:
            options.append({
                "option_id": "C",
                "type": "partial_approval",
                "settlement_days": 14,
                "upfront_amount": 0,
                "approved_amount": round(partial_booking, 0),
                "expected_loss": round(el_partial, 2),
                "friction_score": 8.0 + (1 - partial_pct) * 2,  # Higher friction for lower approval
                "description": f"Approve ₹{round(partial_booking, 0):,.0f} with 14-day settlement"
            })
            break
    
    # Sort by friction score (lowest first) and take top 3
    options.sort(key=lambda x: x["friction_score"])
    return options[:3]


def validate_compliance(options: List[Dict], max_el: float) -> Dict:
    """
    Validate that all options satisfy compliance rules
    
    Checks:
    1. Expected Loss ≤ max_el
    2. Upfront amount ≤ approved amount
    3. Settlement days in range [7, 90]
    
    Args:
        options: List of option dicts
        max_el: Maximum expected loss threshold
    
    Returns:
        Dict with compliant (bool), violations (list), options_count (int)
    """
    violations = []
    
    for opt in options:
        # Check 1: Expected Loss within limit
        if opt["expected_loss"] > max_el:
            violations.append(
                f"Option {opt['option_id']}: EL ₹{opt['expected_loss']:,.2f} exceeds ₹{max_el:,.2f}"
            )
        
        # Check 2: Upfront not exceeding approved amount
        if opt.get("upfront_amount", 0) > opt["approved_amount"]:
            violations.append(
                f"Option {opt['option_id']}: Upfront ₹{opt['upfront_amount']:,.0f} exceeds approved ₹{opt['approved_amount']:,.0f}"
            )
        
        # Check 3: Settlement days reasonable (7-90 days)
        if not (7 <= opt["settlement_days"] <= 90):
            violations.append(
                f"Option {opt['option_id']}: Settlement days {opt['settlement_days']} out of range [7, 90]"
            )
    
    return {
        "compliant": len(violations) == 0,
        "violations": violations,
        "options_count": len(options),
        "all_checks_passed": len(violations) == 0
    }
