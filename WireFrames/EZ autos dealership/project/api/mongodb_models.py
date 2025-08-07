import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from datetime import datetime
import certifi

# Connect to MongoDB
try:
    client = MongoClient(
        os.getenv('MONGODB_URI'),
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000
    )
    
    # Test the connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
    
    # Initialize database
    db = client[os.getenv('MONGODB_NAME')]
    
    # Collections
    vehicles_collection = db.vehicles
    test_drives_collection = db.test_drives
    chat_history_collection = db.chat_history
    feedback_collection = db.feedback
    team_members_collection = db.team_members
    vehicle_images_collection = db.vehicle_images
    financing_applications_collection = db.financing_applications
    faq_collection = db.faq
    contact_info_collection = db.contact_info

    # Create indexes in the background
    def ensure_indexes():
        try:
            # Vehicle indexes
            vehicles_collection.create_index([("make", ASCENDING)], background=True)
            vehicles_collection.create_index([("model", ASCENDING)], background=True)
            vehicles_collection.create_index([("year", DESCENDING)], background=True)
            vehicles_collection.create_index([("price", ASCENDING)], background=True)
            vehicles_collection.create_index([("featured", DESCENDING)], background=True)
            vehicles_collection.create_index([("status", ASCENDING)], background=True)
            vehicles_collection.create_index([("fuel_type", ASCENDING)], background=True)
            vehicles_collection.create_index([("transmission", ASCENDING)], background=True)
            vehicles_collection.create_index([("mileage", ASCENDING)], background=True)

            # Test drive indexes
            test_drives_collection.create_index([("user_id", ASCENDING)], background=True)
            test_drives_collection.create_index([("vehicle_id", ASCENDING)], background=True)
            test_drives_collection.create_index([("booking_date", ASCENDING)], background=True)
            test_drives_collection.create_index([("status", ASCENDING)], background=True)
            test_drives_collection.create_index([("created_at", DESCENDING)], background=True)

            # Chat history indexes
            chat_history_collection.create_index([("user_id", ASCENDING)], background=True)
            chat_history_collection.create_index([("session_id", ASCENDING)], background=True)
            chat_history_collection.create_index([("created_at", DESCENDING)], background=True)
            chat_history_collection.create_index([("sender", ASCENDING)], background=True)

            # Feedback indexes
            feedback_collection.create_index([("user_id", ASCENDING)], background=True)
            feedback_collection.create_index([("vehicle_id", ASCENDING)], background=True)
            feedback_collection.create_index([("rating", DESCENDING)], background=True)
            feedback_collection.create_index([("category", ASCENDING)], background=True)
            feedback_collection.create_index([("created_at", DESCENDING)], background=True)

            # Team members indexes
            team_members_collection.create_index([("email", ASCENDING)], background=True, unique=True)
            team_members_collection.create_index([("status", ASCENDING)], background=True)
            team_members_collection.create_index([("department", ASCENDING)], background=True)

            # Vehicle images indexes
            vehicle_images_collection.create_index([("vehicle_id", ASCENDING)], background=True)
            vehicle_images_collection.create_index([("is_primary", DESCENDING)], background=True)

            # Financing applications indexes
            financing_applications_collection.create_index([("user_id", ASCENDING)], background=True)
            financing_applications_collection.create_index([("vehicle_id", ASCENDING)], background=True)
            financing_applications_collection.create_index([("status", ASCENDING)], background=True)
            financing_applications_collection.create_index([("created_at", DESCENDING)], background=True)

            # FAQ indexes
            faq_collection.create_index([("category", ASCENDING)], background=True)
            faq_collection.create_index([("status", ASCENDING)], background=True)
            faq_collection.create_index([("created_at", DESCENDING)], background=True)

            # Contact info indexes
            contact_info_collection.create_index([("type", ASCENDING)], background=True)
            contact_info_collection.create_index([("is_active", DESCENDING)], background=True)

            print("Successfully created/verified all indexes")
        except Exception as e:
            print(f"Warning: Error managing indexes: {str(e)}")

    ensure_indexes()

except Exception as e:
    print(f"Error connecting to MongoDB: {str(e)}")
    # Set collections to None if connection fails
    vehicles_collection = None
    test_drives_collection = None
    chat_history_collection = None
    feedback_collection = None
    team_members_collection = None
    vehicle_images_collection = None
    financing_applications_collection = None

