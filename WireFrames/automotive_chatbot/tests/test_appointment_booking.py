import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api.actions.appointment_actions import ActionBookAppointment, ActionViewAppointments

class TestAppointmentBooking(unittest.TestCase):
    """Unit tests for Appointment Booking feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.book_action = ActionBookAppointment()
        self.view_action = ActionViewAppointments()
        self.tracker = MagicMock()
        self.domain = MagicMock()
        
    @patch('pymongo.MongoClient')
    def test_book_appointment_success(self, mock_mongo):
        """Test successful appointment booking"""
        # Mock database
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_mongo.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_one.return_value.inserted_id = 'test_id'
        
        # Mock tracker with valid appointment data
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        self.tracker.get_slot.side_effect = lambda slot: {
            'appointment_date': future_date,
            'appointment_time': '10:00',
            'service_type': 'maintenance',
            'customer_name': 'John Doe',
            'customer_phone': '12345678',
            'customer_email': 'john@example.com'
        }.get(slot)
        
        # Execute action
        result = self.book_action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['template'], 'utter_appointment_booked')
        self.assertIn('confirmed', result[0]['text'].lower())
        self.assertIn('John Doe', result[0]['text'])
        
    def test_book_appointment_missing_data(self):
        """Test appointment booking with missing required data"""
        # Mock tracker with missing customer name
        self.tracker.get_slot.side_effect = lambda slot: {
            'appointment_date': '2024-12-25',
            'appointment_time': '10:00',
            'service_type': 'maintenance',
            'customer_name': None,
            'customer_phone': '12345678',
            'customer_email': 'john@example.com'
        }.get(slot)
        
        # Execute action
        result = self.book_action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('name', result[0]['text'].lower())
        
    def test_book_appointment_past_date(self):
        """Test appointment booking with past date"""
        # Mock tracker with past date
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.tracker.get_slot.side_effect = lambda slot: {
            'appointment_date': past_date,
            'appointment_time': '10:00',
            'service_type': 'maintenance',
            'customer_name': 'John Doe',
            'customer_phone': '12345678',
            'customer_email': 'john@example.com'
        }.get(slot)
        
        # Execute action
        result = self.book_action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('future date', result[0]['text'].lower())
        
    def test_book_appointment_invalid_time(self):
        """Test appointment booking with invalid time"""
        # Mock tracker with invalid time
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        self.tracker.get_slot.side_effect = lambda slot: {
            'appointment_date': future_date,
            'appointment_time': '25:00',  # Invalid time
            'service_type': 'maintenance',
            'customer_name': 'John Doe',
            'customer_phone': '12345678',
            'customer_email': 'john@example.com'
        }.get(slot)
        
        # Execute action
        result = self.book_action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('valid time', result[0]['text'].lower())
        
    @patch('pymongo.MongoClient')
    def test_check_availability_available(self, mock_mongo):
        """Test checking availability when slots are available"""
        # Mock database with no conflicting appointments
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_mongo.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find.return_value = []  # No existing appointments
        
        # Mock tracker
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        self.tracker.get_slot.side_effect = lambda slot: {
            'appointment_date': future_date,
            'appointment_time': '10:00'
        }.get(slot)
        
        # Execute action
        result = self.check_action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('available', result[0]['text'].lower())
        
    @patch('pymongo.MongoClient')
    def test_check_availability_unavailable(self, mock_mongo):
        """Test checking availability when slots are unavailable"""
        # Mock database with conflicting appointment
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_mongo.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find.return_value = [{'_id': 'existing_appointment'}]
        
        # Mock tracker
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        self.tracker.get_slot.side_effect = lambda slot: {
            'appointment_date': future_date,
            'appointment_time': '10:00'
        }.get(slot)
        
        # Execute action
        result = self.check_action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('not available', result[0]['text'].lower())
        
    def test_validate_appointment_data(self):
        """Test appointment data validation"""
        # Test valid data
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        valid_data = {
            'date': future_date,
            'time': '10:00',
            'name': 'John Doe',
            'phone': '12345678',
            'email': 'john@example.com',
            'service': 'maintenance'
        }
        
        is_valid, message = self.book_action.validate_appointment_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(message, '')
        
        # Test invalid email
        invalid_data = valid_data.copy()
        invalid_data['email'] = 'invalid_email'
        
        is_valid, message = self.book_action.validate_appointment_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn('email', message.lower())
        
        # Test invalid phone
        invalid_data = valid_data.copy()
        invalid_data['phone'] = '123'  # Too short
        
        is_valid, message = self.book_action.validate_appointment_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn('phone', message.lower())
        
    def test_business_hours_validation(self):
        """Test business hours validation"""
        # Test valid business hours (9 AM - 6 PM)
        self.assertTrue(self.book_action.is_within_business_hours('09:00'))
        self.assertTrue(self.book_action.is_within_business_hours('12:00'))
        self.assertTrue(self.book_action.is_within_business_hours('17:00'))
        
        # Test invalid business hours
        self.assertFalse(self.book_action.is_within_business_hours('08:00'))
        self.assertFalse(self.book_action.is_within_business_hours('19:00'))
        self.assertFalse(self.book_action.is_within_business_hours('22:00'))

if __name__ == '__main__':
    unittest.main()