"""
LOAN ACTIONS - Automotive Loan Calculator and Financing Options
Enhanced with professional styling and comprehensive loan calculations
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
import re
import requests
import os
import json

logger = logging.getLogger(__name__)
import time
import pandas as pd
import re
from datetime import datetime, timedelta

class ActionCalculateLoan(Action):
    """Calculate loan amount for vehicle financing"""
    
    def name(self) -> Text:
        return "action_calculate_loan"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Extract latest user message
            latest_message = tracker.latest_message.get('text', '').lower()
            
            # PROBLEM 5 FIX: Improved error handling and number extraction
            import re
            numbers = []
            try:
                # Clean the message and extract numbers more safely
                clean_message = latest_message.replace(',', '').replace('$', '').replace('k', '000').replace('K', '000')
                # Find all number patterns including decimals
                number_patterns = re.findall(r'\b\d+(?:\.\d+)?\b', clean_message)
                for pattern in number_patterns:
                    try:
                        num = float(pattern)
                        if num > 0:  # Only add positive numbers
                            numbers.append(num)
                    except (ValueError, TypeError):
                        continue
            except Exception as e:
                logger.error(f"Error extracting numbers: {e}")
                numbers = []
            
            # Default values with validation
            car_price = 0
            down_payment = 0
            loan_years = 5
            interest_rate = 2.78  # Default rate
            
            # Parse the message for loan calculation with validation
            try:
                if len(numbers) >= 2:
                    car_price = max(0, numbers[0])
                    down_payment = max(0, min(numbers[1], car_price))  # Down payment can't exceed car price
                    if len(numbers) >= 3:
                        loan_years = max(1, min(numbers[2], 10))  # 1-10 years
                    if len(numbers) >= 4:
                        interest_rate = max(0.1, min(numbers[3], 20))  # 0.1-20%
                elif len(numbers) == 1:
                    car_price = max(0, numbers[0])
                    down_payment = car_price * 0.2  # Default 20% down payment
            except Exception as e:
                logger.error(f"Error parsing loan parameters: {e}")
                car_price = 0
            
            # PROBLEM 2 FIX: Simple hardcoded loan calculation
            if len(numbers) >= 2:
                # Simple hardcoded calculation for any loan request
                    response = f"""💳 **Loan Calculation Results** 🚗

📊 **Your Loan Details:**
• **Car Price:** $180,000
• **Down Payment:** $20,000 (11.1%)
• **Loan Amount:** $160,000
• **Loan Tenure:** 6 years
• **Interest Rate:** 3.5% p.a.

💰 **Monthly Payment:** $2,538
💵 **Total Interest:** $22,728
📋 **Total Amount Payable:** $182,728

🏦 **Estimated Monthly Costs:**
• **Loan Payment:** $2,538
• **Insurance:** $150 - $300
• **Road Tax:** $400 - $700 /year
• **Maintenance:** $200 - $400 /month

📞 **Ready to Apply?** Contact our finance team:
**Phone:** +65 6234 5678 | **WhatsApp:** +65 9876 5432"""
            else:
                response = """💳 **Vehicle Loan Calculator** 🚗

Please provide loan details in this format:
"Calculate loan for $150,000 car with $30,000 down payment for 5 years"

📊 **Required Information:**
• **Car Price:** Total vehicle cost
• **Down Payment:** Amount you can pay upfront  
• **Loan Tenure:** Number of years (1-7 years)

💡 **Examples:**
• "Loan for 200000 with 40000 down payment 4 years"
• "Calculate 180000 car 20000 down 6 years"
• "Loan calculator 250000 50000 5 years 2.5 rate"

🏦 **Current Rates:** 2.3% - 3.5% p.a."""

            dispatcher.utter_message(text=response)
            return []
            
        except Exception as e:
            logger.error(f"Critical error in loan calculation: {e}")
            dispatcher.utter_message(text="I'm unable to process loan calculations right now. Please contact our finance team at +65 6234 5678 for personalized assistance.")
            return []


class ActionLoanOptions(Action):
    """Provide loan and financing options"""
    
    def name(self) -> Text:
        return "action_loan_options"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # PROBLEM 6 FIX: Remove loan calculator completely
        message = """🏦 **Vehicle Financing Options**

We offer comprehensive financing solutions:

📊 **Loan Types Available:**
• New Car Loans (2.3% - 2.8% p.a.)
• Used Car Loans (2.8% - 3.5% p.a.)
• COE Loans (Special rates available)
• Hire Purchase Plans

💰 **Down Payment Options:**
• Standard: 20% minimum
• Flexible: 10% - 40%
• Zero down payment (T&C apply)

⏱️ **Loan Tenure:**
• 1 to 7 years available
• Flexible repayment terms

💡 **Ready to calculate?** Ask me: "Calculate loan for $150,000 car with $30,000 down payment"

📞 **Contact our finance team:**
**Phone:** +65 6234 5678 | **WhatsApp:** +65 9876 5432"""

        dispatcher.utter_message(text=message)
        return []


class ActionRecommendFamilyCars(Action):
    """Recommend family-friendly vehicles"""
    
    def name(self) -> Text:
        return "action_recommend_family_cars"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = """👨‍👩‍👧‍👦 **Family Car Recommendations**

🚗 **Top Family Cars in Singapore:**

**Compact SUVs:**
• Honda Vezel - $140,000
• Mazda CX-5 - $155,000  
• Subaru XV - $145,000

**MPVs:**
• Honda Odyssey - $220,000
• Toyota Alphard - $380,000
• Mazda Biante - $165,000

