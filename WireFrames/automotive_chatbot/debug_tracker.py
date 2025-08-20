#!/usr/bin/env python3
"""
调试tracker状态，查看appointment_time槽位的详细信息
"""

import requests
import json

def get_tracker_state():
    """获取tracker状态"""
    try:
        tracker_url = "http://localhost:5005/conversations/test_slot_mapping_fix/tracker"
        response = requests.get(tracker_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Tracker request failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Tracker request failed: {e}")
        return None

def main():
    tracker = get_tracker_state()
    if tracker:
        slots = tracker.get('slots', {})
        active_loop = tracker.get('active_loop', {})
        latest_events = tracker.get('events', [])[-15:]
        
        print("=== 完整槽位状态 ===")
        for slot_name, slot_value in slots.items():
            if slot_value is not None:
                print(f"{slot_name}: {slot_value}")
        
        print(f"\n=== Active Loop ===")
        print(f"Active Loop: {active_loop}")
        
        print(f"\n=== 最近15个事件 ===")
        for i, event in enumerate(latest_events):
            print(f"{i+1}. {event.get('event')}: {event.get('name', event.get('value', event.get('text', event.get('name'))))}")
            if event.get('event') == 'slot':
                print(f"   槽位: {event.get('name')} = {event.get('value')}")

if __name__ == "__main__":
    main()