# Vehicle operations
def create_vehicle(vehicle_data):
    if vehicles_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        # Ensure required fields
        required_fields = ['make', 'model', 'year', 'price', 'mileage', 'transmission', 'color']
        for field in required_fields:
            if field not in vehicle_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        vehicle_data.setdefault('fuel_type', 'Gasoline')
        vehicle_data.setdefault('featured', False)
        vehicle_data.setdefault('status', 'available')
        vehicle_data.setdefault('description', '')
        vehicle_data.setdefault('image_url', 'https://images.pexels.com/photos/1231643/pexels-photo-1231643.jpeg')
        vehicle_data['created_at'] = datetime.utcnow()
        vehicle_data['updated_at'] = datetime.utcnow()
        
        return vehicles_collection.insert_one(vehicle_data)
    except Exception as e:
        raise Exception(f"Error creating vehicle: {str(e)}")

def get_vehicles(filters=None, limit=None, skip=0, sort_by=None):
    if vehicles_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        query = filters or {}
        
        # Handle price range filters
        if 'min_price' in query or 'max_price' in query:
            price_filter = {}
            if 'min_price' in query:
                price_filter['$gte'] = int(query.pop('min_price'))
            if 'max_price' in query:
                price_filter['$lte'] = int(query.pop('max_price'))
            if price_filter:
                query['price'] = price_filter
        
        # Handle mileage filter
        if 'max_mileage' in query:
            query['mileage'] = {'$lte': int(query.pop('max_mileage'))}
        
        # Handle text search for make/model
        if 'search' in query:
            search_term = query.pop('search')
            query['$or'] = [
                {'make': {'$regex': search_term, '$options': 'i'}},
                {'model': {'$regex': search_term, '$options': 'i'}},
                {'description': {'$regex': search_term, '$options': 'i'}}
            ]
        
        cursor = vehicles_collection.find(query).skip(skip)
        
        # Apply sorting
        if sort_by:
            if sort_by == 'price_asc':
                cursor = cursor.sort('price', ASCENDING)
            elif sort_by == 'price_desc':
                cursor = cursor.sort('price', DESCENDING)
            elif sort_by == 'year_desc':
                cursor = cursor.sort('year', DESCENDING)
            elif sort_by == 'mileage_asc':
                cursor = cursor.sort('mileage', ASCENDING)
            elif sort_by == 'featured':
                cursor = cursor.sort([('featured', DESCENDING), ('created_at', DESCENDING)])
        else:
            cursor = cursor.sort('created_at', DESCENDING)
        
        if limit:
            cursor = cursor.limit(limit)
            
        return list(cursor)
    except Exception as e:
        raise Exception(f"Error fetching vehicles: {str(e)}")

def get_vehicle_by_id(vehicle_id):
    if vehicles_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        return vehicles_collection.find_one({"_id": ObjectId(vehicle_id)})
    except Exception as e:
        raise Exception(f"Error fetching vehicle: {str(e)}")

def update_vehicle(vehicle_id, update_data):
    if vehicles_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        update_data['updated_at'] = datetime.utcnow()
        return vehicles_collection.update_one(
            {"_id": ObjectId(vehicle_id)},
            {"$set": update_data}
        )
    except Exception as e:
        raise Exception(f"Error updating vehicle: {str(e)}")

def delete_vehicle(vehicle_id):
    if vehicles_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        return vehicles_collection.delete_one({"_id": ObjectId(vehicle_id)})
    except Exception as e:
        raise Exception(f"Error deleting vehicle: {str(e)}")

# Test drive operations
def create_test_drive(test_drive_data):
    if test_drives_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        # Validate required fields
        required_fields = ['user_id', 'vehicle_id', 'booking_date', 'customer_name', 'customer_email']
        for field in required_fields:
            if field not in test_drive_data:
                raise ValueError(f"Missing required field: {field}")
        
        test_drive_data.setdefault('status', 'pending')
        test_drive_data.setdefault('notes', '')
        test_drive_data['created_at'] = datetime.utcnow()
        test_drive_data['updated_at'] = datetime.utcnow()
        
        return test_drives_collection.insert_one(test_drive_data)
    except Exception as e:
        raise Exception(f"Error creating test drive: {str(e)}")

def get_test_drives(filters=None, limit=50):
    if test_drives_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        query = filters or {}
        return list(test_drives_collection.find(query).sort("created_at", DESCENDING).limit(limit))
    except Exception as e:
        raise Exception(f"Error fetching test drives: {str(e)}")

