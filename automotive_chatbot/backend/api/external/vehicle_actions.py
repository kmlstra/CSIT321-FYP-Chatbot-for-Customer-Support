"""
Vehicle-related RASA Actions
Handles vehicle information, test drives, maintenance, and recommendations
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
import requests
import os
import json
import time
import pandas as pd
import re
from datetime import datetime, timedelta

def load_vehicle_data():
    """Load vehicle data from Excel file for RAG"""
    try:
        data_path = os.path.join(os.path.dirname(__file__), '../../data/singapore_vehicle_data.xlsx')
        if not os.path.exists(data_path):
            data_path = os.path.join(os.path.dirname(__file__), '../../data/vehicles.xlsx')
        
        if os.path.exists(data_path):
            df = pd.read_excel(data_path)
            return df
        return None
    except Exception as e:
        logging.error(f"Error loading vehicle data: {e}")
        return None

class ActionGetVehicleInfo(Action):
    def name(self) -> Text:
        return "action_get_vehicle_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "")
        brand, model = self.extract_vehicle_details(user_text)
        
        df = load_vehicle_data()
        if df is None:
            response = """❌ **Vehicle Database Temporarily Unavailable**

I'm having trouble accessing our vehicle database right now. 
Please try again later or contact us directly for vehicle information.

📞 **Contact us at:**
• Phone: +65 6234 5678
• WhatsApp: +65 4284 8294
• Email: info@clevercompanion.sg"""
            
            dispatcher.utter_message(text=response)
            return []
        
        if brand and model:
            vehicle_info = self.find_vehicle_in_data(df, brand, model)
            if vehicle_info:
                response = f"""🚗 **{vehicle_info['Brand']} {vehicle_info['Model']}** 📋

**💰 Price Range:** ${vehicle_info.get('Price_Min', 'N/A'):,} - ${vehicle_info.get('Price_Max', 'N/A'):,}
**⛽ Fuel Type:** {vehicle_info.get('Fuel_Type', 'N/A')}
**🚗 Body Type:** {vehicle_info.get('Body_Type', 'N/A')}
**📏 Engine:** {vehicle_info.get('Engine_Size', 'N/A')}L
**💺 Seating:** {vehicle_info.get('Seating_Capacity', 'N/A')} seats

**🔋 Features:**
• {vehicle_info.get('Features', 'Standard automotive features')}

💡 **Interested?** Ask me to "book test drive for {brand} {model}" or about pricing!"""
            else:
                # Show available models for the brand
                models = self.get_brand_models(df, brand)
                if models:
                    response = f"""🚗 **{brand} Models Available** 📋

**Available {brand} models:**
{', '.join(models[:10])}

💡 **Try asking:** "Tell me about {brand} {models[0]}" or "Book test drive for {brand} {models[0]}" """
                else:
                    response =f"""❌ **{brand} Not Found**

I couldn't find information about {brand} vehicles in our database.

**Popular brands we support:**
• Toyota • Honda • BMW • Mercedes • Audi
• Volkswagen • Nissan • Hyundai • Kia • Mazda

💡 **Try asking:** "Tell me about Toyota Camry" or "Show me Honda models" """
        
        elif brand:
            models = self.get_brand_models(df, brand)
            if models:
                response = f"""🚗 **{brand} Vehicle Models** 📋

**Available {brand} models:**
{', '.join(models[:15])}

💡 **For detailed info, ask:** "Tell me about {brand} [model name]"
💡 **To book test drive:** "Book test drive for {brand} [model name]" """
            else:
                response = f"""❌ **{brand} Not Available**

We don't currently have {brand} vehicles in our database.

**Popular brands available:**
• Toyota • Honda • BMW • Mercedes • Audi
• Volkswagen • Nissan • Hyundai • Kia • Mazda"""
        
        else:
            response = """🚗 **Vehicle Information Service** 📋

Please specify the brand and model you're interested in.

**Example queries:**
• "Tell me about Toyota Camry"
• "Show me BMW models"
• "Honda Civic specifications"

**Popular vehicles:**
• Toyota Camry • Honda Civic • BMW 3 Series
• Mercedes C-Class • Audi A4 • Volkswagen Golf

