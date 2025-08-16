"""Appointment Booking RASA Actions
Handles appointment booking, viewing, and management for automotive services
"""

from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from .auto_logger import AutoLoggedAction
from api.config.database import DatabaseContext
from api.services.email_service import send_appointment_confirmation_email, send_appointment_cancellation_email, is_email_enabled
from api.utils.cache import appointment_cache, client_cache
from api.cache.feature_cache_manager import check_appointment_feature_enabled
import logging
from datetime import datetime, timedelta, time
import pytz
from bson import ObjectId
import re
from dateutil import parser
from dateutil.relativedelta import relativedelta
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# MongoDB configuration
MONGODB_URL = os.getenv('MONGODB_URL')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'automotive_chatbot_saas')

# Configure detailed logging for appointment actions
logger = logging.getLogger('api.actions.appointment_actions')
logger.setLevel(logging.DEBUG)

# Create console handler with detailed formatting
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.propagate = False

# MongoDB connection helper
async def get_mongodb_client():
    """Get MongoDB client connection"""
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        # Test connection
        await client.admin.command('ping')
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None

async def get_client_data_from_db(client_id: str):
    """Retrieve client data directly from MongoDB"""
    try:
        db = await get_mongodb_client()
        if not db:
            return None
            
        # Get client data - try both string ID and ObjectId
        client = await db.clients.find_one({"_id": client_id})
        if not client:
            # Try with ObjectId if string search fails
            try:
                client = await db.clients.find_one({"_id": ObjectId(client_id)})
            except Exception:
                pass
        
        if not client:
            return None
            
        return client
        
    except Exception as e:
        logger.error(f"Error retrieving client data from MongoDB: {e}")
        return None

def get_appointment_types():
    """Get available appointment types with caching"""
    cache_key = "appointment_types"
    cached_types = appointment_cache.get(cache_key)
    
    if cached_types is not None:
        return cached_types
    
    # Generate appointment types with icons and descriptions
    types = [
        {
            "id": "test_drive", 
            "name": "Test Drive", 
            "duration": 60,
            "icon": "🚗",
            "description": "Experience our vehicles firsthand with a personalized test drive"
        },
        {
            "id": "sales_consultation", 
            "name": "Sales Consultation", 
            "duration": 45,
            "icon": "💼",
            "description": "Get expert advice on vehicle selection and pricing options"
        },
        {
            "id": "trade_in_evaluation", 
            "name": "Trade-in Evaluation", 
            "duration": 30,
            "icon": "🔄",
            "description": "Professional assessment of your current vehicle's trade-in value"
        }
    ]
    
    # Cache for 5 minutes
    appointment_cache.set(cache_key, types, ttl=300)
    return types

def get_appointment_type_by_id(type_id: str):
    """Get appointment type by ID"""
    types = get_appointment_types()
    for apt_type in types:
        if apt_type["id"] == type_id:
            return apt_type
    return None

def get_appointment_options_message():
    """Generate formatted appointment options message"""
    types = get_appointment_types()
    message = "🚗 Select Your Appointment Type - Choose from our available services: "
    
    for apt_type in types:
        # Add icon and description if available, otherwise use basic format
        icon = apt_type.get('icon', '🔧')
        description = apt_type.get('description', f"Duration: {apt_type['duration']} minutes")
        message += f"{icon} {apt_type['name']} - {description}, "
    
    message = message.rstrip(', ') + ". Simply type the service you need (e.g., 'test drive', 'sales consultation', 'trade-in evaluation')."
    return message

def get_appointment_options_with_buttons():
    """Generate appointment options with clickable buttons and explanatory text"""
    types = get_appointment_types()
    
    # Generate buttons for each appointment type
    buttons = []
    for apt_type in types:
        icon = apt_type.get('icon', '🔧')
        buttons.append({
            "title": f"{icon} {apt_type['name']}",
            "payload": apt_type['name'].lower()
        })
    
    return {
        "text": "🚗 Welcome to our appointment booking system! 📋 Please select the type of service you'd like to book:",
        "buttons": buttons
    }


