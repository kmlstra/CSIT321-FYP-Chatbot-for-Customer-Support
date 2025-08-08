"""
Default and Fallback RASA Actions
Handles fallback responses and default behaviors
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
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

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🤔 **I'm not sure I understand that request.**

I can help you with:
• 🚗 **Vehicle Information** - Car details, specifications, availability
• 💰 **COE Prices** - Current prices, predictions, category explanations
• 🏦 **Loan Calculations** - Monthly payments, interest rates, requirements
• 🔧 **Maintenance** - Service schedules, repair guidance, booking appointments
• 📞 **Contact Information** - Phone, email, location, operating hours
• 🛞 **Test Drives** - Schedule test drives for available vehicles

Could you please rephrase your question or choose one of the topics above? 😊"""
        
        dispatcher.utter_message(text=response)
        return []

# New action for capability confirmation responses
class ActionCapabilityConfirm(Action):
    def name(self) -> Text:
        return "action_capability_confirm"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # Determine what capability they're asking about
        if any(word in user_text for word in ['calculate', 'loan', 'financing']):
            capability = "loan calculations"
            details = "I can help you calculate monthly payments, interest rates, and loan requirements for vehicle purchases."
        elif any(word in user_text for word in ['coe', 'price', 'predict']):
            capability = "COE price information and predictions"
            details = "I can provide current COE prices, historical trends, and forecasts for different categories."
        elif any(word in user_text for word in ['maintenance', 'service', 'repair']):
            capability = "maintenance guidance"
            details = "I can provide maintenance schedules, service recommendations, and help you book appointments."
        elif any(word in user_text for word in ['vehicle', 'car', 'recommend']):
            capability = "vehicle recommendations"
            details = "I can suggest vehicles based on your budget, preferences, and requirements."
        else:
            capability = "automotive assistance"
            details = "I can help with COE prices, loan calculations, vehicle information, maintenance guidance, and more."
        
        response = f"""✅ **Yes, I definitely can help you with {capability}!**

{details}

What specific information would you like to know? I'm here to assist you! 🚗"""
        
        dispatcher.utter_message(text=response)
        return [] 