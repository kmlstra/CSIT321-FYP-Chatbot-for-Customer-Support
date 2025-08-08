"""
Maintenance-related RASA Actions
Handles vehicle maintenance tips, guides, and schedules
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
import re

logger = logging.getLogger(__name__)

class ActionMaintenanceGuide(Action):
    def name(self) -> Text:
        return "action_maintenance_guide"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🔧 **Singapore Vehicle Maintenance Guide**

🔧 **Available Guides:**

• 🛞 **Tires:** Complete changing guide, pressure checks
• 🔧 **Engine:** Oil changes, air filter, spark plugs
• 🛑 **Brakes:** Pad inspection, fluid checks
• 🔋 **Electrical:** Battery maintenance, lighting
• 💧 **Fluids:** Coolant, transmission, power steering
• 🌬️ **Filters:** Cabin and engine air filters

💡 **Ask specifically about any task!**

Examples:
• "How to change tire?"
• "Oil change steps"
• "Battery maintenance"

🔧 **Popular maintenance searches:**
• Tire pressure check
• Engine oil replacement
• Brake pad inspection
• Battery terminals cleaning
• Air filter replacement
• Coolant level check"""

        dispatcher.utter_message(text=response)
        return []

class ActionTireMaintenance(Action):
    def name(self) -> Text:
        return "action_tire_maintenance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🛞 **Complete Tire Maintenance Guide** 🚗

