# 🚀 Automotive Chatbot Platform - Quick Setup Guide

## 📋 Prerequisites
- **Python 3.9.13** (RASA 3.6.4 compatible)
- **Node.js 18+** and **npm**
- **Git** installed
- **Windows 10/11** (this guide is Windows-specific)
- **MongoDB Atlas Account** (for SaaS database)

---

## 🛠️ Step-by-Step Installation

### Step 0: MongoDB Atlas Setup (NEW - REQUIRED)
```bash
# First, set up your MongoDB Atlas database
cd backend
python setup_mongodb_collections.py
```

**This creates:**
- ✅ All SaaS collections (clients, client_users, conversations, etc.)
- ✅ Sample client data for testing
- ✅ Super admin user (admin@clevercompanion.com / SuperAdmin123!)
- ✅ Proper security indexes and validation

### Step 1: Enable Long Path Support (Git Bash)
```bash
# Run this in Git Bash as Administrator
./enable_longpath.sh
```

### Step 2: Create Virtual Environment
```powershell
# In PowerShell, navigate to project directory
cd WireFrames\automotive_chatbot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install All Dependencies
```powershell
# Run the comprehensive setup script
python setup.py
```

**What this installs:**
- **Backend Python packages:** RASA 3.6.4, FastAPI, LangChain, FAISS, etc.
- **Frontend Node packages:** Next.js, React, Tailwind CSS, etc.
- **All dependencies** listed in requirements.txt and package.json files

### Step 4: Environment Configuration
```powershell
# The .env file is already configured with MongoDB Atlas credentials
# No changes needed for basic setup
```

### Step 5: Train RASA Model (UPDATED)
```powershell
# Train the RASA model with SaaS multi-tenant actions
npm run rasa:train
```

### Step 6: Start All Services (UPDATED)
```powershell
# Option 1: Start everything at once (includes SaaS backend)
npm run dev:all

# Option 2: Clean start (kills existing processes first)
npm run clean-start
```

---

## 🌐 **NEW: SaaS Access Points**

Once running, access these NEW SaaS URLs:

| Service | URL | Description |
|---------|-----|-------------|
| **Client Signup** | http://localhost:3000/client-signup | New automotive businesses register |
| **Client Login** | http://localhost:3000/client-login | Client admin login |
| **Client Dashboard** | http://localhost:3000/client-dashboard | Configure chatbot settings |
| **Super Admin** | http://localhost:3000/super-admin | Manage all clients |
| **Super Admin Login** | http://localhost:3000/super-admin-login | Platform management |
| **Widget API** | http://localhost:8000/api/widget | Multi-tenant chat API |

### **Original Access Points (Still Available):**

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main web interface |
| **Backend API** | http://localhost:8000 | REST API endpoints |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **RASA API** | http://localhost:5005 | RASA NLU/Core API |
| **RASA Actions** | http://localhost:5055 | Custom actions server |
| **Admin Dashboard** | http://localhost:3000/page | System monitoring |

---

## 🧪 **Testing the SaaS Platform**

### **1. Test Client Registration Flow:**
```bash
# 1. Visit client signup
# http://localhost:3000/client-signup

# 2. Register a new automotive business
# Business: "ABC Motors Singapore"
# Domain: "abcmotors.com.sg"
# Email: "admin@abcmotors.com.sg"

# 3. Account will be "pending" status
```

### **2. Test Super Admin Approval:**
```bash
# 1. Visit super admin login
# http://localhost:3000/super-admin-login

# 2. Login with:
# Email: admin@clevercompanion.com
# Password: SuperAdmin123!

# 3. Approve the pending client account
```

### **3. Test Client Dashboard:**
```bash
# 1. Visit client login
# http://localhost:3000/client-login

# 2. Login with approved client credentials

# 3. Configure chatbot:
#    - Branding (logo, colors)
#    - Features (enable/disable)
#    - Contact information
#    - Vehicle inventory

# 4. Get embed code for website
```

### **4. Test Sample Client (Pre-created):**
```bash
# Login with sample client:
# Email: admin@abcmotors.com.sg
# Password: password123

