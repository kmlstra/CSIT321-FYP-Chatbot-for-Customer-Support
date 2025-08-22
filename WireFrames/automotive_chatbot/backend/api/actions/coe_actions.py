"""
COE-related RASA Actions
Handles COE prices, predictions, and renewal information
"""

from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from .auto_logger import AutoLoggedAction
from api.middleware.intent_validation_middleware import validate_medium_confidence
import logging
import requests
import os
import json
import time
import pandas as pd
import re

from datetime import datetime, timedelta
import random

# Import visualization utilities
from api.utils.visualization_utils import get_chart_for_coe_response

# Import optimized feature cache manager
from api.cache.feature_cache_manager import check_coe_feature_enabled

logger = logging.getLogger(__name__)

# Import secure configuration and rate limiter
import sys
import os
from api.config import settings
from api.middleware.lta_rate_limiter import rate_limited_lta_request, lta_rate_limiter
from api.services.notifications import notify_coe_api_failure

# ========================================
# CONSTANTS FOR REUSABLE MESSAGES
# ========================================

COE_SERVICE_UNAVAILABLE_MESSAGE = """
    ❌ **COE Price Information Currently Unavailable**

    I'm sorry, the COE price service is temporarily down. Our technical team has been automatically notified and is working to resolve this issue.

    **🔄 Please try again later.**

    Thank you for your patience."""

COE_FEATURE_DISABLED_MESSAGE = """
    🚫 **COE Price Service Not Available**

    I'm sorry, but COE price information is not currently enabled for your account. This feature may be temporarily disabled or not included in your current service plan.

    **📞 For COE price information and vehicle inquiries, please:**
    • Contact our support team directly
    • Visit our showroom for personalized assistance
    • Check with your account manager about enabling COE services

    We're here to help with all your automotive needs! 🚗"""

def extract_coe_query_details(text: str) -> dict:
    """Extract specific month/year from COE queries with comprehensive date support"""
    months = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
        'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    result = {'month': None, 'year': None, 'prediction_requested': False, 'bidding_round': None}
    text_lower = text.lower()
    current_date = datetime.now()
    
    # Enhanced prediction detection - but also check for future dates
    if any(word in text_lower for word in ['predict', 'prediction', 'forecast', 'estimate', 'future', 'next month', 'coming months']):
        result['prediction_requested'] = True
        # Don't return early - continue to check for specific future dates
    
    # Detect specific bidding round requests
    if any(phrase in text_lower for phrase in ['first bidding', '1st bidding', 'first round', '1st round', 'first coe', '1st coe']):
        result['bidding_round'] = 'first'
    elif any(phrase in text_lower for phrase in ['second bidding', '2nd bidding', 'second round', '2nd round', 'second coe', '2nd coe']):
        result['bidding_round'] = 'second'
    
    current_date = datetime.now()
    
    # Handle relative date expressions
    if any(phrase in text_lower for phrase in ['last year', 'previous year']):
        result['year'] = current_date.year - 1
        # Check if specific month mentioned with "last year"
        for month_name, month_num in months.items():
            if month_name in text_lower:
                result['month'] = month_num
                break
        if not result['month']:
            result['month'] = 12  # Default to December if no month specified
            
    elif any(phrase in text_lower for phrase in ['last month', 'previous month']):
        if current_date.month == 1:
            result['month'] = 12
            result['year'] = current_date.year - 1
        else:
            result['month'] = current_date.month - 1
            result['year'] = current_date.year
            
    elif 'two months ago' in text_lower:
        target_date = current_date - timedelta(days=60)
        result['month'] = target_date.month
        result['year'] = target_date.year
        
    elif 'three months ago' in text_lower:
        target_date = current_date - timedelta(days=90)
        result['month'] = target_date.month
        result['year'] = target_date.year
        
    else:
        # Enhanced month detection - find the month first
        found_month = None
        for month_name, month_num in months.items():
            if month_name in text_lower:
                found_month = month_num
                break
        
        if found_month:
            result['month'] = found_month
            
            # Enhanced year detection - multiple patterns and context-aware
            year_patterns = [
                r'\b(20\d{2})\b',          # 2024, 2023, etc.
                r'\b(\d{4})\b',            # Any 4-digit year
                r'\b(\d{2})\b'             # 24, 23 (will convert to 20XX)
            ]
            
            found_year = None
            for pattern in year_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    year = int(match)
                    # Validate and convert 2-digit years
                    if year < 100:
                        if year >= 20 and year <= 35:  # 20-35 -> 2020-2035 (extended for future dates)
                            year = 2000 + year
                        elif year >= 0 and year <= 30:  # 0-30 -> 2000-2030 (extended range)
                            year = 2000 + year
                        else:
                            continue  # Skip invalid 2-digit years
                    
                    # Extended year range for COE data (including future dates)
                    if 2000 <= year <= 2035:
                        found_year = year
                        break
                
                if found_year:
                    break
            
            if found_year:
                result['year'] = found_year
            else:
                # Default to current year if no year specified but month found
                result['year'] = current_date.year
    
    # Handle patterns like "mar 2023", "2023 march", "march 2025", "03/24", "03-2025"
    # Look for year-month or month-year combinations
    if not result['month'] or not result['year']:
        # Pattern 1: "mar 2023", "march 2025" (month name + year)
        month_year_pattern = r'(?:' + '|'.join(months.keys()) + r')\s+(\d{4})'
        match = re.search(month_year_pattern, text_lower)
        if match:
            year = int(match.group(1))
            if 2000 <= year <= 2035:  # Extended range for future dates
                result['year'] = year
                # Find the month in the matched text
                for month_name, month_num in months.items():
                    if month_name in match.group(0):
                        result['month'] = month_num
                        break
                
                # Check if this is a future date - if so, mark as prediction
                if result['month'] and result['year']:
                    query_date = datetime(result['year'], result['month'], 1)
                    if query_date > current_date:
                        result['prediction_requested'] = True
        
        # Pattern 2: "2023 march", "2025 mar" (year + month name)
        year_month_pattern = r'(\d{4})\s+(?:' + '|'.join(months.keys()) + r')'
        match = re.search(year_month_pattern, text_lower)
        if match:
            year = int(match.group(1))
            if 2000 <= year <= 2035:  # Extended range for future dates
                result['year'] = year
                # Find the month in the matched text
                for month_name, month_num in months.items():
                    if month_name in match.group(0):
                        result['month'] = month_num
                        break
                
                # Check if this is a future date - if so, mark as prediction
                if result['month'] and result['year']:
                    query_date = datetime(result['year'], result['month'], 1)
                    if query_date > current_date:
                        result['prediction_requested'] = True
        
        # Pattern 3: "03/2025", "03-2025", "3/2025" (MM/YYYY, MM-YYYY)
        numeric_date_patterns = [
            r'\b(\d{1,2})[/.-](\d{4})\b',  # MM/YYYY, MM-YYYY, MM.YYYY
            r'\b(\d{4})[/.-](\d{1,2})\b'   # YYYY/MM, YYYY-MM, YYYY.MM
        ]
        
        for pattern in numeric_date_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                num1, num2 = int(match[0]), int(match[1])
                
                # Determine which is month and which is year
                if 2000 <= num1 <= 2035 and 1 <= num2 <= 12:
                    # num1 is year, num2 is month
                    result['year'] = num1
                    result['month'] = num2
                    break
                elif 2000 <= num2 <= 2035 and 1 <= num1 <= 12:
                    # num2 is year, num1 is month
                    result['year'] = num2
                    result['month'] = num1
                    break
            if result['month'] and result['year']:
                # Check if this is a future date - if so, mark as prediction
                query_date = datetime(result['year'], result['month'], 1)
                if query_date > current_date:
                    result['prediction_requested'] = True
                break
        
        # Pattern 4: "03/24", "3/24" (MM/YY - short year format)
        if not result['month'] or not result['year']:
            short_year_patterns = [
                r'\b(\d{1,2})[/.-](\d{2})\b',  # MM/YY, MM-YY, MM.YY
            ]
            
            for pattern in short_year_patterns:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    month_candidate, year_candidate = int(match[0]), int(match[1])
                    
                    # Convert 2-digit year to 4-digit (assume 20xx)
                    if year_candidate <= 35:  # 00-35 -> 2000-2035
                        full_year = 2000 + year_candidate
                    else:  # 36-99 -> 1936-1999 (unlikely for COE data)
                        continue  # Skip these
                    
                    if 1 <= month_candidate <= 12 and 2000 <= full_year <= 2035:
                        result['month'] = month_candidate
                        result['year'] = full_year
                        break
                if result['month'] and result['year']:
                    # Check if this is a future date - if so, mark as prediction
                    query_date = datetime(result['year'], result['month'], 1)
                    if query_date > current_date:
                        result['prediction_requested'] = True
                    break
    
    # Handle historical/past keywords without specific dates
    if any(word in text_lower for word in ['historical', 'history', 'past', 'old', 'before', 'back then']) and not result['month'] and not result['year']:
        # Default to previous month for general historical queries
        if current_date.month == 1:
            result['month'] = 12
            result['year'] = current_date.year - 1
        else:
            result['month'] = current_date.month - 1
            result['year'] = current_date.year
    

    return result

def format_change(change: int, use_html: bool = False) -> str:
    """Format price change with appropriate arrow indicator"""
    if use_html:
        # Return HTML with image tags for web display (PNG format)
        if change > 0:
            return f'<img src="/static/media/arrow-indicator/up-arrow-red.svg" alt="↗" class="trend-arrow"> +${change:,}'
        elif change < 0:
            return f'<img src="/static/media/arrow-indicator/down-arrow-green.svg" alt="↘" class="trend-arrow"> ${change:,}'
        else:
            return f'<img src="/static/media/arrow-indicator/no-change-grey.svg" alt="→" class="trend-arrow"> No change'
    else:
        # Return text with emoji indicators for chat display
        if change > 0:
            return f"📈 +${change:,}"
        elif change < 0:
            return f"📉 ${change:,}"
        else:
            return "➡️ No change"

