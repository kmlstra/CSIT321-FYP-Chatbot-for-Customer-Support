import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import requests

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api.actions.coe_actions import ActionCOEPrices

class TestCOEPrices(unittest.TestCase):
    """Unit tests for COE Prices feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.action = ActionCOEPrices()
        self.tracker = MagicMock()
        self.domain = MagicMock()
        
    @patch('requests.get')
    def test_get_coe_prices_success(self, mock_get):
        """Test successful COE prices retrieval"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': {
                'records': [
                    {
                        'month': '2024-01',
                        'bidding_no': '1',
                        'vehicle_class': 'Category A',
                        'current_bids_received': '100',
                        'current_premium': '50000'
                    },
                    {
                        'month': '2024-01',
                        'bidding_no': '1',
                        'vehicle_class': 'Category B',
                        'current_bids_received': '150',
                        'current_premium': '75000'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Execute action
        result = self.action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['template'], 'utter_coe_prices')
        self.assertIn('Category A', result[0]['text'])
        self.assertIn('Category B', result[0]['text'])
        self.assertIn('$50,000', result[0]['text'])
        self.assertIn('$75,000', result[0]['text'])
        
    @patch('requests.get')
    def test_get_coe_prices_api_failure(self, mock_get):
        """Test COE prices retrieval when API fails"""
        # Mock API failure
        mock_get.side_effect = requests.RequestException("API Error")
        
        # Execute action
        result = self.action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['template'], 'utter_coe_prices')
        self.assertIn('unable to retrieve', result[0]['text'].lower())
        
    @patch('requests.get')
    def test_get_coe_prices_empty_response(self, mock_get):
        """Test COE prices retrieval with empty response"""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'records': []}}
        mock_get.return_value = mock_response
        
        # Execute action
        result = self.action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['template'], 'utter_coe_prices')
        self.assertIn('no current COE prices', result[0]['text'].lower())
        
    def test_format_coe_data(self):
        """Test COE data formatting"""
        # Test data
        coe_data = [
            {
                'vehicle_class': 'Category A',
                'current_premium': '50000',
                'current_bids_received': '100'
            }
        ]
        
        # Format data
        formatted = self.action.format_coe_data(coe_data)
        
        # Assertions
        self.assertIn('Category A', formatted)
        self.assertIn('$50,000', formatted)
        self.assertIn('100 bids', formatted)

if __name__ == '__main__':
    unittest.main()