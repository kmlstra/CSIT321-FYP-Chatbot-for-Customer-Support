"""Unit Tests for Contact Actions
Tests for ActionSmartContact class and contact functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.actions.contact_actions import ActionSmartContact
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Tracker


class TestContactActions(unittest.TestCase):
    """Test Contact RASA Actions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.action = ActionSmartContact()
        self.dispatcher = Mock(spec=CollectingDispatcher)
        self.tracker = Mock(spec=Tracker)
        self.domain = {}
        
        # Mock latest message
        self.tracker.latest_message = {'text': 'test message'}
    
    def test_action_smart_contact_initialization(self):
        """Test ActionSmartContact initialization"""
        action = ActionSmartContact()
        self.assertIsInstance(action, ActionSmartContact)
        self.assertEqual(action.name(), 'action_smart_contact')
    
    @patch('api.actions.contact_actions.datetime')
    @patch('api.actions.contact_actions.pytz')
    def test_get_current_time_context(self, mock_pytz, mock_datetime):
        """Test _get_current_time_context method"""
        # Mock Singapore timezone
        mock_tz = Mock()
        mock_pytz.timezone.return_value = mock_tz
        
        # Mock current time (business hours)
        mock_now = Mock()
        mock_now.hour = 10
        mock_now.weekday.return_value = 1  # Tuesday
        mock_datetime.now.return_value = mock_now
        
        context = self.action._get_current_time_context()
        
        self.assertIsInstance(context, dict)
        self.assertIn('is_business_hours', context)
        self.assertIn('current_hour', context)
        self.assertIn('is_weekend', context)
        mock_pytz.timezone.assert_called_with('Asia/Singapore')
    
    def test_analyze_contact_intent_email(self):
        """Test _analyze_contact_intent method for email intent"""
        test_cases = [
            'I need your email address',
            'How can I email you?',
            'Send me an email',
            'What is your email?'
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                result = self.action._analyze_contact_intent(message)
                self.assertTrue(result['needs_email'])
                self.assertFalse(result['needs_phone'])
                self.assertFalse(result['needs_whatsapp'])
    
    def test_analyze_contact_intent_phone(self):
        """Test _analyze_contact_intent method for phone intent"""
        test_cases = [
            'What is your phone number?',
            'I want to call you',
            'Give me your telephone number',
            'How can I phone you?'
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                result = self.action._analyze_contact_intent(message)
                self.assertTrue(result['needs_phone'])
                self.assertFalse(result['needs_email'])
                self.assertFalse(result['needs_whatsapp'])
    
    def test_analyze_contact_intent_whatsapp(self):
        """Test _analyze_contact_intent method for WhatsApp intent"""
        test_cases = [
            'Can I WhatsApp you?',
            'What is your WhatsApp number?',
            'Send me a WhatsApp message',
            'I prefer WhatsApp communication'
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                result = self.action._analyze_contact_intent(message)
                self.assertTrue(result['needs_whatsapp'])
                self.assertFalse(result['needs_email'])
                self.assertFalse(result['needs_phone'])
    
    def test_analyze_contact_intent_hours(self):
        """Test _analyze_contact_intent method for hours intent"""
        test_cases = [
            'What are your operating hours?',
            'When are you open?',
            'What time do you close?',
            'Are you open on Sunday?'
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                result = self.action._analyze_contact_intent(message)
                self.assertTrue(result['needs_hours'])
                self.assertFalse(result['needs_email'])
                self.assertFalse(result['needs_phone'])
    
    def test_analyze_contact_intent_location(self):
        """Test _analyze_contact_intent method for location intent"""
        test_cases = [
            'Where is your office?',
            'What is your address?',
            'How can I visit you?',
            'Show me directions to your showroom'
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                result = self.action._analyze_contact_intent(message)
                self.assertTrue(result['needs_location'])
                self.assertFalse(result['needs_email'])
                self.assertFalse(result['needs_phone'])
    
    def test_analyze_contact_intent_all(self):
        """Test _analyze_contact_intent method for all contact info intent"""
        test_cases = [
            'I need all your contact information',
            'Give me your complete contact details',
            'How can I contact you?',
            'What are all your contact options?'
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                result = self.action._analyze_contact_intent(message)
                self.assertTrue(result['needs_all'])
    
    def test_get_operating_hours_info_specific_day(self):
        """Test _get_operating_hours_info method for specific day"""
        # Test weekday
        result = self.action._get_operating_hours_info('What time are you open on Monday?')
        self.assertIn('Monday Hours', result)
        self.assertIn('9:00 AM - 7:00 PM', result)
        
        # Test Saturday
        result = self.action._get_operating_hours_info('Are you open on Saturday?')
        self.assertIn('Saturday Hours', result)
        self.assertIn('9:00 AM - 6:00 PM', result)
        
        # Test Sunday
        result = self.action._get_operating_hours_info('What about Sunday hours?')
        self.assertIn('Sunday Hours', result)
        self.assertIn('10:00 AM - 5:00 PM', result)
    
    def test_get_operating_hours_info_general(self):
        """Test _get_operating_hours_info method for general hours"""
        result = self.action._get_operating_hours_info('What are your hours?')
        self.assertIn('Operating Hours', result)
        self.assertIn('Mon-Fri:', result)
        self.assertIn('Saturday:', result)
        self.assertIn('Sunday:', result)
    
    @patch('api.actions.contact_actions.support_info')
    @patch('api.actions.contact_actions.logger')
    def test_execute_action_email_intent(self, mock_logger, mock_support_info):
        """Test execute_action method with email intent"""
        # Setup mocks
        mock_support_info.email = 'test@example.com'
        mock_support_info.average_response_time = '24 hours'
        mock_support_info.get_email_url.return_value = 'mailto:test@example.com'
        
        self.tracker.latest_message = {'text': 'I need your email address'}
        
        # Execute action
        result = self.action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify
        self.assertEqual(result, [])
        self.dispatcher.utter_message.assert_called_once()
        
        # Check that the response contains email information
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('Email Support', response_text)
        self.assertIn('test@example.com', response_text)
    
    @patch('api.actions.contact_actions.support_info')
    @patch('api.actions.contact_actions.logger')
    def test_execute_action_phone_intent(self, mock_logger, mock_support_info):
        """Test execute_action method with phone intent"""
        # Setup mocks
        mock_support_info.phone_number = '+65 1234 5678'
        
        self.tracker.latest_message = {'text': 'What is your phone number?'}
        
        # Execute action
        result = self.action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify
        self.assertEqual(result, [])
        self.dispatcher.utter_message.assert_called_once()
        
        # Check that the response contains phone information
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('Phone Support', response_text)
        self.assertIn('+65 1234 5678', response_text)
    
    @patch('api.actions.contact_actions.support_info')
    @patch('api.actions.contact_actions.logger')
    def test_execute_action_whatsapp_intent(self, mock_logger, mock_support_info):
        """Test execute_action method with WhatsApp intent"""
        # Setup mocks
        mock_support_info.whatsapp_number = '+65 9876 5432'
        mock_support_info.get_whatsapp_url.return_value = 'https://wa.me/6598765432'
        
        self.tracker.latest_message = {'text': 'Can I WhatsApp you?'}
        
        # Execute action
        result = self.action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify
        self.assertEqual(result, [])
        self.dispatcher.utter_message.assert_called_once()
        
        # Check that the response contains WhatsApp information
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('WhatsApp Support', response_text)
        self.assertIn('+65 9876 5432', response_text)
    
    @patch('api.actions.contact_actions.support_info')
    @patch('api.actions.contact_actions.logger')
    def test_execute_action_location_intent(self, mock_logger, mock_support_info):
        """Test execute_action method with location intent"""
        # Setup mocks
        mock_support_info.address = '123 Test Street, Singapore 123456'
        mock_support_info.google_maps_url = 'https://maps.google.com/test'
        
        self.tracker.latest_message = {'text': 'Where is your office?'}
        
        # Execute action
        result = self.action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify
        self.assertEqual(result, [])
        self.dispatcher.utter_message.assert_called_once()
        
        # Check that the response contains location information
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('Visit Our Showroom', response_text)
        self.assertIn('123 Test Street, Singapore 123456', response_text)
    
    @patch('api.actions.contact_actions.support_info')
    @patch('api.actions.contact_actions.logger')
    def test_execute_action_hours_intent(self, mock_logger, mock_support_info):
        """Test execute_action method with hours intent"""
        self.tracker.latest_message = {'text': 'What are your operating hours?'}
        
        # Execute action
        result = self.action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify
        self.assertEqual(result, [])
        self.dispatcher.utter_message.assert_called_once()
        
        # Check that the response contains hours information
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('Operating Hours', response_text)
        self.assertIn('Mon-Fri:', response_text)
    
    @patch('api.actions.contact_actions.support_info')
    @patch('api.actions.contact_actions.logger')
    def test_execute_action_all_contact_info(self, mock_logger, mock_support_info):
        """Test execute_action method with all contact info intent"""
        # Setup mocks
        mock_support_info.email = 'test@example.com'
        mock_support_info.phone_number = '+65 1234 5678'
        mock_support_info.whatsapp_number = '+65 9876 5432'
        mock_support_info.address = '123 Test Street, Singapore 123456'
        mock_support_info.average_response_time = '24 hours'
        mock_support_info.get_email_url.return_value = 'mailto:test@example.com'
        mock_support_info.get_whatsapp_url.return_value = 'https://wa.me/6598765432'
        mock_support_info.google_maps_url = 'https://maps.google.com/test'
        
        self.tracker.latest_message = {'text': 'I need all your contact information'}
        
        # Execute action
        result = self.action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify
        self.assertEqual(result, [])
        self.dispatcher.utter_message.assert_called_once()
        
        # Check that the response contains all contact information
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('Email Support', response_text)
        self.assertIn('Phone Support', response_text)
        self.assertIn('WhatsApp Support', response_text)
        self.assertIn('Visit Our Showroom', response_text)
    
    @patch('api.actions.contact_actions.support_info')
    @patch('api.actions.contact_actions.logger')
    def test_execute_action_error_handling(self, mock_logger, mock_support_info):
        """Test execute_action method error handling"""
        # Setup mocks to raise an exception
        mock_support_info.email = 'test@example.com'
        mock_support_info.phone_number = '+65 1234 5678'
        mock_support_info.whatsapp_number = '+65 9876 5432'
        mock_support_info.address = '123 Test Street, Singapore 123456'
        mock_support_info.get_whatsapp_url.side_effect = Exception('Test error')
        
        self.tracker.latest_message = {'text': 'contact information'}
        
        # Execute action
        result = self.action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify
        self.assertEqual(result, [])
        self.dispatcher.utter_message.assert_called_once()
        
        # Check that fallback response is used
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('CleverCompanion Singapore', response_text)
        self.assertIn('test@example.com', response_text)
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
    
    @patch('api.actions.contact_actions.support_info')
    def test_execute_action_no_specific_intent(self, mock_support_info):
        """Test execute_action method when no specific intent is detected"""
        # Setup mocks
        mock_support_info.email = 'test@example.com'
        mock_support_info.phone_number = '+65 1234 5678'
        mock_support_info.whatsapp_number = '+65 9876 5432'
        mock_support_info.address = '123 Test Street, Singapore 123456'
        mock_support_info.average_response_time = '24 hours'
        mock_support_info.get_email_url.return_value = 'mailto:test@example.com'
        mock_support_info.get_whatsapp_url.return_value = 'https://wa.me/6598765432'
        mock_support_info.google_maps_url = 'https://maps.google.com/test'
        
        self.tracker.latest_message = {'text': 'hello there'}
        
        # Execute action
        result = self.action.execute_action(self.dispatcher, self.tracker, self.domain)
        
        # Verify
        self.assertEqual(result, [])
        self.dispatcher.utter_message.assert_called_once()
        
        # Check that all contact information is provided
        call_args = self.dispatcher.utter_message.call_args
        response_text = call_args[1]['text']
        self.assertIn('Email Support', response_text)
        self.assertIn('Phone Support', response_text)
        self.assertIn('WhatsApp Support', response_text)
        self.assertIn('Visit Our Showroom', response_text)


if __name__ == '__main__':
    unittest.main()