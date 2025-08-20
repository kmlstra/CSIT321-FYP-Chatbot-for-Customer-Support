"""
Default and Fallback RASA Actions
Handles fallback responses and default behaviors
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
import requests
import os
import json
import time
import pandas as pd
import re
from datetime import datetime, timedelta
from .auto_logger import AutoLoggedAction
from api.middleware.intent_validation_middleware import validate_medium_confidence

class ActionDefaultFallback(AutoLoggedAction):
    """
    Default fallback action with intent validation middleware integration.
    """
    def name(self) -> Text:
        return "action_default_fallback"

    # @validate_medium_confidence(confidence_threshold=0.5)
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Log user message and action execution
        self.log_user_message(tracker)
        self.log_action_execution("ActionDefaultFallback", tracker)
        
        response = """🤔 I'm not sure I understand that request.

        I can help you with:
        • 💰 COE Prices - Current prices, predictions, category explanations
        • 🏦 Loan Calculations - Monthly payments, interest rates, requirements
        • 📅 Appointment Booking - Test Drive, Sales Consultation, Trade-in Evaluation
        • 📞 Contact Information - Phone, email, location, operating hours

        Could you please rephrase your question or choose one of the topics above? 😊"""
        
        dispatcher.utter_message(text=response)
        
        # Log bot response
        self.log_bot_response(dispatcher, tracker, "ActionDefaultFallback")
        
        return []

# New action for capability confirmation responses
class ActionCapabilityConfirm(AutoLoggedAction):
    """
    Capability confirmation action with intent validation middleware integration.
    """
    def name(self) -> Text:
        return "action_capability_confirm"

    @validate_medium_confidence(confidence_threshold=0.6)
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Log user message and action execution
        self.log_user_message(tracker)
        self.log_action_execution("ActionCapabilityConfirm", tracker)
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # Determine what capability they're asking about
        if any(word in user_text for word in ['calculate', 'loan', 'financing']):
            capability = "loan calculations"
            details = "I can help you calculate monthly payments, interest rates, and loan requirements for vehicle purchases."
        elif any(word in user_text for word in ['coe', 'price', 'predict']):
            capability = "COE price information and predictions"
            details = "I can provide current COE prices, historical trends, and forecasts for different categories."
        elif any(word in user_text for word in ['appointment', 'booking', 'schedule']):
            capability = "appointment booking"
            details = "I can help you book appointments for Test Drive, Sales Consultation, or Trade-in Evaluation."
        else:
            capability = "automotive assistance"
            details = "I can help with COE prices, loan calculations, vehicle information, maintenance guidance, and more."
        
        response = f"""✅ **Yes, I definitely can help you with {capability}!**

{details}

What specific information would you like to know? I'm here to assist you! 🚗"""
        
        dispatcher.utter_message(text=response)
        
        # Log bot response
        self.log_bot_response(dispatcher, tracker, "ActionCapabilityConfirm")
        
        return []


class ActionProvideHelp(AutoLoggedAction):
    """
    Help provision action with intent validation middleware integration.
    """
    def name(self) -> Text:
        return "action_provide_help"

    @validate_medium_confidence(confidence_threshold=0.6)
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Log user message and action execution
        self.log_user_message(tracker)
        self.log_action_execution("ActionProvideHelp", tracker)
        
        response = """🚗 Hi! I'm CleverCompanion, your Singapore automotive assistant!

Here's what I can help you with:

🏷️ COE Information:
• Current COE prices for all categories
• COE trends and predictions
• Category explanations (A, B, C, D, E)
• Bidding process guidance
• Renewal assistance

📊 Vehicle Services:
• Loan calculations and financing options
• Appointment booking (Test Drive, Sales Consultation, Trade-in Evaluation)

📞 Contact & Support:
• Contact information and locations
• Business hours and availability

How can I assist you today? Just ask me about any of these topics, and I'll provide detailed information! 😊"""
        
        dispatcher.utter_message(text=response)
        
        # Log bot response
        self.log_bot_response(dispatcher, tracker, "ActionProvideHelp")
        
        return []


class ActionProvideClarification(AutoLoggedAction):
    """
    Clarification provision action with intent validation middleware integration.
    """
    def name(self) -> Text:
        return "action_provide_clarification"

    @validate_medium_confidence(confidence_threshold=0.6)
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Log user message and action execution
        self.log_user_message(tracker)
        self.log_action_execution("ActionProvideClarification", tracker)
        
        # Get the last bot message to provide context
        events = tracker.events
        last_bot_message = "my previous response"
        
        for event in reversed(events):
            if event.get("event") == "bot" and event.get("text"):
                text = event.get("text", "")
                last_bot_message = text[:100] + "..." if len(text) > 100 else text
                break
        
        response = f"""🤔 Let me clarify that for you!

I understand you'd like more explanation about {last_bot_message if last_bot_message != "my previous response" else "my previous response"}.

I can help explain:
• COE prices and categories in simple terms
• How loan calculations work
• Appointment booking process and available services

What specifically would you like me to explain in more detail?

Feel free to ask me to:
• "Explain COE categories"
• "How does loan calculation work?"
• "What appointment types are available?"
• Or any other question you have!

I'm here to make everything clear and easy to understand! 😊"""
        
        dispatcher.utter_message(text=response)
        
        # Log bot response
        self.log_bot_response(dispatcher, tracker, "ActionProvideClarification")
        
        return []
