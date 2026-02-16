"""Agent 3: Terms Crafter - Generate 3 credit term options"""

import logging
from agents.tools import generate_options
from agents.config import LGD

logger = logging.getLogger(__name__)

class TermsCrafterAgent:
    """Agent 3: Generate mathematically valid credit term options"""
    
    def craft_options(
        self,
        financial_analysis: dict,
        ml_scores: dict,
        risk_constraints: dict
    ) -> list:
        """
        Generate 3 credit term options that satisfy EL ≤ max_el
        
        Args:
            financial_analysis: Output from Financial Analyst
            ml_scores: ML scores with pd_7d, pd_14d, pd_30d
            risk_constraints: Dict with max_expected_loss, lgd
        
        Returns:
            List of 3 option dicts (A, B, C) sorted by friction_score
        """
        exposure = financial_analysis['total_exposure']
        outstanding = financial_analysis['breakdown']['outstanding']
        booking_amount = financial_analysis['breakdown']['booking_amount']
        
        pd_7d = ml_scores['pd_7d']
        pd_14d = ml_scores['pd_14d']
        pd_30d = ml_scores['pd_30d']
        
        lgd = risk_constraints['lgd']
        max_el = risk_constraints['max_expected_loss']
        
        # Generate options using deterministic algorithm
        options = generate_options(
            exposure=exposure,
            outstanding=outstanding,
            booking_amount=booking_amount,
            pd_7d=pd_7d,
            pd_14d=pd_14d,
            pd_30d=pd_30d,
            lgd=lgd,
            max_el=max_el
        )
        
        if not options:
            logger.warning("[Terms Crafter] No valid options found! All exceed max EL.")
            return []
        
        # Assign option IDs (A, B, C)
        option_ids = ['A', 'B', 'C']
        for i, opt in enumerate(options):
            if i < len(option_ids):
                opt['option_id'] = option_ids[i]
        
        logger.info(f"[Terms Crafter] Generated {len(options)} options:")
        for opt in options:
            logger.info(f"  Option {opt['option_id']}: {opt['type']}, " +
                       f"EL=₹{opt['expected_loss']:,.2f}, " +
                       f"friction={opt['friction_score']}")
        
        return options
