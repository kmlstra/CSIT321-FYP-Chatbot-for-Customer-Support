#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的AWS EC2修复脚本
解决EC2内存升级后的所有问题：CSS丢失、端口无法访问等
"""

import paramiko
import time
import sys
import json
from datetime import datetime

class EC2CompleteFixer:
    def __init__(self):
        self.host = "13.215.240.173"
        self.username = "ubuntu"
        self.key_path = "d:/CSIT321-FYP-Chatbot-for-Customer-Support/cc.pem"
        self.ssh = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "host": self.host,
            "fixes_applied": [],
            "port_status": {},
            "errors": [],
            "success": False
        }
    
    def connect_ssh(self):
        """建立SSH连接"""
        try:
            print(f"正在连接到 {self.host}...")
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            key = paramiko.RSAKey.from_private_key_file(self.key_path)
            self.ssh.connect(
                hostname=self.host,
                username=self.username,
                pkey=key,
                timeout=30
            )
            print("✅ SSH连接成功")
            return True
        except Exception as e:
            error_msg = f"SSH连接失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.results["errors"].append(error_msg)
            return False
    
    def execute_command(self, command, description=""):
        """执行SSH命令"""
        try:
            if description:
                print(f"执行: {description}")
            
            stdin, stdout, stderr = self.ssh.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if exit_status == 0:
                print(f"✅ {description or command} - 成功")
                return True, output
            else:
                print(f"❌ {description or command} - 失败: {error}")
                self.results["errors"].append(f"{description}: {error}")
                return False, error
        except Exception as e:
            error_msg = f"命令执行失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.results["errors"].append(error_msg)
            return False, str(e)
    
    def stop_all_containers(self):
        """停止所有Docker容器"""
        print("\n=== 停止所有Docker容器 ===")
        success, _ = self.execute_command(
            "sudo docker stop $(sudo docker ps -q) 2>/dev/null || true",
            "停止所有运行中的容器"
        )
        if success:
            self.results["fixes_applied"].append("停止所有Docker容器")
        return success
    
    def remove_problematic_containers(self):
        """删除有问题的容器"""
        print("\n=== 删除有问题的容器 ===")
        containers_to_remove = [
            "automotive_chatbot-frontend-1",
            "automotive_chatbot-rasa-actions-1",
            "automotive_chatbot-nginx-1"
        ]
        
        for container in containers_to_remove:
            success, _ = self.execute_command(
                f"sudo docker rm -f {container} 2>/dev/null || true",
                f"删除容器 {container}"
            )
        
        self.results["fixes_applied"].append("删除有问题的容器")
        return True
    
    def rebuild_frontend_container(self):
        """重新构建前端容器"""
        print("\n=== 重新构建前端容器 ===")
        
        # 进入项目目录并重新构建
        commands = [
            ("cd /home/ubuntu/CSIT321-FYP-Chatbot-for-Customer-Support/WireFrames/automotive_chatbot", "进入项目目录"),
            ("sudo docker-compose build --no-cache frontend", "重新构建前端容器"),
        ]
        
        for command, desc in commands:
            success, output = self.execute_command(command, desc)
            if not success:
                return False
        
        self.results["fixes_applied"].append("重新构建前端容器")
        return True
    
    def fix_nginx_config(self):
        """修复Nginx配置"""
        print("\n=== 修复Nginx配置 ===")
        
        # 检查并修复nginx配置
        nginx_config = '''
server {
    listen 80;
    server_name _;
    
    # 前端静态文件
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Rasa webhook
    location /webhooks/ {
        proxy_pass http://rasa:5005/webhooks/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
'''
        
        # 写入nginx配置
        success, _ = self.execute_command(
            f"echo '{nginx_config}' | sudo tee /home/ubuntu/CSIT321-FYP-Chatbot-for-Customer-Support/WireFrames/automotive_chatbot/nginx/nginx.conf",
            "更新Nginx配置文件"
        )
        
        if success:
            self.results["fixes_applied"].append("修复Nginx配置")
        return success
    
    def start_all_services(self):
        """启动所有服务"""
        print("\n=== 启动所有服务 ===")
        
        # 进入项目目录
        success, _ = self.execute_command(
            "cd /home/ubuntu/CSIT321-FYP-Chatbot-for-Customer-Support/WireFrames/automotive_chatbot",
            "进入项目目录"
        )
        
        if not success:
            return False
        
        # 启动所有服务
        success, output = self.execute_command(
            "cd /home/ubuntu/CSIT321-FYP-Chatbot-for-Customer-Support/WireFrames/automotive_chatbot && sudo docker-compose up -d",
            "启动所有Docker服务"
        )
        
        if success:
            self.results["fixes_applied"].append("启动所有Docker服务")
            # 等待服务启动
            print("等待服务启动...")
            time.sleep(30)
        
        return success
    
    def test_ports(self):
        """测试所有端口"""
        print("\n=== 测试端口状态 ===")
        
        ports_to_test = {
            "80": "Nginx (前端)",
            "3000": "Frontend", 
            "5005": "Rasa",
            "5055": "Rasa Actions",
            "8000": "Backend API"
        }
        
        for port, service in ports_to_test.items():
            success, output = self.execute_command(
                f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port} --connect-timeout 5 || echo 'FAILED'",
                f"测试端口 {port} ({service})"
            )
            
            if success and output.strip() not in ['FAILED', '000']:
                self.results["port_status"][port] = {
                    "status": "accessible",
                    "service": service,
                    "response_code": output.strip()
                }
                print(f"✅ 端口 {port} ({service}) - 可访问 (HTTP {output.strip()})")
            else:
                self.results["port_status"][port] = {
                    "status": "failed",
                    "service": service,
                    "error": output.strip() if output else "连接失败"
                }
                print(f"❌ 端口 {port} ({service}) - 无法访问")
    
    def check_docker_status(self):
        """检查Docker容器状态"""
        print("\n=== 检查Docker容器状态 ===")
        
        success, output = self.execute_command(
            "sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
            "获取Docker容器状态"
        )
        
        if success:
            print("Docker容器状态:")
            print(output)
            self.results["docker_status"] = output
    
    def generate_report(self):
        """生成修复报告"""
        accessible_ports = [port for port, info in self.results["port_status"].items() if info["status"] == "accessible"]
        failed_ports = [port for port, info in self.results["port_status"].items() if info["status"] == "failed"]
        
        self.results["success"] = len(failed_ports) == 0
        
        report = f"""
