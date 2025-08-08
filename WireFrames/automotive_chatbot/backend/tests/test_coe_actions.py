"""Unit Tests for COE Actions
Tests for COE price retrieval, predictions, and query parsing functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.actions.coe_actions import (
    extract_coe_query_details,
    ActionCOEPrices,
    ActionCOEPrediction,
    ActionCOERenewal
)
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Tracker

class TestCOEQueryExtraction(unittest.TestCase):
    """Test COE query parsing and date extraction"""
    
    def test_extract_month_year_basic(self):
        """Test basic month and year extraction"""
        result = extract_coe_query_details("COE prices for March 2024")
        self.assertEqual(result['month'], 3)
        self.assertEqual(result['year'], 2024)
        self.assertFalse(result['prediction_requested'])
    
    def test_extract_prediction_keywords(self):
        """Test prediction keyword detection"""
        test_cases = [
            "predict COE prices for next month",
            "forecast future COE trends",
            "estimate COE prices",
            "what will COE prices be next month"
        ]
        
        for query in test_cases:
            with self.subTest(query=query):
                result = extract_coe_query_details(query)
                self.assertTrue(result['prediction_requested'], f"Failed for query: {query}")
    
    def test_extract_bidding_round(self):
        """Test bidding round detection"""
        test_cases = [
            ("first bidding round March 2024", "first"),
            ("1st COE bidding", "first"),
            ("second round COE prices", "second"),
            ("2nd bidding results", "second")
        ]
        
        for query, expected_round in test_cases:
            with self.subTest(query=query):
                result = extract_coe_query_details(query)
                self.assertEqual(result['bidding_round'], expected_round)
    
    def test_extract_relative_dates(self):
        """Test relative date expressions"""
        current_date = datetime.now()
        
        # Test last month
        result = extract_coe_query_details("COE prices last month")
        if current_date.month == 1:
            self.assertEqual(result['month'], 12)
            self.assertEqual(result['year'], current_date.year - 1)
        else:
            self.assertEqual(result['month'], current_date.month - 1)
            self.assertEqual(result['year'], current_date.year)
    
    def test_extract_numeric_date_formats(self):
        """Test numeric date format parsing"""
        test_cases = [
            ("COE prices 03/2024", 3, 2024),
            ("COE prices 12-2023", 12, 2023),
            ("COE prices 2024/05", 5, 2024)
        ]
        
        for query, expected_month, expected_year in test_cases:
            with self.subTest(query=query):
                result = extract_coe_query_details(query)
                self.assertEqual(result['month'], expected_month)
                self.assertEqual(result['year'], expected_year)
    
    def test_extract_future_dates_as_predictions(self):
        """Test that future dates are marked as predictions"""
        future_year = datetime.now().year + 1
        result = extract_coe_query_details(f"COE prices March {future_year}")
        self.assertEqual(result['month'], 3)
        self.assertEqual(result['year'], future_year)
        self.assertTrue(result['prediction_requested'])

class TestCOEActions(unittest.TestCase):
    """Test COE RASA Actions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dispatcher = Mock(spec=CollectingDispatcher)
        self.tracker = Mock(spec=Tracker)
        self.domain = {}
        
        # Mock tracker.latest_message
        self.tracker.latest_message = {"text": "COE prices"}
        
    def test_action_coe_prices_initialization(self):
        """Test ActionCOEPrices initialization"""
        action = ActionCOEPrices()
        self.assertEqual(action.name(), "action_coe_prices")
    
    @patch('api.actions.coe_actions.rate_limited_lta_request')
    def test_action_coe_prices_success(self, mock_request):
        """Test successful COE price retrieval"""
        # Mock successful API response
        mock_request.return_value = {
            'success': True,
            'data': {
                'category_a': {'current': 95000, 'previous': 90000},
                'category_b': {'current': 105000, 'previous': 100000}
            }
        }
        
        action = ActionCOEPrices()
        self.tracker.latest_message = {"text": "current COE prices"}
        
        result = action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify dispatcher was called
        self.dispatcher.utter_message.assert_called_once()
        
        # Verify the response contains price information
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('95000', response_text)
        self.assertIn('105000', response_text)
        
        # Verify return value
        self.assertEqual(result, [])
    
    @patch('api.actions.coe_actions.rate_limited_lta_request')
    def test_action_coe_prices_api_failure(self, mock_request):
        """Test COE price retrieval when API fails"""
        # Mock API failure
        mock_request.return_value = {
            'success': False,
            'error': 'API unavailable'
        }
        
        action = ActionCOEPrices()
        result = action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify error message was sent
        self.dispatcher.utter_message.assert_called_once()
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('unavailable', response_text.lower())
    
    def test_action_coe_prediction_initialization(self):
        """Test ActionCOEPrediction initialization"""
        action = ActionCOEPrediction()
        self.assertEqual(action.name(), "action_coe_prediction")
    
    @patch('api.actions.coe_actions.rate_limited_lta_request')
    def test_action_coe_prediction_success(self, mock_request):
        """Test successful COE prediction"""
        # Mock successful API response with historical data
        mock_request.return_value = {
            'success': True,
            'data': {
                'category_a': {
                    'current': 95000,
                    'trend': 'increasing',
                    'prediction': 98000
                }
            }
        }
        
        action = ActionCOEPrediction()
        self.tracker.latest_message = {"text": "predict COE prices next month"}
        
        result = action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify dispatcher was called
        self.dispatcher.utter_message.assert_called_once()
        
        # Verify the response contains prediction information
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('prediction', response_text.lower())
    
    def test_action_coe_renewal_initialization(self):
        """Test ActionCOERenewal initialization"""
        action = ActionCOERenewal()
        self.assertEqual(action.name(), "action_coe_renewal")
    
    @patch('api.actions.coe_actions.rate_limited_lta_request')
    def test_action_coe_renewal_pqp_calculation(self, mock_request):
        """Test COE renewal PQP calculation"""
        # Mock successful API response
        mock_request.return_value = {
            'success': True,
            'data': {
                'category_a': {
                    'current': 95000,
                    'pqp': 85000
                }
            }
        }
        
        action = ActionCOERenewal()
        self.tracker.latest_message = {"text": "COE renewal PQP"}
        
        result = action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify dispatcher was called
        self.dispatcher.utter_message.assert_called_once()
        
        # Verify the response contains PQP information
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('pqp', response_text.lower())

class TestCOEDataValidation(unittest.TestCase):
    """Test COE data validation and edge cases"""
    
    def test_invalid_date_handling(self):
        """Test handling of invalid dates"""
        invalid_queries = [
            "COE prices for month 13",
            "COE prices 1999",  # Too old
            "COE prices 2050",  # Too far in future
            "COE prices February 30"  # Invalid date
        ]
        
        for query in invalid_queries:
            with self.subTest(query=query):
                result = extract_coe_query_details(query)
                # Should handle gracefully without crashing
                self.assertIsInstance(result, dict)
    
    def test_empty_query_handling(self):
        """Test handling of empty or malformed queries"""
        empty_queries = [
            "",
            "   ",
            "COE",
            "prices"
        ]
        
        for query in empty_queries:
            with self.subTest(query=query):
                result = extract_coe_query_details(query)
                self.assertIsInstance(result, dict)
                self.assertIn('month', result)
                self.assertIn('year', result)
                self.assertIn('prediction_requested', result)

if __name__ == '__main__':