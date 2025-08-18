"""Optimized Appointment Booking RASA Actions
Handles appointment booking, viewing, and management for automotive services
Optimized with async processing, database connection pooling, and enhanced caching
"""

import os
import logging
import asyncio
from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
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

# Initialize global instances
database_pool = get_database_pool()
db_pool = DatabasePool()

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
        db = await db_pool.get_database()
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
    return await cache_get_or_set(cache_key, fetch_client_data, ttl=300)

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
            
            appointments = await self._get_customer_appointments_async(customer_phone)
            
            if not appointments:
                dispatcher.utter_message(
                    text="🔍 **No Appointments Found**\n\nI couldn't find any appointments linked to this phone number in our system.\n\n💡 **Possible reasons:**\n• Different phone number was used for booking\n• Appointments were made under a different contact\n• No appointments have been scheduled yet\n\n🚗 **Ready to get started?** I'd be happy to help you book your first appointment! Just let me know what service you need."
                )
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
            self.log_action_execution("AsyncActionViewAppointments", tracker, success=False, error=str(e))
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
        return await cache_get_or_set(cache_key, fetch_appointments, ttl=120)

    async def _format_appointments_message_async(self, upcoming: List[Dict], past: List[Dict]) -> str:
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
            
            success, cancelled_appointment = await self._cancel_appointment_async(appointment_id, customer_phone)
            
            if success:
                success_message = f"✅ **Appointment Successfully Cancelled!**\n\nYour appointment (ID: {appointment_id[:8]}) has been cancelled and removed from our system. \n\n💡 **What's next?**\n• Need to reschedule? I can help you find a new time slot\n• Have questions? Feel free to ask me anything\n• Want to book a different service? Just let me know!\n\nThank you for letting us know in advance! 😊"
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
                not_found_message = f"🔍 **Appointment Not Found**\n\nI couldn't locate an appointment with ID **{appointment_id[:8]}** for your phone number.\n\n💡 **Please check:**\n• Is the appointment ID correct? (Check your confirmation message)\n• Did you use the same phone number for booking?\n• Has the appointment already been cancelled?\n\nIf you're still having trouble, I can help you view all your appointments to find the right ID! 📋"
                dispatcher.utter_message(text=not_found_message)
                
                # Log bot response
                self.log_bot_response(dispatcher, tracker, "AsyncActionCancelAppointment")
            
            return [SlotSet("appointment_id", None)]
            
        except Exception as e:
            logger.error(f"Error in AsyncActionCancelAppointment: {e}")
            fallback_message = "Sorry, there was an error cancelling your appointment. Please try again or contact us directly."
            dispatcher.utter_message(text=fallback_message)
            
            # Log action execution failure and bot response
            self.log_action_execution("AsyncActionCancelAppointment", tracker, success=False, error=str(e))
            self.log_bot_response(dispatcher, tracker, "AsyncActionCancelAppointment")
            
            return []

    async def _cancel_appointment_async(self, appointment_id: str, customer_phone: str) -> tuple[bool, Optional[Dict]]:
        """Cancel appointment in database and return appointment data for email"""
        try:
            db = await get_mongodb_client()
            if not db:
                return False, None
            
            collection = db.appointments
            
            # First, find the appointment to get its data for email
            appointment = await collection.find_one({
                "appointment_id": appointment_id,
                "customer_phone": customer_phone,
                "status": {"$in": ["confirmed", "pending"]}
            })
            
            if not appointment:
                return False, None
            
            # Update the appointment status with timestamp
            current_time = datetime.now(pytz.timezone('Asia/Singapore'))
            result = await collection.update_one(
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

class ActionViewAppointments(Action):
    """Action to view customer appointments"""
    
    def name(self) -> Text:
        return "action_view_appointments"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Check if appointment feature is enabled
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            if not client_id:
                dispatcher.utter_message(text="抱歉，预约功能目前不可用。请稍后再试。")
                return []
            
            if not check_appointment_feature_enabled(client_id):
                dispatcher.utter_message(text="抱歉，预约功能目前不可用。请稍后再试。")
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
                    dispatcher.utter_message(text="请提供您的电话号码以查看预约信息。")
                    return [SlotSet("requested_slot", "phone_number")]
            
            # Get customer appointments
            appointments = self._get_customer_appointments(phone_number)
            
            if not appointments:
                dispatcher.utter_message(text="您目前没有任何预约记录。")
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
                message_parts.append("📅 **即将到来的预约:**")
                for apt in upcoming_appointments:
                    apt_time = apt['appointment_datetime']
                    if isinstance(apt_time, str):
                        apt_time = datetime.fromisoformat(apt_time.replace('Z', '+00:00'))
                    
                    formatted_time = apt_time.strftime('%Y年%m月%d日 %H:%M')
                    message_parts.append(
                        f"• {apt.get('service_type', '未知服务')} - {formatted_time}\n"
                        f"  状态: {apt.get('status', '未知')}\n"
                        f"  预约ID: {apt.get('_id', 'N/A')}"
                    )
            
            if past_appointments:
                message_parts.append("\n📋 **历史预约:**")
                for apt in past_appointments[-3:]:  # Show last 3 past appointments
                    apt_time = apt['appointment_datetime']
                    if isinstance(apt_time, str):
                        apt_time = datetime.fromisoformat(apt_time.replace('Z', '+00:00'))
                    
                    formatted_time = apt_time.strftime('%Y年%m月%d日 %H:%M')
                    message_parts.append(
                        f"• {apt.get('service_type', '未知服务')} - {formatted_time}\n"
                        f"  状态: {apt.get('status', '未知')}"
                    )
            
            final_message = "\n\n".join(message_parts)
            dispatcher.utter_message(text=final_message)
            
            return [SlotSet("phone_number", phone_number)]
            
        except Exception as e:
            logger.error(f"Error in ActionViewAppointments: {e}")
            dispatcher.utter_message(text="抱歉，查看预约时出现错误。请稍后再试。")
            return []
    
    def _get_customer_appointments(self, phone_number: str) -> List[Dict[str, Any]]:
        """Get customer appointments from database"""
        try:
            client = get_mongo_client()
            if not client:
                return []
            
            db = client[os.getenv('DATABASE_NAME', 'automotive_chatbot_saas')]
            appointments_collection = db['appointments']
            
            # Find appointments by phone number
            appointments = list(appointments_collection.find(
                {"customer_phone": phone_number}
            ).sort("appointment_datetime", -1))
            
            client.close()
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
                dispatcher.utter_message(
                    text="I understand you'd like to book an appointment. Let me help you with that!"
                )
                return [FollowupAction("action_book_appointment")]
            else:
                dispatcher.utter_message(
                    text="I'm here to help! Could you please clarify what you'd like to do?"
                )
                return []
                
        except Exception as e:
            logger.error(f"Error in ActionValidateIntent: {e}")
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
            if not client_id:
                dispatcher.utter_message(
                    text="Sorry, appointment booking is currently not available. Please try again later."
                )
                return []
            
            if not check_appointment_feature_enabled(client_id):
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
            
            # If no service type detected, show options with buttons
            try:
                # Use synchronous version with buttons to avoid event loop conflicts
                appointment_options = self._get_appointment_options_with_buttons_sync()
                
                # Send message with buttons and activate the form
                dispatcher.utter_message(
                    text=appointment_options["text"],
                    buttons=appointment_options["buttons"]
                )
                # Activate the appointment form to collect user details
                return [FollowupAction("appointment_form")]
            except Exception as e:
                logger.error(f"Error getting appointment options: {e}")
                # Fallback to basic sync version if buttons fail
                appointment_options = self._get_appointment_options_sync()
                dispatcher.utter_message(text=appointment_options)
                return [SlotSet("requested_slot", "service_type")]
                
        except Exception as e:
            logger.error(f"Error in ActionBookAppointment: {e}")
            dispatcher.utter_message(
                text="Sorry, there was an error with appointment booking. Please try again."
            )
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
                    "payload": apt_type['name'].lower()
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
            dispatcher.utter_message(text="Please select a service type: Test Drive, Sales Consultation, or Trade-in Evaluation.")
            return {"service_type": None}
    
    def validate_customer_name(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        """Validate customer_name value."""
        customer_name = tracker.get_slot('customer_name')
        if customer_name and len(customer_name.strip()) >= 2:
            return {"customer_name": customer_name.strip()}
        else:
            dispatcher.utter_message(text="Please provide your full name (at least 2 characters).")
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
                dispatcher.utter_message(text="Please provide a valid Singapore phone number (8 digits starting with 8 or 9).")
                return {"customer_phone": None}
        else:
            dispatcher.utter_message(text="Please provide your phone number.")
            return {"customer_phone": None}
    
    def validate_appointment_date(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        """Validate appointment_date value."""
        appointment_date = tracker.get_slot('appointment_date')
        if appointment_date:
            return {"appointment_date": appointment_date}
        else:
            dispatcher.utter_message(text="Please provide your preferred appointment date (e.g., 'tomorrow', 'Monday', '2024-01-15').")
            return {"appointment_date": None}
    
    def validate_appointment_time(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        """Validate appointment_time value."""
        appointment_time = tracker.get_slot('appointment_time')
        if appointment_time:
            return {"appointment_time": appointment_time}
        else:
            dispatcher.utter_message(text="Please provide your preferred appointment time (e.g., '2pm', '10:30 AM', 'morning').")
            return {"appointment_time": None}
    

    
    def submit(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Define what the form has to do after all required slots are filled"""
        
        # Get all the collected information
        service_type = tracker.get_slot('service_type')
        customer_name = tracker.get_slot('customer_name')
        customer_phone = tracker.get_slot('customer_phone')
        appointment_date = tracker.get_slot('appointment_date')
        appointment_time = tracker.get_slot('appointment_time')
        
        # Create appointment confirmation message
        confirmation_message = f"""🎉 **Appointment Confirmed!** 

📋 **Appointment Details:**
• **Service:** {service_type}
• **Customer:** {customer_name}
• **Phone:** {customer_phone}
• **Date:** {appointment_date}
• **Time:** {appointment_time}

✅ **Your appointment has been successfully booked!**
📱 **You'll receive a confirmation message shortly.**

🤝 **Need to make changes?** Just let me know and I'll help you reschedule!"""
        
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
        
        # Clear the form slots
        return [
            SlotSet("service_type", None),
            SlotSet("customer_name", None), 
            SlotSet("customer_phone", None),
            SlotSet("appointment_date", None),
            SlotSet("appointment_time", None)
        ]

# Legacy class aliases for backward compatibility
ActionCancelAppointment = AsyncActionCancelAppointment

