"""Meta-Agent: Orchestrate all 6 specialized agents"""

import logging
from agents.model_loader import ModelLoader
from agents.financial_analyst import FinancialAnalystAgent
from agents.risk_ai import RiskAIAgent
from agents.terms_crafter import TermsCrafterAgent
from agents.comms_agent import CommsAgent
from agents.monitor_agent import MonitorAgent
from agents.negotiation_agent import NegotiationAgent
from agents.config import RISK_CONSTRAINTS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetaAgent:
    """Orchestrator: Manage workflow across all 6 specialized agents"""
    
    def __init__(self):
        # Initialize model loader
        self.model_loader = ModelLoader()
        
        # Initialize all 6 agents
        self.financial_analyst = FinancialAnalystAgent()
        self.risk_ai = RiskAIAgent()
        self.terms_crafter = TermsCrafterAgent()
        self.comms = CommsAgent()
        self.monitor = MonitorAgent()
        self.negotiation = NegotiationAgent()
        
        logger.info("[Meta-Agent] Initialized all 6 agents")
    
    def process_booking_request(self, booking_request: dict) -> dict:
        """
        Main orchestration: Process a booking request through decision gates
        
        Flow:
        1. Score company via ML models
        2. Decision gate:
           - Green (low risk): Auto-approve
           - Red (high risk): Block
           - Yellow (moderate): Full negotiation pipeline
        3. Run agents 1-6 for yellow flag
        
        Returns:
            Dict with decision, scores, options, message, all agent outputs
        """
        company_id = booking_request['company_id']
        
        logger.info(f"\n{'='*80}")
        logger.info(f"[Meta-Agent] Processing booking: {company_id}")
        logger.info(f"{'='*80}")
        
        # Step 1: Score company
        logger.info("[Meta-Agent] Step 1: Scoring company with ML models...")
        scoring_result = self.model_loader.score_company(company_id)
        
        ml_scores = {
            'intent_score': scoring_result['intent_score'],
            'capacity_score': scoring_result['capacity_score'],
            'pd_7d': scoring_result['pd_7d'],
            'pd_14d': scoring_result['pd_14d'],
            'pd_30d': scoring_result['pd_30d']
        }
        
        risk_category = scoring_result['risk_category']
        
        logger.info(f"  Intent: {ml_scores['intent_score']:.3f}, " +
                   f"Capacity: {ml_scores['capacity_score']:.3f}, " +
                   f"Category: {risk_category.upper()}")
        
        # Step 2: Decision gate
        if risk_category == 'green':
            return self._auto_approve_flow(booking_request, ml_scores)
        elif risk_category == 'red':
            return self._block_flow(booking_request, ml_scores, scoring_result)
        else:  # yellow
            return self._negotiation_flow(booking_request, ml_scores, scoring_result)
    
    def _auto_approve_flow(self, booking_request: dict, ml_scores: dict) -> dict:
        """Handle green-flag auto-approval"""
        logger.info("[Meta-Agent] ✓ GREEN FLAG → Auto-approving")
        
        return {
            'decision': 'APPROVED',
            'risk_category': 'green',
            'ml_scores': ml_scores,
            'booking_request': booking_request,
            'approved_amount': booking_request['booking_amount'],
            'settlement_days': 30,
            'message': f"✓ Auto-approved: ₹{booking_request['booking_amount']:,.0f} " +
                      f"for {booking_request['company_name']} (30-day standard terms)"
        }
    
    def _block_flow(self, booking_request: dict, ml_scores: dict, scoring_result: dict) -> dict:
        """Handle red-flag blocking"""
        logger.info("[Meta-Agent] ✗ RED FLAG → Blocking")
        
        reason = []
        if ml_scores['intent_score'] >= 0.60:
            reason.append(f"High intent score ({ml_scores['intent_score']:.2f})")
        if ml_scores['capacity_score'] < 0.40:
            reason.append(f"Low capacity score ({ml_scores['capacity_score']:.2f})")
        
        return {
            'decision': 'BLOCKED',
            'risk_category': 'red',
            'ml_scores': ml_scores,
            'booking_request': booking_request,
            'reason': ' | '.join(reason),
            'message': f"✗ Blocked: {booking_request['company_name']} fails risk threshold. " +
                      f"Reason: {', '.join(reason)}"
        }
    
    def _negotiation_flow(self, booking_request: dict, ml_scores: dict, scoring_result: dict) -> dict:
        """Handle yellow-flag full pipeline with options"""
        logger.info("[Meta-Agent] ⚠ YELLOW FLAG → Full negotiation pipeline")
        
        # Mock company data (in production, fetch from database)
        company_data = {
            'company_name': booking_request['company_name'],
            'segment': 'Travel Agency',
            'total_bookings': 47,
            'credit_limit': 100000,
            'credit_utilization': 0.65,
            'on_time_payment_rate': 0.85,
            'avg_late_payment_days': 3.2,
            'chargeback_rate': 0.02,
            'business_age_months': 24,
            'years_with_platform': 2.0,
            'payment_history': 'Mostly on-time, 2 delays in last 6 months'
        }
        
        external_data = {
            'recent_news': 'No major red flags',
            'industry_outlook': 'Travel sector recovering post-COVID',
            'market_conditions': 'Stable',
            'gst_revenue_trend': 0.08,  # 8% growth
            'gst_filing_status': 'Regular',
            'cash_flow_7d': 25000,
            'cibil_score': 720,
            'cibil_trend': 'Stable'
        }
        
        # Agent 1: Financial Analysis
        logger.info("\n[Meta-Agent] Step 2: Running Financial Analyst...")
        financial_analysis = self.financial_analyst.analyze(booking_request, ml_scores)
        logger.info(f"  Total Exposure: ₹{financial_analysis['total_exposure']:,.0f}")
        logger.info(f"  Baseline EL (30d): ₹{financial_analysis['baseline_el_30d']:,.2f}")
        logger.info(f"  Exceeds limit: {financial_analysis['exceeds_risk_appetite']}")
        
        # Agent 2: Risk AI
        logger.info("\n[Meta-Agent] Step 3: Running Risk AI...")
        risk_assessment = self.risk_ai.assess(ml_scores, company_data, external_data)
        logger.info(f"  Risk Summary: {risk_assessment['risk_summary'][:80]}...")
        logger.info(f"  Recommendation: {risk_assessment['recommendation']}")
        
        # Agent 3: Terms Crafter
        logger.info("\n[Meta-Agent] Step 4: Running Terms Crafter...")
        options = self.terms_crafter.craft_options(
            financial_analysis,
            ml_scores,
            RISK_CONSTRAINTS
        )
        logger.info(f"  Generated {len(options)} options")
        
        if not options:
            logger.warning("[Meta-Agent] ✗ No valid options possible")
            return {
                'decision': 'BLOCKED',
                'risk_category': 'yellow',
                'ml_scores': ml_scores,
                'booking_request': booking_request,
                'reason': 'No options satisfy risk constraints (EL > ₹5,000 for all scenarios)',
                'financial_analysis': financial_analysis,
                'risk_assessment': risk_assessment
            }
        
        # Agent 5: Monitor (validate options)
        logger.info("\n[Meta-Agent] Step 5: Running Monitor Agent...")
        validation = self.monitor.validate(options, RISK_CONSTRAINTS)
        
        if not validation['compliant']:
            logger.error("[Meta-Agent] ✗ Options failed compliance")
            # Retry once with stricter params (not implemented fully here)
            return {
                'decision': 'BLOCKED',
                'risk_category': 'yellow',
                'ml_scores': ml_scores,
                'booking_request': booking_request,
                'reason': f"Options failed validation: {validation['violations']}",
                'options': options,
                'validation': validation
            }
        
        # Agent 4: Communications
        logger.info("\n[Meta-Agent] Step 6: Running Comms Agent...")
        message = self.comms.compose_message(
            booking_request,
            options,
            risk_assessment,
            company_data
        )
        logger.info(f"  Message subject: {message['subject']}")
        
        # Return full result
        return {
            'decision': 'NEGOTIATE',
            'risk_category': 'yellow',
            'ml_scores': ml_scores,
            'booking_request': booking_request,
            'financial_analysis': financial_analysis,
            'risk_assessment': risk_assessment,
            'options': options,
            'validation': validation,
            'message': message
        }
    
    def handle_negotiation(
        self,
        user_message: str,
        round_number: int,
        booking_request: dict,
        ml_scores: dict,
        initial_options: list
    ) -> dict:
        """
        Handle negotiation round (Agent 6)
        
        Args:
            user_message: Customer's negotiation message
            round_number: Current round (1-3)
            booking_request: Original booking request
            ml_scores: ML scores
            initial_options: Initially offered options
        
        Returns:
            Negotiation result from Agent 6
        """
        logger.info(f"\n[Meta-Agent] Negotiation Round {round_number}")
        
        result = self.negotiation.negotiate(
            user_message=user_message,
            round_number=round_number,
            booking_request=booking_request,
            ml_scores=ml_scores,
            initial_options=initial_options,
            risk_constraints=RISK_CONSTRAINTS
        )
        
        if result.get('escalate'):
            logger.warning("[Meta-Agent] ⚠ Escalating to manual review")
        else:
            logger.info(f"[Meta-Agent] Counter-offer: " +
                       f"₹{result['offer']['upfront']:,.0f} upfront, " +
                       f"{result['offer']['settlement_days']} days")
        
        return result
    
    def reset_negotiation_memory(self):
        """Reset negotiation conversation memory"""
        self.negotiation.reset_memory()