class ActionValidateIntent(AutoLoggedAction):
    """Validate intent based on conversation context
    
    Features:
    - Prevents wrong actions from being triggered
    - Provides context-aware validation
    - Redirects to appropriate actions based on context
    - Handles low confidence predictions
    - Detects misclassified intents
    """
    
    def name(self) -> Text:
        return "action_validate_intent"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Store tracker for use in helper methods
            self.tracker = tracker
            
            # Extract session and client information for logging
            session_id = tracker.sender_id
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            
            # Get current intent and conversation context
            current_intent = tracker.latest_message.get('intent', {}).get('name')
            user_message = tracker.latest_message.get('text', '').lower()
            appointment_active = tracker.get_slot("appointment_active")
            confidence = tracker.latest_message.get('intent', {}).get('confidence', 0)
            
            logger.debug(f"ActionValidateIntent START - Session: {session_id}, Client: {client_id}")
            logger.debug(f"Intent: {current_intent}, Confidence: {confidence:.3f}, Text: '{user_message}'")
            logger.debug(f"Appointment Active: {appointment_active}")
            
            # Check if user is in middle of booking process
            if appointment_active:
                logger.debug(f"User in booking process, checking intent compatibility")
                # If user is booking and says something unrelated, guide them back
                if current_intent not in ['book_appointment', 'provide_info', 'affirm', 'deny']:
                    logger.debug(f"Unrelated intent {current_intent} during booking, resetting appointment_active")
                    dispatcher.utter_message(
                        text="I notice you're in the middle of booking an appointment. Would you like to continue with the booking or start something else? Just let me know!"
                    )
                    return [SlotSet("appointment_active", None)]
            
            # Check for low confidence predictions
            if confidence < 0.7:
                logger.debug(f"Low confidence ({confidence:.3f}) for intent {current_intent}, handling unclear intent")
                return self._handle_unclear_intent(dispatcher, user_message)
            
            # Validate appointment-related intents have required context
            validation_result = self._validate_intent_context(current_intent, user_message, tracker)
            if validation_result:
                logger.debug(f"Intent validation failed for {current_intent}: {validation_result}")
                dispatcher.utter_message(text=validation_result)
                return []
            
            # Check for potential misclassified intents
            misclassification_result = self._check_misclassification(current_intent, user_message, dispatcher)
            if misclassification_result:
                logger.debug(f"Misclassification detected for intent {current_intent}")
                return misclassification_result
            
            # Intent is valid for current context
            logger.debug(f"Intent {current_intent} validated successfully")
            return []
            
        except Exception as e:
            logger.error(f"Error in ActionValidateIntent: {e}", exc_info=True)
            return []
    

    
    def _validate_intent_context(self, intent: str, message: str, tracker: Tracker) -> Optional[str]:
        """Validate if the intent makes sense in the current context"""
        if intent == 'view_appointments':
            customer_phone = tracker.get_slot("customer_phone")
            if not customer_phone:
                return ("To view your appointments, I'll need your phone number first. "
                       "Please provide your phone number.")
        
        elif intent == 'cancel_appointment':
            appointment_id = tracker.get_slot("appointment_id")
            customer_phone = tracker.get_slot("customer_phone")
            if not appointment_id and not customer_phone:
                return ("To cancel an appointment, I'll need either your appointment ID "
                       "or phone number. Please provide one of these.")
        
        return None
    
    def _check_misclassification(self, intent: str, message: str, dispatcher: CollectingDispatcher) -> List[Dict[Text, Any]]:
        """Check for potential misclassified intents and provide corrections"""
        appointment_keywords = ['appointment', 'booking', 'schedule', 'book', 'cancel', 'reschedule', 'time', 'slot']
        loan_keywords = ['loan', 'calculate', 'financing', 'payment', 'interest', 'borrow']
        phone_keywords = ['phone', 'number', 'contact', 'call', 'mobile']
        time_keywords = ['6pm', '6 pm', 'evening', 'after work', 'late', 'time']
        
        # Check if loan intent but talking about appointments
        if intent == 'calculate_loan':
            if any(keyword in message for keyword in appointment_keywords):
                dispatcher.utter_message(
                    text="It seems like you're asking about appointments, not loan calculations. "
                         "Would you like to book, view, or cancel an appointment?"
                )
                return []
            
            if any(keyword in message for keyword in phone_keywords) and not any(keyword in message for keyword in loan_keywords):
                dispatcher.utter_message(
                    text="It looks like you're providing contact information. "
                         "Are you trying to book an appointment or provide details for a service?"
                )
                return []
        
        # Check if appointment intent but talking about loans
        elif intent in ['book_appointment', 'view_appointments', 'cancel_appointment']:
            if any(keyword in message for keyword in loan_keywords) and not any(keyword in message for keyword in appointment_keywords):
                dispatcher.utter_message(
                    text="It seems like you're asking about loan calculations, not appointments. "
                         "Would you like me to help calculate your car loan?"
                )
                return []
        
        # Check for time-related confusion
        if any(keyword in message for keyword in time_keywords) and intent == 'calculate_loan':
            dispatcher.utter_message(
                text="It looks like you're mentioning a time. Are you trying to schedule an appointment? "
                     "I can help you book an appointment for a test drive or consultation."
            )
            return []
        
        return []
    
    def _handle_unclear_intent(self, dispatcher: CollectingDispatcher, message: str) -> List[Dict[Text, Any]]:
        """Handle unclear or low-confidence intents"""
        # Try to determine what the user might want based on keywords
        if any(word in message for word in ['appointment', 'book', 'schedule']):
            # Check if appointment booking is enabled for this client
            client_id = self.tracker.latest_message.get('metadata', {}).get('client_id')
            appointment_available = check_appointment_feature_enabled(client_id) if client_id else True
            if appointment_available:
                dispatcher.utter_message(
                    text="It sounds like you want to book an appointment. "
                         "I can help you schedule a test drive, sales consultation, or trade-in evaluation. "
                         "What type of appointment would you like?"
                )
            else:
                dispatcher.utter_message(
                    text="I understand you're interested in scheduling an appointment, but this feature is not available at the moment. "
                         "Please contact us directly for assistance with scheduling."
                )
        elif any(word in message for word in ['loan', 'calculate', 'financing']):
            dispatcher.utter_message(
                text="It sounds like you want to calculate a car loan. "
                     "I can help you calculate monthly payments. "
                     "Please provide: car price, down payment, loan years, and interest rate."
            )
        elif any(word in message for word in ['view', 'check', 'see']) and any(word in message for word in ['appointment']):
            dispatcher.utter_message(
                text="It sounds like you want to view your appointments. "
                     "I'll need your phone number to look up your bookings."
            )
        else:
            dispatcher.utter_message(
                text="I'm not sure what you're looking for. I can help you with:\n"
                     "• Book appointments (test drives, consultations)\n"
                     "• View or cancel existing appointments\n"
                     "• Calculate car loan payments\n"
                     "• Get COE information\n\n"
                     "What would you like to do?"
            )
        
        return []


