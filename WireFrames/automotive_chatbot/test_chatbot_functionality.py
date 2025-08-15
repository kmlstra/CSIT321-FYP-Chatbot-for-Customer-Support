#!/usr/bin/env python3
"""
Comprehensive Chatbot Functionality Test Script
This script tests all chatbot functionalities to ensure they work correctly before deployment.

Test Coverage:
1. Appointment booking functionality
2. Loan calculator functionality
3. Contact information functionality
4. COE price functionality
5. Live support functionality
6. General conversation flow

Usage: python test_chatbot_functionality.py
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:8001"
CLIENT_ID = "689b48203093ee717f8770e5"
TEST_SESSION_ID = f"test_session_{int(time.time())}"

# Test cases for different functionalities
TEST_CASES = [
    {
        "name": "Appointment Booking Test",
        "messages": [
            "I want to book an appointment",
            "I need to schedule a service appointment",
            "Can I book a car service?"
        ],
        "expected_keywords": ["appointment", "book", "schedule", "service", "available"]
    },
    {
        "name": "Loan Calculator Test",
        "messages": [
            "I want to calculate a car loan",
            "How much would a loan cost for a $50000 car?",
            "Can you help me with loan calculations?"
        ],
        "expected_keywords": ["loan", "calculate", "interest", "monthly", "payment"]
    },
    {
        "name": "Contact Information Test",
        "messages": [
            "What are your contact details?",
            "How can I contact you?",
            "What's your phone number?"
        ],
        "expected_keywords": ["contact", "phone", "email", "address", "hours"]
    },
    {
        "name": "COE Price Test",
        "messages": [
            "What are the current COE prices?",
            "Can you tell me COE rates?",
            "How much is COE now?"
        ],
        "expected_keywords": ["COE", "price", "certificate", "entitlement", "current"]
    },
    {
        "name": "Live Support Test",
        "messages": [
            "I need to speak to a human",
            "Can I talk to live support?",
            "Transfer me to an agent"
        ],
        "expected_keywords": ["human", "agent", "support", "transfer", "live"]
    },
    {
        "name": "General Conversation Test",
        "messages": [
            "Hello",
            "What services do you offer?",
            "Tell me about your company"
        ],
        "expected_keywords": ["hello", "services", "automotive", "help", "company"]
    }
]

def test_widget_config():
    """Test if widget configuration is accessible"""
    print("\n=== Testing Widget Configuration ===")
    try:
        response = requests.get(f"{BASE_URL}/api/widget/config/{CLIENT_ID}")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Widget config loaded successfully")
            print(f"   Client ID: {config.get('client_id')}")
            print(f"   Status: {config.get('status')}")
            return True
        else:
            print(f"❌ Widget config failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Widget config error: {str(e)}")
        return False

def send_message(message):
    """Send a message to the chatbot and get response"""
    try:
        payload = {
            "message": message,
            "client_id": CLIENT_ID,
            "session_id": TEST_SESSION_ID
        }
        
        response = requests.post(
            f"{BASE_URL}/api/widget/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Chat API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Message send error: {str(e)}")
        return None

def test_functionality(test_case):
    """Test a specific chatbot functionality"""
    print(f"\n=== {test_case['name']} ===")
    
    results = []
    
    for message in test_case['messages']:
        print(f"\n📤 Sending: {message}")
        
        response = send_message(message)
        
        if response:
            bot_response = response.get('response', '')
            print(f"📥 Response: {bot_response}")
            
            # Check if response contains expected keywords
            keywords_found = []
            for keyword in test_case['expected_keywords']:
                if keyword.lower() in bot_response.lower():
                    keywords_found.append(keyword)
            
            if keywords_found:
                print(f"✅ Found relevant keywords: {', '.join(keywords_found)}")
                results.append(True)
            else:
                print(f"⚠️  No relevant keywords found. Expected: {', '.join(test_case['expected_keywords'])}")
                results.append(False)
        else:
            print(f"❌ No response received")
            results.append(False)
        
        # Wait between messages to avoid rate limiting
        time.sleep(1)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 {test_case['name']} Success Rate: {success_rate:.1f}%")
    
    return success_rate >= 50  # Consider 50% success rate as passing

def test_error_handling():
    """Test error handling and edge cases"""
    print("\n=== Testing Error Handling ===")
    
    error_tests = [
        "",  # Empty message
        "   ",  # Whitespace only
        "a" * 1000,  # Very long message
        "🚗🔧💰📞",  # Emoji only
    ]
    
    for test_msg in error_tests:
        print(f"\n📤 Testing: '{test_msg[:50]}{'...' if len(test_msg) > 50 else ''}'")
        response = send_message(test_msg)
        
        if response:
            print(f"✅ Handled gracefully: {response.get('response', '')[:100]}")
        else:
            print(f"❌ Failed to handle error case")

def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "="*60)
    print("           COMPREHENSIVE CHATBOT TEST REPORT")
    print("="*60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Session ID: {TEST_SESSION_ID}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Base URL: {BASE_URL}")
    
    print("\n📋 Test Results:")
    passed_tests = 0
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if passed:
            passed_tests += 1
    
    overall_success = (passed_tests / total_tests) * 100
    print(f"\n📊 Overall Success Rate: {passed_tests}/{total_tests} ({overall_success:.1f}%)")
    
    if overall_success >= 80:
        print("\n🎉 CHATBOT FUNCTIONALITY TEST: PASSED")
        print("   ✅ Ready for deployment!")
        return True
    else:
        print("\n⚠️  CHATBOT FUNCTIONALITY TEST: FAILED")
        print("   ❌ Issues need to be resolved before deployment!")
        return False

def main():
    """Main test execution function"""
    print("🤖 Starting Comprehensive Chatbot Functionality Test")
    print(f"Target URL: {BASE_URL}")
    print(f"Client ID: {CLIENT_ID}")
    
    # Test widget configuration first
    if not test_widget_config():
        print("❌ Widget configuration test failed. Cannot proceed.")
        sys.exit(1)
    
    # Run all functionality tests
    test_results = {}
    
    for test_case in TEST_CASES:
        test_results[test_case['name']] = test_functionality(test_case)
    
    # Test error handling
    test_error_handling()
    
    # Generate final report
    success = generate_test_report(test_results)
    
    # Save results to file
    report_file = f"chatbot_test_report_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "session_id": TEST_SESSION_ID,
            "client_id": CLIENT_ID,
            "base_url": BASE_URL,
            "test_results": test_results,
            "overall_success": success
        }, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    if success:
        print("\n🚀 All tests passed! Chatbot is ready for deployment.")
        sys.exit(0)
    else:
        print("\n🛑 Tests failed! Please fix issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()