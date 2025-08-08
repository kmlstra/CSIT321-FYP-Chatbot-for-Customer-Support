"""Unit Tests for Information Utility
Tests for support information management and contact data functionality
"""

import unittest
from unittest.mock import patch, Mock
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.utils.information import (
    SupportInformation,
    support_info,
    get_whatsapp_number,
    get_phone_number,
    get_email,
    get_support_hours,
    get_whatsapp_url,
    get_all_contact_info,
    is_business_hours
)

class TestSupportInformation(unittest.TestCase):
    """Test SupportInformation class functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.support_info = SupportInformation()
    
    def test_initialization(self):
        """Test SupportInformation initialization"""
        self.assertIsNotNone(self.support_info.whatsapp_number)
        self.assertIsNotNone(self.support_info.phone_number)
        self.assertIsNotNone(self.support_info.email)
        self.assertIsNotNone(self.support_info.support_hours)
    
    def test_contact_properties(self):
        """Test contact information properties"""
        # Test WhatsApp number
        self.assertTrue(self.support_info.whatsapp_number.startswith('+65'))
        
        # Test phone number
        self.assertTrue(self.support_info.phone_number.startswith('+65'))
        
        # Test email
        self.assertIn('@', self.support_info.email)
        self.assertTrue(self.support_info.email.endswith('.sg'))
        
        # Test support hours structure
        hours = self.support_info.support_hours
        self.assertIn('monday_friday', hours)
        self.assertIn('saturday', hours)
        self.assertIn('sunday', hours)
    
    def test_whatsapp_url_generation(self):
        """Test WhatsApp URL generation"""
        # Test default message
        url = self.support_info.get_whatsapp_url()
        self.assertTrue(url.startswith('https://wa.me/'))
        self.assertIn('text=', url)
        
        # Test custom message
        custom_message = "Hello, I need help!"
        url_custom = self.support_info.get_whatsapp_url(custom_message)
        self.assertIn('Hello', url_custom)
        self.assertIn('%20', url_custom)  # URL encoded space
    
    def test_phone_url_generation(self):
        """Test phone URL generation"""
        url = self.support_info.get_phone_url()
        self.assertTrue(url.startswith('tel:'))
        self.assertIn('+65', url)
    
    def test_email_url_generation(self):
        """Test email URL generation"""
        # Test default subject
        url = self.support_info.get_email_url()
        self.assertTrue(url.startswith('mailto:'))
        self.assertIn('subject=', url)
        
        # Test custom subject
        custom_subject = "Urgent Support Request"
        url_custom = self.support_info.get_email_url(custom_subject)
        self.assertIn('Urgent', url_custom)
        self.assertIn('%20', url_custom)  # URL encoded space
    
    def test_support_hours_text(self):
        """Test support hours text formatting"""
        hours_text = self.support_info.get_support_hours_text()
        self.assertIn('Monday-Friday', hours_text)
        self.assertIn('Saturday', hours_text)
        self.assertIn('Sunday', hours_text)
        self.assertIn('AM', hours_text)
        self.assertIn('PM', hours_text)
    
    @patch('api.utils.information.datetime')
    def test_business_hours_weekday(self, mock_datetime):
        """Test business hours detection for weekdays"""
        # Mock Monday 10 AM
        mock_now = Mock()
        mock_now.weekday.return_value = 0  # Monday
        mock_now.hour = 10
        mock_datetime.now.return_value = mock_now
        
        self.assertTrue(self.support_info.is_business_hours())
        
        # Mock Monday 8 AM (before business hours)
        mock_now.hour = 8
        self.assertFalse(self.support_info.is_business_hours())
        
        # Mock Monday 8 PM (after business hours)
        mock_now.hour = 20
        self.assertFalse(self.support_info.is_business_hours())
    
    @patch('api.utils.information.datetime')
    def test_business_hours_weekend(self, mock_datetime):
        """Test business hours detection for weekends"""
        # Mock Saturday 11 AM
        mock_now = Mock()
        mock_now.weekday.return_value = 5  # Saturday
        mock_now.hour = 11
        mock_datetime.now.return_value = mock_now
        
        self.assertTrue(self.support_info.is_business_hours())
        
        # Mock Sunday 11 AM
        mock_now.weekday.return_value = 6  # Sunday
        self.assertTrue(self.support_info.is_business_hours())
        
        # Mock Sunday 6 PM (after business hours)
        mock_now.hour = 18
        self.assertFalse(self.support_info.is_business_hours())
    
    def test_get_all_contact_info(self):
        """Test comprehensive contact information retrieval"""
        contact_info = self.support_info.get_all_contact_info()
        
        # Check required fields
        required_fields = [
            'whatsapp_number', 'phone_number', 'email', 'support_hours',
            'average_response_time', 'urgent_hours_message', 'whatsapp_url',
            'phone_url', 'email_url', 'support_hours_text', 'is_business_hours'
        ]
        
        for field in required_fields:
            self.assertIn(field, contact_info)
        
        # Check data types
        self.assertIsInstance(contact_info['whatsapp_number'], str)
        self.assertIsInstance(contact_info['phone_number'], str)
        self.assertIsInstance(contact_info['email'], str)
        self.assertIsInstance(contact_info['support_hours'], dict)
        self.assertIsInstance(contact_info['is_business_hours'], bool)
    
    def test_get_company_info(self):
        """Test company information retrieval"""
        company_info = self.support_info.get_company_info()
        
        required_fields = [
            'company_name', 'website', 'address', 'services',
            'business_registration', 'operating_since'
        ]
        
        for field in required_fields:
            self.assertIn(field, company_info)
        
        # Check specific values
        self.assertEqual(company_info['company_name'], 'CleverCompanion')
        self.assertTrue(company_info['website'].startswith('https://'))
        self.assertIsInstance(company_info['services'], list)
        self.assertTrue(len(company_info['services']) > 0)
    
    def test_update_contact_info(self):
        """Test contact information updates"""
        original_phone = self.support_info.phone_number
        
        # Test valid update
        new_phone = "+65 9999 8888"
        self.support_info.update_contact_info(phone_number=new_phone)
        self.assertEqual(self.support_info.phone_number, new_phone)
        
        # Test invalid field update (should raise ValueError)
        with self.assertRaises(ValueError):
            self.support_info.update_contact_info(invalid_field="test")
        
        # Restore original value
        self.support_info.update_contact_info(phone_number=original_phone)

class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for direct access"""
    
    def test_get_whatsapp_number(self):
        """Test get_whatsapp_number function"""
        number = get_whatsapp_number()
        self.assertIsInstance(number, str)
        self.assertTrue(number.startswith('+65'))
    
    def test_get_phone_number(self):
        """Test get_phone_number function"""
        number = get_phone_number()
        self.assertIsInstance(number, str)
        self.assertTrue(number.startswith('+65'))
    
    def test_get_email(self):
        """Test get_email function"""
        email = get_email()
        self.assertIsInstance(email, str)
        self.assertIn('@', email)
    
    def test_get_support_hours(self):
        """Test get_support_hours function"""
        hours = get_support_hours()
        self.assertIsInstance(hours, dict)
        self.assertIn('monday_friday', hours)
    
    def test_get_whatsapp_url(self):
        """Test get_whatsapp_url function"""
        url = get_whatsapp_url()
        self.assertTrue(url.startswith('https://wa.me/'))
        
        # Test with custom message
        custom_url = get_whatsapp_url("Test message")
        self.assertIn('Test', custom_url)
    
    def test_get_all_contact_info(self):
        """Test get_all_contact_info function"""
        info = get_all_contact_info()
        self.assertIsInstance(info, dict)
        self.assertIn('whatsapp_number', info)
        self.assertIn('phone_number', info)
        self.assertIn('email', info)
    
    def test_is_business_hours(self):
        """Test is_business_hours function"""
        result = is_business_hours()
        self.assertIsInstance(result, bool)

