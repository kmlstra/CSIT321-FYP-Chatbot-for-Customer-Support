import requests
import json

def test_cancel_with_phone():
    """测试取消预约完整流程（包括提供电话号码）"""
    
    webhook_url = "http://localhost:5005/webhooks/rest/webhook"
    sender_id = "cancel_phone_test"
    
    print("=== 测试取消预约完整流程 ===")
    print(f"发送者ID: {sender_id}")
    print(f"Webhook地址: {webhook_url}\n")
    
    # 步骤1: 发送取消预约请求
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
                text = msg.get('text', 'No text')
                print(f"  消息 {i+1}: {text}")
        else:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return
    
    print("\n" + "-"*50)
    
    # 步骤2: 提供电话号码
    print("\n步骤2: 提供电话号码 '94471414'")
    try:
        response = requests.post(
            webhook_url,
            json={
                "sender": sender_id,
                "message": "94471414"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应成功: {len(result)} 条消息")
            for i, msg in enumerate(result):
                text = msg.get('text', 'No text')
                print(f"  消息 {i+1}: {text}")
                
                # 检查是否包含取消确认信息
                if 'cancel' in text.lower() or 'appointment' in text.lower():
                    if 'successfully' in text.lower() or 'confirmed' in text.lower():
                        print("  ✅ 检测到取消成功消息")
                    elif 'not found' in text.lower() or 'no appointment' in text.lower():
                        print("  ℹ️ 检测到未找到预约消息（正常，因为是测试数据）")
        else:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_cancel_with_phone()