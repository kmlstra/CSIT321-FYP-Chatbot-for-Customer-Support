# AWS Docker服务器修复指南

## 问题概述

**当前状态 (2025-08-21 10:45)**:
- ✅ Nginx服务运行中 (端口80)
- ❌ 后端API服务无响应 (端口8000)
- ❌ 前端服务无响应 (端口3000)
- ❌ Rasa服务无响应 (端口5005)
- ❌ Rasa Actions无响应 (端口5055)
- ❌ SSH连接失败 (端口22)

**关键发现**:
- Nginx返回502 Bad Gateway错误，表明反向代理配置正常但后端服务不可用
- 服务器实例可能正在运行，但Docker容器有问题
- 需要通过AWS控制台进行修复

## 立即修复方案

### 方案1: AWS控制台重启实例 (推荐)

#### 步骤1: 检查EC2实例状态
1. 登录AWS管理控制台
2. 导航到 EC2 > 实例
3. 找到实例 `13.215.240.173`
4. 检查实例状态:
   - 如果状态为 "stopped" → 启动实例
   - 如果状态为 "running" → 继续下一步
   - 如果状态为 "pending" → 等待启动完成

#### 步骤2: 重启实例
```bash
# 在AWS控制台中:
1. 选择实例
2. 点击 "实例状态" > "重新启动实例"
3. 确认重启
4. 等待3-5分钟让所有服务启动
```

#### 步骤3: 验证服务恢复
等待重启完成后，检查以下URL:
- http://13.215.240.173/ (前端)
- http://13.215.240.173:8000/health (后端健康检查)
- http://13.215.240.173:8000/docs (API文档)

### 方案2: 通过AWS Systems Manager (如果SSH不可用)

#### 前提条件
- EC2实例需要安装SSM Agent
- 实例需要适当的IAM角色

#### 执行命令
1. 在AWS控制台中导航到 Systems Manager > Session Manager
2. 启动会话到目标实例
3. 执行以下命令:

```bash
# 检查Docker服务状态
sudo systemctl status docker

# 重启Docker服务
sudo systemctl restart docker

# 进入项目目录
cd /home/ubuntu/automotive_chatbot

# 重启所有容器
sudo docker-compose -f docker-compose.prod.yml down
sudo docker-compose -f docker-compose.prod.yml up -d

# 检查容器状态
sudo docker ps -a
```

### 方案3: 安全组和网络配置检查

#### 检查安全组设置
1. 在EC2控制台中选择实例
2. 点击 "安全" 选项卡
3. 检查安全组规则:

**必需的入站规则**:
```
端口 22  (SSH)     - 您的IP地址
端口 80  (HTTP)    - 0.0.0.0/0
端口 443 (HTTPS)   - 0.0.0.0/0
端口 3000 (前端)   - 0.0.0.0/0 (可选，用于直接访问)
端口 5005 (Rasa)   - 0.0.0.0/0 (可选，用于直接访问)
端口 8000 (后端)   - 0.0.0.0/0 (可选，用于直接访问)
```

#### 检查弹性IP
1. 导航到 EC2 > 弹性IP
2. 确认IP `13.215.240.173` 仍然关联到正确的实例
3. 如果未关联，重新关联

## 详细故障排除

### 问题1: Nginx返回502错误

**原因**: 后端服务容器未运行或无法访问

**解决方案**:
```bash
# 检查后端容器状态
sudo docker ps | grep automotive-backend

# 如果容器未运行，重启
sudo docker restart automotive-backend

# 检查容器日志
sudo docker logs automotive-backend --tail 50

# 检查网络连接
sudo docker exec automotive-nginx-prod ping automotive-backend
```

### 问题2: 前端服务无响应

**原因**: 前端容器未运行或构建失败

**解决方案**:
```bash
# 重启前端容器
sudo docker restart automotive-frontend

# 检查前端日志
sudo docker logs automotive-frontend --tail 50

# 如果需要重新构建
sudo docker-compose -f docker-compose.prod.yml build frontend
sudo docker-compose -f docker-compose.prod.yml up -d frontend
```

### 问题3: Rasa服务无响应

**原因**: Rasa容器启动失败或模型加载问题

**解决方案**:
```bash
# 重启Rasa服务
sudo docker restart automotive-rasa
sudo docker restart automotive-rasa-actions

# 检查Rasa日志
sudo docker logs automotive-rasa --tail 50
sudo docker logs automotive-rasa-actions --tail 50

# 检查模型文件
sudo docker exec automotive-rasa ls -la /app/models/
```

## 预防措施

### 1. 设置CloudWatch监控
```bash
# 创建实例状态检查警报
# 在CloudWatch控制台中设置:
- 实例状态检查失败警报
- 系统状态检查失败警报
- CPU使用率异常警报
```

### 2. 自动重启脚本
创建定时任务检查服务健康状态:
```bash
# 在实例中添加crontab
*/5 * * * * /home/ubuntu/health-check.sh
```

### 3. 备份和快照
```bash
# 定期创建EBS快照
# 在EC2控制台中:
1. 选择实例
2. 存储 > 创建快照
3. 设置自动快照策略
```

## 验证修复成功

### 检查清单
- [ ] EC2实例状态为 "running"
- [ ] 所有Docker容器正在运行
- [ ] http://13.215.240.173/ 返回前端页面
- [ ] http://13.215.240.173:8000/health 返回健康状态
- [ ] http://13.215.240.173:8000/docs 显示API文档
- [ ] Rasa服务可以处理请求
- [ ] SSH连接恢复正常

### 测试命令
```bash
# 本地测试脚本
python aws_server_diagnostic.py

# 手动测试
curl -X GET "http://13.215.240.173:8000/health"
curl -X POST "http://13.215.240.173/webhooks/rest/webhook" \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'
```

## 联系信息

**紧急联系**:
- AWS支持: 如果实例无法启动
- 系统管理员: 如果需要权限协助

**文档更新**: 2025-08-21 10:45
**状态**: 等待执行修复方案

---

## 执行记录

### 修复尝试 #1
- **时间**: 2025-08-21 10:45
- **执行者**: 自动化脚本
- **方案**: 通过HTTP端点尝试修复
- **结果**: 失败 - 需要AWS控制台操作
- **下一步**: 执行方案1 (重启实例)

### 修复尝试 #2
- **时间**: _待填写_
- **执行者**: _待填写_
- **方案**: _待填写_
- **结果**: _待填写_