💡 **Need help choosing?** Ask me for "economic car recommendations" """
        
        dispatcher.utter_message(text=response)
        return []

    def extract_vehicle_details(self, text: str) -> tuple:
        """Extract brand and model from user text"""
        try:
            brands = ['toyota', 'honda', 'bmw', 'mercedes', 'audi', 'volkswagen', 'nissan', 'hyundai', 'kia', 'mazda', 'subaru', 'mitsubishi', 'lexus', 'infiniti', 'volvo', 'peugeot', 'renault', 'skoda', 'seat', 'mini']
            
            text_lower = text.lower()
            found_brand = None
            
            for brand in brands:
                if brand in text_lower:
                    found_brand = brand.title()
                    break
            
            if found_brand:
                # Try to extract model (word after brand)
                brand_index = text_lower.find(found_brand.lower())
                after_brand = text[brand_index + len(found_brand):].strip()
                model_match = re.search(r'^[\s]*([A-Za-z0-9\-]+)', after_brand)
                if model_match:
                    model = model_match.group(1).title()
                    return found_brand, model
                else:
                    return found_brand, None
            
            return None, None
            
        except Exception as e:
            logging.error(f"Error extracting vehicle details: {e}")
            return None, None

    def find_vehicle_in_data(self, df, brand, model):
        """Find specific vehicle in dataframe"""
        try:
            if 'Brand' in df.columns and 'Model' in df.columns:
                vehicle = df[(df['Brand'].str.lower() == brand.lower()) & 
                           (df['Model'].str.lower() == model.lower())]
                if not vehicle.empty:
                    return vehicle.iloc[0].to_dict()
            return None
        except Exception as e:
            logging.error(f"Error finding vehicle: {e}")
            return None

    def get_brand_models(self, df, brand):
        """Get all models for a specific brand"""
        try:
            if 'Brand' in df.columns and 'Model' in df.columns:
                brand_vehicles = df[df['Brand'].str.lower() == brand.lower()]
                models = brand_vehicles['Model'].unique().tolist()
                return models[:15]  # Limit to 15 models
            return []
        except Exception as e:
            logging.error(f"Error getting brand models: {e}")
            return []

class ActionBookTestDrive(Action):
    def name(self) -> Text:
        return "action_book_test_drive"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "")
        
        # HARDCODED PROTOTYPE DEMO - Extract booking details from user message
        if "honda civic" in user_text.lower() and "ivan" in user_text.lower() and "sunday" in user_text.lower():
            # This is the prototype demo case - UPDATED WITH ACTUAL DATE
            from datetime import datetime, timedelta
            
            # Calculate next Sunday
            today = datetime.now()
            days_ahead = 6 - today.weekday()  # 6 = Sunday
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_sunday = today + timedelta(days_ahead)
            formatted_date = next_sunday.strftime("%d %B %Y")  # e.g., "23 June 2025"
            
            response = f"""✅ **Test Drive Booking Confirmed** 🚗

📋 **Booking Details:**
• **Customer:** Ivan
• **Vehicle:** Honda Civic
• **Date:** {formatted_date} (Sunday)
• **Time:** 10:00 AM  
• **Contact:** 92474141

📍 **Location:** CleverCompanion Showroom
350 Orchard Road, Shaw House #05-02

📱 **Confirmation:**
We'll send you the confirmation through WhatsApp at 92474141.

✨ **What to bring:**
• Valid Driving License
• NRIC/Passport
• Comfortable shoes for driving

🎯 **See you on {formatted_date} at 10:00 AM, Ivan!**"""
        else:
            response = """📅 **Test Drive Booking** 🚗

**Ready to schedule your test drive!**

**📋 We'll need:**
• Preferred vehicle model
• Your preferred date & time
• Valid driving license
• Contact information

**📞 Book immediately:**
• **Phone:** +65 6234 5678
• **WhatsApp:** +65 4284 8294

**🕐 Available slots:**
• **Weekdays:** 9AM - 7PM
• **Saturday:** 9AM - 6PM
• **Sunday:** 10AM - 5PM

**🚗 Most popular test drives:**
• Toyota Camry • Honda Civic • BMW 3 Series
• Mercedes C-Class • Audi A4

💡 **Quick booking:** Call us now at +65 6234 5678! """
        
        dispatcher.utter_message(text=response)
        return []

# MOVED ActionGetMaintenanceInfo TO maintenance_actions.py - KEEPING THIS PLACEHOLDER FOR REFERENCE

class ActionRecommendEconomicCars(Action):
    def name(self) -> Text:
        return "action_recommend_economic_cars"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """💰 **Economic Car Recommendations** 🚗

**🏆 Top Budget-Friendly Vehicles:**

**🥇 Toyota Vitz (Category A)**
• **Price:** $65,000 - $75,000
• **Fuel:** Excellent (18-20 km/L)
• **Maintenance:** Low cost, reliable

