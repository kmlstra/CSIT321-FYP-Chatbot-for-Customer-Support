import requests
import json

def test_cancel_conversation():
    """简单测试取消预约对话流程"""
    
    webhook_url = "http://localhost:5005/webhooks/rest/webhook"
    
    # 创建新的对话会话
    sender_id = "simple_cancel_test"
    
    print("=== 简单取消预约测试 ===")
    print(f"发送者ID: {sender_id}")
    print(f"Webhook地址: {webhook_url}\n")
    
    # 测试1: 直接发送取消预约请求
    print("步骤1: 发送 'Cancel my appointment'")
    try:
        response = requests.post(
            webhook_url,
            json={
                "sender": sender_id,
                "message": "Cancel my appointment"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应成功: {len(result)} 条消息")
            for i, msg in enumerate(result):
                print(f"  消息 {i+1}: {msg.get('text', 'No text')}")
        else:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return
    
    print("\n" + "="*50)
    
    # 测试2: 发送不同的取消预约表达
    cancel_phrases = [
        "I want to cancel my booking",
        "Remove my appointment",
        "Delete my appointment"
    ]
    
    for i, phrase in enumerate(cancel_phrases, 2):
        print(f"\n步骤{i}: 发送 '{phrase}'")
        try:
            response = requests.post(
                webhook_url,
                json={
                    "sender": f"{sender_id}_{i}",  # 使用不同的sender_id
                    "message": phrase
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 响应成功: {len(result)} 条消息")
                for j, msg in enumerate(result):
                    print(f"  消息 {j+1}: {msg.get('text', 'No text')}")
            else:
                print(f"❌ 请求失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_cancel_conversation()