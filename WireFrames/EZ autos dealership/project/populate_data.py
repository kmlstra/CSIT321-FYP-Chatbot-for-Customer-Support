import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Now import Django models and MongoDB functions
from django.contrib.auth.models import User
from api.models import Profile, KnowledgeBase, ChatbotSettings, VehicleInquiry, NewsletterSubscription
from api.mongodb_models import (
    create_vehicle, create_test_drive, save_chat_message, 
    save_feedback, create_team_member,
    vehicles_collection, test_drives_collection, 
    chat_history_collection, feedback_collection, team_members_collection
)

def populate_django_data():
    """Populate Django database with sample data"""
    print("Populating Django database...")
    
    # Create additional users
    users_data = [
        {'email': 'customer1@example.com', 'password': 'password123', 'role': 'user'},
        {'email': 'customer2@example.com', 'password': 'password123', 'role': 'user'},
        {'email': 'sales@ezautos.com', 'password': 'password123', 'role': 'sales'},
        {'email': 'manager@ezautos.com', 'password': 'password123', 'role': 'manager'},
    ]
    
    for user_data in users_data:
        if not User.objects.filter(username=user_data['email']).exists():
            user = User.objects.create_user(
                username=user_data['email'],
                email=user_data['email'],
                password=user_data['password']
            )
            Profile.objects.create(user=user, role=user_data['role'])
            print(f"Created user: {user_data['email']}")
    
    # Create knowledge base articles
    kb_articles = [
        {
            'title': 'How to Schedule a Test Drive',
            'content': 'You can schedule a test drive by contacting our sales team or using our online booking system. We recommend bringing a valid driver\'s license and proof of insurance.',
            'category': 'Test Drives',
            'tags': ['test drive', 'booking', 'requirements'],
            'status': 'active'
        },
        {
            'title': 'Financing Options Available',
            'content': 'We offer various financing options including traditional auto loans, lease agreements, and special promotional rates. Our finance team can help you find the best option for your budget.',
            'category': 'Financing',
            'tags': ['financing', 'loans', 'lease'],
            'status': 'active'
        },
        {
            'title': 'Vehicle Warranty Information',
            'content': 'All our vehicles come with comprehensive warranty coverage. New vehicles include manufacturer warranty, while pre-owned vehicles come with our certified pre-owned warranty.',
            'category': 'Warranty',
            'tags': ['warranty', 'coverage', 'protection'],
            'status': 'active'
        },
        {
            'title': 'Trade-In Process',
            'content': 'We accept trade-ins and offer competitive valuations. Bring your vehicle for an appraisal, and we\'ll provide you with a fair market value assessment.',
            'category': 'Trade-In',
            'tags': ['trade-in', 'appraisal', 'valuation'],
            'status': 'active'
        },
        {
            'title': 'Service and Maintenance',
            'content': 'Our certified service center provides comprehensive maintenance and repair services. We use genuine parts and offer competitive pricing on all services.',
            'category': 'Service',
            'tags': ['service', 'maintenance', 'repair'],
            'status': 'active'
        }
    ]
    
    admin_user = User.objects.filter(email='admin@example.com').first()
    for article_data in kb_articles:
        if not KnowledgeBase.objects.filter(title=article_data['title']).exists():
            KnowledgeBase.objects.create(
                **article_data,
                created_by=admin_user
            )
            print(f"Created KB article: {article_data['title']}")
    
    # Create chatbot settings
    # Create vehicle inquiries
    inquiry_types = ['general', 'test_drive', 'financing', 'trade_in']
    for i in range(10):
        VehicleInquiry.objects.create(
            vehicle_id=f"vehicle_{i+1}",
            inquiry_type=random.choice(inquiry_types),
            name=f"Customer {i+1}",
            email=f"customer{i+1}@example.com",
            phone=f"(555) 123-{4567+i}",
            message=f"I'm interested in learning more about this vehicle. Could you provide more details about pricing and availability?",
            status='pending'
        )
    print("Created 10 vehicle inquiries")
    
    # Create newsletter subscriptions
    for i in range(25):
        email = f"subscriber{i+1}@example.com"
        if not NewsletterSubscription.objects.filter(email=email).exists():
            NewsletterSubscription.objects.create(
                email=email,
                name=f"Subscriber {i+1}",
                is_active=True
            )
    print("Created 25 newsletter subscriptions")

