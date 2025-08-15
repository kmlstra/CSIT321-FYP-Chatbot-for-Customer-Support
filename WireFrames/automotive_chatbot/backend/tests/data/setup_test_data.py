#!/usr/bin/env python3
"""
Test data setup scripts for ABC Motors and XYZ Auto
"""

import asyncio
from datetime import datetime, timedelta
from bson import ObjectId
import secrets
import bcrypt
from typing import Dict, List, Any
import json

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

class TestDataSetup:
    """Setup comprehensive test data for automotive clients"""
    
    def __init__(self, db):
        self.db = db
        self.created_data = {
            "clients": [],
            "users": [],
            "conversations": [],
            "appointments": [],
            "vehicles": [],
            "services": []
        }
    
    async def setup_all_test_data(self):
        """Setup all test data for both ABC Motors and XYZ Auto"""
        print("Setting up comprehensive test data...")
        
        # Setup ABC Motors
        abc_motors_data = await self.setup_abc_motors()
        
        # Setup XYZ Auto
        xyz_auto_data = await self.setup_xyz_auto()
        
        # Setup additional test clients
        additional_clients = await self.setup_additional_test_clients()
        
        # Setup sample conversations and appointments
        await self.setup_sample_conversations(abc_motors_data["client_id"])
        await self.setup_sample_conversations(xyz_auto_data["client_id"])
        
        await self.setup_sample_appointments(abc_motors_data["client_id"])
        await self.setup_sample_appointments(xyz_auto_data["client_id"])
        
        # Setup vehicle inventory
        await self.setup_vehicle_inventory(abc_motors_data["client_id"])
        await self.setup_vehicle_inventory(xyz_auto_data["client_id"])
        
        # Setup service offerings
        await self.setup_service_offerings(abc_motors_data["client_id"])
        await self.setup_service_offerings(xyz_auto_data["client_id"])
        
        print("Test data setup completed successfully!")
        
        return {
            "abc_motors": abc_motors_data,
            "xyz_auto": xyz_auto_data,
            "additional_clients": additional_clients,
            "summary": self.created_data
        }
    
    async def setup_abc_motors(self) -> Dict[str, Any]:
        """Setup ABC Motors test data"""
        print("Setting up ABC Motors...")
        
        # Create ABC Motors client
        abc_client_doc = {
            "business_name": "ABC Motors Pte Ltd",
            "domain": "abcmotors.com",
            "contact_email": "admin@abcmotors.com",
            "phone": "+65 6234 5678",
            "address": "123 Automotive Drive, Singapore 123456",
            "status": "active",
            "api_key": f"cc_abc_{secrets.token_urlsafe(32)}",
            "subscription_plan": "premium",
            "created_at": datetime.utcnow(),
            "settings": {
                "timezone": "Asia/Singapore",
                "currency": "SGD",
                "language": "en",
                "business_hours": {
                    "monday": {"open": "09:00", "close": "18:00"},
                    "tuesday": {"open": "09:00", "close": "18:00"},
                    "wednesday": {"open": "09:00", "close": "18:00"},
                    "thursday": {"open": "09:00", "close": "18:00"},
                    "friday": {"open": "09:00", "close": "18:00"},
                    "saturday": {"open": "09:00", "close": "17:00"},
                    "sunday": {"open": "10:00", "close": "16:00"}
                }
            },
            "widget_settings": {
                "theme": {
                    "primary_color": "#FF6B35",
                    "secondary_color": "#004E89",
                    "background_color": "#FFFFFF",
                    "text_color": "#333333"
                },
                "branding": {
                    "logo_url": "https://abcmotors.com/logo.png",
                    "company_name": "ABC Motors",
                    "welcome_message": "Welcome to ABC Motors! How can we help you find your perfect vehicle today?",
                    "tagline": "Your Trusted Automotive Partner"
                },
                "features": {
                    "appointment_booking": True,
                    "vehicle_inquiry": True,
                    "service_booking": True,
                    "test_drive_scheduling": True,
                    "financing_calculator": True,
                    "trade_in_valuation": True,
                    "live_chat": True,
                    "file_upload": True,
                    "contact_form": True,
                    "multilingual_support": True
                },
                "contact_info": {
                    "phone": "+65 6234 5678",
                    "email": "sales@abcmotors.com",
                    "address": "123 Automotive Drive, Singapore 123456",
                    "website": "https://www.abcmotors.com",
                    "social_media": {
                        "facebook": "https://facebook.com/abcmotors",
                        "instagram": "https://instagram.com/abcmotors",
                        "linkedin": "https://linkedin.com/company/abcmotors"
                    }
                }
            }
        }
        
        abc_client_result = await self.db.clients.insert_one(abc_client_doc)
        abc_client_id = str(abc_client_result.inserted_id)
        self.created_data["clients"].append(abc_client_id)
        
        # Create ABC Motors users
        abc_users = [
            {
                "client_id": abc_client_id,
                "name": "John Smith",
                "email": "john.smith@abcmotors.com",
                "password_hash": hash_password("ABCMotors123!"),
                "role": "admin",
                "status": "active",
                "permissions": ["manage_appointments", "view_analytics", "manage_inventory", "manage_users"],
                "created_at": datetime.utcnow(),
                "profile": {
                    "department": "Management",
                    "position": "General Manager",
                    "phone": "+65 6234 5679"
                }
            },
            {
                "client_id": abc_client_id,
                "name": "Sarah Johnson",
                "email": "sarah.johnson@abcmotors.com",
                "password_hash": hash_password("SalesTeam456!"),
                "role": "sales",
                "status": "active",
                "permissions": ["manage_appointments", "view_inventory", "create_quotes"],
                "created_at": datetime.utcnow(),
                "profile": {
                    "department": "Sales",
                    "position": "Senior Sales Executive",
                    "phone": "+65 6234 5680"
                }
            },
            {
                "client_id": abc_client_id,
                "name": "Mike Chen",
                "email": "mike.chen@abcmotors.com",
                "password_hash": hash_password("ServiceTeam789!"),
                "role": "service",
                "status": "active",
                "permissions": ["manage_service_appointments", "view_service_history"],
                "created_at": datetime.utcnow(),
                "profile": {
                    "department": "Service",
                    "position": "Service Manager",
                    "phone": "+65 6234 5681"
                }
            }
        ]
        
        abc_user_results = await self.db.client_users.insert_many(abc_users)
        self.created_data["users"].extend([str(id) for id in abc_user_results.inserted_ids])
        
        return {
            "client_id": abc_client_id,
            "business_name": "ABC Motors Pte Ltd",
            "domain": "abcmotors.com",
            "api_key": abc_client_doc["api_key"],
            "admin_user": {
                "name": "John Smith",
                "email": "john.smith@abcmotors.com",
                "password": "ABCMotors123!"
            },
            "users": abc_users
        }
    
    async def setup_xyz_auto(self) -> Dict[str, Any]:
        """Setup XYZ Auto test data"""
        print("Setting up XYZ Auto...")
        
        # Create XYZ Auto client
        xyz_client_doc = {
            "business_name": "XYZ Auto Solutions Pte Ltd",
            "domain": "xyzauto.com",
            "contact_email": "info@xyzauto.com",
            "phone": "+65 6345 6789",
            "address": "456 Motor Street, Singapore 654321",
            "status": "active",
            "api_key": f"cc_xyz_{secrets.token_urlsafe(32)}",
            "subscription_plan": "standard",
            "created_at": datetime.utcnow(),
            "settings": {
                "timezone": "Asia/Singapore",
                "currency": "SGD",
                "language": "en",
                "business_hours": {
                    "monday": {"open": "08:30", "close": "19:00"},
                    "tuesday": {"open": "08:30", "close": "19:00"},
                    "wednesday": {"open": "08:30", "close": "19:00"},
                    "thursday": {"open": "08:30", "close": "19:00"},
                    "friday": {"open": "08:30", "close": "19:00"},
                    "saturday": {"open": "08:30", "close": "18:00"},
                    "sunday": "closed"
                }
            },
            "widget_settings": {
                "theme": {
                    "primary_color": "#2E86AB",
                    "secondary_color": "#A23B72",
                    "background_color": "#F8F9FA",
                    "text_color": "#212529"
                },
                "branding": {
                    "logo_url": "https://xyzauto.com/logo.png",
                    "company_name": "XYZ Auto Solutions",
                    "welcome_message": "Hello! Welcome to XYZ Auto Solutions. How can we assist you today?",
                    "tagline": "Innovative Automotive Solutions"
                },
                "features": {
                    "appointment_booking": True,
                    "vehicle_inquiry": True,
                    "service_booking": True,
                    "test_drive_scheduling": False,
                    "financing_calculator": False,
                    "trade_in_valuation": True,
                    "live_chat": True,
                    "file_upload": False,
                    "contact_form": True,
                    "multilingual_support": False
                },
                "contact_info": {
                    "phone": "+65 6345 6789",
                    "email": "contact@xyzauto.com",
                    "address": "456 Motor Street, Singapore 654321",
                    "website": "https://www.xyzauto.com",
                    "social_media": {
                        "facebook": "https://facebook.com/xyzauto",
                        "twitter": "https://twitter.com/xyzauto"
                    }
                }
            }
        }
        
        xyz_client_result = await self.db.clients.insert_one(xyz_client_doc)
        xyz_client_id = str(xyz_client_result.inserted_id)
        self.created_data["clients"].append(xyz_client_id)
        
        # Create XYZ Auto users
        xyz_users = [
            {
                "client_id": xyz_client_id,
                "name": "Lisa Wong",
                "email": "lisa.wong@xyzauto.com",
                "password_hash": hash_password("XYZAuto456!"),
                "role": "admin",
                "status": "active",
                "permissions": ["manage_appointments", "view_analytics", "manage_inventory"],
                "created_at": datetime.utcnow(),
                "profile": {
                    "department": "Operations",
                    "position": "Operations Manager",
                    "phone": "+65 6345 6790"
                }
            },
            {
                "client_id": xyz_client_id,
                "name": "David Tan",
                "email": "david.tan@xyzauto.com",
                "password_hash": hash_password("SalesXYZ789!"),
                "role": "sales",
                "status": "active",
                "permissions": ["manage_appointments", "view_inventory"],
                "created_at": datetime.utcnow(),
                "profile": {
                    "department": "Sales",
                    "position": "Sales Representative",
                    "phone": "+65 6345 6791"
                }
            }
        ]
        
        xyz_user_results = await self.db.client_users.insert_many(xyz_users)
        self.created_data["users"].extend([str(id) for id in xyz_user_results.inserted_ids])
        
        return {
            "client_id": xyz_client_id,
            "business_name": "XYZ Auto Solutions Pte Ltd",
            "domain": "xyzauto.com",
            "api_key": xyz_client_doc["api_key"],
            "admin_user": {
                "name": "Lisa Wong",
                "email": "lisa.wong@xyzauto.com",
                "password": "XYZAuto456!"
            },
            "users": xyz_users
        }
    
    async def setup_additional_test_clients(self) -> List[Dict[str, Any]]:
        """Setup additional test clients for performance and multi-tenant testing"""
        print("Setting up additional test clients...")
        
        additional_clients = []
        
        client_configs = [
            {
                "business_name": "Premium Auto Gallery",
                "domain": "premiumauto.sg",
                "contact_email": "admin@premiumauto.sg",
                "admin_name": "Robert Lee",
                "admin_email": "robert.lee@premiumauto.sg",
                "admin_password": "Premium123!"
            },
            {
                "business_name": "City Motors Hub",
                "domain": "citymotors.sg",
                "contact_email": "admin@citymotors.sg",
                "admin_name": "Jennifer Lim",
                "admin_email": "jennifer.lim@citymotors.sg",
                "admin_password": "CityMotors456!"
            },
            {
                "business_name": "Elite Car Centre",
                "domain": "elitecar.sg",
                "contact_email": "admin@elitecar.sg",
                "admin_name": "Kevin Ng",
                "admin_email": "kevin.ng@elitecar.sg",
                "admin_password": "EliteCar789!"
            }
        ]
        
        for config in client_configs:
            # Create client
            client_doc = {
                "business_name": config["business_name"],
                "domain": config["domain"],
                "contact_email": config["contact_email"],
                "status": "active",
                "api_key": f"cc_{secrets.token_urlsafe(16)}",
                "subscription_plan": "basic",
                "created_at": datetime.utcnow(),
                "settings": {
                    "timezone": "Asia/Singapore",
                    "currency": "SGD",
                    "language": "en"
                }
            }
            
            client_result = await self.db.clients.insert_one(client_doc)
            client_id = str(client_result.inserted_id)
            self.created_data["clients"].append(client_id)
            
            # Create admin user
            user_doc = {
                "client_id": client_id,
                "name": config["admin_name"],
                "email": config["admin_email"],
                "password_hash": hash_password(config["admin_password"]),
                "role": "admin",
                "status": "active",
                "created_at": datetime.utcnow()
            }
            
            user_result = await self.db.client_users.insert_one(user_doc)
            self.created_data["users"].append(str(user_result.inserted_id))
            
            additional_clients.append({
                "client_id": client_id,
                "business_name": config["business_name"],
                "domain": config["domain"],
                "admin_user": {
                    "name": config["admin_name"],
                    "email": config["admin_email"],
                    "password": config["admin_password"]
                }
            })
        
        return additional_clients
    
    async def setup_sample_conversations(self, client_id: str):
        """Setup sample conversations for testing"""
        print(f"Setting up sample conversations for client {client_id[:8]}...")
        
        conversations = [
            {
                "client_id": client_id,
                "session_id": f"conv_{secrets.token_hex(8)}",
                "customer_info": {
                    "name": "Alice Tan",
                    "email": "alice.tan@email.com",
                    "phone": "+65 6123 4567"
                },
                "messages": [
                    {
                        "timestamp": datetime.utcnow() - timedelta(hours=2),
                        "sender": "customer",
                        "content": "Hi, I'm interested in buying a new car"
                    },
                    {
                        "timestamp": datetime.utcnow() - timedelta(hours=2, minutes=-1),
                        "sender": "bot",
                        "content": "Hello Alice! I'd be happy to help you find the perfect car. What type of vehicle are you looking for?"
                    },
                    {
                        "timestamp": datetime.utcnow() - timedelta(hours=2, minutes=-3),
                        "sender": "customer",
                        "content": "I'm looking for a family sedan, preferably hybrid"
                    }
                ],
                "message_count": 3,
                "status": "active",
                "created_at": datetime.utcnow() - timedelta(hours=2),
                "last_activity": datetime.utcnow() - timedelta(minutes=30),
                "tags": ["vehicle_inquiry", "hybrid", "sedan", "family_car"]
            },
            {
                "client_id": client_id,
                "session_id": f"conv_{secrets.token_hex(8)}",
                "customer_info": {
                    "name": "Bob Wilson",
                    "email": "bob.wilson@email.com",
                    "phone": "+65 6234 5678"
                },
                "messages": [
                    {
                        "timestamp": datetime.utcnow() - timedelta(days=1),
                        "sender": "customer",
                        "content": "I need to schedule a service appointment"
                    },
                    {
                        "timestamp": datetime.utcnow() - timedelta(days=1, minutes=-2),
                        "sender": "bot",
                        "content": "I can help you schedule a service appointment. What type of service do you need?"
                    }
                ],
                "message_count": 2,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=1),
                "last_activity": datetime.utcnow() - timedelta(days=1, minutes=-5),
                "tags": ["service_appointment", "maintenance"]
            },
            {
                "client_id": client_id,
                "session_id": f"conv_{secrets.token_hex(8)}",
                "customer_info": {
                    "name": "Carol Lee",
                    "email": "carol.lee@email.com",
                    "phone": "+65 6345 6789"
                },
                "messages": [
                    {
                        "timestamp": datetime.utcnow() - timedelta(hours=6),
                        "sender": "customer",
                        "content": "What financing options do you have?"
                    },
                    {
                        "timestamp": datetime.utcnow() - timedelta(hours=6, minutes=-1),
                        "sender": "bot",
                        "content": "We offer various financing options including bank loans, in-house financing, and leasing. What's your budget range?"
                    },
                    {
                        "timestamp": datetime.utcnow() - timedelta(hours=6, minutes=-3),
                        "sender": "customer",
                        "content": "Around $50,000 for a new SUV"
                    }
                ],
                "message_count": 3,
                "status": "active",
                "created_at": datetime.utcnow() - timedelta(hours=6),
                "last_activity": datetime.utcnow() - timedelta(hours=6, minutes=-3),
                "tags": ["financing", "suv", "budget_50k"]
            }
        ]
        
        conversation_results = await self.db.conversations.insert_many(conversations)
        self.created_data["conversations"].extend([str(id) for id in conversation_results.inserted_ids])
    
    async def setup_sample_appointments(self, client_id: str):
        """Setup sample appointments for testing"""
        print(f"Setting up sample appointments for client {client_id[:8]}...")
        
        appointments = [
            {
                "client_id": client_id,
                "appointment_id": f"apt_{secrets.token_hex(6)}",
                "customer_name": "Alice Tan",
                "customer_email": "alice.tan@email.com",
                "customer_phone": "+65 6123 4567",
                "appointment_datetime": datetime.utcnow() + timedelta(days=2, hours=10),
                "service_type": "test_drive",
                "vehicle_interest": "Toyota Camry Hybrid",
                "status": "confirmed",
                "notes": "Customer interested in hybrid sedan for family use",
                "assigned_staff": "Sarah Johnson",
                "created_at": datetime.utcnow() - timedelta(hours=3),
                "updated_at": datetime.utcnow() - timedelta(hours=1)
            },
            {
                "client_id": client_id,
                "appointment_id": f"apt_{secrets.token_hex(6)}",
                "customer_name": "Bob Wilson",
                "customer_email": "bob.wilson@email.com",
                "customer_phone": "+65 6234 5678",
                "appointment_datetime": datetime.utcnow() + timedelta(days=1, hours=14),
                "service_type": "maintenance",
                "vehicle_info": "Honda Civic 2020",
                "status": "pending",
                "notes": "Regular maintenance service - 20,000km",
                "assigned_staff": "Mike Chen",
                "created_at": datetime.utcnow() - timedelta(days=1),
                "updated_at": datetime.utcnow() - timedelta(days=1)
            },
            {
                "client_id": client_id,
                "appointment_id": f"apt_{secrets.token_hex(6)}",
                "customer_name": "Carol Lee",
                "customer_email": "carol.lee@email.com",
                "customer_phone": "+65 6345 6789",
                "appointment_datetime": datetime.utcnow() + timedelta(days=5, hours=11),
                "service_type": "consultation",
                "vehicle_interest": "BMW X3",
                "status": "confirmed",
                "notes": "Financing consultation for SUV purchase",
                "assigned_staff": "Sarah Johnson",
                "created_at": datetime.utcnow() - timedelta(hours=6),
                "updated_at": datetime.utcnow() - timedelta(hours=6)
            },
            {
                "client_id": client_id,
                "appointment_id": f"apt_{secrets.token_hex(6)}",
                "customer_name": "David Kumar",
                "customer_email": "david.kumar@email.com",
                "customer_phone": "+65 6456 7890",
                "appointment_datetime": datetime.utcnow() - timedelta(days=1, hours=15),
                "service_type": "test_drive",
                "vehicle_interest": "Mercedes-Benz C-Class",
                "status": "completed",
                "notes": "Test drive completed successfully. Customer interested in purchase.",
                "assigned_staff": "Sarah Johnson",
                "created_at": datetime.utcnow() - timedelta(days=3),
                "updated_at": datetime.utcnow() - timedelta(days=1, hours=16)
            }
        ]
        
        appointment_results = await self.db.appointments.insert_many(appointments)
        self.created_data["appointments"].extend([str(id) for id in appointment_results.inserted_ids])
    
    async def setup_vehicle_inventory(self, client_id: str):
        """Setup vehicle inventory for testing"""
        print(f"Setting up vehicle inventory for client {client_id[:8]}...")
        
        vehicles = [
            {
                "client_id": client_id,
                "vehicle_id": f"veh_{secrets.token_hex(6)}",
                "make": "Toyota",
                "model": "Camry",
                "variant": "Hybrid",
                "year": 2024,
                "price": 165000,
                "currency": "SGD",
                "status": "available",
                "stock_quantity": 3,
                "specifications": {
                    "engine": "2.5L Hybrid",
                    "transmission": "CVT",
                    "fuel_type": "Hybrid",
                    "seating_capacity": 5,
                    "body_type": "Sedan",
                    "drivetrain": "FWD"
                },
                "features": ["Safety Sense 2.0", "Apple CarPlay", "LED Headlights", "Wireless Charging"],
                "images": ["https://example.com/camry1.jpg", "https://example.com/camry2.jpg"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "client_id": client_id,
                "vehicle_id": f"veh_{secrets.token_hex(6)}",
                "make": "Honda",
                "model": "Civic",
                "variant": "RS",
                "year": 2024,
                "price": 145000,
                "currency": "SGD",
                "status": "available",
                "stock_quantity": 2,
                "specifications": {
                    "engine": "1.5L Turbo",
                    "transmission": "CVT",
                    "fuel_type": "Petrol",
                    "seating_capacity": 5,
                    "body_type": "Sedan",
                    "drivetrain": "FWD"
                },
                "features": ["Honda SENSING", "Sunroof", "Premium Audio", "Alloy Wheels"],
                "images": ["https://example.com/civic1.jpg", "https://example.com/civic2.jpg"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "client_id": client_id,
                "vehicle_id": f"veh_{secrets.token_hex(6)}",
                "make": "BMW",
                "model": "X3",
                "variant": "xDrive30i",
                "year": 2024,
                "price": 285000,
                "currency": "SGD",
                "status": "available",
                "stock_quantity": 1,
                "specifications": {
                    "engine": "2.0L Twin Turbo",
                    "transmission": "8-Speed Automatic",
                    "fuel_type": "Petrol",
                    "seating_capacity": 5,
                    "body_type": "SUV",
                    "drivetrain": "AWD"
                },
                "features": ["iDrive 7", "Panoramic Sunroof", "Harman Kardon Audio", "Adaptive Suspension"],
                "images": ["https://example.com/x3_1.jpg", "https://example.com/x3_2.jpg"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        vehicle_results = await self.db.vehicles.insert_many(vehicles)
        self.created_data["vehicles"].extend([str(id) for id in vehicle_results.inserted_ids])
    
    async def setup_service_offerings(self, client_id: str):
        """Setup service offerings for testing"""
        print(f"Setting up service offerings for client {client_id[:8]}...")
        
        services = [
            {
                "client_id": client_id,
                "service_id": f"svc_{secrets.token_hex(6)}",
                "name": "Regular Maintenance",
                "category": "maintenance",
                "description": "Comprehensive vehicle maintenance including oil change, filter replacement, and inspection",
                "duration_minutes": 120,
                "price": 150,
                "currency": "SGD",
                "available": True,
                "booking_slots": {
                    "monday": ["09:00", "11:00", "14:00", "16:00"],
                    "tuesday": ["09:00", "11:00", "14:00", "16:00"],
                    "wednesday": ["09:00", "11:00", "14:00", "16:00"],
                    "thursday": ["09:00", "11:00", "14:00", "16:00"],
                    "friday": ["09:00", "11:00", "14:00", "16:00"],
                    "saturday": ["09:00", "11:00", "14:00"]
                },
                "requirements": ["Vehicle registration", "Service history"],
                "created_at": datetime.utcnow()
            },
            {
                "client_id": client_id,
                "service_id": f"svc_{secrets.token_hex(6)}",
                "name": "Test Drive",
                "category": "sales",
                "description": "Test drive experience with our sales consultant",
                "duration_minutes": 60,
                "price": 0,
                "currency": "SGD",
                "available": True,
                "booking_slots": {
                    "monday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                    "tuesday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                    "wednesday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                    "thursday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                    "friday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                    "saturday": ["10:00", "11:00", "14:00", "15:00"],
                    "sunday": ["10:00", "11:00", "14:00"]
                },
                "requirements": ["Valid driving license", "IC/Passport"],
                "created_at": datetime.utcnow()
            },
            {
                "client_id": client_id,
                "service_id": f"svc_{secrets.token_hex(6)}",
                "name": "Vehicle Inspection",
                "category": "inspection",
                "description": "Comprehensive vehicle inspection for pre-owned vehicles",
                "duration_minutes": 90,
                "price": 80,
                "currency": "SGD",
                "available": True,
                "booking_slots": {
                    "monday": ["09:00", "11:00", "14:00"],
                    "tuesday": ["09:00", "11:00", "14:00"],
                    "wednesday": ["09:00", "11:00", "14:00"],
                    "thursday": ["09:00", "11:00", "14:00"],
                    "friday": ["09:00", "11:00", "14:00"],
                    "saturday": ["09:00", "11:00"]
                },
                "requirements": ["Vehicle documents", "Appointment confirmation"],
                "created_at": datetime.utcnow()
            }
        ]
        
        service_results = await self.db.services.insert_many(services)
        self.created_data["services"].extend([str(id) for id in service_results.inserted_ids])
    
    async def cleanup_test_data(self):
        """Clean up all created test data"""
        print("Cleaning up test data...")
        
        # Clean up in reverse order of dependencies
        collections_to_clean = [
            ("services", self.created_data["services"]),
            ("vehicles", self.created_data["vehicles"]),
            ("appointments", self.created_data["appointments"]),
            ("conversations", self.created_data["conversations"]),
            ("client_users", self.created_data["users"]),
            ("clients", self.created_data["clients"])
        ]
        
        for collection_name, ids in collections_to_clean:
            if ids:
                collection = getattr(self.db, collection_name)
                object_ids = [ObjectId(id) for id in ids]
                result = await collection.delete_many({"_id": {"$in": object_ids}})
                print(f"Deleted {result.deleted_count} documents from {collection_name}")
        
        print("Test data cleanup completed!")

# Utility functions for test scripts
async def setup_test_environment(db):
    """Setup complete test environment"""
    setup = TestDataSetup(db)
    return await setup.setup_all_test_data()

async def cleanup_test_environment(db, created_data=None):
    """Cleanup test environment"""
    if created_data:
        setup = TestDataSetup(db)
        setup.created_data = created_data.get("summary", {})
        await setup.cleanup_test_data()
    else:
        # Clean up all test data
        collections = ["services", "vehicles", "appointments", "conversations", "client_users", "clients"]
        for collection_name in collections:
            collection = getattr(db, collection_name)
            await collection.delete_many({})
        print("All test data cleaned up!")

if __name__ == "__main__":
    # This script can be run standalone for manual test data setup
    import motor.motor_asyncio
    import os
    
    async def main():
        # Connect to test database
        mongo_url = os.getenv("MONGODB_TEST_URL", "mongodb://localhost:27017/automotive_chatbot_test")
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        db = client.get_default_database()
        
        # Setup test data
        test_data = await setup_test_environment(db)
        
        print("\nTest data setup summary:")
        print(f"ABC Motors Client ID: {test_data['abc_motors']['client_id']}")
        print(f"XYZ Auto Client ID: {test_data['xyz_auto']['client_id']}")
        print(f"Additional clients: {len(test_data['additional_clients'])}")
        
        # Save test data info to file
        with open("test_data_info.json", "w") as f:
            json.dump(test_data, f, indent=2, default=str)
        
        print("\nTest data info saved to test_data_info.json")
        
        client.close()
    
    asyncio.run(main())