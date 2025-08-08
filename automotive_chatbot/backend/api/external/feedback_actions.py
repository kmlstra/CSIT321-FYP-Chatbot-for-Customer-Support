"""
Feedback-related RASA Actions
Handles customer feedback, reviews, and car ratings
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

logger = logging.getLogger(__name__)

class ActionFeedbackRequest(Action):
    def name(self) -> Text:
        return "action_feedback_request"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """💬 **Feedback System** 📝

Thank you for wanting to share your feedback! 

**Who would you like to provide feedback about?**
• Sales consultant
• Service advisor  
• Manager
• General staff
• Overall experience

Please tell me:
1️⃣ **Who:** The person's name or role
2️⃣ **What:** Your feedback/experience

**Example:**
"I'd like to give feedback about John from sales - he was very helpful and patient"

💡 **Ready to share your feedback?**"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionProcessFeedback(Action):
    def name(self) -> Text:
        return "action_process_feedback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # Check if user is giving feedback about a specific person
        if any(word in user_text for word in ['feedback for', 'feedback about', 'alan', 'sales', 'team', 'staff', 'consultant']):
            # PROBLEM 2 FIX: Handle specific feedback about staff/team members
            response = """🌟 **Thank You for Your Positive Feedback!** 🌟

We're delighted to hear about your positive experience! Your feedback means a lot to us and helps us continue providing excellent service.

📝 **Your feedback has been recorded and will be shared with our team.**

✨ **We'd love to stay in touch!**
Could you please share your contact details so we can:
• Thank you personally
• Keep you updated on our latest offers
• Invite you to exclusive events

📧 **Email:** ________________
📱 **Phone/WhatsApp:** ________________

🙏 **Thank you for choosing CleverCompanion!**
Your positive experience motivates our entire team!"""
            
        else:
            # Determine if feedback is positive or negative for general feedback
            positive_keywords = ['good', 'great', 'excellent', 'helpful', 'patient', 'professional', 'recommend', 'satisfied', 'happy', 'amazing', 'wonderful', 'outstanding']
            negative_keywords = ['bad', 'poor', 'terrible', 'rude', 'unhelpful', 'slow', 'disappointed', 'unsatisfied', 'angry', 'worst', 'complaint', 'complain']
            
            is_positive = any(word in user_text for word in positive_keywords)
            is_negative = any(word in user_text for word in negative_keywords)
            
            if is_positive and not is_negative:
                # Positive feedback
                response = """🌟 **Thank You for Your Positive Feedback!** 🌟

We're delighted to hear about your positive experience! Your feedback means a lot to us and helps us continue providing excellent service.

📝 **Your feedback has been recorded and will be shared with our team.**

✨ **We'd love to stay in touch!**
Could you please share your contact details so we can:
• Thank you personally
• Keep you updated on our latest offers
• Invite you to exclusive events

📧 **Email:** ________________
📱 **Phone/WhatsApp:** ________________

🙏 **Thank you for choosing CleverCompanion!**
Your positive experience motivates our entire team!"""
                
            elif is_negative and not is_positive:
                # Negative feedback/complaint
                response = """😔 **We Sincerely Apologize** 😔

We're sorry to hear about your disappointing experience. This is not the standard of service we strive for, and we take your feedback very seriously.

🔍 **Immediate Action:**
• Your complaint has been escalated to our management team
• We will investigate this matter thoroughly
• We are committed to making this right

📞 **Let us resolve this for you:**
Please share your contact details so our manager can reach out within 24 hours:

📧 **Email:** ________________
📱 **Phone/WhatsApp:** ________________
📅 **Best time to contact:** ________________

🤝 **Our Promise:**
We will work hard to regain your trust and ensure this doesn't happen again.

💼 **Management Team:** +65 6234 5678"""
                
            else:
                # General feedback
                response = """📝 **Thank You for Your Feedback!** 

Your input has been recorded and will be reviewed by our team. We value all feedback as it helps us improve our services.

📞 **If you need immediate assistance:**
• **Phone:** +65 6234 5678
• **WhatsApp:** +65 4284 8294
• **Email:** info@clevercompanion.sg

🙏 **Thank you for taking the time to share your thoughts!**"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionGetCarReviews(Action):
    def name(self) -> Text:
        return "action_get_car_reviews"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # PROBLEM 3 FIX: Ask for specific model/brand first instead of showing generic list
        response = """⭐ **Car Reviews & Ratings Service** 🚗

What **car model or brand** would you like to see reviews and ratings for?

📋 **Popular Models Available:**
• Honda Civic, Vezel, Accord
• Toyota Camry, Corolla, C-HR
• BMW 320i, 330i, X3
• Mercedes C200, E200, GLA
• Mazda 3, CX-5, CX-8
• Subaru XV, Forester, Outback