def populate_mongodb_data():
    """Populate MongoDB with sample data"""
    print("Populating MongoDB database...")
    
    # Check if collections are available - FIXED: Use 'is None' instead of boolean check
    if vehicles_collection is None:
        print("MongoDB vehicles collection not available, skipping vehicle data")
        return
    
    # Additional vehicles (beyond the ones created in mongodb_models.py)
    additional_vehicles = [
        {
            "make": "Honda",
            "model": "Accord",
            "year": 2023,
            "price": 32000,
            "mileage": 5000,
            "fuel_type": "Hybrid",
            "transmission": "Automatic",
            "color": "Silver",
            "image_url": "https://images.pexels.com/photos/1592384/pexels-photo-1592384.jpeg",
            "featured": False,
            "description": "Reliable midsize sedan with excellent fuel economy and spacious interior.",
            "status": "available",
            "vin": "1HGCV1F30JA123456",
            "engine": "2.0L Hybrid",
            "drivetrain": "FWD",
            "mpg_city": 48,
            "mpg_highway": 47,
            "features": ["Honda Sensing", "Apple CarPlay", "Heated Seats", "Dual-Zone Climate"]
        },
        {
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "price": 28500,
            "mileage": 8000,
            "fuel_type": "Gasoline",
            "transmission": "Automatic",
            "color": "Blue",
            "image_url": "https://images.pexels.com/photos/1545743/pexels-photo-1545743.jpeg",
            "featured": False,
            "description": "Popular midsize sedan known for reliability and comfort.",
            "status": "available",
            "vin": "4T1C11AK5JU123456",
            "engine": "2.5L 4-Cylinder",
            "drivetrain": "FWD",
            "mpg_city": 28,
            "mpg_highway": 39,
            "features": ["Toyota Safety Sense", "Wireless Charging", "JBL Audio", "Smart Key"]
        },
        {
            "make": "Ford",
            "model": "F-150",
            "year": 2023,
            "price": 45000,
            "mileage": 12000,
            "fuel_type": "Gasoline",
            "transmission": "Automatic",
            "color": "Red",
            "image_url": "https://images.pexels.com/photos/1335077/pexels-photo-1335077.jpeg",
            "featured": True,
            "description": "America's best-selling truck with impressive towing capacity and advanced features.",
            "status": "available",
            "vin": "1FTFW1E50JFC12345",
            "engine": "3.5L V6 EcoBoost",
            "drivetrain": "4WD",
            "mpg_city": 20,
            "mpg_highway": 24,
            "features": ["Pro Trailer Backup Assist", "SYNC 4", "FordPass Connect", "LED Lighting"]
        },
        {
            "make": "Chevrolet",
            "model": "Tahoe",
            "year": 2023,
            "price": 58000,
            "mileage": 15000,
            "fuel_type": "Gasoline",
            "transmission": "Automatic",
            "color": "Black",
            "image_url": "https://images.pexels.com/photos/1592384/pexels-photo-1592384.jpeg",
            "featured": False,
            "description": "Full-size SUV with three rows of seating and powerful V8 engine.",
            "status": "available",
            "vin": "1GNSKCKC5JR123456",
            "engine": "5.3L V8",
            "drivetrain": "4WD",
            "mpg_city": 16,
            "mpg_highway": 20,
            "features": ["Magnetic Ride Control", "Bose Audio", "Rear Entertainment", "Hands-Free Liftgate"]
        },
        {
            "make": "Nissan",
            "model": "Altima",
            "year": 2023,
            "price": 26500,
            "mileage": 18000,
            "fuel_type": "Gasoline",
            "transmission": "Automatic",
            "color": "White",
            "image_url": "https://images.pexels.com/photos/1592384/pexels-photo-1592384.jpeg",
            "featured": False,
            "description": "Stylish sedan with advanced safety features and comfortable ride.",
            "status": "available",
            "vin": "1N4BL4BV5JC123456",
            "engine": "2.5L 4-Cylinder",
            "drivetrain": "FWD",
            "mpg_city": 28,
            "mpg_highway": 39,
            "features": ["ProPILOT Assist", "NissanConnect", "Zero Gravity Seats", "Intelligent Key"]
        }
    ]
    
    # Add vehicles if they don't exist
    for vehicle_data in additional_vehicles:
        try:
            existing = vehicles_collection.find_one({"vin": vehicle_data["vin"]})
            if not existing:
                result = create_vehicle(vehicle_data)
                print(f"Created vehicle: {vehicle_data['year']} {vehicle_data['make']} {vehicle_data['model']}")
        except Exception as e:
            print(f"Error creating vehicle {vehicle_data['make']} {vehicle_data['model']}: {str(e)}")
    
    # Create test drive bookings
    if test_drives_collection is not None:
        try:
            # Get some vehicle IDs for test drives
            sample_vehicles = list(vehicles_collection.find().limit(5))
            
            for i in range(15):
                vehicle = random.choice(sample_vehicles)
                booking_date = datetime.now() + timedelta(days=random.randint(1, 30))
                
                test_drive_data = {
                    "user_id": str(random.randint(1, 5)),
                    "vehicle_id": str(vehicle["_id"]),
                    "booking_date": booking_date.isoformat(),
                    "customer_name": f"Customer {i+1}",
                    "customer_email": f"customer{i+1}@example.com",
                    "customer_phone": f"(555) 123-{4567+i}",
                    "status": random.choice(["pending", "approved", "completed", "cancelled"]),
                    "notes": f"Test drive request for {vehicle['make']} {vehicle['model']}"
                }
                
                result = create_test_drive(test_drive_data)
                print(f"Created test drive booking {i+1}")
        except Exception as e:
            print(f"Error creating test drives: {str(e)}")
    
    # Create chat history
    if chat_history_collection is not None:
        try:
            chat_sessions = [f"session_{i}" for i in range(1, 11)]
            
            sample_conversations = [
                ("Hello, I'm looking for a reliable family car", "Hello! I'd be happy to help you find a reliable family car. What size family do you have and what's your budget range?"),
                ("What financing options do you have?", "We offer various financing options including traditional auto loans with rates starting at 2.9% APR, lease agreements, and special promotional rates. Would you like to speak with our finance team?"),
                ("Can I schedule a test drive?", "Absolutely! I can help you schedule a test drive. Which vehicle are you interested in testing?"),
                ("What are your business hours?", "We're open Monday-Friday 9AM-8PM, Saturday 10AM-6PM, and Sunday 11AM-5PM. Is there a specific time you'd like to visit?"),
                ("Do you accept trade-ins?", "Yes, we accept trade-ins and offer competitive valuations. You can bring your vehicle for a free appraisal. What vehicle are you looking to trade in?")
            ]
            
            for i in range(25):
                session_id = random.choice(chat_sessions)
                user_msg, bot_msg = random.choice(sample_conversations)
                
                # Save user message
                save_chat_message({
                    "user_id": str(random.randint(1, 5)),
                    "session_id": session_id,
                    "message": user_msg,
                    "sender": "user"
                })
                
                # Save bot response
                save_chat_message({
                    "user_id": str(random.randint(1, 5)),
                    "session_id": session_id,
                    "message": bot_msg,
                    "sender": "bot"
                })
            
            print("Created 50 chat messages (25 conversations)")
        except Exception as e:
            print(f"Error creating chat history: {str(e)}")
    
    # Create feedback
    if feedback_collection is not None:
        try:
            sample_vehicles = list(vehicles_collection.find().limit(5))
            feedback_categories = ["Service", "Product", "Website", "Support"]
            
            sample_comments = [
                "Excellent service! The staff was very helpful and knowledgeable.",
                "Great selection of vehicles and competitive pricing.",
                "The website is easy to use and has all the information I needed.",
                "Quick response to my inquiries and professional service.",
                "Very satisfied with my purchase experience.",
                "The test drive was well organized and informative.",
                "Financing process was smooth and transparent.",
                "Outstanding customer service from start to finish."
            ]
            
            for i in range(20):
                vehicle = random.choice(sample_vehicles) if sample_vehicles else None
                
                feedback_data = {
                    "user_id": str(random.randint(1, 5)),
                    "rating": random.randint(3, 5),
                    "comment": random.choice(sample_comments),
                    "category": random.choice(feedback_categories),
                    "status": "active"
                }
                
                if vehicle:
                    feedback_data["vehicle_id"] = str(vehicle["_id"])
                
                result = save_feedback(feedback_data)
                print(f"Created feedback entry {i+1}")
        except Exception as e:
            print(f"Error creating feedback: {str(e)}")
    
    # Create additional team members
    if team_members_collection is not None:
        try:
            additional_team = [
                {
                    "name": "Sarah Wilson",
                    "email": "sarah@ezautos.com",
                    "role": "Customer Service Representative",
                    "department": "Customer Service",
                    "phone": "(555) 123-4570",
                    "status": "active",
                    "hire_date": "2022-08-15",
                    "bio": "Sarah specializes in customer support and handles all customer inquiries with care and professionalism."
                },
                {
                    "name": "David Brown",
                    "email": "david@ezautos.com",
                    "role": "Automotive Technician",
                    "department": "Service",
                    "phone": "(555) 123-4571",
                    "status": "active",
                    "hire_date": "2020-11-20",
                    "bio": "David is our lead technician with over 15 years of experience in automotive repair and maintenance."
                },
                {
                    "name": "Lisa Garcia",
                    "email": "lisa@ezautos.com",
                    "role": "Marketing Coordinator",
                    "department": "Marketing",
                    "phone": "(555) 123-4572",
                    "status": "active",
                    "hire_date": "2023-02-10",
                    "bio": "Lisa manages our marketing campaigns and social media presence to help customers discover our services."
                }
            ]
            
            for member_data in additional_team:
                try:
                    existing = team_members_collection.find_one({"email": member_data["email"]})
                    if not existing:
                        result = create_team_member(member_data)
                        print(f"Created team member: {member_data['name']}")
                except Exception as e:
                    print(f"Error creating team member {member_data['name']}: {str(e)}")
        except Exception as e:
            print(f"Error creating team members: {str(e)}")

def main():
    try:
        print("Starting database population...")
        print("=" * 50)
        
        # Populate Django database
        populate_django_data()
        print("\n" + "=" * 50)
        
        # Populate MongoDB database
        populate_mongodb_data()
        print("\n" + "=" * 50)
        
        print("Database population completed successfully!")
        print("\nTest credentials:")
        print("Admin: admin@example.com / admin")
        print("Customer: customer1@example.com / password123")
        print("Sales: sales@ezautos.com / password123")
        print("Manager: manager@ezautos.com / password123")
        
    except Exception as e:
        print(f"Error during population: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()