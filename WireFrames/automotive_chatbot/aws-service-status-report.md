# AWS EC2 服务状态报告

## 报告概述
- **生成时间**: 2024年12月19日
- **EC2实例**: 13.215.240.173
- **检查状态**: 连接超时/无法访问

## 当前问题分析

### 1. 连接问题
- **症状**: 脚本执行超时，无法完成连接测试
- **可能原因**:
  - EC2实例已停止运行
  - 网络连接问题
  - 安全组配置阻止访问
  - SSH密钥权限问题

### 2. 之前发现的问题
根据之前的分析，发现以下问题：
- Rasa服务器(5005端口)启动失败
- 主Rasa服务进程未运行，只有Actions服务(5055端口)在运行
- 启动脚本中的参数解析问题已修复，但服务仍未正常启动

## 服务状态概览

### 预期服务端口
| 服务 | 端口 | 状态 | 说明 |
|------|------|------|------|
| Frontend | 3000 | 未知 | Next.js前端应用 |
| Backend API | 8000 | 未知 | FastAPI后端服务 |
| Rasa Server | 5005 | 故障 | 主Rasa对话服务 |
| Rasa Actions | 5055 | 运行中 | Rasa自定义动作服务 |
| SSH | 22 | 未知 | 远程访问 |
| HTTP | 80 | 未知 | Web访问 |

## 问题诊断步骤

### 1. EC2实例状态检查
```bash
# 通过AWS控制台检查
1. 登录AWS控制台
2. 进入EC2服务
3. 查看实例状态 (Running/Stopped/Terminated)
4. 检查实例健康检查状态
```

### 2. 网络连接测试
```powershell
# 基本连通性测试
Test-Connection -ComputerName 13.215.240.173 -Count 4

# 端口连通性测试
Test-NetConnection -ComputerName 13.215.240.173 -Port 22
Test-NetConnection -ComputerName 13.215.240.173 -Port 80
Test-NetConnection -ComputerName 13.215.240.173 -Port 3000
Test-NetConnection -ComputerName 13.215.240.173 -Port 5005
Test-NetConnection -ComputerName 13.215.240.173 -Port 8000
```

### 3. SSH连接测试
```bash
# SSH连接测试
ssh -i cc.pem -o ConnectTimeout=10 ubuntu@13.215.240.173
```

## 解决方案建议

### 立即行动项

#### 1. 重启EC2实例
```bash
# 通过AWS CLI (如果配置)
aws ec2 reboot-instances --instance-ids i-xxxxxxxxx

# 或通过AWS控制台
1. 选择实例
2. 点击 "Instance state" -> "Reboot instance"
```

#### 2. 检查安全组配置
确保以下端口在安全组中开放：
- 22 (SSH)
- 80 (HTTP)
- 3000 (Frontend)
- 5005 (Rasa Server)
- 5055 (Rasa Actions)
- 8000 (Backend API)

#### 3. 验证Elastic IP
检查实例是否仍然关联到正确的Elastic IP地址

### 服务修复步骤

#### 1. 重新部署Rasa服务
```bash
# SSH到服务器后执行
sudo docker-compose down
sudo docker-compose pull
sudo docker-compose up -d

# 检查容器状态
sudo docker ps -a
sudo docker logs automotive-rasa
```

#### 2. 修复Rasa启动问题
```bash
# 检查启动脚本
sudo docker exec automotive-rasa cat /app/start-rasa.sh

# 手动启动Rasa服务进行调试
sudo docker exec -it automotive-rasa bash
cd /app
python -m rasa run --model models/current.tar.gz --port 5005 --host 0.0.0.0 --enable-api --cors "*"
```

#### 3. 验证所有服务
```bash
# 检查所有端点
curl http://13.215.240.173:8000/health
curl http://13.215.240.173:5005/
curl http://13.215.240.173:5055/
curl http://13.215.240.173:3000/
```

## 监控和维护建议

### 1. 设置CloudWatch监控
- CPU使用率监控
- 内存使用率监控
- 网络流量监控
- 磁盘空间监控

### 2. 自动化健康检查
```bash
# 创建健康检查脚本
#!/bin/bash
echo "Health check at $(date)"
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:5005/ || exit 1
echo "All services healthy"
```

### 3. 日志管理
```bash
# 设置日志轮转
sudo docker-compose logs --tail=100 > /var/log/app-$(date +%Y%m%d).log
```

## 紧急联系信息

### AWS支持
- AWS控制台: https://console.aws.amazon.com/
- EC2实例ID: 需要从控制台获取
- 区域: ap-southeast-1 (新加坡)

### 故障排除清单

- [ ] 检查EC2实例状态
- [ ] 验证网络连接
- [ ] 检查安全组配置
- [ ] 验证SSH密钥
- [ ] 重启EC2实例
- [ ] 检查Docker服务状态
- [ ] 重新部署应用
- [ ] 验证所有API端点
- [ ] 更新DNS记录(如需要)
- [ ] 通知相关团队

## 预防措施

### 1. 定期备份
- 创建AMI快照
- 备份应用数据
- 备份配置文件

### 2. 自动化部署
- 使用CI/CD管道
- 自动化测试
- 滚动更新策略

### 3. 监控告警
- 设置服务不可用告警
- 设置资源使用率告警
- 设置错误率告警

---

**注意**: 此报告基于当前无法连接到EC2实例的情况生成。一旦恢复连接，需要重新运行诊断脚本获取实时状态信息。