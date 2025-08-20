"""Optimized Appointment Booking RASA Actions
Handles appointment booking, viewing, and management for automotive services
Optimized with async processing, database connection pooling, and enhanced caching
"""

import os
import logging
import asyncio
from typing import Any, Text, Dict, List, Optional, Tuple, Union
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, ActiveLoop
from rasa_sdk.forms import FormValidationAction, REQUESTED_SLOT
from rasa_sdk.types import DomainDict
from .auto_logger import AutoLoggedAction
from api.config.database import DatabaseContext
from api.services.email_service import send_appointment_confirmation_email, send_appointment_cancellation_email, is_email_enabled
from api.utils.cache import appointment_cache, client_cache
from api.utils.database_pool import DatabasePool
from api.utils.enhanced_cache import get_cache, cache_result
from api.cache.feature_cache_manager import check_appointment_feature_enabled
from datetime import datetime, timedelta, time
import pytz
from bson import ObjectId
import re
from dateutil import parser
from dateutil.relativedelta import relativedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from dotenv import load_dotenv
from pathlib import Path
import json
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import our enhanced utilities
from ..utils.database_pool import get_database_pool
from ..middleware.intent_validation_middleware import validate_medium_confidence, validate_high_confidence

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

# Initialize global database pool instance
database_pool = get_database_pool()

# Async MongoDB connection helpers
async def get_mongo_collection(collection_name: str) -> Optional[AsyncIOMotorCollection]:
    """Get MongoDB collection using connection pool"""
    try:
        collection = await database_pool.get_collection(collection_name)
        if collection is None:
            logger.error(f"Failed to get collection: {collection_name}")
        return collection
    except Exception as e:
        logger.error(f"Error getting collection {collection_name}: {e}")
        return None

async def get_database_stats() -> Dict[str, Any]:
    """Get database connection statistics"""
    return database_pool.get_connection_stats()

# MongoDB connection helper with connection pooling
async def get_mongodb_client():
    """Get MongoDB client connection using connection pool"""
    try:
        db = await database_pool.get_database()
        if not db:
            logger.error("Failed to get database from connection pool")
            return None
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None

@cache_result(ttl=300, key_prefix="client_data")
async def get_client_data_from_db_by_phone(phone_number: str) -> Optional[Dict[str, Any]]:
    """Retrieve client data from database with caching"""
    try:
        customers_collection = await get_mongo_collection('customers')
        if not customers_collection:
            return None
        
        # Find customer by phone number
        customer = await customers_collection.find_one({"phone": phone_number})
        
        if customer:
            # Convert ObjectId to string for JSON serialization
            customer['_id'] = str(customer['_id'])
            logger.debug(f"Retrieved client data for phone: {phone_number}")
        
        return customer
    except Exception as e:
        logger.error(f"Error retrieving client data: {e}")
        return None

async def get_client_data_from_db(client_id: str):
    """Retrieve client data directly from MongoDB with caching"""
    cache_key = f"client_data:{client_id}"
    
    async def fetch_client_data():
        try:
            db = await get_mongodb_client()
            if not db:
                return None

            collection = db.clients
            # Get client data - try both string ID and ObjectId
            client = await collection.find_one({"_id": client_id})
            if not client:
                # Try with ObjectId if string search fails
                try:
                    client = await collection.find_one({"_id": ObjectId(client_id)})
                except Exception:
                    pass
            
            return client
            
        except Exception as e:
            logger.error(f"Error retrieving client data from MongoDB: {e}")
            return None
    
    # Use enhanced cache with 5-minute TTL
    cache = get_cache()
    return await cache.get_or_set(cache_key, fetch_client_data, ttl=300)

@cache_result(ttl=600, key_prefix="appointment_types")
async def get_appointment_types_from_db() -> List[Dict[str, Any]]:
    """Get available appointment types from database with caching"""
    try:
        appointment_types_collection = await get_mongo_collection('appointment_types')
        if not appointment_types_collection:
            return []
    

        
        # Get all active appointment types
        cursor = appointment_types_collection.find({"active": True})
        appointment_types = await cursor.to_list(length=None)
        
        # Convert ObjectIds to strings
        for apt_type in appointment_types:
            apt_type['_id'] = str(apt_type['_id'])
        
        logger.debug(f"Retrieved {len(appointment_types)} appointment types")
        return appointment_types
    except Exception as e:
        logger.error(f"Error retrieving appointment types: {e}")
        return []

@cache_result(ttl=300, key_prefix="appointment_types")
async def get_appointment_types():
    """Get available appointment types with enhanced caching"""
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
    
    return types

async def get_appointment_type_by_id(type_id: str):
    """Get appointment type by ID with caching"""
    types = await get_appointment_types()
    for apt_type in types:
        if apt_type["id"] == type_id:
            return apt_type
    return None

async def get_appointment_options_message():
    """Generate formatted appointment options message with caching"""
    types = await get_appointment_types()
    message = "🚗 Select Your Appointment Type - Choose from our available services: "

    for apt_type in types:
        # Add icon and description if available, otherwise use basic format
        icon = apt_type.get('icon', '🔧')
        description = apt_type.get('description', f"Duration: {apt_type['duration']} minutes")
        message += f"{icon} {apt_type['name']} - {description}, "

    message = message.rstrip(', ') + ". Simply type the service you need (e.g., 'test drive', 'sales consultation', 'trade-in evaluation')."
    return message

