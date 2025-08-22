# EC2实例重启和服务恢复指导

## 概述
本指导文档提供了重启AWS EC2实例和恢复所有服务的详细步骤。

## 前提条件
- AWS控制台访问权限
- SSH密钥文件 (cc.pem)
- 基本的Linux命令行知识

## 步骤1: 检查EC2实例状态

### 通过AWS控制台
1. 登录AWS控制台: https://console.aws.amazon.com/
2. 导航到EC2服务
3. 在左侧菜单选择 "Instances"
4. 查找实例IP: 13.215.240.173
5. 检查实例状态:
   - **Running**: 实例正在运行
   - **Stopped**: 实例已停止
   - **Stopping**: 实例正在停止
   - **Pending**: 实例正在启动

### 通过AWS CLI (可选)
```bash
# 如果已配置AWS CLI
aws ec2 describe-instances --filters "Name=ip-address,Values=13.215.240.173"
```

## 步骤2: 重启EC2实例

### 方法1: 通过AWS控制台 (推荐)
1. 在EC2控制台中选择目标实例
2. 点击 "Instance state" 下拉菜单
3. 选择适当的操作:
   - 如果实例状态是 "Running": 选择 "Reboot instance"
   - 如果实例状态是 "Stopped": 选择 "Start instance"
4. 确认操作
5. 等待实例状态变为 "Running"

### 方法2: 通过AWS CLI
```bash
# 重启运行中的实例
aws ec2 reboot-instances --instance-ids i-xxxxxxxxx

# 启动已停止的实例
aws ec2 start-instances --instance-ids i-xxxxxxxxx
```

## 步骤3: 验证网络连接

### 基本连通性测试
```powershell
# Windows PowerShell
Test-Connection -ComputerName 13.215.240.173 -Count 4
```

```bash
# Linux/Mac
ping -c 4 13.215.240.173
```

### SSH连接测试
```bash
# 测试SSH连接
ssh -i cc.pem -o ConnectTimeout=10 ubuntu@13.215.240.173 "echo 'SSH connection successful'"
```

## 步骤4: 检查和恢复Docker服务

### 连接到EC2实例
```bash
ssh -i cc.pem ubuntu@13.215.240.173
```

### 检查Docker状态
```bash
# 检查Docker服务状态
sudo systemctl status docker

# 如果Docker未运行，启动它
sudo systemctl start docker
sudo systemctl enable docker
```

### 检查Docker Compose服务
```bash
# 进入项目目录
cd /home/ubuntu/automotive-chatbot

# 检查容器状态
sudo docker-compose ps

# 查看所有容器（包括停止的）
sudo docker ps -a
```

## 步骤5: 重启应用服务

### 完全重启所有服务
```bash
# 停止所有服务
sudo docker-compose down

# 拉取最新镜像（可选）
sudo docker-compose pull

# 启动所有服务
sudo docker-compose up -d

# 检查启动状态
sudo docker-compose ps
```

### 单独重启特定服务
```bash
# 重启Rasa服务
sudo docker-compose restart automotive-rasa

# 重启Backend服务
sudo docker-compose restart automotive-backend

# 重启Frontend服务
sudo docker-compose restart automotive-frontend
```

## 步骤6: 验证服务状态

### 检查容器日志
```bash
# 查看Rasa容器日志
sudo docker logs automotive-rasa --tail 20

# 查看Backend容器日志
sudo docker logs automotive-backend --tail 20

# 查看Frontend容器日志
sudo docker logs automotive-frontend --tail 20

# 实时查看日志
sudo docker-compose logs -f
```

### 检查容器健康状态
```bash
# 检查容器进程
sudo docker exec automotive-rasa ps aux
sudo docker exec automotive-backend ps aux
sudo docker exec automotive-frontend ps aux
```

## 步骤7: 测试API端点

### 从EC2实例内部测试
```bash
# 测试Backend API
curl http://localhost:8000/health

# 测试Rasa API
curl http://localhost:5005/

# 测试Rasa Actions
curl http://localhost:5055/

# 测试Frontend
curl http://localhost:3000/
```

