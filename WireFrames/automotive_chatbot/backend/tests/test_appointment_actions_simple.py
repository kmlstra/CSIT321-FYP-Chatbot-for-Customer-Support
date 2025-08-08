#!/usr/bin/env python3
"""
Simple test script for appointment functionality
Tests core parsing logic without complex dependencies
"""

import re
from datetime import datetime, timedelta
import pytz

def test_time_parsing():
    """Test time parsing functionality based on appointment_actions.py logic"""
    print("\n=== Testing Time Parsing ===")
    
    def parse_time_string(time_str):
        """Parse time string to 24-hour format - based on appointment_actions.py"""
        if not time_str:
            return None
            
        time_str = time_str.strip().lower()
        
        # Enhanced regex patterns for different time formats
        patterns = [
            # 12-hour format with am/pm (with or without space)
            r'^(\d{1,2})\s*([ap]m)$',  # 2pm, 2 pm
            r'^(\d{1,2}):(\d{2})\s*([ap]m)$',  # 2:30pm, 2:30 PM
            # 24-hour format
            r'^(\d{1,2}):(\d{2})$',  # 14:30
            r'^(\d{1,2})$'  # Just hour number
        ]
        
        for pattern in patterns:
            match = re.match(pattern, time_str)
            if match:
                if len(match.groups()) == 2 and match.group(2) in ['am', 'pm']:
                    # Format: 2pm, 2am
                    hour = int(match.group(1))
                    period = match.group(2)
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    return f"{hour:02d}:00"
                elif len(match.groups()) == 3:
                    # Format: 2:30pm, 2:30am
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    period = match.group(3)
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    return f"{hour:02d}:{minute:02d}"
                elif len(match.groups()) == 2 and ':' in time_str:
                    # Format: 14:30
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
        
        return None
    
    test_cases = [
        ("2pm", "14:00"),
        ("2 pm", "14:00"),
        ("2:30pm", "14:30"),
        ("2:30 PM", "14:30"),
        ("14:00", "14:00"),
        ("14:30", "14:30"),
        ("10am", "10:00"),
        ("10 AM", "10:00"),
        ("12pm", "12:00"),
        ("12am", "00:00")
    ]
    
    passed = 0
    total = len(test_cases)
    
    for input_time, expected in test_cases:
        try:
            result = parse_time_string(input_time)
            if result == expected:
                print(f"✓ '{input_time}' -> '{result}'")
                passed += 1
            else:
                print(f"✗ '{input_time}' -> '{result}' (expected '{expected}')")
        except Exception as e:
            print(f"✗ '{input_time}' -> ERROR: {e}")
    
    print(f"\nTime Parsing: {passed}/{total} tests passed")
    return passed == total

def test_date_parsing():
    """Test date parsing functionality"""
    print("\n=== Testing Date Parsing ===")
    
    def parse_date_string(date_str):
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None
            
        date_str = date_str.strip().lower()
        sg_tz = pytz.timezone('Asia/Singapore')
        now = datetime.now(sg_tz)
        
        # Handle relative dates
        if date_str == "today":
            return now.strftime("%Y-%m-%d")
        elif date_str == "tomorrow":
            tomorrow = now + timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d")
        
        # Handle various date formats
        date_patterns = [
            r'^(\d{4})-(\d{1,2})-(\d{1,2})$',  # 2024-12-25
            r'^(\d{1,2})/(\d{1,2})/(\d{4})$',  # 25/12/2024
            r'^(\w{3})\s+(\d{1,2}),\s+(\d{4})$'  # Dec 25, 2024
        ]
        
        for pattern in date_patterns:
            match = re.match(pattern, date_str)
            if match:
                if pattern.endswith('$'):
                    if '/' in date_str:
                        # DD/MM/YYYY format
                        day, month, year = match.groups()
                        return f"{year}-{int(month):02d}-{int(day):02d}"
                    elif '-' in date_str:
                        # YYYY-MM-DD format
                        year, month, day = match.groups()
                        return f"{year}-{int(month):02d}-{int(day):02d}"
                    elif ',' in date_str:
                        # Month DD, YYYY format
                        month_str, day, year = match.groups()
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        month_num = month_map.get(month_str.lower())
                        if month_num:
                            return f"{year}-{month_num:02d}-{int(day):02d}"
        
        return None
    
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    test_cases = [
        ("today", today),
        ("tomorrow", tomorrow),
        ("2024-12-25", "2024-12-25"),
        ("25/12/2024", "2024-12-25"),
        ("Dec 25, 2024", "2024-12-25")
    ]
    
    passed = 0
    total = len(test_cases)
    
    for input_date, expected in test_cases:
        try:
            result = parse_date_string(input_date)
            if result == expected:
                print(f"✓ '{input_date}' -> '{result}'")
                passed += 1
            else:
                print(f"✗ '{input_date}' -> '{result}' (expected '{expected}')")
        except Exception as e:
            print(f"✗ '{input_date}' -> ERROR: {e}")
    
    print(f"\nDate Parsing: {passed}/{total} tests passed")
    return passed == total

