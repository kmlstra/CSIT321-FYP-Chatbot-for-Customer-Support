# AWS Docker服务器紧急修复指南

## 🚨 当前问题诊断

**检查时间**: 2024年1月20日  
**服务器IP**: 13.215.240.173  
**问题状态**: 所有服务超时，疑似EC2实例已停止

### 诊断结果
- ❌ Frontend: 请求超时
- ❌ Backend Health: 请求超时  
- ❌ Backend Docs: 请求超时
- ❌ Rasa Webhook: 请求超时
- ❌ Nginx Status: 请求超时
- ❌ Rasa功能测试: HTTP 502错误

## 🔧 立即修复步骤

### 步骤1: 检查EC2实例状态

1. **登录AWS控制台**
   - 访问: https://console.aws.amazon.com/
   - 选择正确的区域 (新加坡 ap-southeast-1)

2. **检查EC2实例**
   ```
   服务 > EC2 > 实例
   查找实例ID或IP: 13.215.240.173
   检查实例状态:
   - 🟢 running (运行中)
   - 🟡 pending (启动中) 
   - 🔴 stopped (已停止)
   - 🟠 stopping (停止中)
   ```

### 步骤2: 重启EC2实例 (如果已停止)

1. **选择实例**
   - 勾选目标实例
   - 点击 "实例状态" > "启动实例"

2. **等待启动完成**
   - 状态变为 "running"
   - 等待2-3分钟让服务完全启动

3. **检查公网IP**
   - 确认公网IP仍为: 13.215.240.173
   - 如果IP改变，需要更新DNS/配置

### 步骤3: 通过SSH连接服务器

```bash
# 使用提供的密钥文件连接
ssh -i "cc.pem" ubuntu@13.215.240.173

# 如果连接失败，检查:
# 1. 密钥文件权限: chmod 400 cc.pem
# 2. 安全组是否允许SSH (端口22)
# 3. 实例是否完全启动
```

### 步骤4: 检查Docker服务状态

```bash
# 检查Docker是否运行
sudo systemctl status docker

# 如果Docker未运行，启动它
sudo systemctl start docker
sudo systemctl enable docker

# 检查Docker容器状态
sudo docker ps -a

# 检查Docker Compose服务
cd /path/to/project
sudo docker-compose -f docker-compose.prod.yml ps
```

### 步骤5: 重启所有Docker服务

```bash
# 进入项目目录
cd /home/ubuntu/automotive_chatbot  # 或实际项目路径

# 停止所有服务
sudo docker-compose -f docker-compose.prod.yml down

# 重新启动所有服务
sudo docker-compose -f docker-compose.prod.yml up -d

# 检查服务状态
sudo docker-compose -f docker-compose.prod.yml ps

# 查看服务日志
sudo docker-compose -f docker-compose.prod.yml logs
```

### 步骤6: 单独重启问题服务

```bash
# 重启Nginx (如果502错误)
sudo docker