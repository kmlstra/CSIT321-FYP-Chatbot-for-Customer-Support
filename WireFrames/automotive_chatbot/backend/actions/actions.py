from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import random
from pymongo import MongoClient
from datetime import datetime

class ActionGreet(Action):
    def name(self) -> Text:
        return "utter_greet"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(response="utter_greet")
        return []

class ActionGoodbye(Action):
    def name(self) -> Text:
        return "utter_goodbye"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(response="utter_goodbye")
        return []

class ActionCOEPrices(Action):
    def name(self) -> Text:
        return "action_coe_prices"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="Current COE prices:\nCategory A: $92,000\nCategory B: $103,000\nCategory C: $80,000\nCategory E: $105,000")
        return []

class ActionGetVehicleInfo(Action):
    def name(self) -> Text:
        return "action_get_vehicle_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        car_brand = tracker.get_slot("car_brand")
        car_model = tracker.get_slot("car_model")
        if car_brand and car_model:
            dispatcher.utter_message(text=f"{car_brand} {car_model} is a top-rated model in its class. Would you like to schedule a test drive?")
        else:
            dispatcher.utter_message(text="Could you specify the car brand and model you're interested in?")
        return []

class ActionBookTestDrive(Action):
    def name(self) -> Text:
        return "action_book_test_drive"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="✅ Test drive booked! A representative will contact you shortly to confirm details.")
        return []

class ActionGetMaintenanceInfo(Action):
    def name(self) -> Text:
        return "action_get_maintenance_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(response="utter_maintenance")
        return []

class ActionContactUs(Action):
    def name(self) -> Text:
        return "action_contact_us"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="📞 Contact us via:\n• Phone: +65 6123 4567\n• Email: support@clevercompanion.sg\n• WhatsApp: +65 9123 4567")
        return []

class ActionEmailOnly(Action):
    def name(self) -> Text:
        return "action_email_only"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="📧 Email: support@clevercompanion.sg")
        return []

class ActionPhoneOnly(Action):
    def name(self) -> Text:
        return "action_phone_only"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="📞 Phone: +65 6123 4567")
        return []

class ActionWhatsappOnly(Action):
    def name(self) -> Text:
        return "action_whatsapp_only"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="💬 WhatsApp: +65 9123 4567")
        return []

class ActionProvideBusinessHours(Action):
    def name(self) -> Text:
        return "action_provide_business_hours"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="🕒 Business Hours:\nMon–Fri: 9 AM to 7 PM\nSat: 9 AM to 5 PM\nSun & PH: Closed")
        return []

class ActionStoreLocation(Action):
    def name(self) -> Text:
        return "action_store_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="📍 Our showroom is located at 123 Automotive Drive, Singapore 123456.")
        return []

class ActionVehiclePricing(Action):
    def name(self) -> Text:
        return "action_vehicle_pricing"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="Vehicle prices vary. Please provide the make and model for accurate pricing.")
        return []

class ActionLoanCalculationResult(Action):
    def name(self) -> Text:
        return "action_loan_calculation_result"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        # Example response
        dispatcher.utter_message(text="💰 Your estimated monthly loan installment is SGD 940 for a 5-year plan at 2.28% interest.")
        return []

class ActionGetInsuranceInfo(Action):
    def name(self) -> Text:
        return "action_get_insurance_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="🛡️ Insurance options include comprehensive, third-party, and third-party fire & theft. We recommend comprehensive for new vehicles.")
        return []

class ActionGetFuelPrices(Action):
    def name(self) -> Text:
        return "action_get_fuel_prices"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="⛽ Current fuel prices in Singapore:\n• RON 95: $2.75/litre\n• RON 98: $3.10/litre\n• Diesel: $2.50/litre")
        return []

class ActionGetEVInfo(Action):
    def name(self) -> Text:
        return "action_get_ev_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="🔌 EVs are exempted from road tax surcharges till 2025. Top models include Tesla Model 3, Hyundai Ioniq 5, and MG 4 EV.")
        return []

class ActionFeedbackRequest(Action):
    def name(self) -> Text:
        return "action_feedback_request"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="We value your feedback! How was your experience with our assistant or services today?")
        return []

class ActionProcessFeedback(Action):
    def name(self) -> Text:
        return "action_process_feedback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        feedback_text = tracker.latest_message.get("text")
        sender_id = tracker.sender_id

        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client["clever_companion"]
        feedbacks = db["user_feedback"]

        feedbacks.insert_one({
            "sender_id": sender_id,
            "feedback": feedback_text,
            "timestamp": datetime.utcnow()
        })

        dispatcher.utter_message(text="🙏 Thank you! Your feedback has been saved.")
        return []
        
class ActionGetCarReviews(Action):
    def name(self) -> Text:
        return "action_get_car_reviews"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        dispatcher.utter_message(text="Car reviews are available for most models. Please specify the car you're interested in.")
        return []

class ActionShowCarReviews(Action):
    def name(self) -> Text:
        return "action_show_car_reviews"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        car_model = tracker.get_slot("car_model") or "Honda Civic"
        reviews = [
            f"{car_model} offers a smooth ride and great fuel efficiency.",
            f"{car_model} is praised for reliability and low maintenance.",
            f"Users love the comfort and tech features in {car_model}."
        ]
        dispatcher.utter_message(text="\n\n".join(reviews))
        return []

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(response="utter_default")
        return []

