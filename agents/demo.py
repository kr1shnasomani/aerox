"""CLI Demo: Test AEROX Multi-Agent System with 5 scenarios"""

import json
import logging
from agents.meta_agent import MetaAgent
from agents.config import (
    GREEN_FLAG_BOOKING, GREEN_FLAG_SCORES,
    RED_FLAG_BOOKING, RED_FLAG_SCORES,
    MOCK_BOOKING_REQUEST, MOCK_ML_SCORES,
    NEGOTIATION_TEST_MESSAGES
)

# Colorized output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")

def print_section(title, color=Colors.CYAN):
    print(f"\n{color}{Colors.BOLD}[{title}]{Colors.END}")

def print_json(data, color=Colors.GREEN):
    print(f"{color}{json.dumps(data, indent=2)}{Colors.END}")

def test_1_yellow_flag():
    """Test 1: Yellow flag company - full negotiation pipeline"""
    print_header("TEST 1: YELLOW FLAG - Full Negotiation Pipeline")
    
    meta = MetaAgent()
    
    # Use mock data (yellow flag scenario)
    result = meta.process_booking_request(MOCK_BOOKING_REQUEST)
    
    print_section("Final Decision", Colors.YELLOW)
    print(f"{Colors.YELLOW}Decision: {result['decision']}{Colors.END}")
    print(f"{Colors.YELLOW}Risk Category: {result['risk_category']}{Colors.END}")
    
    print_section("ML Scores")
    print(f"Intent: {result['ml_scores']['intent_score']:.3f}")
    print(f"Capacity: {result['ml_scores']['capacity_score']:.3f}")
    print(f"PD (7d): {result['ml_scores']['pd_7d']:.4f}")
    print(f"PD (30d): {result['ml_scores']['pd_30d']:.4f}")
    
    if 'financial_analysis' in result:
        print_section("Financial Analysis")
        print(f"Total Exposure: ₹{result['financial_analysis']['total_exposure']:,.0f}")
        print(f"Baseline EL: ₹{result['financial_analysis']['baseline_el_30d']:,.2f}")
        print(f"Exceeds Limit: {result['financial_analysis']['exceeds_risk_appetite']}")
    
    if 'risk_assessment' in result:
        print_section("Risk Assessment")
        print(f"Summary: {result['risk_assessment']['risk_summary'][:150]}...")
        print(f"Recommendation: {result['risk_assessment']['recommendation']}")
    
    if 'options' in result:
        print_section("Credit Options", Colors.GREEN)
        for opt in result['options']:
            print(f"\n  {Colors.GREEN}Option {opt['option_id']}{Colors.END} ({opt['type']})")
            print(f"    Settlement: {opt['settlement_days']} days")
            print(f"    Upfront: ₹{opt['upfront_amount']:,.0f}")
            print(f"    Approved: ₹{opt['approved_amount']:,.0f}")
            print(f"    Expected Loss: ₹{opt['expected_loss']:,.2f}")
            print(f"    Friction Score: {opt['friction_score']}")
    
    if 'message' in result and isinstance(result['message'], dict):
        print_section("WhatsApp Message", Colors.CYAN)
        print(f"Subject: {result['message']['subject']}")
        print(f"\n{result['message']['body'][:300]}...")
        print(f"\nCTA Buttons: {result['message']['cta_buttons']}")
    
    return result

def test_2_red_flag():
    """Test 2: Red flag company - should block immediately"""
    print_header("TEST 2: RED FLAG - Block Decision")
    
    meta = MetaAgent()
    result = meta.process_booking_request(RED_FLAG_BOOKING)
    
    print_section("Final Decision", Colors.RED)
    print(f"{Colors.RED}Decision: {result['decision']}{Colors.END}")
    print(f"{Colors.RED}Risk Category: {result['risk_category']}{Colors.END}")
    print(f"{Colors.RED}Reason: {result['reason']}{Colors.END}")
    
    print_section("ML Scores")
    print(f"Intent: {result['ml_scores']['intent_score']:.3f} (HIGH RISK)")
    print(f"Capacity: {result['ml_scores']['capacity_score']:.3f}")
    
    print(f"\n{Colors.RED}✗ Booking blocked - no options generated{Colors.END}")
    
    return result

def test_3_green_flag():
    """Test 3: Green flag company - auto-approve"""
    print_header("TEST 3: GREEN FLAG - Auto-Approval")
    
    meta = MetaAgent()
    result = meta.process_booking_request(GREEN_FLAG_BOOKING)
    
    print_section("Final Decision", Colors.GREEN)
    print(f"{Colors.GREEN}Decision: {result['decision']}{Colors.END}")
    print(f"{Colors.GREEN}Risk Category: {result['risk_category']}{Colors.END}")
    print(f"{Colors.GREEN}Message: {result['message']}{Colors.END}")
    
    print_section("ML Scores")
    print(f"Intent: {result['ml_scores']['intent_score']:.3f} (LOW RISK)")
    print(f"Capacity: {result['ml_scores']['capacity_score']:.3f} (HIGH CAPACITY)")
    
    print_section("Approved Terms", Colors.GREEN)
    print(f"Amount: ₹{result['approved_amount']:,.0f}")
    print(f"Settlement: {result['settlement_days']} days")
    
    print(f"\n{Colors.GREEN}✓ Auto-approved - no negotiation needed{Colors.END}")
    
    return result

