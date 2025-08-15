import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api.actions.live_support_actions import ActionLiveSupport

class TestLiveSupport(unittest.TestCase):
    """Unit tests for Live Support feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.live_support_action = ActionLiveSupport()
        self.tracker = MagicMock()
        self.domain = MagicMock()
        
    def test_connect_live_support_during_hours(self):
        """Test connecting to live support during business hours"""
        # Mock business hours (9 AM - 6 PM)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 0)  # 2 PM
            mock_datetime.strptime = datetime.strptime
            
            # Mock tracker with user info
            self.tracker.get_slot.side_effect = lambda slot: {
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'issue_type': 'technical'
            }.get(slot)
            
            # Execute action
            result = self.connect_action.run(self.tracker, self.domain)
            
            # Assertions
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['template'], 'utter_live_support_connected')
            self.assertIn('agent', result[0]['text'].lower())
            
    def test_connect_live_support_after_hours(self):
        """Test connecting to live support after business hours"""
        # Mock after hours (8 PM)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 20, 0)  # 8 PM
            mock_datetime.strptime = datetime.strptime
            
            # Mock tracker with user info
            self.tracker.get_slot.side_effect = lambda slot: {
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'issue_type': 'technical'
            }.get(slot)
            
            # Execute action
            result = self.connect_action.run(self.tracker, self.domain)
            
            # Assertions
            self.assertEqual(len(result), 1)
            self.assertIn('hours', result[0]['text'].lower())
            self.assertIn('9', result[0]['text'])  # Business hours start
            
    def test_connect_live_support_missing_info(self):
        """Test connecting to live support with missing user information"""
        # Mock tracker with missing customer name
        self.tracker.get_slot.side_effect = lambda slot: {
            'customer_name': None,
            'customer_email': 'john@example.com',
            'issue_type': 'technical'
        }.get(slot)
        
        # Execute action
        result = self.connect_action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('name', result[0]['text'].lower())
        
    def test_check_support_availability_available(self):
        """Test checking support availability when agents are available"""
        # Mock business hours with available agents
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 0)  # 2 PM
            mock_datetime.strptime = datetime.strptime
            
            with patch.object(self.check_action, 'get_available_agents') as mock_agents:
                mock_agents.return_value = 3  # 3 available agents
                
                # Execute action
                result = self.check_action.run(self.tracker, self.domain)
                
                # Assertions
                self.assertEqual(len(result), 1)
                self.assertIn('available', result[0]['text'].lower())
                self.assertIn('3', result[0]['text'])
                
    def test_check_support_availability_busy(self):
        """Test checking support availability when all agents are busy"""
        # Mock business hours with no available agents
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 0)  # 2 PM
            mock_datetime.strptime = datetime.strptime
            
            with patch.object(self.check_action, 'get_available_agents') as mock_agents:
                mock_agents.return_value = 0  # No available agents
                
                with patch.object(self.check_action, 'get_estimated_wait_time') as mock_wait:
                    mock_wait.return_value = 15  # 15 minutes wait
                    
                    # Execute action
                    result = self.check_action.run(self.tracker, self.domain)
                    
                    # Assertions
                    self.assertEqual(len(result), 1)
                    self.assertIn('busy', result[0]['text'].lower())
                    self.assertIn('15', result[0]['text'])
                    
    def test_check_support_availability_after_hours(self):
        """Test checking support availability after business hours"""
        # Mock after hours
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 20, 0)  # 8 PM
            mock_datetime.strptime = datetime.strptime
            
            # Execute action
            result = self.check_action.run(self.tracker, self.domain)
            
            # Assertions
            self.assertEqual(len(result), 1)
            self.assertIn('closed', result[0]['text'].lower())
            
    def test_escalate_to_supervisor(self):
        """Test escalating to supervisor"""
        # Mock tracker with escalation request
        self.tracker.get_slot.side_effect = lambda slot: {
            'escalate': True,
            'customer_name': 'John Doe',
            'issue_description': 'Complex technical issue'
        }.get(slot)
        
        # Execute action
        result = self.connect_action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('supervisor', result[0]['text'].lower())
        
    def test_priority_support_request(self):
        """Test priority support request handling"""
        # Mock tracker with priority request
        self.tracker.get_slot.side_effect = lambda slot: {
            'priority': 'high',
            'customer_name': 'VIP Customer',
            'customer_email': 'vip@example.com',
            'issue_type': 'urgent'
        }.get(slot)
        
        # Execute action
        result = self.connect_action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('priority', result[0]['text'].lower())
        
    def test_support_queue_management(self):
        """Test support queue management"""
        # Test queue position
        with patch.object(self.connect_action, 'get_queue_position') as mock_queue:
            mock_queue.return_value = 5
            
            # Mock tracker
            self.tracker.get_slot.side_effect = lambda slot: {
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com'
            }.get(slot)
            
            # Execute action
            result = self.connect_action.run(self.tracker, self.domain)
            
            # Should mention queue position
            self.assertIn('5', result[0]['text'])
            
    def test_support_session_creation(self):
        """Test support session creation"""
        with patch('pymongo.MongoClient') as mock_mongo:
            # Mock database
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_mongo.return_value.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            mock_collection.insert_one.return_value.inserted_id = 'session_123'
            
            # Mock tracker
            self.tracker.get_slot.side_effect = lambda slot: {
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'issue_type': 'technical'
            }.get(slot)
            
            # Execute action
            result = self.connect_action.run(self.tracker, self.domain)
            
            # Verify session creation was attempted
            mock_collection.insert_one.assert_called_once()
            
    def test_business_hours_validation(self):
        """Test business hours validation"""
        # Test various times
        test_times = [
            (datetime(2024, 1, 15, 8, 0), False),   # 8 AM - before hours
            (datetime(2024, 1, 15, 9, 0), True),    # 9 AM - start of hours
            (datetime(2024, 1, 15, 12, 0), True),   # 12 PM - during hours
            (datetime(2024, 1, 15, 18, 0), True),   # 6 PM - end of hours
            (datetime(2024, 1, 15, 19, 0), False),  # 7 PM - after hours
            (datetime(2024, 1, 13, 14, 0), False),  # Saturday - weekend
            (datetime(2024, 1, 14, 14, 0), False),  # Sunday - weekend
        ]
        
        for test_time, expected in test_times:
            with self.subTest(time=test_time):
                result = self.connect_action.is_business_hours(test_time)
                self.assertEqual(result, expected)
                
    def test_support_ticket_creation(self):
        """Test support ticket creation for offline requests"""
        # Mock after hours request
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 20, 0)  # 8 PM
            
            with patch('pymongo.MongoClient') as mock_mongo:
                # Mock database
                mock_db = MagicMock()
                mock_collection = MagicMock()
                mock_mongo.return_value.__getitem__.return_value = mock_db
                mock_db.__getitem__.return_value = mock_collection
                mock_collection.insert_one.return_value.inserted_id = 'ticket_123'
                
                # Mock tracker
                self.tracker.get_slot.side_effect = lambda slot: {
                    'customer_name': 'John Doe',
                    'customer_email': 'john@example.com',
                    'issue_description': 'Need help with my account'
                }.get(slot)
                
                # Execute action
                result = self.connect_action.run(self.tracker, self.domain)
                
                # Should create a ticket for offline request
                self.assertIn('ticket', result[0]['text'].lower())
                mock_collection.insert_one.assert_called_once()

if __name__ == '__main__':
    unittest.main()