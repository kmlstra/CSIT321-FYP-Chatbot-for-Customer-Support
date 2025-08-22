#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker服务修复脚本
用于重启AWS服务器上的所有Docker容器
"""

import subprocess
import time
import requests
import json
from datetime import datetime

# 服务器配置
SERVER_IP = "13.215.240.173"
SSH_KEY_PATH = "d:\\CSIT321-FYP-Chatbot-for-Customer-Support\\cc.pem"
SSH_USER = "ubuntu"

# 服务端口配置
SERVICE_PORTS = {
    "nginx": 80,
    "frontend": 3000,
    "rasa": 5005,
    "rasa_actions": 5055,
    "backend": 8000
}

def run_ssh_command(command):
    """执行SSH命令"""
    ssh_cmd = [
        "ssh",
        "-i", SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"{SSH_USER}@{SERVER_IP}",
        command
    ]
    
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "SSH命令执行超时"
    except Exception as e:
        return False, "", f"SSH执行错误: {str(e)}"

def check_port_status(port, timeout=5):
    """检查端口状态"""
    try:
        response = requests.get(f"http://{SERVER_IP}:{port}", timeout=timeout)
        return True, response.status_code
    except:
        return False, None

def fix_docker_services():
    """修复Docker服务"""
    print("🔧 开始修复Docker服务...")
    
    # 停止所有容器
    print("⏹️ 停止所有Docker容器...")
    success, stdout, stderr = run_ssh_command("sudo docker stop $(sudo docker ps -aq)")
    if success:
        print("✅ 所有容器已停止")
    else:
        print(f"⚠️ 停止容器时出现问题: {stderr}")
    
    # 清理Docker系统
    print("🧹 清理Docker系统...")
    success, stdout, stderr = run_ssh_command("sudo docker system prune -f")
    if success:
        print("✅ Docker系统清理完成")
    else:
        print(f"⚠️ 清理时出现问题: {stderr}")
    
    # 重启Docker服务
    print("🔄 重启Docker服务...")
    success, stdout, stderr = run_ssh_command("sudo systemctl restart docker")
    if success:
        print("✅ Docker服务重启成功")
    else:
        print(f"❌ Docker服务重启失败: {stderr}")
        return False
    
    # 等待Docker服务启动
    print("⏳ 等待Docker服务启动...")
    time.sleep(10)
    
    # 启动所有容器
    print("🚀 启动所有Docker容器...")
    success, stdout, stderr = run_ssh_command("cd /home/ubuntu && sudo docker-compose -f docker-compose.yml up -d")
    if success:
        print("✅ 所有容器启动成功")
        print(f"输出: {stdout}")
    else:
        print(f"❌ 容器启动失败: {stderr}")
        return False
    
    # 等待服务启动
    print("⏳ 等待服务完全启动...")
    time.sleep(30)
    
    return True

def test_all_ports():
    """测试所有端口"""
    print("\n🧪 测试所有服务端口...")
    results = {}
    
    for service, port in SERVICE_PORTS.items():
        print(f"测试 {service} (端口 {port})...", end=" ")
        is_working, status_code = check_port_status(port)
        
        if is_working:
            print(f"✅ 正常 (状态码: {status_code})")
            results[service] = {"status": "正常", "port": port, "status_code": status_code}
        else:
            print(f"❌ 异常")
            results[service] = {"status": "异常", "port": port, "status_code": None}
    
    return results

def main():
    """主修复流程"""
    print("AWS Docker服务自动修复工具")
    print("=" * 50)
    print(f"目标服务器: {SERVER_IP}")
    print(f"修复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 执行修复
    if fix_docker_services():
        print("\n✅ Docker服务修复完成")
        
        # 测试所有端口
        test_results = test_all_ports()
        
        # 生成修复报告
        working_services = [s for s, r in test_results.items() if r["status"] == "正常"]
        failed_services = [s for s, r in test_results.items() if r["status"] == "异常"]
        
        print("\n" + "=" * 50)
        print("📊 修复结果总结")
        print(f"✅ 正常服务: {len(working_services)}/{len(SERVICE_PORTS)}")
        print(f"❌ 异常服务: {len(failed_services)}/{len(SERVICE_PORTS)}")
        
        if working_services:
            print(f"\n✅ 正常服务列表: {', '.join(working_services)}")
        
        if failed_services:
            print(f"\n❌ 仍需修复的服务: {', '.join(failed_services)}")
        
        # 保存详细报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "server_ip": SERVER_IP,
            "repair_status": "completed",
            "test_results": test_results,
            "summary": {
                "total_services": len(SERVICE_PORTS),
                "working_services": len(working_services),
                "failed_services": len(failed_services),
                "success_rate": len(working_services) / len(SERVICE_PORTS) * 100
            }
        }
        
        report_file = f"docker_repair_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细修复报告已保存: {report_file}")
        
        if len(working_services) == len(SERVICE_PORTS):
            print("\n🎉 所有服务修复成功！")
        else:
            print("\n⚠️ 部分服务仍需手动检查")
    
    else:
        print("\n❌ Docker服务修复失败")
        print("请检查SSH连接和服务器状态")

if __name__ == "__main__":
    main()