def update_test_drive_status(test_drive_id, status, notes=None):
    if test_drives_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if notes:
            update_data["admin_notes"] = notes
            
        return test_drives_collection.update_one(
            {"_id": ObjectId(test_drive_id)},
            {"$set": update_data}
        )
    except Exception as e:
        raise Exception(f"Error updating test drive: {str(e)}")

# Chat operations
def save_chat_message(message_data):
    if chat_history_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        # Validate required fields
        required_fields = ['session_id', 'message', 'sender']
        for field in required_fields:
            if field not in message_data:
                raise ValueError(f"Missing required field: {field}")
        
        message_data['created_at'] = datetime.utcnow()
        return chat_history_collection.insert_one(message_data)
    except Exception as e:
        raise Exception(f"Error saving chat message: {str(e)}")

def get_chat_history(filters=None, limit=100):
    if chat_history_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        query = filters or {}
        return list(chat_history_collection.find(query).sort("created_at", DESCENDING).limit(limit))
    except Exception as e:
        raise Exception(f"Error fetching chat history: {str(e)}")

# Feedback operations
def save_feedback(feedback_data):
    if feedback_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        # Validate required fields
        required_fields = ['rating', 'comment', 'category']
        for field in required_fields:
            if field not in feedback_data:
                raise ValueError(f"Missing required field: {field}")
        
        feedback_data.setdefault('status', 'active')
        feedback_data['created_at'] = datetime.utcnow()
        return feedback_collection.insert_one(feedback_data)
    except Exception as e:
        raise Exception(f"Error saving feedback: {str(e)}")

def get_feedback(filters=None, limit=100):
    if feedback_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        query = filters or {}
        return list(feedback_collection.find(query).sort("created_at", DESCENDING).limit(limit))
    except Exception as e:
        raise Exception(f"Error fetching feedback: {str(e)}")

# Team member operations
def create_team_member(member_data):
    if team_members_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        # Validate required fields
        required_fields = ['name', 'email', 'role', 'department']
        for field in required_fields:
            if field not in member_data:
                raise ValueError(f"Missing required field: {field}")
        
        member_data.setdefault('status', 'active')
        member_data.setdefault('phone', '')
        member_data.setdefault('hire_date', datetime.utcnow().isoformat())
        member_data['created_at'] = datetime.utcnow()
        member_data['updated_at'] = datetime.utcnow()
        
        return team_members_collection.insert_one(member_data)
    except Exception as e:
        raise Exception(f"Error creating team member: {str(e)}")

def get_team_members(filters=None):
    if team_members_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        query = filters or {}
        return list(team_members_collection.find(query).sort("created_at", DESCENDING))
    except Exception as e:
        raise Exception(f"Error fetching team members: {str(e)}")

def update_team_member(member_id, update_data):
    if team_members_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        update_data['updated_at'] = datetime.utcnow()
        return team_members_collection.update_one(
            {"_id": ObjectId(member_id)},
            {"$set": update_data}
        )
    except Exception as e:
        raise Exception(f"Error updating team member: {str(e)}")

def delete_team_member(member_id):
    if team_members_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        return team_members_collection.delete_one({"_id": ObjectId(member_id)})
    except Exception as e:
        raise Exception(f"Error deleting team member: {str(e)}")

# Financing application operations
def create_financing_application(application_data):
    if financing_applications_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        application_data.setdefault('status', 'pending')
        application_data['created_at'] = datetime.utcnow()
        application_data['updated_at'] = datetime.utcnow()
        
        return financing_applications_collection.insert_one(application_data)
    except Exception as e:
        raise Exception(f"Error creating financing application: {str(e)}")

def get_financing_applications(filters=None):
    if financing_applications_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        query = filters or {}
        return list(financing_applications_collection.find(query).sort("created_at", DESCENDING))
    except Exception as e:
        raise Exception(f"Error fetching financing applications: {str(e)}")

# Vehicle images operations
def add_vehicle_image(vehicle_id, image_data):
    if vehicle_images_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        image_data['vehicle_id'] = vehicle_id
        image_data.setdefault('is_primary', False)
        image_data.setdefault('alt_text', '')
        image_data['created_at'] = datetime.utcnow()
        
        return vehicle_images_collection.insert_one(image_data)
    except Exception as e:
        raise Exception(f"Error adding vehicle image: {str(e)}")