async def get_appointment_options_with_buttons():
    """Generate appointment options with clickable buttons and explanatory text"""
    types = await get_appointment_types()

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

class AsyncActionViewAppointments(AutoLoggedAction):
    """Optimized async version of ActionViewAppointments
    
    Features:
    - Async database operations with connection pooling
    - Enhanced caching for improved performance
    - Optimized query patterns
    - Better error handling and logging
    - Intent validation middleware integration
    """

    def name(self) -> Text:
        return "action_view_appointments"

    @validate_medium_confidence(confidence_threshold=0.6)
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Log user message and action execution
        self.log_user_message(tracker)
        self.log_action_execution("AsyncActionViewAppointments", tracker)
        
        try:
            # Check if appointment booking feature is enabled for this client
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            if client_id:
                if not check_appointment_feature_enabled(client_id):
                    response_message = "I'm sorry, but appointment viewing is currently not available. Please contact our support team for assistance."
                    dispatcher.utter_message(text=response_message)
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
                # Single response with auto-fill functionality using json_message (consistent with cancel appointment)
                response_message = "📱 **Let me help you check your appointments!**\n\nTo view your booking history and upcoming appointments, I'll need your phone number. Please provide the number you used when making your bookings."
                dispatcher.utter_message(
                    text=response_message,
                    json_message={
                        "autofill": "view appointments for "
                    }
                )
                return []
            
            appointments = await self._get_customer_appointments_async(customer_phone)
            
            if not appointments:
                response_message = "🔍 **No Appointments Found**\n\nI couldn't find any appointments linked to this phone number in our system.\n\n💡 **Possible reasons:**\n• Different phone number was used for booking\n• Appointments were made under a different contact\n• No appointments have been scheduled yet\n\n🚗 **Ready to get started?** I'd be happy to help you book your first appointment! Just let me know what service you need."
                dispatcher.utter_message(text=response_message)
                return []
            
            # Separate upcoming and past appointments
            # Use Singapore timezone to match how appointments are stored
            sg_tz = pytz.timezone('Asia/Singapore')
            now = datetime.now(sg_tz)
            upcoming = [apt for apt in appointments if apt['appointment_datetime'] > now]
            past = [apt for apt in appointments if apt['appointment_datetime'] <= now]
            
            message = await self._format_appointments_message_async(upcoming, past)
            dispatcher.utter_message(text=message)
            
            # Log bot response
            self.log_bot_response(dispatcher, tracker, "AsyncActionViewAppointments")
            
            return []
            
        except Exception as e:
            logger.error(f"Error in AsyncActionViewAppointments: {e}")
            fallback_message = "Sorry, there was an error retrieving your appointments. Please try again."
            dispatcher.utter_message(text=fallback_message)
            
            # Log action execution failure and bot response
            self.log_action_execution("AsyncActionViewAppointments", tracker, success=False, error_message=str(e))
            self.log_bot_response(dispatcher, tracker, "AsyncActionViewAppointments")
            
            return []

    async def _get_customer_appointments_async(self, customer_phone: str) -> List[Dict[str, Any]]:
        """Get all appointments for a customer with enhanced caching"""
        cache_key = f"customer_appointments:{customer_phone}"
        
        async def fetch_appointments():
            try:
                db = await get_mongodb_client()
                if not db:
                    return []
                
                collection = db.appointments
                
                # Get appointments and sort by appointment_date, then appointment_time
                cursor = collection.find({
                    "customer_phone": customer_phone
                }).sort("appointment_date", -1)
                
                appointments = await cursor.to_list(length=None)
                
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
        
        # Cache for 2 minutes (shorter TTL for appointment data)
        cache = get_cache()
        return await cache.get_or_set(cache_key, fetch_appointments, ttl=120)

    async def _format_appointments_message_async(self, upcoming: List[Dict], past: List[Dict]) -> str:
        """Format appointments into a readable message"""
        message_parts = []
        
        # Add header message
        total_appointments = len(upcoming) + len(past)
        message_parts.append(f"🗓️ **Your Appointment Dashboard**\n\nFound {total_appointments} appointment{'s' if total_appointments != 1 else ''} in your booking history\n")

        if upcoming:
            message_parts.append("\n📅 **Upcoming Appointments:**\n")
            
            for apt in upcoming:
                formatted_date = apt['appointment_datetime'].strftime('%B %d, %Y')
                formatted_time = apt['appointment_datetime'].strftime('%I:%M %p')
                
                message_parts.append(f"\n• **ID:** {apt['appointment_id'][:8]}\n")
                message_parts.append(f"  **Date:** {formatted_date}\n")
                message_parts.append(f"  **Time:** {formatted_time}\n")
                message_parts.append(f"  **Service:** {apt['service_type']}\n")
                message_parts.append(f"  **Status:** {apt['status'].title()}\n")
        
        if past:
            message_parts.append("\n📋 **Past Appointments:**\n")
            
            for apt in past[:3]:  # Show only last 3 past appointments
                formatted_date = apt['appointment_datetime'].strftime('%B %d, %Y')
                formatted_time = apt['appointment_datetime'].strftime('%I:%M %p')
                
                message_parts.append(f"\n• **ID:** {apt['appointment_id'][:8]}\n")
                message_parts.append(f"  **Date:** {formatted_date}\n")
                message_parts.append(f"  **Time:** {formatted_time}\n")
                message_parts.append(f"  **Service:** {apt['service_type']}\n")
                message_parts.append(f"  **Status:** {apt['status'].title()}\n")

            if len(past) > 3:
                message_parts.append(f"\n... and {len(past) - 3} more past appointments\n")
        
        if not upcoming and not past:
            return "No appointments found."
        
        return "".join(message_parts)