@rate_limited_lta_request(cache_key="coe_prices_live", cache_minutes=120)
def get_live_coe_prices():
    """Fetch live COE prices from data.gov.sg API with rate limiting and caching"""
    try:

        
        # New data.gov.sg API endpoint (no authentication required)
        response = requests.get(
            f"{settings.COE_API_URL}?resource_id={settings.COE_DATASET_ID}&limit=100&sort=month desc",
            timeout=10
        )
        

        
        if response.status_code == 200:
            data = response.json()

            
            if 'result' in data and 'records' in data['result'] and data['result']['records']:
                # Get the most recent bidding results for each category
                records = data['result']['records']
                latest_prices = {}
                
                # Find the latest month's data for each category
                latest_month = None
                for record in records:
                    if latest_month is None:
                        latest_month = record.get('month')
                    
                    if record.get('month') == latest_month:
                        category = record.get('vehicle_class', '').replace('Category ', '')
                        premium = record.get('premium')
                        if category and premium:
                            latest_prices[category] = int(float(premium))
                
                # Validate that we have all required categories
                required_categories = ['A', 'B', 'C', 'D', 'E']
                found_categories = set(latest_prices.keys())
                

                
                if len(found_categories) >= 4 and found_categories.intersection(required_categories):  # At least 4 out of 5 categories
                    # Parse the latest_month to datetime for consistency
                    try:
                        latest_date = datetime.strptime(latest_month, '%Y-%m') if latest_month else datetime.now()
                    except ValueError:
                        latest_date = datetime.now()
                    
                    # Get previous bidding round data for comparison and PQP calculation
                    previous_prices = {}
                    pqp_prices = {}  # PQP = Previous bidding round's COE prices
                    previous_period = None
                    
                    # Sort records by month and bidding_no to get proper sequence
                    sorted_records = sorted(records, key=lambda x: (x.get('month', ''), x.get('bidding_no', '1')), reverse=True)
                    
                    # Find the previous bidding round (not just previous month)
                    current_bidding_no = None
                    for record in sorted_records:
                        if record.get('month') == latest_month:
                            current_bidding_no = record.get('bidding_no', '1')
                            break
                    
                    # Get previous bidding round data - improved logic
                    previous_period_found = False
                    for record in sorted_records:
                        record_month = record.get('month')
                        record_bidding = record.get('bidding_no', '1')
                        
                        # Skip current period records
                        if record_month == latest_month and record_bidding == current_bidding_no:
                            continue
                            
                        # Get the immediate previous bidding round
                        if not previous_period_found:
                            previous_period = f"{record_month}-{record_bidding}"
                            previous_period_found = True
                            
                            # Collect all categories for this previous period
                            for prev_record in sorted_records:
                                if (prev_record.get('month') == record_month and 
                                    prev_record.get('bidding_no', '1') == record_bidding):
                                    category = prev_record.get('vehicle_class', '').replace('Category ', '')
                                    premium = prev_record.get('premium')
                                    if category and premium:
                                        previous_prices[category] = int(float(premium))
                                        pqp_prices[category] = int(float(premium))  # PQP is previous bidding round's price
                            break  # Found the previous period, stop searching
                    
                    # Calculate changes
                    def calculate_change(current, previous_dict, category):
                        if category in previous_dict:
                            return current - previous_dict[category]
                        return 0
                    
                    # Return in the simple format user expects - NOW INCLUDING CATEGORY D
                    current_prices = {
                        'A': latest_prices.get('A', 0),
                        'B': latest_prices.get('B', 0),
                        'C': latest_prices.get('C', 0),
                        'D': latest_prices.get('D', 0),
                        'E': latest_prices.get('E', 0)
                    }
                    
                    trends = {
                        'A': format_change(calculate_change(latest_prices.get('A', 0), previous_prices, 'A'), use_html=True),
                        'B': format_change(calculate_change(latest_prices.get('B', 0), previous_prices, 'B'), use_html=True),
                        'C': format_change(calculate_change(latest_prices.get('C', 0), previous_prices, 'C'), use_html=True),
                        'D': format_change(calculate_change(latest_prices.get('D', 0), previous_prices, 'D'), use_html=True),
                        'E': format_change(calculate_change(latest_prices.get('E', 0), previous_prices, 'E'), use_html=True)
                    }
                    
                    # Detect current bidding round (1st or 2nd of the month)
                    current_round_display = "1st" if current_bidding_no == '1' else "2nd"
                    bidding_round_text = f"{current_round_display} BIDDING"
                    
                    # Extract previous period info
                    prev_month = previous_period.split('-')[0] if previous_period else latest_month
                    prev_bidding = previous_period.split('-')[1] if previous_period and '-' in previous_period else '1'
                    prev_round_display = "1st" if prev_bidding == '1' else "2nd"
                    
                    result = {
                        'current_prices': current_prices,
                        'pqp_prices': pqp_prices,
                        'trends': trends,
                        'bidding_period': latest_month or datetime.now().strftime('%Y-%m'),
                        'previous_period': prev_month or datetime.now().strftime('%Y-%m'),
                        'current_bidding_round': current_bidding_no or '1',
                        'current_round_display': current_round_display,
                        'bidding_round_text': bidding_round_text,
                        'previous_round_display': prev_round_display,
                        'date': latest_date,
                        'month_str': latest_month or datetime.now().strftime('%Y-%m')
                    }

                    return result
                else:

                    return get_fallback_coe_prices()
            else:

                return get_fallback_coe_prices()
        else:

            return get_fallback_coe_prices()
        
        # Fallback if API fails

        return get_fallback_coe_prices()
        
    except Exception as e:
        logger.error(f"Error fetching live COE prices: {e}")
        return get_fallback_coe_prices()

def get_fallback_coe_prices():
    """Return None when API is unavailable and send notification to tech team"""
    notify_coe_api_failure()
    return None

