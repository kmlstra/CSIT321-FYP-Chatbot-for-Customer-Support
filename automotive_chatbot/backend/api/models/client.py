"""
Client Model - Multi-tenant SaaS Database Schema
Defines the structure for automotive business clients
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, EmailStr, HttpUrl
from bson import ObjectId

class BrandingConfig(BaseModel):
    """Client branding configuration"""
    logo_url: Optional[HttpUrl] = None
    primary_color: str = "#4F46E5"
    secondary_color: str = "#7C3AED"
    company_name: str
    favicon_url: Optional[HttpUrl] = None
    custom_css: Optional[str] = None

class ContactInfo(BaseModel):
    """Client contact information"""
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    whatsapp: Optional[str] = None
    website: Optional[HttpUrl] = None
    google_maps_url: Optional[HttpUrl] = None

class BusinessHours(BaseModel):
    """Business operating hours"""
    monday: str = "9:00 AM - 6:00 PM"
    tuesday: str = "9:00 AM - 6:00 PM"
    wednesday: str = "9:00 AM - 6:00 PM"
    thursday: str = "9:00 AM - 6:00 PM"
    friday: str = "9:00 AM - 6:00 PM"
    saturday: str = "9:00 AM - 5:00 PM"
    sunday: str = "Closed"
    public_holidays: str = "Closed"

class ChatbotFeatures(BaseModel):
    """Enabled/disabled chatbot features"""
    coe_prices: bool = True
    loan_calculator: bool = True
    test_drive_booking: bool = True
    maintenance_tips: bool = True
    vehicle_search: bool = True
    contact_support: bool = True
    business_hours: bool = True
    custom_responses: bool = False

class SubscriptionPlan(BaseModel):
    """Subscription plan details"""
    plan_type: str  # basic, premium, enterprise
    monthly_conversations: int
    features_included: List[str]
    price_per_month: float
    overage_rate: float  # per additional conversation

class ClientSettings(BaseModel):
    """Complete client configuration"""
    branding: BrandingConfig
    features: ChatbotFeatures
    contact_info: ContactInfo
    business_hours: BusinessHours
    custom_welcome_message: Optional[str] = None
    custom_responses: Optional[Dict[str, str]] = None

class Client(BaseModel):
    """Main client model for automotive businesses"""
    id: Optional[str] = None  # MongoDB ObjectId as string
    business_name: str
    domain: str  # Primary domain for the business
    allowed_domains: List[str] = []  # Additional allowed domains
    contact_email: EmailStr
    subscription_plan: SubscriptionPlan
    status: str = "pending"  # pending, active, suspended, cancelled
    settings: ClientSettings
    
    # Metadata
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    activated_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    # Usage tracking
    current_month_conversations: int = 0
    total_conversations: int = 0
    
    # API keys and security
    api_key: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class ClientUser(BaseModel):
    """Users who can manage a client's chatbot"""
    id: Optional[str] = None
    client_id: str  # Reference to Client
    email: EmailStr
    name: str
    role: str = "admin"  # admin, manager, viewer
    password_hash: str
    status: str = "active"  # pending, active, inactive
    
    # Permissions
    permissions: List[str] = [
        "view_analytics",
        "edit_branding", 
        "manage_vehicles",
        "edit_responses",
        "view_conversations"
    ]
    
    # Metadata
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None
    login_count: int = 0
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class ClientVehicle(BaseModel):
    """Vehicle inventory for each client"""
    id: Optional[str] = None
    client_id: str
    brand: str
    model: str
    year: int
    price: float
    coe_category: str  # A, B, C, E
    availability: str = "in_stock"  # in_stock, sold, reserved
    
    # Vehicle details
    engine_capacity: Optional[float] = None
    fuel_type: str = "Petrol"  # Petrol, Hybrid, Electric, Diesel
    transmission: str = "Automatic"
    mileage: Optional[int] = None
    features: List[str] = []
    images: List[HttpUrl] = []
    description: Optional[str] = None
    
    # Metadata
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class Conversation(BaseModel):
    """Multi-tenant conversation storage"""
    id: Optional[str] = None
    client_id: str
    session_id: str
    user_id: str  # Anonymous or registered user
    
    # Conversation data
    messages: List[Dict[str, Any]] = []
    user_info: Optional[Dict[str, Any]] = None  # Collected user details
    lead_status: str = "new"  # new, qualified, contacted, converted
    
    # Analytics
    total_messages: int = 0
    duration_seconds: Optional[int] = None
    user_satisfaction: Optional[int] = None  # 1-5 rating
    conversion_event: Optional[str] = None  # test_drive_booked, contact_requested
    
    # Metadata
    created_at: datetime = datetime.utcnow()
    ended_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class Analytics(BaseModel):
    """Daily analytics per client"""
    id: Optional[str] = None
    client_id: str
    date: datetime
    
    # Metrics
    total_conversations: int = 0
    unique_users: int = 0
    avg_response_time: float = 0.0
    user_satisfaction_avg: Optional[float] = None
    
    # Popular queries
    popular_intents: Dict[str, int] = {}
    popular_vehicles: Dict[str, int] = {}
    
    # Conversion metrics
    test_drives_booked: int = 0
    contact_requests: int = 0
    loan_calculations: int = 0
    
    # Technical metrics
    error_rate: float = 0.0
    uptime_percentage: float = 100.0
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Subscription plan templates
SUBSCRIPTION_PLANS = {
    "basic": SubscriptionPlan(
        plan_type="basic",
        monthly_conversations=1000,
        features_included=["coe_prices", "vehicle_search", "contact_support"],
        price_per_month=99.0,
        overage_rate=0.10
    ),
    "premium": SubscriptionPlan(
        plan_type="premium", 
        monthly_conversations=5000,
        features_included=["coe_prices", "loan_calculator", "test_drive_booking", 
                          "maintenance_tips", "vehicle_search", "contact_support"],
        price_per_month=299.0,
        overage_rate=0.08
    ),
    "enterprise": SubscriptionPlan(
        plan_type="enterprise",
        monthly_conversations=20000,
        features_included=["all_features", "custom_responses", "priority_support", 
                          "white_label", "api_access"],
        price_per_month=999.0,
        overage_rate=0.05
    )
}