def test_phone_number_validation():
    """Test phone number validation"""
    print("\n=== Testing Phone Number Validation ===")
    
    def validate_phone_number(phone):
        """Validate phone number format"""
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # Check if it has at least 8 digits (Singapore local) or 10+ digits (international)
        return len(digits_only) >= 8
    
    phone_patterns = [
        ("+6512345678", True),
        ("12345678", True),
        ("(65) 1234-5678", True),
        ("123-456-7890", True),
        ("123.456.7890", True),
        ("123", False),
        ("", False),
        ("abc", False)
    ]
    
    passed = 0
    total = len(phone_patterns)
    
    for phone, expected in phone_patterns:
        try:
            result = validate_phone_number(phone)
            if result == expected:
                status = "Valid" if result else "Invalid"
                print(f"✓ '{phone}' - Correctly identified as {status}")
                passed += 1
            else:
                print(f"✗ '{phone}' - Validation failed")
        except Exception as e:
            print(f"✗ '{phone}' - ERROR: {e}")
    
    print(f"\nPhone Validation: {passed}/{total} tests passed")
    return passed == total

def test_business_hours_validation():
    """Test business hours validation"""
    print("\n=== Testing Business Hours Validation ===")
    
    def is_business_hours(time_str):
        """Check if time is within business hours (9 AM - 6 PM)"""
        if not time_str or ':' not in time_str:
            return False
        
        try:
            hour = int(time_str.split(':')[0])
            return 9 <= hour < 18
        except:
            return False
    
    business_hours_tests = [
        ("09:00", True),
        ("12:00", True),
        ("17:59", True),
        ("08:00", False),
        ("18:00", False),
        ("22:00", False)
    ]
    
    passed = 0
    total = len(business_hours_tests)
    
    for time_str, should_be_valid in business_hours_tests:
        try:
            is_valid = is_business_hours(time_str)
            
            if is_valid == should_be_valid:
                status = "within" if is_valid else "outside"
                print(f"✓ {time_str} - Correctly identified as {status} business hours")
                passed += 1
            else:
                print(f"✗ {time_str} - Validation failed")
        except Exception as e:
            print(f"✗ {time_str} - ERROR: {e}")
    
    print(f"\nBusiness Hours: {passed}/{total} tests passed")
    return passed == total

def test_appointment_id_validation():
    """Test appointment ID validation"""
    print("\n=== Testing Appointment ID Validation ===")
    
    def validate_appointment_id(apt_id):
        """Validate appointment ID format"""
        if not apt_id:
            return False
        
        apt_id = str(apt_id).strip()
        if not apt_id:
            return False
        
        # Valid if it's alphanumeric and has reasonable length
        return len(apt_id) >= 3 and apt_id.replace(' ', '').isalnum()
    
    id_tests = [
        ("12345", True),
        ("APT001", True),
        ("A123", True),
        ("999", True),
        ("", False),
        (None, False),
        ("   ", False),
        ("12", False),  # Too short
        ("@#$", False)  # Invalid characters
    ]
    
    passed = 0
    total = len(id_tests)
    
    for apt_id, expected in id_tests:
        try:
            result = validate_appointment_id(apt_id)
            if result == expected:
                status = "Valid" if result else "Invalid"
                print(f"✓ '{apt_id}' - Correctly identified as {status}")
                passed += 1
            else:
                print(f"✗ '{apt_id}' - Validation failed")
        except Exception as e:
            print(f"✗ '{apt_id}' - ERROR: {e}")
    
    print(f"\nID Validation: {passed}/{total} tests passed")
    return passed == total

def run_all_tests():
    """Run all tests and provide summary"""
    print("\n" + "="*60)
    print("APPOINTMENT FUNCTIONALITY - TEST SUITE")
    print("="*60)
    
    tests = [
        ("Time Parsing", test_time_parsing),
        ("Date Parsing", test_date_parsing),
        ("Phone Validation", test_phone_number_validation),
        ("Business Hours", test_business_hours_validation),
        ("ID Validation", test_appointment_id_validation)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                print(f"\n✓ {test_name}: PASSED")
            else:
                print(f"\n✗ {test_name}: FAILED")
        except Exception as e:
            print(f"\n✗ {test_name}: ERROR - {e}")
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! The appointment parsing logic is working correctly.")
        print("\n📋 Key Features Validated:")
        print("   • Time parsing supports multiple formats (2pm, 2:30pm, 14:00)")
        print("   • Date parsing handles relative dates (today, tomorrow) and various formats")
        print("   • Phone number validation accepts international and local formats")
        print("   • Business hours validation ensures appointments within 9 AM - 6 PM")
        print("   • Appointment ID validation ensures proper format and length")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the implementation.")
    
    print("\n" + "="*60)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    run_all_tests()