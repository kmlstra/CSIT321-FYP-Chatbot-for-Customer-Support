# Docker Hub部署指南

## 概述
本指南说明如何在AWS EC2上部署来自Docker Hub的automotive-chatbot镜像。

## 前置条件
- AWS EC2实例已启动并运行
- Docker和Docker Compose已安装
- 安全组已配置允许以下端口：80, 5005, 5055, 8000, 6379, 9090, 3001

## 部署步骤

### 1. 连接到AWS EC2实例
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 2. 安装Docker和Docker Compose（如果尚未安装）
```bash
# 更新系统
sudo apt update

# 安装Docker
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录以应用用户组更改
exit
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3. 创建部署目录
```bash
mkdir -p ~/automotive-chatbot-deployment
cd ~/automotive-chatbot-deployment
```

### 4. 下载配置文件
```bash
# 下载docker-compose配置
wget https://raw.githubusercontent.com/your-repo/automotive-chatbot/main/WireFrames/automotive_chatbot/aws-deployment/docker/docker-compose-unified.yml

# 下载其他必要的配置文件
wget https://raw.githubusercontent.com/your-repo/automotive-chatbot/main/WireFrames/automotive_chatbot/aws-deployment/docker/endpoints-aws.yml
wget https://raw.githubusercontent.com/your-repo/automotive-chatbot/main/WireFrames/automotive_chatbot/aws-deployment/docker/prometheus.yml
```

### 5. 设置环境变量
```bash
# 创建.env文件
cat > .env << EOF
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET=your_jwt_secret_key
CORS_ORIGINS=http://your-ec2-ip,https://your-domain.com
REDIS_PASSWORD=your_redis_password
GRAFANA_PASSWORD=your_grafana_admin_password
EOF
```

### 6. 拉取Docker镜像
```bash
# 拉取主应用镜像
docker pull ethernallove/automotive-chatbot:latest

# 拉取监控镜像
docker pull prom/prometheus:latest
docker pull grafana/grafana:latest
```

### 7. 启动服务
```bash
# 启动所有服务
docker-compose -f docker-compose-unified.yml up -d

# 查看服务状态
docker-compose -f docker-compose-unified.yml ps

# 查看日志
docker-compose -f docker-compose-unified.yml logs -f
```

### 8. 验证部署
```bash
# 检查主应用健康状态
curl http://localhost:80/health
curl http://localhost:8000/health
curl http://localhost:5005/status

# 检查各服务端口
netstat -tlnp | grep -E ':(80|5005|5055|8000|6379|9090|3001)'
```

## 服务端口说明
- **80**: 前端应用 (Nginx)
- **8000**: 后端API (FastAPI)
- **5005**: RASA Core服务
- **5055**: RASA Actions服务
- **6379**: Redis缓存
- **9090**: Prometheus监控
- **3001**: Grafana仪表板

## 访问应用
- 主应用: http://your-ec2-ip
- API文档: http://your-ec2-ip:8000/docs
- RASA状态: http://your-ec2-ip:5005/status
- Prometheus: http://your-ec2-ip:9090
- Grafana: http://your-ec2-ip:3001

## 常用管理命令
```bash
# 停止所有服务
docker-compose -f docker-compose-unified.yml down

# 重启服务
docker-compose -f docker-compose-unified.yml restart

# 更新镜像
docker pull ethernallove/automotive-chatbot:latest
docker-compose -f docker-compose-unified.yml up -d

# 查看资源使用情况
docker stats

# 清理未使用的镜像
docker image prune -f
```

## 故障排除

### 1. 服务无法启动
```bash
# 查看详细日志
docker-compose -f docker-compose-unified.yml logs automotive-chatbot

# 检查容器状态
docker ps -a
```

### 2. 端口冲突
```bash
# 检查端口占用
sudo netstat -tlnp | grep :80
sudo lsof -i :80
```

### 3. 内存不足
```bash
# 检查系统资源
free -h
df -h
docker system df
```

## 安全建议
1. 定期更新Docker镜像
2. 使用强密码设置环境变量
3. 配置防火墙规则
4. 启用SSL/TLS加密
5. 定期备份数据卷

## 监控和日志
- 使用Prometheus和Grafana进行系统监控
- 日志文件位置: `/app/logs`（容器内）
- 使用`docker-compose logs`查看实时日志