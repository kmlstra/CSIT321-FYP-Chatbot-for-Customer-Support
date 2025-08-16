from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from api.cache.client_cache import get_client_cache
from api.cache.feature_cache_manager import check_loan_calculator_feature_enabled
import re
import logging

logger = logging.getLogger(__name__)



class ActionLoanCalculator(Action):
    """Simple and user-friendly loan calculator"""
    
    def name(self) -> Text:
        return "action_loan_calculator"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if loan calculator feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_loan_calculator_feature_enabled(client_id):
            dispatcher.utter_message(text="I'm sorry, but the loan calculator feature is not available at the moment. Please contact our support team for assistance with financing inquiries.")
            return []
        
        user_message = tracker.latest_message.get('text', '').lower()
        current_intent = tracker.latest_message.get('intent', {}).get('name')
        
        # Check if this is actually a loan calculation request
        if not self._is_loan_related(user_message, current_intent):
            dispatcher.utter_message(text="I'm not sure what you're looking for. Could you please clarify your request?")
            return []
        
        # Check if user is asking for help or general loan calculator info
        if self._is_help_request(user_message) or self._is_welcome_request(user_message):
            self._show_calculator_help(dispatcher)
            return []
        
        # Try to extract loan parameters
        loan_params = self._extract_loan_parameters(user_message)
        
        if not loan_params:
            self._show_input_format(dispatcher)
            return []
        
        # Calculate and display results
        try:
            result = self._calculate_loan(loan_params)
            self._display_results(dispatcher, loan_params, result)
        except Exception:
            dispatcher.utter_message(text="Sorry, there was an error calculating your loan. Please check your inputs and try again.")
        
        return []
    
    def _is_loan_related(self, text: str, intent: str) -> bool:
        """Check if the request is actually about loan calculation"""
        # If intent is specifically calculate_loan, it's valid
        if intent == 'calculate_loan':
            return True
        
        # Check for loan-related keywords
        loan_keywords = [
            'loan', 'calculate', 'financing', 'payment', 'interest', 'borrow',
            'monthly payment', 'car loan', 'auto loan', 'finance'
        ]
        
        # Check for appointment-related keywords that should NOT trigger loan calculator
        appointment_keywords = [
            'appointment', 'booking', 'schedule', 'book', 'cancel', 'reschedule',
            'time slot', 'available', 'service', 'test drive', 'consultation'
        ]
        
        # Check for phone-related keywords that should NOT trigger loan calculator
        phone_keywords = [
            'phone', 'number', 'contact', 'call', 'mobile', 'telephone'
        ]
        
        # If it contains appointment or phone keywords, it's not a loan request
        if any(keyword in text for keyword in appointment_keywords + phone_keywords):
            return False
        
        # If it contains loan keywords, it might be a loan request
        has_loan_keywords = any(keyword in text for keyword in loan_keywords)
        
        # Also check if there are numbers that could be loan parameters
        numbers = re.findall(r'\d+(?:\.\d+)?', text.replace(',', ' '))
        has_multiple_numbers = len(numbers) >= 2
        
        return has_loan_keywords or has_multiple_numbers
    
    def _is_help_request(self, text: str) -> bool:
        """Check if user is asking for help"""
        help_keywords = ['help', 'how to use', 'calculator', 'how do i', 'can you help']
        return any(keyword in text for keyword in help_keywords) and not any(char.isdigit() for char in text)
    
    def _is_welcome_request(self, text: str) -> bool:
        """Check if this is a general loan calculator request without specific parameters"""
        welcome_phrases = [
            'calculate car loan with current interest rates',
            'loan calculator',
            'car loan calculator',
            'i want to calculate my car loan',
            'calculate loan',
            'financing options'
        ]
        # Check if it's a general request without specific numbers
        is_general_request = any(phrase in text for phrase in welcome_phrases)
        has_specific_numbers = len([x for x in text.split() if x.replace('.', '').replace(',', '').isdigit()]) >= 3
        return is_general_request and not has_specific_numbers
    
    def _show_calculator_help(self, dispatcher: CollectingDispatcher) -> None:
        """Show loan calculator help information"""
        response = """🧮 **Car Loan Calculator**

I can help you calculate your monthly car loan payments! 

📝 **How to use:**
Just tell me these 4 details in any order:
• Car price
• Down payment amount
• Loan period (years)
• Interest rate (%)

💡 **Example:**
"Calculate loan for car price 80000, down payment 20000, 7 years, 3.5% interest"

🔢 **Simple format:**
"80000, 20000, 7, 3.5"

Try it now! 🚗💰"""
        dispatcher.utter_message(text=response)
    
    def _extract_loan_parameters(self, text: str) -> Optional[dict[str, float]]:
        """Extract loan parameters from user input"""
        # Try simple comma-separated format first
        numbers = re.findall(r'\d+(?:\.\d+)?', text.replace(',', ' '))
        
        if len(numbers) >= 4:
            try:
                return {
                    'car_price': float(numbers[0]),
                    'down_payment': float(numbers[1]),
                    'loan_years': float(numbers[2]),
                    'interest_rate': float(numbers[3])
                }
            except ValueError:
                pass
        
        # Try extracting from natural language
        car_price = self._extract_number_near_keywords(text, ['price', 'cost', 'car'])
        down_payment = self._extract_number_near_keywords(text, ['down', 'deposit', 'upfront'])
        loan_years = self._extract_number_near_keywords(text, ['year', 'period', 'term'])
        interest_rate = self._extract_number_near_keywords(text, ['interest', 'rate', '%'])
        
        # Only return a dictionary if all values are successfully extracted
        if all(param is not None for param in [car_price, down_payment, loan_years, interest_rate]):
            # Type assertion: we know these are not None due to the check above
            assert car_price is not None
            assert down_payment is not None
            assert loan_years is not None
            assert interest_rate is not None
            
            return {
                'car_price': car_price,
                'down_payment': down_payment,
                'loan_years': loan_years,
                'interest_rate': interest_rate
            }
        
        return None
    
    def _extract_number_near_keywords(self, text: str, keywords: List[str]) -> Optional[float]:
        """Extract number near specific keywords"""
        for keyword in keywords:
            # Look for number before or after keyword
            patterns = [
                rf'{keyword}\s*(\d+(?:\.\d+)?)',
                rf'(\d+(?:\.\d+)?)\s*{keyword}',
                rf'{keyword}\s*:?\s*(\d+(?:\.\d+)?)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        continue
        return None
    
    def _calculate_loan(self, params: Dict[str, float]) -> Dict[str, float]:
        """Calculate loan details"""
        car_price = params['car_price']
        down_payment = params['down_payment']
        loan_years = params['loan_years']
        interest_rate = params['interest_rate']
        
        # Validate inputs
        if down_payment >= car_price:
            raise ValueError("Down payment cannot be greater than or equal to car price")
        
        if loan_years <= 0 or interest_rate < 0:
            raise ValueError("Invalid loan years or interest rate")
        
        loan_amount = car_price - down_payment
        monthly_rate = interest_rate / 100 / 12
        total_months = loan_years * 12
        
        # Calculate monthly payment
        if monthly_rate > 0:
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** total_months) / ((1 + monthly_rate) ** total_months - 1)
        else:
            monthly_payment = loan_amount / total_months
        
        total_payment = monthly_payment * total_months
        total_interest = total_payment - loan_amount
        down_payment_percent = (down_payment / car_price) * 100
        
        return {
            'loan_amount': loan_amount,
            'monthly_payment': monthly_payment,
            'total_payment': total_payment,
            'total_interest': total_interest,
            'down_payment_percent': down_payment_percent
        }
    
    def _display_results(self, dispatcher: CollectingDispatcher, params: Dict[str, float], result: Dict[str, float]) -> None:
        """Display loan calculation results"""
        response = f"""💰 **Car Loan Calculation Results**

🚗 **Vehicle Details:**
• Car Price: ${params['car_price']:,.0f}
• Down Payment: ${params['down_payment']:,.0f} ({result['down_payment_percent']:.1f}%)
• Loan Amount: ${result['loan_amount']:,.0f}

📊 **Loan Terms:**
• Loan Period: {params['loan_years']:.0f} years
• Interest Rate: {params['interest_rate']:.1f}% per annum

💳 **Payment Summary:**
• **Monthly Payment: ${result['monthly_payment']:,.0f}**
• Total Payment: ${result['total_payment']:,.0f}
• Total Interest: ${result['total_interest']:,.0f}

💡 **Tips:**
• Higher down payment = Lower monthly payments
• Shorter loan term = Less total interest
• Shop around for better interest rates

Need to calculate with different values? Just send me new numbers! 🔄"""
        
        dispatcher.utter_message(text=response)
    
    def _show_input_format(self, dispatcher: CollectingDispatcher) -> None:
        """Show input format when parameters cannot be extracted"""
        response = """❌ **I couldn't understand your loan details**

Please provide all 4 values:

🔢 **Simple format:**
"80000, 20000, 7, 3.5"
(car price, down payment, years, interest rate)

💬 **Natural format:**
"Calculate loan for car price 80000, down payment 20000, 7 years, 3.5% interest"

📝 **Example:**
• Car price: $80,000
• Down payment: $20,000  
• Loan period: 7 years
• Interest rate: 3.5%

Try again with all 4 numbers! 🚗"""
        
        dispatcher.utter_message(text=response)

# Keep the old action name for backward compatibility
class ActionCalculateLoanPayment(ActionLoanCalculator):
    """Backward compatibility alias"""
    
    def name(self) -> Text:
        return "action_loan_calculation_result"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if loan calculator feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_loan_calculator_feature_enabled(client_id):
            dispatcher.utter_message(text="I'm sorry, but the loan calculator feature is not available at the moment. Please contact our support team for assistance with financing inquiries.")
            return []
        
        # Call parent class implementation
        return super().run(dispatcher, tracker, domain)