#!/usr/bin/env python3
"""
New Appointment Form Submission Test Script
Tests complete appointment form flow and submission functionality in English
"""

import requests
import json
import time
from datetime import datetime

# Configuration
RASA_URL = "http://localhost:5005"
ACTIONS_URL = "http://localhost:5055"
BACKEND_URL = "http://localhost:8000"

def check_services():
    """Check if all services are running"""
    print("🔍 Checking service status...")
    
    services = {
        "Rasa Core": f"{RASA_URL}/status",
        "Rasa Actions": f"{ACTIONS_URL}/health",
        "Backend API": f"{BACKEND_URL}/health"
    }
    
    all_running = True
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service}: Running")
            else:
                print(f"❌ {service}: Status code {response.status_code}")
                all_running = False
        except Exception as e:
            print(f"❌ {service}: Connection failed - {e}")
            all_running = False
    
    return all_running

def send_message(message, sender_id="test_user_new"):
    """Send message to Rasa"""
    url = f"{RASA_URL}/webhooks/rest/webhook"
    payload = {
        "sender": sender_id,
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Message sending error: {e}")
        return None

def get_tracker_info(sender_id="test_user_new"):
    """Get tracker information"""
    url = f"{RASA_URL}/conversations/{sender_id}/tracker"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get tracker: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Tracker retrieval error: {e}")
        return None

def print_tracker_status(tracker):
    """Print tracker status information"""
    if not tracker:
        print("❌ Unable to get tracker information")
        return
    
    print("\n📊 Tracker Status:")
    print(f"  Active Loop: {tracker.get('active_loop', {}).get('name', 'None')}")
    print(f"  Requested Slot: {tracker.get('slots', {}).get('requested_slot', 'None')}")
    
    # Show all slots
    slots = tracker.get('slots', {})
    appointment_slots = ['service_type', 'customer_name', 'customer_phone', 'appointment_date', 'appointment_time']
    
    print("\n🎯 Appointment Slot Status:")
    for slot in appointment_slots:
        value = slots.get(slot)
        status = "✅" if value else "❌"
        print(f"  {status} {slot}: {value}")
    
    # Show latest event
    events = tracker.get('events', [])
    if events:
        latest_event = events[-1]
        print(f"\n🔄 Latest Event: {latest_event.get('event')} - {latest_event.get('name', latest_event.get('text', 'N/A'))}")

def check_database_appointment(phone_number):
    """Check appointment records in database"""
    try:
        # Check appointments through backend API
        url = f"{BACKEND_URL}/api/appointments"
        params = {"phone": phone_number}
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            appointments = response.json()
            print(f"\n📋 Found {len(appointments)} appointment records in database")
            for apt in appointments:
                print(f"  Appointment ID: {apt.get('appointment_id', 'N/A')}")
                print(f"  Service Type: {apt.get('service_type', 'N/A')}")
                print(f"  Customer Name: {apt.get('customer_name', 'N/A')}")
                print(f"  Appointment Date: {apt.get('appointment_date', 'N/A')}")
                print(f"  Appointment Time: {apt.get('appointment_time', 'N/A')}")
                print(f"  Status: {apt.get('status', 'N/A')}")
            return len(appointments) > 0
        else:
            print(f"❌ Database check failed: {response.status_code}")
            if response.status_code == 401:
                print("  Authentication error - this is expected for direct API access")
            return False
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False

def test_complete_appointment_flow():
    """Test complete appointment flow in English"""
    print("\n🚀 Starting complete appointment flow test...")
    
    sender_id = f"test_user_new_{int(time.time())}"
    test_phone = "91234567"
    
    # Test steps in English
    test_steps = [
        ("I want to book an appointment", "Start booking"),
        ("Test Drive", "Select service type"),
        ("John Smith", "Provide name"),
        (test_phone, "Provide phone"),
        ("2024-12-25", "Provide date"),
        ("2pm", "Provide time")
    ]
    
    for i, (message, description) in enumerate(test_steps, 1):
        print(f"\n📝 Step {i}: {description}")
        print(f"Sending message: '{message}'")
        
        # Send message
        response = send_message(message, sender_id)
        if response:
            print(f"Received {len(response)} replies:")
            for j, reply in enumerate(response, 1):
                text = reply.get('text', '')
                if text:
                    print(f"  Reply {j}: {text[:100]}{'...' if len(text) > 100 else ''}")
                    
                    # Check for confirmation message
                    if "confirmed" in text.lower() or "appointment confirmed" in text.lower():
                        print("\n🎉 CONFIRMATION MESSAGE DETECTED!")
        else:
            print("❌ No reply received")
        
        # Wait for processing
        time.sleep(2)
        
        # Get tracker status
        tracker = get_tracker_info(sender_id)
        print_tracker_status(tracker)
        
        # Check if form is completed
        if tracker:
            active_loop = tracker.get('active_loop', {}).get('name')
            requested_slot = tracker.get('slots', {}).get('requested_slot')
            
            if not active_loop and not requested_slot:
                print("\n🎉 Form appears to be completed!")
                break
    
    # Final database check
    print("\n🔍 Checking database for appointment records...")
    found_appointment = check_database_appointment(test_phone)
    
    if found_appointment:
        print("\n✅ Test successful! Appointment saved to database")
    else:
        print("\n❌ Test failed! Appointment not saved to database")
    
    return found_appointment

def main():
    """Main function"""
    print("🧪 Appointment Form Submission Test Script - New Version")
    print("=" * 60)
    
    # Check service status first
    if not check_services():
        print("\n❌ Some services are not running, please start all services first")
        return False
    
    print("\n✅ All services are running normally")
    
    # Execute test
    success = test_complete_appointment_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completed: Appointment form submission working properly")
    else:
        print("❌ Test failed: Appointment form submission has issues")
    
    return success

if __name__ == "__main__":
    main()