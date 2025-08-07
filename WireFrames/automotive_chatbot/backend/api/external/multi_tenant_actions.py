"""
Multi-tenant RASA Actions
Handles client-specific responses and data
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
import requests
import os
import json
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger(__name__)

class MultiTenantActionBase(Action):
    """Base class for multi-tenant actions"""
    
    def get_client_context(self, tracker: Tracker) -> Dict[str, Any]:
        """Extract client context from tracker metadata"""
        try:
            metadata = tracker.latest_message.get("metadata", {})
            return metadata.get("client_config", {})
        except:
            return {}
    
    def get_client_id(self, tracker: Tracker) -> str:
        """Extract client ID from tracker"""
        try:
            metadata = tracker.latest_message.get("metadata", {})
            return metadata.get("client_id", "")
        except:
            return ""
    
    def format_response_with_branding(self, response: str, client_config: Dict[str, Any]) -> str:
        """Apply client-specific branding to response"""
        
        # Replace placeholders with client-specific information
        branding = client_config.get("branding", {})
        contact_info = client_config.get("contact_info", {})
        
        # Replace company name
        company_name = branding.get("company_name", "CleverCompanion")
        response = response.replace("[COMPANY_NAME]", company_name)
        
        # Replace contact information
        if "[PHONE]" in response and contact_info.get("phone"):
            response = response.replace("[PHONE]", contact_info["phone"])
        
        if "[EMAIL]" in response and contact_info.get("email"):
            response = response.replace("[EMAIL]", contact_info["email"])
        
        if "[ADDRESS]" in response and contact_info.get("address"):
            response = response.replace("[ADDRESS]", contact_info["address"])
        
        if "[WHATSAPP]" in response and contact_info.get("whatsapp"):
            response = response.replace("[WHATSAPP]", contact_info["whatsapp"])
        
        return response

class ActionMultiTenantCOEPrices(MultiTenantActionBase):
    def name(self) -> Text:
        return "action_multi_tenant_coe_prices"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        client_config = self.get_client_context(tracker)
        
        # Check if COE prices feature is enabled for this client
        features = client_config.get("features", {})
        if not features.get("coe_prices", True):
            response = f"I'm sorry, COE price information is not available for {client_config.get('branding', {}).get('company_name', 'this service')}. Please contact us directly for pricing information."
            dispatcher.utter_message(text=response)
            return []
        
        # Get COE prices (same logic as original action)
        response = """📊 **Latest COE Prices (Singapore)**

🚗 **Category A:** $96,999 🔴↗ +$1,500
🚙 **Category B:** $113,000 🟢↘ -$2,000  
🚚 **Category C:** $75,500 🟢↘ -$1,500
🏍️ **Category E:** $108,900 🔴↗ -$3,000

📅 **Last Updated:** [TIMESTAMP]

💡 Need help choosing the right category for your vehicle? Ask me about specific car models!

📞 **Contact [COMPANY_NAME]:**
Phone: [PHONE] | Email: [EMAIL]"""
        
        # Apply client branding
        response = response.replace("[TIMESTAMP]", datetime.now().strftime("%d %B %Y, %I:%M %p"))
        response = self.format_response_with_branding(response, client_config)
        
        dispatcher.utter_message(text=response)
        return []

class ActionMultiTenantContactUs(MultiTenantActionBase):
    def name(self) -> Text:
        return "action_multi_tenant_contact_us"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        client_config = self.get_client_context(tracker)
        contact_info = client_config.get("contact_info", {})
        branding = client_config.get("branding", {})
        business_hours = client_config.get("business_hours", {})
        
        company_name = branding.get("company_name", "Our Company")
        
        response = f"""📞 **Contact {company_name}** 🚗

"""
        
        # Add contact methods based on what's available
        if contact_info.get("phone"):
            response += f"""📱 **Phone:** {contact_info['phone']}
<button onclick="window.open('tel:{contact_info['phone']}', '_blank')" style="background: #007AFF; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 12px; margin: 5px 0;">📞 Call Now</button>

"""
        
        if contact_info.get("email"):
            response += f"""📧 **Email:** {contact_info['email']}
<button onclick="window.open('mailto:{contact_info['email']}', '_blank')" style="background: #FF6B35; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 12px; margin: 5px 0;">📧 Email Us</button>

"""
        
        if contact_info.get("whatsapp"):
            response += f"""💬 **WhatsApp:** {contact_info['whatsapp']}
<button onclick="window.open('https://wa.me/{contact_info['whatsapp'].replace('+', '').replace(' ', '')}', '_blank')" style="background: #25D366; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 12px; margin: 5px 0;">💬 WhatsApp</button>

"""
        
        if contact_info.get("address"):
            response += f"""📍 **Address:** {contact_info['address']}

"""
        
        # Add business hours if available
        if business_hours:
            response += """🕐 **Business Hours:**
"""
            for day, hours in business_hours.items():
                if hours and hours.lower() != "closed":
                    response += f"• **{day.capitalize()}:** {hours}\n"
        
        response += f"""
