# MongoDB Setup Guide

## 🗄️ MongoDB Configuration for Automotive Chatbot Platform

### Quick Setup

1. **Check if MongoDB is running:**
   ```bash
   .venv\Scripts\python backend\utils\db_checker.py
   ```

2. **Setup MongoDB connection:**
   ```bash
   .venv\Scripts\python mongodb_setup.py
   ```

## 📋 Connection Options

### Option 1: Local MongoDB (Default)
```env
# backend/.env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=chatbot_platform
```

### Option 2: MongoDB with Authentication
```env
# backend/.env
MONGODB_URL=mongodb://username:password@localhost:27017/chatbot_platform
MONGODB_DB=chatbot_platform
```

### Option 3: MongoDB Atlas (Cloud)
```env
# backend/.env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/chatbot_platform?retryWrites=true&w=majority
MONGODB_DB=chatbot_platform
```

### Option 4: Custom Host/Port
```env
# backend/.env
MONGODB_URL=mongodb://localhost:27018
MONGODB_DB=chatbot_platform
```

### Option 5: Docker MongoDB
```bash
# Start MongoDB in Docker
docker run -d -p 27017:27017 --name mongodb mongo

# Or with authentication
docker run -d -p 27017:27017 --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo
```

## 🔧 Configuration Files

### 1. Environment Variables (`backend/.env`)
```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=chatbot_platform
MONGODB_TIMEOUT=5000

# Optional: MongoDB Atlas
# MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/

# Optional: With Authentication
# MONGODB_URL=mongodb://admin:password@localhost:27017/chatbot_platform?authSource=admin
```

### 2. Database Configuration (`backend/config/database.py`)
This file handles all MongoDB connections and provides:
- Automatic connection management
- Health checks
- Collection shortcuts
- Error handling

### 3. API Configuration (`backend/api/config.py`)
Contains all application settings including MongoDB settings.

## 🧪 Testing MongoDB Connection

### Method 1: Database Checker Script
```bash
.venv\Scripts\python backend\utils\db_checker.py
```
**Output:**
```
🚗 Automotive Chatbot - MongoDB Connectivity Checker
=======================================================
🔄 Connecting to MongoDB...
📍 URL: mongodb://localhost:27017
🗄️  Database: chatbot_platform
✅ MongoDB connection successful!

📊 MongoDB Server Info:
   Version: 7.0.4
   Platform: windows

🗃️  Available Databases: admin, config, local, chatbot_platform
✅ Database 'chatbot_platform' exists
📁 Collections: users, chatbots, conversations

🧪 Testing basic operations...
✅ Insert test: Success
✅ Read test: Success
✅ Update test: Success
✅ Delete test: Success
🎉 All database operations working correctly!
```

### Method 2: API Health Check
```bash
# Check via FastAPI health endpoint
curl http://localhost:8000/health
```

### Method 3: Status Checker
```bash
.venv\Scripts\python check_status.py
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "MongoDB connection failed: [Errno 11001] getaddrinfo failed"
**Solution:** MongoDB is not running
```bash
# Windows
net start MongoDB

# Linux/Mac
sudo systemctl start mongod

# Docker
docker start mongodb
```

#### 2. "Authentication failed"
**Solution:** Check credentials in `.env` file
```env
# Correct format for authenticated MongoDB
MONGODB_URL=mongodb://username:password@localhost:27017/database_name?authSource=admin
```

#### 3. "Server selection timeout"
**Solution:** Check if MongoDB is accessible
```bash
# Test MongoDB directly
mongo --eval "db.adminCommand('ismaster')"

# Or check service status
sc query MongoDB
```

#### 4. "No module named 'pymongo'"
**Solution:** Install dependencies
```bash
.venv\Scripts\pip install pymongo motor
```

### MongoDB Installation

#### Windows
1. Download from https://www.mongodb.com/try/download/community
2. Install as Windows Service
3. Start service: `net start MongoDB`

#### Using Docker
```bash
# Quick start
docker run -d -p 27017:27017 mongo

# With persistent data
docker run -d -p 27017:27017 -v mongodb_data:/data/db mongo

# With authentication
docker run -d -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo
```

#### MongoDB Atlas (Cloud)
1. Create account at https://www.mongodb.com/atlas
2. Create cluster
3. Get connection string
4. Update `.env` file

## 📊 Database Schema

### Collections Structure
```javascript
// users
{
  "_id": ObjectId,
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": ISODate,
  "updated_at": ISODate
}

// chatbots
{
  "_id": ObjectId,
  "name": "Automotive Assistant",
  "description": "Expert in automotive advice",
  "owner_id": ObjectId,
  "config": {},
  "created_at": ISODate
}

// conversations
{
  "_id": ObjectId,
  "user_id": "anonymous_user_123",
  "chatbot_id": ObjectId,
  "messages": [
    {
      "role": "user",
      "content": "What's the best engine oil?",
      "timestamp": ISODate
    },
    {
      "role": "assistant", 
      "content": "For most vehicles...",
      "timestamp": ISODate
    }
  ],
  "created_at": ISODate
}
```

## 🔗 Integration

### Using in FastAPI Routes
```python
from backend.config.database import get_chatbots_collection

@router.post("/chatbots")
async def create_chatbot(chatbot_data: dict):
    collection = await get_chatbots_collection()
    result = await collection.insert_one(chatbot_data)
    return {"id": str(result.inserted_id)}
```

### Health Check Endpoint
```python
from backend.config.database import db_config

@app.get("/health")
async def health_check():
    db_health = await db_config.health_check()
    return {
        "api": "healthy",
        "database": db_health
    }
``` 