**🥈 Honda Fit (Category A)**
• **Price:** $68,000 - $78,000
• **Fuel:** Very good (16-18 km/L)
• **Features:** Spacious interior

**🥉 Nissan Almera (Category A)**
• **Price:** $70,000 - $80,000
• **Fuel:** Good (15-17 km/L)
• **Warranty:** Comprehensive coverage

**💡 Money-saving tips:**
• Choose Category A vehicles (lower COE)
• Consider certified pre-owned
• Opt for manual transmission
• Look for fuel-efficient models

**📊 Total ownership costs (5 years):**
• Car price + COE + Insurance + Maintenance
• Category A: ~$120,000 - $150,000

💡 **Want details?** Ask about specific models or "calculate loan" for financing!"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionRecommendFamilyCars(Action):
    def name(self) -> Text:
        return "action_recommend_family_cars"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """👨‍👩‍👧‍👦 **Family Car Recommendations** 🚗

**🏆 Top Family-Friendly Vehicles:**

**🥇 Toyota Sienta (7-Seater)**
• **Price:** $118,000 - $130,000
• **Seats:** 7 passengers
• **Fuel:** Hybrid - Excellent efficiency
• **Features:** Sliding doors, flexible seating

**🥈 Honda Vezel (SUV)**
• **Price:** $135,000 - $145,000
• **Type:** Compact SUV
• **Safety:** Honda SENSING suite
• **Features:** High driving position, spacious

**🥉 Mazda CX-5 (SUV)**
• **Price:** $145,000 - $155,000
• **Type:** Mid-size SUV
• **Performance:** SKYACTIV technology
• **Features:** Premium interior, cargo space

**🚙 Honda Odyssey (Premium MPV)**
• **Price:** $185,000 - $200,000
• **Seats:** 8 passengers
• **Features:** Luxury comfort, advanced safety

**💡 Family considerations:**
• Safety ratings and features
• Seating capacity (5, 7, or 8 seats)
• Cargo space for family trips
• Fuel efficiency for daily use
• Easy entry/exit for children

**📊 Running costs comparison:**
• Sienta: Lower fuel & maintenance costs
• Vezel: Balanced performance & economy
• CX-5: Premium features, higher costs

💡 **Need specific details?** Ask about any model or "calculate loan" for financing!"""
        
        dispatcher.utter_message(text=response)
        return [] 

