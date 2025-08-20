#!/usr/bin/env python3
"""
测试预约表单功能
验证服务类型选择后是否能正确进入AppointmentForm流程
"""

import requests
import json
import time

def test_appointment_form():
    """测试预约表单功能"""
    base_url = "http://localhost:5005"
    
    print("=== 测试预约表单功能 ===")
    
    # 测试1: 发送预约请求
    print("\n1. 发送预约请求...")
    response = requests.post(f"{base_url}/webhooks/rest/webhook", json={
        "sender": "test_user",
        "message": "I want to book an appointment",
        "metadata": {
            "client_id": "test_client",
            "domain": "automotive",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    })
    
    if response.status_code == 200:
        messages = response.json()
        print(f"机器人回复: {[msg.get('text', msg) for msg in messages]}")
    else:
        print(f"请求失败: {response.status_code}")
        return
    
    time.sleep(1)
    
    # 测试2: 选择Test Drive服务类型
    print("\n2. 选择Test Drive服务类型...")
    response = requests.post(f"{base_url}/webhooks/rest/webhook", json={
        "sender": "test_user",
        "message": "Test Drive",
        "metadata": {
            "client_id": "test_client",
            "domain": "automotive",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    })
    
    if response.status_code == 200:
        messages = response.json()
        print(f"机器人回复: {[msg.get('text', msg) for msg in messages]}")
        
        # 检查是否要求提供姓名或其他详细信息
        response_text = ' '.join([msg.get('text', '') for msg in messages if msg.get('text')])
        if any(keyword in response_text.lower() for keyword in ['name', 'phone', 'contact', 'details', '姓名', '电话', '联系']):
            print("✅ 成功: 系统要求提供详细信息，AppointmentForm正常工作")
        else:
            print("❌ 失败: 系统没有要求提供详细信息，AppointmentForm可能未正确激活")
    else:
        print(f"请求失败: {response.status_code}")
        return
    
    time.sleep(1)
    
    # 测试3: 提供姓名
    print("\n3. 提供姓名...")
    response = requests.post(f"{base_url}/webhooks/rest/webhook", json={
        "sender": "test_user",
        "message": "John Doe",
        "metadata": {
            "client_id": "test_client",
            "domain": "automotive",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    })
    
    if response.status_code == 200:
        messages = response.json()
        print(f"机器人回复: {[msg.get('text', msg) for msg in messages]}")
    else:
        print(f"请求失败: {response.status_code}")
    
    time.sleep(1)
    
    # 测试4: 提供电话号码
    print("\n4. 提供电话号码...")
    response = requests.post(f"{base_url}/webhooks/rest/webhook", json={
        "sender": "test_user",
        "message": "91234567",
        "metadata": {
            "client_id": "test_client",
            "domain": "automotive",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    })
    
    if response.status_code == 200:
        messages = response.json()
        print(f"机器人回复: {[msg.get('text', msg) for msg in messages]}")
    else:
        print(f"请求失败: {response.status_code}")

def test_cancel_appointment():
    """测试取消预约功能"""
    base_url = "http://localhost:5005"
    
    print("\n\n=== 测试取消预约功能 ===")
    
    # 测试取消预约
    print("\n1. 发送取消预约请求...")
    response = requests.post(f"{base_url}/webhooks/rest/webhook", json={
        "sender": "test_user_cancel",
        "message": "Cancel my appointment",
        "metadata": {
            "client_id": "test_client",
            "domain": "automotive",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    })
    
    if response.status_code == 200:
        messages = response.json()
        print(f"机器人回复: {[msg.get('text', msg) for msg in messages]}")
        
        # 检查是否有回应
        if messages and len(messages) > 0:
            print("✅ 成功: 取消预约功能有回应")
        else:
            print("❌ 失败: 取消预约功能没有回应")
    else:
        print(f"请求失败: {response.status_code}")

def test_view_appointments():
    """测试查看预约功能"""
    base_url = "http://localhost:5005"
    
    print("\n\n=== 测试查看预约功能 ===")
    
    # 测试查看预约
    print("\n1. 发送查看预约请求...")
    response = requests.post(f"{base_url}/webhooks/rest/webhook", json={
        "sender": "test_user_view",
        "message": "View my appointments",
        "metadata": {
            "client_id": "test_client",
            "domain": "automotive",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    })
    
    if response.status_code == 200:
        messages = response.json()
        print(f"机器人回复: {[msg.get('text', msg) for msg in messages]}")
        
        # 检查是否有回应
        if messages and len(messages) > 0:
            print("✅ 成功: 查看预约功能有回应")
        else:
            print("❌ 失败: 查看预约功能没有回应")
    else:
        print(f"请求失败: {response.status_code}")

if __name__ == "__main__":
    try:
        # 等待RASA服务完全启动
        print("等待RASA服务启动...")
        time.sleep(3)
        
        # 运行所有测试
        test_appointment_form()
        test_cancel_appointment()
        test_view_appointments()
        
        print("\n=== 测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        print("❌ 错误: 无法连接到RASA服务，请确保服务正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")