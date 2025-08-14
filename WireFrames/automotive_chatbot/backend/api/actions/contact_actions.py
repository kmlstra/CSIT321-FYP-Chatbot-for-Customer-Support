"""Contact and Location-related RASA Actions
Handles contact information, store location, and operating hours for second-hand car dealer
"""

from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from .auto_logger import AutoLoggedAction
from api.utils.cache import contact_cache
from api.cache.client_cache import get_client_cache, get_fallback_contact_data
from api.cache.feature_cache_manager import check_live_support_feature_enabled
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)




class ActionSmartContact(AutoLoggedAction):
    """Intelligent contact action for second-hand car dealer
    
    Features:
    - Context-aware responses based on business hours
    - Intent-specific contact information delivery
    - Modern UI styling for contact information
    - Suitable for car dealership inquiries
    """
    
    def name(self) -> Text:
        return "action_smart_contact"
    
    def _get_current_time_context(self, business_hours: Dict = None) -> Dict[str, Any]:
        """Get current time context for business hours awareness"""
        try:
            # Singapore timezone
            sg_tz = pytz.timezone('Asia/Singapore')
            current_time = datetime.now(sg_tz)
            current_hour = current_time.hour
            current_day = current_time.strftime('%A').lower()
            
            # Default business hours if not provided
            if not business_hours:
                business_hours = {
                    'monday': {'open': '09:00', 'close': '19:00'},
                    'tuesday': {'open': '09:00', 'close': '19:00'},
                    'wednesday': {'open': '09:00', 'close': '19:00'},
                    'thursday': {'open': '09:00', 'close': '19:00'},
                    'friday': {'open': '09:00', 'close': '19:00'},
                    'saturday': {'open': '09:00', 'close': '18:00'},
                    'sunday': {'open': '10:00', 'close': '17:00'}
                }
            
            # Check if current day has business hours
            day_hours = business_hours.get(current_day, {})
            is_business_hours = False
            
            if day_hours and 'open' in day_hours and 'close' in day_hours:
                try:
                    open_time = datetime.strptime(day_hours['open'], '%H:%M').time()
                    close_time = datetime.strptime(day_hours['close'], '%H:%M').time()
                    current_time_only = current_time.time()
                    
                    is_business_hours = open_time <= current_time_only < close_time
                except ValueError:
                    # Fallback to default logic if parsing fails
                    if current_day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                        is_business_hours = 9 <= current_hour < 19
                    elif current_day == 'saturday':
                        is_business_hours = 9 <= current_hour < 18
                    elif current_day == 'sunday':
                        is_business_hours = 10 <= current_hour < 17
                    else:
                        is_business_hours = False
            
            return {
                'current_time': current_time,
                'current_hour': current_hour,
                'current_day': current_day,
                'is_business_hours': is_business_hours,
                'is_weekend': current_day in ['saturday', 'sunday'],
                'time_until_open': None if is_business_hours else self._calculate_time_until_open(current_time, sg_tz)
            }
        except Exception as e:
            logger.error(f"Error getting time context: {e}")
            return {'is_business_hours': True, 'current_day': 'monday'}
    
    def _calculate_time_until_open(self, current_time: datetime, sg_tz: Any) -> str:
        """Calculate time until business opens"""
        try:
            current_day = current_time.strftime('%A').lower()
            current_hour = current_time.hour
            
            if current_day == 'sunday' and current_hour < 10:
                return "Opens at 10:00 AM today"
            elif current_day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'] and current_hour < 9:
                return "Opens at 9:00 AM today"
            elif current_day == 'saturday' and current_hour < 9:
                return "Opens at 9:00 AM today"
            else:
                return "Opens tomorrow at 9:00 AM"
        except Exception:
            return "Opens at 9:00 AM"
    
    def _get_contextual_response_message(self, time_context: Dict[str, Any], intent_analysis: Optional[Dict[str, bool]] = None) -> str:
        """Generate contextual greeting based on time context and intent"""
        # Always provide consistent messaging regardless of specific intent
        if not time_context.get('is_business_hours', True):
            return f"Thank you for contacting us! While our phone lines are currently closed, here's how to reach us. {time_context.get('time_until_open', '')}:"
        else:
            return "Thank you for contacting us! Here's how to reach us:"
    
    def _analyze_contact_intent(self, user_message: str) -> Dict[str, bool]:
        """Enhanced contact intent analysis with better context understanding"""
        message_lower = user_message.lower()
        
        # Enhanced keywords for different contact methods
        email_keywords = ['email', 'mail', 'send', 'write', 'documentation', 'detailed', 'inquiry', 'formal', 'e-mail', 'support email', 'email address', 'send message']
        phone_keywords = ['phone', 'call', 'speak', 'talk', 'voice', 'telephone', 'ring', 'number', 'contact number', 'phone number', 'telephone number', 'calling', 'dial', 'call you', 'speak to someone', 'voice support']
        whatsapp_keywords = ['whatsapp', 'chat', 'message', 'quick', 'fast', 'instant', 'messaging', 'text', 'wa', 'whatsapp chat', 'live chat', 'instant message']
        hours_keywords = ['hours', 'time', 'open', 'available', 'when', 'schedule', 'timing', 'operating', 'business', 'working hours', 'office hours', 'what time', 'are you open', 'closed']
        public_holiday_keywords = ['public holiday', 'holiday', 'holidays', 'public holidays', 'new year', 'christmas', 'chinese new year', 'cny', 'national day', 'deepavali', 'hari raya', 'good friday', 'vesak day', 'labour day']
        location_keywords = ['location', 'address', 'where', 'visit', 'office', 'map', 'directions', 'find', 'showroom', 'branch', 'store', 'come to', 'visit you', 'your office']
        
        # Enhanced urgency and context detection
        urgent_keywords = ['urgent', 'emergency', 'asap', 'immediately', 'now', 'right now', 'quickly']
        general_contact_keywords = ['contact', 'reach', 'get in touch', 'connect', 'support', 'help', 'assistance']
        
        # Intent detection with enhanced logic
        needs_email = any(keyword in message_lower for keyword in email_keywords)
        needs_phone = any(keyword in message_lower for keyword in phone_keywords)
        needs_whatsapp = any(keyword in message_lower for keyword in whatsapp_keywords)
        needs_hours = any(keyword in message_lower for keyword in hours_keywords)
        needs_public_holiday_hours = any(keyword in message_lower for keyword in public_holiday_keywords)
        needs_location = any(keyword in message_lower for keyword in location_keywords)
        
        # If asking about public holidays, treat as hours request
        if needs_public_holiday_hours:
            needs_hours = True
        is_urgent = any(keyword in message_lower for keyword in urgent_keywords)
        
        # Enhanced logic for determining if user wants all contact info
        # Only show all if explicitly asking for general contact AND no specific intent detected
        specific_intent_detected = any([needs_email, needs_phone, needs_whatsapp, needs_hours, needs_location])
        
        needs_all = (
            (any(word in message_lower for word in ['all', 'everything', 'complete']) and 
             any(word in message_lower for word in general_contact_keywords)) or
            (any(word in message_lower for word in general_contact_keywords) and not specific_intent_detected) or
            (not specific_intent_detected and not any(word in message_lower for word in ['contact', 'reach', 'get in touch', 'connect', 'support', 'help', 'assistance']))
        )
        
        # If urgent, prioritize WhatsApp and phone
        if is_urgent and not any([needs_email, needs_hours, needs_location]):
            needs_whatsapp = True
            needs_phone = True
        
        return {
            'needs_email': needs_email,
            'needs_phone': needs_phone,
            'needs_whatsapp': needs_whatsapp,
            'needs_hours': needs_hours,
            'needs_public_holiday_hours': needs_public_holiday_hours,
            'needs_location': needs_location,
            'needs_all': needs_all,
            'is_urgent': is_urgent
        }
    
    def _get_operating_hours_info(self, user_message: str, client_data) -> str:
        """Get specific operating hours information based on user query"""
        message_lower = user_message.lower()
        
        # Check for public holiday specific queries
        public_holiday_keywords = ['public holiday', 'holiday', 'holidays', 'public holidays', 'new year', 'christmas', 'chinese new year', 'cny', 'national day', 'deepavali', 'hari raya', 'good friday', 'vesak day', 'labour day']
        is_public_holiday_query = any(keyword in message_lower for keyword in public_holiday_keywords)
        
        if is_public_holiday_query:
            # Return specific public holiday information with contact details
            whatsapp_number = client_data.get('whatsapp', client_data.get('phone', ''))
            email = client_data.get('email', 'Email not available')
            address = client_data.get('address', 'Address not available')
            return f"""
🎉 **Public Holiday Hours**
We are CLOSED on all Singapore Public Holidays

📅 **Public Holidays We're Closed:**
• 🎊 New Year's Day
• 🧧 Chinese New Year (2 days)
• ✝️ Good Friday
• 👷 Labour Day
• 🙏 Vesak Day
• 🌙 Hari Raya Puasa
• 🇸🇬 National Day
• 🐑 Hari Raya Haji
• 🪔 Deepavali
• 🎄 Christmas Day

💬 **Need urgent assistance during holidays?**
WhatsApp us anytime - we'll respond when we're back!

📞 **Emergency Contact (Holidays)**
💬 **WhatsApp:** {whatsapp_number}
📧 **Email:** {email}
📍 **Address:** {address}
"""
        
        # Check for specific day queries
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        specific_day = None
        for day in days:
            if day in message_lower:
                specific_day = day
                break
        
        # Get business hours from client data
        business_hours = client_data.get('business_hours', {})
        
        if specific_day:
            # Return specific day hours from client data
            if specific_day in business_hours:
                day_hours = business_hours[specific_day]
                if isinstance(day_hours, dict) and 'open' in day_hours and 'close' in day_hours:
                    hours = f"{day_hours['open']} - {day_hours['close']}"
                elif isinstance(day_hours, str):
                    hours = day_hours if day_hours.lower() != 'closed' else "Closed"
                else:
                    hours = "Closed"
            else:
                hours = "Closed"
            
            return f"""
🕒 **{specific_day.title()} Hours**
{hours}
"""
        else:
            # Return general hours with public holiday information
            # Format business hours from client data
            def format_hours(day_key, default_hours):
                if day_key in business_hours:
                    day_hours = business_hours[day_key]
                    if isinstance(day_hours, dict) and 'open' in day_hours and 'close' in day_hours:
                        return f"{day_hours['open']} - {day_hours['close']}"
                    elif isinstance(day_hours, str):
                        return day_hours if day_hours.lower() != 'closed' else "Closed"
                return default_hours
            
            weekday_hours = format_hours('monday', "9:00 AM - 7:00 PM")
            saturday_hours = format_hours('saturday', "9:00 AM - 6:00 PM")
            sunday_hours = format_hours('sunday', "10:00 AM - 5:00 PM")
            
            return f"""
🕒 **Operating Hours**

📅 **Weekdays (Monday - Friday)**
⏰ {weekday_hours}

📅 **Saturday**
⏰ {saturday_hours}

📅 **Sunday**
⏰ {sunday_hours}

🎉 **Public Holidays: CLOSED**

📋 **Singapore Public Holidays We're Closed:**
• 🎊 New Year's Day
• 🧧 Chinese New Year (2 days)
• ✝️ Good Friday
• 👷 Labour Day
• 🙏 Vesak Day
• 🌙 Hari Raya Puasa
• 🇸🇬 National Day
• 🐑 Hari Raya Haji
• 🪔 Deepavali
• 🎄 Christmas Day

💬 **Need urgent help during holidays?**
WhatsApp us anytime - we'll respond when we're back!
"""
    
    def _get_email_info(self, conversation_id: str, client_data) -> str:
        """Get only email information with clickable button"""
        email = client_data.get('email', 'Email not available')
        return f"""
📧 **Email Support**
<a href="mailto:{email}" class="cc-contact-link cc-email-btn">📧 Send Email</a>

⚡ We respond within 24 hours
"""

    def _get_phone_info(self, client_data) -> str:
        """Get only phone information with clickable button"""
        phone = client_data.get('phone', 'Phone not available')
        return f"""
📞 **Phone Support**
<a href="tel:{phone}" class="cc-contact-link cc-phone-btn">📞 Call Now</a>
⚡ Available during business hours
"""

    def _get_whatsapp_info(self, conversation_id: str, client_data) -> str:
        """Get only WhatsApp information with button"""
        whatsapp_number = client_data.get('whatsapp', client_data.get('phone', ''))
        # Clean conversation ID by removing any HTML tags or session info
        clean_id = conversation_id.split('<')[0].split('&')[0].split('?')[0].strip()
        whatsapp_message = f"I need live support. Conversation ID: {clean_id}"
        whatsapp_url = f"https://wa.me/{whatsapp_number.replace('+', '').replace(' ', '')}?text={whatsapp_message}"
        return f"""
💬 **WhatsApp Support**
<button onclick="window.open('{whatsapp_url}', '_blank')" class="cc-whatsapp-btn" style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px;">💬 Chat with Us on WhatsApp</button>
⚡ Quick response during business hours
"""

    def _get_location_info(self, client_data) -> str:
        """Get only location information with embedded map"""
        # Create simple Google Maps embed URL using actual address without API key
        import urllib.parse
        address = client_data.get('address', 'Address not available')
        encoded_address = urllib.parse.quote_plus(address)
        maps_embed_url = f"https://maps.google.com/maps?q={encoded_address}&output=embed"
        google_maps_url = f"https://maps.google.com/maps?q={encoded_address}"
        return f"""
📍 **Our Location**
{address}
🏢 Visit our showroom and service center

<iframe src="{maps_embed_url}" width="300" height="200" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>

<a href="{google_maps_url}" target="_blank" class="cc-maps-btn">📍 View on Google Maps</a>
"""

    def _get_full_contact_card(self, conversation_id: str, client_data, context_message: Optional[str] = None, availability_note: Optional[str] = None) -> str:
        """Get the full contact card with all contact information - FIXED: No duplicate buttons"""
        # Use default messages if not provided
        business_name = client_data.get('business_name', 'Our Business')
        if not context_message:
            context_message = f"Contact {business_name}"
        if not availability_note:
            availability_note = "Choose your preferred way to reach us"
            
        whatsapp_number = client_data.get('whatsapp', client_data.get('phone', ''))
        # Clean conversation ID by removing any HTML tags or session info
        clean_id = conversation_id.split('<')[0].split('&')[0].split('?')[0].strip()
        whatsapp_message = f"I need live support. Conversation ID: {clean_id}"
        whatsapp_url = f"https://wa.me/{whatsapp_number.replace('+', '').replace(' ', '')}?text={whatsapp_message}"
        
        # Create simple Google Maps embed URL using actual address without API key
        import urllib.parse
        address = client_data.get('address', 'Address not available')
        encoded_address = urllib.parse.quote_plus(address)
        maps_embed_url = f"https://maps.google.com/maps?q={encoded_address}&output=embed"
        google_maps_url = f"https://maps.google.com/maps?q={encoded_address}"
        
        # Get operating hours from client data
        business_hours = client_data.get('business_hours', {})
        
        def format_hours(day_key, default_hours):
            if day_key in business_hours:
                day_hours = business_hours[day_key]
                if isinstance(day_hours, dict) and 'open' in day_hours and 'close' in day_hours:
                    return f"{day_hours['open']} - {day_hours['close']}"
                elif isinstance(day_hours, str):
                    return day_hours if day_hours.lower() != 'closed' else "Closed"
            return default_hours
        
        weekday_hours = format_hours('monday', "9:00 AM - 7:00 PM")
        saturday_hours = format_hours('saturday', "9:00 AM - 6:00 PM")
        sunday_hours = format_hours('sunday', "10:00 AM - 5:00 PM")
        
        phone = client_data.get('phone', 'Phone not available')
        email = client_data.get('email', 'Email not available')
        
        return f"""
📞 **{context_message}**
{availability_note}

💬 **WhatsApp Support**
<button onclick="window.open('{whatsapp_url}', '_blank')" class="cc-whatsapp-btn" style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px;">💬 Chat with Us on WhatsApp</button>
⚡ Quick response during business hours

📞 **Phone Support**
<a href="tel:{phone}" class="cc-contact-link cc-phone-btn">📞 Call Now</a>
⚡ Available during business hours

📧 **Email Support**
<a href="mailto:{email}" class="cc-contact-link cc-email-btn">📧 Send Email</a>
⚡ We respond within 24 hours

📍 **Our Location**
{address}
🏢 Visit our showroom and service center

<iframe src="{maps_embed_url}" width="300" height="200" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>

<a href="{google_maps_url}" target="_blank" class="cc-maps-btn">📍 View on Google Maps</a>

🕒 **Operating Hours**
📅 **Weekdays (Mon-Fri):** {weekday_hours}
📅 **Saturday:** {saturday_hours}
📅 **Sunday:** {sunday_hours}
🎉 **Public Holidays:** CLOSED
"""
    
    def _get_urgent_contact_response(self, conversation_id: str, time_context: Dict[str, Any], client_data) -> str:
        """Get urgent contact response with WhatsApp and phone prioritized - FIXED: No duplicate buttons"""
        whatsapp_number = client_data.get('whatsapp', client_data.get('phone', ''))
        # Clean conversation ID by removing any HTML tags or session info
        clean_id = conversation_id.split('<')[0].split('&')[0].split('?')[0].strip()
        whatsapp_message = f"I need live support. Conversation ID: {clean_id}"
        whatsapp_url = f"https://wa.me/{whatsapp_number.replace('+', '').replace(' ', '')}?text={whatsapp_message}"
        phone = client_data.get('phone', 'Phone not available')
        return f"""
🚨 **Urgent Support**
Get immediate assistance

💬 **WhatsApp (Fastest)**
Usually responds within 5 minutes
<button onclick="window.open('{whatsapp_url}', '_blank')" class="cc-whatsapp-btn" style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px;">💬 Chat with Us on WhatsApp</button>

📞 **Direct Phone**
<a href="tel:{phone}" class="cc-contact-link cc-phone-btn">📞 Call Now</a>

⚡ WhatsApp is fastest • 📞 Phone: Mon-Fri 9AM-7PM
"""

    def _get_contextual_contact_response(self, user_message: str, conversation_id: str, time_context: Dict[str, Any], client_data) -> str:
        """Get contextual contact response based on current time and context"""
        # Determine context based on time - focus on general availability
        if not time_context.get('is_business_hours', True):
            context_message = "24/7 Support Available"
            availability_note = f"Email always available • Phone opens at 9:00 AM"
        elif time_context.get('is_weekend', False):
            context_message = "Weekend support available"
            availability_note = "Email & WhatsApp preferred • Limited phone hours"
        else:
            context_message = "We're online and ready to help"
            availability_note = "All support channels active"
            
        # Use the consolidated full contact card with context
        return self._get_full_contact_card(conversation_id, client_data, context_message, availability_note)

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Check if contact support feature is enabled for this client
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            if not check_live_support_feature_enabled(client_id):
                dispatcher.utter_message(text="I'm sorry, but contact support is not available at the moment. Please try again later or check our website for alternative ways to reach us.")
                return []
            
            # Get the user's message and conversation ID
            user_message = tracker.latest_message.get('text', '')
            conversation_id = tracker.sender_id
            
            # Check cache first for contact data
            cache_key = f"contact_data_{client_id}" if client_id else "contact_data_fallback"
            client_data = contact_cache.get(cache_key)
            
            if client_data:
                logger.info(f"Retrieved contact data from cache for client_id: {client_id}")
            else:
                # Get client-specific data from cache (with automatic MongoDB fallback)
                if client_id:
                    cache = get_client_cache()
                    client_data = cache.get_client_data(client_id)
                    if client_data:
                        logger.info(f"Retrieved client data from cache for client_id: {client_id}")
                        # Cache the contact data for faster future access
                        contact_cache.set(cache_key, client_data, ttl=3600)  # 1 hour cache
            
                # Use fallback data if client data not available
                if not client_data:
                    client_data = get_fallback_contact_data()
                    logger.info(f"Using fallback contact data for client_id: {client_id}")
                    # Cache fallback data too
                    contact_cache.set(cache_key, client_data, ttl=3600)  # 1 hour cache
            
            logger.info(f"Smart contact action triggered with message: {user_message}, client_id: {client_id}")
            
            # Get time context with client business hours
            time_context = self._get_current_time_context(client_data.get('business_hours', {}))
            
            # Analyze what the user is looking for
            intent_analysis = self._analyze_contact_intent(user_message)
            
            # Handle urgent requests with priority contact methods
            if intent_analysis.get('is_urgent', False):
                if intent_analysis['needs_phone'] or intent_analysis['needs_whatsapp']:
                    urgent_response = self._get_urgent_contact_response(conversation_id, time_context, client_data)
                    dispatcher.utter_message(text=urgent_response)
                    logger.info(f"Urgent contact response sent successfully")
                    return []
            
            # Get contextual greeting with intent awareness
            greeting = self._get_contextual_response_message(time_context, intent_analysis)
            
            # Build response parts based on intent analysis
            response_parts = []
            
            # Count how many specific intents are detected
            specific_intents = sum([
                intent_analysis['needs_hours'],
                intent_analysis['needs_email'], 
                intent_analysis['needs_phone'],
                intent_analysis['needs_whatsapp'],
                intent_analysis['needs_location']
            ])
            
            # Check if this is a general contact request (like clicking contact button)
            general_contact_keywords = ['contact', 'reach', 'get in touch', 'connect', 'support', 'help', 'assistance']
            is_general_contact = any(keyword in user_message.lower() for keyword in general_contact_keywords)
            
            # If only one specific intent is detected AND it's not a general contact request, show only that information
            if specific_intents == 1 and not is_general_contact:
                if intent_analysis['needs_hours']:
                    # Only show operating hours
                    hours_info = self._get_operating_hours_info(user_message, client_data)
                    response_parts.append(hours_info)
                elif intent_analysis['needs_email']:
                    # Only show email info
                    email_info = self._get_email_info(conversation_id, client_data)
                    response_parts.append(email_info)
                elif intent_analysis['needs_phone']:
                    # Only show phone info
                    phone_info = self._get_phone_info(client_data)
                    response_parts.append(phone_info)
                elif intent_analysis['needs_whatsapp']:
                    # Only show WhatsApp info
                    whatsapp_info = self._get_whatsapp_info(conversation_id, client_data)
                    response_parts.append(whatsapp_info)
                elif intent_analysis['needs_location']:
                    # Only show location info
                    location_info = self._get_location_info(client_data)
                    response_parts.append(location_info)
            else:
                # Show greeting for multiple intents or general requests
                response_parts.append(greeting)
                
                # If multiple specific intents or general contact request, show appropriate response
                if specific_intents > 1:
                    # Multiple specific requests - show full contact card
                    contact_card = self._get_full_contact_card(conversation_id, client_data)
                    response_parts.append(contact_card)
                elif intent_analysis['needs_all'] or specific_intents == 0 or is_general_contact:
                    # General contact request - show contextual response with all contact options
                    contact_card = self._get_contextual_contact_response(user_message, conversation_id, time_context, client_data)
                    response_parts.append(contact_card)
            
            final_response = "\n\n".join(response_parts)
            dispatcher.utter_message(text=final_response)
            
            logger.info(f"Smart contact response sent successfully")
            
        except Exception as e:
            logger.error(f"Error in ActionSmartContact: {e}")
            # Fallback response
            conversation_id = tracker.sender_id
            # Get client_id for fallback as well
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            fallback_data = get_fallback_contact_data()
            
            whatsapp_number = fallback_data.get('whatsapp', fallback_data.get('phone', ''))
            whatsapp_message = f"Conversation ID: {conversation_id}"
            whatsapp_url = f"https://wa.me/{whatsapp_number.replace('+', '').replace(' ', '')}?text={whatsapp_message}"
            fallback_response = f"""🤝 **{fallback_data.get('business_name', 'Our Business')} Support**

📞 **Phone:** {fallback_data.get('phone', 'Phone not available')}
<a href="tel:{fallback_data.get('phone', '')}" class="cc-contact-link cc-phone-btn">📞 Call Now</a>

📧 **Email:** {fallback_data.get('email', 'Email not available')}
<a href="mailto:{fallback_data.get('email', '')}" class="cc-contact-link cc-email-btn">📧 Send Email</a>

💬 **WhatsApp:** {whatsapp_number}
<button onclick="window.open('{whatsapp_url}', '_blank')" class="cc-whatsapp-btn" style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px;">💬 Chat Now</button>

📍 **Address:** {fallback_data.get('address', 'Address not available')}
🕒 **Hours:** Mon-Fri 9AM-7PM, Sat 9AM-6PM, Sun 10AM-5PM"""
            dispatcher.utter_message(text=fallback_response)
        
        return []