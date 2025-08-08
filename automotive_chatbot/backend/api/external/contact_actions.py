"""
Contact and Location-related RASA Actions
Handles contact information, store location, and operating hours
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

class ActionEmailOnly(Action):
    def name(self) -> Text:
        return "action_email_only"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """📧 **Thank you for contacting us!**

Here's our email for your convenience:

📧 **Email:**
info@clevercompanion.sg

<button onclick="window.open('mailto:info@clevercompanion.sg', '_blank')" style="background: #FF6B35; color: white; border: none; padding: 12px 24px; border-radius: 25px; cursor: pointer; font-size: 14px; margin: 10px 0; display: inline-block;">📧 Email me now</button>"""
# <button onclick="window.open('mailto:info@clevercompanion.sg', '_blank')" style="background: #FF6B35; color: white; border: none; padding: 12px 24px; border-radius: 25px; cursor: pointer; font-size: 14px; margin: 10px 0; display: inline-block; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(255, 107, 53, 0.3);" onmouseover="this.style.background='#E5522A'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(255, 107, 53, 0.4)';" onmouseout="this.style.background='#FF6B35'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(255, 107, 53, 0.3)';">📧 Email me now</button>"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionPhoneOnly(Action):
    def name(self) -> Text:
        return "action_phone_only"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """📞 **Thank you for contacting us!**

Here's our phone number for your convenience:

📞 **Phone:**
+65 6234 5678

<button onclick="window.open('tel:+6562345678', '_blank')" style="background: #007AFF; color: white; border: none; padding: 12px 24px; border-radius: 25px; cursor: pointer; font-size: 14px; margin: 10px 0; display: inline-block;">📞 Call me now</button>"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionWhatsAppOnly(Action):
    def name(self) -> Text:
        return "action_whatsapp_only"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """💬 **Thank you for contacting us!**

Here's our WhatsApp for your convenience:

📱 **WhatsApp:**
+65 4284 8294

<button onclick="window.open('https://wa.me/6542848294', '_blank')" style="background: #25D366; color: white; border: none; padding: 12px 24px; border-radius: 25px; cursor: pointer; font-size: 14px; margin: 10px 0; display: inline-block;">📱 WhatsApp me now</button>"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionContactUs(Action):
    def name(self) -> Text:
        return "action_contact_us"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """📞 **Contact CleverCompanion Singapore** 🚗

📱 **WhatsApp:** +65 4284 8294
<button onclick="window.open('https://wa.me/6542848294', '_blank')" style="background: #25D366; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 12px; margin: 5px 0; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(37, 211, 102, 0.3);" onmouseover="this.style.background='#1DA851'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(37, 211, 102, 0.4)';" onmouseout="this.style.background='#25D366'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(37, 211, 102, 0.3)';">📱 WhatsApp me now</button>

📞 **Phone:** +65 6234 5678
<button onclick="window.open('tel:+6562345678', '_blank')" style="background: #007AFF; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 12px; margin: 5px 0; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0, 122, 255, 0.3);" onmouseover="this.style.background='#0056CC'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(0, 122, 255, 0.4)';" onmouseout="this.style.background='#007AFF'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0, 122, 255, 0.3)';">📞 Call me now</button>

📧 **Email:** info@clevercompanion.sg
<button onclick="window.open('mailto:info@clevercompanion.sg', '_blank')" style="background: #FF6B35; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 12px; margin: 5px 0; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(255, 107, 53, 0.3);" onmouseover="this.style.background='#E5522A'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(255, 107, 53, 0.4)';" onmouseout="this.style.background='#FF6B35'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(255, 107, 53, 0.3)';">📧 Email me now</button>

🏪 **Visit our showroom:**
**📍 Address:**
**350 Orchard Road, Shaw House**
**#05-02, Singapore 238868**

<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3988.779267047514!2d103.84868561534441!3d1.3073684621171985!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x31da1911a97c1e01%3A0x96c9b587f3c75e99!2s123%20Main%20St%2C%20Singapore!5e0!3m2!1sen!2ssg!4v1625067890123" width="250" height="150" style="border:0; border-radius: 10px; margin: 10px 0;" allowfullscreen="" loading="lazy"></iframe>

<button onclick="window.open('https://maps.google.com?q=123+Main+Street+Singapore', '_blank')" style="background: #4285F4; color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; font-size: 12px; margin: 5px 0; display: inline-block;">📍 View on Google Maps</button>

