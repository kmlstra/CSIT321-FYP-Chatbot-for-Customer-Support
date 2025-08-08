# 🚀 Quick Start Guide

## Prerequisites
- **Python 3.9+** installed
- **Node.js 18+** and npm installed  
- **MongoDB** running locally (or MongoDB Atlas)
- **Git** for version control

## ⚡ One-Command Setup

### 1. Clone and Setup
```bash
git clone <repository-url>
cd WireFrames/automotive_chatbot
python setup.py
```

The `setup.py` will automatically:
- Create virtual environment (`.venv`)
- Install all Python dependencies
- Install Node.js dependencies  
- Download required models
- Setup MongoDB connection
- Configure environment variables

### 2. Start All Services (Including Rasa)
```bash
npm run dev:all
```

This will start:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Rasa Chatbot**: http://localhost:5005

### 3. Start without Rasa (Optional)
```bash
npm run dev:all-no-rasa
```

This starts only Frontend and Backend services.

## 🛠️ Manual Setup (if needed)

### Step 1: Python Environment
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac/Linux
```

### Step 2: Install Dependencies
```bash
pip install -r backend/requirements.txt
npm install
```

### Step 3: Download Models
```bash
python -m spacy download en_core_web_sm
```

### Step 4: Setup Database
```bash
python mongodb_setup.py
```

### Step 5: Environment Variables
Create `.env` file in root:
```env
OPENAI_API_KEY=your_openai_key_here
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=automotive_chatbot
LTA_API_KEY=your_singapore_lta_key
```

## 🎯 Quick Test

### Test Backend API
```bash
curl http://localhost:8000/health
```

### Test Rasa Training
```bash
cd backend
rasa train
```

### Test Frontend
Visit: http://localhost:3000

## 🚨 Common Issues

### Issue: "rasa: command not found"
**Solution**: Make sure virtual environment is activated and Rasa is installed
```bash
.venv\Scripts\activate
pip install rasa==3.6.20
```

### Issue: MongoDB connection error
**Solution**: Start MongoDB service
```bash
# Windows
net start MongoDB

# Mac
brew services start mongodb-community

# Linux  
sudo systemctl start mongod
```

### Issue: Port already in use
**Solution**: Kill processes on ports 3000, 8000, 5005
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <process_id> /F

# Mac/Linux
lsof -ti:3000 | xargs kill -9
```

## 📱 Access Points

Once everything is running:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main chatbot interface |
| Backend API | http://localhost:8000 | REST API endpoints |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Rasa API | http://localhost:5005 | Conversational AI engine |
| MongoDB | mongodb://localhost:27017 | Database connection |

## 🎉 You're Ready!

Your automotive chatbot platform is now running! Visit the frontend to start chatting with the AI assistant about cars, COE prices, and automotive services in Singapore.

## 📚 Next Steps

- [User Manual](USER_MANUAL.md) - Detailed usage guide
- [Integration Guide](INTEGRATION_GUIDE.md) - API integration examples  
- [Rasa Setup](RASA_SETUP.md) - Advanced Rasa configuration
- [MongoDB Setup](MONGODB_SETUP.md) - Database configuration 