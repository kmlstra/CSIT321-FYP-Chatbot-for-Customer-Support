#!/usr/bin/env python3
"""
Detailed Form Debug Script for Appointment Booking
Tests the complete appointment flow and tracks form state at each step
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class DetailedFormDebugTester:
    def __init__(self, rasa_url: str = "http://localhost:5005"):
        self.rasa_url = rasa_url
        self.sender_id = f"test_user_{int(time.time())}"
        self.session = requests.Session()
        
    def send_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Send message to Rasa and return response"""
        try:
            response = self.session.post(
                f"{self.rasa_url}/webhooks/rest/webhook",
                json={"sender": self.sender_id, "message": message},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error sending message '{message}': {e}")
            return None
    
    def get_tracker(self) -> Optional[Dict[str, Any]]:
        """Get current tracker state"""
        try:
            response = self.session.get(
                f"{self.rasa_url}/conversations/{self.sender_id}/tracker",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting tracker: {e}")
            return None
    
    def print_tracker_state(self, step: str, tracker: Dict[str, Any]):
        """Print detailed tracker state information"""
        print(f"\n{'='*60}")
        print(f"📊 TRACKER STATE - {step}")
        print(f"{'='*60}")
        
        # Active form
        active_form = tracker.get('active_loop', {}).get('name')
        print(f"🔄 Active Form: {active_form}")
        
        # Requested slot
        requested_slot = tracker.get('slots', {}).get('requested_slot')
        print(f"🎯 Requested Slot: {requested_slot}")
        
        # All slots
        slots = tracker.get('slots', {})
        appointment_slots = {
            'service_type': slots.get('service_type'),
            'customer_name': slots.get('customer_name'),
            'customer_phone': slots.get('customer_phone'),
            'appointment_date': slots.get('appointment_date'),
            'appointment_time': slots.get('appointment_time')
        }
        
        print(f"\n📝 Appointment Slots:")
        for slot_name, slot_value in appointment_slots.items():
            status = "✅" if slot_value else "❌"
            print(f"  {status} {slot_name}: {slot_value}")
        
        # Latest events
        events = tracker.get('events', [])
        latest_events = events[-5:] if len(events) > 5 else events
        
        print(f"\n📋 Latest Events:")
        for i, event in enumerate(latest_events, 1):
            event_type = event.get('event')
            if event_type == 'action':
                action_name = event.get('name')
                print(f"  {i}. Action: {action_name}")
            elif event_type == 'slot':
                slot_name = event.get('name')
                slot_value = event.get('value')
                print(f"  {i}. Slot Set: {slot_name} = {slot_value}")
            elif event_type == 'user':
                user_text = event.get('text')
                intent = event.get('parse_data', {}).get('intent', {}).get('name')
                print(f"  {i}. User: '{user_text}' (intent: {intent})")
            elif event_type == 'bot':
                bot_text = event.get('text')
                print(f"  {i}. Bot: '{bot_text}'")
        
        # Form validation status
        all_slots_filled = all(appointment_slots.values())
        form_should_be_complete = all_slots_filled and requested_slot is None
        
        print(f"\n🔍 Form Analysis:")
        print(f"  All slots filled: {all_slots_filled}")
        print(f"  Requested slot is None: {requested_slot is None}")
        print(f"  Form should be complete: {form_should_be_complete}")
        
        return {
            'active_form': active_form,
            'requested_slot': requested_slot,
            'slots': appointment_slots,
            'all_slots_filled': all_slots_filled,
            'form_complete': form_should_be_complete
        }
    
    def test_complete_appointment_flow(self):
        """Test the complete appointment booking flow with detailed tracking"""
        print("🚀 Starting Detailed Appointment Form Debug Test")
        print(f"👤 Sender ID: {self.sender_id}")
        
        # Test steps with expected responses
        test_steps = [
            {
                'step': 'Initial Greeting',
                'message': 'hello',
                'description': 'Start conversation'
            },
            {
                'step': 'Start Appointment',
                'message': 'I want to book an appointment',
                'description': 'Trigger appointment form'
            },
            {
                'step': 'Service Type',
                'message': 'car maintenance',
                'description': 'Provide service type'
            },
            {
                'step': 'Customer Name',
                'message': 'John Smith',
                'description': 'Provide customer name'
            },
            {
                'step': 'Customer Phone',
                'message': '91234567',
                'description': 'Provide phone number'
            },
            {
                'step': 'Appointment Date',
                'message': '2024-02-15',
                'description': 'Provide appointment date'
            },
            {
                'step': 'Appointment Time',
                'message': '10:00 AM',
                'description': 'Provide appointment time - should complete form'
            }
        ]
        
        form_states = []
        
        for i, test_step in enumerate(test_steps, 1):
            print(f"\n\n🔄 STEP {i}: {test_step['step']}")
            print(f"📝 Description: {test_step['description']}")
            print(f"💬 Sending: '{test_step['message']}'")
            
            # Send message
            response = self.send_message(test_step['message'])
            
            if response:
                print(f"\n🤖 Bot Response:")
                for msg in response:
                    if 'text' in msg:
                        print(f"  📢 {msg['text']}")
                    if 'buttons' in msg:
                        print(f"  🔘 Buttons: {[btn['title'] for btn in msg['buttons']]}")
            
            # Wait a moment for processing
            time.sleep(1)
            
            # Get and analyze tracker
            tracker = self.get_tracker()
            if tracker:
                state = self.print_tracker_state(test_step['step'], tracker)
                form_states.append({
                    'step': test_step['step'],
                    'state': state
                })
                
                # Check if form completed after this step
                if state['form_complete']:
                    print(f"\n🎉 FORM COMPLETION DETECTED AFTER STEP: {test_step['step']}")
                    
                    # Wait a bit more and check for submit action
                    time.sleep(2)
                    final_tracker = self.get_tracker()
                    if final_tracker:
                        print(f"\n🔍 FINAL TRACKER CHECK:")
                        self.print_tracker_state("Final Check", final_tracker)
                        
                        # Check for submit action in events
                        events = final_tracker.get('events', [])
                        submit_actions = [e for e in events if e.get('event') == 'action' and 'submit' in e.get('name', '').lower()]
                        
                        if submit_actions:
                            print(f"\n✅ SUBMIT ACTIONS FOUND:")
                            for action in submit_actions:
                                print(f"  🎯 {action.get('name')}")
                        else:
                            print(f"\n❌ NO SUBMIT ACTIONS FOUND")
                    break
            else:
                print(f"❌ Failed to get tracker for step: {test_step['step']}")
        
        # Final summary
        print(f"\n\n{'='*80}")
        print(f"📊 FINAL TEST SUMMARY")
        print(f"{'='*80}")
        
        if form_states:
            final_state = form_states[-1]['state']
            print(f"\n🎯 Final Form State:")
            print(f"  Active Form: {final_state['active_form']}")
            print(f"  Requested Slot: {final_state['requested_slot']}")
            print(f"  All Slots Filled: {final_state['all_slots_filled']}")
            print(f"  Form Complete: {final_state['form_complete']}")
            
            print(f"\n📝 Slot Values:")
            for slot_name, slot_value in final_state['slots'].items():
                status = "✅" if slot_value else "❌"
                print(f"  {status} {slot_name}: {slot_value}")
        
        # Check for any confirmation messages
        final_tracker = self.get_tracker()
        if final_tracker:
            events = final_tracker.get('events', [])
            bot_messages = [e.get('text') for e in events if e.get('event') == 'bot' and e.get('text')]
            confirmation_messages = [msg for msg in bot_messages if any(word in msg.lower() for word in ['confirm', 'booked', 'scheduled', 'appointment'])]
            
            if confirmation_messages:
                print(f"\n✅ CONFIRMATION MESSAGES FOUND:")
                for msg in confirmation_messages:
                    print(f"  📢 {msg}")
            else:
                print(f"\n❌ NO CONFIRMATION MESSAGES FOUND")
                print(f"\n📋 All Bot Messages:")
                for msg in bot_messages[-5:]:
                    print(f"  📢 {msg}")

def main():
    """Main test function"""
    tester = DetailedFormDebugTester()
    
    print("🔧 Testing Rasa connection...")
    test_response = tester.send_message("test")
    if test_response is None:
        print("❌ Cannot connect to Rasa server. Please ensure it's running on http://localhost:5005")
        return
    
    print("✅ Rasa connection successful!")
    tester.test_complete_appointment_flow()

if __name__ == "__main__":
    main()