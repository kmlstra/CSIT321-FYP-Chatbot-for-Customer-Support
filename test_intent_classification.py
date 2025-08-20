import requests
import json

def test_intent_classification():
    """测试意图分类的详细结果"""
    
    # RASA NLU端点
    nlu_url = "http://localhost:5005/model/parse"
    
    # 测试用例
    test_cases = [
        "Cancel my appointment",
        "I want to cancel my booking",
        "Remove my appointment", 
        "Delete my scheduled appointment",
        "I can't make it, cancel please",
        "Book an appointment",
        "I want to book an appointment",
        "Schedule an appointment"
    ]
    
    print("=== 测试意图分类 ===")
    print(f"NLU服务地址: {nlu_url}\n")
    
    for text in test_cases:
        try:
            # 发送请求到RASA NLU
            response = requests.post(
                nlu_url,
                json={"text": text},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                intent = result.get('intent', {})
                intent_name = intent.get('name', 'unknown')
                confidence = intent.get('confidence', 0.0)
                
                print(f"文本: '{text}'")
                print(f"识别意图: {intent_name} (置信度: {confidence:.3f})")
                
                # 显示所有候选意图
                intent_ranking = result.get('intent_ranking', [])
                if len(intent_ranking) > 1:
                    print("候选意图:")
                    for i, candidate in enumerate(intent_ranking[:3]):
                        print(f"  {i+1}. {candidate['name']} ({candidate['confidence']:.3f})")
                
                print("-" * 50)
                
            else:
                print(f"❌ 请求失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            break
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_intent_classification()