#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB连接和预约功能测试脚本
测试内容：
1. MongoDB连接池测试
2. 查看预约功能测试
3. 取消预约功能测试
4. 数据库查询验证
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# 添加backend路径到sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'WireFrames', 'automotive_chatbot', 'backend'))

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), 'WireFrames', 'automotive_chatbot', 'backend', '.env'))

class MongoDBConnectionTester:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGODB_URL') or os.getenv('CHATBOT_MONGODB_URL')
        self.db_name = os.getenv('MONGODB_DB', 'automotive_chatbot_saas')
        self.client = None
        self.db = None
        
        # 调试信息：打印环境变量
        print(f"调试信息:")
        print(f"  MONGODB_URL: {os.getenv('MONGODB_URL')}")
        print(f"  CHATBOT_MONGODB_URL: {os.getenv('CHATBOT_MONGODB_URL')}")
        print(f"  MONGODB_DB: {os.getenv('MONGODB_DB')}")
        print(f"  使用的URI: {self.mongo_uri}")
        print(f"  使用的数据库: {self.db_name}")
        
        if not self.mongo_uri:
            print("❌ 错误：未找到MongoDB连接URI环境变量")
            raise ValueError("MongoDB URI not found in environment variables")
        
    def test_connection_pool(self):
        """测试MongoDB连接池"""
        print("\n=== 测试MongoDB连接池 ===")
        try:
            # 创建MongoDB客户端
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                waitQueueTimeoutMS=5000
            )
            
            # 测试连接
            self.client.admin.command('ping')
            print("✅ MongoDB连接成功")
            
            # 获取数据库
            self.db = self.client[self.db_name]
            print(f"✅ 数据库 '{self.db_name}' 连接成功")
            
            # 测试连接池状态
            pool_options = self.client.options.pool_options
            print(f"✅ 连接池配置:")
            print(f"   - 最大连接数: {pool_options.max_pool_size}")
            print(f"   - 最小连接数: {pool_options.min_pool_size}")
            print(f"   - 最大空闲时间: {pool_options.max_idle_time_ms}ms")
            
            return True
            
        except ConnectionFailure as e:
            print(f"❌ MongoDB连接失败: {e}")
            return False
        except ServerSelectionTimeoutError as e:
            print(f"❌ MongoDB服务器选择超时: {e}")
            return False
        except Exception as e:
            print(f"❌ 连接测试出错: {e}")
            return False
    
    def test_appointments_collection(self):
        """测试预约集合"""
        print("\n=== 测试预约集合 ===")
        try:
            if not self.db:
                print("❌ 数据库连接未建立")
                return False
                
            # 获取预约集合
            appointments_collection = self.db['appointments']
            
            # 检查集合是否存在
            collections = self.db.list_collection_names()
            if 'appointments' in collections:
                print("✅ 预约集合存在")
            else:
                print("⚠️ 预约集合不存在，将在第一次插入时创建")
            
            # 统计预约数量
            total_appointments = appointments_collection.count_documents({})
            print(f"✅ 总预约数量: {total_appointments}")
            
            # 统计不同状态的预约
            statuses = ['confirmed', 'cancelled', 'completed']
            for status in statuses:
                count = appointments_collection.count_documents({'status': status})
                print(f"   - {status}状态预约: {count}")
            
            return True
            
        except Exception as e:
            print(f"❌ 预约集合测试出错: {e}")
            return False
    
    def test_view_appointments_query(self, phone_number="+6512345678"):
        """测试查看预约查询"""
        print(f"\n=== 测试查看预约查询 (电话: {phone_number}) ===")
        try:
            if not self.db:
                print("❌ 数据库连接未建立")
                return False
                
            appointments_collection = self.db['appointments']
            
            # 查询该电话号码的所有预约
            query = {'customer_phone': phone_number}
            appointments = list(appointments_collection.find(query).sort('appointment_date', 1))
            
            print(f"✅ 找到 {len(appointments)} 个预约")
            
            if appointments:
                current_time = datetime.now()
                upcoming = []
                past = []
                
                for apt in appointments:
                    apt_date = apt.get('appointment_date')
                    if isinstance(apt_date, str):
                        try:
                            apt_date = datetime.fromisoformat(apt_date.replace('Z', '+00:00'))
                        except:
                            continue
                    
                    if apt_date and apt_date > current_time:
                        upcoming.append(apt)
                    else:
                        past.append(apt)
                
                print(f"   - 即将到来的预约: {len(upcoming)}")
                print(f"   - 过去的预约: {len(past)}")
                
                # 显示最近的几个预约详情
                for i, apt in enumerate(appointments[:3]):
                    print(f"   预约 {i+1}:")
                    print(f"     - ID: {apt.get('_id')}")
                    print(f"     - 日期: {apt.get('appointment_date')}")
                    print(f"     - 时间: {apt.get('appointment_time')}")
                    print(f"     - 状态: {apt.get('status')}")
                    print(f"     - 服务: {apt.get('service_type')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 查看预约查询测试出错: {e}")
            return False
    
    def test_cancel_appointment_query(self, phone_number="+6512345678"):
        """测试取消预约查询"""
        print(f"\n=== 测试取消预约查询 (电话: {phone_number}) ===")
        try:
            if not self.db:
                print("❌ 数据库连接未建立")
                return False
                
            appointments_collection = self.db['appointments']
            
            # 查找最新的未取消预约
            query = {
                'customer_phone': phone_number,
                'status': {'$ne': 'cancelled'}
            }
            
            latest_appointment = appointments_collection.find_one(
                query,
                sort=[('appointment_date', -1)]
            )
            
            if latest_appointment:
                print("✅ 找到可取消的最新预约:")
                print(f"   - ID: {latest_appointment.get('_id')}")
                print(f"   - 日期: {latest_appointment.get('appointment_date')}")
                print(f"   - 时间: {latest_appointment.get('appointment_time')}")
                print(f"   - 状态: {latest_appointment.get('status')}")
                print(f"   - 服务: {latest_appointment.get('service_type')}")
                
                # 模拟取消操作（不实际执行）
                print("\n模拟取消操作:")
                update_query = {'_id': latest_appointment['_id']}
                update_data = {
                    '$set': {
                        'status': 'cancelled',
                        'cancelled_at': datetime.now().isoformat()
                    }
                }
                print(f"   - 更新查询: {update_query}")
                print(f"   - 更新数据: {update_data}")
                print("   ⚠️ 注意: 这只是模拟，未实际执行取消操作")
                
            else:
                print("⚠️ 没有找到可取消的预约")
                
                # 检查是否有任何预约
                any_appointment = appointments_collection.find_one({'customer_phone': phone_number})
                if any_appointment:
                    print("   但找到了其他预约（可能已取消）")
                else:
                    print("   该电话号码没有任何预约记录")
            
            return True
            
        except Exception as e:
            print(f"❌ 取消预约查询测试出错: {e}")
            return False
    
    def test_database_operations(self):
        """测试数据库基本操作"""
        print("\n=== 测试数据库基本操作 ===")
        try:
            if not self.db:
                print("❌ 数据库连接未建立")
                return False
            
            # 测试集合列表
            collections = self.db.list_collection_names()
            print(f"✅ 数据库中的集合: {collections}")
            
            # 测试数据库统计
            stats = self.db.command('dbstats')
            print(f"✅ 数据库统计:")
            print(f"   - 数据库大小: {stats.get('dataSize', 0)} bytes")
            print(f"   - 集合数量: {stats.get('collections', 0)}")
            print(f"   - 索引数量: {stats.get('indexes', 0)}")
            
            # 测试预约集合索引
            if 'appointments' in collections:
                appointments_collection = self.db['appointments']
                indexes = list(appointments_collection.list_indexes())
                print(f"✅ 预约集合索引:")
                for idx in indexes:
                    print(f"   - {idx.get('name')}: {idx.get('key')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库操作测试出错: {e}")
            return False
    
    def create_test_appointment(self, phone_number="+6512345678"):
        """创建测试预约数据"""
        print(f"\n=== 创建测试预约数据 (电话: {phone_number}) ===")
        try:
            if not self.db:
                print("❌ 数据库连接未建立")
                return False
            
            appointments_collection = self.db['appointments']
            
            # 检查是否已有测试数据
            existing = appointments_collection.find_one({'customer_phone': phone_number})
            if existing:
                print(f"✅ 已存在测试预约数据，跳过创建")
                return True
            
            # 创建测试预约
            test_appointment = {
                'customer_name': 'Test Customer',
                'customer_phone': phone_number,
                'appointment_date': (datetime.now() + timedelta(days=7)).isoformat(),
                'appointment_time': '14:00',
                'service_type': 'General Maintenance',
                'status': 'confirmed',
                'created_at': datetime.now().isoformat(),
                'notes': 'Test appointment for MongoDB connection testing'
            }
            
            result = appointments_collection.insert_one(test_appointment)
            print(f"✅ 创建测试预约成功，ID: {result.inserted_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建测试预约出错: {e}")
            return False
    
    def cleanup_test_data(self, phone_number="+6512345678"):
        """清理测试数据"""
        print(f"\n=== 清理测试数据 (电话: {phone_number}) ===")
        try:
            if not self.db:
                print("❌ 数据库连接未建立")
                return False
            
            appointments_collection = self.db['appointments']
            
            # 删除测试数据
            result = appointments_collection.delete_many({
                'customer_phone': phone_number,
                'notes': 'Test appointment for MongoDB connection testing'
            })
            
            print(f"✅ 清理了 {result.deleted_count} 条测试数据")
            
            return True
            
        except Exception as e:
            print(f"❌ 清理测试数据出错: {e}")
            return False
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            print("\n✅ 数据库连接已关闭")

