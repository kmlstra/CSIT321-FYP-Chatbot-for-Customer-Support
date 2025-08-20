#!/usr/bin/env python3
"""
调试取消预约功能的详细测试脚本
"""

import requests
import json
import time

def debug_cancel_appointment():
    """详细调试取消预约功能"""
    
    base_url = "http://localhost:5005"
    sender_id = "debug_cancel_test"
    
    print("=== 调试取消预约功能 ===")
    print(f"测试用户ID: {sender_id}")
    print(f"RASA服务地址: {base_url}")
    print()
    
    # 测试步骤1: 发送取消预约意图
    print("步骤1: 发送取消预约请求")
    message1 = {
        "sender": sender_id,
        "message": "Cancel my appointment"
    }
    
    try:
        response1 = requests.post(f"{base_url}/webhooks/rest/webhook", json=message1, timeout=10)
        print(f"请求状态码: {response1.status_code}")
        print(f"响应内容: {json.dumps(response1.json(), indent=2, ensure_ascii=False)}")
        
        if response1.status_code == 200:
            bot_responses = response1.json()
            if bot_responses:
                print(f"机器人回复数量: {len(bot_responses)}")
                for i, resp in enumerate(bot_responses):
                    print(f"回复 {i+1}: {resp.get('text', 'No text')}")
            else:
                print("❌ 机器人没有回复")
        else:
            print(f"❌ 请求失败: {response1.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # 等待一下
    time.sleep(2)
    
    # 测试步骤2: 提供电话号码
    print("步骤2: 提供电话号码")
    message2 = {
        "sender": sender_id,
        "message": "my phone number is 91234567"
    }
    
    try:
        response2 = requests.post(f"{base_url}/webhooks/rest/webhook", json=message2, timeout=10)
        print(f"请求状态码: {response2.status_code}")
        print(f"响应内容: {json.dumps(response2.json(), indent=2, ensure_ascii=False)}")
        
        if response2.status_code == 200:
            bot_responses = response2.json()
            if bot_responses:
                print(f"机器人回复数量: {len(bot_responses)}")
                for i, resp in enumerate(bot_responses):
                    print(f"回复 {i+1}: {resp.get('text', 'No text')}")
                    if 'buttons' in resp:
                        print(f"按钮: {resp['buttons']}")
            else:
                print("❌ 机器人没有回复")
        else:
            print(f"❌ 请求失败: {response2.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # 测试步骤3: 检查对话状态
    print("步骤3: 检查对话状态")
    try:
        tracker_url = f"{base_url}/conversations/{sender_id}/tracker"
        tracker_response = requests.get(tracker_url, timeout=10)
        print(f"Tracker状态码: {tracker_response.status_code}")
        
        if tracker_response.status_code == 200:
            tracker_data = tracker_response.json()
            print(f"当前意图: {tracker_data.get('latest_message', {}).get('intent', {}).get('name', 'Unknown')}")
            print(f"置信度: {tracker_data.get('latest_message', {}).get('intent', {}).get('confidence', 'Unknown')}")
            print(f"当前槽位:")
            for slot_name, slot_value in tracker_data.get('slots', {}).items():
                if slot_value is not None:
                    print(f"  {slot_name}: {slot_value}")
            
            print(f"\n最近的事件:")
            events = tracker_data.get('events', [])
            for event in events[-5:]:  # 显示最近5个事件
                print(f"  {event.get('event', 'Unknown')}: {event}")
        else:
            print(f"❌ 获取tracker失败: {tracker_response.status_code}")
            
    except Exception as e:
        print(f"❌ 获取tracker异常: {e}")
    
    print("\n=== 调试完成 ===")

if __name__ == "__main__":
    debug_cancel_appointment()