class AsyncActionCancelAppointment(AutoLoggedAction):
    """Optimized async version of ActionCancelAppointment
    
    Features:
    - Async database operations with connection pooling
    - Enhanced caching for improved performance
    - Optimized query patterns
    - Better error handling and logging
    - Intent validation middleware integration
    """

    def name(self) -> Text:
        return "action_cancel_appointment"

    @validate_high_confidence(confidence_threshold=0.7)
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Log user message and action execution
        self.log_user_message(tracker)
        self.log_action_execution("AsyncActionCancelAppointment", tracker)
        
        try:
            # Check if appointment booking feature is enabled for this client
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            
            # If no client_id, use default 'test_client' for testing or fallback
            if not client_id:
                client_id = 'test_client'
            
            if not check_appointment_feature_enabled(client_id):
                response_message = "I'm sorry, but appointment management is currently not available. Please contact our support team for assistance."
                dispatcher.utter_message(text=response_message)
                return []
            
            customer_phone = tracker.get_slot("customer_phone")
            
            if not customer_phone:
                # Try to extract from latest message
                latest_message = tracker.latest_message.get('text', '')
                phone_match = re.search(r'\b\d{8,}\b', latest_message)
                if phone_match:
                    customer_phone = phone_match.group()
                else:
                    # Auto-fill phone number in input box directly
                    response_message = "📱 I'd be happy to help you cancel your appointment! For security purposes, I'll need to verify your phone number before proceeding."
                    dispatcher.utter_message(
                        text=response_message,
                        json_message={
                            "autofill": "cancel appointment for "
                        }
                    )
                    return []
            
            success, cancelled_appointment = await self._cancel_appointment_async(customer_phone)
            
            if success:
                # Format appointment details for confirmation
                apt_time = cancelled_appointment.get('appointment_datetime')
                if isinstance(apt_time, str):
                    apt_time = datetime.fromisoformat(apt_time.replace('Z', '+00:00'))
                formatted_time = apt_time.strftime('%B %d, %Y at %I:%M %p') if apt_time else 'Unknown time'
                service_type = cancelled_appointment.get('service_type', 'Unknown service')
                
                success_message = f"✅ **Appointment Cancelled Successfully!** Your {service_type} appointment on {formatted_time} has been cancelled. Need to reschedule or book a different service? Just let me know! 😊"
                dispatcher.utter_message(text=success_message)
                
                # Log bot response
                self.log_bot_response(dispatcher, tracker, "AsyncActionCancelAppointment")
                
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
                    
                # Clear cache for this customer's appointments
                cache = get_cache()
                await cache.delete(f"customer_appointments:{customer_phone}")
                
            else:
                not_found_message = "🔍 **No Appointment Found** - Sorry, I couldn't find any active appointment records for your phone number. The appointment may have already been cancelled or the phone number might not match. I can help you view all your appointment records! 📋"
                dispatcher.utter_message(text=not_found_message)
                
                # Log bot response
                self.log_bot_response(dispatcher, tracker, "AsyncActionCancelAppointment")
            
            return [SlotSet("appointment_id", None)]
            
        except Exception as e:
            logger.error(f"Error in AsyncActionCancelAppointment: {e}")
            fallback_message = "Sorry, there was an error cancelling your appointment. Please try again or contact us directly."
            dispatcher.utter_message(text=fallback_message)
            
            # Log action execution failure and bot response
            self.log_action_execution("AsyncActionCancelAppointment", tracker, success=False, error_message=str(e))
            self.log_bot_response(dispatcher, tracker, "AsyncActionCancelAppointment")
            
            return []

    async def _cancel_appointment_async(self, customer_phone: str) -> Tuple[bool, Optional[Dict]]:
        """Cancel the most recent active appointment for the customer"""
        try:
            db = await get_mongodb_client()
            if not db:
                return False, None
            
            collection = db.appointments
            
            # Find the most recent active appointment for this customer
            appointment = await collection.find_one(
                {
                    "customer_phone": customer_phone,
                    "status": {"$in": ["confirmed", "pending"]}
                },
                sort=[("appointment_datetime", -1)]  # Get the most recent appointment
            )
            
            if not appointment:
                return False, None
            
            # Update the appointment status with timestamp
            current_time = datetime.now(pytz.timezone('Asia/Singapore'))
            result = await collection.update_one(
                {
                    "_id": appointment["_id"],
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

class ActionViewAppointments(AutoLoggedAction):
    """Action to view customer appointments"""
    
    def name(self) -> Text:
        return "action_view_appointments"
    
    @validate_medium_confidence(confidence_threshold=0.6)
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Log user message and action execution
        self.log_user_message(tracker)
        self.log_action_execution("ActionViewAppointments", tracker)
        
        try:
            # Check if appointment feature is enabled
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            
            # If no client_id, use default 'test_client' for testing or fallback
            if not client_id:
                client_id = 'test_client'
            
            if not check_appointment_feature_enabled(client_id):
                response_message = "Sorry, appointment functionality is currently unavailable. Please try again later."
                dispatcher.utter_message(text=response_message)
                # Log bot response
                self.log_bot_response(dispatcher, tracker, "ActionViewAppointments")
                return []
            
            # Get customer phone number from slot or latest message
            phone_number = tracker.get_slot("phone_number")
            
            if not phone_number:
                # Try to extract from latest message
                latest_message = tracker.latest_message.get('text', '')
                phone_match = re.search(r'\b\d{8,}\b', latest_message)
                if phone_match:
                    phone_number = phone_match.group()
                else:
                    # Auto-fill phone number in input box directly - SINGLE RESPONSE
                    response_message = "Please provide your phone number to view your appointment information."
                    dispatcher.utter_message(
                        text=response_message,
                        json_message={
                            "autofill": "view appointments for "
                        }
                    )
                    # Log bot response
                    self.log_bot_response(dispatcher, tracker, "ActionViewAppointments")
                    return [SlotSet("requested_slot", "phone_number")]
            
            # Get customer appointments
            appointments = await self._get_customer_appointments(phone_number)
            
            if not appointments:
                response_message = "You currently have no appointment records."
                dispatcher.utter_message(text=response_message)
                # Log bot response
                self.log_bot_response(dispatcher, tracker, "ActionViewAppointments")
                return []
            
            # Separate upcoming and past appointments
            now = datetime.now(pytz.timezone('Asia/Singapore'))
            upcoming_appointments = []
            past_appointments = []
            
            for appointment in appointments:
                appointment_datetime = appointment.get('appointment_datetime')
                if isinstance(appointment_datetime, str):
                    appointment_datetime = datetime.fromisoformat(appointment_datetime.replace('Z', '+00:00'))
                
                if appointment_datetime > now:
                    upcoming_appointments.append(appointment)
                else:
                    past_appointments.append(appointment)
            
            # Format and send message
            message_parts = []
            
            if upcoming_appointments:
                message_parts.append("📅 **Upcoming Appointments:**")
                for apt in upcoming_appointments:
                    apt_time = apt['appointment_datetime']
                    if isinstance(apt_time, str):
                        apt_time = datetime.fromisoformat(apt_time.replace('Z', '+00:00'))
                    
                    formatted_time = apt_time.strftime('%B %d, %Y at %I:%M %p')
                    message_parts.append(
                        f"• {apt.get('service_type', 'Unknown Service')} - {formatted_time}\n"
                        f"  Status: {apt.get('status', 'Unknown').title()}\n"
                        f"  Appointment ID: {apt.get('_id', 'N/A')}"
                    )
            
            if past_appointments:
                message_parts.append("\n📋 **Past Appointments:**")
                for apt in past_appointments[-3:]:  # Show last 3 past appointments
                    apt_time = apt['appointment_datetime']
                    if isinstance(apt_time, str):
                        apt_time = datetime.fromisoformat(apt_time.replace('Z', '+00:00'))
                    
                    formatted_time = apt_time.strftime('%B %d, %Y at %I:%M %p')
                    message_parts.append(
                        f"• {apt.get('service_type', 'Unknown Service')} - {formatted_time}\n"
                        f"  Status: {apt.get('status', 'Unknown').title()}"
                    )
            
            # FIXED: Single unified response instead of multiple parts
            final_message = " ".join(message_parts)
            dispatcher.utter_message(text=final_message)
            
            # Log bot response
            self.log_bot_response(dispatcher, tracker, "ActionViewAppointments")
            
            return [SlotSet("phone_number", phone_number)]
            
        except Exception as e:
            logger.error(f"Error in ActionViewAppointments: {e}")
            dispatcher.utter_message(text="Sorry, there was an error viewing appointments. Please try again later.")
            return []
    
    async def _get_customer_appointments(self, phone_number: str) -> List[Dict[str, Any]]:
        """Get customer appointments from database using async connection"""
        try:
            db = await get_mongodb_client()
            if not db:
                return []
            
            appointments_collection = db.appointments
            
            # Find appointments by phone number
            cursor = appointments_collection.find(
                {"customer_phone": phone_number}
            ).sort("appointment_datetime", -1)
            
            appointments = await cursor.to_list(length=None)
            
            # Convert ObjectId to string for JSON serialization
            for appointment in appointments:
                if '_id' in appointment:
                    appointment['_id'] = str(appointment['_id'])
            
            return appointments
            
        except Exception as e:
            logger.error(f"Error retrieving customer appointments: {e}")
            return []



class ActionValidateIntent(Action):
    """Action to validate user intent for appointment booking"""
    
    def name(self) -> Text:
        return "action_validate_intent"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get the latest user message
            latest_message = tracker.latest_message.get('text', '').lower()
            
            # Check if the message contains appointment-related keywords
            appointment_keywords = [
                'appointment', 'book', 'schedule', 'reserve', 'meeting',
                'test drive', 'consultation', 'service', 'visit'
            ]
            
            intent_detected = any(keyword in latest_message for keyword in appointment_keywords)
            
            if intent_detected:
                # Don't send message here - let action_book_appointment handle it
                return [FollowupAction("action_book_appointment")]
            else:
                # Don't send generic response - let other actions handle it
                return []
                
        except Exception as e:
            logger.error(f"Error in ActionValidateIntent: {e}")
            # Single error response
            dispatcher.utter_message(
                text="Sorry, there was an error processing your request. Please try again."
            )
            return []

class ActionBookAppointment(Action):
    """Action to handle appointment booking"""
    
    def name(self) -> Text:
        return "action_book_appointment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Check if appointment feature is enabled
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            
            # If no client_id, use default 'test_client' for testing or fallback
            if not client_id:
                client_id = 'test_client'
            
            # Check if appointment feature is enabled for this client
            if not check_appointment_feature_enabled(client_id):
                # FIXED: Single response for feature disabled
                dispatcher.utter_message(
                    text="Sorry, appointment booking is currently not available. Please try again later."
                )
                return []
            
            # Check if service_type is already provided from entities or previous interaction
            service_type = None
            
            # First check entities from the current message
            entities = tracker.latest_message.get('entities', [])
            for entity in entities:
                if entity.get('entity') == 'service_type':
                    service_type = entity.get('value')
                    break
            
            # If no entity found, check the message text for service type
            if not service_type:
                user_text = tracker.latest_message.get('text', '').lower()
                service_mappings = {
                    'test drive': 'Test Drive',
                    'sales consultation': 'Sales Consultation',
                    'trade-in evaluation': 'Trade-in Evaluation',
                    'trade in evaluation': 'Trade-in Evaluation'
                }
                
                for key, value in service_mappings.items():
                    if key in user_text:
                        service_type = value
                        break
            
            # If service type is found, set it and activate the form
            if service_type:
                logger.info(f"Service type detected: {service_type}")
                return [
                    SlotSet("service_type", service_type),
                    FollowupAction("appointment_form")
                ]
            
            # If no service type detected, show options with buttons - SINGLE RESPONSE
            try:
                # Use synchronous version with buttons to avoid event loop conflicts
                appointment_options = self._get_appointment_options_with_buttons_sync()
                
                # FIXED: Send single unified message with buttons
                dispatcher.utter_message(
                    text=appointment_options["text"],
                    buttons=appointment_options["buttons"]
                )
                # Don't activate form yet - wait for user selection
                return []
            except Exception as e:
                logger.error(f"Error getting appointment options: {e}")
                # FIXED: Fallback to basic sync version if buttons fail - single response
                appointment_options = self._get_appointment_options_sync()
                dispatcher.utter_message(text=appointment_options)
                return []
                
        except Exception as e:
            logger.error(f"Error in ActionBookAppointment: {e}")
            # FIXED: Single response for error
            response_message = "Sorry, there was an error with appointment booking. Please try again."
            dispatcher.utter_message(text=response_message)
            return []
    
    def _get_appointment_options_with_buttons_sync(self) -> Dict[str, Any]:
        """Get appointment options with buttons synchronously"""
        try:
            # Use hardcoded appointment types to ensure consistency
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
                    "description": "Get your current vehicle evaluated for trade-in value"
                }
            ]
            
            # Generate buttons for each appointment type
            buttons = []
            for apt_type in types:
                icon = apt_type.get('icon', '🔧')
                buttons.append({
                    "title": f"{icon} {apt_type['name']}",
                    "payload": apt_type['name']
                })
            
            return {
                "text": "🚗 Welcome to our appointment booking system! 📋 Please select the type of service you'd like to book:",
                "buttons": buttons
            }
            
        except Exception as e:
            logger.error(f"Error in _get_appointment_options_with_buttons_sync: {e}")
            # Fallback to basic text format
            return {
                "text": "🚗 Welcome! I can help you book an appointment. Please let me know what type of service you need.",
                "buttons": []
            }
    
    def _get_appointment_options_sync(self) -> str:
        """Get appointment options synchronously"""
        try:
            from ..config.database import get_collection
            
            # Get appointment types from database
            collection = get_collection('appointment_types')
            if not collection:
                return "🚗 Welcome! I can help you book an appointment. Please let me know what type of service you need."
            
            types = list(collection.find({}))
            
            if not types:
                return "🚗 Welcome! I can help you book an appointment. Please let me know what type of service you need."
            
            # Format appointment options
            message_parts = ["🚗 Welcome to our appointment booking system! 📋 Please select the type of service you'd like to book:"]
            message_parts.append("")
            
            for i, apt_type in enumerate(types, 1):
                icon = apt_type.get('icon', '🔧')
                name = apt_type.get('name', 'Service')
                description = apt_type.get('description', 'Professional service')
                duration = apt_type.get('duration', 60)
                
                message_parts.append(f"{i}. {icon} **{name}**")
                message_parts.append(f"   {description}")
                message_parts.append(f"   Duration: {duration} minutes")
                message_parts.append("")
            
            message_parts.append("💡 Simply type the service name or number to continue!")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error in _get_appointment_options_sync: {e}")
            return "🚗 Welcome! I can help you book an appointment. Please let me know what type of service you need."

