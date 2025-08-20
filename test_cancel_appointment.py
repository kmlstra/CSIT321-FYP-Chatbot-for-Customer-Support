#!/usr/bin/env python3
"""
测试取消预约功能的脚本
"""

import requests
import json
import time

def test_cancel_appointment():
    """测试取消预约功能"""
    
    # RASA服务器URL
    rasa_url = "http://localhost:5005/webhooks/rest/webhook"
    
    # 测试消息
    test_messages = [
        {
            "sender": "test_user",
            "message": "Cancel my appointment",
            "metadata": {
                "client_id": "689c9761bc4138c381b17f66"
            }
        },
        {
            "sender": "test_user", 
            "message": "my phone number is 91234567",
            "metadata": {
                "client_id": "689c9761bc4138c381b17f66"
            }
        }
    ]
    
    print("🧪 开始测试取消预约功能...")
    print("=" * 50)
    
    for i, test_msg in enumerate(test_messages, 1):
        print(f"\n📤 发送测试消息 {i}: {test_msg['message']}")
        
        try:
            # 发送请求到RASA
            response = requests.post(
                rasa_url,
                json=test_msg,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📊 HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                bot_responses = response.json()
                print(f"📥 机器人响应数量: {len(bot_responses)}")
                
                for j, bot_response in enumerate(bot_responses, 1):
                    print(f"\n🤖 响应 {j}:")
                    if 'text' in bot_response:
                        print(f"   文本: {bot_response['text']}")
                    if 'json_message' in bot_response:
                        print(f"   JSON消息: {json.dumps(bot_response['json_message'], indent=2)}")
                    if 'buttons' in bot_response:
                        print(f"   按钮: {bot_response['buttons']}")
                        
                if not bot_responses:
                    print("❌ 错误: 没有收到机器人响应")
                    
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"   响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求错误: {e}")
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            
        # 等待一秒再发送下一个消息
        if i < len(test_messages):
            time.sleep(1)
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")

if __name__ == "__main__":
    test_cancel_appointment()