def get_vehicle_images(vehicle_id):
    if vehicle_images_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        return list(vehicle_images_collection.find({"vehicle_id": vehicle_id}).sort("is_primary", DESCENDING))
    except Exception as e:
        raise Exception(f"Error fetching vehicle images: {str(e)}")

# FAQ operations
def create_faq(faq_data):
    if faq_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        faq_data.setdefault('status', 'active')
        faq_data['created_at'] = datetime.utcnow()
        faq_data['updated_at'] = datetime.utcnow()
        
        return faq_collection.insert_one(faq_data)
    except Exception as e:
        raise Exception(f"Error creating FAQ: {str(e)}")

def get_faqs(filters=None):
    if faq_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        query = filters or {'status': 'active'}
        return list(faq_collection.find(query).sort("created_at", DESCENDING))
    except Exception as e:
        raise Exception(f"Error fetching FAQs: {str(e)}")

def update_faq(faq_id, update_data):
    if faq_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        update_data['updated_at'] = datetime.utcnow()
        return faq_collection.update_one(
            {"_id": ObjectId(faq_id)},
            {"$set": update_data}
        )
    except Exception as e:
        raise Exception(f"Error updating FAQ: {str(e)}")

def delete_faq(faq_id):
    if faq_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        return faq_collection.delete_one({"_id": ObjectId(faq_id)})
    except Exception as e:
        raise Exception(f"Error deleting FAQ: {str(e)}")

# Contact info operations
def create_contact_info(contact_data):
    if contact_info_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        contact_data.setdefault('is_active', True)
        contact_data['created_at'] = datetime.utcnow()
        contact_data['updated_at'] = datetime.utcnow()
        
        return contact_info_collection.insert_one(contact_data)
    except Exception as e:
        raise Exception(f"Error creating contact info: {str(e)}")

def get_contact_info(filters=None):
    if contact_info_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        query = filters or {'is_active': True}
        return list(contact_info_collection.find(query).sort("type", ASCENDING))
    except Exception as e:
        raise Exception(f"Error fetching contact info: {str(e)}")

def update_contact_info(contact_id, update_data):
    if contact_info_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        update_data['updated_at'] = datetime.utcnow()
        return contact_info_collection.update_one(
            {"_id": ObjectId(contact_id)},
            {"$set": update_data}
        )
    except Exception as e:
        raise Exception(f"Error updating contact info: {str(e)}")

def delete_contact_info(contact_id):
    if contact_info_collection is None:
        raise Exception("MongoDB connection not available")
    try:
        return contact_info_collection.delete_one({"_id": ObjectId(contact_id)})
    except Exception as e:
        raise Exception(f"Error deleting contact info: {str(e)}")