=== EC2修复完成报告 ===
时间: {self.results['timestamp']}
服务器: {self.results['host']}

已应用的修复:
{chr(10).join(f"- {fix}" for fix in self.results['fixes_applied'])}

端口状态:
✅ 可访问端口: {', '.join(accessible_ports) if accessible_ports else '无'}
❌ 失败端口: {', '.join(failed_ports) if failed_ports else '无'}

详细端口信息:
{chr(10).join(f"端口 {port}: {info['service']} - {info['status']}" for port, info in self.results['port_status'].items())}

错误信息:
{chr(10).join(f"- {error}" for error in self.results['errors']) if self.results['errors'] else '无错误'}

修复状态: {'✅ 完全成功' if self.results['success'] else '❌ 部分失败'}
"""
        
        print(report)
        
        # 保存报告到文件
        with open("EC2_COMPLETE_FIX_REPORT.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return self.results["success"]
    
    def run_complete_fix(self):
        """运行完整修复流程"""
        print("开始EC2完整修复流程...")
        
        # 1. 连接SSH
        if not self.connect_ssh():
            print("❌ 无法连接到服务器，请检查EC2实例是否运行")
            return False
        
        try:
            # 2. 停止所有容器
            self.stop_all_containers()
            
            # 3. 删除有问题的容器
            self.remove_problematic_containers()
            
            # 4. 修复Nginx配置
            self.fix_nginx_config()
            
            # 5. 重新构建前端容器
            self.rebuild_frontend_container()
            
            # 6. 启动所有服务
            self.start_all_services()
            
            # 7. 检查Docker状态
            self.check_docker_status()
            
            # 8. 测试所有端口
            self.test_ports()
            
            # 9. 生成报告
            success = self.generate_report()
            
            return success
            
        except Exception as e:
            error_msg = f"修复过程中发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            self.results["errors"].append(error_msg)
            return False
        
        finally:
            if self.ssh:
                self.ssh.close()
                print("SSH连接已关闭")

def main():
    """主函数"""
    print("=== AWS EC2完整修复脚本 ===")
    print("目标服务器: 13.215.240.173")
    print("修复内容: CSS丢失、端口无法访问、Docker服务异常")
    print("="*50)
    
    fixer = EC2CompleteFixer()
    success = fixer.run_complete_fix()
    
    if success:
        print("\n🎉 修复完成！所有服务已恢复正常")
        print("可以访问以下地址:")
        print("- 主页: http://13.215.240.173/")
        print("- API: http://13.215.240.173:8000/")
        print("- Rasa: http://13.215.240.173:5005/")
        print("- Rasa Actions: http://13.215.240.173:5055/")
    else:
        print("\n❌ 修复未完全成功，请查看报告了解详情")
        print("如果EC2实例停止，请手动重启后重新运行此脚本")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())