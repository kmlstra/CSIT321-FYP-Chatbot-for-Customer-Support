import requests
import json

def test_view_appointments_specific():
    """测试特定的查看预约表达"""
    url = "http://localhost:5005/webhooks/rest/webhook"
    
    # 测试不同的view_appointments表达
    test_phrases = [
        "Show me my appointments",
        "What appointments do I have?", 
        "Check my bookings",
        "List my scheduled appointments",
        "view my appointments",
        "show my booking details",
        "i want to check my appointment"
    ]
    
    print("\n=== 测试不同的查看预约表达 ===")
    
    for i, phrase in enumerate(test_phrases):
        print(f"\n--- 测试 {i+1}: '{phrase}' ---")
        
        payload = {
            "sender": f"test_user_{i}",
            "message": phrase
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data:
                    for msg in response_data:
                        text = msg.get('text', 'No text')
                        print(f"机器人回复: {text[:100]}..." if len(text) > 100 else f"机器人回复: {text}")
                else:
                    print("没有收到任何响应")
            else:
                print(f"请求失败: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"连接错误: {e}")
    
    # 测试意图识别
    print("\n\n=== 测试意图识别 ===")
    parse_url = "http://localhost:5005/model/parse"
    
    test_message = "Show me my appointments"
    parse_payload = {"text": test_message}
    
    try:
        response = requests.post(parse_url, json=parse_payload, timeout=10)
        if response.status_code == 200:
            parse_data = response.json()
            print(f"消息: '{test_message}'")
            print(f"识别的意图: {parse_data.get('intent', {}).get('name', 'Unknown')}")
            print(f"置信度: {parse_data.get('intent', {}).get('confidence', 0)}")
            print(f"实体: {parse_data.get('entities', [])}")
        else:
            print(f"意图识别失败: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"意图识别连接错误: {e}")

if __name__ == "__main__":
    test_view_appointments_specific()