class TestDataValidation(unittest.TestCase):
    """Test data validation and edge cases"""
    
    def test_phone_number_format(self):
        """Test phone number format validation"""
        phone = get_phone_number()
        # Should be Singapore format
        self.assertTrue(phone.startswith('+65'))
        # Should contain only digits, spaces, and + symbol
        cleaned = phone.replace('+', '').replace(' ', '')
        self.assertTrue(cleaned.isdigit())
    
    def test_email_format(self):
        """Test email format validation"""
        email = get_email()
        # Basic email validation
        self.assertIn('@', email)
        self.assertIn('.', email)
        # Should not contain spaces
        self.assertNotIn(' ', email)
    
    def test_url_encoding(self):
        """Test URL encoding in generated URLs"""
        # Test WhatsApp URL with special characters
        message_with_special_chars = "Hello! How are you?"
        url = get_whatsapp_url(message_with_special_chars)
        
        # Should be URL encoded
        self.assertNotIn('!', url)  # Should be encoded as %21
        self.assertNotIn(' ', url)  # Should be encoded as %20
        self.assertIn('%', url)     # Should contain encoded characters
    
    def test_support_hours_consistency(self):
        """Test support hours data consistency"""
        hours = get_support_hours()
        
        # All days should have time ranges
        for day, time_range in hours.items():
            self.assertIn('AM', time_range.upper())
            self.assertIn('PM', time_range.upper())
            self.assertIn('-', time_range)

if __name__ == '__main__':
    unittest.main()