🎯 **Ready to help with all your automotive needs at {company_name}!**"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionMultiTenantVehicleSearch(MultiTenantActionBase):
    def name(self) -> Text:
        return "action_multi_tenant_vehicle_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        client_config = self.get_client_context(tracker)
        client_id = self.get_client_id(tracker)
        
        # Check if vehicle search is enabled
        features = client_config.get("features", {})
        if not features.get("vehicle_search", True):
            company_name = client_config.get("branding", {}).get("company_name", "us")
            response = f"Vehicle search is not available through this chat. Please contact {company_name} directly for our current inventory."
            dispatcher.utter_message(text=response)
            return []
        
        # In a real implementation, you would query the client's vehicle database
        # For now, we'll provide a generic response
        company_name = client_config.get("branding", {}).get("company_name", "our showroom")
        
        response = f"""🚗 **Vehicle Search at {company_name}**

I can help you find the perfect vehicle! Here's what we offer:

**🏷️ Popular Categories:**
• **Family Cars** - 7-seaters, SUVs, MPVs
• **Luxury Vehicles** - Premium sedans and SUVs  
• **Economic Cars** - Fuel-efficient, budget-friendly
• **Electric/Hybrid** - Eco-friendly options

**💡 Tell me what you're looking for:**
• "Show me family cars under $150k"
• "I need a luxury sedan"
• "What hybrid cars do you have?"

**📞 For our complete inventory, contact us:**
Phone: [PHONE] | Email: [EMAIL]

**🎯 Let me know your preferences and I'll help you find the right vehicle!**"""
        
        response = self.format_response_with_branding(response, client_config)
        
        dispatcher.utter_message(text=response)
        return []

class ActionMultiTenantLoanCalculator(MultiTenantActionBase):
    def name(self) -> Text:
        return "action_multi_tenant_loan_calculator"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        client_config = self.get_client_context(tracker)
        
        # Check if loan calculator is enabled
        features = client_config.get("features", {})
        if not features.get("loan_calculator", True):
            company_name = client_config.get("branding", {}).get("company_name", "us")
            response = f"Loan calculation services are not available through this chat. Please contact {company_name} directly for financing options."
            dispatcher.utter_message(text=response)
            return []
        
        company_name = client_config.get("branding", {}).get("company_name", "our finance team")
        
        response = f"""💳 **Vehicle Financing at {company_name}** 🏦

I can help you calculate your vehicle loan! Please provide:

**📋 Required Information:**
• **Car Price:** Total vehicle cost
• **Down Payment:** Amount you can pay upfront  
• **Loan Tenure:** Number of years (1-7 years)

**💡 Example:**
"Calculate loan for $150,000 car with $30,000 down payment for 5 years"

**🏦 We work with major Singapore banks:**
• DBS/POSB: 2.88% - 3.88% p.a.
• OCBC: 2.85% - 3.85% p.a.
• UOB: 2.78% - 3.78% p.a.
• Maybank: 2.68% - 3.68% p.a.

**📞 For personalized financing advice:**
Contact [COMPANY_NAME] at [PHONE] | [EMAIL]

**Ready to calculate your loan? Just provide the details above!**"""
        
        response = self.format_response_with_branding(response, client_config)
        
        dispatcher.utter_message(text=response)
        return []

class ActionMultiTenantTestDrive(MultiTenantActionBase):
    def name(self) -> Text:
        return "action_multi_tenant_test_drive"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        client_config = self.get_client_context(tracker)
        
        # Check if test drive booking is enabled
        features = client_config.get("features", {})
        if not features.get("test_drive_booking", True):
            company_name = client_config.get("branding", {}).get("company_name", "us")
            response = f"Test drive booking is not available through this chat. Please contact {company_name} directly to schedule a test drive."
            dispatcher.utter_message(text=response)
            return []
        
        company_name = client_config.get("branding", {}).get("company_name", "our showroom")
        business_hours = client_config.get("business_hours", {})
        
        response = f"""🚗 **Test Drive Booking at {company_name}** 📅

Ready to experience your next vehicle? I can help you schedule a test drive!

**📋 We'll need:**
• Your preferred vehicle model
• Your preferred date & time
• Valid driving license
• Contact information

**📞 Quick Booking:**
Phone: [PHONE] | WhatsApp: [WHATSAPP]

"""
        
        # Add business hours if available
        if business_hours:
            response += "🕐 **Available Times:**\n"
            for day, hours in business_hours.items():
                if hours and hours.lower() != "closed":
                    response += f"• **{day.capitalize()}:** {hours}\n"
        
        response += f"""
**📍 Visit {company_name}:**
Address: [ADDRESS]

**💡 Example booking request:**
"I want to test drive Honda Civic on Saturday 2pm, my name is John and my contact is 91234567"

**Ready to book your test drive?**"""
        
        response = self.format_response_with_branding(response, client_config)
        
        dispatcher.utter_message(text=response)
        return []