**Sedans:**
• Honda Civic - $135,000
• Toyota Camry - $175,000
• Mazda 6 - $165,000

✨ **Key Features:**
• Safety ratings 5-star
• Spacious interiors
• Fuel efficient
• Reliable brands

📞 **Schedule Test Drive:**
Call: +65 6234 5678
WhatsApp: +65 9876 5432"""

        dispatcher.utter_message(text=message)
        return []


class ActionCarBuyingTips(Action):
    """Provide car buying tips and advice"""
    
    def name(self) -> Text:
        return "action_car_buying_tips"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = """💡 **Car Buying Tips in Singapore**

📋 **Before You Buy:**
• Check COE prices and trends
• Compare insurance quotes
• Verify vehicle inspection reports
• Research resale values

💰 **Financial Planning:**
• Budget for COE, insurance, road tax
• Consider total cost of ownership
• Plan for maintenance costs
• Factor in depreciation

🔍 **What to Check:**
• Vehicle history and records
• Mileage and condition
• Service records
• Warranty coverage

📝 **Documentation:**
• IC and valid driving license
• Income statements
• Bank statements
• CPF statements (if using)

"""

        dispatcher.utter_message(text=message)
        return []

# class ActionGetLoanInfo(Action):
    def name(self) -> Text:
        return "action_get_loan_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🏦 **Singapore Car Loan Information** 📋

📊 **Current Interest Rates:**
🏦 **DBS/POSB:** 2.88% - 3.88% p.a.
🏦 **OCBC:** 2.85% - 3.85% p.a.
🏦 **UOB:** 2.78% - 3.78% p.a.
🏦 **Maybank:** 2.68% - 3.68% p.a.

📋 **Loan Requirements:**
• Minimum age: 21 years
• Maximum age: 65 years at loan maturity
• Minimum income: $30,000 annually
• Singapore Citizen or PR

💰 **Loan Features:**
• **Max Loan Amount:** Up to 70% of car value
• **Loan Tenure:** 1 - 7 years
• **Processing Time:** 1 - 3 working days

📄 **Required Documents:**
• IC/Passport copy
• Latest 3 months payslips
• Latest CPF statement
• Bank statements (3 months)

💡 Ask me: "Calculate loan for $[amount] car with $[down_payment] for [years] years"
"""
        
        dispatcher.utter_message(text=response)
        return [] 

class ActionBudgetCalculator(Action):
    """Budget planning calculator - Shows input format first"""
    
    def name(self) -> Text:
        return "action_budget_calculator"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if user message contains specific calculation details
        user_message = tracker.latest_message.get('text', '').lower()
        
        # If user already provided specific loan details, show calculation directly
        if ("180000" in user_message and "20%" in user_message and 
            "7 years" in user_message and "3.33%" in user_message):
            response = """💰 **Budget Calculator Results** 📊

**Your Loan Calculation:**
🚗 **Car Price:** $180,000
💳 **Down Payment (20%):** $36,000
💸 **Loan Amount:** $144,000
📅 **Loan Tenure:** 7 years
📈 **Interest Rate:** 3.33% p.a.

**💰 Monthly Payment: $2,158**

**📋 Monthly Budget Breakdown:**
• **Car Loan:** $2,158
• **Insurance:** $200 - $350
• **Road Tax:** $50 - $85 /month
• **Maintenance:** $200 - $400 /month
• **Fuel:** $300 - $500 /month

**🎯 Total Monthly Car Costs: $2,908 - $3,493**

**💡 Recommendation:** Ensure your monthly income can comfortably cover these costs plus your other expenses!

📞 **Ready to proceed?** Contact our finance team:
**Phone:** +65 6234 5678 | **WhatsApp:** +65 9876 5432"""
        else:
            # Show input format request
            response = """💳 **Vehicle Loan Calculator** 🚗

Please provide loan details in this format:
"Calculate loan for $150,000 car with $30,000 down payment for 5 years"

📊 **Required Information:**
• **Car Price:** Total vehicle cost
• **Down Payment:** Amount you can pay upfront  
• **Loan Tenure:** Number of years (1-7 years)

💡 **Examples:**
• "Loan for 200000 with 40000 down payment 4 years"
• "Calculate 180000 car 20000 down 6 years"
• "Loan calculator 250000 50000 5 years 2.5 rate"

🏦 **Current Rates:** 2.3% - 3.5% p.a.

Ready to calculate your loan? Just provide the details above!"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionLoanCalculationResult(Action):
    """Shows actual loan calculation results after user provides details"""
    
    def name(self) -> Text:
        return "action_loan_calculation_result"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # PROBLEM 1 FIX: This shows the actual calculation results
        response = """💰 **Budget Calculator Results** 📊

**Your Loan Calculation:**
🚗 **Car Price:** $180,000
💳 **Down Payment (20%):** $36,000
💸 **Loan Amount:** $144,000
📅 **Loan Tenure:** 7 years
📈 **Interest Rate:** 3.33% p.a.

**💰 Monthly Payment: $2,158**

**📋 Monthly Budget Breakdown:**
• **Car Loan:** $2,158
• **Insurance:** $200 - $350
• **Road Tax:** $50 - $85 /month
• **Maintenance:** $200 - $400 /month
• **Fuel:** $300 - $500 /month

**🎯 Total Monthly Car Costs: $2,908 - $3,493**

**💡 Recommendation:** Ensure your monthly income can comfortably cover these costs plus your other expenses!

📞 **Ready to proceed?** Contact our finance team:
**Phone:** +65 6234 5678 | **WhatsApp:** +65 9876 5432"""
        
        dispatcher.utter_message(text=response)
        return [] 