class ActionSearchVehicles(Action):
    def name(self) -> Text:
        return "action_search_vehicles"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # Hardcoded car listings based on Singapore user personas
        car_listings = {
            "budget": [
                {
                    "brand": "Toyota", "model": "Vios", "year": 2020, "price": 78000,
                    "mileage": 45000, "coe_left": "6 years", "fuel_type": "Petrol",
                    "description": "Perfect first car for young professionals"
                },
                {
                    "brand": "Honda", "model": "City", "year": 2019, "price": 82000,
                    "mileage": 52000, "coe_left": "5 years", "fuel_type": "Petrol",
                    "description": "Reliable and fuel-efficient for daily commuting"
                },
                {
                    "brand": "Nissan", "model": "Almera", "year": 2021, "price": 85000,
                    "mileage": 28000, "coe_left": "7 years", "fuel_type": "Petrol",
                    "description": "Modern features at affordable price"
                }
            ],
            "family": [
                {
                    "brand": "Toyota", "model": "Sienta", "year": 2020, "price": 118000,
                    "mileage": 38000, "coe_left": "6 years", "fuel_type": "Hybrid",
                    "description": "7-seater perfect for growing families"
                },
                {
                    "brand": "Honda", "model": "Vezel", "year": 2021, "price": 135000,
                    "mileage": 25000, "coe_left": "7 years", "fuel_type": "Hybrid",
                    "description": "Spacious SUV with excellent safety features"
                },
                {
                    "brand": "Mazda", "model": "CX-5", "year": 2020, "price": 145000,
                    "mileage": 35000, "coe_left": "6 years", "fuel_type": "Petrol",
                    "description": "Premium family SUV with sporty handling"
                }
            ],
            "luxury": [
                {
                    "brand": "BMW", "model": "320i", "year": 2021, "price": 185000,
                    "mileage": 22000, "coe_left": "7 years", "fuel_type": "Petrol",
                    "description": "Executive sedan with dynamic performance"
                },
                {
                    "brand": "Mercedes", "model": "C200", "year": 2020, "price": 195000,
                    "mileage": 28000, "coe_left": "6 years", "fuel_type": "Petrol",
                    "description": "Luxury and comfort combined"
                },
                {
                    "brand": "Audi", "model": "A4", "year": 2021, "price": 178000,
                    "mileage": 20000, "coe_left": "7 years", "fuel_type": "Petrol",
                    "description": "Sophisticated technology and design"
                }
            ],
            "eco": [
                {
                    "brand": "Toyota", "model": "Prius", "year": 2020, "price": 125000,
                    "mileage": 32000, "coe_left": "6 years", "fuel_type": "Hybrid",
                    "description": "Exceptional fuel efficiency and reliability"
                },
                {
                    "brand": "Honda", "model": "Insight", "year": 2021, "price": 132000,
                    "mileage": 18000, "coe_left": "7 years", "fuel_type": "Hybrid",
                    "description": "Eco-friendly with premium features"
                }
            ]
        }
        
        # Determine search category based on user input
        category = self.determine_search_category(user_text)
        
        if category and category in car_listings:
            cars = car_listings[category]
            category_names = {
                "budget": "Budget-Friendly Cars",
                "family": "Family Cars",
                "luxury": "Luxury Cars", 
                "eco": "Eco-Friendly Cars"
            }
            
            response = f"""🚗 **{category_names[category]} Available** 📋

"""
            
            for i, car in enumerate(cars, 1):
                response += f"""**{i}. {car['brand']} {car['model']} ({car['year']})**
💰 **Price:** ${car['price']:,}
📏 **Mileage:** {car['mileage']:,} km
📅 **COE Left:** {car['coe_left']}
⛽ **Fuel:** {car['fuel_type']}
📝 **Description:** {car['description']}

"""
            
            response += """💡 **Interested?** Ask me:
• "Tell me more about [brand] [model]"
• "Book test drive for [brand] [model]"
• "Calculate loan for [brand] [model]"

🎯 **All vehicles are inspected and come with warranty!**"""
            
        else:
            response = """🔍 **Vehicle Search** 🚗

What type of car are you looking for?

**🏷️ By Budget:**
• "Show me budget cars" - Under $90,000
• "Show me mid-range cars" - $90,000 - $150,000
• "Show me luxury cars" - Above $150,000

**👨‍👩‍👧‍👦 By Usage:**
• "Show me family cars" - 7-seaters & SUVs
• "Show me eco-friendly cars" - Hybrids & efficient cars
• "Show me sports cars" - Performance vehicles

**🔧 By Features:**
• "Show me automatic cars"
• "Show me hybrid cars"
• "Show me SUVs"

What would you like to see? 🚗"""
        
        dispatcher.utter_message(text=response)
        return []
    
    def determine_search_category(self, text: str) -> str:
        """Determine which category of cars user is looking for"""
        
        if any(word in text for word in ['budget', 'cheap', 'affordable', 'under 90']):
            return "budget"
        elif any(word in text for word in ['family', '7 seat', 'suv', 'mpv', 'kids']):
            return "family"
        elif any(word in text for word in ['luxury', 'premium', 'bmw', 'mercedes', 'audi', 'expensive']):
            return "luxury"
        elif any(word in text for word in ['eco', 'hybrid', 'fuel efficient', 'green', 'environment']):
            return "eco"
        elif any(word in text for word in ['mid range', 'medium', '100k', '120k']):
            return "family"  # Default mid-range to family cars
        
        return None 