### 从外部测试
```bash
# 测试所有外部端点
curl http://13.215.240.173:8000/health
curl http://13.215.240.173:5005/
curl http://13.215.240.173:5055/
curl http://13.215.240.173:3000/
```

### 使用PowerShell测试
```powershell
# 运行本地测试脚本
powershell -ExecutionPolicy Bypass -File .\aws-status-check.ps1
```

## 步骤8: 特殊问题处理

### Rasa服务启动问题
如果Rasa服务无法正常启动：

```bash
# 进入Rasa容器进行调试
sudo docker exec -it automotive-rasa bash

# 检查启动脚本
cat /app/start-rasa.sh

# 手动启动Rasa服务
cd /app
python -m rasa run --model models/current.tar.gz --port 5005 --host 0.0.0.0 --enable-api --cors "*"
```

### 端口冲突问题
```bash
# 检查端口使用情况
sudo netstat -tlnp | grep :5005
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :3000

# 杀死占用端口的进程
sudo kill -9 <PID>
```

### 磁盘空间问题
```bash
# 检查磁盘使用情况
df -h

# 清理Docker资源
sudo docker system prune -f
sudo docker volume prune -f

# 清理日志文件
sudo journalctl --vacuum-time=7d
```

## 步骤9: 安全组配置检查

### 必需的入站规则
确保以下端口在安全组中开放：

| 端口 | 协议 | 源 | 描述 |
|------|------|----|----- |
| 22 | TCP | 0.0.0.0/0 | SSH访问 |
| 80 | TCP | 0.0.0.0/0 | HTTP访问 |
| 443 | TCP | 0.0.0.0/0 | HTTPS访问 |
| 3000 | TCP | 0.0.0.0/0 | Frontend应用 |
| 5005 | TCP | 0.0.0.0/0 | Rasa API |
| 5055 | TCP | 0.0.0.0/0 | Rasa Actions |
| 8000 | TCP | 0.0.0.0/0 | Backend API |

### 通过AWS控制台检查
1. 在EC2控制台选择实例
2. 点击 "Security" 标签
3. 点击安全组链接
4. 检查 "Inbound rules" 标签
5. 确保所有必需端口都已开放

## 步骤10: 监控和维护

### 设置监控脚本
```bash
# 创建健康检查脚本
cat > /home/ubuntu/health-check.sh << 'EOF'
#!/bin/bash
echo "Health check at $(date)"
echo "Checking services..."

# 检查Docker服务
if ! systemctl is-active --quiet docker; then
    echo "ERROR: Docker service is not running"
    exit 1
fi

# 检查容器状态
if ! docker-compose ps | grep -q "Up"; then
    echo "ERROR: Some containers are not running"
    docker-compose ps
    exit 1
fi

# 检查API端点
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: Backend API is not responding"
    exit 1
fi

if ! curl -f http://localhost:5005/ > /dev/null 2>&1; then
    echo "ERROR: Rasa API is not responding"
    exit 1
fi

echo "All services are healthy"
EOF

chmod +x /home/ubuntu/health-check.sh
```

### 设置定时任务
```bash
# 添加到crontab
crontab -e

# 添加以下行（每5分钟检查一次）
*/5 * * * * /home/ubuntu/health-check.sh >> /var/log/health-check.log 2>&1
```

## 故障排除清单

- [ ] EC2实例状态为 "Running"
- [ ] 网络连接正常 (ping成功)
- [ ] SSH连接正常
- [ ] Docker服务运行中
- [ ] 所有容器状态为 "Up"
- [ ] Backend API (8000) 响应正常
- [ ] Rasa API (5005) 响应正常
- [ ] Rasa Actions (5055) 响应正常
- [ ] Frontend (3000) 响应正常
- [ ] 安全组配置正确
- [ ] 磁盘空间充足
- [ ] 日志无严重错误

## 紧急联系信息

- **AWS支持**: https://console.aws.amazon.com/support/
- **实例区域**: ap-southeast-1 (新加坡)
- **实例IP**: 13.215.240.173

## 备注

- 重启过程通常需要2-5分钟
- 如果问题持续存在，考虑创建新的AMI快照
- 定期备份重要数据和配置
- 监控AWS账单以避免意外费用

---

**最后更新**: 2024年12月19日
**版本**: 1.0