# Initialize sample data with comprehensive vehicle information
def initialize_sample_data():
    try:
        # Add sample vehicles if none exist
        if vehicles_collection is not None and vehicles_collection.count_documents({}) == 0:
            sample_vehicles = [
                {
                    "make": "BMW",
                    "model": "5 Series",
                    "year": 2023,
                    "price": 58900,
                    "mileage": 1500,
                    "fuel_type": "Hybrid",
                    "transmission": "Automatic",
                    "color": "Alpine White",
                    "image_url": "https://images.pexels.com/photos/892522/pexels-photo-892522.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
                    "featured": True,
                    "description": "Luxury sedan with premium features and excellent fuel economy. Features include leather seats, navigation system, and advanced safety features.",
                    "status": "available",
                    "vin": "WBAJA7C50JCE12345",
                    "engine": "2.0L Turbo Hybrid",
                    "drivetrain": "RWD",
                    "exterior_color": "Alpine White",
                    "interior_color": "Black Leather",
                    "mpg_city": 28,
                    "mpg_highway": 36,
                    "features": ["Navigation", "Leather Seats", "Sunroof", "Backup Camera", "Bluetooth"]
                },
                {
                    "make": "Audi",
                    "model": "Q7",
                    "year": 2023,
                    "price": 62450,
                    "mileage": 2200,
                    "fuel_type": "Gasoline",
                    "transmission": "Automatic",
                    "color": "Mythos Black",
                    "image_url": "https://images.pexels.com/photos/1104768/pexels-photo-1104768.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
                    "featured": True,
                    "description": "Spacious luxury SUV with advanced technology and comfortable interior. Perfect for families who want luxury and practicality.",
                    "status": "available",
                    "vin": "WA1VAAF70JD012345",
                    "engine": "3.0L V6 Turbo",
                    "drivetrain": "AWD",
                    "exterior_color": "Mythos Black",
                    "interior_color": "Beige Leather",
                    "mpg_city": 19,
                    "mpg_highway": 25,
                    "features": ["AWD", "Third Row Seating", "Premium Audio", "Panoramic Sunroof", "Adaptive Cruise Control"]
                },
                {
                    "make": "Tesla",
                    "model": "Model 3",
                    "year": 2023,
                    "price": 46990,
                    "mileage": 800,
                    "fuel_type": "Electric",
                    "transmission": "Automatic",
                    "color": "Pearl White",
                    "image_url": "https://images.pexels.com/photos/7234518/pexels-photo-7234518.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
                    "featured": True,
                    "description": "All-electric sedan with impressive range and cutting-edge technology. Zero emissions and minimal maintenance costs.",
                    "status": "available",
                    "vin": "5YJ3E1EA5JF012345",
                    "engine": "Electric Motor",
                    "drivetrain": "RWD",
                    "exterior_color": "Pearl White",
                    "interior_color": "Black Premium",
                    "range": 358,
                    "charging_time": "8 hours (240V)",
                    "features": ["Autopilot", "Over-the-Air Updates", "Supercharging", "Glass Roof", "Premium Audio"]
                },
                {
                    "make": "Mercedes-Benz",
                    "model": "GLE",
                    "year": 2023,
                    "price": 68750,
                    "mileage": 1800,
                    "fuel_type": "Gasoline",
                    "transmission": "Automatic",
                    "color": "Obsidian Black",
                    "image_url": "https://images.pexels.com/photos/11413034/pexels-photo-11413034.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
                    "featured": True,
                    "description": "Luxury SUV with exceptional build quality and advanced safety features. The perfect blend of performance and comfort.",
                    "status": "available",
                    "vin": "4JGDA5HB5JA012345",
                    "engine": "3.0L V6 Turbo",
                    "drivetrain": "AWD",
                    "exterior_color": "Obsidian Black",
                    "interior_color": "Saddle Brown Leather",
                    "mpg_city": 21,
                    "mpg_highway": 28,
                    "features": ["MBUX Infotainment", "Air Suspension", "Heated/Cooled Seats", "360 Camera", "Wireless Charging"]
                },
                {
                    "make": "Porsche",
                    "model": "Taycan",
                    "year": 2023,
                    "price": 88900,
                    "mileage": 1200,
                    "fuel_type": "Electric",
                    "transmission": "Automatic",
                    "color": "Frozen Blue",
                    "image_url": "https://images.pexels.com/photos/3802510/pexels-photo-3802510.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
                    "featured": True,
                    "description": "High-performance electric sports car with stunning design and thrilling acceleration. Pure Porsche DNA in electric form.",
                    "status": "available",
                    "vin": "WP0ZZZ99ZJS012345",
                    "engine": "Dual Electric Motors",
                    "drivetrain": "AWD",
                    "exterior_color": "Frozen Blue",
                    "interior_color": "Black/Bordeaux Red",
                    "range": 227,
                    "charging_time": "5.5 hours (240V)",
                    "features": ["Sport Chrono", "Air Suspension", "Porsche Communication Management", "Bose Audio", "Sport Seats Plus"]
                },
                {
                    "make": "Lexus",
                    "model": "RX",
                    "year": 2023,
                    "price": 54100,
                    "mileage": 2500,
                    "fuel_type": "Hybrid",
                    "transmission": "Automatic",
                    "color": "Nebula Gray",
                    "image_url": "https://images.pexels.com/photos/7929342/pexels-photo-7929342.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
                    "featured": True,
                    "description": "Refined luxury SUV with excellent reliability and smooth hybrid powertrain. Known for exceptional comfort and quality.",
                    "status": "available",
                    "vin": "2T2BZMCA5JC012345",
                    "engine": "2.5L Hybrid",
                    "drivetrain": "AWD",
                    "exterior_color": "Nebula Gray",
                    "interior_color": "Rioja Red Leather",
                    "mpg_city": 37,
                    "mpg_highway": 34,
                    "features": ["Lexus Safety System+", "Mark Levinson Audio", "Heated/Ventilated Seats", "Head-Up Display", "Wireless Charging"]
                }
            ]
            
            for vehicle in sample_vehicles:
                create_vehicle(vehicle)
            print("Sample vehicles added to database")

        # Add sample team members if none exist
        if team_members_collection is not None and team_members_collection.count_documents({}) == 0:
            sample_members = [
                {
                    "name": "John Doe",
                    "email": "john@ezautos.com",
                    "role": "Sales Manager",
                    "department": "Sales",
                    "phone": "(555) 123-4567",
                    "status": "active",
                    "hire_date": "2020-01-15",
                    "bio": "John has over 10 years of experience in automotive sales and specializes in luxury vehicles."
                },
                {
                    "name": "Jane Smith",
                    "email": "jane@ezautos.com",
                    "role": "Service Advisor",
                    "department": "Service",
                    "phone": "(555) 123-4568",
                    "status": "active",
                    "hire_date": "2019-03-20",
                    "bio": "Jane is our lead service advisor with expertise in all major automotive brands."
                },
                {
                    "name": "Mike Johnson",
                    "email": "mike@ezautos.com",
                    "role": "Finance Manager",
                    "department": "Finance",
                    "phone": "(555) 123-4569",
                    "status": "active",
                    "hire_date": "2021-06-10",
                    "bio": "Mike helps customers find the best financing options for their vehicle purchases."
                }
            ]
            
            for member in sample_members:
                create_team_member(member)
            print("Sample team members added to database")

        # Add sample FAQ data if none exist
        if faq_collection is not None and faq_collection.count_documents({}) == 0:
            sample_faqs = [
                {
                    "question": "What documentation do I need to purchase a vehicle?",
                    "answer": "To purchase a vehicle, you'll need a valid government-issued ID, proof of insurance, and proof of income if financing. Additional documents may be required depending on your payment method.",
                    "category": "Purchasing",
                    "status": "active"
                },
                {
                    "question": "Do you offer vehicle financing?",
                    "answer": "Yes, we offer competitive financing options through our trusted lending partners. You can use our Financial Planner tool to estimate payments and apply for pre-approval.",
                    "category": "Financing",
                    "status": "active"
                },
                {
                    "question": "What is your return policy?",
                    "answer": "We offer a 7-day/500-mile money-back guarantee on all vehicle purchases, allowing you to return the vehicle for a full refund if you're not completely satisfied.",
                    "category": "Policies",
                    "status": "active"
                },
                {
                    "question": "Do you accept trade-ins?",
                    "answer": "Yes, we accept trade-ins and offer fair market value for your vehicle. You can get an instant estimate using our online trade-in calculator.",
                    "category": "Trade-ins",
                    "status": "active"
                },
                {
                    "question": "What warranty options are available?",
                    "answer": "We offer various warranty packages including basic, extended, and comprehensive coverage. All pre-owned vehicles come with a minimum 90-day warranty.",
                    "category": "Warranty",
                    "status": "active"
                },
                {
                    "question": "Can I test drive a vehicle before purchasing?",
                    "answer": "Absolutely! We encourage test drives of any vehicle you're interested in. You can schedule a test drive online or visit our dealership during business hours.",
                    "category": "Test Drive",
                    "status": "active"
                }
            ]
            
            for faq in sample_faqs:
                create_faq(faq)
            print("Sample FAQ data added to database")

        # Add sample contact info if none exist
        if contact_info_collection is not None and contact_info_collection.count_documents({}) == 0:
            sample_contact_info = [
                {
                    "type": "address",
                    "label": "Address",
                    "value": "123 Auto Boulevard, Car City, CC 12345",
                    "icon": "MapPin",
                    "is_active": True
                },
                {
                    "type": "phone",
                    "label": "Phone",
                    "value": "(555) 123-4567",
                    "icon": "Phone",
                    "is_active": True
                },
                {
                    "type": "email",
                    "label": "Email",
                    "value": "info@ezautos.com",
                    "icon": "Mail",
                    "is_active": True
                },
                {
                    "type": "hours",
                    "label": "Business Hours",
                    "value": "Monday - Friday: 9AM - 8PM\nSaturday: 10AM - 6PM\nSunday: 11AM - 5PM",
                    "icon": "Clock",
                    "is_active": True
                }
            ]
            
            for contact in sample_contact_info:
                create_contact_info(contact)
            print("Sample contact info added to database")

    except Exception as e:
        print(f"Error initializing sample data: {str(e)}")

# Initialize sample data when module is imported
initialize_sample_data()