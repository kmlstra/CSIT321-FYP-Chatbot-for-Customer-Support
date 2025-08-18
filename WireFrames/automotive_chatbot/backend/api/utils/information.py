"""Information Class for CleverCompanion Support Data
Centralized information storage with dynamic client data loading
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import os
import sys
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Add the backend directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class SupportInformation:
    """Centralized support information class for CleverCompanion with dynamic client data"""
    
    def __init__(self, client_id: Optional[str] = None):
        """Initialize support information with optional client_id for dynamic loading"""
        self.client_id = client_id
        self._data = self._get_default_data()
        
        # If client_id is provided, load client-specific data
        if client_id:
            try:
                # Try cache first for immediate response
                cached_data = self._load_from_cache(client_id)
                if cached_data:
                    self._data.update(cached_data)
                else:
                    # Fallback to database load
                    client_data = self._load_client_data(client_id)
                    if client_data:
                        self._data.update(client_data)
            except Exception as e:
                logger.warning(f"Could not load client data for {client_id}: {e}")
                # Fall back to default data
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Get default CleverCompanion data"""
        return {
            "whatsapp_number": "+6542848294",
            "phone_number": "+6562345678", 
            "email": "info@clevercompanion.sg",
            "support_hours": {
                "monday_friday": "9:00 AM - 7:00 PM",
                "saturday": "9:00 AM - 6:00 PM", 
                "sunday": "10:00 AM - 5:00 PM"
            },
            "average_response_time": "< 2 minutes",
            "urgent_hours_message": "For urgent matters outside business hours, please leave a message and we'll respond first thing the next business day.",
            "company_name": "CleverCompanion",
            "website": "https://clevercompanion.sg",
            "address": "1 Corporation Dr, #05-19, Singapore 619775",
            "services": [
                "COE Price Monitoring",
                "Vehicle Recommendations", 
                "Automotive Consultation",
                "Market Analysis",
                "Customer Support"
            ],
            "appointment_types": [
                {
                    "id": "test_drive",
                    "name": "Test Drive",
                    "description": "Experience our vehicles firsthand",
                    "icon": "🚗",
                    "duration_minutes": 60,
                    "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
                },
                {
                    "id": "sales_consultation",
                    "name": "Sales Consultation",
                    "description": "Discuss vehicle options with our sales team",
                    "icon": "💼",
                    "duration_minutes": 45,
                    "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
                },
                {
                    "id": "trade_in_evaluation",
                    "name": "Trade-in Evaluation",
                    "description": "Get your current vehicle appraised",
                    "icon": "🔄",
                    "duration_minutes": 30,
                    "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
                }
            ],
            "business_registration": "Singapore",
            "operating_since": "2024"
        }
    
    def _load_from_cache(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Load client data from cache if available"""
        try:
            from api.utils.cache_preloader import get_cache_preloader
            from api.config.database import get_real_admin_db
            import asyncio
            
            # Get database connection for cache preloader
            try:
                loop = asyncio.get_running_loop()
                # We're in a running event loop, can't use asyncio.run
                return None  # Skip cache loading in async context for now
            except RuntimeError:
                # No running event loop, safe to get database
                try:
                    db = asyncio.run(get_real_admin_db())
                    cache_preloader = get_cache_preloader(db)
                except Exception as e:
                    logger.warning(f"Failed to get database for cache preloader: {e}")
                    return None
                    
            if not cache_preloader:
                return None
                
            # Get cached support information
            cached_support = cache_preloader.get_cached_support_info(client_id)
            if cached_support:
                return cached_support
                
            # Try to build from individual cached components
            cached_client = cache_preloader.get_cached_client_data(client_id)
            cached_branding = cache_preloader.get_cached_branding(client_id)
            cached_contact = cache_preloader.get_cached_contact_info(client_id)
            cached_features = cache_preloader.get_cached_features(client_id)
            
            if any([cached_client, cached_branding, cached_contact, cached_features]):
                # Build support info from cached components
                support_data = {}
                
                if cached_client:
                    support_data.update({
                        "company_name": cached_client.get("business_name", "CleverCompanion"),
                        "website": f"https://{cached_client.get('domain', 'clevercompanion.sg')}",
                        "email": cached_client.get("contact_email", "info@clevercompanion.sg")
                    })
                
                if cached_contact:
                    support_data.update({
                        "phone_number": cached_contact.get("phone", "+6562345678"),
                        "whatsapp_number": cached_contact.get("whatsapp", "+6542848294"),
                        "address": cached_contact.get("address", "1 Corporation Dr, #05-19, Singapore 619775")
                    })
                    
                    if cached_contact.get("business_hours"):
                        hours = cached_contact["business_hours"]
                        support_data["support_hours"] = {
                            "monday_friday": hours.get("weekdays", "9:00 AM - 7:00 PM"),
                            "saturday": hours.get("saturday", "9:00 AM - 6:00 PM"),
                            "sunday": hours.get("sunday", "10:00 AM - 5:00 PM")
                        }
                
                if cached_features:
                    services = []
                    if cached_features.get("vehicle_inquiry", True):
                        services.extend(["Vehicle Recommendations", "Automotive Consultation"])
                    if cached_features.get("appointment_booking", True):
                        services.append("Appointment Booking")
                    if cached_features.get("service_booking", True):
                        services.append("Service Booking")
                    if cached_features.get("test_drive_scheduling", True):
                        services.append("Test Drive Scheduling")
                    if cached_features.get("financing_calculator", True):
                        services.append("Financing Calculator")
                    if cached_features.get("trade_in_valuation", True):
                        services.append("Trade-in Valuation")
                    
                    if services:
                        support_data["services"] = services
                
                return support_data
                
            return None
            
        except Exception as e:
            logger.warning(f"Error loading from cache: {e}")
            return None
    
    def _load_client_data(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Load client-specific data from database"""
        try:
            from api.config.database import get_real_admin_db
            from api.client_management.client_crud import ClientCRUD
            from api.utils.cache_preloader import get_cache_preloader
            import asyncio
            import threading
            
            # Try cache first for immediate response
            cached_data = self._load_from_cache(client_id)
            if cached_data:
                return cached_data
            
            # Use asyncio.run to handle async functions properly
            async def load_data():
                # Get database connection
                db = await get_real_admin_db()
                crud = ClientCRUD(db)
                
                client = await crud.get_client(client_id)
                if not client:
                    return None, None, None, None
                
                branding = await crud.get_client_branding(client_id) or {}
                contact_info = await crud.get_client_contact_info(client_id) or {}
                features = await crud.get_client_features(client_id) or {}
                return client, branding, contact_info, features
            
            # Use synchronous database access to avoid event loop conflicts
            try:
                from api.config.database import get_collection
                
                # Get client data using sync database connection
                clients_collection = get_collection('clients')
                if not clients_collection:
                    logger.error("Failed to get clients collection")
                    return None
                
                # Try to find client by ObjectId first, then by custom id, domain, or api_key
                client = None
                try:
                    from bson import ObjectId
                    # Try ObjectId first
                    client = clients_collection.find_one({"_id": ObjectId(client_id)})
                except:
                    pass
                
                if not client:
                    # Try custom id, domain, or api_key
                    client = clients_collection.find_one({
                        "$or": [
                            {"id": client_id},
                            {"domain": client_id},
                            {"api_key": client_id}
                        ]
                    })
                
                if not client:
                    logger.warning(f"No client found for ID: {client_id}")
                    return None
                
                # Extract settings from client document
                settings = client.get('settings', {})
                branding = settings.get('branding', {})
                contact_info = settings.get('contact_info', {})
                features = settings.get('features', {})
                
                logger.info(f"Successfully loaded client data for client_id: {client_id}")
                
            except Exception as e:
                logger.error(f"Failed to load client data for {client_id}: {e}")
                return None
            
            # Transform client data to match our format
            client_data = {
                "company_name": client.get("business_name", "CleverCompanion"),
                "website": f"https://{client.get('domain', 'clevercompanion.sg')}",
                "email": client.get("contact_email", "info@clevercompanion.sg"),
                "address": contact_info.get("address", "1 Corporation Dr, #05-19, Singapore 619775"),
                "phone_number": contact_info.get("phone", "+6562345678"),
                "whatsapp_number": contact_info.get("whatsapp", "+6542848294"),
            }
            
            # Add operating hours if available
            if contact_info.get("business_hours"):
                hours = contact_info["business_hours"]
                client_data["support_hours"] = {
                    "monday_friday": hours.get("weekdays", "9:00 AM - 7:00 PM"),
                    "saturday": hours.get("saturday", "9:00 AM - 6:00 PM"),
                    "sunday": hours.get("sunday", "10:00 AM - 5:00 PM")
                }
            
            # Add services based on enabled features
            services = []
            if features.get("vehicle_inquiry", True):
                services.extend(["Vehicle Recommendations", "Automotive Consultation"])
            if features.get("appointment_booking", True):
                services.append("Appointment Booking")
            if features.get("service_booking", True):
                services.append("Service Booking")
            if features.get("test_drive_scheduling", True):
                services.append("Test Drive Scheduling")
            if features.get("financing_calculator", True):
                services.append("Financing Calculator")
            if features.get("trade_in_valuation", True):
                services.append("Trade-in Valuation")
            
            if services:
                client_data["services"] = services
            
            return client_data
            
        except Exception as e:
            print(f"Error loading client data: {e}")
            return None
    
    @property
    def whatsapp_number(self) -> str:
        """Get WhatsApp contact number"""
        return self._data["whatsapp_number"]
    
    @property
    def phone_number(self) -> str:
        """Get phone contact number"""
        return self._data["phone_number"]
    
    @property
    def email(self) -> str:
        """Get email contact"""
        return self._data["email"]
    
    @property
    def support_hours(self) -> Dict[str, str]:
        """Get support hours"""
        return self._data["support_hours"]
    
    @property
    def average_response_time(self) -> str:
        """Get average response time"""
        return self._data["average_response_time"]
    
    @property
    def urgent_hours_message(self) -> str:
        """Get urgent hours message"""
        return self._data["urgent_hours_message"]
    
    @property
    def company_name(self) -> str:
        """Get company name"""
        return self._data["company_name"]
    
    @property
    def website(self) -> str:
        """Get website URL"""
        return self._data["website"]
    
    @property
    def address(self) -> str:
        """Get company address"""
        return self._data["address"]

    @property
    def google_maps_url(self) -> str:
        """Get Google Maps URL dynamically generated from address"""
        # URL encode the address for Google Maps
        import urllib.parse
        encoded_address = urllib.parse.quote_plus(self.address)
        return f"https://maps.google.com/maps?q={encoded_address}"
    
    @property
    def services(self) -> list:
        """Get list of services"""
        return self._data["services"]
    
    @property
    def appointment_types(self) -> list:
        """Get list of appointment types"""
        return self._data["appointment_types"]
    
    def get_appointment_type_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Get appointment type by ID"""
        for apt_type in self.appointment_types:
            if apt_type["id"] == appointment_id:
                return apt_type
        return None
    
    def get_appointment_type_names(self) -> list:
        """Get list of appointment type names"""
        return [apt_type["name"] for apt_type in self.appointment_types]
    
    # Note: get_appointment_options_message and get_appointment_options_with_buttons
    # methods have been moved to backend.api.actions.appointment_actions
    # for better organization and to resolve dashboard display issues
    
    def get_whatsapp_url(self, message: Optional[str] = None) -> str:
        """Generate WhatsApp URL with optional message"""
        default_message = "Hello! I need assistance with CleverCompanion automotive services."
        msg = message or default_message
        
        # Remove + and format message for URL
        clean_number = self.whatsapp_number.replace("+", "")
        encoded_message = msg.replace(" ", "%20").replace("!", "%21")
        
        return f"https://wa.me/{clean_number}?text={encoded_message}"
    
    def get_phone_url(self) -> str:
        """Generate phone URL"""
        return f"tel:{self.phone_number}"
    
    def get_email_url(self, subject: Optional[str] = None) -> str:
        """Generate email URL with optional subject"""
        default_subject = "CleverCompanion Support Inquiry"
        subj = subject or default_subject
        encoded_subject = subj.replace(" ", "%20")
        
        return f"mailto:{self.email}?subject={encoded_subject}"
    
    def get_support_hours_text(self) -> str:
        """Get formatted support hours text"""
        hours = self.support_hours
        return f"Monday-Friday: {hours['monday_friday']}, Saturday: {hours['saturday']}, Sunday: {hours['sunday']}"
    
    def is_business_hours(self) -> bool:
        """Check if current time is within business hours (Singapore timezone)"""
        # This is a simplified version - you can enhance with proper timezone handling
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour
        
        if weekday < 5:  # Monday to Friday (9AM-7PM)
            return 9 <= hour < 19
        elif weekday == 5:  # Saturday (9AM-6PM)
            return 9 <= hour < 18
        elif weekday == 6:  # Sunday (10AM-5PM)
            return 10 <= hour < 17
        else:
            return False
    
    def get_all_contact_info(self) -> Dict[str, Any]:
        """Get all contact information as dictionary"""
        return {
            "whatsapp_number": self.whatsapp_number,
            "phone_number": self.phone_number,
            "email": self.email,
            "support_hours": self.support_hours,
            "average_response_time": self.average_response_time,
            "urgent_hours_message": self.urgent_hours_message,
            "whatsapp_url": self.get_whatsapp_url(),
            "phone_url": self.get_phone_url(),
            "email_url": self.get_email_url(),
            "support_hours_text": self.get_support_hours_text(),
            "is_business_hours": self.is_business_hours()
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get company information"""
        return {
            "company_name": self.company_name,
            "website": self.website,
            "address": self.address,
            "services": self.services,
            "business_registration": self._data["business_registration"],
            "operating_since": self._data["operating_since"]
        }
    
    def update_contact_info(self, **kwargs) -> None:
        """Update contact information"""
        allowed_fields = [
            "whatsapp_number", "phone_number", "email", 
            "support_hours", "average_response_time", "urgent_hours_message"
        ]
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                self._data[key] = value
            else:
                raise ValueError(f"Field '{key}' is not allowed to be updated")

# Global instance for easy import (default CleverCompanion data)
support_info = SupportInformation()

# Factory function to create client-specific instances
def get_client_support_info(client_id: str) -> SupportInformation:
    """Get client-specific support information instance"""
    return SupportInformation(client_id=client_id)

# Convenience functions for direct access (default data)
def get_whatsapp_number(client_id: Optional[str] = None) -> str:
    """Get WhatsApp number"""
    if client_id:
        return get_client_support_info(client_id).whatsapp_number
    return support_info.whatsapp_number

def get_phone_number(client_id: Optional[str] = None) -> str:
    """Get phone number"""
    if client_id:
        return get_client_support_info(client_id).phone_number
    return support_info.phone_number

def get_email(client_id: Optional[str] = None) -> str:
    """Get email address"""
    if client_id:
        return get_client_support_info(client_id).email
    return support_info.email

def get_support_hours(client_id: Optional[str] = None) -> Dict[str, str]:
    """Get support hours"""
    if client_id:
        return get_client_support_info(client_id).support_hours
    return support_info.support_hours

def get_whatsapp_url(message: Optional[str] = None, client_id: Optional[str] = None) -> str:
    """Get WhatsApp URL with message"""
    if client_id:
        return get_client_support_info(client_id).get_whatsapp_url(message)
    return support_info.get_whatsapp_url(message)

def get_appointment_types(client_id: Optional[str] = None) -> list:
    """Get appointment types"""
    if client_id:
        return get_client_support_info(client_id).appointment_types
    return support_info.appointment_types

def get_appointment_type_by_id(appointment_id: str, client_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get appointment type by ID"""
    if client_id:
        return get_client_support_info(client_id).get_appointment_type_by_id(appointment_id)
    return support_info.get_appointment_type_by_id(appointment_id)

def get_appointment_type_names(client_id: Optional[str] = None) -> list:
    """Get appointment type names"""
    if client_id:
        return get_client_support_info(client_id).get_appointment_type_names()
    return support_info.get_appointment_type_names()

# Note: get_appointment_options_message and get_appointment_options_with_buttons
# functions have been moved to backend.api.actions.appointment_actions
# for better organization and to resolve dashboard display issues

def get_all_contact_info(client_id: Optional[str] = None) -> Dict[str, Any]:
    """Get all contact information"""
    if client_id:
        return get_client_support_info(client_id).get_all_contact_info()
    return support_info.get_all_contact_info()

def get_company_info(client_id: Optional[str] = None) -> Dict[str, Any]:
    """Get company information"""
    if client_id:
        return get_client_support_info(client_id).get_company_info()
    return support_info.get_company_info()

def is_business_hours() -> bool:
    """Check if it's business hours"""
    return support_info.is_business_hours()