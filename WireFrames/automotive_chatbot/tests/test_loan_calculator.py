import unittest
import sys
import os
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api.actions.loan_calculator_actions import ActionLoanCalculator

class TestLoanCalculator(unittest.TestCase):
    """Unit tests for Loan Calculator feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.action = ActionLoanCalculator()
        self.tracker = MagicMock()
        self.domain = MagicMock()
        
    def test_calculate_loan_valid_inputs(self):
        """Test loan calculation with valid inputs"""
        # Mock tracker with valid slots
        self.tracker.get_slot.side_effect = lambda slot: {
            'loan_amount': 50000,
            'loan_term': 5,
            'interest_rate': 3.5
        }.get(slot)
        
        # Execute action
        result = self.action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['template'], 'utter_loan_calculation')
        self.assertIn('monthly payment', result[0]['text'].lower())
        self.assertIn('$', result[0]['text'])
        
    def test_calculate_loan_missing_amount(self):
        """Test loan calculation with missing loan amount"""
        # Mock tracker with missing loan amount
        self.tracker.get_slot.side_effect = lambda slot: {
            'loan_amount': None,
            'loan_term': 5,
            'interest_rate': 3.5
        }.get(slot)
        
        # Execute action
        result = self.action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('loan amount', result[0]['text'].lower())
        
    def test_calculate_loan_missing_term(self):
        """Test loan calculation with missing loan term"""
        # Mock tracker with missing loan term
        self.tracker.get_slot.side_effect = lambda slot: {
            'loan_amount': 50000,
            'loan_term': None,
            'interest_rate': 3.5
        }.get(slot)
        
        # Execute action
        result = self.action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('loan term', result[0]['text'].lower())
        
    def test_calculate_loan_missing_interest_rate(self):
        """Test loan calculation with missing interest rate"""
        # Mock tracker with missing interest rate
        self.tracker.get_slot.side_effect = lambda slot: {
            'loan_amount': 50000,
            'loan_term': 5,
            'interest_rate': None
        }.get(slot)
        
        # Execute action
        result = self.action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('interest rate', result[0]['text'].lower())
        
    def test_calculate_loan_zero_interest(self):
        """Test loan calculation with zero interest rate"""
        # Mock tracker with zero interest rate
        self.tracker.get_slot.side_effect = lambda slot: {
            'loan_amount': 50000,
            'loan_term': 5,
            'interest_rate': 0
        }.get(slot)
        
        # Execute action
        result = self.action.run(self.tracker, self.domain)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertIn('monthly payment', result[0]['text'].lower())
        # With 0% interest, monthly payment should be loan_amount / (term * 12)
        expected_payment = 50000 / (5 * 12)
        self.assertIn(f'{expected_payment:.2f}', result[0]['text'])
        
    def test_calculate_monthly_payment(self):
        """Test monthly payment calculation formula"""
        # Test calculation method directly
        loan_amount = 50000
        annual_rate = 3.5
        term_years = 5
        
        monthly_payment = self.action.calculate_monthly_payment(
            loan_amount, annual_rate, term_years
        )
        
        # Verify calculation is reasonable
        self.assertGreater(monthly_payment, 0)
        self.assertLess(monthly_payment, loan_amount)  # Should be less than total loan
        
        # Test with zero interest
        monthly_payment_zero = self.action.calculate_monthly_payment(
            loan_amount, 0, term_years
        )
        expected_zero_interest = loan_amount / (term_years * 12)
        self.assertAlmostEqual(monthly_payment_zero, expected_zero_interest, places=2)
        
    def test_invalid_loan_inputs(self):
        """Test loan calculation with invalid inputs"""
        # Test negative loan amount
        self.tracker.get_slot.side_effect = lambda slot: {
            'loan_amount': -50000,
            'loan_term': 5,
            'interest_rate': 3.5
        }.get(slot)
        
        result = self.action.run(self.tracker, self.domain)
        self.assertIn('valid', result[0]['text'].lower())
        
        # Test negative loan term
        self.tracker.get_slot.side_effect = lambda slot: {
            'loan_amount': 50000,
            'loan_term': -5,
            'interest_rate': 3.5
        }.get(slot)
        
        result = self.action.run(self.tracker, self.domain)
        self.assertIn('valid', result[0]['text'].lower())
        
        # Test negative interest rate
        self.tracker.get_slot.side_effect = lambda slot: {
            'loan_amount': 50000,
            'loan_term': 5,
            'interest_rate': -3.5
        }.get(slot)
        
        result = self.action.run(self.tracker, self.domain)
        self.assertIn('valid', result[0]['text'].lower())

if __name__ == '__main__':
    unittest.main()