# This client is already approved and configured
```

## 📊 RASA Training Reports & Evaluation

### Available Training Commands

```powershell
# Basic training
npm run rasa:train

# Test existing model with evaluation metrics
npm run rasa:test

# Test NLU with cross-validation
npm run rasa:test-nlu

# Full evaluation with accuracy reports
npm run rasa:evaluate

# Train + Evaluate in one command
npm run rasa:train-evaluate

# Complete report generation
npm run rasa:full-report
```

### What Reports Include

**📈 Accuracy Metrics:**
- Intent classification accuracy
- Entity extraction F1-scores
- Confusion matrices
- Precision/Recall per intent

**📊 Evaluation Files Generated:**
- `backend/results/intent_report.json` - Intent classification metrics
- `backend/results/CRFEntityExtractor_report.json` - Entity extraction metrics
- `backend/results/intent_confusion_matrix.png` - Visual confusion matrix
- `backend/results/intent_histogram.png` - Intent distribution
- `backend/results/story_report.json` - End-to-end story evaluation

**🎯 Cross-Validation Results:**
- 5-fold cross-validation scores
- Average accuracy across folds
- Standard deviation of performance

### Reading Training Reports

```powershell
# View intent classification report
type backend\results\intent_report.json

# View overall metrics summary
type backend\results\story_report.json

# Open confusion matrix image
start backend\results\intent_confusion_matrix.png
```

---

## 🔍 Dependency Verification

### All Backend Dependencies (Python)
✅ **Core RASA Stack:**
- `rasa==3.6.4` - Main RASA framework
- `rasa-sdk==3.6.1` - RASA SDK for custom actions

✅ **Web Framework:**
- `fastapi==0.104.1` - REST API framework
- `uvicorn>=0.23.0,<0.24.0` - ASGI server

✅ **Database Support:**
- `pymongo>=3.12,<4.0` - MongoDB driver
- `motor>=2.5.0,<3.0.0` - Async MongoDB driver
- `SQLAlchemy==1.4.53` - SQL database ORM

✅ **NLP & AI:**
- `transformers>=4.21.0,<4.25.0` - Hugging Face transformers
- `langchain>=0.0.300,<0.0.360` - LangChain framework
- `faiss-cpu>=1.7.4,<1.8.0` - Vector search

✅ **Scientific Computing:**
- `scipy>=1.7.0,<1.12.0` - Scientific computing
- `numpy>=1.19.2,<1.25.0` - Numerical computing
- `pandas>=1.5.0,<2.0.0` - Data manipulation

✅ **Authentication & Security:**
- `python-jose[cryptography]>=3.3.0,<4.0.0` - JWT handling
- `passlib[bcrypt]>=1.7.4,<2.0.0` - Password hashing
- `email-validator>=2.0.0,<3.0.0` - Email validation

✅ **File Processing:**
- `pypdf>=3.15.0,<4.0.0` - PDF processing
- `openpyxl>=3.1.0,<4.0.0` - Excel file handling

### All Frontend Dependencies (Node.js)

✅ **Core React Stack:**
- `react@19.1.0` - React framework
- `react-dom@19.1.0` - React DOM renderer
- `next@15.3.3` - Next.js framework

✅ **UI & Styling:**
- `tailwindcss@3.4.1` - CSS framework
- `@heroicons/react@2.1.1` - Icon library
- `lucide-react@0.514.0` - Additional icons

✅ **State & Form Management:**
- `zustand@4.5.1` - State management
- `react-hook-form@7.50.1` - Form handling

✅ **HTTP & Development:**
- `axios@1.6.7` - HTTP client
- `concurrently@8.2.2` - Run multiple commands
- `typescript@5.8.3` - TypeScript support

---

## 🐛 Troubleshooting

### Port Conflicts
```powershell
# Kill all processes and restart
npm run kill-ports
npm run dev:all
```

### RASA Training Issues
```powershell
# Check RASA installation
.\.venv\Scripts\python.exe -c "import rasa; print(rasa.__version__)"