class ActionAppointmentCalculator(AutoLoggedAction):
    """Enhanced appointment booking system following loan calculator format"""
    
    def name(self) -> Text:
        return "action_appointment_calculator"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Check if appointment booking feature is enabled for this client
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            if client_id:
                if not check_appointment_feature_enabled(client_id):
                    dispatcher.utter_message(
                        text="I'm sorry, but appointment booking is currently not available. Please contact our support team for assistance."
                    )
                    return []
            
            user_message = tracker.latest_message.get('text', '').strip().lower()
            
            # Check if this is a welcome/help request
            if self._is_welcome_request(user_message):
                self._show_appointment_help(dispatcher, client_id)
                return []
            
            # Try to extract appointment parameters
            appointment_params = self._extract_appointment_parameters(user_message)
            
            if appointment_params:
                # All parameters found, proceed with booking
                return self._process_appointment_booking(dispatcher, appointment_params, client_id)
            else:
                # Show input format requirements
                self._show_input_format(dispatcher, client_id)
                return []
                
        except Exception as e:
            logger.error(f"[APPOINTMENT_CALCULATOR] Error: {e}", exc_info=True)
            dispatcher.utter_message(text="❌ Sorry, there was an error processing your request. Please try again.")
            return []
    
    def _is_welcome_request(self, text: str) -> bool:
        """Check if this is a general appointment booking request without specific parameters"""
        welcome_phrases = [
            'book appointment',
            'schedule appointment',
            'appointment booking',
            'i want to book',
            'make appointment',
            'schedule service'
        ]
        # Check if it's a general request without specific details
        is_general_request = any(phrase in text for phrase in welcome_phrases)
        has_specific_details = any(keyword in text for keyword in ['test drive', 'sales', 'trade', 'tomorrow', 'today', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']) or bool(re.search(r'\d{1,2}\s*(am|pm)', text))
        return is_general_request and not has_specific_details
    
    def _show_appointment_help(self, dispatcher: CollectingDispatcher, client_id: str) -> None:
        """Show appointment booking help information with operating hours and services"""
        # Get client data for business hours and services
        client_data = get_client_data(client_id) if client_id else {}
        
        # Format business hours
        business_hours_text = self._format_business_hours(client_data.get('business_hours', {}))
        
        # Get available services
        services_text = self._format_available_services()
        
        response = f"""📅 **Appointment Booking System**

I can help you schedule your service appointment!

🕒 **Our Operating Hours:**
{business_hours_text}

🔧 **Available Services:**
{services_text}

📝 **How to book:**
Provide these 5 details in any order:
• Service type (Test Drive, Sales Consultation, Trade-in Evaluation)
• Your name
• Phone number
• Date (today, tomorrow, Monday, etc.)
• Time (2pm, 10:30am, etc.)

💡 **Example:**
"Book test drive for John Smith, 91234567, tomorrow 2pm"

🔢 **Simple format:**
"Test Drive, John Smith, 91234567, tomorrow, 2pm"

Try it now! 🚗📞"""
        
        dispatcher.utter_message(text=response)
    
    def _format_business_hours(self, business_hours: Dict[str, Any]) -> str:
        """Format business hours for display"""
        if not business_hours:
            return "Mon-Fri: 9:00 AM - 6:00 PM\nSat: 9:00 AM - 5:00 PM\nSun: Closed"
        
        days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_names = {'monday': 'Mon', 'tuesday': 'Tue', 'wednesday': 'Wed', 'thursday': 'Thu', 
                    'friday': 'Fri', 'saturday': 'Sat', 'sunday': 'Sun'}
        
        formatted_hours = []
        for day in days_order:
            if day in business_hours:
                hours = business_hours[day]
                if isinstance(hours, str):
                    formatted_hours.append(f"{day_names[day]}: {hours}")
                else:
                    formatted_hours.append(f"{day_names[day]}: 9:00 AM - 6:00 PM")
            else:
                formatted_hours.append(f"{day_names[day]}: 9:00 AM - 6:00 PM")
        
        return "\n".join(formatted_hours)
    
    def _format_available_services(self) -> str:
        """Format available services for display"""
        appointment_types = get_appointment_types()
        services = []
        
        for service in appointment_types:
            name = service['name']
            duration = service['duration']
            description = service.get('description', '')
            services.append(f"• **{name}** ({duration} min) - {description}")
        
        return "\n".join(services)
    
    def _extract_appointment_parameters(self, text: str) -> Optional[Dict[str, str]]:
        """Extract appointment parameters from user input"""
        # Try simple comma-separated format first
        parts = [part.strip() for part in text.split(',')]
        
        if len(parts) >= 5:
            try:
                return {
                    'service_type': parts[0].title(),
                    'customer_name': parts[1].title(),
                    'customer_phone': self._clean_phone_number(parts[2]),
                    'appointment_date': parts[3].lower(),
                    'appointment_time': parts[4].lower()
                }
            except (ValueError, IndexError):
                pass
        
        # Try extracting from natural language
        service_type = self._extract_service_type(text)
        customer_name = self._extract_customer_name(text)
        customer_phone = self._extract_phone_number(text)
        appointment_date = self._extract_date(text)
        appointment_time = self._extract_time(text)
        
        # Only return if all parameters are found
        if all(param is not None for param in [service_type, customer_name, customer_phone, appointment_date, appointment_time]):
            return {
                'service_type': service_type,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'appointment_date': appointment_date,
                'appointment_time': appointment_time
            }
        
        return None
    
    def _extract_service_type(self, text: str) -> Optional[str]:
        """Extract service type from text"""
        text_lower = text.lower()
        if 'test drive' in text_lower:
            return 'Test Drive'
        elif 'sales' in text_lower or 'consultation' in text_lower:
            return 'Sales Consultation'
        elif 'trade' in text_lower or 'evaluation' in text_lower:
            return 'Trade-in Evaluation'
        return None
    
    def _extract_customer_name(self, text: str) -> Optional[str]:
        """Extract customer name from text"""
        # Look for name patterns
        name_patterns = [
            r'for\s+([A-Za-z]+\s+[A-Za-z]+)',
            r'name\s+([A-Za-z]+\s+[A-Za-z]+)',
            r'([A-Za-z]+\s+[A-Za-z]+)\s*,\s*\d{8}',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                # Validate it's not a service type or common word
                if name.lower() not in ['test drive', 'sales consultation', 'trade evaluation']:
                    return name
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        text_lower = text.lower()
        date_keywords = ['today', 'tomorrow', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for keyword in date_keywords:
            if keyword in text_lower:
                return keyword
        
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from text"""
        time_patterns = [
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\.(\d{2})\s*(am|pm)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                if len(match.groups()) == 2:  # Simple format like "2pm"
                    return f"{match.group(1)}{match.group(2)}"
                else:  # Format with minutes like "2:30pm"
                    return f"{match.group(1)}:{match.group(2)}{match.group(3)}"
        
        return None
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and validate phone number"""
        # Remove all non-digits
        cleaned = re.sub(r'\D', '', phone)
        
        # Handle Singapore format
        if len(cleaned) == 10 and cleaned.startswith('65'):
            cleaned = cleaned[2:]  # Remove country code
        
        return cleaned
    
    def _process_appointment_booking(self, dispatcher: CollectingDispatcher, params: Dict[str, str], client_id: str) -> List[Dict[Text, Any]]:
        """Process the appointment booking with confirmation"""
        try:
            # Validate parameters
            validation_result = self._validate_appointment_parameters(params)
            if not validation_result['valid']:
                dispatcher.utter_message(text=f"❌ {validation_result['error']}")
                self._show_input_format(dispatcher, client_id)
                return []
            
            # Create appointment datetime
            appointment_datetime = self._create_appointment_datetime(params['appointment_date'], params['appointment_time'])
            
            # Create appointment data
            appointment_data = {
                'service_type': params['service_type'],
                'customer_name': params['customer_name'],
                'customer_phone': params['customer_phone'],
                'appointment_date': params['appointment_date'],
                'appointment_time': params['appointment_time'],
                'appointment_datetime': appointment_datetime,
                'customer_email': '',
                'status': 'confirmed',
                'client_id': client_id,
                'appointment_id': str(ObjectId()),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Save appointment
            if self._save_appointment(appointment_data):
                self._display_booking_confirmation(dispatcher, params, appointment_datetime)
            else:
                dispatcher.utter_message(text="❌ Sorry, there was an error booking your appointment. Please try again.")
            
            return []
            
        except Exception as e:
            logger.error(f"[APPOINTMENT_CALCULATOR] Error processing booking: {e}", exc_info=True)
            dispatcher.utter_message(text="❌ Sorry, there was an error processing your booking. Please try again.")
            return []
    
    def _validate_appointment_parameters(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Validate appointment parameters"""
        # Validate service type
        valid_services = ['Test Drive', 'Sales Consultation', 'Trade-in Evaluation']
        if params['service_type'] not in valid_services:
            return {'valid': False, 'error': f"Invalid service type. Available services: {', '.join(valid_services)}"}
        
        # Validate phone number
        phone = params['customer_phone']
        if not phone or len(phone) != 8 or not phone.isdigit() or phone[0] not in '689':
            return {'valid': False, 'error': "Invalid phone number. Please provide a valid 8-digit Singapore number starting with 6, 8, or 9."}
        
        # Validate name
        name = params['customer_name']
        if not name or len(name.split()) < 2:
            return {'valid': False, 'error': "Please provide your full name (first and last name)."}
        
        return {'valid': True}
    
    def _display_booking_confirmation(self, dispatcher: CollectingDispatcher, params: Dict[str, str], appointment_datetime: datetime) -> None:
        """Display appointment booking confirmation"""
        formatted_date = appointment_datetime.strftime('%B %d, %Y')
        formatted_time = appointment_datetime.strftime('%I:%M %p')
        
        response = f"""✅ **Appointment Booking Confirmed!**

📅 **Appointment Details:**
• Service: {params['service_type']}
• Customer: {params['customer_name']}
• Phone: {params['customer_phone']}
• Date: {formatted_date}
• Time: {formatted_time}

📧 **Confirmation sent to your contact details!**
⏰ **We'll send you a reminder 24 hours before your appointment.**

💬 **Need to reschedule or cancel?**
Just send us a message with your phone number!

🚗 **Thank you for choosing our services!**"""
        
        dispatcher.utter_message(text=response)
    
    def _show_input_format(self, dispatcher: CollectingDispatcher, client_id: str) -> None:
        """Show input format when parameters cannot be extracted"""
        # Get available services for display
        services_text = self._format_available_services()
        
        response = f"""❌ **I couldn't understand your appointment details**

Please provide all 5 details:

🔧 **Available Services:**
{services_text}

🔢 **Simple format:**
"Service, Full Name, Phone, Date, Time"

💡 **Examples:**
• "Test Drive, John Smith, 91234567, tomorrow, 2pm"
• "Sales Consultation, Mary Tan, 98765432, Monday, 10:30am"

💬 **Natural format:**
"Book test drive for John Smith, phone 91234567, tomorrow at 2pm"

📝 **Required details:**
• Service type (Test Drive, Sales Consultation, Trade-in Evaluation)
• Full name (first and last)
• 8-digit phone number (starting with 6, 8, or 9)
• Date (today, tomorrow, or day of week)
• Time (with am/pm)

Try again with all 5 details! 🚗📞"""
        
        dispatcher.utter_message(text=response)


class ActionBookAppointment(AutoLoggedAction):
    """Simplified appointment booking - just collect basic info and save to database"""
    
    def name(self) -> Text:
        return "action_book_appointment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get basic info from user message
            user_message = tracker.latest_message.get('text', '').strip()
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            
            # Get current slots
            service_type = tracker.get_slot("service_type")
            customer_name = tracker.get_slot("customer_name")
            customer_phone = tracker.get_slot("customer_phone")
            customer_email = tracker.get_slot("customer_email")
            appointment_date = tracker.get_slot("appointment_date")
            appointment_time = tracker.get_slot("appointment_time")
            
            # Enhanced service type detection - check both slots and current message
            if not service_type:
                # Check if service_type entity was extracted from current message
                entities = tracker.latest_message.get('entities', [])
                for entity in entities:
                    if entity.get('entity') == 'service_type':
                        service_type = entity.get('value', '').title()
                        break
                
                # Fallback to text-based detection if no entity found
                if not service_type:
                    user_message_lower = user_message.lower()
                    if 'test drive' in user_message_lower:
                        service_type = 'Test Drive'
                    elif 'sales' in user_message_lower or 'consultation' in user_message_lower:
                        service_type = 'Sales Consultation'
                    elif 'trade' in user_message_lower or 'evaluation' in user_message_lower:
                        service_type = 'Trade-in Evaluation'
            
            # Log current slot values for debugging
            logger.debug(f"[APPOINTMENT_BOOKING] Current slots - service_type: {service_type}, customer_name: {customer_name}, customer_phone: {customer_phone}")
            logger.debug(f"[APPOINTMENT_BOOKING] User message: {user_message}")
            
            # Simple phone extraction
            if not customer_phone:
                phone_match = re.search(r'\b([689]\d{7})\b', user_message)
                if phone_match:
                    customer_phone = phone_match.group(1)
            
            # Simple name extraction
            if not customer_name:
                words = user_message.split()
                for word in words:
                    if word.isalpha() and len(word) > 2 and word.lower() not in ['test', 'drive', 'sales', 'consultation', 'trade', 'appointment', 'book', 'schedule']:
                        customer_name = word.title()
                        break
            
            # Enhanced date/time extraction - handle combined inputs like 'monday 1pm'
            if not appointment_date or not appointment_time:
                # Extract both date and time from combined inputs
                extracted_date, extracted_time = self._extract_date_time_from_message(user_message)
                
                if not appointment_date and extracted_date:
                    appointment_date = extracted_date
                    
                if not appointment_time and extracted_time:
                    appointment_time = extracted_time
            
            # Check if we have minimum required info
            # Only ask for service type if it's truly not set and user hasn't provided other details
            if not service_type and not (customer_name or customer_phone):
                dispatcher.utter_message(
                    text="What service would you like to book?",
                    buttons=[
                        {"title": "Test Drive", "payload": "test drive"},
                        {"title": "Sales Consultation", "payload": "sales consultation"},
                        {"title": "Trade-in Evaluation", "payload": "trade-in evaluation"}
                    ]
                )
                return [SlotSet("appointment_active", True)]
            
            # If service_type is missing but user provided details, ask specifically for service type
            if not service_type and (customer_name or customer_phone):
                dispatcher.utter_message(
                    text="I have your details! What service would you like to book?",
                    buttons=[
                        {"title": "Test Drive", "payload": "test drive"},
                        {"title": "Sales Consultation", "payload": "sales consultation"},
                        {"title": "Trade-in Evaluation", "payload": "trade-in evaluation"}
                    ]
                )
                return [
                    SlotSet("customer_name", customer_name),
                    SlotSet("customer_phone", customer_phone),
                    SlotSet("appointment_active", True)
                ]
            
            # If we have service_type but missing customer details, ask for them
            if service_type and (not customer_name or not customer_phone):
                dispatcher.utter_message(text="Great! I'll help you book a {} appointment. Please provide your name and phone number to continue.".format(service_type))
                return [
                    SlotSet("service_type", service_type),
                    SlotSet("appointment_active", True)
                ]
            
            if not appointment_date or not appointment_time:
                dispatcher.utter_message(text="When would you like to schedule your appointment? (e.g., 'tomorrow 2pm')")
                return [
                    SlotSet("service_type", service_type),
                    SlotSet("customer_name", customer_name),
                    SlotSet("customer_phone", customer_phone),
                    SlotSet("appointment_active", True)
                ]
            
            # Create appointment data with confirmed status
            # All appointments are automatically confirmed upon booking
            
            # Create proper datetime field from separate date/time strings
            appointment_datetime = self._create_appointment_datetime(appointment_date, appointment_time)
            
            appointment_data = {
                'service_type': service_type,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'appointment_date': appointment_date,  # Keep for backward compatibility
                'appointment_time': appointment_time,  # Keep for backward compatibility
                'appointment_datetime': appointment_datetime,  # New unified datetime field
                'customer_email': customer_email or '',
                'status': 'confirmed',  # Changed from 'pending' to 'confirmed' as requested
                'client_id': client_id,  # Current client ID for multi-tenant support
                'appointment_id': str(ObjectId()),
                'created_at': datetime.now()
            }
            
            # Save appointment to database
            if self._save_appointment(appointment_data):
                confirmation_message = self._generate_confirmation_message(appointment_data)
                dispatcher.utter_message(text=confirmation_message)
            else:
                dispatcher.utter_message(text="❌ Sorry, there was an error booking your appointment. Please try again.")
            
            return self._clear_appointment_slots()
                
        except Exception as e:
            logger.error(f"[APPOINTMENT_BOOKING] CRITICAL ERROR in ActionBookAppointment: {e}", exc_info=True)
            dispatcher.utter_message(text="❌ Sorry, there was an error processing your request. Please try again.")
            return self._clear_appointment_slots()
    
    def _extract_date_time_from_message(self, message):
        """Extract date and time from combined inputs like 'monday 1pm'"""
        try:
            message_lower = message.lower()
            extracted_date = None
            extracted_time = None
            
            # Days of the week mapping
            days_of_week = {
                'monday': 'monday', 'mon': 'monday',
                'tuesday': 'tuesday', 'tue': 'tuesday', 'tues': 'tuesday',
                'wednesday': 'wednesday', 'wed': 'wednesday',
                'thursday': 'thursday', 'thu': 'thursday', 'thur': 'thursday', 'thurs': 'thursday',
                'friday': 'friday', 'fri': 'friday',
                'saturday': 'saturday', 'sat': 'saturday',
                'sunday': 'sunday', 'sun': 'sunday'
            }
            
            # Extract date
            if 'today' in message_lower:
                extracted_date = 'today'
            elif 'tomorrow' in message_lower:
                extracted_date = 'tomorrow'
            else:
                # Check for days of the week
                for day_variant, day_name in days_of_week.items():
                    if day_variant in message_lower:
                        extracted_date = day_name
                        break
            
            # Extract time - handle various formats
            time_patterns = [
                r'(\d{1,2})\s*(am|pm)',  # 1pm, 2 am
                r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 1:30pm, 2:00 am
                r'(\d{1,2})\.(\d{2})\s*(am|pm)',  # 1.30pm
            ]
            
            for pattern in time_patterns:
                time_match = re.search(pattern, message_lower)
                if time_match:
                    if len(time_match.groups()) == 2:  # Simple format like "1pm"
                        hour = time_match.group(1)
                        period = time_match.group(2).upper()
                        extracted_time = f"{hour}{period}"
                    elif len(time_match.groups()) == 3:  # Format with minutes like "1:30pm"
                        hour = time_match.group(1)
                        minutes = time_match.group(2)
                        period = time_match.group(3).upper()
                        extracted_time = f"{hour}:{minutes}{period}"
                    break
            
            return extracted_date, extracted_time
            
        except Exception as e:
            print(f"Error extracting date/time: {e}")
            return None, None
    
    def _create_appointment_datetime(self, appointment_date: str, appointment_time: str) -> datetime:
        """Create a proper datetime object from separate date and time strings
        
        Args:
            appointment_date: Date string (e.g., "Monday", "tomorrow", "2024-01-15")
            appointment_time: Time string (e.g., "2pm", "14:00", "2:00 PM")
            
        Returns:
            datetime: Combined datetime object in Singapore timezone
        """
        try:
            import pytz
            from dateutil import parser
            from dateutil.relativedelta import relativedelta
            
            sg_tz = pytz.timezone('Asia/Singapore')
            now = datetime.now(sg_tz)
            
            # Parse date part
            date_obj = None
            appointment_date_lower = appointment_date.lower().strip()
            
            if appointment_date_lower in ['today']:
                date_obj = now.date()
            elif appointment_date_lower in ['tomorrow']:
                date_obj = (now + relativedelta(days=1)).date()
            elif appointment_date_lower in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                # Find next occurrence of this weekday
                weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                target_weekday = weekdays.index(appointment_date_lower)
                days_ahead = target_weekday - now.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                date_obj = (now + relativedelta(days=days_ahead)).date()
            else:
                # Try to parse as a specific date
                try:
                    parsed_date = parser.parse(appointment_date, default=now)
                    date_obj = parsed_date.date()
                except:
                    # Fallback to tomorrow if parsing fails
                    date_obj = (now + relativedelta(days=1)).date()
            
            # Parse time part
            time_obj = None
            appointment_time_clean = appointment_time.lower().strip()
            
            # Handle common time formats
            time_patterns = [
                (r'(\d{1,2})\s*pm', lambda m: datetime.strptime(f"{int(m.group(1)) + (0 if int(m.group(1)) == 12 else 12)}:00", "%H:%M").time()),
                (r'(\d{1,2})\s*am', lambda m: datetime.strptime(f"{int(m.group(1)) if int(m.group(1)) != 12 else 0}:00", "%H:%M").time()),
                (r'(\d{1,2}):(\d{2})\s*pm', lambda m: datetime.strptime(f"{int(m.group(1)) + (0 if int(m.group(1)) == 12 else 12)}:{m.group(2)}", "%H:%M").time()),
                (r'(\d{1,2}):(\d{2})\s*am', lambda m: datetime.strptime(f"{int(m.group(1)) if int(m.group(1)) != 12 else 0}:{m.group(2)}", "%H:%M").time()),
                (r'(\d{1,2}):(\d{2})', lambda m: datetime.strptime(f"{m.group(1)}:{m.group(2)}", "%H:%M").time()),
            ]
            
            import re
            for pattern, converter in time_patterns:
                match = re.search(pattern, appointment_time_clean)
                if match:
                    time_obj = converter(match)
                    break
            
            if not time_obj:
                # Fallback to 2 PM if parsing fails
                time_obj = datetime.strptime("14:00", "%H:%M").time()
            
            # Combine date and time
            combined_datetime = datetime.combine(date_obj, time_obj)
            
            # Localize to Singapore timezone
            localized_datetime = sg_tz.localize(combined_datetime)
            
            return localized_datetime
            
        except Exception as e:
            logger.error(f"Error creating appointment datetime: {e}")
            # Fallback to tomorrow 2 PM
            import pytz
            sg_tz = pytz.timezone('Asia/Singapore')
            now = datetime.now(sg_tz)
            fallback = now.replace(hour=14, minute=0, second=0, microsecond=0) + relativedelta(days=1)
            return fallback
    
    def _clear_appointment_slots(self) -> List[SlotSet]:
        """Clear all appointment-related slots after booking completion or cancellation"""
        return [
            SlotSet("appointment_active", False),
            SlotSet("service_type", None),
            SlotSet("appointment_date", None),
            SlotSet("appointment_time", None),
            SlotSet("customer_name", None),
            SlotSet("customer_phone", None),
            SlotSet("customer_email", None),
            SlotSet("appointment_id", None)
        ]
    
    def _save_appointment(self, appointment_data: Dict[str, Any]) -> bool:
        """Save appointment to database"""
        try:
            logger.info(f"[APPOINTMENT_BOOKING] Attempting to save appointment to MongoDB")
            logger.debug(f"[APPOINTMENT_BOOKING] Appointment data to save: {appointment_data}")
            
            with DatabaseContext('appointments') as collection:
                if not collection:
                    logger.error(f"[APPOINTMENT_BOOKING] CRITICAL: Failed to get database collection for appointments")
                    return False
                
                logger.info(f"[APPOINTMENT_BOOKING] Database collection obtained successfully")
                result = collection.insert_one(appointment_data)
                
                if result.inserted_id is not None:
                    logger.info(f"[APPOINTMENT_BOOKING] SUCCESS: Appointment saved to MongoDB with ID: {result.inserted_id}")
                    logger.debug(f"[APPOINTMENT_BOOKING] Insert result details: {result}")
                    return True
                else:
                    logger.error(f"[APPOINTMENT_BOOKING] CRITICAL: Failed to insert appointment - no ID returned")
                    return False
                
        except Exception as e:
            logger.error(f"[APPOINTMENT_BOOKING] CRITICAL: Error saving appointment to MongoDB: {e}", exc_info=True)
            logger.error(f"[APPOINTMENT_BOOKING] Failed appointment data: {appointment_data}")
            return False
    
    def _extract_phone_number(self, text: str) -> Optional[str]:
        """Extract phone number from text using regex patterns"""
        if not text:
            return None
            
        # Common phone number patterns for Singapore
        phone_patterns = [
            r'\b(\+65\s?)?([689]\d{7})\b',  # Singapore format: +65 91234567 or 91234567
            r'\b(\+65\s?)?([689]\d{3}[\s-]?\d{4})\b',  # With separator: 9123-4567
            r'\b\d{8}\b',  # 8-digit numbers
            r'\b\d{4}[\s-]?\d{4}\b',  # 4-4 format
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    # Extract the phone number part (second group)
                    # Add bounds checking to prevent empty tuple access
                    if len(matches[0]) > 1:
                        phone = matches[0][1]
                    elif len(matches[0]) > 0:
                        phone = matches[0][0]
                    else:
                        continue  # Skip empty tuple
                else:
                    phone = matches[0]
                
                # Clean up the phone number
                phone = re.sub(r'[\s-]', '', phone)
                
                # Validate Singapore phone number format
                if len(phone) == 8 and phone[0] in '689':
                    return phone
                elif len(phone) == 10 and phone.startswith('65'):
                    return phone[2:]  # Remove country code
                    
        return None
    
    def _generate_confirmation_message(self, appointment_data: Dict[str, Any]) -> str:
        """Generate appointment confirmation message - short and user-friendly"""
        appointment_datetime = appointment_data["appointment_datetime"]
        formatted_date = appointment_datetime.strftime('%B %d, %Y')
        formatted_time = appointment_datetime.strftime('%I:%M %p')
        service_type = appointment_data['service_type']
        
        # Short, clean confirmation message to prevent split responses
        return f"✅ Appointment Confirmed! 📅 {formatted_date} at {formatted_time} 🔧 Service: {service_type.title()} 👤 Customer: {appointment_data['customer_name']} 📱 Phone: {appointment_data['customer_phone']} 📧 Confirmation sent to your email! ⏰ We'll remind you 24 hours before. 💬 Need to reschedule? Just send us a message!"


class ActionViewAppointments(AutoLoggedAction):
    """View customer's appointments
    
    Features:
    - Shows upcoming appointments
    - Displays appointment history
    - Provides appointment details
    """
    
    def name(self) -> Text:
        return "action_view_appointments"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Check if appointment booking feature is enabled for this client
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            if client_id:
                if not check_appointment_feature_enabled(client_id):
                    dispatcher.utter_message(
                        text="I'm sorry, but appointment viewing is currently not available. Please contact our support team for assistance."
                    )
                    return []
            
            # Get customer phone number to find appointments
            customer_phone = tracker.get_slot("customer_phone")
            
            # If no phone in slot, check if current message contains phone entity
            if not customer_phone:
                entities = tracker.latest_message.get('entities', [])
                phone_entities = [e for e in entities if e.get('entity') == 'customer_phone']
                if phone_entities:
                    customer_phone = phone_entities[0].get('value')
                    # Set the slot for future use
                    return [SlotSet("customer_phone", customer_phone)]
            
            if not customer_phone:
                dispatcher.utter_message(
                    text="📱 **Let me help you check your appointments!**\n\nTo view your booking history and upcoming appointments, I'll need your phone number. Please provide the number you used when making your bookings."
                )
                return []
            
            appointments = self._get_customer_appointments(customer_phone)
            
            if not appointments:
                dispatcher.utter_message(
                    text="🔍 **No Appointments Found**\n\nI couldn't find any appointments linked to this phone number in our system.\n\n💡 **Possible reasons:**\n• Different phone number was used for booking\n• Appointments were made under a different contact\n• No appointments have been scheduled yet\n\n🚗 **Ready to get started?** I'd be happy to help you book your first appointment! Just let me know what service you need."
                )
                return []
            
            # Separate upcoming and past appointments
            # Use Singapore timezone to match how appointments are stored
            import pytz
            sg_tz = pytz.timezone('Asia/Singapore')
            now = datetime.now(sg_tz)
            upcoming = [apt for apt in appointments if apt['appointment_datetime'] > now]
            past = [apt for apt in appointments if apt['appointment_datetime'] <= now]
            
            message = self._format_appointments_message(upcoming, past)
            dispatcher.utter_message(text=message)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in ActionViewAppointments: {e}")
            dispatcher.utter_message(
                text="Sorry, there was an error retrieving your appointments. Please try again."
            )
            return []
    
    def _get_customer_appointments(self, customer_phone: str) -> List[Dict[str, Any]]:
        """Get all appointments for a customer"""
        try:
            with DatabaseContext('appointments') as collection:
                if not collection:
                    return []
                
                # Get appointments and sort by appointment_date, then appointment_time
                # Since we now store appointment_datetime field, we can sort by that
                appointments = list(collection.find({
                    "customer_phone": customer_phone
                }).sort("appointment_date", -1))
                
                # Convert appointments to include appointment_datetime for compatibility
                processed_appointments = []
                for apt in appointments:
                    # If appointment_datetime doesn't exist, create it from date and time
                    if 'appointment_datetime' not in apt:
                        try:
                            # Parse the stored date and time strings
                            date_str = apt.get('appointment_date', '')
                            time_str = apt.get('appointment_time', '')
                            
                            # Create datetime object
                            if date_str and time_str:
                                # Combine date and time strings
                                datetime_str = f"{date_str} {time_str}"
                                # Try to parse the combined string
                                apt_datetime = parser.parse(datetime_str)
                                # Localize to Singapore timezone
                                sg_tz = pytz.timezone('Asia/Singapore')
                                if apt_datetime.tzinfo is None:
                                    apt_datetime = sg_tz.localize(apt_datetime)
                                apt['appointment_datetime'] = apt_datetime
                            else:
                                # Skip appointments without proper date/time
                                continue
                        except Exception as e:
                            logger.error(f"Error parsing appointment datetime: {e}")
                            continue
                    
                    processed_appointments.append(apt)
                
                # Sort by appointment_datetime
                processed_appointments.sort(key=lambda x: x['appointment_datetime'], reverse=True)
                
                return processed_appointments
                
        except Exception as e:
            logger.error(f"Error getting customer appointments: {e}")
            return []
    
    def _format_appointments_message(self, upcoming: List[Dict], past: List[Dict]) -> str:
        """Format appointments into a readable message"""
        message_parts = []
        
        # Add header message
        total_appointments = len(upcoming) + len(past)
        message_parts.append(f"""<div style="margin-bottom: 20px; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; text-align: center;">
    <h2 style="margin: 0 0 8px 0; font-size: 24px;">🗓️ Your Appointment Dashboard</h2>
    <p style="margin: 0; opacity: 0.9;">Found {total_appointments} appointment{'s' if total_appointments != 1 else ''} in your booking history</p>
</div>""")
        
        if upcoming:
            message_parts.append("<div style='margin-bottom: 20px;'>")
            message_parts.append("<h3 style='color: #059669; margin-bottom: 12px;'>📅 Upcoming Appointments</h3>")
            
            for apt in upcoming:
                formatted_date = apt['appointment_datetime'].strftime('%B %d, %Y')
                formatted_time = apt['appointment_datetime'].strftime('%I:%M %p')
                
                message_parts.append(f"""
<div style="
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 12px;
">
    <p style="margin: 0 0 8px 0; font-weight: bold; color: #059669;">ID: {apt['appointment_id'][:8]}</p>
    <p style="margin: 0 0 4px 0;"><strong>Date:</strong> {formatted_date}</p>
    <p style="margin: 0 0 4px 0;"><strong>Time:</strong> {formatted_time}</p>
    <p style="margin: 0 0 4px 0;"><strong>Service:</strong> {apt['service_type']}</p>
    <p style="margin: 0;"><strong>Status:</strong> {apt['status'].title()}</p>
</div>
""")
            
            message_parts.append("</div>")
        
        if past:
            message_parts.append("<div style='margin-bottom: 20px;'>")
            message_parts.append("<h3 style='color: #6b7280; margin-bottom: 12px;'>📋 Past Appointments</h3>")
            
            for apt in past[:3]:  # Show only last 3 past appointments
                formatted_date = apt['appointment_datetime'].strftime('%B %d, %Y')
                formatted_time = apt['appointment_datetime'].strftime('%I:%M %p')
                
                message_parts.append(f"""
<div style="
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 12px;
">
    <p style="margin: 0 0 8px 0; font-weight: bold; color: #6b7280;">ID: {apt['appointment_id'][:8]}</p>
    <p style="margin: 0 0 4px 0;"><strong>Date:</strong> {formatted_date}</p>
    <p style="margin: 0 0 4px 0;"><strong>Time:</strong> {formatted_time}</p>
    <p style="margin: 0 0 4px 0;"><strong>Service:</strong> {apt['service_type']}</p>
    <p style="margin: 0;"><strong>Status:</strong> {apt['status'].title()}</p>
</div>
""")
            
            if len(past) > 3:
                message_parts.append(f"<p style='color: #6b7280; font-style: italic;'>... and {len(past) - 3} more past appointments</p>")
            
            message_parts.append("</div>")
        
        if not upcoming and not past:
            return "No appointments found."
        
        return "".join(message_parts)
    



class ActionCancelAppointment(AutoLoggedAction):
    """Cancel an existing appointment
    
    Features:
    - Cancels appointment by ID
    - Updates appointment status
    - Provides cancellation confirmation
    """
    
    def name(self) -> Text:
        return "action_cancel_appointment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Check if appointment booking feature is enabled for this client
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            if client_id:
                if not check_appointment_feature_enabled(client_id):
                    dispatcher.utter_message(
                        text="I'm sorry, but appointment management is currently not available. Please contact our support team for assistance."
                    )
                    return []
            
            appointment_id = tracker.get_slot("appointment_id")
            customer_phone = tracker.get_slot("customer_phone")
            
            if not appointment_id:
                dispatcher.utter_message(
                    text="🔍 I'd be happy to help you cancel your appointment! To proceed, I'll need your appointment ID. You can find this in your booking confirmation."
                )
                return []
            
            if not customer_phone:
                dispatcher.utter_message(
                    text="📱 For security purposes, I'll need to verify your phone number before cancelling the appointment. Could you please provide the phone number used for booking?"
                )
                return []
            
            success, cancelled_appointment = self._cancel_appointment(appointment_id, customer_phone)
            
            if success:
                dispatcher.utter_message(
                    text=f"✅ **Appointment Successfully Cancelled!**\n\nYour appointment (ID: {appointment_id[:8]}) has been cancelled and removed from our system. \n\n💡 **What's next?**\n• Need to reschedule? I can help you find a new time slot\n• Have questions? Feel free to ask me anything\n• Want to book a different service? Just let me know!\n\nThank you for letting us know in advance! 😊"
                )
                
                # Send email cancellation notification if enabled and email available
                try:
                    if is_email_enabled() and cancelled_appointment and cancelled_appointment.get('customer_email'):
                        # Prepare email data with formatted date/time
                        # Handle both new appointments (with appointment_datetime) and old ones (with separate fields)
                        if 'appointment_datetime' in cancelled_appointment:
                            appointment_date = cancelled_appointment['appointment_datetime'].strftime('%B %d, %Y')
                            appointment_time = cancelled_appointment['appointment_datetime'].strftime('%I:%M %p')
                        else:
                            # Fallback to separate date and time fields
                            appointment_date = cancelled_appointment.get('appointment_date', 'Unknown Date')
                            appointment_time = cancelled_appointment.get('appointment_time', 'Unknown Time')
                        
                        email_data = {
                            'customer_name': cancelled_appointment.get('customer_name', 'Customer'),
                            'customer_email': cancelled_appointment['customer_email'],
                            'appointment_id': cancelled_appointment['appointment_id'],
                            'appointment_date': appointment_date,
                            'appointment_time': appointment_time,
                            'service_type': cancelled_appointment['service_type']
                        }
                        
                        email_sent = send_appointment_cancellation_email(email_data)


                except Exception as email_error:
                    logger.error(f"Error sending email cancellation notification: {email_error}")
                    # Don't fail the cancellation if email fails
            else:
                dispatcher.utter_message(
                    text=f"🔍 **Appointment Not Found**\n\nI couldn't locate an appointment with ID **{appointment_id[:8]}** for your phone number.\n\n💡 **Please check:**\n• Is the appointment ID correct? (Check your confirmation message)\n• Did you use the same phone number for booking?\n• Has the appointment already been cancelled?\n\nIf you're still having trouble, I can help you view all your appointments to find the right ID! 📋"
                )
            
            return [SlotSet("appointment_id", None)]
            
        except Exception as e:
            logger.error(f"Error in ActionCancelAppointment: {e}")
            dispatcher.utter_message(
                text="Sorry, there was an error cancelling your appointment. Please try again or contact us directly."
            )
            return []
    
    def _cancel_appointment(self, appointment_id: str, customer_phone: str) -> tuple[bool, Optional[Dict]]:
        """Cancel appointment in database and return appointment data for SMS"""
        try:
            with DatabaseContext('appointments') as collection:
                if not collection:
                    return False, None
                
                # First, find the appointment to get its data for SMS
                appointment = collection.find_one({
                    "appointment_id": appointment_id,
                    "customer_phone": customer_phone,
                    "status": {"$in": ["confirmed", "pending"]}
                })
                
                if not appointment:
                    return False, None
                
                # Update the appointment status with timestamp
                current_time = datetime.now(pytz.timezone('Asia/Singapore'))
                result = collection.update_one(
                    {
                        "appointment_id": appointment_id,
                        "customer_phone": customer_phone,
                        "status": {"$in": ["confirmed", "pending"]}
                    },
                    {
                        "$set": {
                            "status": "cancelled",
                            "cancelled_time": current_time,
                            "updated_at": current_time
                        }
                    }
                )
                
                if result.modified_count > 0:
                    return True, appointment
                else:
                    return False, None
                
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return False, None