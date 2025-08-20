#!/usr/bin/env python3
"""
English Appointment Booking Test Script
Tests the complete appointment form flow in English
"""

import requests
import json
import time

def test_appointment_booking():
    """Test the complete appointment booking flow in English"""
    base_url = "http://localhost:5005"
    
    # Test conversation flow
    conversation_steps = [
        {
            "message": "I want to book an appointment",
            "expected_keywords": ["service", "type"]
        },
        {
            "message": "oil change",
            "expected_keywords": ["name", "full"]
        },
        {
            "message": "John Smith",
            "expected_keywords": ["phone", "number"]
        },
        {
            "message": "1234567890",
            "expected_keywords": ["date", "when"]
        },
        {
            "message": "tomorrow",
            "expected_keywords": ["time", "what time"]
        },
        {
            "message": "2pm",
            "expected_keywords": ["confirm", "appointment", "booked"]
        }
    ]
    
    print("=== Testing English Appointment Booking Flow ===")
    
    # Start new conversation
    session_id = "test_english_session"
    
    for i, step in enumerate(conversation_steps, 1):
        print(f"\nStep {i}: Sending '{step['message']}'")
        
        # Send message to Rasa
        response = requests.post(
            f"{base_url}/webhooks/rest/webhook",
            json={
                "sender": session_id,
                "message": step["message"]
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        bot_responses = response.json()
        print(f"Bot responses: {len(bot_responses)} messages")
        
        if not bot_responses:
            print("❌ No response from bot")
            return False
        
        # Check bot response
        for resp in bot_responses:
            if "text" in resp:
                print(f"Bot: {resp['text']}")
                
                # Check if expected keywords are in response
                response_text = resp["text"].lower()
                found_keyword = any(keyword.lower() in response_text for keyword in step["expected_keywords"])
                
                if not found_keyword:
                    print(f"⚠️  Warning: Expected keywords {step['expected_keywords']} not found in response")
        
        # Wait a bit between messages
        time.sleep(1)
    
    # Check conversation tracker
    print("\n=== Checking Conversation Tracker ===")
    tracker_response = requests.get(f"{base_url}/conversations/{session_id}/tracker")
    
    if tracker_response.status_code == 200:
        tracker_data = tracker_response.json()
        
        # Check slots
        slots = tracker_data.get("slots", {})
        print("\nSlot values:")
        for slot_name in ["service_type", "customer_name", "customer_phone", "appointment_date", "appointment_time"]:
            value = slots.get(slot_name)
            print(f"  {slot_name}: {value}")
        
        # Check if all required slots are filled
        required_slots = ["service_type", "customer_name", "customer_phone", "appointment_date", "appointment_time"]
        filled_slots = [slot for slot in required_slots if slots.get(slot) is not None]
        
        print(f"\nFilled slots: {len(filled_slots)}/{len(required_slots)}")
        
        # Check active form
        active_loop = tracker_data.get("active_loop")
        print(f"Active loop: {active_loop}")
        
        # Check latest action
        latest_action = tracker_data.get("latest_action_name")
        print(f"Latest action: {latest_action}")
        
        # Look for confirmation message in events
        events = tracker_data.get("events", [])
        confirmation_found = False
        
        for event in reversed(events[-10:]):  # Check last 10 events
            if event.get("event") == "bot" and "text" in event:
                text = event["text"].lower()
                if any(word in text for word in ["confirm", "booked", "scheduled", "appointment"]):
                    confirmation_found = True
                    print(f"✅ Confirmation message found: {event['text']}")
                    break
        
        if not confirmation_found:
            print("❌ No confirmation message found")
            return False
        
        # Success criteria
        if len(filled_slots) == len(required_slots) and confirmation_found:
            print("\n✅ Test PASSED: All slots filled and confirmation received")
            return True
        else:
            print(f"\n❌ Test FAILED: Only {len(filled_slots)}/{len(required_slots)} slots filled")
            return False
    
    else:
        print(f"❌ Failed to get tracker: HTTP {tracker_response.status_code}")
        return False

if __name__ == "__main__":
    try:
        success = test_appointment_booking()
        if success:
            print("\n🎉 English appointment booking test completed successfully!")
        else:
            print("\n💥 English appointment booking test failed!")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()