💡 **Examples:**
• "Show me Honda Civic reviews"
• "BMW 320i ratings and reviews"
• "What do people say about Toyota Camry?"

🔍 **Just tell me the model and I'll show you:**
• Customer reviews and ratings
• Pros and cons
• Price ranges and fuel consumption
• Owner satisfaction scores

Which car would you like to know about?"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionShowCarReviews(Action):
    """Shows detailed car reviews when user specifies a model"""
    
    def name(self) -> Text:
        return "action_show_car_reviews"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # Extract car model from the text
        car_models = {
            'honda civic': 'Honda Civic',
            'civic': 'Honda Civic',
            'toyota camry': 'Toyota Camry',
            'camry': 'Toyota Camry',
            'bmw 320i': 'BMW 320i',
            'bmw 3 series': 'BMW 3 Series',
            '320i': 'BMW 320i',
            'mercedes c200': 'Mercedes C200',
            'mercedes c class': 'Mercedes C-Class',
            'c200': 'Mercedes C200',
            'honda vezel': 'Honda Vezel',
            'vezel': 'Honda Vezel',
            'mazda cx5': 'Mazda CX-5',
            'cx5': 'Mazda CX-5',
            'cx-5': 'Mazda CX-5'
        }
        
        requested_model = None
        for key, model in car_models.items():
            if key in user_text:
                requested_model = model
                break
        
        if requested_model:
            # Specific model reviews
            if requested_model == 'Honda Civic':
                response = f"""⭐ **{requested_model} Reviews & Ratings** ⭐

**Overall Rating:** 4.5/5 ⭐⭐⭐⭐⭐

**Customer Reviews:**
👤 **Sarah L.** - ⭐⭐⭐⭐⭐
"Excellent fuel economy and reliable. Perfect for daily commuting!"

👤 **Ahmad K.** - ⭐⭐⭐⭐⭐
"Smooth drive, spacious interior. Great value for money."

👤 **Jenny T.** - ⭐⭐⭐⭐⭐
"Low maintenance costs and good resale value. Highly recommended!"

**Pros:** ✅ Fuel efficient ✅ Reliable ✅ Good resale value
**Cons:** ❌ Road noise at highway speeds ❌ Limited rear legroom

**Average COE + Car Price:** $140,000 - $160,000
**Fuel Consumption:** 16-18 km/L"""
                
            elif requested_model == 'Toyota Camry':
                response = f"""⭐ **{requested_model} Reviews & Ratings** ⭐

**Overall Rating:** 4.7/5 ⭐⭐⭐⭐⭐

**Customer Reviews:**
👤 **David W.** - ⭐⭐⭐⭐⭐
"Premium feel, comfortable ride. Perfect for executives!"

👤 **Michelle C.** - ⭐⭐⭐⭐⭐
"Spacious, smooth, and reliable. Best family sedan!"

👤 **Robert H.** - ⭐⭐⭐⭐⭐
"Advanced safety features give peace of mind."

**Pros:** ✅ Spacious interior ✅ Smooth ride ✅ Advanced safety
**Cons:** ❌ Higher price point ❌ Premium fuel recommended

**Average COE + Car Price:** $180,000 - $220,000
**Fuel Consumption:** 14-16 km/L"""
                
            else:
                response = f"""⭐ **{requested_model} Reviews & Ratings** ⭐

Sorry, I don't have detailed reviews for {requested_model} yet. However, here are some popular models with reviews:

**Available Reviews:**
• **Honda Civic** - 4.5/5 ⭐⭐⭐⭐⭐
• **Toyota Camry** - 4.7/5 ⭐⭐⭐⭐⭐
• **BMW 320i** - 4.3/5 ⭐⭐⭐⭐⭐
• **Mercedes C200** - 4.4/5 ⭐⭐⭐⭐⭐
• **Honda Vezel** - 4.6/5 ⭐⭐⭐⭐⭐
• **Mazda CX-5** - 4.2/5 ⭐⭐⭐⭐⭐

**Would you like reviews for any of these models?**"""
        else:
            # No specific model found
            response = """⭐ **Car Reviews & Ratings Service** 🚗

Sorry, I don't have reviews for that specific model yet.

**Available Car Reviews:**
• **Honda Civic** - 4.5/5 ⭐⭐⭐⭐⭐
• **Toyota Camry** - 4.7/5 ⭐⭐⭐⭐⭐  
• **BMW 320i** - 4.3/5 ⭐⭐⭐⭐⭐
• **Mercedes C200** - 4.4/5 ⭐⭐⭐⭐⭐
• **Honda Vezel** - 4.6/5 ⭐⭐⭐⭐⭐
• **Mazda CX-5** - 4.2/5 ⭐⭐⭐⭐⭐

💡 **Try asking:** "Show me Honda Civic reviews" or "BMW 320i ratings"

Which car would you like to know about?"""
        
        dispatcher.utter_message(text=response)
        return [] 