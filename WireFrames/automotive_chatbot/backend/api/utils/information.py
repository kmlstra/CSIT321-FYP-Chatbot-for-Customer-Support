"""Information Class for CleverCompanion Support Data
Centralized information storage without API dependencies
"""

from typing import Dict, Any, Optional
from datetime import datetime

class SupportInformation:
    """Centralized support information class for CleverCompanion"""
    
    def __init__(self):
        """Initialize support information"""
        self._data = {
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
    
    def get_appointment_options_message(self) -> str:
        """Generate formatted appointment options message"""
        message = "🚗 <strong>Select Your Appointment Type</strong>\n\nChoose from our available services:\n\n"
        
        for apt_type in self.appointment_types:
            message += f"{apt_type['icon']} <strong>{apt_type['name']}</strong> - {apt_type['description']}\n"
        
        message += "\n💬 Simply type the service you need (e.g., \"test drive\", \"sales consultation\", \"trade-in evaluation\")"
        return message
    
    def get_appointment_options_with_buttons(self) -> Dict[str, Any]:
        """Generate appointment options message with clickable buttons"""
        message = "🚗 <strong>Select Your Appointment Type</strong>\n\nChoose from our available services:\n\n"
        
        for apt_type in self.appointment_types:
            message += f"{apt_type['icon']} <strong>{apt_type['name']}</strong> - {apt_type['description']}\n"
        
        message += "\n📋 <strong>What I'll also need:</strong>\n• Preferred date and time\n• Your contact information"
        
        # Generate buttons for each appointment type
        buttons = []
        for apt_type in self.appointment_types:
            buttons.append({
                "title": f"{apt_type['icon']} {apt_type['name']}",
                "payload": apt_type['name'].lower()
            })
        
        return {
            "text": message,
            "buttons": buttons
        }
    
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

# Global instance for easy import
support_info = SupportInformation()

# Convenience functions for direct access
def get_whatsapp_number() -> str:
    """Get WhatsApp number"""
    return support_info.whatsapp_number

def get_phone_number() -> str:
    """Get phone number"""
    return support_info.phone_number

def get_email() -> str:
    """Get email address"""
    return support_info.email

def get_support_hours() -> Dict[str, str]:
    """Get support hours"""
    return support_info.support_hours

def get_whatsapp_url(message: Optional[str] = None) -> str:
    """Get WhatsApp URL with message"""
    return support_info.get_whatsapp_url(message)

def get_appointment_types() -> list:
    """Get appointment types"""
    return support_info.appointment_types

def get_appointment_type_by_id(appointment_id: str) -> Optional[Dict[str, Any]]:
    """Get appointment type by ID"""
    return support_info.get_appointment_type_by_id(appointment_id)

def get_appointment_type_names() -> list:
    """Get appointment type names"""
    return support_info.get_appointment_type_names()

def get_appointment_options_message() -> str:
    """Get formatted appointment options message"""
    return support_info.get_appointment_options_message()

def get_appointment_options_with_buttons() -> Dict[str, Any]:
    """Get appointment options with clickable buttons"""
    return support_info.get_appointment_options_with_buttons()

def get_all_contact_info() -> Dict[str, Any]:
    """Get all contact information"""
    return support_info.get_all_contact_info()

def is_business_hours() -> bool:
    """Check if it's business hours"""
    return support_info.is_business_hours()