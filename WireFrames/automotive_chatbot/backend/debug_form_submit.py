import requests
import json
import time

def test_form_submit_debug():
    """详细调试表单提交问题"""
    base_url = "http://localhost:5005"
    
    print("🔍 调试表单提交问题")
    print("=" * 50)
    
    # 创建新会话
    session_id = f"debug_session_{int(time.time())}"
    
    def send_message(message, step_name):
        """发送消息并获取详细响应信息"""
        print(f"\n📤 {step_name}")
        print(f"📤 发送: {message}")
        
        try:
            response = requests.post(
                f"{base_url}/webhooks/rest/webhook",
                json={
                    "sender": session_id,
                    "message": message
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"📥 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data:
                    for msg in data:
                        if 'text' in msg:
                            print(f"📥 文本响应: {msg['text']}")
                        if 'buttons' in msg:
                            print(f"🔘 按钮: {[btn['title'] for btn in msg['buttons']]}")
                else:
                    print("❌ 空响应")
                    
                return data
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"❌ 错误内容: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return None
    
    # 检查tracker状态
    def check_tracker_status():
        """检查当前tracker状态"""
        try:
            response = requests.get(
                f"{base_url}/conversations/{session_id}/tracker",
                timeout=5
            )
            
            if response.status_code == 200:
                tracker = response.json()
                print(f"\n🔍 Tracker状态:")
                print(f"   - 活跃循环: {tracker.get('active_loop', {}).get('name', 'None')}")
                print(f"   - 请求的槽位: {tracker.get('slots', {}).get('requested_slot', 'None')}")
                print(f"   - 最新动作: {tracker.get('latest_action', {}).get('action_name', 'None')}")
                
                # 显示所有槽位状态
                slots = tracker.get('slots', {})
                print(f"   - 槽位状态:")
                for slot_name in ['service_type', 'customer_name', 'customer_phone', 'appointment_date', 'appointment_time']:
                    value = slots.get(slot_name)
                    print(f"     * {slot_name}: {value}")
                    
                return tracker
            else:
                print(f"❌ 无法获取tracker: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取tracker异常: {str(e)}")
            return None
    
    # 执行完整的预约流程
    steps = [
        ("I want to book an appointment", "启动预约流程"),
        ("oil change", "输入服务类型"),
        ("John Smith", "输入客户姓名"),
        ("91234567", "输入电话号码"),
        ("tomorrow", "输入预约日期"),
        ("2pm", "输入预约时间")
    ]
    
    for message, step_name in steps:
        send_message(message, step_name)
        check_tracker_status()
        time.sleep(2)  # 等待处理完成
    
    print("\n🔍 最终tracker状态检查:")
    final_tracker = check_tracker_status()
    
    if final_tracker:
        active_loop = final_tracker.get('active_loop', {}).get('name')
        if active_loop is None:
            print("✅ 表单已完成（active_loop为null）")
        else:
            print(f"❌ 表单仍在活跃状态: {active_loop}")
            
        # 检查是否有预约确认消息
        events = final_tracker.get('events', [])
        bot_messages = [event for event in events if event.get('event') == 'bot']
        if bot_messages:
            last_message = bot_messages[-1].get('text', '')
            if '预约已确认' in last_message or 'appointment confirmed' in last_message.lower():
                print("✅ 找到预约确认消息")
            else:
                print("❌ 未找到预约确认消息")
                print(f"最后的机器人消息: {last_message}")

if __name__ == "__main__":
    test_form_submit_debug()