#!/usr/bin/env python3
"""检查MongoDB中的unified_sessions集合"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.config.database import DatabaseContext
import json
from datetime import datetime

def check_sessions():
    """检查unified_sessions集合中的数据"""
    print("=== 检查unified_sessions集合 ===")
    
    with DatabaseContext('unified_sessions') as sessions:
        if not sessions:
            print("❌ 无法连接到数据库")
            return
        
        # 获取总数
        total_count = sessions.count_documents({})
        print(f"总会话数: {total_count}")
        
        # 检查特定会话ID
        target_session_id = "f6e65062-f780-49ee-bc97-0f247ca3c4b6"
        print(f"\n=== 检查特定会话ID: {target_session_id} ===")
        
        target_session = sessions.find_one({'session_id': target_session_id}, {'_id': 0})
        if target_session:
            print("✅ 找到目标会话:")
            # 转换datetime为字符串以便JSON序列化
            session_copy = target_session.copy()
            for key, value in session_copy.items():
                if isinstance(value, datetime):
                    session_copy[key] = value.isoformat()
            print(json.dumps(session_copy, indent=2, ensure_ascii=False))
        else:
            print("❌ 未找到目标会话")
        
        if total_count > 0:
            # 获取最近的3个会话
            recent_sessions = list(sessions.find({}, {'_id': 0}).sort('created_at', -1).limit(3))
            print(f"\n最近的{len(recent_sessions)}个会话:")
            
            for i, session in enumerate(recent_sessions, 1):
                print(f"\n--- 会话 {i} ---")
                print(f"session_id: {session.get('session_id')}")
                print(f"created_at: {session.get('created_at')}")
        else:
            print("❌ 没有找到任何会话数据")

if __name__ == "__main__":
    check_sessions()