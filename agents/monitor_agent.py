"""Agent 5: Monitor Agent - Validate compliance of credit options"""

import logging
from agents.tools import validate_compliance

logger = logging.getLogger(__name__)

class MonitorAgent:
    """Agent 5: Ensure all options satisfy compliance rules"""
    
    def validate(self, options: list, risk_constraints: dict) -> dict:
        """
        Validate that all options meet compliance requirements
        
        Checks:
        1. Expected Loss ≤ max_expected_loss
        2. Upfront amount ≤ approved_amount
        3. Settlement days in range [7, 90]
        
        Returns:
            Dict with compliant, violations, options_count, all_checks_passed
        """
        max_el = risk_constraints['max_expected_loss']
        
        result = validate_compliance(options, max_el)
        
        if result['compliant']:
            logger.info(f"[Monitor Agent] ✓ All {result['options_count']} options compliant")
        else:
            logger.warning(f"[Monitor Agent] ✗ {len(result['violations'])} violations found:")
            for violation in result['violations']:
                logger.warning(f"  - {violation}")
        
        return result