def get_historical_coe_data(year: Optional[int] = None, month: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetch historical COE data from data.gov.sg API"""
    try:
        response = requests.get(
            f"{settings.COE_API_URL}?resource_id={settings.COE_DATASET_ID}&limit=500&sort=month desc",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and 'records' in data['result']:
                historical_records = []
                monthly_data = {}
                
                # Group records by month and bidding round
                for record in data['result']['records']:
                    month_str = record.get('month', '')
                    category = record.get('vehicle_class', '').replace('Category ', '')
                    premium = record.get('premium')
                    bidding_no = record.get('bidding_no', '1')  # Default to first bidding if not specified
                    
                    if month_str and category and premium:
                        if month_str not in monthly_data:
                            monthly_data[month_str] = {'first': {}, 'second': {}}
                        
                        # Determine bidding round based on bidding_no
                        if bidding_no == '2' or 'second' in str(bidding_no).lower():
                            monthly_data[month_str]['second'][category] = int(float(premium))
                        else:
                            monthly_data[month_str]['first'][category] = int(float(premium))
                
                # Convert to historical records format
                for month_str, bidding_data in monthly_data.items():
                    try:
                        # Parse month (format: YYYY-MM)
                        record_date = datetime.strptime(month_str, '%Y-%m')
                        
                        # Filter by year/month if specified
                        if year and month:
                            if record_date.year == year and record_date.month == month:
                                # Add both bidding rounds if available
                                for round_name, prices in bidding_data.items():
                                    if len(prices) >= 5:  # Need A, B, C, D, E
                                        historical_records.append({
                                            'date': record_date,
                                            'bidding_round': round_name,
                                            'A': prices.get('A', 0),
                                            'B': prices.get('B', 0),
                                            'C': prices.get('C', 0),
                                            'D': prices.get('D', 0),
                                            'E': prices.get('E', 0)
                                        })
                        else:
                            # Add both bidding rounds if available
                            for round_name, prices in bidding_data.items():
                                if len(prices) >= 5:  # Need A, B, C, D, E
                                    historical_records.append({
                                        'date': record_date,
                                        'bidding_round': round_name,
                                        'A': prices.get('A', 0),
                                        'B': prices.get('B', 0),
                                        'C': prices.get('C', 0),
                                        'D': prices.get('D', 0),
                                        'E': prices.get('E', 0)
                                    })
                    except ValueError:
                        continue  # Skip invalid date formats
                
                return sorted(historical_records, key=lambda x: (x['date'], x['bidding_round']), reverse=True)
        
        return []
        
    except Exception as e:
        logger.error(f"Error fetching historical COE data: {e}")
        return []

def format_historical_coe_response(month_data_list: List[Dict], month_name: str, bidding_round: Optional[str] = None) -> str:
    """Format historical COE response with bidding round information"""
    if not month_data_list:
        return f"Sorry, I don't have COE data for {month_name}. I have current data available."
    
    if bidding_round:
        # Show specific bidding round
        specific_data = None
        for data in month_data_list:
            if data.get('bidding_round') == bidding_round:
                specific_data = data
                break
        
        if specific_data:
            round_display = "First" if bidding_round == 'first' else "Second"
            response = f"""📊 **COE Prices for {month_name} - {round_display} Bidding Round**

🚗 **Category A:** ${specific_data['A']:,}
🚙 **Category B:** ${specific_data['B']:,}
🚚 **Category C:** ${specific_data['C']:,}
🏍️ **Category D:** ${specific_data['D']:,}
🔄 **Category E:** ${specific_data['E']:,}

📅 **Bidding Round:** {round_display} bidding of {month_name}
📊 **Data Source:** Land Transport Authority (LTA) Singapore"""
        else:
            response = f"Sorry, I don't have {bidding_round} bidding data for {month_name}."
    else:
        # Show both bidding rounds
        first_data = None
        second_data = None
        
        for data in month_data_list:
            if data.get('bidding_round') == 'first':
                first_data = data
            elif data.get('bidding_round') == 'second':
                second_data = data
        
        response = f"""📊 **COE Prices for {month_name} - Both Bidding Rounds**\n\n"""
        
        if first_data:
            response += f"""🔵 **First Bidding Round (1st Wednesday):**
🚗 **Category A:** ${first_data['A']:,}
🚙 **Category B:** ${first_data['B']:,}
🚚 **Category C:** ${first_data['C']:,}
🏍️ **Category D:** ${first_data['D']:,}
🔄 **Category E:** ${first_data['E']:,}

"""
        
        if second_data:
            response += f"""🔴 **Second Bidding Round (3rd Wednesday):**
🚗 **Category A:** ${second_data['A']:,}
🚙 **Category B:** ${second_data['B']:,}
🚚 **Category C:** ${second_data['C']:,}
🏍️ **Category D:** ${second_data['D']:,}
🔄 **Category E:** ${second_data['E']:,}

"""
        
        if not first_data and not second_data:
            response = f"Sorry, I don't have complete bidding data for {month_name}."
        else:
            response += f"""📅 **Monthly Schedule:** COE bidding occurs twice monthly (1st & 3rd Wednesday)
📊 **Data Source:** Land Transport Authority (LTA) Singapore"""
    
    return response

def format_coe_response_with_chart(base_response: str, prices: Dict[str, Any], historical_data: Optional[List[Dict[str, Any]]] = None, chart_type: str = 'comparison') -> str:
    """Format COE response with chart integration"""
    try:
        chart_html = get_chart_for_coe_response(prices, historical_data if historical_data is not None else [], chart_type)
        if chart_html:
            return f"{base_response}\n\n{chart_html}"
        else:
            return base_response
    except Exception as e:
        return base_response

class ActionCOEPrices(AutoLoggedAction):
    """
    COE prices action with intent validation middleware integration.
    Handles COE price queries with medium confidence validation.
    """
    def name(self) -> Text:
        return "action_coe_prices"

    @validate_medium_confidence(confidence_threshold=0.6)
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Log user message and action execution
        self.log_user_message(tracker)
        self.log_action_execution("action_coe_prices", "started", tracker)
        
        try:
            # Check if COE prices feature is enabled for this client
            client_id = tracker.latest_message.get('metadata', {}).get('client_id')
            if client_id:
                if not check_coe_feature_enabled(client_id):
                    dispatcher.utter_message(
                        text="I'm sorry, but COE price information is currently not available. Please contact our support team for assistance."
                    )
                    return []
        
            user_text = tracker.latest_message.get("text", "")
            query_details = extract_coe_query_details(user_text)
        
            if query_details['month'] and query_details['year']:
                # Check if this is a future date prediction request
                if query_details.get('prediction_requested', False):
                    # Handle future date prediction - redirect to prediction action
                    month_name = datetime(query_details['year'], query_details['month'], 1).strftime("%B %Y")
                    response = f"🔮 **COE Price Prediction for {month_name}**\n\nI understand you're asking about COE prices for {month_name}. Since this is a future date, let me provide you with our intelligent forecasting analysis instead.\n\nPlease ask me for 'COE predictions' to get detailed forecasting analysis based on current market trends and historical patterns."
                else:
                    # Historical data request
                    year = query_details['year']
                    month = query_details['month']
                    bidding_round = query_details.get('bidding_round')
                    
                    historical_data = get_historical_coe_data(year, month)
                    
                    if historical_data:
                        # Get data for the specific month (all bidding rounds)
                        month_data_list = []
                        for record in historical_data:
                            if record['date'].year == year and record['date'].month == month:
                                month_data_list.append(record)
                        
                        if month_data_list:
                            month_name = datetime(year, month, 1).strftime("%B %Y")
                            response = format_historical_coe_response(month_data_list, month_name, bidding_round)
                        else:
                            response = f"Sorry, I don't have COE data for the requested period. I have current data available."
                    else:
                        response = f"Sorry, I don't have COE data for the requested period. I have current data available."
                    
            else:
                # Current data request
                current_prices = get_live_coe_prices()

                if current_prices is None:
                    response = COE_SERVICE_UNAVAILABLE_MESSAGE
                else:
                    # Extract current prices and trends from new format
                    prices = current_prices['current_prices']
                    pqp = current_prices.get('pqp_prices', {})
                    trends = current_prices['trends']
                    
                    # Determine current bidding round - improved detection
                    current_period = current_prices['bidding_period']
                    current_bidding_round = current_prices.get('current_bidding_round', '1')
                    current_round_display = current_prices.get('current_round_display', '1st')
                    bidding_round_text = current_prices.get('bidding_round_text', '1st BIDDING')
                    
                    # Enhanced bidding round detection
                    try:
                        current_date = datetime.now()
                        
                        # Use the actual bidding round data from API
                        if current_bidding_round == '1':
                            bidding_round_info = f"\n🔵 **Current Period:** {current_round_display} bidding round of {current_date.strftime('%B %Y')} (1st Wednesday)"
                        elif current_bidding_round == '2':
                            bidding_round_info = f"\n🔴 **Current Period:** {current_round_display} bidding round of {current_date.strftime('%B %Y')} (3rd Wednesday)"
                        else:
                            # Fallback to date-based detection
                            current_day = current_date.day
                            if current_day <= 15:
                                bidding_round_info = f"\n🔵 **Current Period:** 1st bidding round of {current_date.strftime('%B %Y')} (1st Wednesday)"
                            else:
                                bidding_round_info = f"\n🔴 **Current Period:** 2nd bidding round of {current_date.strftime('%B %Y')} (3rd Wednesday)"
                        
                        # Add general schedule info
                        bidding_round_info += "\n📅 **Schedule:** COE bidding occurs twice monthly (1st & 3rd Wednesday)"
                        
                    except Exception as e:
                        bidding_round_info = "\n📅 **Bidding Schedule:** COE bidding occurs twice monthly (1st & 3rd Wednesday)"
                    
                    # Always format the base response consistently - ADD COE MARKER
                    base_response = f"""📊 **Latest COE Prices (Live Data)**

🚗 **Category A:** ${prices['A']:,} {trends['A']}
🚙 **Category B:** ${prices['B']:,} {trends['B']}
🚚 **Category C:** ${prices['C']:,} {trends['C']}
🏍️ **Category D:** ${prices['D']:,} {trends['D']}
🔄 **Category E:** ${prices['E']:,} {trends['E']}

📋 **PQP (Prevailing Quota Premium):**
🚗 **Category A:** ${pqp.get('A', 0):,}
🚙 **Category B:** ${pqp.get('B', 0):,}
🚚 **Category C:** ${pqp.get('C', 0):,}
🏍️ **Category D:** ${pqp.get('D', 0):,}
🔄 **Category E:** ${pqp.get('E', 0):,}

📅 **Current Period:** {current_prices['bidding_period']}
📅 **PQP Period:** {current_prices.get('previous_period', 'N/A')}{bidding_round_info}

💡 **PQP Note:** Used for 5-year COE renewals instead of current bidding price

📊 **Data Source:** Land Transport Authority (LTA) Singapore"""

                    # Try to generate price comparison chart
                    try:
                        historical_data = get_historical_coe_data()
                        chart_html = get_chart_for_coe_response(prices, historical_data, 'comparison')
                        if chart_html:
                            # Combine text and chart into a single message for proper frontend processing
                            response = f"{base_response}\n\n{chart_html}"
                        else:
                            # Use base response if no chart
                            response = base_response
                                
                    except Exception as e:
                        # Use base response if chart generation fails
                        response = base_response

            # Send the response - it will be processed by formatCOEData() on the frontend
            dispatcher.utter_message(text=response)
            
            # Log bot response
            self.log_bot_response(dispatcher, tracker)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in ActionCOEPrices: {e}")
            fallback_message = "Sorry, there was an error retrieving COE price information. Please try again."
            dispatcher.utter_message(text=fallback_message)
            
            # Log action execution failure and bot response
            self.log_action_execution("action_coe_prices", "failed", tracker, str(e))
            self.log_bot_response(dispatcher, tracker)
            
            return []
    



class ActionExplainCOECategories(AutoLoggedAction):
    def name(self) -> Text:
        return "action_explain_coe_categories"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Log user message and action execution
        self.log_user_message(tracker)
        self.log_action_execution("action_explain_coe_categories", "started", tracker)
        
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            self.log_bot_response(dispatcher, tracker)
            return []
        
        # Get current prices for dynamic information
        current_prices = get_live_coe_prices()
        
        if current_prices is None:
            price_section = "📊 **Current Prices:** Temporarily unavailable"
        else:
            prices = current_prices['current_prices']
            trends = current_prices['trends']
            price_section = f"""📊 **Current Live Prices:**
🚗 **Category A:** ${prices['A']:,} {trends['A']}
🚙 **Category B:** ${prices['B']:,} {trends['B']}
🚚 **Category C:** ${prices['C']:,} {trends['C']}
🏍️ **Category D:** ${prices['D']:,} {trends['D']}
🔄 **Category E:** ${prices['E']:,} {trends['E']}"""

        response = f"""📚 **COE Categories Comprehensive Guide** 🚗

{price_section}

## 🚗 **Category A (Cars ≤1600cc & ≤130bhp)**
**✅ Eligible Vehicles:** Small to medium cars with engine capacity up to 1600cc OR electric cars with power up to 130bhp

**🚗 Popular Models:** Toyota Vios • Honda City • Nissan Almera • Mitsubishi Attrage • Kia Cerato • Hyundai Avante • Suzuki Swift

**💰 Key Benefits:**
• Most affordable COE category
• Excellent fuel efficiency (15-20km/L)
• Perfect for city driving and daily commuting
• Lower insurance and maintenance costs

**🎯 Best For:** First-time car buyers, budget-conscious families, urban commuters

**📝 Special Note:** All taxis (regardless of engine size) fall under Category A

---

## 🚙 **Category B (Cars >1600cc or >130bhp)**
**✅ Eligible Vehicles:** Cars with engine capacity above 1600cc OR electric cars with power above 130bhp

**🚙 Premium Models:** BMW 320i • Mercedes C200 • Toyota Camry • Honda Accord • Mazda CX-5 • Subaru Forester • Lexus ES250

**🏆 Key Benefits:**
• More powerful engines and performance
• Luxury features and premium comfort
• Enhanced performance for long drives
• Higher status and prestige

**🎯 Best For:** Families needing more space, performance enthusiasts, luxury car buyers

---

## 🚚 **Category C (Commercial Vehicles & Buses)**
**✅ Eligible Vehicles:** Commercial vehicles, trucks, vans, buses, construction vehicles

**🚚 Vehicle Types:** Isuzu trucks • Mitsubishi Fuso • Toyota Hiace vans • School buses • Delivery trucks

**💼 Key Benefits:**
• Lower COE prices than passenger cars
• Designed for heavy-duty operations
• Higher payload capacity
• Commercial tax benefits

**🎯 Best For:** Business owners, logistics companies, construction firms, public transport

---

## 🏍️ **Category D (Motorcycles & Scooters)**
**✅ Eligible Vehicles:** All two-wheeled motor vehicles including motorcycles and scooters

**🏍️ Popular Models:** Yamaha motorcycles • Honda bikes • Suzuki models • Vespa scooters • Harley-Davidson

**🌟 Key Benefits:**
• Most affordable COE category
• Excellent fuel economy (30-40km/L)
• Easy parking and maneuverability
• Beat traffic congestion

**🎯 Best For:** Solo commuters, motorcycle enthusiasts, cost-conscious transport

**⚠️ Important:** Our dealership specializes in cars (Categories A & B). For motorcycles, consult licensed motorcycle dealers.

---

## 🔄 **Category E (Open Category)**
**✅ Eligible Vehicles:** Can bid for ANY vehicle type - cars, motorcycles, commercial vehicles

**🔄 Flexibility:** Ultimate choice when other categories are oversubscribed or unavailable

**💎 Key Benefits:**
• Guaranteed option when other categories are full
• Maximum flexibility in vehicle choice
• Can be used for any vehicle type
• Premium positioning in market

**🎯 Best For:** Buyers needing guaranteed COE, when other categories are oversubscribed

**💰 Cost Consideration:** Highest COE prices due to premium positioning and flexibility

---

## 💡 **How to Choose the Right Category:**

**1. Check Your Vehicle Specs:** Look at engine capacity (cc) and power (bhp/hp)
**2. Consider Your Budget:** Category A is most affordable, Category E is most expensive
**3. Think About Usage:** Daily commuting vs. family trips vs. performance driving
**4. Plan for Flexibility:** Category E as backup if primary choice is oversubscribed

## 🎯 **Pro Tips:**
• Category A vehicles typically offer better resale value due to lower running costs
• Category B vehicles provide more comfort for longer journeys
• Always verify your specific vehicle's category requirements before bidding
• Consider total cost of ownership, not just COE price

**Which category interests you most? I can provide specific current prices and recommendations!** 🤔

📊 **Data Source:** Land Transport Authority (LTA) Singapore"""
                
        dispatcher.utter_message(text=response)
        
        # Log bot response
        self.log_bot_response(dispatcher, tracker)
        
        return []

class ActionExplainCOERenewal(AutoLoggedAction):
    def name(self) -> Text:
        return "action_explain_coe_renewal"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        # Get current prices for dynamic renewal cost calculation
        current_prices = get_live_coe_prices()
        
        if current_prices is None:
            response = COE_SERVICE_UNAVAILABLE_MESSAGE
        else:
            prices = current_prices['current_prices']
            renewal_costs = f"""
            📊 **Current Renewal Costs:** (Based on latest COE prices)
            🚗 **Category A:** ~${prices['A']:,}
            🚙 **Category B:** ~${prices['B']:,}
            🚚 **Category C:** ~${prices['C']:,}
            🏍️ **Category D:** ~${prices['D']:,}
            🔄 **Category E:** ~${prices['E']:,}"""
        
        response = f"""🔄 **COE Renewal Process Guide**

        📋 **What is COE Renewal?**
        COE renewal allows you to extend your vehicle's usage beyond the initial 10-year period without scrapping.

        🕐 **When to Renew:**
        • Apply 1-3 months before your COE expires
        • Check your COE expiry date on your vehicle registration card
        • Don't wait until the last minute - processing takes time

        💰 **Renewal Options:**
        1️⃣ **5-Year Renewal:** Pay current PQP (Prevailing Quota Premium) - typically lower cost
        2️⃣ **10-Year Renewal:** Pay current COE bidding price - full renewal period
        {renewal_costs}

        📋 **Required Documents:**
        • Vehicle registration card (original)
        • Valid comprehensive insurance policy
        • Vehicle inspection report (if required)
        • NRIC/Passport (for verification)

        🌐 **Quick Access to COE Renewal:**
        📱 **LTA Online Portal:** https://onemotoring.lta.gov.sg/content/onemotoring/home/services/vehicle-services/certificate-of-entitlement/coe-renewal.html
        📞 **LTA Hotline:** 1800-225-5582 (for assistance)
        🏢 **LTA Service Centers:** Available across Singapore

        ⚠️ **Important Renewal Reminders:**
        • Renewal must be completed before COE expiry
        • Late renewal may result in additional penalties
        • Insurance must be valid throughout the renewal period
        • Vehicle must pass inspection if required

        💡 **Need Help with COE Renewal Application?**
        I can provide information and guidance about the renewal process, but I cannot help you complete the actual renewal application. You'll need to:
        • Visit the LTA website directly
        • Call LTA's hotline for step-by-step assistance
        • Visit an LTA service center for in-person help

        Would you like me to explain more about renewal costs or timing recommendations? 🤔"""
                        
        dispatcher.utter_message(text=response)
        return []

class ActionCOERenewalAssistance(AutoLoggedAction):
    def name(self) -> Text:
        return "action_coe_renewal_assistance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        response = """❌ **COE Renewal Application Assistance**

        I'm sorry, but I **cannot help you complete the actual COE renewal application** or submit it on your behalf.

        🛑 **What I Cannot Do:**
        • Fill out renewal forms for you
        • Submit applications to LTA
        • Make payments on your behalf
        • Access your personal vehicle records

        ✅ **What I Can Help With:**
        • Explain the renewal process step-by-step
        • Provide current renewal costs and pricing
        • Guide you to the right LTA resources
        • Answer questions about renewal requirements
        • Explain renewal timing and deadlines

        🌐 **For Actual COE Renewal:**
        • **LTA Online Portal:** https://onemotoring.lta.gov.sg/content/onemotoring/home/services/vehicle-services/certificate-of-entitlement/coe-renewal.html
        • **LTA Hotline:** 1800-225-5582 (for direct assistance)
        • **LTA Service Centers:** Visit in person for help

        💡 **Pro Tip:** The LTA online portal is the fastest way to complete your renewal. Their customer service team can guide you through the process if you need help.

        Would you like me to explain the renewal process or provide current pricing information instead? 🤔"""
                
        dispatcher.utter_message(text=response)
        return []

class ActionCOERenewal(AutoLoggedAction):
    """Handle COE renewal inquiries"""
    
    def name(self) -> Text:
        return "action_coe_renewal"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        response = """🔄 **COE Renewal Information**

COE renewal allows you to extend your vehicle's Certificate of Entitlement for another 5 or 10 years.

📋 **Renewal Options:**
• **5-year renewal** - Pay Prevailing Quota Premium (PQP)
• **10-year renewal** - Pay 2x Prevailing Quota Premium (PQP)

💰 **Current Renewal Costs:**
• Category A: Based on current PQP rates
• Category B: Based on current PQP rates
• Check LTA website for latest PQP rates

⏰ **Important Timing:**
• Renew within 3 months before COE expiry
• Late renewal incurs additional penalties
• Cannot drive vehicle if COE expires

🌐 **How to Renew:**
• **Online:** LTA OneMotoring portal
• **In-person:** LTA service centers
• **Through dealers:** Authorized car dealers

📞 **Need Help?**
• LTA Hotline: 1800-225-5582
• Visit: https://onemotoring.lta.gov.sg

Would you like more details about renewal costs or the renewal process? 🤔"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionCoeBiddingAssistance(AutoLoggedAction):
    """Handle COE bidding assistance inquiries"""
    
    def name(self) -> Text:
        return "action_coe_bidding_assistance"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        response = """🚫 **COE Bidding Assistance**

I'm unable to help you bid for COE directly through this chatbot. COE bidding must be done through official LTA channels only.

✅ **What I Can Help With:**
• Explain the bidding process and requirements
• Provide current COE prices and trends
• Guide you on bidding strategies and timing
• Answer questions about different COE categories
• Explain bidding rules and regulations

🌐 **For Actual COE Bidding:**
• **LTA OneMotoring Portal:** https://onemotoring.lta.gov.sg/content/onemotoring/home/services/vehicle-services/certificate-of-entitlement/coe-bidding.html
• **LTA Hotline:** 1800-225-5582 (for bidding assistance)
• **Authorized Car Dealers:** They can help with the bidding process

📋 **Before Bidding, Ensure You Have:**
• Valid NRIC/FIN and sufficient funds
• Understanding of current COE prices and trends
• Knowledge of bidding deadlines and procedures
• Decided on the right COE category for your vehicle

💡 **Pro Tip:** Check the latest COE prices and market trends before bidding to make an informed decision!

Would you like me to explain the bidding process or provide current COE pricing information? 🤔"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionCOECategoryDetails(AutoLoggedAction):
    def name(self) -> Text:
        return "action_coe_category_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        user_text = tracker.latest_message.get("text", "").lower()
        
                # Determine which category the user is asking about
        category = None
        # Enhanced COE-specific category detection to avoid conflicts with car recommendation intents
        if any(phrase in user_text for phrase in ['category a', 'cat a', 'coe category a', 'coe a', 'category a coe', 'small car coe', '1600cc coe', 'under 1600cc', 'below 1600cc']) or \
           (any(word in user_text for word in ['coe', 'category', 'certificate']) and any(word in user_text for word in ['small car', '1600cc', 'compact'])):
            category = 'A'
        elif any(phrase in user_text for phrase in ['category b', 'cat b', 'coe category b', 'coe b', 'category b coe', 'large car coe', 'luxury coe', 'above 1600cc', 'over 1600cc']) or \
             (any(word in user_text for word in ['coe', 'category', 'certificate']) and any(word in user_text for word in ['large car', 'luxury', 'performance'])):
            category = 'B'
        elif any(phrase in user_text for phrase in ['category c', 'cat c', 'coe category c', 'coe c', 'category c coe', 'commercial coe', 'goods vehicle', 'commercial vehicle']) or \
             (any(word in user_text for word in ['coe', 'category', 'certificate']) and any(word in user_text for word in ['truck', 'commercial', 'goods', 'van', 'lorry'])):
            category = 'C'
        elif any(phrase in user_text for phrase in ['category d', 'cat d', 'coe category d', 'coe d', 'category d coe', 'motorcycle coe', 'bike coe', 'scooter coe']) or \
             (any(word in user_text for word in ['coe', 'category', 'certificate']) and any(word in user_text for word in ['motorcycle', 'scooter', 'bike', 'motorbike', 'two-wheeler'])):
            category = 'D'
        elif any(phrase in user_text for phrase in ['category e', 'cat e', 'coe category e', 'coe e', 'category e coe', 'open category', 'flexible coe', 'any category coe']) or \
             (any(word in user_text for word in ['coe', 'category', 'certificate']) and any(word in user_text for word in ['open', 'flexible', 'any vehicle', 'oversubscribed'])):
            category = 'E'
        
        # If no specific category detected, use the main COE categories explanation
        if not category:
            # Call the ActionExplainCOECategories action instead of custom fallback
            categories_action = ActionExplainCOECategories()
            return categories_action.run(dispatcher, tracker, domain)
        
        current_prices = get_live_coe_prices()
        
        if current_prices is None:
            price_info = "Price information temporarily unavailable"
            trend_info = ""
        else:
            prices = current_prices['current_prices']
            trends = current_prices['trends']
            price_info = f"${prices[category]:,}"
            trend_info = f" {trends[category]}"
        
        # Enhanced category-specific details with car examples
        category_details = {
            'A': {
                'emoji': '🚗',
                'name': 'Category A COE - Small Cars',
                'description': 'Cars with engine capacity up to 1600cc OR electric cars with power up to 130bhp',
                'car_examples': [
                    '🚗 **Toyota Vios** - 1.5L, popular sedan, excellent fuel economy',
                    '🚗 **Honda City** - 1.5L, spacious interior, reliable performance', 
                    '🚗 **Nissan Almera** - 1.0L turbo, modern features, compact size',
                    '🚗 **Mitsubishi Attrage** - 1.2L, affordable, good for daily driving',
                    '🚗 **Kia Cerato** - 1.6L, stylish design, comprehensive warranty',
                    '🚗 **Hyundai Avante** - 1.6L, premium features, comfortable ride',
                    '🚗 **Suzuki Swift** - 1.2L, sporty handling, fuel efficient'
                ],
                'benefits': [
                    '💰 Most affordable COE category',
                    '⛽ Excellent fuel efficiency (15-20km/L)',
                    '🏙️ Perfect for city driving and parking',
                    '🛡️ Lower insurance and maintenance costs',
                    '📈 Good resale value due to popularity'
                ],
                'ideal_for': 'First-time car buyers, budget-conscious families, urban commuters, daily city driving'
            },
            'B': {
                'emoji': '🚙',
                'name': 'Category B COE - Large Cars',
                'description': 'Cars with engine capacity above 1600cc OR electric cars with power above 130bhp',
                'car_examples': [
                    '🚙 **BMW 320i** - 2.0L turbo, luxury sedan, advanced technology',
                    '🚙 **Mercedes C200** - 1.5L turbo, premium comfort, prestigious brand',
                    '🚙 **Toyota Camry** - 2.5L, reliable luxury, spacious interior',
                    '🚙 **Honda Accord** - 1.5L turbo, executive sedan, smooth performance',
                    '🚙 **Mazda CX-5** - 2.5L, premium SUV, exceptional handling',
                    '🚙 **Subaru Forester** - 2.0L, all-wheel drive, family SUV',
                    '🚙 **Lexus ES250** - 2.5L, luxury comfort, premium interior'
                ],
                'benefits': [
                    '🚀 More powerful engines and performance',
                    '🏆 Luxury features and premium comfort',
                    '👨‍👩‍👧‍👦 More space for families',
                    '🛣️ Better for long-distance driving',
                    '⭐ Higher status and prestige'
                ],
                'ideal_for': 'Families needing more space, performance enthusiasts, luxury car buyers, frequent long-distance travelers'
            },
            'C': {
                'emoji': '🚚',
                'name': 'Category C COE - Commercial Vehicles',
                'description': 'Goods vehicles, trucks, vans, buses, and commercial vehicles',
                'car_examples': [
                    '🚚 **Isuzu NPR** - Light truck, delivery operations',
                    '🚚 **Mitsubishi Fuso** - Heavy truck, construction work',
                    '🚚 **Toyota Hiace** - Commercial van, passenger transport',
                    '🚚 **Nissan Cabstar** - Light truck, urban delivery',
                    '🚚 **Hyundai H100** - Commercial van, goods transport',
                    '🚌 **School buses** - Public transport vehicles',
                    '🚚 **Construction vehicles** - Specialized commercial use'
                ],
                'benefits': [
                    '💼 Lower COE prices than passenger cars',
                    '🏗️ Designed for heavy-duty operations',
                    '📦 High payload capacity',
                    '🚛 Commercial tax benefits',
                    '🔧 Robust build for business use'
                ],
                'ideal_for': 'Business owners, logistics companies, construction firms, delivery services, public transport operators'
            },
            'D': {
                'emoji': '🏍️',
                'name': 'Category D COE - Motorcycles',
                'description': 'All two-wheeled motor vehicles including motorcycles and scooters',
                'car_examples': [
                    '🏍️ **Yamaha YZF-R15** - Sports bike, 155cc, performance riding',
                    '🏍️ **Honda CBR150R** - Sport bike, 150cc, reliable performance',
                    '🛵 **Vespa Primavera** - Premium scooter, 150cc, Italian design',
                    '🏍️ **Suzuki GSX-R150** - Sports bike, racing heritage',
                    '🛵 **Yamaha NMAX** - Premium scooter, 155cc, daily commuting',
                    '🏍️ **Harley-Davidson** - Cruiser bikes, premium motorcycles',
                    '🛵 **Honda PCX** - Scooter, 150cc, fuel efficient'
                ],
                'benefits': [
                    '💰 Most affordable COE category',
                    '⛽ Excellent fuel economy (30-40km/L)',
                    '🅿️ Easy parking and maneuverability',
                    '🚦 Beat traffic congestion',
                    '🌱 Lower carbon footprint'
                ],
                'ideal_for': 'Solo commuters, motorcycle enthusiasts, cost-conscious transport, urban mobility',
                'special_note': '⚠️ **Important:** Our dealership specializes in cars (Categories A & B). For motorcycles, please consult licensed motorcycle dealers.'
            },
            'E': {
                'emoji': '🔄',
                'name': 'Category E COE - Open Category',
                'description': 'Flexible category that can be used for any vehicle type',
                'car_examples': [
                    '🔄 **Any Category A car** - If Category A is oversubscribed',
                    '🔄 **Any Category B car** - If Category B is oversubscribed', 
                    '🔄 **Luxury vehicles** - When other categories are full',
                    '🔄 **Import cars** - Rare or special vehicles',
                    '🔄 **Commercial vehicles** - Alternative to Category C',
                    '🔄 **Motorcycles** - Alternative to Category D',
                    '🔄 **Any vehicle** - Maximum flexibility'
                ],
                'benefits': [
                    '🎯 Guaranteed option when other categories are full',
                    '🔄 Maximum flexibility in vehicle choice',
                    '📈 Can be used for any vehicle type',
                    '🚗 Backup when primary choice is oversubscribed',
                    '💎 Premium positioning in market'
                ],
                'ideal_for': 'Buyers needing guaranteed COE, when other categories are oversubscribed, premium vehicle purchases, import vehicles'
            }
        }
        
        info = category_details[category]
        car_examples_text = '\n            '.join(info['car_examples'])
        benefits_text = '\n            '.join(info['benefits'])
        
        response = f"""{info['emoji']} **{info['name']}**

                    **Current Price:** {price_info}{trend_info}

                    📋 **Category Description:**
                    {info['description']}

                    🚗 **Vehicle Examples:**
                                {car_examples_text}

                    ✅ **Key Benefits:**
                                {benefits_text}

                    🎯 **Ideal For:** {info['ideal_for']}"""

        if 'special_note' in info:
            response += f"\n\n{info['special_note']}"

        response += f"""

        💡 **Need More Help?**
        • Ask about current COE prices: "What are today's COE prices?"
        • Get price predictions: "COE price predictions"
        • Learn about timing: "When is the best time to buy COE?"

        Would you like more specific information about {info['name']}? 🤔"""
        
        dispatcher.utter_message(text=response)
        return []

class ActionExplainCOEBiddingProcess(AutoLoggedAction):
    def name(self) -> Text:
        return "action_explain_coe_bidding_process"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = """🎯 **COE Bidding Process Explained**

            📋 **What is COE Bidding?**
            A sealed-bid auction system where buyers compete for the right to register a vehicle in Singapore.

            🗓️ **Bidding Schedule:**
            • **Frequency**: Twice monthly (1st & 3rd Wednesday)
            • **Duration**: 3 days (Wednesday to Friday)
            • **Timing**: 12:00 PM to 6:00 PM daily
            • **Results**: Announced Friday evening

            💰 **How Bidding Works:**
            1️⃣ **Submit Bid**: Place your maximum bid amount
            2️⃣ **Uniform Price**: All successful bidders pay the same price
            3️⃣ **Quota Premium**: Lowest successful bid becomes the COE price
            4️⃣ **Payment**: Pay within 2 business days if successful

            📊 **Bidding Strategy:**
            • **Research**: Check historical prices and trends
            • **Budget**: Set maximum affordable amount
            • **Timing**: Consider submitting bids closer to deadline
            • **Categories**: Choose the right category for your vehicle

            🏆 **Success Factors:**
            • **Market Awareness**: Understanding supply and demand
            • **Price Trends**: Analyzing recent bidding results
            • **Economic Conditions**: Considering market sentiment
            • **Bidder Behavior**: Anticipating competition levels

            ⚠️ **Important Notes:**
            • **Non-refundable**: Unsuccessful bids forfeit processing fee
            • **Binding**: Successful bids are legally binding
            • **Validity**: COE valid for 10 years from issue date
            • **Transfer**: COE can be transferred with vehicle ownership

            💡 **Need help with bidding strategy?** Our team can guide you through the process!"""
                    
        dispatcher.utter_message(text=response)
        return []



class ActionCOETrends(AutoLoggedAction):
    def name(self) -> Text:
        return "action_coe_trends"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        current_prices = get_live_coe_prices()
        
        if current_prices is None:
            response = COE_SERVICE_UNAVAILABLE_MESSAGE
        else:
            prices = current_prices['current_prices']
            trends = current_prices['trends']
            
            response = f"""📈 **COE Price Trends & Market Analysis**

        📊 **Current Month ({current_prices['bidding_period']}):**
        🚗 **Category A:** ${prices['A']:,} {trends['A']}
        🚙 **Category B:** ${prices['B']:,} {trends['B']}
        🚚 **Category C:** ${prices['C']:,} {trends['C']}
        🏍️ **Category D:** ${prices['D']:,} {trends['D']}
        🔄 **Category E:** ${prices['E']:,} {trends['E']}

        📉 **Market Factors Affecting COE Prices:**
        • **Supply**: Government quota allocation
        • **Demand**: Vehicle registration applications
        • **Economic Conditions**: GDP growth, employment rates
        • **Policy Changes**: EV incentives, car-lite initiatives
        • **Season**: Chinese New Year, mid-year bonuses

        🎯 **Buying Recommendations:**
        • **Best Value**: Category A (small cars)
        • **Luxury Cars**: Category B (higher investment)
        • **Commercial**: Category C (business use)
        • **Motorcycles**: Category D (most affordable)
        • **Flexibility**: Category E (premium option)

        ⏰ **Optimal Bidding Times:**
        • **Mid-month**: Generally lower competition
        • **Avoid**: Month-end salary periods
        • **Strategy**: Monitor 2-3 bidding cycles before buying

        💡 **Want detailed trend analysis?** Ask about specific categories or time periods!"""

            # Generate trend chart
            try:
                historical_data = get_historical_coe_data()
                chart_html = get_chart_for_coe_response(prices, historical_data, 'trend')
                if chart_html:
                    response += f"\n\n{chart_html}"
            except Exception as e:
                pass

        dispatcher.utter_message(text=response)
        return []

class ActionPQPChecker(AutoLoggedAction):
    def name(self) -> Text:
        return "action_pqp_checker"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        current_prices = get_live_coe_prices()
        
        if current_prices is None:
            response = COE_SERVICE_UNAVAILABLE_MESSAGE
        else:
            prices = current_prices['current_prices']
            pqp = current_prices.get('pqp_prices', {})
            
            # Calculate savings by using PQP vs current prices
            savings = {}
            for category in ['A', 'B', 'C', 'D', 'E']:
                current = prices.get(category, 0)
                pqp_price = pqp.get(category, 0)
                if pqp_price > 0:
                    savings[category] = current - pqp_price
                else:
                    savings[category] = 0
            
            response = f"""🔍 **PQP (Prevailing Quota Premium) Checker**

📋 **What is PQP?**
PQP is the previous month's COE price, used for 5-year COE renewals as an alternative to current bidding prices.

📊 **Current PQP vs Latest COE Prices:**

🚗 **Category A:**
• **PQP (Renewal):** ${pqp.get('A', 0):,}
• **Current COE:** ${prices['A']:,}
• **Savings:** {'+$' + str(abs(savings['A'])) + ' (PQP cheaper)' if savings['A'] > 0 else '-$' + str(abs(savings['A'])) + ' (Current cheaper)' if savings['A'] < 0 else 'Same price'}

🚙 **Category B:**
• **PQP (Renewal):** ${pqp.get('B', 0):,}
• **Current COE:** ${prices['B']:,}
• **Savings:** {'+$' + str(abs(savings['B'])) + ' (PQP cheaper)' if savings['B'] > 0 else '-$' + str(abs(savings['B'])) + ' (Current cheaper)' if savings['B'] < 0 else 'Same price'}

🚚 **Category C:**
• **PQP (Renewal):** ${pqp.get('C', 0):,}
• **Current COE:** ${prices['C']:,}
• **Savings:** {'+$' + str(abs(savings['C'])) + ' (PQP cheaper)' if savings['C'] > 0 else '-$' + str(abs(savings['C'])) + ' (Current cheaper)' if savings['C'] < 0 else 'Same price'}

🏍️ **Category D:**
• **PQP (Renewal):** ${pqp.get('D', 0):,}
• **Current COE:** ${prices['D']:,}
• **Savings:** {'+$' + str(abs(savings['D'])) + ' (PQP cheaper)' if savings['D'] > 0 else '-$' + str(abs(savings['D'])) + ' (Current cheaper)' if savings['D'] < 0 else 'Same price'}

🔄 **Category E:**
• **PQP (Renewal):** ${pqp.get('E', 0):,}
• **Current COE:** ${prices['E']:,}
• **Savings:** {'+$' + str(abs(savings['E'])) + ' (PQP cheaper)' if savings['E'] > 0 else '-$' + str(abs(savings['E'])) + ' (Current cheaper)' if savings['E'] < 0 else 'Same price'}

🔄 **Renewal Options:**
• **5-Year Renewal:** Pay PQP amount
• **10-Year Renewal:** Pay current COE bidding price

📅 **Period Information:**
• **PQP Period:** {current_prices.get('previous_period', 'N/A')}
• **Current Period:** {current_prices['bidding_period']}

💡 **Renewal Recommendation:**
{'Choose PQP for 5-year renewal - better value!' if sum(savings.values()) > 0 else 'Consider 10-year renewal if you plan long-term ownership.' if sum(savings.values()) < 0 else 'Both options are similarly priced.'}"""

        dispatcher.utter_message(text=response)
        return []

class ActionCOEPrediction(AutoLoggedAction):
    def name(self) -> Text:
        return "action_coe_prediction"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        # First, provide explanation of COE prediction methodology
        explanation_response = f"""🔮 **COE Price Prediction Methodology Explained**

📊 **How Our Predictions Work:**
Our COE price predictions use advanced statistical analysis and machine learning algorithms to forecast future prices based on historical data patterns.


📈 **Data Sources:**
✅ Official LTA historical COE bidding results
✅ Multi-year price trends and patterns
✅ Seasonal buying behavior analysis
✅ Market volatility assessments
✅ Economic indicators correlation

🎯 **Prediction Accuracy:**
• **Short-term (1 month):** Higher accuracy due to trend continuation
• **Medium-term (3 months):** Good accuracy with seasonal adjustments
• **Long-term (6 months):** Moderate accuracy due to external factors

⚠️ **Important Disclaimers:**
• Predictions are based on historical patterns and statistical analysis
• Market conditions, government policies, and external factors can cause deviations
• These are estimates, not guarantees of future prices
• Use predictions as guidance, not definitive investment advice

Now, let me provide you with the detailed predictions based on current market data:
"""

        dispatcher.utter_message(text=explanation_response)
        
        current_prices = get_live_coe_prices()
        
        if current_prices is None:
            response = COE_SERVICE_UNAVAILABLE_MESSAGE
        else:
            prices = current_prices['current_prices']
            current_date = datetime.now()
            
            # Fetch historical data for trend analysis
            historical_data = get_historical_coe_data()
            
            def calculate_predictions(category, current_price):
                """Advanced data-driven predictions using statistical analysis of historical patterns"""
                
                if len(historical_data) < 6:
                    return {
                        'next_month': current_price,
                        'three_month': current_price,
                        'six_month': current_price,
                        'confidence': 'Low',
                        'analysis': 'Insufficient historical data for reliable predictions'
                    }
                
                # Extract price series for this category
                prices = []
                dates = []
                for record in historical_data:
                    if category in record:
                        prices.append(record[category])
                        dates.append(record['date'])
                
                if len(prices) < 6:
                    return {
                        'next_month': current_price,
                        'three_month': current_price,
                        'six_month': current_price,
                        'confidence': 'Low',
                        'analysis': f'Insufficient data for category {category}'
                    }
                
                # Reverse to get chronological order (oldest first)
                prices.reverse()
                dates.reverse()
                
                # 1. MOVING AVERAGES ANALYSIS
                def calculate_moving_average(data, period):
                    if len(data) < period:
                        return data[-1] if data else 0
                    return sum(data[-period:]) / period
                
                ma_3 = calculate_moving_average(prices, 3)
                ma_6 = calculate_moving_average(prices, 6)
                ma_12 = calculate_moving_average(prices, 12) if len(prices) >= 12 else ma_6
                
                # 2. TREND ANALYSIS (Linear Regression)
                def calculate_trend(data, periods=6):
                    if len(data) < 3:
                        return 0
                    
                    recent_data = data[-periods:] if len(data) >= periods else data
                    n = len(recent_data)
                    x_values = list(range(n))
                    
                    # Simple linear regression
                    x_mean = sum(x_values) / n
                    y_mean = sum(recent_data) / n
                    
                    numerator = sum((x_values[i] - x_mean) * (recent_data[i] - y_mean) for i in range(n))
                    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
                    
                    if denominator == 0:
                        return 0
                    
                    slope = numerator / denominator
                    return slope
                
                trend_slope = calculate_trend(prices, 6)
                long_trend = calculate_trend(prices, 12) if len(prices) >= 12 else trend_slope
                
                # 3. VOLATILITY ANALYSIS
                def calculate_volatility(data, periods=6):
                    if len(data) < 2:
                        return 0
                    
                    recent_data = data[-periods:] if len(data) >= periods else data
                    changes = []
                    for i in range(1, len(recent_data)):
                        change = (recent_data[i] - recent_data[i-1]) / recent_data[i-1]
                        changes.append(change)
                    
                    if not changes:
                        return 0
                    
                    # Standard deviation of percentage changes
                    mean_change = sum(changes) / len(changes)
                    variance = sum((change - mean_change) ** 2 for change in changes) / len(changes)
                    return variance ** 0.5  # Standard deviation
                
                volatility = calculate_volatility(prices, 6)
                
                # 4. SEASONAL PATTERN ANALYSIS (From actual data)
                def analyze_seasonal_patterns(price_data, date_data):
                    monthly_patterns = {}
                    for i, date in enumerate(date_data):
                        month = date.month
                        if month not in monthly_patterns:
                            monthly_patterns[month] = []
                        if i > 0:  # Calculate month-over-month change
                            change = (price_data[i] - price_data[i-1]) / price_data[i-1]
                            monthly_patterns[month].append(change)
                    
                    # Average change for each month
                    seasonal_multipliers = {}
                    for month, changes in monthly_patterns.items():
                        if changes:
                            avg_change = sum(changes) / len(changes)
                            seasonal_multipliers[month] = 1 + avg_change
                        else:
                            seasonal_multipliers[month] = 1.0
                    
                    return seasonal_multipliers
                
                seasonal_patterns = analyze_seasonal_patterns(prices, dates)
                
                # 5. SUPPORT/RESISTANCE LEVELS
                def find_support_resistance(data, window=3):
                    if len(data) < window * 2:
                        return current_price, current_price
                    
                    # Find local minima (support) and maxima (resistance)
                    supports = []
                    resistances = []
                    
                    for i in range(window, len(data) - window):
                        # Check if it's a local minimum
                        is_support = all(data[i] <= data[j] for j in range(i-window, i+window+1) if j != i)
                        if is_support:
                            supports.append(data[i])
                        
                        # Check if it's a local maximum  
                        is_resistance = all(data[i] >= data[j] for j in range(i-window, i+window+1) if j != i)
                        if is_resistance:
                            resistances.append(data[i])
                    
                    support_level = max(supports) if supports else min(data[-6:])
                    resistance_level = min(resistances) if resistances else max(data[-6:])
                    
                    return support_level, resistance_level
                
                support, resistance = find_support_resistance(prices)
                
                # 6. MOMENTUM ANALYSIS
                def calculate_momentum(data, period=3):
                    if len(data) < period + 1:
                        return 0
                    return (data[-1] - data[-period-1]) / data[-period-1]
                
                momentum = calculate_momentum(prices, 3)
                
                # 7. PREDICTIVE MODEL CALCULATION
                base_price = current_price
                
                # Get seasonal factor for next months
                next_month_num = (current_date.month % 12) + 1
                three_month_num = ((current_date.month + 2) % 12) + 1
                six_month_num = ((current_date.month + 5) % 12) + 1
                
                seasonal_next = seasonal_patterns.get(next_month_num, 1.0)
                seasonal_three = seasonal_patterns.get(three_month_num, 1.0)
                seasonal_six = seasonal_patterns.get(six_month_num, 1.0)
                
                # Trend projection (monthly slope)
                trend_factor_1m = 1 + (trend_slope * 1)
                trend_factor_3m = 1 + (trend_slope * 3)
                trend_factor_6m = 1 + (long_trend * 6)
                
                # Volatility bounds
                vol_factor = min(0.1, volatility * 2)  # Cap volatility impact
                
                # Mean reversion factor (if too far from moving average)
                ma_distance = (current_price - ma_6) / ma_6 if ma_6 > 0 else 0
                reversion_factor = 1 - (ma_distance * 0.3)  # Pull back towards mean
                
                # Calculate predictions with confidence intervals
                next_month_pred = int(base_price * seasonal_next * trend_factor_1m * reversion_factor)
                three_month_pred = int(base_price * seasonal_three * trend_factor_3m * (reversion_factor ** 0.5))
                six_month_pred = int(base_price * seasonal_six * trend_factor_6m)
                
                # Apply support/resistance bounds
                next_month_pred = max(support * 0.95, min(resistance * 1.05, next_month_pred))
                three_month_pred = max(support * 0.90, min(resistance * 1.10, three_month_pred))
                six_month_pred = max(support * 0.85, min(resistance * 1.15, six_month_pred))
                
                # ENHANCED CONFIDENCE CALCULATION - Multi-Factor Analysis
                confidence_score = 0
                confidence_factors = []
                
                # 1. Data Quality Factor (35% weight)
                if len(prices) >= 24:  # 2+ years of data
                    confidence_score += 35
                    confidence_factors.append("Excellent data depth (24+ months)")
                elif len(prices) >= 12:  # 1+ year of data
                    confidence_score += 25
                    confidence_factors.append("Good data depth (12+ months)")
                elif len(prices) >= 6:  # 6+ months of data
                    confidence_score += 15
                    confidence_factors.append("Moderate data depth (6+ months)")
                else:
                    confidence_score += 5
                    confidence_factors.append("Limited data depth (<6 months)")
                
                # 2. Market Stability Factor (25% weight)
                if volatility < 0.03:  # Very stable market
                    confidence_score += 25
                    confidence_factors.append("Very stable market conditions")
                elif volatility < 0.06:  # Moderate stability
                    confidence_score += 18
                    confidence_factors.append("Stable market conditions")
                elif volatility < 0.10:  # Some volatility
                    confidence_score += 10
                    confidence_factors.append("Moderate market volatility")
                else:  # High volatility
                    confidence_score += 3
                    confidence_factors.append("High market volatility")
                
                # 3. Trend Consistency Factor (25% weight)
                if abs(trend_slope) < 25:  # Very stable trend
                    confidence_score += 25
                    confidence_factors.append("Consistent price trend")
                elif abs(trend_slope) < 75:  # Moderate trend
                    confidence_score += 18
                    confidence_factors.append("Moderate trend consistency")
                elif abs(trend_slope) < 150:  # Strong trend
                    confidence_score += 10
                    confidence_factors.append("Strong directional trend")
                else:  # Extreme trend
                    confidence_score += 5
                    confidence_factors.append("Extreme price movements")
                
                # 4. Mean Reversion Factor (15% weight)
                if abs(ma_distance) < 0.03:  # Very close to average
                    confidence_score += 15
                    confidence_factors.append("Price near historical average")
                elif abs(ma_distance) < 0.08:  # Reasonably close
                    confidence_score += 10
                    confidence_factors.append("Price within normal range")
                elif abs(ma_distance) < 0.15:  # Somewhat distant
                    confidence_score += 5
                    confidence_factors.append("Price moderately above/below average")
                else:  # Very distant from average
                    confidence_score += 2
                    confidence_factors.append("Price significantly deviated from average")
                
                # 5. R-Squared Factor for Trend Reliability (bonus points)
                if len(prices) >= 6:
                    recent_data = prices[-6:]
                    x_vals = list(range(len(recent_data)))
                    
                    # Calculate R-squared for trend line fit
                    x_mean = sum(x_vals) / len(x_vals)
                    y_mean = sum(recent_data) / len(recent_data)
                    
                    ss_tot = sum((y - y_mean) ** 2 for y in recent_data)
                    ss_res = sum((recent_data[i] - (y_mean + trend_slope * (x_vals[i] - x_mean))) ** 2 for i in range(len(recent_data)))
                    
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                    
                    if r_squared > 0.8:  # Strong correlation
                        confidence_score += 10
                        confidence_factors.append(f"Strong trend correlation (R²={r_squared:.2f})")
                    elif r_squared > 0.6:  # Moderate correlation
                        confidence_score += 5
                        confidence_factors.append(f"Moderate trend correlation (R²={r_squared:.2f})")
                
                # Cap confidence score at 100
                confidence_score = min(100, confidence_score)
                
                # Enhanced confidence levels with more granularity
                if confidence_score >= 85:
                    confidence_level = 'Very High'
                elif confidence_score >= 70:
                    confidence_level = 'High'
                elif confidence_score >= 55:
                    confidence_level = 'Moderate'
                elif confidence_score >= 40:
                    confidence_level = 'Low'
                else:
                    confidence_level = 'Very Low'
                
                # Market analysis summary
                trend_direction = 'Upward' if trend_slope > 20 else 'Downward' if trend_slope < -20 else 'Sideways'
                volatility_level = 'High' if volatility > 0.08 else 'Moderate' if volatility > 0.04 else 'Low'
                
                return {
                    'next_month': next_month_pred,
                    'three_month': three_month_pred,
                    'six_month': six_month_pred,
                    'confidence': confidence_level,
                    'confidence_score': confidence_score,
                    'analysis': {
                        'trend': f'{trend_direction} trend (${trend_slope:.0f}/month)',
                        'volatility': f'{volatility_level} volatility ({volatility:.1%})',
                        'momentum': f'{"Positive" if momentum > 0 else "Negative"} momentum ({momentum:.1%})',
                        'support_resistance': f'Support: ${support:,.0f}, Resistance: ${resistance:,.0f}',
                        'moving_averages': f'MA3: ${ma_3:,.0f}, MA6: ${ma_6:,.0f}',
                        'data_points': f'{len(prices)} months of historical data'
                    }
                }
            
            # Generate predictions for all categories
            predictions = {}
            for category in ['A', 'B', 'C', 'D', 'E']:
                if category in prices:
                    predictions[category] = calculate_predictions(category, prices[category])
            
            # Professional response with modern styling and interactive elements
            response = f"""🔮 **INTELLIGENT COE FORECASTING SYSTEM**

📊 **ADVANCED STATISTICAL ANALYSIS DASHBOARD**

**🚗 CATEGORY A ANALYSIS**
┌─────────────────────────────────────────┐
│ **Current Price**: ${prices['A']:,.0f}                    │
│ **📈 Next Month**: ${predictions['A']['next_month']:,.0f} ({'+' if predictions['A']['next_month'] > prices['A'] else ''}${predictions['A']['next_month'] - prices['A']:,.0f})     │
│ **📊 3-Month**: ${predictions['A']['three_month']:,.0f}                      │
│ **🎯 6-Month**: ${predictions['A']['six_month']:,.0f}                      │
│ **Trend**: {predictions['A']['analysis']['trend']}           │
│ **Confidence**: {predictions['A']['confidence']} ({predictions['A']['confidence_score']}/100)        │
└─────────────────────────────────────────┘

**🚙 CATEGORY B ANALYSIS**
┌─────────────────────────────────────────┐
│ **Current Price**: ${prices['B']:,.0f}                    │
│ **📈 Next Month**: ${predictions['B']['next_month']:,.0f} ({'+' if predictions['B']['next_month'] > prices['B'] else ''}${predictions['B']['next_month'] - prices['B']:,.0f})     │
│ **📊 3-Month**: ${predictions['B']['three_month']:,.0f}                      │
│ **🎯 6-Month**: ${predictions['B']['six_month']:,.0f}                      │
│ **Trend**: {predictions['B']['analysis']['trend']}           │
│ **Confidence**: {predictions['B']['confidence']} ({predictions['B']['confidence_score']}/100)        │
└─────────────────────────────────────────┘

**🚚 CATEGORY C ANALYSIS**
┌─────────────────────────────────────────┐
│ **Current Price**: ${prices['C']:,.0f}                    │
│ **📈 Next Month**: ${predictions['C']['next_month']:,.0f} ({'+' if predictions['C']['next_month'] > prices['C'] else ''}${predictions['C']['next_month'] - prices['C']:,.0f})     │
│ **📊 3-Month**: ${predictions['C']['three_month']:,.0f}                      │
│ **🎯 6-Month**: ${predictions['C']['six_month']:,.0f}                      │
│ **Trend**: {predictions['C']['analysis']['trend']}           │
│ **Confidence**: {predictions['C']['confidence']} ({predictions['C']['confidence_score']}/100)        │
└─────────────────────────────────────────┘

**🏍️ CATEGORY D ANALYSIS**
┌─────────────────────────────────────────┐
│ **Current Price**: ${prices['D']:,.0f}                    │
│ **📈 Next Month**: ${predictions['D']['next_month']:,.0f} ({'+' if predictions['D']['next_month'] > prices['D'] else ''}${predictions['D']['next_month'] - prices['D']:,.0f})     │
│ **📊 3-Month**: ${predictions['D']['three_month']:,.0f}                      │
│ **🎯 6-Month**: ${predictions['D']['six_month']:,.0f}                      │
│ **Trend**: {predictions['D']['analysis']['trend']}           │
│ **Confidence**: {predictions['D']['confidence']} ({predictions['D']['confidence_score']}/100)        │
└─────────────────────────────────────────┘

**🔄 CATEGORY E ANALYSIS**
┌─────────────────────────────────────────┐
│ **Current Price**: ${prices['E']:,.0f}                    │
│ **📈 Next Month**: ${predictions['E']['next_month']:,.0f} ({'+' if predictions['E']['next_month'] > prices['E'] else ''}${predictions['E']['next_month'] - prices['E']:,.0f})     │
│ **📊 3-Month**: ${predictions['E']['three_month']:,.0f}                      │
│ **🎯 6-Month**: ${predictions['E']['six_month']:,.0f}                      │
│ **Trend**: {predictions['E']['analysis']['trend']}           │
│ **Confidence**: {predictions['E']['confidence']} ({predictions['E']['confidence_score']}/100)        │
└─────────────────────────────────────────┘

💡 **Note:** These are sophisticated predictions based on mathematical analysis of historical patterns. Market conditions, policy changes, and external factors may cause deviations."""

            # Try to generate prediction chart
            try:
                historical_data = get_historical_coe_data()
                chart_html = get_chart_for_coe_response(prices, historical_data, 'prediction')
                if chart_html:
                    # Combine text and chart into a single message for proper frontend processing
                    response = f"{response}\n\n{chart_html}"
                        
            except Exception as e:
                logger.warning(f"Could not generate prediction chart: {e}")
                # Use base response if chart generation fails
                pass

            

        dispatcher.utter_message(text=response)
        return []

class ActionCOETimingRecommendation(AutoLoggedAction):
    def name(self) -> Text:
        return "action_coe_timing_recommendation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        current_prices = get_live_coe_prices()
        
        if current_prices is None:
            response = COE_SERVICE_UNAVAILABLE_MESSAGE
        else:
            prices = current_prices['current_prices']
            current_date = datetime.now()
            month = current_date.month
            
            # Get historical data for sophisticated analysis
            historical_data = get_historical_coe_data()
            
            def analyze_market_timing():
                """Advanced market timing analysis based on historical data patterns"""
                
                if len(historical_data) < 12:
                    return {
                        'timing_score': 3,
                        'season_advice': '📊 **Limited Data** - Standard market conditions',
                        'market_state': 'Neutral',
                        'data_insights': 'Insufficient historical data for detailed analysis'
                    }
                
                # 1. SEASONAL ANALYSIS FROM ACTUAL DATA
                monthly_performance = {}
                for record in historical_data:
                    record_month = record['date'].month
                    if record_month not in monthly_performance:
                        monthly_performance[record_month] = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}
                    
                    for category in ['A', 'B', 'C', 'D', 'E']:
                        if category in record:
                            monthly_performance[record_month][category].append(record[category])
                
                # Calculate average prices by month
                monthly_averages = {}
                for month_num, data in monthly_performance.items():
                    monthly_averages[month_num] = {}
                    for category, prices_list in data.items():
                        if prices_list:
                            monthly_averages[month_num][category] = sum(prices_list) / len(prices_list)
                
                # Determine if current month is historically good/bad for buying
                current_month_data = monthly_averages.get(month, {})
                
                # Compare current month to annual average
                annual_averages = {}
                total_months = 0
                for month_data in monthly_averages.values():
                    total_months += 1
                    for category, avg_price in month_data.items():
                        if category not in annual_averages:
                            annual_averages[category] = []
                        annual_averages[category].append(avg_price)
                
                # Calculate overall annual averages
                overall_averages = {}
                for category, price_list in annual_averages.items():
                    if price_list:
                        overall_averages[category] = sum(price_list) / len(price_list)
                
                # 2. CURRENT MARKET STATE ANALYSIS
                current_vs_historical = {}
                market_position_score = 0
                
                for category in ['A', 'B']:  # Focus on main car categories
                    if category in prices and category in overall_averages:
                        current_price = prices[category]
                        historical_avg = overall_averages[category]
                        deviation = (current_price - historical_avg) / historical_avg
                        current_vs_historical[category] = deviation
                        
                        # Score based on how far current price is from historical average
                        if deviation < -0.1:  # 10% below average - excellent time
                            market_position_score += 5
                        elif deviation < -0.05:  # 5% below average - good time
                            market_position_score += 4
                        elif deviation < 0.05:  # Within 5% - neutral
                            market_position_score += 3
                        elif deviation < 0.1:  # 5-10% above - caution
                            market_position_score += 2
                        else:  # >10% above - wait
                            market_position_score += 1
                
                market_position_score = market_position_score / 2 if len(current_vs_historical) > 0 else 3
                
                # 3. TREND MOMENTUM ANALYSIS
                def calculate_recent_momentum():
                    if len(historical_data) < 3:
                        return 0, 'Insufficient data'
                    
                    # Get last 3 months of data
                    recent_data = historical_data[:3]  # Already sorted newest first
                    momentum_scores = []
                    
                    for i in range(len(recent_data) - 1):
                        current_record = recent_data[i]
                        previous_record = recent_data[i + 1]
                        
                        for category in ['A', 'B']:
                            if category in current_record and category in previous_record:
                                change = (current_record[category] - previous_record[category]) / previous_record[category]
                                momentum_scores.append(change)
                    
                    if not momentum_scores:
                        return 0, 'No momentum data'
                    
                    avg_momentum = sum(momentum_scores) / len(momentum_scores)
                    
                    if avg_momentum > 0.03:  # Rising more than 3%
                        return 1, 'Strong upward momentum - prices rising'
                    elif avg_momentum > 0.01:  # Rising 1-3%
                        return 2, 'Moderate upward momentum'
                    elif avg_momentum > -0.01:  # Stable within 1%
                        return 4, 'Stable market conditions'
                    elif avg_momentum > -0.03:  # Declining 1-3%
                        return 5, 'Moderate downward momentum - good time to buy'
                    else:  # Declining more than 3%
                        return 5, 'Strong downward momentum - excellent time to buy'
                
                momentum_score, momentum_desc = calculate_recent_momentum()
                
                # 4. VOLATILITY ANALYSIS
                def calculate_market_volatility():
                    if len(historical_data) < 6:
                        return 3, 'Unknown volatility'
                    
                    # Calculate volatility for main categories
                    volatilities = []
                    for category in ['A', 'B']:
                        category_prices = []
                        for record in historical_data[:6]:  # Last 6 months
                            if category in record:
                                category_prices.append(record[category])
                        
                        if len(category_prices) >= 3:
                            # Calculate standard deviation
                            mean_price = sum(category_prices) / len(category_prices)
                            variance = sum((price - mean_price) ** 2 for price in category_prices) / len(category_prices)
                            volatility = (variance ** 0.5) / mean_price  # Coefficient of variation
                            volatilities.append(volatility)
                    
                    if not volatilities:
                        return 3, 'Cannot calculate volatility'
                    
                    avg_volatility = sum(volatilities) / len(volatilities)
                    
                    if avg_volatility > 0.08:  # High volatility
                        return 2, 'High market volatility - risky timing'
                    elif avg_volatility > 0.04:  # Moderate volatility
                        return 3, 'Moderate market volatility'
                    else:  # Low volatility
                        return 5, 'Low market volatility - stable conditions'
                
                volatility_score, volatility_desc = calculate_market_volatility()
                
                # 5. COMPOSITE TIMING SCORE
                # Weight different factors
                timing_score = (
                    market_position_score * 0.4 +  # 40% weight on current vs historical
                    momentum_score * 0.3 +         # 30% weight on recent momentum
                    volatility_score * 0.3          # 30% weight on volatility
                )
                
                timing_score = max(1, min(5, round(timing_score)))  # Ensure 1-5 range
                
                # 6. GENERATE ADVICE BASED ON ANALYSIS
                if timing_score >= 4.5:
                    season_advice = f"🎯 **Excellent Timing** - {momentum_desc}, {volatility_desc}"
                    market_state = "Buyer's Market"
                elif timing_score >= 3.5:
                    season_advice = f"✅ **Good Timing** - {momentum_desc}, {volatility_desc}"
                    market_state = "Favorable Conditions"
                elif timing_score >= 2.5:
                    season_advice = f"🟡 **Moderate Timing** - {momentum_desc}, {volatility_desc}"
                    market_state = "Neutral Market"
                elif timing_score >= 1.5:
                    season_advice = f"⚠️ **Challenging Timing** - {momentum_desc}, {volatility_desc}"
                    market_state = "Seller's Market"
                else:
                    season_advice = f"🔴 **Poor Timing** - {momentum_desc}, {volatility_desc}"
                    market_state = "Unfavorable Conditions"
                
                # Generate data insights
                insights = []
                for category, deviation in current_vs_historical.items():
                    if deviation < -0.05:
                        insights.append(f"Category {category} is {abs(deviation):.1%} below historical average")
                    elif deviation > 0.05:
                        insights.append(f"Category {category} is {deviation:.1%} above historical average")
                
                data_insights = '; '.join(insights) if insights else 'Prices near historical averages'
                
                return {
                    'timing_score': int(timing_score),
                    'season_advice': season_advice,
                    'market_state': market_state,
                    'data_insights': data_insights,
                    'momentum_analysis': momentum_desc,
                    'volatility_analysis': volatility_desc,
                    'historical_comparison': current_vs_historical
                }
            
            # Perform advanced analysis
            market_analysis = analyze_market_timing()
            timing_score = market_analysis['timing_score']
            
            # Generate specific recommendations based on analysis
            if timing_score >= 4:
                action_advice = "🟢 **BUY NOW** - Data supports immediate purchase"
                strategy = "Market conditions favor buyers - act quickly"
            elif timing_score == 3:
                action_advice = "🟡 **NEUTRAL TIMING** - Reasonable time to buy if needed"
                strategy = "Balanced market - buy if urgent, wait if flexible"
            else:
                action_advice = "🔴 **CONSIDER WAITING** - Data suggests poor timing"
                strategy = "Market conditions favor waiting for better entry point"
            
            # Renewal vs New Purchase analysis (enhanced)
            pqp = current_prices.get('pqp_prices', {})
            renewal_analysis = {}
            
            for category in ['A', 'B', 'C', 'D', 'E']:
                if category in prices and category in pqp:
                    current = prices[category]
                    pqp_price = pqp[category]
                    if pqp_price > 0:
                        savings = current - pqp_price
                        savings_pct = (savings / current) * 100
                        
                        if savings > 8000:
                            renewal_analysis[category] = f"💰 Strong case for 5-year renewal (Save ${savings:,}, {savings_pct:.1f}%)"
                        elif savings > 3000:
                            renewal_analysis[category] = f"✅ Good case for 5-year renewal (Save ${savings:,}, {savings_pct:.1f}%)"
                        elif savings > 0:
                            renewal_analysis[category] = f"⚖️ Slight advantage for 5-year renewal (Save ${savings:,})"
                        elif savings > -3000:
                            renewal_analysis[category] = f"⚖️ Similar costs - choose based on plans (${abs(savings):,} difference)"
                        else:
                            renewal_analysis[category] = f"🔄 Consider 10-year renewal (${abs(savings):,} more for longer validity)"
            
            response = f"""⏰ **Advanced COE Timing Analysis** (Data-Driven Recommendations)

📅 **Current Market Assessment ({current_date.strftime('%B %Y')})**
{market_analysis['season_advice']}

🎯 **Overall Recommendation:**
{action_advice}

📊 **Timing Score: {timing_score}/5** ⭐{'⭐' * (timing_score-1)}
**Market State:** {market_analysis['market_state']}

🔍 **Data-Driven Insights:**
• **Historical Position:** {market_analysis['data_insights']}
• **Market Momentum:** {market_analysis['momentum_analysis']}
• **Volatility Assessment:** {market_analysis['volatility_analysis']}
• **Analysis Based On:** {len(historical_data)} months of actual LTA data

🏆 **Strategic Recommendations:**

**For New Car Buyers:**
• **Primary Strategy:** {strategy}
• **Risk Level:** {'Low' if timing_score >= 4 else 'Moderate' if timing_score >= 3 else 'High'}
• **Flexibility Advice:** {'Lock in now if considering purchase' if timing_score >= 4 else 'Monitor for 1-2 cycles if flexible' if timing_score == 3 else 'Strong advantage to wait if timeline allows'}

**For COE Renewals (Data-Based Analysis):**
🚗 **Category A:** {renewal_analysis.get('A', 'Analyze based on your specific renewal timeline')}
🚙 **Category B:** {renewal_analysis.get('B', 'Analyze based on your specific renewal timeline')}
🚚 **Category C:** {renewal_analysis.get('C', 'Analyze based on your specific renewal timeline')}
🏍️ **Category D:** {renewal_analysis.get('D', 'Analyze based on your specific renewal timeline')}
🔄 **Category E:** {renewal_analysis.get('E', 'Analyze based on your specific renewal timeline')}

📈 **Market Outlook (Based on Current Analysis):**
• **Trend Direction:** {'Upward pressure expected' if timing_score <= 2 else 'Stable to slight increase' if timing_score == 3 else 'Favorable conditions' if timing_score == 4 else 'Excellent entry point'}
• **Recommendation Confidence:** {'High' if len(historical_data) >= 12 else 'Moderate' if len(historical_data) >= 6 else 'Limited data'}
• **Next Review:** Monitor market in 2-4 weeks for trend confirmation

💡 **Intelligent Timing Framework:**
✅ Historical price analysis vs current levels
✅ Momentum indicators from recent price movements  
✅ Volatility assessment for risk evaluation
✅ Statistical confidence based on data depth
✅ Category-specific PQP vs market price comparison

📊 **Powered by:** {len(historical_data)} months of LTA historical data with advanced statistical analysis"""

        dispatcher.utter_message(text=response)
        return []

class ActionCOEVisualization(AutoLoggedAction):
    def name(self) -> Text:
        return "action_coe_visualization"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Check if COE feature is enabled for this client
        client_id = tracker.get_slot("client_id")
        if not check_coe_feature_enabled(client_id):
            dispatcher.utter_message(text=COE_FEATURE_DISABLED_MESSAGE)
            return []
        
        user_text = tracker.latest_message.get("text", "").lower()
        
        # Determine chart type from user request
        chart_type = 'comparison'  # default
        if any(word in user_text for word in ['trend', 'history', 'historical', 'past']):
            chart_type = 'trend'
        elif any(word in user_text for word in ['predict', 'forecast', 'future']):
            chart_type = 'prediction'
        elif any(word in user_text for word in ['volatility', 'volatile', 'risk']):
            chart_type = 'volatility'
        elif any(word in user_text for word in ['compare', 'comparison', 'current']):
            chart_type = 'comparison'
        
        current_prices = get_live_coe_prices()
        
        if current_prices is None:
            response = COE_SERVICE_UNAVAILABLE_MESSAGE
        else:
            prices = current_prices['current_prices']
            historical_data = get_historical_coe_data()
            
            chart_titles = {
                'trend': 'COE Price Trends - Historical Analysis',
                'comparison': 'Current COE Price Comparison',
                'volatility': 'COE Price Volatility Analysis',
                'prediction': 'COE Price Predictions'
            }
            
            response = f"""📊 **{chart_titles[chart_type]}**

🎯 **Visual Analysis**: Below is your requested {chart_type} chart showing COE price data.

📈 **Chart Features:**
• **Interactive Data**: All current COE categories (A, B, C, D, E)
• **Singapore Colors**: Category-specific color coding
• **Professional Format**: High-resolution, print-ready charts
• **Real-time Data**: Latest information from LTA Singapore

💡 **Chart Types Available:**
• **Trend Charts**: Historical price movements over time
• **Comparison Charts**: Current prices across all categories
• **Volatility Charts**: Market risk and price stability analysis
• **Prediction Charts**: Future price forecasts with confidence intervals

🔍 **How to Read the Chart:**
• Each color represents a different COE category
• Prices are in Singapore Dollars (SGD)
• Time periods show bidding cycles
• Trend lines indicate market direction"""

            # Generate the requested chart
            try:
                chart_html = get_chart_for_coe_response(prices, historical_data, chart_type)
                if chart_html:
                    response += f"\n\n{chart_html}"
                else:
                    response += "\n\n❌ **Chart generation failed** - Please try again or contact support."
            except Exception as e:
                logger.error(f"Chart generation error: {e}")
                response += "\n\n❌ **Chart generation failed** - Please try again or contact support."

        dispatcher.utter_message(text=response)
        return []