# Force retrain model
cd backend
..\.venv\Scripts\python.exe -m rasa train --force
```

### Frontend Build Issues
```powershell
# Reinstall frontend dependencies
cd frontend
npm install --force
npm run build
```

### Database Connection (UPDATED)
```powershell
# Test MongoDB Atlas connection
cd backend
python -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    client = AsyncIOMotorClient('mongodb+srv://darknesscrawler:P%40ssw0rd%211@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot')
    await client.admin.command('ping')
    print('✅ MongoDB Atlas connected successfully')

asyncio.run(test())
"
```

---

## 📝 Quick Development Commands

```powershell
# Development workflow
npm run dev:all              # Start all services
npm run rasa:train          # Train RASA model
npm run rasa:full-report    # Generate training report
npm run status              # Check all services

# Testing workflow  
npm run rasa:test           # Test current model
npm run rasa:test-nlu       # Test NLU with cross-validation
npm run rasa:evaluate      # Full evaluation with metrics

# Maintenance
npm run kill-ports          # Clean up processes
npm run clean-start         # Fresh start
```

## 🎯 **SaaS Platform Workflow**

```powershell
# Complete SaaS setup workflow:

# 1. Setup database
cd backend
python setup_mongodb_collections.py

# 2. Train RASA model
npm run rasa:train

# 3. Start all services
npm run dev:all

# 4. Test the platform:
# - Register client: http://localhost:3000/client-signup
# - Approve client: http://localhost:3000/super-admin-login
# - Configure chatbot: http://localhost:3000/client-login
# - Test widget: Get embed code from dashboard
```

---

## 🏗️ BCE Architecture Overview

**Backend (BCE Framework):**
- **Boundaries:** `api/boundaries/` - HTTP request/response handling
- **Controllers:** `api/controllers/` - Business logic orchestration  
- **Entities:** `api/entities/` - Data access and operations
- **External:** `api/external/` - RASA actions and external integrations

**Frontend (API Consumer):**
- **Components:** React components for UI
- **Services:** HTTP API calls to backend
- **Hooks:** Custom React hooks for state management

**SaaS Extensions:**
- **Client Management:** Multi-tenant client handling
- **Authentication:** JWT-based auth for clients and super admin
- **Widget API:** Dynamic widget generation per client
- **Security:** Role-based access control and data isolation

---

## ✅ Success Indicators

**Setup Complete When:**
- ✅ All 5 services start without errors
- ✅ Frontend loads at localhost:3000
- ✅ Backend API responds at localhost:8000/docs
- ✅ RASA API responds at localhost:5005/status
- ✅ RASA actions server running on localhost:5055
- ✅ Training reports generate successfully
- ✅ MongoDB Atlas connection successful
- ✅ SaaS pages load (client-signup, super-admin, etc.)
- ✅ Client registration and approval flow works

**Training Reports Ready When:**
- ✅ `backend/results/` directory contains evaluation files
- ✅ Intent accuracy > 85%
- ✅ Entity F1-score > 80%
- ✅ Cross-validation shows consistent performance

**SaaS Platform Ready When:**
- ✅ Can register new automotive business clients
- ✅ Super admin can approve/manage clients
- ✅ Clients can configure their chatbot branding
- ✅ Multi-tenant widget works with client-specific data
- ✅ Database properly isolates client data

---

## 🚨 Important Notes

1. **Single Requirements File:** Only `backend/requirements.txt` - no separate installers
2. **RASA Mandatory:** RASA 3.6.4 is core requirement - cannot be removed
3. **Python 3.9.13:** Required for RASA compatibility
4. **Clean File Management:** Temporary/debug files are auto-removed
5. **BCE Backend Only:** Frontend uses standard React patterns
6. **MongoDB Atlas:** All client data stored in cloud database
7. **SaaS Ready:** Multi-tenant architecture for multiple automotive businesses
8. **Security:** Role-based access control and data isolation built-in

---

## 🆘 Need Help?

1. **Check logs** in the terminal where services are running
2. **Verify dependencies** using the setup.py diagnostic output
3. **Test individual services** using the npm run commands
4. **Review training reports** for model performance insights
5. **Use clean-start** if processes are stuck
6. **Test SaaS flow** using the client registration and approval process
7. **Check MongoDB Atlas** connection if database issues occur

**Working Configuration Verified:** ✅ RASA 3.6.4 + FastAPI + Next.js + MongoDB 