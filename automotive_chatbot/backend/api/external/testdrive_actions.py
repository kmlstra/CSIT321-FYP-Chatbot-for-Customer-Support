"""
Test Drive Booking RASA Actions
Handles test drive bookings, confirmations, and scheduling
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def extract_booking_details(text: str) -> dict:
    """Extract booking details from user text"""
    details = {
        'vehicle': None,
        'date': None,
        'time': None,
        'name': None,
        'phone': None
    }
    
    # Extract vehicle model
    vehicles = ['honda civic', 'toyota camry', 'bmw', 'mercedes', 'audi', 'lexus', 'nissan', 'mazda', 'hyundai', 'kia']
    text_lower = text.lower()
    
    for vehicle in vehicles:
        if vehicle in text_lower:
            details['vehicle'] = vehicle.title()
            break
    
    # Extract date patterns
    date_patterns = [
        r'\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})\b',
        r'\b(\d{1,2})/(\d{1,2})\b',
        r'\b(tomorrow|today|next week)\b'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text_lower)
        if match:
            details['date'] = match.group(0)
            break
    
    # Extract time patterns
    time_patterns = [
        r'\b(\d{1,2})(am|pm)\b',
        r'\b(\d{1,2}):(\d{2})(am|pm)?\b',
        r'\b(\d{1,2})\s*(am|pm)\b'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            details['time'] = match.group(0)
            break
    
    # Extract name (look for "my name is" or "i am")
    name_patterns = [
        r'my name is\s+([a-zA-Z\s]+)',
        r'i am\s+([a-zA-Z\s]+)',
        r'name\s+([a-zA-Z\s]+)'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text_lower)
        if match:
            details['name'] = match.group(1).strip()
            break
    
    # Extract phone number
    phone_patterns = [
        r'\b(\d{8})\b',
        r'\b(\d{4}\s*\d{4})\b',
        r'\b(\+65\s*\d{8})\b'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            details['phone'] = match.group(1)
            break
    
    return details

class ActionTestDriveBooking(Action):
    def name(self) -> Text:
        return "action_test_drive_booking"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🚗 **Test Drive Booking** 📅

We'll need:
• Your name
• Your preferred date & time
• Valid driving license
• Contact information

📞 **Phone:** +65 6234 5678
📱 **WhatsApp:** +65 4284 8294

🕐 **Available slots:**
• **Weekdays:** 9AM - 7PM
• **Saturday:** 9AM - 6PM
• **Sunday:** 10AM - 5PM

🏪 **Showroom location:**
**350 Orchard Road, Shaw House**
**#05-02, Singapore 238868**

Please provide your details to proceed with booking."""

        dispatcher.utter_message(text=response)
        return []

class ActionProcessTestDriveBooking(Action):
    def name(self) -> Text:
        return "action_process_test_drive_booking"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "")
        booking_details = extract_booking_details(user_text)
        
        # Check what information is missing
        missing_info = []
        if not booking_details['vehicle']:
            missing_info.append("**Vehicle model**")
        if not booking_details['date']:
            missing_info.append("**Preferred date**")
        if not booking_details['time']:
            missing_info.append("**Preferred time**")
        if not booking_details['name']:
            missing_info.append("**Your name**")
        if not booking_details['phone']:
            missing_info.append("**Phone number**")
        
        if missing_info:
            response = f"""❌ **Missing Information**

I need the following details to complete your booking:
{chr(10).join(f'• {info}' for info in missing_info)}

Please provide all details in one message. For example:
*"I want to test drive Honda Civic on 21 June 10am, my name is John and my phone number is 12345678"*"""
            
            dispatcher.utter_message(text=response)
            return []
        
        # All information provided - show confirmation
        response = f"""✅ **Booking Confirmation**

📋 **Booking Details:**
• **Vehicle:** {booking_details['vehicle']}
• **Date:** {booking_details['date']}
• **Time:** {booking_details['time']}
• **Name:** {booking_details['name']}
• **Phone:** {booking_details['phone']}

🏪 **Location:**
**350 Orchard Road, Shaw House**
**#05-02, Singapore 238868**

✅ **Please confirm if all details are correct**

📞 **Need changes?** Call us at +65 6234 5678
📱 **WhatsApp:** +65 4284 8294

**Reply "CONFIRM" to finalize your booking**"""

        dispatcher.utter_message(text=response)
        return [
            SlotSet("booking_vehicle", booking_details['vehicle']),
            SlotSet("booking_date", booking_details['date']),
            SlotSet("booking_time", booking_details['time']),
            SlotSet("booking_name", booking_details['name']),
            SlotSet("booking_phone", booking_details['phone'])
        ]

class ActionConfirmTestDriveBooking(Action):
    def name(self) -> Text:
        return "action_confirm_test_drive_booking"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get stored booking details
        vehicle = tracker.get_slot("booking_vehicle")
        date = tracker.get_slot("booking_date")
        time = tracker.get_slot("booking_time")
        name = tracker.get_slot("booking_name")
        phone = tracker.get_slot("booking_phone")
        
        if not all([vehicle, date, time, name, phone]):
            response = """❌ **Booking Error**

Sorry, I don't have your complete booking details. Please start over with:
*"I want to test drive [vehicle] on [date] at [time], my name is [name] and my phone number is [phone]"*"""
        else:
            response = f"""🎉 **Booking Confirmed!** ✅

📋 **Your Test Drive Booking:**
• **Vehicle:** {vehicle}
• **Date:** {date}
• **Time:** {time}
• **Name:** {name}
• **Phone:** {phone}

🏪 **Location:**
**350 Orchard Road, Shaw House**
**#05-02, Singapore 238868**

📧 **Confirmation sent to your contact details**

📝 **What to bring:**
• Valid driving license
• Identification (NRIC/Passport)

📞 **Questions?** Call +65 6234 5678
📱 **WhatsApp:** +65 4284 8294

**We look forward to seeing you!** 🚗"""

        dispatcher.utter_message(text=response)
        return [] 