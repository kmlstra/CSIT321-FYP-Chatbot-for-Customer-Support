"""Appointment Booking RASA Actions
Handles appointment booking, viewing, and management for automotive services
"""

from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from backend.api.middleware.auto_logger import AutoLoggedAction
from backend.config.database import get_collection, DatabaseContext
from backend.api.utils.information import get_appointment_options_message, get_appointment_options_with_buttons, get_appointment_types, get_appointment_type_by_id
from backend.api.services.email_service import send_appointment_confirmation_email, send_appointment_cancellation_email, is_email_enabled
import logging
from datetime import datetime, timedelta
import pytz
from bson import ObjectId
import re
<<<<<<< Updated upstream
=======
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

logger = logging.getLogger(__name__)

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
            logger.warning(f"No client found for ID: {client_id}")
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
>>>>>>> Stashed changes


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
            # Get current intent and conversation context
            current_intent = tracker.latest_message.get('intent', {}).get('name')
            user_message = tracker.latest_message.get('text', '').lower()
            appointment_active = tracker.get_slot("appointment_active")
            confidence = tracker.latest_message.get('intent', {}).get('confidence', 0)
            
            logger.info(f"Validating intent: {current_intent} with confidence: {confidence}")
            logger.info(f"User message: {user_message}")
            logger.info(f"Appointment active: {appointment_active}")
            
            # Check if user is in middle of booking process
            if appointment_active:
                # If user is booking and says something unrelated, guide them back
                if current_intent not in ['book_appointment', 'provide_info', 'affirm', 'deny']:
                    dispatcher.utter_message(
                        text="I notice you're in the middle of booking an appointment. Would you like to continue with the booking or start something else? Just let me know!"
                    )
                    return [SlotSet("appointment_active", None)]
            
            # Check for low confidence predictions
            if confidence < 0.7:
                logger.warning(f"Low confidence intent prediction: {current_intent} ({confidence})")
                return self._handle_unclear_intent(dispatcher, user_message)
            
            # Validate appointment-related intents have required context
            validation_result = self._validate_intent_context(current_intent, user_message, tracker)
            if validation_result:
                dispatcher.utter_message(text=validation_result)
                return []
            
            # Check for potential misclassified intents
            misclassification_result = self._check_misclassification(current_intent, user_message, dispatcher)
            if misclassification_result:
                return misclassification_result
            
            # Intent is valid for current context
            return []
            
        except Exception as e:
            logger.error(f"Error in ActionValidateIntent: {e}")
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
            dispatcher.utter_message(
                text="It sounds like you want to book an appointment. "
                     "I can help you schedule a test drive, sales consultation, or trade-in evaluation. "
                     "What type of appointment would you like?"
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

logger = logging.getLogger(__name__)


class ActionBookAppointment(AutoLoggedAction):
    """Book a new appointment for automotive services
    
    Features:
    - Collects appointment details (date, time, service type, contact info)
    - Validates appointment slots
    - Stores appointment in database
    - Provides confirmation with appointment ID
    """
    
    def name(self) -> Text:
        return "action_book_appointment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Extract slots
            appointment_date = tracker.get_slot("appointment_date")
            appointment_time = tracker.get_slot("appointment_time")
            service_type = tracker.get_slot("service_type")
            customer_name = tracker.get_slot("customer_name")
            customer_phone = tracker.get_slot("customer_phone")
            customer_email = tracker.get_slot("customer_email")
            appointment_active = tracker.get_slot("appointment_active")
            
            # Extract entities from current message to supplement slots
            latest_message = tracker.latest_message
            entities = latest_message.get('entities', [])
            
            # Update slots with entities from current message if slots are empty
            for entity in entities:
                entity_name = entity.get('entity')
                entity_value = entity.get('value')
                
                if entity_name == 'appointment_date' and not appointment_date:
                    appointment_date = entity_value
                elif entity_name == 'appointment_time' and not appointment_time:
                    appointment_time = entity_value
                elif entity_name == 'service_type' and not service_type:
                    service_type = entity_value
                elif entity_name == 'customer_name' and not customer_name:
                    customer_name = entity_value
                elif entity_name == 'customer_phone' and not customer_phone:
                    customer_phone = entity_value
                elif entity_name == 'customer_email' and not customer_email:
                    customer_email = entity_value
            
            # CRITICAL FIX: Fallback for button payloads when service_type entity is not extracted
            if not service_type:
                user_message = tracker.latest_message.get('text', '').lower().strip()
                # Map button payloads to service types
                service_mapping = {
                    'sales consultation': 'Sales Consultation',
                    'test drive': 'Test Drive', 
                    'trade-in evaluation': 'Trade-in Evaluation',
                }
                
                if user_message in service_mapping:
                    service_type = service_mapping[user_message]
                    logger.info(f"Button payload detected: '{user_message}' -> service_type: '{service_type}'")
            
            # Fallback phone number extraction if not detected as entity
            if not customer_phone:
                user_message = tracker.latest_message.get('text', '')
                extracted_phone = self._extract_phone_number(user_message)
                if extracted_phone:
                    customer_phone = extracted_phone
            
            # Fallback for combined date-time inputs like "wednesday 2pm"
            if not appointment_date or not appointment_time:
                user_message = tracker.latest_message.get('text', '').lower()
                parsed_datetime = self._parse_combined_datetime(user_message)
                if parsed_datetime:
                    if not appointment_date and parsed_datetime.get('date'):
                        appointment_date = parsed_datetime['date']
                    if not appointment_time and parsed_datetime.get('time'):
                        appointment_time = parsed_datetime['time']
            
            # Set appointment_active to true when booking starts
            if not appointment_active:
                logger.info("Setting appointment_active to True - starting booking flow")
                
                # # Check if user provided date/time info in their initial request
                # if appointment_date and appointment_time:
                #     # User provided date/time, skip welcome and go to service selection
                #     logger.info("User provided date/time info, proceeding to service selection")
                #     service_options = self._get_service_options_message()
                #     dispatcher.utter_message(
                #         text=f"📅 **Great! I have {appointment_date} at {appointment_time}.**\n\n{service_options['text']}",
                #         buttons=service_options["buttons"]
                #     )
                #     # Return early to prevent continuing to step-by-step flow
                #     slot_updates = [SlotSet("appointment_active", True)]
                #     if appointment_date:
                #         slot_updates.append(SlotSet("appointment_date", appointment_date))
                #     if appointment_time:
                #         slot_updates.append(SlotSet("appointment_time", appointment_time))
                #     if service_type:
                #         slot_updates.append(SlotSet("service_type", service_type))
                #     if customer_name:
                #         slot_updates.append(SlotSet("customer_name", customer_name))
                #     if customer_phone:
                #         slot_updates.append(SlotSet("customer_phone", customer_phone))
                #     if customer_email:
                #         slot_updates.append(SlotSet("customer_email", customer_email))
                #     return slot_updates
                if appointment_date or appointment_time:
                    # User provided partial date/time info
                    logger.info("User provided partial date/time info, proceeding to service selection")
                    service_options = self._get_service_options_message()
                    partial_info = appointment_date or appointment_time
                    dispatcher.utter_message(
                        text=f"📅 **Perfect! I have {partial_info} noted.**\n\n{service_options['text']}",
                        buttons=service_options["buttons"]
                    )
                    # Return early to prevent continuing to step-by-step flow
                    slot_updates = [SlotSet("appointment_active", True)]
                    if appointment_date:
                        slot_updates.append(SlotSet("appointment_date", appointment_date))
                    if appointment_time:
                        slot_updates.append(SlotSet("appointment_time", appointment_time))
                    if service_type:
                        slot_updates.append(SlotSet("service_type", service_type))
                    if customer_name:
                        slot_updates.append(SlotSet("customer_name", customer_name))
                    if customer_phone:
                        slot_updates.append(SlotSet("customer_phone", customer_phone))
                    if customer_email:
                        slot_updates.append(SlotSet("customer_email", customer_email))
                    return slot_updates
                else:
                    # Standard welcome message with service selection
                    service_options = self._get_service_options_message()
                    logger.info(f"Sending service options with {len(service_options['buttons'])} buttons: {service_options['buttons']}")
                    dispatcher.utter_message(
                        text=service_options["text"],
                        buttons=service_options["buttons"]
                    )
                    # Return early to prevent continuing to step-by-step flow
                    slot_updates = [SlotSet("appointment_active", True)]
                    if appointment_date:
                        slot_updates.append(SlotSet("appointment_date", appointment_date))
                    if appointment_time:
                        slot_updates.append(SlotSet("appointment_time", appointment_time))
                    if service_type:
                        slot_updates.append(SlotSet("service_type", service_type))
                    if customer_name:
                        slot_updates.append(SlotSet("customer_name", customer_name))
                    if customer_phone:
                        slot_updates.append(SlotSet("customer_phone", customer_phone))
                    if customer_email:
                        slot_updates.append(SlotSet("customer_email", customer_email))
                    return slot_updates
            
            # Special handling: If appointment is active and user already provided date/time,
            # and now they're providing service type, proceed to contact info collection
            elif appointment_active and appointment_date and appointment_time and service_type and (not customer_name or not customer_phone):
                logger.info("User provided service type after date/time, proceeding to contact info collection")
                # Preserve any extracted entities as slots
>>>>>>> Stashed changes
                slot_updates = [SlotSet("appointment_active", True)]
                if appointment_date:
                    slot_updates.append(SlotSet("appointment_date", appointment_date))
                if appointment_time:
                    slot_updates.append(SlotSet("appointment_time", appointment_time))
                if service_type:
                    slot_updates.append(SlotSet("service_type", service_type))
                if customer_name:
                    slot_updates.append(SlotSet("customer_name", customer_name))
                if customer_phone:
                    slot_updates.append(SlotSet("customer_phone", customer_phone))
                if customer_email:
                    slot_updates.append(SlotSet("customer_email", customer_email))
                
                # Ask for contact information directly
                contact_message = self._generate_contact_request_message(customer_name, customer_phone)
                dispatcher.utter_message(text=contact_message)
                return slot_updates
            
            # Additional check: If user just provided service type and we have date/time from slots, proceed to contact info
            elif appointment_active and service_type and tracker.get_slot("appointment_date") and tracker.get_slot("appointment_time") and (not customer_name or not customer_phone):
                logger.info("Service type provided, date/time already in slots, proceeding to contact info")
                # Use slot values for date/time if not in current entities
                slot_date = tracker.get_slot("appointment_date") if not appointment_date else appointment_date
                slot_time = tracker.get_slot("appointment_time") if not appointment_time else appointment_time
                
                # Preserve any extracted entities as slots
                slot_updates = [SlotSet("appointment_active", True)]
                slot_updates.append(SlotSet("appointment_date", slot_date))
                slot_updates.append(SlotSet("appointment_time", slot_time))
                slot_updates.append(SlotSet("service_type", service_type))
                if customer_name:
                    slot_updates.append(SlotSet("customer_name", customer_name))
                if customer_phone:
                    slot_updates.append(SlotSet("customer_phone", customer_phone))
                if customer_email:
                    slot_updates.append(SlotSet("customer_email", customer_email))
                
                # Ask for contact information directly
                contact_message = self._generate_contact_request_message(customer_name, customer_phone)
                dispatcher.utter_message(text=contact_message)
                return slot_updates
            
            # Debug: Log current slot values
            logger.info(f"Current entities - Date: {appointment_date}, Time: {appointment_time}, Service: {service_type}, Name: {customer_name}, Phone: {customer_phone}, Email: {customer_email}")
            
            # Step-by-step information collection - improved flow logic
            # Priority 1: If appointment is active and service type is provided, proceed to date/time
            # Priority 2: If date/time provided but no service type, ask for service type
            # Priority 3: If service type provided but no date/time, ask for date/time  
            # Priority 4: If both provided but no contact info, ask for contact info
            
            # Check what's missing and prioritize based on what user provided
            # Also check slot values to get complete picture
            slot_service = tracker.get_slot("service_type")
            slot_date = tracker.get_slot("appointment_date")
            slot_time = tracker.get_slot("appointment_time")
            slot_name = tracker.get_slot("customer_name")
            slot_phone = tracker.get_slot("customer_phone")
            
            # Use current entities or fall back to slot values
            current_service = service_type or slot_service
            current_date = appointment_date or slot_date
            current_time = appointment_time or slot_time
            current_name = customer_name or slot_name
            current_phone = customer_phone or slot_phone
            
            missing_service = not current_service
            missing_datetime = not current_date or not current_time
            missing_contact = not current_name or not current_phone
            
            logger.info(f"Flow check - Service: {current_service} (entity: {service_type}, slot: {slot_service}), Date: {current_date}, Time: {current_time}, Name: {current_name}, Phone: {current_phone}")
            logger.info(f"Missing flags - Service: {missing_service}, DateTime: {missing_datetime}, Contact: {missing_contact}")
            
            # CRITICAL FIX: If appointment is active and user just provided a service type, proceed to date/time
            if appointment_active and service_type and missing_datetime:
                logger.info("Service type provided after initial options, proceeding to date/time request")
                # Preserve any extracted entities as slots
                slot_updates = [SlotSet("appointment_active", True)]
                if current_date:
                    slot_updates.append(SlotSet("appointment_date", current_date))
                if current_time:
                    slot_updates.append(SlotSet("appointment_time", current_time))
                if service_type:  # Use the newly provided service type
                    slot_updates.append(SlotSet("service_type", service_type))
                if current_name:
                    slot_updates.append(SlotSet("customer_name", current_name))
                if current_phone:
                    slot_updates.append(SlotSet("customer_phone", current_phone))
                if customer_email:
                    slot_updates.append(SlotSet("customer_email", customer_email))
                
                # Ask for date and time
                datetime_message = self._generate_datetime_request_message(service_type, current_date, current_time)
                dispatcher.utter_message(text=datetime_message)
                return slot_updates
            
            # If user provided date/time first but no service type, ask for service type
            if missing_service and not missing_datetime:
                # Preserve any extracted entities as slots
                slot_updates = [SlotSet("appointment_active", True)]
                if current_date:
                    slot_updates.append(SlotSet("appointment_date", current_date))
                if current_time:
                    slot_updates.append(SlotSet("appointment_time", current_time))
                if current_name:
                    slot_updates.append(SlotSet("customer_name", current_name))
                if current_phone:
                    slot_updates.append(SlotSet("customer_phone", current_phone))
                if customer_email:
                    slot_updates.append(SlotSet("customer_email", customer_email))
                
                # Ask for service type selection with clickable buttons
                service_options = self._get_service_options_message()
                dispatcher.utter_message(
                    text=service_options["text"],
                    buttons=service_options["buttons"]
                )
                return slot_updates
            
            # If user provided service type first but no date/time, ask for date/time
            elif missing_datetime and not missing_service:
                # Preserve any extracted entities as slots
                slot_updates = [SlotSet("appointment_active", True)]
                if current_date:
                    slot_updates.append(SlotSet("appointment_date", current_date))
                if current_time:
                    slot_updates.append(SlotSet("appointment_time", current_time))
                if current_service:
                    slot_updates.append(SlotSet("service_type", current_service))
                if current_name:
                    slot_updates.append(SlotSet("customer_name", current_name))
                if current_phone:
                    slot_updates.append(SlotSet("customer_phone", current_phone))
                if customer_email:
                    slot_updates.append(SlotSet("customer_email", customer_email))
                
                # Ask for date and time
                datetime_message = self._generate_datetime_request_message(current_service, current_date, current_time)
                dispatcher.utter_message(text=datetime_message)
                return slot_updates
            
            # If both service and datetime missing, ask for service type first (default flow)
            elif missing_service and missing_datetime:
                # Preserve any extracted entities as slots
                slot_updates = [SlotSet("appointment_active", True)]
                if current_date:
                    slot_updates.append(SlotSet("appointment_date", current_date))
                if current_time:
                    slot_updates.append(SlotSet("appointment_time", current_time))
                if current_name:
                    slot_updates.append(SlotSet("customer_name", current_name))
                if current_phone:
                    slot_updates.append(SlotSet("customer_phone", current_phone))
                if customer_email:
                    slot_updates.append(SlotSet("customer_email", customer_email))
                
                # Ask for service type selection with clickable buttons
                service_options = self._get_service_options_message()
                dispatcher.utter_message(
                    text=service_options["text"],
                    buttons=service_options["buttons"]
                )
                return slot_updates
            
            # If service type is already in slots but datetime is missing, ask for datetime
            elif not missing_service and missing_datetime:
                # Preserve any extracted entities as slots
                slot_updates = [SlotSet("appointment_active", True)]
                if current_date:
                    slot_updates.append(SlotSet("appointment_date", current_date))
                if current_time:
                    slot_updates.append(SlotSet("appointment_time", current_time))
                if current_service:
                    slot_updates.append(SlotSet("service_type", current_service))
                if current_name:
                    slot_updates.append(SlotSet("customer_name", current_name))
                if current_phone:
                    slot_updates.append(SlotSet("customer_phone", current_phone))
                if customer_email:
                    slot_updates.append(SlotSet("customer_email", customer_email))
                
                # Ask for date and time
                datetime_message = self._generate_datetime_request_message(current_service, current_date, current_time)
                dispatcher.utter_message(text=datetime_message)
                return slot_updates
            
            # Contact information collection (after both service and datetime are set)
            elif not current_name or not current_phone:
                # Preserve any extracted entities as slots
                slot_updates = [SlotSet("appointment_active", True)]
                if current_date:
                    slot_updates.append(SlotSet("appointment_date", current_date))
                if current_time:
                    slot_updates.append(SlotSet("appointment_time", current_time))
                if current_service:
                    slot_updates.append(SlotSet("service_type", current_service))
                if current_name:
                    slot_updates.append(SlotSet("customer_name", current_name))
                if current_phone:
                    slot_updates.append(SlotSet("customer_phone", current_phone))
                if customer_email:
                    slot_updates.append(SlotSet("customer_email", customer_email))
                
                # Ask for contact information
                contact_message = self._generate_contact_request_message(current_name, current_phone)
                dispatcher.utter_message(text=contact_message)
                return slot_updates
            
            # Validate and parse appointment date/time
            # Ensure current_date and current_time are strings before parsing
            if not isinstance(current_date, str) or not isinstance(current_time, str):
                error_message = self._generate_datetime_error_message()
                dispatcher.utter_message(text=error_message)
                return []
            
            appointment_datetime = self._parse_appointment_datetime(current_date, current_time)
            if not appointment_datetime:
                error_message = self._generate_datetime_error_message()
                dispatcher.utter_message(text=error_message)
                return []
            
            # Check if appointment slot is available
            if not self._is_slot_available(appointment_datetime):
                unavailable_message = self._generate_slot_unavailable_message(appointment_datetime)
                dispatcher.utter_message(text=unavailable_message)
                return []
            
            # Create appointment record
            appointment_data = {
                "appointment_id": str(ObjectId()),
                "customer_name": current_name,
                "customer_phone": current_phone,
                "customer_email": customer_email or "",
                "service_type": current_service,
                "appointment_datetime": appointment_datetime,
                "status": "confirmed",
                "created_at": datetime.utcnow(),
                "notes": "",
                "conversation_id": tracker.sender_id
            }
            
            # Save to database
            success = self._save_appointment(appointment_data)
            if success:
                confirmation_message = self._generate_confirmation_message(appointment_data)
                dispatcher.utter_message(text=confirmation_message)
                
                # Send email confirmation if enabled and email provided
                try:
                    if is_email_enabled() and customer_email:
                        # Prepare email data with formatted date/time
                        email_data = appointment_data.copy()
                        email_data['appointment_date'] = appointment_datetime.strftime('%B %d, %Y')
                        email_data['appointment_time'] = appointment_datetime.strftime('%I:%M %p')
                        
                        email_sent = send_appointment_confirmation_email(email_data)
                        if email_sent:
                            logger.info(f"Email confirmation sent for appointment {appointment_data['appointment_id'][:8]}")
                        else:
                            logger.warning(f"Failed to send email confirmation for appointment {appointment_data['appointment_id'][:8]}")
                    elif not customer_email:
                        logger.info("No email address provided - skipping email confirmation")
                    else:
                        logger.info("Email service not enabled - skipping email confirmation")
                except Exception as email_error:
                    logger.error(f"Error sending email confirmation: {email_error}")
                    # Don't fail the booking if email fails
                
                # Clear appointment slots and add follow-up action
                return [
                    SlotSet("appointment_date", None),
                    SlotSet("appointment_time", None),
                    SlotSet("service_type", None),
                    SlotSet("customer_name", None),
                    SlotSet("customer_phone", None),
                    SlotSet("customer_email", None),
                    SlotSet("appointment_active", None),
                    FollowupAction("action_listen")
                ]
            else:
                dispatcher.utter_message(
                    text="Sorry, there was an error booking your appointment. Please try again or contact us directly."
                )
                return []
                
        except Exception as e:
            logger.error(f"Error in ActionBookAppointment: {e}")
            dispatcher.utter_message(
                text="Sorry, there was an error processing your appointment request. Please try again."
            )
            return []
    
    def _parse_appointment_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse appointment date and time strings into datetime object"""
        try:
            sg_tz = pytz.timezone('Asia/Singapore')
            now = datetime.now(sg_tz)
            
            # Parse date
            date_str = date_str.lower().strip()
            if date_str in ['today']:
                target_date = now.date()
            elif date_str in ['tomorrow']:
                target_date = (now + timedelta(days=1)).date()
            elif date_str in ['day after tomorrow', 'day after']:
                target_date = (now + timedelta(days=2)).date()
            else:
                # Try to parse date formats like "2024-01-15", "Jan 15", "15 Jan"
                try:
                    # Try ISO format first
                    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        # Try "Jan 15" format
                        target_date = datetime.strptime(f"{date_str} {now.year}", '%b %d %Y').date()
                    except ValueError:
                        try:
                            # Try "15 Jan" format
                            target_date = datetime.strptime(f"{date_str} {now.year}", '%d %b %Y').date()
                        except ValueError:
                            return None
            
            # Parse time
            time_str = time_str.lower().strip()
            # Handle various time formats with improved regex patterns
            time_patterns = [
                (r'(\d{1,2}):(\d{2})\s*(am|pm)', 'time_with_minutes_ampm'),  # 2:30 PM, 2:30pm
                (r'(\d{1,2})\s*(am|pm)', 'time_ampm'),                      # 2 PM, 2 pm
                (r'(\d{1,2})(am|pm)', 'time_ampm_no_space'),               # 2pm, 2am (no space)
                (r'(\d{1,2}):(\d{2})', 'time_24h_with_minutes'),          # 14:30
                (r'^(\d{1,2})$', 'time_24h_hour_only'),                   # 14 (hour only)
            ]
            
            target_time = None
            hour = 0
            minute = 0
            
            for pattern, pattern_type in time_patterns:
                match = re.search(pattern, time_str)
                if match:
                    if pattern_type == 'time_with_minutes_ampm':
                        # Format: 2:30 PM, 2:30pm
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        
                        # Validate 12-hour format values
                        if not (1 <= hour <= 12) or not (0 <= minute <= 59):
                            continue
                            
                        if 'pm' in time_str and hour != 12:
                            hour += 12
                        elif 'am' in time_str and hour == 12:
                            hour = 0
                            
                    elif pattern_type in ['time_ampm', 'time_ampm_no_space']:
                        # Format: 2 PM, 2 pm, 2pm, 2am
                        hour = int(match.group(1))
                        minute = 0
                        
                        # Validate 12-hour format values
                        if not (1 <= hour <= 12):
                            continue
                            
                        if 'pm' in time_str and hour != 12:
                            hour += 12
                        elif 'am' in time_str and hour == 12:
                            hour = 0
                            
                    elif pattern_type == 'time_24h_with_minutes':
                        # Format: 14:30
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        
                    elif pattern_type == 'time_24h_hour_only':
                        # Format: 14
                        hour = int(match.group(1))
                        minute = 0
                    
                    # Validate hour and minute values
                    if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                        continue
                    
                    target_time = datetime(2000, 1, 1, hour, minute).time()
                    break
            
            if not target_time:
                return None
            
            # Combine date and time
            appointment_datetime = sg_tz.localize(datetime.combine(target_date, target_time))
            
            # Check if appointment is in the future
            if appointment_datetime <= now:
                return None
            
            return appointment_datetime
            
        except Exception as e:
            logger.error(f"Error parsing appointment datetime: {e}")
            return None
    
    def _parse_combined_datetime(self, user_message: str) -> Optional[Dict[str, str]]:
        """Parse combined date-time inputs like 'wednesday 2pm', 'tomorrow at 3:30pm', etc."""
        try:
            import re
            from datetime import datetime, timedelta
            import pytz
            
            sg_tz = pytz.timezone('Asia/Singapore')
            now = datetime.now(sg_tz)
            
            # Common day patterns
            day_patterns = {
                r'\b(today)\b': 0,
                r'\b(tomorrow)\b': 1,
                r'\b(monday|mon)\b': None,
                r'\b(tuesday|tue)\b': None,
                r'\b(wednesday|wed)\b': None,
                r'\b(thursday|thu)\b': None,
                r'\b(friday|fri)\b': None,
                r'\b(saturday|sat)\b': None,
                r'\b(sunday|sun)\b': None,
                r'\b(next week)\b': 7,
                r'\b(next monday)\b': None,
                r'\b(next tuesday)\b': None,
                r'\b(next wednesday)\b': None,
                r'\b(next thursday)\b': None,
                r'\b(next friday)\b': None,
                r'\b(next saturday)\b': None,
                r'\b(next sunday)\b': None,
            }
            
            # Time patterns
            time_patterns = [
                r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b',  # 2:30 PM
                r'\b(\d{1,2})\s*(am|pm)\b',          # 2 PM
                r'\b(\d{1,2})(am|pm)\b',             # 2pm
                r'\b(\d{1,2}):(\d{2})\b',            # 14:30
                r'\b(morning)\b',                     # morning
                r'\b(afternoon)\b',                   # afternoon
                r'\b(evening)\b',                     # evening
            ]
            
            extracted_date = None
            extracted_time = None
            
            # Extract date
            for pattern, days_offset in day_patterns.items():
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    day_name = match.group(1).lower()
                    
                    if days_offset is not None:
                        # Fixed offset days (today, tomorrow, next week)
                        target_date = now + timedelta(days=days_offset)
                        extracted_date = target_date.strftime('%Y-%m-%d')
                    else:
                        # Weekday names - improved logic
                        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                        clean_day = day_name.replace('next ', '')
                        
                        if clean_day in weekdays:
                            target_weekday = weekdays.index(clean_day)
                            current_weekday = now.weekday()
                            days_ahead = target_weekday - current_weekday
                            
                            # If it's the same day or past, get next week's occurrence
                            # Also handle 'next' prefix explicitly
                            if days_ahead <= 0 or day_name.startswith('next '):
                                days_ahead += 7
                            
                            target_date = now + timedelta(days=days_ahead)
                            extracted_date = target_date.strftime('%Y-%m-%d')
                            logger.info(f"Parsed weekday '{day_name}' -> date: {extracted_date}")
                    break
            
            # Extract time - improved parsing
            for pattern in time_patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    if 'morning' in match.group(0).lower():
                        extracted_time = '9:00 AM'
                    elif 'afternoon' in match.group(0).lower():
                        extracted_time = '2:00 PM'
                    elif 'evening' in match.group(0).lower():
                        extracted_time = '6:00 PM'
                    else:
                        # Extract actual time with proper parsing
                        groups = match.groups()
                        
                        if len(groups) >= 3 and groups[2]:  # Has AM/PM with minutes
                            hour = int(groups[0])
                            minute = int(groups[1]) if groups[1] else 0
                            am_pm = groups[2].upper()
                            extracted_time = f"{hour}:{minute:02d} {am_pm}"
                        elif len(groups) >= 2 and groups[1] and groups[1].lower() in ['am', 'pm']:  # Has AM/PM without minutes
                            hour = int(groups[0])
                            am_pm = groups[1].upper()
                            extracted_time = f"{hour}:00 {am_pm}"
                        elif len(groups) >= 2 and groups[1] and groups[1].isdigit():  # 24-hour format
                            hour = int(groups[0])
                            minute = int(groups[1])
                            extracted_time = f"{hour:02d}:{minute:02d}"
                        else:
                            # Fallback: normalize the matched text
                            time_match = match.group(0)
                            if re.match(r'\d{1,2}(am|pm)', time_match, re.IGNORECASE):
                                time_match = re.sub(r'(\d)(am|pm)', r'\1 \2', time_match, flags=re.IGNORECASE)
                            extracted_time = time_match.upper()
                        
                        logger.info(f"Parsed time '{match.group(0)}' -> time: {extracted_time}")
                    break
            
            # Return extracted components if at least one is found
            if extracted_date or extracted_time:
                result = {}
                if extracted_date:
                    result['date'] = extracted_date
                if extracted_time:
                    result['time'] = extracted_time
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing combined datetime: {e}")
            return None
    
    def _get_service_options_message(self) -> Dict[str, Any]:
        """Generate service options message with clickable buttons for appointment booking"""
        return get_appointment_options_with_buttons()
    
    def _generate_datetime_request_message(self, service_type: str, appointment_date: Optional[str], appointment_time: Optional[str]) -> str:
        """Generate step-by-step date and time request message"""
        service_name = service_type.title() if service_type else "your service"
        
        if not appointment_date and not appointment_time:
            return f"📅 Perfect! You've selected {service_name}. ⏰ When would you like to schedule your appointment? Please provide date and time (e.g., 'Tomorrow at 2pm' or 'Next Monday morning')."
        elif appointment_date and not appointment_time:
            return f"📅 Great! I have your date as {appointment_date}. ⏰ What time would you prefer for your {service_name}? Time examples: '2pm', '10:30 AM', '14:00', 'morning', 'afternoon'. Just tell me your preferred time!"
        elif not appointment_date and appointment_time:
            return f"⏰ Perfect! I have your time as {appointment_time}. 📅 What date would you like for your {service_name}? Date examples: 'tomorrow', 'next Monday', 'December 15th', '2024-01-20'. Which date works best for you?"
        else:
            return f"📅 Excellent! I have {appointment_date} at {appointment_time} for your {service_name}. 👤 Now I need your contact information to complete the booking."
    
    def _generate_contact_request_message(self, customer_name: Optional[str], customer_phone: Optional[str]) -> str:
        """Generate step-by-step contact information request message"""
        if not customer_name and not customer_phone:
            return "👤 Almost done! I just need your contact information. Please provide your full name (e.g., 'John Smith'), phone number (e.g., '91234567', '+65 8765 4321'), and email address (optional). Example: My name is John Smith, phone 91234567, email john@email.com"
        elif customer_name and not customer_phone:
            return f"👤 Thank you, {customer_name}! 📱 I just need your phone number to complete the booking. Phone examples: '91234567', '+65 8765 4321', '9876-5432'. What's your phone number?"
        elif not customer_name and customer_phone:
            return f"📱 Great! I have your phone number as {customer_phone}. 👤 What's your full name for the appointment? Example: 'John Smith'. Please provide your name to complete the booking."
        else:
            return f"✅ Perfect! I have all your details: Name: {customer_name}, Phone: {customer_phone}. 📧 Would you like to provide an email address for confirmation? (Optional) You can provide your email or say 'no email' to proceed with the booking."
    
    def _generate_missing_info_message(self, missing_info: List[str]) -> str:
        """Generate beautified missing information message with examples"""
        info_text = ", ".join(missing_info)
        return f"📋 Almost there! I need a few more details to book your appointment: {info_text}. Please provide the missing information and I'll complete your booking!"
    
    def _generate_datetime_error_message(self) -> str:
        """Generate user-friendly datetime error message with examples"""
        return "❌ I couldn't understand the date and time format. Date examples: 'tomorrow', 'next Monday', 'December 15th', '2024-01-20'. Time examples: '2pm', '2:00 PM', '10:30 AM', '14:00', 'morning', 'afternoon'. Please try again with a clear date and time!"
    
    def _generate_slot_unavailable_message(self, appointment_datetime: datetime) -> str:
        """Generate user-friendly slot unavailable message with alternatives"""
        formatted_datetime = appointment_datetime.strftime('%B %d, %Y at %I:%M %p')
        
        # Generate alternative time suggestions
        alternative_times = []
        
        # Suggest same day different times
        for hour_offset in [1, 2, -1, -2]:
            alt_time = appointment_datetime + timedelta(hours=hour_offset)
            if alt_time.hour >= 9 and alt_time.hour <= 17:  # Business hours
                alternative_times.append(alt_time.strftime('%I:%M %p'))
        
        # Suggest next day same time
        next_day = appointment_datetime + timedelta(days=1)
        alternative_times.append(f"{next_day.strftime('%B %d')} at {appointment_datetime.strftime('%I:%M %p')}")
        
        alt_text = ", ".join(alternative_times[:3])
        return f"⚠️ Sorry, the slot on {formatted_datetime} is not available. Alternative times: {alt_text}. Please choose one of these times or suggest a different time that works for you!"
    
    def _is_slot_available(self, appointment_datetime: datetime) -> bool:
        """Check if the appointment slot is available"""
        try:
            with DatabaseContext('appointments') as collection:
                if not collection:
                    return True  # If database is not available, assume slot is available
                
                # Check for existing appointments within 30 minutes
                start_time = appointment_datetime - timedelta(minutes=30)
                end_time = appointment_datetime + timedelta(minutes=30)
                
                existing_appointment = collection.find_one({
                    "appointment_datetime": {
                        "$gte": start_time,
                        "$lte": end_time
                    },
                    "status": {"$in": ["confirmed", "pending"]}
                })
                
                return existing_appointment is None
                
        except Exception as e:
            logger.error(f"Error checking slot availability: {e}")
            return True  # If error, assume slot is available
    
    def _save_appointment(self, appointment_data: Dict[str, Any]) -> bool:
        """Save appointment to database"""
        try:
            with DatabaseContext('appointments') as collection:
                if not collection:
                    logger.warning("Database not available, cannot save appointment")
                    return False
                
                result = collection.insert_one(appointment_data)
                return result.inserted_id is not None
                
        except Exception as e:
            logger.error(f"Error saving appointment: {e}")
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
            # Get customer phone number to find appointments
            customer_phone = tracker.get_slot("customer_phone")
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
            now = datetime.utcnow()
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
                
                appointments = list(collection.find({
                    "customer_phone": customer_phone
                }).sort("appointment_datetime", -1))
                
                return appointments
                
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
                        email_data = {
                            'customer_name': cancelled_appointment.get('customer_name', 'Customer'),
                            'customer_email': cancelled_appointment['customer_email'],
                            'appointment_id': cancelled_appointment['appointment_id'],
                            'appointment_date': cancelled_appointment['appointment_datetime'].strftime('%B %d, %Y'),
                            'appointment_time': cancelled_appointment['appointment_datetime'].strftime('%I:%M %p'),
                            'service_type': cancelled_appointment['service_type']
                        }
                        
                        email_sent = send_appointment_cancellation_email(email_data)
                        if email_sent:
                            logger.info(f"Email cancellation notification sent for appointment {appointment_id[:8]}")
                        else:
                            logger.warning(f"Failed to send email cancellation notification for appointment {appointment_id[:8]}")
                    elif not cancelled_appointment or not cancelled_appointment.get('customer_email'):
                        logger.info("No email address available - skipping email cancellation notification")
                    else:
                        logger.info("Email service not enabled - skipping email cancellation notification")
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
                
                # Update the appointment status
                result = collection.update_one(
                    {
                        "appointment_id": appointment_id,
                        "customer_phone": customer_phone,
                        "status": {"$in": ["confirmed", "pending"]}
                    },
                    {
                        "$set": {
                            "status": "cancelled",
                            "cancelled_at": datetime.utcnow()
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