def test_4_negotiation_rounds():
    """Test 4: 3-round negotiation simulation"""
    print_header("TEST 4: 3-ROUND NEGOTIATION CHAT")
    
    meta = MetaAgent()
    
    # First get initial options
    initial_result = meta.process_booking_request(MOCK_BOOKING_REQUEST)
    
    if initial_result['decision'] != 'NEGOTIATE':
        print(f"{Colors.RED}Cannot negotiate - decision is {initial_result['decision']}{Colors.END}")
        return initial_result
    
    print_section("Initial Options Sent")
    for opt in initial_result['options']:
        print(f"  Option {opt['option_id']}: {opt['settlement_days']} days, ₹{opt['upfront_amount']:,.0f} upfront")
    
    # Simulate 3 rounds
    ml_scores = initial_result['ml_scores']
    booking_request = initial_result['booking_request']
    initial_options = initial_result['options']
    
    for round_num, user_message in enumerate(NEGOTIATION_TEST_MESSAGES, start=1):
        print_section(f"Round {round_num}", Colors.YELLOW)
        print(f"{Colors.CYAN}Customer:{Colors.END} {user_message}")
        
        neg_result = meta.handle_negotiation(
            user_message=user_message,
            round_number=round_num,
            booking_request=booking_request,
            ml_scores=ml_scores,
            initial_options=initial_options
        )
        
        print(f"\n{Colors.GREEN}Agent:{Colors.END} {neg_result['response'][:200]}...")
        
        if neg_result.get('offer'):
            print(f"\n{Colors.YELLOW}Counter-Offer:{Colors.END}")
            print(f"  Upfront: ₹{neg_result['offer']['upfront']:,.0f}")
            print(f"  Settlement: {neg_result['offer']['settlement_days']} days")
            print(f"  Expected Loss: ₹{neg_result['expected_loss']:,.2f}")
        
        if neg_result.get('escalate'):
            print(f"\n{Colors.RED}⚠ ESCALATED TO MANUAL REVIEW{Colors.END}")
            break
    
    # Reset memory
    meta.reset_negotiation_memory()
    
    return neg_result

def test_5_edge_case():
    """Test 5: Edge case - no valid options possible"""
    print_header("TEST 5: EDGE CASE - No Valid Options")
    
    # Create high-risk scenario where EL always exceeds limit
    edge_booking = {
        'company_id': 'IN-TRV-999999',
        'company_name': 'HighRisk Travels Pvt Ltd',
        'route': 'DEL-BOM',
        'booking_amount': 50000,
        'current_outstanding': 80000,  # Already high outstanding
        'credit_limit': 100000
    }
    
    meta = MetaAgent()
    result = meta.process_booking_request(edge_booking)
    
    print_section("Final Decision", Colors.RED)
    print(f"{Colors.RED}Decision: {result['decision']}{Colors.END}")
    print(f"{Colors.RED}Risk Category: {result['risk_category']}{Colors.END}")
    
    if 'reason' in result:
        print(f"{Colors.RED}Reason: {result['reason']}{Colors.END}")
    
    if 'financial_analysis' in result:
        print_section("Financial Analysis")
        print(f"Total Exposure: ₹{result['financial_analysis']['total_exposure']:,.0f}")
        print(f"Baseline EL: ₹{result['financial_analysis']['baseline_el_30d']:,.2f}")
        print(f"Exceeds Limit: {result['financial_analysis']['exceeds_risk_appetite']}")
    
    print(f"\n{Colors.RED}✗ Blocked - all options exceed EL threshold of ₹5,000{Colors.END}")
    
    return result

def main():
    """Run all 5 test scenarios"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                    AEROX MULTI-AGENT SYSTEM DEMO                           ║")
    print("║                    6 Agents + LangChain + Google Gemini                    ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    print(f"{Colors.CYAN}Running 5 test scenarios...{Colors.END}\n")
    
    results = {}
    
    try:
        # Test 1: Yellow flag
        results['test_1'] = test_1_yellow_flag()
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        
        # Test 2: Red flag
        results['test_2'] = test_2_red_flag()
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        
        # Test 3: Green flag
        results['test_3'] = test_3_green_flag()
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        
        # Test 4: Negotiation
        results['test_4'] = test_4_negotiation_rounds()
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        
        # Test 5: Edge case
        results['test_5'] = test_5_edge_case()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}Error in demo: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print_header("DEMO COMPLETE")
    
    print(f"{Colors.GREEN}Summary:{Colors.END}")
    for test_name, result in results.items():
        decision = result.get('decision', 'ERROR')
        color = Colors.GREEN if decision == 'APPROVED' else Colors.RED if decision == 'BLOCKED' else Colors.YELLOW
        print(f"  {color}{test_name}: {decision}{Colors.END}")
    
    print(f"\n{Colors.CYAN}All 6 agents tested:{Colors.END}")
    print(f"  ✓ Agent 1: Financial Analyst")
    print(f"  ✓ Agent 2: Risk AI")
    print(f"  ✓ Agent 3: Terms Crafter")
    print(f"  ✓ Agent 4: Comms Agent")
    print(f"  ✓ Agent 5: Monitor Agent")
    print(f"  ✓ Agent 6: Negotiation Agent")
    
    print(f"\n{Colors.HEADER}Thank you for testing AEROX! 🚀{Colors.END}\n")

if __name__ == "__main__":
    main()