**🔧 Tire Changing Steps:**
1. Park on flat, stable surface
2. Engage parking brake
3. Loosen lug nuts (don't remove yet)
4. Jack up vehicle safely
5. Remove lug nuts completely
6. Pull tire straight toward you
7. Align new tire with bolts
8. Replace lug nuts hand-tight
9. Lower vehicle slightly
10. Tighten lug nuts in star pattern
11. Lower vehicle completely
12. Final tightening check

**📏 Pressure Checks:**
• Check monthly when tires are cold
• Singapore recommended: 32-35 PSI
• Use quality pressure gauge
• Don't forget spare tire

**⚠️ Safety Tips:**
• Never work under vehicle supported only by jack
• Use wheel chocks on opposite end
• Keep lug wrench and jack in good condition

**🔍 When to Replace:**
• Tread depth less than 1.6mm
• Visible cords or bulges
• Age over 6 years (regardless of wear)"""

        dispatcher.utter_message(text=response)
        return []

class ActionEngineMaintenance(Action):
    def name(self) -> Text:
        return "action_engine_maintenance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🔧 **Engine Maintenance Guide** ⚙️

**🛢️ Oil Change Steps:**
1. Warm engine (drive 2-3 minutes)
2. Park on level surface
3. Locate oil drain plug
4. Remove drain plug with wrench
5. Drain oil completely (15-20 mins)
6. Replace drain plug with new gasket
7. Remove old oil filter
8. Apply thin oil film to new filter gasket
9. Install new filter hand-tight + 3/4 turn
10. Add new oil through filler cap
11. Check level with dipstick
12. Run engine, check for leaks

**🌬️ Air Filter Replacement:**
• Check every 12,000km
• Replace if dirty/clogged
• Clean housing before installing new filter

**⚡ Spark Plugs:**
• Replace every 30,000-50,000km
• Check gap specification
• Use torque wrench for installation

**📅 Singapore Schedule:**
• Oil change: Every 10,000km or 6 months
• Air filter: Every 20,000km
• Spark plugs: Every 40,000km"""

        dispatcher.utter_message(text=response)
        return []

class ActionBrakeMaintenance(Action):
    def name(self) -> Text:
        return "action_brake_maintenance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🛑 **Brake System Maintenance** 🚗

**🔍 Brake Pad Inspection:**
1. Remove wheel for visual inspection
2. Check pad thickness through caliper
3. Look for uneven wear patterns
4. Check for metal-on-metal contact

**⚠️ Warning Signs:**
• Squealing or grinding noise
• Vibration when braking
• Brake pedal feels soft/spongy
• Car pulls to one side when braking

**💧 Brake Fluid Checks:**
• Check level monthly
• Fluid should be clear/light amber
• Replace every 2 years in Singapore humidity
• Never let reservoir run dry

**🔧 Maintenance Schedule:**
• Brake pads: Every 25,000-40,000km
• Brake fluid: Every 2 years
• Brake inspection: Every 6 months

**🚨 Safety Notes:**
• Never ignore brake warning sounds
• Professional service recommended for major brake work
• Test brakes after any maintenance"""

        dispatcher.utter_message(text=response)
        return []

class ActionElectricalMaintenance(Action):
    def name(self) -> Text:
        return "action_electrical_maintenance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🔋 **Electrical System Maintenance** ⚡

**🔋 Battery Maintenance:**
1. Clean terminals monthly
2. Check electrolyte level (non-sealed batteries)
3. Test voltage regularly (12.6V when off)
4. Check mounting brackets for tightness

**🧹 Terminal Cleaning:**
1. Disconnect negative terminal first
2. Mix baking soda with water
3. Scrub terminals with old toothbrush
4. Rinse with clean water
5. Dry completely
6. Apply petroleum jelly to terminals
7. Reconnect positive first, then negative

**💡 Lighting System:**
• Check all lights monthly
• Replace bulbs in pairs for even lighting
• Clean headlight lenses regularly

**🔌 Signs of Electrical Problems:**
• Dim headlights
• Slow engine cranking
• Dashboard warning lights
• Battery terminals corroded

**🔧 Singapore Climate Tips:**
• High humidity accelerates corrosion
• Check connections every 3 months
• Keep battery terminals clean and dry"""

        dispatcher.utter_message(text=response)
        return []

class ActionFluidMaintenance(Action):
    def name(self) -> Text:
        return "action_fluid_maintenance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """💧 **Vehicle Fluids Maintenance** 🚗

**🌡️ Coolant System:**
• Check level when engine is cold
• Mix should be 50/50 coolant/water
• Replace every 2 years in Singapore
• Look for leaks under parked car

**⚙️ Transmission Fluid:**
• Check with engine running, transmission warm
• Fluid should be red and clean
• Replace per manufacturer schedule
• Never overfill - can cause damage

**🔄 Power Steering Fluid:**
• Check level monthly
• Should be clear/light colored
• Top up with manufacturer-specified fluid
• Leaks often indicate worn seals

**🔧 Maintenance Schedule:**
• Engine oil: Every 10,000km
• Coolant: Every 2 years
• Transmission: Every 60,000km
• Power steering: Check monthly
• Brake fluid: Every 2 years

**⚠️ Warning Signs:**
• Colored spots under parked car
• Low fluid warning lights
• Unusual noises from systems
• Overheating or poor performance"""

        dispatcher.utter_message(text=response)
        return []

class ActionFilterMaintenance(Action):
    def name(self) -> Text:
        return "action_filter_maintenance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🌬️ **Filter Maintenance Guide** 🔧

**🌬️ Cabin Air Filter:**
1. Locate filter housing (usually behind glove box)
2. Remove glove box or access panel
3. Slide out old filter
4. Note airflow direction arrow
5. Install new filter matching direction
6. Reassemble access panels

**🔧 Engine Air Filter:**
1. Open air filter housing
2. Remove old filter element
3. Clean housing with damp cloth
4. Check for debris in intake tube
5. Install new filter
6. Ensure housing seals properly

**📅 Replacement Schedule:**
• Cabin filter: Every 15,000km or 12 months
• Engine filter: Every 20,000km
• More frequent in dusty conditions

**🌪️ Singapore Considerations:**
• High humidity and pollution
• Replace cabin filter more frequently
• Check filters during haze season

**💡 Benefits:**
• Better air quality inside car
• Improved engine performance
• Better fuel efficiency
• Reduced allergens"""

        dispatcher.utter_message(text=response)
        return []

class ActionGetMaintenanceInfo(Action):
    """MOVED FROM vehicle_actions.py - Main maintenance info action"""
    
    def name(self) -> Text:
        return "action_get_maintenance_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # Check for tire-related queries
        if any(keyword in user_text for keyword in ['tire', 'tyre', 'flat', 'change']):
            response = """🔧 **Complete Tire Changing Guide** 🛞

**Step-by-Step Process:**

**1. Safety First** 🚨
• Park on level ground away from traffic
• Turn on hazard lights and apply parking brake
• Place wheel chocks behind opposite wheels

**2. Preparation** 🛠️
• Remove spare tire, jack, and lug wrench from boot
• Loosen lug nuts (don't remove completely yet)
• Locate proper jack point under vehicle

**3. Lifting Vehicle** ⬆️
• Position jack securely under lift point
• Raise vehicle until tire is 6 inches off ground
• **Never put body under lifted vehicle**

**4. Removing Flat Tire** 🔧
• Fully remove loosened lug nuts (keep them safe)
• Pull tire straight toward you to remove
• Set flat tire aside safely

**5. Installing Spare** 🔄
• Align spare tire with wheel bolts
• Replace lug nuts and hand-tighten first
• Tighten in star/cross pattern with wrench

**6. Final Steps** ✅
• Lower vehicle until tire touches ground
• Fully tighten nuts in star pattern
• Lower completely and remove jack
• Check spare tire pressure
• Store flat tire and tools in boot

**💡 Safety Tips:**
• Spare tires are temporary - Max 80 km/h speed
• Get permanent replacement ASAP
• If on highway, call roadside assistance (+65 6748 9911)
• Keep emergency kit: reflective triangle, torch, gloves

**🚗 Singapore Specific:**
• Emergency services: 995 (Police), 1777 (24hr breakdown)
• Most service centers open 24/7 on major highways"""
        
        else:
            response = """🔧 **Singapore Vehicle Maintenance Guide**

🛠️ **Available Guides:**
• 🛞 **Tires:** Complete changing guide, pressure checks
• 🛢️ **Engine:** Oil changes, air filter, spark plugs
• 🛑 **Brakes:** Pad inspection, fluid checks
• 🔋 **Electrical:** Battery maintenance, lighting
• 💧 **Fluids:** Coolant, transmission, power steering
• 🌪️ **Filters:** Cabin and engine air filters

💡 **Ask specifically about any task!**
Examples:
• "How to change tire?"
• "Oil change steps"
• "Battery maintenance"

🚗 All guides tailored for Singapore's climate!"""
        
        dispatcher.utter_message(text=response)
        return [] 