🎯 Ready to help with all your automotive needs!"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionStoreLocation(Action):
    def name(self) -> Text:
        return "action_store_location"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """📍 **CleverCompanion Showroom Location** 🏪

**📍 Address:**
**350 Orchard Road, Shaw House**
**#05-02, Singapore 238868**

🚇 **Nearest MRT:** Orchard MRT (NS22/TE14) - 2 mins walk
🚌 **Bus Stops:** Orchard Road (Bus Stop 09037, 09038)
🅿️ **Parking:** Shaw House Carpark (Levels B3-B6)

<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3988.8152!2d103.8316!3d1.3048!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x31da19a6b1234567%3A0x987654321abcdef0!2sShaw%20House%2C%20350%20Orchard%20Rd%2C%20Singapore!5e0!3m2!1sen!2ssg!4v1625067890123" width="280" height="180" style="border:0; border-radius: 15px; margin: 15px 0;" allowfullscreen="" loading="lazy"></iframe>

<button onclick="window.open('https://maps.google.com?q=350+Orchard+Road+Shaw+House+Singapore', '_blank')" style="background: #4285F4; color: white; border: none; padding: 12px 24px; border-radius: 25px; cursor: pointer; font-size: 14px; margin: 10px 0; display: inline-block;">📍 View on Google Maps</button>

🚗 **Premium showroom in the heart of Orchard Road!**"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionOperatingHours(Action):
    def name(self) -> Text:
        return "action_operating_hours"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # Extract specific day from user query
        days = {
            'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
            'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday', 'sunday': 'Sunday',
            'mon': 'Monday', 'tue': 'Tuesday', 'wed': 'Wednesday',
            'thu': 'Thursday', 'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday'
        }
        
        specific_day = None
        for day_key, day_name in days.items():
            if day_key in user_text:
                specific_day = day_name
                break
        
        if 'public holiday' in user_text or 'ph' in user_text:
            response = """🏛️ **Public Holiday Hours**

**We are CLOSED on all public holidays**

📅 **Regular Operating Hours:**
**📅 Monday - Friday:** 9:00 AM - 7:00 PM
**📅 Saturday:** 9:00 AM - 6:00 PM  
**📅 Sunday:** 10:00 AM - 5:00 PM"""
            
        elif specific_day:
            if specific_day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                response = f"""⏰ **Operating hours on {specific_day}:**
9:00 AM - 7:00 PM
(Except public holidays)"""
            elif specific_day == 'Saturday':
                response = f"""⏰ **Operating hours on {specific_day}:**
9:00 AM - 6:00 PM
(Except public holidays)"""
            elif specific_day == 'Sunday':
                response = f"""⏰ **Operating hours on {specific_day}:**
10:00 AM - 5:00 PM
(Except public holidays)"""
        else:
            response = """📅 **Operating Hours**

**📅 Monday - Friday:** 9:00 AM - 7:00 PM
**📅 Saturday:** 9:00 AM - 6:00 PM  
**📅 Sunday:** 10:00 AM - 5:00 PM
**🏛️ Public Holidays:** CLOSED"""
          
        dispatcher.utter_message(text=response)
        return []

# Missing action that was causing RASA exception
class ActionProvideBusinessHours(Action):
    def name(self) -> Text:
        return "action_provide_business_hours"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # Extract specific day from user query
        days = {
            'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
            'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday', 'sunday': 'Sunday',
            'mon': 'Monday', 'tue': 'Tuesday', 'wed': 'Wednesday',
            'thu': 'Thursday', 'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday'
        }
        
        specific_day = None
        for day_key, day_name in days.items():
            if day_key in user_text:
                specific_day = day_name
                break
        
        # Check for closing time requests
        if any(word in user_text for word in ['close', 'closed', 'closing', 'end']):
            if specific_day:
                if specific_day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                    response = f"""⏰ **Closing time on {specific_day}:**
7:00 PM
(Except public holidays)"""
                elif specific_day == 'Saturday':
                    response = f"""⏰ **Closing time on {specific_day}:**
6:00 PM
(Except public holidays)"""
                elif specific_day == 'Sunday':
                    response = f"""⏰ **Closing time on {specific_day}:**
5:00 PM
(Except public holidays)"""
            else:
                response = """⏰ **Closing Times**

**📅 Monday - Friday:** 7:00 PM
**📅 Saturday:** 6:00 PM  
**📅 Sunday:** 5:00 PM
**🏛️ Public Holidays:** CLOSED"""
        
        elif specific_day:
            if specific_day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                response = f"""⏰ **Operating hours on {specific_day}:**
9:00 AM - 7:00 PM
(Except public holidays)"""
            elif specific_day == 'Saturday':
                response = f"""⏰ **Operating hours on {specific_day}:**
9:00 AM - 6:00 PM
(Except public holidays)"""
            elif specific_day == 'Sunday':
                response = f"""⏰ **Operating hours on {specific_day}:**
10:00 AM - 5:00 PM
(Except public holidays)"""
        else:
            response = """📅 **Operating Hours**

**📅 Monday - Friday:** 9:00 AM - 7:00 PM
**📅 Saturday:** 9:00 AM - 6:00 PM  
**📅 Sunday:** 10:00 AM - 5:00 PM
**🏛️ Public Holidays:** CLOSED"""
          
        dispatcher.utter_message(text=response)
        return []

# Note: Feedback actions have been moved to feedback_actions.py 