class ActionPersonaBasedRecommendations(Action):
    """Provide vehicle recommendations based on user personas - PROTOTYPE DEMO"""
    
    def name(self) -> Text:
        return "action_persona_based_recommendations"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # PERSONA 1: Young Professional (Budget-conscious, first car) - ENHANCED REALISTIC TRIGGERS
        if ("young professional" in user_text or "first car" in user_text or "budget conscious" in user_text or
            "fresh graduate" in user_text or "just started working" in user_text or "entry level" in user_text or
            "affordable reliable" in user_text or "good fuel economy" in user_text or "low maintenance" in user_text):
            response = """👔 **Young Professional Vehicle Recommendations** 💼

**🎯 Perfect matches for your lifestyle:**

**1. Honda Civic 1.6L** 
• **Price:** $135,000 - $145,000
• **Fuel Efficiency:** 16.5 km/L
• **Why Perfect:** Reliable, fuel-efficient, great resale value
• **Features:** Auto headlights, keyless entry, 7" touchscreen

**2. Toyota Corolla Altis 1.6L**
• **Price:** $130,000 - $140,000  
• **Fuel Efficiency:** 17.2 km/L
• **Why Perfect:** Low maintenance, proven reliability, affordable insurance
• **Features:** Toyota Safety Sense, CVT transmission, spacious boot

**3. Hyundai Avante 1.6L**
• **Price:** $125,000 - $135,000
• **Fuel Efficiency:** 16.8 km/L  
• **Why Perfect:** Best value for money, modern tech, 10-year warranty
• **Features:** 8" infotainment, wireless charging, smart key

💡 **Your Profile:** Budget-conscious, reliable transport, low running costs
📊 **Estimated Monthly Costs:** $800-1,200 (loan + insurance + maintenance)"""

        # PERSONA 2: Family-oriented (Safety, space, practical) - ENHANCED REALISTIC TRIGGERS  
        elif ("family oriented" in user_text or "family car" in user_text or "kids" in user_text or "children" in user_text or
              "safety features" in user_text or "7 seater" in user_text or "spacious" in user_text or "suv" in user_text or
              "mpv" in user_text or "child safety" in user_text or "school runs" in user_text or "weekend trips" in user_text):
            response = """👨‍👩‍👧‍👦 **Family-Oriented Vehicle Recommendations** 🚗

**🎯 Perfect matches for your family needs:**

**1. Honda Vezel 1.5L Hybrid**
• **Price:** $165,000 - $175,000
• **Safety:** 5-star NCAP rating
• **Why Perfect:** Spacious cabin, high seating position, excellent safety
• **Features:** Honda SENSING suite, electric tailgate, premium audio

**2. Toyota Sienta 1.5L (7-seater)**
• **Price:** $145,000 - $155,000
• **Safety:** Pre-collision system, lane assist
• **Why Perfect:** 7 seats, sliding doors, child-friendly features  
• **Features:** Dual power sliding doors, 3rd row seating, multiple cup holders

**3. Mazda CX-5 2.0L**
• **Price:** $175,000 - $185,000
• **Safety:** Top Safety Pick+ award
• **Why Perfect:** Premium interior, smooth ride, advanced safety tech
• **Features:** i-ACTIVSENSE safety, BOSE audio, power liftgate

💡 **Your Profile:** Safety-first, space for family, practical features
📊 **Estimated Monthly Costs:** $1,200-1,600 (loan + insurance + maintenance)"""

        # PERSONA 3: Luxury enthusiast (Performance, premium features, status) - ENHANCED REALISTIC TRIGGERS
        elif ("luxury enthusiast" in user_text or "premium" in user_text or "luxury" in user_text or "performance" in user_text or
              "bmw" in user_text or "mercedes" in user_text or "audi" in user_text or "executive" in user_text or
              "status symbol" in user_text or "prestige" in user_text or "comfort features" in user_text or "high end" in user_text):
            response = """🏆 **Luxury Enthusiast Vehicle Recommendations** ✨

**🎯 Perfect matches for your refined taste:**

**1. BMW 320i M Sport**
• **Price:** $245,000 - $265,000
• **Performance:** 184hp, 0-100km/h in 7.1s
• **Why Perfect:** Dynamic handling, premium interior, prestigious badge
• **Features:** M Sport package, Harman Kardon audio, gesture control

**2. Mercedes-Benz C200 AMG Line**
• **Price:** $235,000 - $255,000
• **Performance:** 184hp turbo engine, 9G-Tronic transmission
• **Why Perfect:** Elegant design, advanced tech, superior comfort
• **Features:** MBUX infotainment, ambient lighting, memory seats

**3. Audi A4 S Line 2.0 TFSI**
• **Price:** $240,000 - $260,000
• **Performance:** 190hp, Quattro AWD available
• **Why Perfect:** Sophisticated interior, cutting-edge tech, smooth performance
• **Features:** Virtual cockpit, MMI touch, S line styling

💡 **Your Profile:** Performance & luxury focused, premium features, status symbol
📊 **Estimated Monthly Costs:** $1,800-2,400 (loan + insurance + maintenance)"""

        else:
            # Default recommendation prompt
            response = """🎯 **Personalized Vehicle Recommendations** 🚗

**Tell me about your lifestyle for personalized recommendations:**

**👔 Try saying:** "I'm a fresh graduate just started working, need something affordable and reliable with good fuel economy"

**👨‍👩‍👧‍👦 Try saying:** "I have kids and need a spacious car with safety features for school runs and weekend trips"

**🏆 Try saying:** "I want a luxury car with premium comfort features as an executive status symbol"

I'll provide 3 tailored vehicle recommendations with detailed specifications, pricing, and why they're perfect for your needs!

💡 **Each recommendation includes:**
• Exact pricing and monthly costs
• Key features that match your lifestyle  
• Detailed specifications
• Why it's perfect for your persona"""

        dispatcher.utter_message(text=response)
        return [] 
