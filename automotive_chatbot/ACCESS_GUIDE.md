# 🚀 Quick Access Guide

## 🌐 How to Access the Application

### 1. Start All Services
```bash
npm run dev:all
```
**Wait for all services to start (about 2-3 minutes)**

### 2. Access URLs

#### 🏠 **Admin Dashboard (page.tsx)**
- **URL**: `http://localhost:3000/page`
- **Login Token**: `admin_demo_token`
- **What it does**: System configuration, RASA training, analytics

#### 💬 **Main Chatbot Interface**
- **URL**: `http://localhost:3000`
- **What it does**: Chat with the automotive bot

#### 🔧 **Backend API & Documentation**
- **URL**: `http://localhost:8000/docs`
- **What it does**: API testing, endpoint documentation

#### 🤖 **RASA API (for testing)**
- **URL**: `http://localhost:5005`
- **What it does**: Direct RASA API access

---

## 🛠️ Troubleshooting

### ❌ "Connection Refused" Error
**Problem**: Using wrong port (8080 doesn't exist)
**Solution**: Use correct ports:
- Frontend: `3000` (NOT 8080)
- Backend: `8000`

### ❌ "RASA Actions Not Found"
**Problem**: Actions server not connected
**Solution**: 
```bash
npm run kill-ports
# Wait 10 seconds
npm run dev:all
```

### ❌ Frontend Not Loading
**Problem**: Next.js compilation issues
**Solution**: Clear cache and restart
```bash
cd frontend
rm -rf .next
cd ..
npm run dev:all
```

---

## 📱 Quick Test Steps

1. **Start services**: `npm run dev:all`
2. **Open Chrome**: Go to `http://localhost:3000/page`
3. **Login**: Use token `admin_demo_token`
4. **Test chat**: Go to `http://localhost:3000` and type "hello"
5. **Check backend**: Visit `http://localhost:8000/docs`

---

## 🎯 What Each Service Does

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 3000 | React UI (Admin + Chat) |
| **Backend** | 8000 | FastAPI (BCE Architecture) |
| **RASA** | 5005 | NLU & Dialogue Management |
| **Actions** | 5055 | Custom RASA Actions |

---

## 🚨 Common Mistakes

1. ❌ **Using port 8080** → ✅ Use port 3000
2. ❌ **Accessing before services start** → ✅ Wait for "All services started successfully!"
3. ❌ **Wrong login token** → ✅ Use `admin_demo_token`
4. ❌ **Not clearing cache** → ✅ Kill ports and restart

**🎉 Success indicator**: You should see "All services started successfully!" message 