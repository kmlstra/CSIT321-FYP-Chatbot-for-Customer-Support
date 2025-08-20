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


from .auto_logger import AutoLoggedAction
from api.cache.feature_cache_manager import check_live_support_feature_enabled
from api.middleware.intent_validation_middleware import validate_high_confidence

logger = logging.getLogger(__name__)





class ActionLiveSupport(AutoLoggedAction):
    """Live support action with intent validation middleware integration"""
    
    def name(self) -> Text:
        return "action_live_support"

    def _get_current_time_context(self, business_hours=None) -> Dict[str, Any]:
        """Get current time context for business hours awareness"""
        try:
            # Singapore timezone
            sg_tz = pytz.timezone('Asia/Singapore')
            current_time = datetime.now(sg_tz)
            current_hour = current_time.hour
            current_day = current_time.strftime('%A').lower()
            
            # Use client-specific business hours if available
            if business_hours:
                try:
                    if current_day in business_hours:
                        day_hours = business_hours[current_day]
                        # Handle both string format ("9:00 AM - 6:00 PM") and object format
                        if isinstance(day_hours, str):
                            if day_hours.lower() == 'closed':
                                is_business_hours = False
                            else:
                                # Parse string format like "9:00 AM - 6:00 PM"
                                import re
                                time_pattern = r'(\d{1,2}):?(\d{0,2})\s*(AM|PM)'
                                matches = re.findall(time_pattern, day_hours.upper())
                                if len(matches) >= 2:
                                    # Parse opening time
                                    open_hour = int(matches[0][0])
                                    if matches[0][2] == 'PM' and open_hour != 12:
                                        open_hour += 12
                                    elif matches[0][2] == 'AM' and open_hour == 12:
                                        open_hour = 0
                                    
                                    # Parse closing time
                                    close_hour = int(matches[1][0])
                                    if matches[1][2] == 'PM' and close_hour != 12:
                                        close_hour += 12
                                    elif matches[1][2] == 'AM' and close_hour == 12:
                                        close_hour = 0
                                    
                                    is_business_hours = open_hour <= current_hour < close_hour
                                else:
                                    is_business_hours = False
                        elif isinstance(day_hours, dict) and 'open' in day_hours and 'close' in day_hours:
                            open_hour = int(day_hours['open'].split(':')[0])
                            close_hour = int(day_hours['close'].split(':')[0])
                            is_business_hours = open_hour <= current_hour < close_hour
                        else:
                            is_business_hours = False
                    else:
                        is_business_hours = False
                except Exception:
                    # Fall back to default hours
                    if current_day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                        is_business_hours = 9 <= current_hour < 19
                    elif current_day == 'saturday':
                        is_business_hours = 9 <= current_hour < 18
                    elif current_day == 'sunday':
                        is_business_hours = 10 <= current_hour < 17
                    else:
                        is_business_hours = False
            else:
                # Default business hours: Mon-Fri 9AM-7PM, Sat 9AM-6PM, Sun 10AM-5PM
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
        except Exception:
            return {'is_business_hours': True, 'current_hour': 12, 'current_day': 'monday', 'is_weekend': False}

    def _format_business_hours(self, business_hours: Dict[str, Any]) -> str:
        """Format business hours for display"""
        try:
            if not business_hours:
                return "Mon-Fri 9AM-7PM, Sat 9AM-6PM, Sun 10AM-5PM"
            
            days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            day_names = {'monday': 'Mon', 'tuesday': 'Tue', 'wednesday': 'Wed', 'thursday': 'Thu', 
                        'friday': 'Fri', 'saturday': 'Sat', 'sunday': 'Sun'}
            
            formatted_hours = []
            for day in days_order:
                if day in business_hours:
                    day_info = business_hours[day]
                    # Handle both string format and object format
                    if isinstance(day_info, str):
                        formatted_hours.append(f"{day_names[day]}: {day_info}")
                    elif isinstance(day_info, dict) and 'open' in day_info and 'close' in day_info:
                        open_time = day_info['open']
                        close_time = day_info['close']
                        formatted_hours.append(f"{day_names[day]}: {open_time}-{close_time}")
                    else:
                        formatted_hours.append(f"{day_names[day]}: Closed")
                else:
                    formatted_hours.append(f"{day_names[day]}: Closed")
            
            return "\n".join(formatted_hours)
            
        except Exception:
            return "Mon-Fri 9AM-7PM, Sat 9AM-6PM, Sun 10AM-5PM"

    @validate_high_confidence(confidence_threshold=0.7)
    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Get client_id from tracker metadata
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            
            # Fast feature check using cache - early return if disabled
            if client_id:
                if not check_live_support_feature_enabled(client_id):
                    dispatcher.utter_message(
                        text="I'm sorry, but live support is currently not available. Please contact our support team for assistance."
                    )
                    return []
            
            # Get conversation ID from unified session manager
            session_id = tracker.sender_id
            try:
                from api.services.unified_session_manager import unified_session_manager
                conversation_id = unified_session_manager.get_conversation_id(session_id)
                if not conversation_id:
                    # Fallback to session_id if conversation_id not found
                    conversation_id = session_id
            except Exception:
                # Fallback to session_id if service unavailable
                conversation_id = session_id
            
            # Optimized client data retrieval with early return for fresh cache
            client_data = None
            if client_id:
                try:
                    from api.cache.client_cache import get_client_cache, get_fallback_contact_data
                    cache = get_client_cache()
                    
                    # Check if we have fresh cached data first (avoid DB call)
                    if client_id in cache._cache and not cache._is_expired(client_id):
                        client_data = cache._cache[client_id].copy()
                        # Add support-specific fields
                        client_data['average_response_time'] = '2-5 minutes'
                        client_data['support_hours'] = client_data.get('business_hours', {})
                        pass
                    else:
                        # Only fetch from DB if cache miss or expired
                        client_data = cache.get_client_data(client_id)
                        if client_data:
                            # Add support-specific fields
                            client_data['average_response_time'] = '2-5 minutes'
                            client_data['support_hours'] = client_data.get('business_hours', {})
                            pass
                except Exception:
                    pass
            
            # Use fallback data if client data not available
            if not client_data:
                from api.cache.client_cache import get_fallback_contact_data
                client_data = get_fallback_contact_data()
                # Add support-specific fields for fallback data
                client_data['average_response_time'] = '2-5 minutes'
                client_data['support_hours'] = client_data.get('business_hours', {})
                pass
            
            # Get current time context with client business hours
            time_context = self._get_current_time_context(client_data.get('business_hours', {}))
            
            # Create WhatsApp URL with clean conversation ID
            whatsapp_number = client_data.get('whatsapp', client_data.get('phone', ''))
            # Clean conversation ID by removing any HTML tags or session info
            clean_id = conversation_id.split('<')[0].split('&')[0].split('?')[0].strip()
            whatsapp_message = f"I need live support. Conversation ID: {clean_id}"
            whatsapp_url = f"https://wa.me/{whatsapp_number.replace('+', '').replace(' ', '')}?text={whatsapp_message}"
            
            # Format business hours text
            business_hours = client_data.get('business_hours', {})
            hours_text = self._format_business_hours(business_hours)
            
            # Determine status and messaging based on business hours
            if time_context['is_business_hours']:
                status_message = "🟢 **Live Support Available Now**"
                availability_note = "Our team is online and ready to assist you!"
                response_info = f"⚡ **Average Response Time:** {client_data.get('average_response_time', '2-5 minutes')}"
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
{hours_text}

