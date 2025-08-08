"""Live Support RASA Actions
Handles live support and WhatsApp integration
Now uses direct information.py import instead of API calls
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
from datetime import datetime
import pytz

# Import our new information class - no more API dependencies!
from ..utils.information import support_info
from ..middleware.auto_logger import AutoLoggedAction

logger = logging.getLogger(__name__)

class ActionLiveSupport(AutoLoggedAction):
    def name(self) -> Text:
        return "action_live_support"

    def _get_current_time_context(self) -> Dict[str, Any]:
        """Get current time context for business hours awareness"""
        try:
            # Singapore timezone
            sg_tz = pytz.timezone('Asia/Singapore')
            current_time = datetime.now(sg_tz)
            current_hour = current_time.hour
            current_day = current_time.strftime('%A').lower()
            
            # Business hours: Mon-Fri 9AM-7PM, Sat 9AM-6PM, Sun 10AM-5PM
            if current_day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                is_business_hours = 9 <= current_hour < 19
            elif current_day == 'saturday':
                is_business_hours = 9 <= current_hour < 18
            elif current_day == 'sunday':
                is_business_hours = 10 <= current_hour < 17
            else:
                is_business_hours = False
            
            return {
                'is_business_hours': is_business_hours,
                'current_hour': current_hour,
                'current_day': current_day,
                'is_weekend': current_day in ['saturday', 'sunday']
            }
        except Exception as e:
            logger.error(f"Error getting time context: {e}")
            return {'is_business_hours': True, 'current_hour': 12, 'current_day': 'monday', 'is_weekend': False}

    def execute_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Get conversation ID from tracker
            conversation_id = tracker.sender_id
            
            # Get current time context
            time_context = self._get_current_time_context()
            
            # Create simplified WhatsApp message with only conversation ID
            whatsapp_message = f"Conversation ID: {conversation_id}"
            whatsapp_url = support_info.get_whatsapp_url(whatsapp_message)
            
            # Determine status and messaging based on business hours
            if time_context['is_business_hours']:
                status_message = "🟢 **Live Support Available Now**"
                availability_note = "Our team is online and ready to assist you!"
                response_info = f"⚡ **Average Response Time:** {support_info.average_response_time}"
            else:
                status_message = "🟡 **Live Support - Outside Business Hours**"
                if time_context['is_weekend']:
                    availability_note = "Weekend support available with extended response times."
                else:
                    availability_note = "We'll respond first thing during business hours."
                response_info = f"⚡ **Response Time:** Within 2-4 hours during business hours"
            
            # Create formatted message with operation hours
            message = f"""{status_message}

<button onclick="window.open('{whatsapp_url}', '_blank')" class="cc-whatsapp-btn" style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px;">💬 Connect on WhatsApp</button>

{availability_note}

📋 **Business Hours:**
• **Mon-Fri:** 9:00 AM - 7:00 PM
• **Saturday:** 9:00 AM - 6:00 PM  
• **Sunday:** 10:00 AM - 5:00 PM

{response_info}

*Your conversation ID will be automatically shared with our support team.*
            """
                
        except Exception as e:
            logger.error(f"Error getting support info: {e}")
            # Fallback message with basic info and conversation ID
            conversation_id = tracker.sender_id
            fallback_whatsapp_url = f"https://wa.me/6591234567?text=Conversation%20ID:%20{conversation_id}"
            message = f"""🔗 **Connect with Live Support**

<button onclick="window.open('{fallback_whatsapp_url}', '_blank')" class="cc-whatsapp-btn" style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px;">💬 Chat on WhatsApp</button>

📋 **Business Hours:**
• **Mon-Fri:** 9:00 AM - 7:00 PM
• **Saturday:** 9:00 AM - 6:00 PM  
• **Sunday:** 10:00 AM - 5:00 PM

⚡ **Average Response Time:** 15-30 minutes

*Your conversation ID will be automatically shared with our support team.*
            """
        
        dispatcher.utter_message(text=message)
        return []