class AppointmentForm(FormValidationAction):
    """Form validation action to collect appointment details"""
    
    def name(self) -> Text:
        return "appointment_form"
    
    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""
        return ["service_type", "customer_name", "customer_phone", "appointment_date", "appointment_time"]
    
    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        return {
            "service_type": [
                self.from_entity(entity="service_type"),
                self.from_text(intent="inform"),
                self.from_text(intent="provide_appointment_details")
            ],
            "customer_name": [
                self.from_entity(entity="customer_name"),
                self.from_text(intent="inform"),
                self.from_text(intent="nlu_fallback"),
                self.from_text(intent="provide_appointment_details")
            ],
            "customer_phone": [
                self.from_entity(entity="customer_phone"),
                self.from_text(intent="inform"),
                self.from_text(intent="nlu_fallback"),
                self.from_text(intent="provide_appointment_details")
            ],
            "appointment_date": [
                self.from_entity(entity="appointment_date"),
                self.from_text(intent="inform"),
                self.from_text(intent="provide_appointment_details")
            ],
            "appointment_time": [
                self.from_entity(entity="appointment_time"),
                self.from_text(intent="inform"),
                self.from_text(intent="nlu_fallback"),
                self.from_text(intent="provide_appointment_details")
            ]
        }

    def validate_service_type(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        """Validate service_type value."""
        service_type = tracker.get_slot('service_type')
        if service_type:
            # Normalize service type
            service_type_lower = service_type.lower()
            valid_services = {
                'test drive': 'Test Drive',
                'sales consultation': 'Sales Consultation', 
                'trade-in evaluation': 'Trade-in Evaluation',
                'trade in evaluation': 'Trade-in Evaluation'
            }
            
            for key, value in valid_services.items():
                if key in service_type_lower:
                    return {"service_type": value}
            
            # If not found in predefined list, use the original value
            return {"service_type": service_type}
        else:
            # Don't send message here - let the form handle it
            return {"service_type": None}
    
    def validate_customer_name(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        """Validate customer_name value."""
        customer_name = tracker.get_slot('customer_name')
        if customer_name and len(customer_name.strip()) >= 2:
            return {"customer_name": customer_name.strip()}
        else:
            # Don't send message here - let the form handle it
            return {"customer_name": None}
    
    def validate_customer_phone(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        """Validate customer_phone value."""
        import re
        customer_phone = tracker.get_slot('customer_phone')
        if customer_phone:
            # Remove all non-digit characters
            phone_digits = re.sub(r'\D', '', customer_phone)
            # Check if it's a valid Singapore phone number
            if len(phone_digits) == 8 and phone_digits.startswith(('8', '9')):
                return {"customer_phone": phone_digits}
            elif len(phone_digits) == 10 and phone_digits.startswith('65'):
                return {"customer_phone": phone_digits[2:]}
            else:
                # Don't send message here - let the form handle it
                return {"customer_phone": None}
        else:
            # Don't send message here - let the form handle it
            return {"customer_phone": None}
    
    def validate_appointment_date(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        """Validate appointment_date value with natural language processing."""
        from datetime import datetime, timedelta
        import re
        
        appointment_date = tracker.get_slot('appointment_date')
        if not appointment_date:
            return {"appointment_date": None}
        
        date_input = appointment_date.lower().strip()
        today = datetime.now().date()
        
        # Handle relative date expressions
        if '今天' in date_input or 'today' in date_input:
            formatted_date = today.strftime('%Y-%m-%d')
            return {"appointment_date": formatted_date}
        elif '明天' in date_input or 'tomorrow' in date_input:
            tomorrow = today + timedelta(days=1)
            formatted_date = tomorrow.strftime('%Y-%m-%d')
            return {"appointment_date": formatted_date}
        elif '后天' in date_input or 'day after tomorrow' in date_input:
            day_after = today + timedelta(days=2)
            formatted_date = day_after.strftime('%Y-%m-%d')
            return {"appointment_date": formatted_date}
        elif '下周' in date_input or 'next week' in date_input:
            next_week = today + timedelta(days=7)
            formatted_date = next_week.strftime('%Y-%m-%d')
            return {"appointment_date": formatted_date}
        
        # Handle specific date formats
        date_patterns = [
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # MM-DD-YYYY or MM/DD/YYYY
            r'(\d{1,2})月(\d{1,2})日',  # Chinese format: X月Y日
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_input)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        if '月' in pattern:  # Chinese format
                            month, day = int(groups[0]), int(groups[1])
                            year = today.year
                            parsed_date = datetime(year, month, day).date()
                        elif pattern.startswith(r'(\d{4})'):
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                            parsed_date = datetime(year, month, day).date()
                        else:
                            month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                            parsed_date = datetime(year, month, day).date()
                        
                        # Validate date is not in the past
                        if parsed_date >= today:
                            formatted_date = parsed_date.strftime('%Y-%m-%d')
                            return {"appointment_date": formatted_date}
                        else:
                            dispatcher.utter_message(text="Please choose a date that is today or in the future.")
                            return {"appointment_date": None}
                except ValueError:
                    continue
        
        # If no pattern matches, return the original value (might be already formatted)
        return {"appointment_date": appointment_date}
    
    def validate_appointment_time(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        """Validate appointment_time value with proper time format handling."""
        import re
        from datetime import datetime
        
        appointment_time = tracker.get_slot('appointment_time')
        
        if not appointment_time:
            # Don't send message here - let the form handle it
            return {"appointment_time": None}
        
        # Normalize the input
        time_input = appointment_time.lower().strip()
        
        # Define time patterns and their corresponding 24-hour formats
        time_patterns = [
            # 12-hour format with am/pm (e.g., "2pm", "2:30 PM", "2 pm")
            (r'^(\d{1,2})\s*:?\s*(\d{0,2})\s*(am|pm)$', self._convert_12_to_24),
            # 24-hour format (e.g., "14:00", "14:30")
            (r'^(\d{1,2})\s*:?\s*(\d{2})$', self._convert_24_hour),
            # Simple hour format (e.g., "2", "14")
            (r'^(\d{1,2})$', self._convert_simple_hour),
            # O'clock format (e.g., "2 o'clock", "2o'clock")
            (r'^(\d{1,2})\s*o\'?clock$', self._convert_oclock),
            # Common time expressions
            (r'^(morning|afternoon|evening)$', self._convert_time_period)
        ]
        
        # Try to match and convert time
        for pattern, converter in time_patterns:
            match = re.match(pattern, time_input)
            if match:
                try:
                    groups = match.groups()
                    converted_time = converter(*groups)
                    
                    # Validate the converted time
                    if self._is_valid_business_time(converted_time):
                        # Convert back to user-friendly format
                        formatted_time = self._format_display_time(converted_time)
                        return {"appointment_time": formatted_time}
                    else:
                        dispatcher.utter_message(text=f"Sorry, {converted_time} is outside our business hours (9:00 AM - 6:00 PM). Please choose a time between 9 AM and 6 PM.")
                        return {"appointment_time": None}
                except (ValueError, KeyError) as e:
                    logger.error(f"Error converting time '{time_input}': {e}")
                    continue
        
        # If no pattern matches, ask for clarification
        dispatcher.utter_message(text=f"I couldn't understand the time '{appointment_time}'. Please provide a time like '2pm', '14:00', '2:30 PM', or 'afternoon'.")
        return {"appointment_time": None}
    
    def _convert_12_to_24(self, hour, minute, period):
        """Convert 12-hour format to 24-hour format."""
        hour = int(hour)
        minute = minute or '00'
        minute = minute.zfill(2)  # Ensure 2 digits
        
        if period.lower() == 'am':
            if hour == 12:
                hour = 0
        else:  # pm
            if hour != 12:
                hour += 12
        
        return f"{hour:02d}:{minute}"
    
    def _convert_24_hour(self, hour, minute, *args):
        """Validate and format 24-hour time."""
        hour = int(hour)
        minute = int(minute)
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"
        else:
            raise ValueError("Invalid 24-hour time format")
    
    def _convert_simple_hour(self, hour, *args):
        """Convert simple hour to appropriate time (assume PM for business hours)."""
        hour = int(hour)
        
        # For business context, assume PM for hours 1-6, AM for hours 7-12
        if 1 <= hour <= 6:
            return f"{hour + 12:02d}:00"  # Convert to PM
        elif 7 <= hour <= 12:
            if hour == 12:
                return "12:00"  # 12 PM
            else:
                return f"{hour:02d}:00"  # AM hours
        else:
            raise ValueError("Invalid hour range")
    
    def _convert_oclock(self, hour, *args):
        """Convert o'clock format."""
        hour = int(hour)
        
        # Same logic as simple hour
        if 1 <= hour <= 6:
            return f"{hour + 12:02d}:00"  # Convert to PM
        elif 7 <= hour <= 12:
            if hour == 12:
                return "12:00"  # 12 PM
            else:
                return f"{hour:02d}:00"  # AM hours
        else:
            raise ValueError("Invalid hour range")
    
    def _convert_time_period(self, period, *args):
        """Convert time period to specific time."""
        period_map = {
            'morning': '09:00',
            'afternoon': '14:00', 
            'evening': '18:00'
        }
        return period_map.get(period.lower(), '14:00')
    
    def _is_valid_business_time(self, time_str):
        """Check if time is within business hours (9 AM - 6 PM)."""
        try:
            hour, minute = map(int, time_str.split(':'))
            # Business hours: 9:00 AM (09:00) to 6:00 PM (18:00)
            return 9 <= hour <= 18 and 0 <= minute <= 59
        except:
            return False
    
    def _format_display_time(self, time_24):
        """Convert 24-hour format to user-friendly 12-hour format."""
        try:
            hour, minute = map(int, time_24.split(':'))
            if hour == 0:
                return f"12:{minute:02d} AM"
            elif hour < 12:
                return f"{hour}:{minute:02d} AM"
            elif hour == 12:
                return f"12:{minute:02d} PM"
            else:
                return f"{hour-12}:{minute:02d} PM"
        except:
            return time_24
    

    
    def submit(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Define what the form has to do after all required slots are filled"""
        
        from rasa_sdk.events import SlotSet, ActiveLoop
        
        # 直接在submit方法中处理提交逻辑
        # Get all the collected information
        service_type = tracker.get_slot('service_type')
        customer_name = tracker.get_slot('customer_name')
        customer_phone = tracker.get_slot('customer_phone')
        appointment_date = tracker.get_slot('appointment_date')
        appointment_time = tracker.get_slot('appointment_time')
        
        logger.info(f"Submit method called with slots: service_type={service_type}, customer_name={customer_name}, customer_phone={customer_phone}, appointment_date={appointment_date}, appointment_time={appointment_time}")
        
        # Validate all required slots are filled
        if not all([service_type, customer_name, customer_phone, appointment_date, appointment_time]):
            dispatcher.utter_message(text="Sorry, some appointment information is missing. Please try booking again.")
            return []
        
        # Create appointment confirmation message
        confirmation_message = f"🎉 **Appointment Confirmed!** Your {service_type} appointment for {customer_name} on {appointment_date} at {appointment_time} has been booked successfully! 📱 You'll receive a confirmation message shortly."
        
        dispatcher.utter_message(text=confirmation_message)
        
        # Save appointment to database
        try:
            from ..config.database import get_collection
            import uuid
            from datetime import datetime
            
            collection = get_collection('appointments')
            if collection:
                appointment_data = {
                    'appointment_id': f"APT-{str(uuid.uuid4())[:8].upper()}",
                    'service_type': service_type,
                    'customer_name': customer_name,
                    'customer_phone': customer_phone,
                    'appointment_date': appointment_date,
                    'appointment_time': appointment_time,
                    'status': 'confirmed',
                    'created_at': datetime.utcnow(),
                    'conversation_id': tracker.sender_id
                }
                
                collection.insert_one(appointment_data)
                logger.info(f"Appointment saved successfully: {appointment_data['appointment_id']}")
        except Exception as e:
            logger.error(f"Error saving appointment: {e}")
        
        # Clear the form slots and deactivate the form
        return [
            SlotSet("service_type", None),
            SlotSet("customer_name", None), 
            SlotSet("customer_phone", None),
            SlotSet("appointment_date", None),
            SlotSet("appointment_time", None),
            ActiveLoop(None)  # 停用表单循环
        ]

class ActionSubmitAppointmentForm(Action):
    """Action to handle appointment form submission after all slots are filled"""
    
    def name(self) -> Text:
        return "action_submit_appointment_form"
    
    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Execute the appointment submission logic"""
        
        from rasa_sdk.events import SlotSet, ActiveLoop
        
        # Get all the collected information
        service_type = tracker.get_slot('service_type')
        customer_name = tracker.get_slot('customer_name')
        customer_phone = tracker.get_slot('customer_phone')
        appointment_date = tracker.get_slot('appointment_date')
        appointment_time = tracker.get_slot('appointment_time')
        
        logger.info(f"ActionSubmitAppointmentForm called with slots: service_type={service_type}, customer_name={customer_name}, customer_phone={customer_phone}, appointment_date={appointment_date}, appointment_time={appointment_time}")
        
        # Validate all required slots are filled
        if not all([service_type, customer_name, customer_phone, appointment_date, appointment_time]):
            dispatcher.utter_message(text="Sorry, some appointment information is missing. Please try booking again.")
            return []
        
        # Create appointment confirmation message
        confirmation_message = f"🎉 **Appointment Confirmed!** Your {service_type} appointment for {customer_name} on {appointment_date} at {appointment_time} has been booked successfully! 📱 You'll receive a confirmation message shortly."
        
        dispatcher.utter_message(text=confirmation_message)
        
        # Save appointment to database
        try:
            from ..config.database import get_collection
            import uuid
            from datetime import datetime
            
            collection = get_collection('appointments')
            if collection:
                appointment_data = {
                    'appointment_id': f"APT-{str(uuid.uuid4())[:8].upper()}",
                    'service_type': service_type,
                    'customer_name': customer_name,
                    'customer_phone': customer_phone,
                    'appointment_date': appointment_date,
                    'appointment_time': appointment_time,
                    'status': 'confirmed',
                    'created_at': datetime.utcnow(),
                    'conversation_id': tracker.sender_id
                }
                
                collection.insert_one(appointment_data)
                logger.info(f"Appointment saved successfully: {appointment_data['appointment_id']}")
        except Exception as e:
            logger.error(f"Error saving appointment: {e}")
        
        # Clear the form slots and deactivate the form
        return [
            SlotSet("service_type", None),
            SlotSet("customer_name", None), 
            SlotSet("customer_phone", None),
            SlotSet("appointment_date", None),
            SlotSet("appointment_time", None),
            ActiveLoop(None)  # 停用表单循环
        ]

# Legacy class aliases for backward compatibility
ActionCancelAppointment = AsyncActionCancelAppointment