{response_info}

*Your conversation ID will be automatically shared with our support team.*
            """
                
        except Exception:
            pass
            # Fallback message
            session_id = tracker.sender_id
            try:
                from api.services.unified_session_manager import unified_session_manager
                conversation_id = unified_session_manager.get_conversation_id(session_id)
                if not conversation_id:
                    # Fallback to session_id if conversation_id not found
                    conversation_id = session_id
            except Exception:
                # Fallback to session_id if service unavailable
                conversation_id = session_id
            from backend.api.cache.client_cache import get_fallback_contact_data
            fallback_data = get_fallback_contact_data()
            fallback_data['average_response_time'] = '2-5 minutes'
            fallback_data['support_hours'] = 'Mon-Fri 9AM-7PM, Sat 9AM-6PM, Sun 10AM-5PM'
            
            whatsapp_number = fallback_data.get('whatsapp', '')
            # Clean conversation ID by removing any HTML tags or session info
            clean_id = conversation_id.split('<')[0].split('&')[0].split('?')[0].strip()
            fallback_whatsapp_message = f"I need live support. Conversation ID: {clean_id}"
            fallback_whatsapp_url = f"https://wa.me/{whatsapp_number.replace('+', '').replace(' ', '')}?text={fallback_whatsapp_message}"
            message = f"""🔗 **Connect with Live Support**

<button onclick="window.open('{fallback_whatsapp_url}', '_blank')" class="cc-whatsapp-btn" style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px;">💬 Chat on WhatsApp</button>

📋 **Business Hours:**
{fallback_data.get('support_hours', 'Mon-Fri 9AM-7PM, Sat 9AM-6PM, Sun 10AM-5PM')}

⚡ **Average Response Time:** {fallback_data.get('average_response_time', '2-5 minutes')}

*Your conversation ID will be automatically shared with our support team.*
            """
        
        dispatcher.utter_message(text=message)
        return []