def main():
    """主测试函数"""
    print("MongoDB连接和预约功能测试开始...")
    print(f"测试时间: {datetime.now()}")
    
    tester = MongoDBConnectionTester()
    
    try:
        # 1. 测试MongoDB连接池
        if not tester.test_connection_pool():
            print("\n❌ MongoDB连接失败，终止测试")
            return False
        
        # 2. 测试预约集合
        if not tester.test_appointments_collection():
            print("\n❌ 预约集合测试失败")
            return False
        
        # 3. 测试数据库基本操作
        if not tester.test_database_operations():
            print("\n❌ 数据库操作测试失败")
            return False
        
        # 4. 创建测试数据（如果需要）
        tester.create_test_appointment()
        
        # 5. 测试查看预约功能
        if not tester.test_view_appointments_query():
            print("\n❌ 查看预约查询测试失败")
            return False
        
        # 6. 测试取消预约功能
        if not tester.test_cancel_appointment_query():
            print("\n❌ 取消预约查询测试失败")
            return False
        
        # 7. 清理测试数据
        tester.cleanup_test_data()
        
        print("\n🎉 所有测试完成！")
        print("\n=== 测试总结 ===")
        print("✅ MongoDB连接池测试通过")
        print("✅ 预约集合测试通过")
        print("✅ 数据库操作测试通过")
        print("✅ 查看预约查询测试通过")
        print("✅ 取消预约查询测试通过")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return False
    except Exception as e:
        print(f"\n❌ 测试过程中出现未预期错误: {e}")
        return False
    finally:
        tester.close_connection()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)