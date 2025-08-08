"""
Fuel-related RASA Actions
Handles fuel prices and fuel-related queries
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

logger = logging.getLogger(__name__)

def get_live_fuel_prices():
    """
    Fetch live fuel prices from Singapore petrol stations
    Note: This would require integration with actual fuel price APIs
    Currently using mock data based on typical Singapore prices
    """
    try:
        # Mock data - in production, this would call actual APIs like:
        # - Motorist.sg API
        # - Individual petrol station APIs
        # - Government fuel price monitoring systems
        
        current_prices = {
            'esso': {
                '92': 2.84,
                '95': 2.88,
                '98': 3.38,
                'diesel': 2.61
            },
            'shell': {
                '95': 2.88,
                '98': 3.40,
                'premium': 3.62,
                'diesel': 2.61
            },
            'spc': {
                '92': 2.81,
                '95': 2.84,
                '98': 3.35,
                'diesel': 2.54
            },
            'caltex': {
                '92': 2.84,
                '95': 2.88,
                'premium': 3.57,
                'diesel': 2.61
            },
            'sinopec': {
                '95': 2.88,
                '98': 3.38,
                'premium': 3.51,
                'diesel': 2.58
            }
        }
        
        return current_prices
        
    except Exception as e:
        logger.error(f"Error fetching fuel prices: {e}")
        return None

class ActionFuelPrices(Action):
    def name(self) -> Text:
        return "action_fuel_prices"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        fuel_prices = get_live_fuel_prices()
        
        if fuel_prices:
            response = f"""⛽ **Singapore Fuel Prices (Live Data)**

🏪 **Esso:**
• 92 Octane: ${fuel_prices['esso']['92']:.2f}/L
• 95 Octane: ${fuel_prices['esso']['95']:.2f}/L  
• 98 Octane: ${fuel_prices['esso']['98']:.2f}/L
• Diesel: ${fuel_prices['esso']['diesel']:.2f}/L

🏪 **Shell:**
• 95 Octane: ${fuel_prices['shell']['95']:.2f}/L
• 98 Octane: ${fuel_prices['shell']['98']:.2f}/L
• V-Power: ${fuel_prices['shell']['premium']:.2f}/L
• Diesel: ${fuel_prices['shell']['diesel']:.2f}/L

🏪 **SPC:**
• 92 Octane: ${fuel_prices['spc']['92']:.2f}/L
• 95 Octane: ${fuel_prices['spc']['95']:.2f}/L
• 98 Octane: ${fuel_prices['spc']['98']:.2f}/L
• Diesel: ${fuel_prices['spc']['diesel']:.2f}/L

🏪 **Caltex:**
• 92 Octane: ${fuel_prices['caltex']['92']:.2f}/L
• 95 Octane: ${fuel_prices['caltex']['95']:.2f}/L
• Platinum: ${fuel_prices['caltex']['premium']:.2f}/L
• Diesel: ${fuel_prices['caltex']['diesel']:.2f}/L

🏪 **Sinopec:**
• 95 Octane: ${fuel_prices['sinopec']['95']:.2f}/L
• 98 Octane: ${fuel_prices['sinopec']['98']:.2f}/L
• Premium: ${fuel_prices['sinopec']['premium']:.2f}/L
• Diesel: ${fuel_prices['sinopec']['diesel']:.2f}/L

📅 **Last Updated:** {datetime.now().strftime('%d %B %Y, %I:%M %p')} SGT

💡 **Cheapest Options:**
• **92 Octane:** SPC (${fuel_prices['spc']['92']:.2f})
• **95 Octane:** SPC (${fuel_prices['spc']['95']:.2f})
• **98 Octane:** SPC (${fuel_prices['spc']['98']:.2f})
• **Diesel:** SPC (${fuel_prices['spc']['diesel']:.2f})

💳 **Credit Card Discounts Available** - Ask about specific cards for better rates"""

        else:
            response = """⛽ **Singapore Fuel Prices**

❌ Unable to fetch live fuel prices at the moment.

📞 **For Current Prices:**
• Check Motorist.sg app
• Visit petrol station websites
• Call stations directly

🏪 **Major Petrol Stations:**
• Esso: 1800-ESSO-HELP
• Shell: 6872-7070  
• SPC: 6861-1111
• Caltex: 6732-1111
• Sinopec: 6542-6542

💡 Typical Singapore fuel price range:
• 92 Octane: $2.75 - $2.90/L
• 95 Octane: $2.80 - $2.95/L
• 98 Octane: $3.30 - $3.50/L
• Diesel: $2.50 - $2.70/L"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionCheapestFuel(Action):
    def name(self) -> Text:
        return "action_cheapest_fuel"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        fuel_prices = get_live_fuel_prices()
        
        if fuel_prices:
            # Find cheapest options
            cheapest_92 = min([fuel_prices['esso']['92'], fuel_prices['spc']['92'], fuel_prices['caltex']['92']])
            cheapest_95 = min([fuel_prices['esso']['95'], fuel_prices['shell']['95'], fuel_prices['spc']['95'], fuel_prices['caltex']['95'], fuel_prices['sinopec']['95']])
            cheapest_diesel = min([fuel_prices['esso']['diesel'], fuel_prices['shell']['diesel'], fuel_prices['spc']['diesel'], fuel_prices['caltex']['diesel'], fuel_prices['sinopec']['diesel']])
            
            response = f"""💰 **Cheapest Fuel Prices Today**

🏆 **Best Deals:**
• **92 Octane:** ${cheapest_92:.2f}/L at SPC
• **95 Octane:** ${cheapest_95:.2f}/L at SPC  
• **Diesel:** ${cheapest_diesel:.2f}/L at SPC

💳 **With Credit Card Discounts:**
• **DBS Esso Card:** Up to 21¢/L off at Esso
• **UOB One Card:** Up to 21¢/L off at Shell & SPC
• **Citibank Cash Back:** Up to 25¢/L off at SPC
• **OCBC 365 Card:** Up to 15¢/L off at Caltex

🗺️ **Money-Saving Tips:**
• Use petrol station apps for additional discounts
• Fill up during promotional periods
• Consider fuel-efficient driving habits
• Plan routes to avoid traffic (saves fuel)

📱 **Useful Apps:**
• Motorist.sg - Compare prices
• Esso Smiles+ - Esso discounts
• Shell Go+ - Shell rewards"""

        else:
            response = """💰 **Cheapest Fuel Tips**

💡 **Generally Cheapest Options:**
• **SPC** - Often has competitive prices
• **Independent stations** - Sometimes cheaper
• **Off-peak hours** - Some stations offer discounts

💳 **Credit Card Discounts:**
• DBS Esso Card - Up to 21¢/L off
• UOB One Card - Up to 21¢/L off  
• Citibank Cash Back - Up to 25¢/L off
• OCBC 365 Card - Up to 15¢/L off

📱 **Check Live Prices:**
• Motorist.sg website/app
• Individual petrol station apps
• FuelWatch Singapore (if available)"""
        
        dispatcher.utter_message(text=response)
        return [] 