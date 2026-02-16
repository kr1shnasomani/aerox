"""Agent 4: Comms Agent - Generate customer-facing WhatsApp message"""

import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class CommsAgent:
    """Agent 4: Generate natural language WhatsApp message"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.7,  # More creative for messaging
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        self.prompt = PromptTemplate(
            template="""You are AEROXs customer communication specialist. Write a professional WhatsApp message.

**Context:**
Company: {company_name}
Requested Amount: ₹{booking_amount:,.0f}
Current Outstanding: ₹{current_outstanding:,.0f}
Credit Limit: ₹{credit_limit:,.0f}
Route: {route}
Years with Platform: {years_with_platform} years

**Situation:** Booking exceeds available credit by ₹{exceeds_by:,.0f}

**Risk Summary:**
{risk_summary}

**3 Credit Options Available:**

{options_formatted}

**Guidelines:**
- Empathetic, professional tone
- Acknowledge their {years_with_platform}+ year relationship
- Present all 3 options clearly with labels A/B/C
- Recommend Option A (lowest friction)
- Clear CTA: Reply A, B, or C
- 150-200 words max
- Use emojis sparingly (⚡ for recommended, 📅 for standard, 💰 for partial)

**Output Format (JSON):**
{{
    "subject": "Credit Options for ₹{booking_amount:,.0f} Booking",
    "body": "your message here",
    "cta_buttons": ["Select A", "Select B", "Select C", "Support"]
}}

Generate the message:""",
            input_variables=[
                "company_name", "booking_amount", "current_outstanding",
                "credit_limit", "route", "years_with_platform", "exceeds_by",
                "risk_summary", "options_formatted"
            ]
        )
    
    def compose_message(
        self,
        booking_request: dict,
        options: list,
        risk_assessment: dict,
        company_data: dict
    ) -> dict:
        """
        Generate WhatsApp message with credit options
        
        Returns:
            Dict with subject, body, cta_buttons
        """
        # Format options for prompt
        options_text = []
        for opt in options:
            if opt['type'] == 'shortened_settlement':
                options_text.append(
                    f"**Option {opt['option_id']}** ⚡ Recommended\n" +
                    f"Settle within **{opt['settlement_days']} days** (no upfront)\n" +
                    f"→ Full ₹{opt['approved_amount']:,.0f} approved"
                )
            elif opt['type'] == 'upfront_payment':
                options_text.append(
                    f"**Option {opt['option_id']}** 📅 Standard timeline\n" +
                    f"Pay **₹{opt['upfront_amount']:,.0f} upfront**\n" +
                    f"→ Remaining ₹{opt['approved_amount'] - opt['upfront_amount']:,.0f} in {opt['settlement_days']} days"
                )
            elif opt['type'] == 'partial_approval':
                options_text.append(
                    f"**Option {opt['option_id']}** 💰 Reduced amount\n" +
                    f"Approve **₹{opt['approved_amount']:,.0f}** with {opt['settlement_days']}-day settlement\n" +
                    f"→ Request more credit later"
                )
        
        options_formatted = "\n\n".join(options_text)
        
        # Calculate exceeds_by
        exceeds_by = booking_request['current_outstanding'] + booking_request['booking_amount'] - booking_request['credit_limit']
        exceeds_by = max(0, exceeds_by)
        
        try:
            # Format prompt
            formatted_prompt = self.prompt.format(
                company_name=booking_request['company_name'],
                booking_amount=booking_request['booking_amount'],
                current_outstanding=booking_request['current_outstanding'],
                credit_limit=booking_request['credit_limit'],
                route=booking_request['route'],
                years_with_platform=company_data.get('years_with_platform', 2.0),
                exceeds_by=exceeds_by,
                risk_summary=risk_assessment['risk_summary'],
                options_formatted=options_formatted
            )
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse JSON from response
            content = response.content.strip()
            
            # Extract JSON (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            message = json.loads(content)
            
            logger.info(f"[Comms Agent] Generated message ({len(message['body'])} chars)")
            
            return message
            
        except Exception as e:
            logger.error(f"Comms Agent failed: {e}")
            # Fallback to template message
            return self._fallback_message(booking_request, options, company_data)
    
    def _fallback_message(self, booking_request, options, company_data):
        """Fallback message template if LLM fails"""
        body = f"""Hi {booking_request['company_name']},

Your ₹{booking_request['booking_amount']:,.0f} booking ({booking_request['route']}) is ready! However, it exceeds your available credit.

We've reviewed your account - you've been a valued partner for {company_data.get('years_with_platform', 2):.1f}+ years. We can approve this with one of these options:

**Option A** ⚡ Recommended
Settle within 7 days (no upfront)
→ Full ₹{options[0]['approved_amount']:,.0f} approved

**Option B** 📅 Standard
Pay upfront amount
→ Balance in 30 days

**Option C** 💰 Reduced
Lower amount approved
→ Request more later

Reply **A**, **B**, or **C** to proceed.
Need help? Click 'Support' below.

— AEROX Credit Team"""
        
        return {
            "subject": f"Credit Options for ₹{booking_request['booking_amount']:,.0f} Booking",
            "body": body,
            "cta_buttons": ["Select A", "Select B", "Select C", "Support"]
        }
