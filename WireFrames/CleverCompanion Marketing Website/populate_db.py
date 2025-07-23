#!/usr/bin/env python3
import pymongo
import urllib.parse
from datetime import datetime
import bcrypt

# MongoDB connection - URL encode the password properly
password = "P@ssw0rd!1"
encoded_password = urllib.parse.quote_plus(password)
MONGODB_URI = f"mongodb+srv://darknesscrawler:{encoded_password}@marketing.agcqpdr.mongodb.net/?retryWrites=true&w=majority&appName=Marketing"

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def populate_database():
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGODB_URI)
        db = client.marketing  # Use 'marketing' as the database name
        
        print("Connected to MongoDB successfully!")
        
        # Clear existing data
        collections = ['users', 'testimonials', 'faqs', 'contacts', 'pricings']
        for collection in collections:
            db[collection].delete_many({})
            print(f"Cleared {collection} collection")
        
        # Create admin user
        admin_user = {
            "username": "admin",
            "email": "admin@clevercompanion.com",
            "password": hash_password("admin123"),
            "role": "admin",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        db.users.insert_one(admin_user)
        print("Created admin user (email: admin@clevercompanion.com, password: admin123)")
        
        # Sample testimonials
        testimonials = [
            {
                "quote": "CleverCompanion has completely transformed how we engage with potential customers. Our lead conversion rate has increased by 35% since implementation.",
                "author": "Michael Chen",
                "position": "General Manager, Parkway Auto Group",
                "avatar": "https://randomuser.me/api/portraits/men/32.jpg",
                "rating": 5,
                "isActive": True,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "quote": "The AI chatbot handles routine inquiries so well that our sales team can focus on high-value activities. It's like having a tireless employee working 24/7.",
                "author": "Sarah Johnson",
                "position": "Digital Marketing Director, Liberty Motors",
                "avatar": "https://randomuser.me/api/portraits/women/44.jpg",
                "rating": 5,
                "isActive": True,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "quote": "Our customers love getting instant answers about vehicle specs and financing options. CleverCompanion has significantly improved our customer satisfaction scores.",
                "author": "David Rodriguez",
                "position": "Customer Experience Manager, Horizon Automotive",
                "avatar": "https://randomuser.me/api/portraits/men/67.jpg",
                "rating": 5,
                "isActive": True,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "quote": "The integration with our inventory system was seamless. Customers get real-time information about vehicle availability, which has reduced our response time significantly.",
                "author": "Jennifer Martinez",
                "position": "IT Director, Premier Auto Sales",
                "avatar": "https://randomuser.me/api/portraits/women/28.jpg",
                "rating": 4,
                "isActive": True,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "quote": "CleverCompanion's analytics dashboard gives us incredible insights into customer behavior. We can now optimize our sales process based on real data.",
                "author": "Robert Thompson",
                "position": "Sales Manager, Elite Motors",
                "avatar": "https://randomuser.me/api/portraits/men/45.jpg",
                "rating": 5,
                "isActive": True,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
        ]
        db.testimonials.insert_many(testimonials)
        print(f"Inserted {len(testimonials)} testimonials")
        
        # Sample FAQs
        faqs = [
            # Getting Started
            {
                "question": "How do I sign up for CleverCompanion?",
                "answer": "Signing up for CleverCompanion is easy. Simply click the 'Get Started' button on our homepage, fill out the registration form, and follow the instructions to set up your account. Our onboarding team will reach out within 24 hours to guide you through the setup process.",
                "category": "Getting Started",
                "isActive": True,
                "order": 1,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "question": "How long does it take to implement CleverCompanion?",
                "answer": "Most dealerships can be fully set up within 24-48 hours. This includes connecting your inventory, customizing chatbot responses, and integrating with your website. Our implementation specialists will work with you to ensure a smooth setup process.",
                "category": "Getting Started",
                "isActive": True,
                "order": 2,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "question": "Do I need technical knowledge to use CleverCompanion?",
                "answer": "No technical knowledge is required. Our platform is designed to be user-friendly, and our setup team handles all technical aspects of implementation. You'll receive comprehensive training on how to use the dashboard and manage your settings.",
                "category": "Getting Started",
                "isActive": True,
                "order": 3,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            # Features & Functionality
            {
                "question": "What languages does the chatbot support?",
                "answer": "CleverCompanion currently supports English, Spanish, French, and German. Additional languages can be added for Enterprise customers upon request.",
                "category": "Features & Functionality",
                "isActive": True,
                "order": 1,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "question": "Can CleverCompanion integrate with our existing inventory system?",
                "answer": "Yes, CleverCompanion integrates with most major automotive inventory management systems including vAuto, DealerTrack, CDK, Reynolds & Reynolds, and many others. If you use a custom system, our team can work with you on a custom integration.",
                "category": "Features & Functionality",
                "isActive": True,
                "order": 2,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            # Billing & Subscriptions
            {
                "question": "What payment methods do you accept?",
                "answer": "We accept all major credit cards (Visa, MasterCard, American Express, Discover) as well as ACH bank transfers for annual subscriptions.",
                "category": "Billing & Subscriptions",
                "isActive": True,
                "order": 1,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "question": "Is there a contract or commitment?",
                "answer": "We offer monthly and annual billing options. While annual plans provide a 20% discount, there's no long-term contract required. You can cancel your subscription at any time.",
                "category": "Billing & Subscriptions",
                "isActive": True,
                "order": 2,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
        ]
        db.faqs.insert_many(faqs)
        print(f"Inserted {len(faqs)} FAQs")
        
        # Contact information
        contact = {
            "phone": {
                "sales": "(800) 123-4567",
                "support": "(800) 765-4321"
            },
            "email": {
                "sales": "sales@clevercompanion.com",
                "support": "support@clevercompanion.com"
            },
            "address": {
                "street": "123 Tech Boulevard, Suite 456",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105"
            },
            "socialMedia": {
                "facebook": "https://facebook.com/clevercompanion",
                "twitter": "https://twitter.com/clevercompanion",
                "linkedin": "https://linkedin.com/company/clevercompanion",
                "instagram": "https://instagram.com/clevercompanion"
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        db.contacts.insert_one(contact)
        print("Inserted contact information")
        
        # Pricing plan
        pricing = {
            "planName": "Complete Plan",
            "price": 299,
            "currency": "USD",
            "billingPeriod": "monthly",
            "features": [
                "Smart Customer Engagement",
                "24/7 Automated Support",
                "Seamless Live Agent Handoff",
                "Test Drive Bookings",
                "Real-Time Notifications",
                "Loan Calculator",
                "Chatbot Customization",
                "Chat History & Analytics",
                "CRM Integration"
            ],
            "isActive": True,
            "isPopular": True,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        db.pricings.insert_one(pricing)
        print("Inserted pricing plan")
        
        print("\nDatabase populated successfully!")
        print("Admin login credentials:")
        print("Email: admin@clevercompanion.com")
        print("Password: admin123")
        
        client.close()
        
    except Exception as e:
        print(f"Error populating database: {e}")

if __name__ == "__main__":
    populate_database()