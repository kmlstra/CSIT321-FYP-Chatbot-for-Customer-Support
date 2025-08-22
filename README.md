# CSIT321 FYP - Chatbot for Customer Support

## 🚀 Project Overview
This is a Final Year Project for an Automotive Chatbot Platform with customer support capabilities.

**Focus:** Primary development work is in the `WireFrames/automotive_chatbot-main/` directory.

## 🛠️ Development Environment Setup

### Prerequisites
- Python 3.9+ installed
- PyCharm IDE
- Git
- Node.js (for frontend)
- MongoDB (for database)

### 🐍 Python Environment Setup

#### 1. Virtual Environment
The project uses a virtual environment located at `WireFrames/automotive_chatbot-main/.venv/` with Python 3.9+.

#### 2. PyCharm Configuration
To fix the "invalid Python interpreter" issue in PyCharm:

1. **Open PyCharm Settings:**
   - Press `Ctrl + Alt + S` or go to `File > Settings`

2. **Configure Python Interpreter:**
   - Navigate to: `Project > Python Interpreter`
   - Click the gear icon ⚙️ next to the Python Interpreter dropdown
   - Select "Add..." → "Existing Environment"
   - Set interpreter path to:
     ```
     C:\CSIT321-FYP-Chatbot-for-Customer-Support\WireFrames\automotive_chatbot-main\.venv\Scripts\python.exe
     ```
   - Click "OK"

#### 3. Quick Setup (Recommended)
```powershell
# Navigate to main project folder
cd "WireFrames\automotive_chatbot-main"

# Run automated setup using virtual environment
.\.venv\Scripts\python.exe setup.py
```

#### 4. Manual Setup (If needed)
```powershell
# Navigate to main project folder
cd "WireFrames\automotive_chatbot-main"

# Create virtual environment (if not exists)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install backend dependencies
pip install -r "backend\requirements-compatible.txt"

# Install frontend dependencies (requires Node.js)
npm install
cd frontend
npm install --legacy-peer-deps
```

### 🔧 Quick Commands

#### Check Python Version
```powershell
cd "WireFrames\automotive_chatbot-main"
.\.venv\Scripts\python.exe --version
```

#### Verify Installation
```powershell
cd "WireFrames\automotive_chatbot-main"
.\.venv\Scripts\pip.exe list
```

## 📂 Project Structure
```
CSIT321-FYP-Chatbot-for-Customer-Support/
├── .venv/                          # Root virtual environment (not used)
├── .idea/                          # PyCharm configuration
├── WireFrames/                     # Project wireframes
│   └── automotive_chatbot-main/    # 🎯 MAIN PROJECT FOLDER
│       ├── .venv/                  # Project virtual environment
│       ├── backend/                # Backend API (FastAPI)
│       ├── frontend/               # Frontend (React/Next.js)
│       ├── docs/                   # Documentation
│       ├── setup.py                # Automated setup script
│       └── README.md               # Project-specific README
└── README.md                       # This file
```

## 🚨 Common Issues & Solutions

### Issue 1: Invalid Python Interpreter in PyCharm
- **Problem:** PyCharm shows "invalid python interpreter"
- **Solution:** Use the path: `WireFrames\automotive_chatbot-main\.venv\Scripts\python.exe`

### Issue 2: Setup Script Errors
- **Problem:** `--upgraade` typo or indentation errors
- **Status:** ✅ Fixed in latest version
- **Solution:** Run `.\.venv\Scripts\python.exe setup.py` from `automotive_chatbot-main` folder

### Issue 3: Python Version Mismatch
- **Problem:** PyCharm shows Python 3.12 but `python --version` shows 3.9
- **Solution:** Configure PyCharm to use the virtual environment interpreter

### Issue 4: Unicode Encoding Error (Windows)
- **Problem:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'`
- **Status:** ✅ Fixed in latest version
- **Solution:** Replaced Unicode characters with ASCII-compatible alternatives

### Issue 5: Missing Dependencies
- **Problem:** Import errors when running the application
- **Solution:** Run the setup script or install manually using the commands above

### Issue 6: Python Command Not Found
- **Problem:** `Python was not found` error
- **Solution:** Always use the virtual environment: `.\.venv\Scripts\python.exe`

## 🎯 Development Workflow

1. **Always work in:** `WireFrames/automotive_chatbot-main/`
2. **Set PyCharm working directory to:** `automotive_chatbot-main` folder
3. **Use the virtual environment:** `.venv` inside `automotive_chatbot-main`
4. **Run commands from:** `automotive_chatbot-main` directory
5. **Use virtual environment Python:** `.\.venv\Scripts\python.exe` instead of `python`

## 🔗 Related Documentation
- [Main Project README](WireFrames/automotive_chatbot/README.md)
- [Backend Setup](WireFrames/automotive_chatbot/backend/README.md)
- [MongoDB Setup](WireFrames/automotive_chatbot/docs/MONGODB_SETUP.md)

## 🚀 AWS Deployment Configuration

### Production Deployment Files
The following files have been synchronized from AWS production environment for future deployments:

#### 1. Docker Compose Configuration
- **File:** `docker-compose.production.yml`
- **Purpose:** Complete production deployment configuration including all services
- **Services Included:**
  - Backend API (FastAPI) - Port 8000
  - Rasa Core - Port 5005
  - Rasa Actions - Port 5055
  - Frontend (React) - Port 3000
  - Nginx Reverse Proxy - Port 80

#### 2. Nginx Configuration
- **File:** `nginx_default.conf`
- **Purpose:** Nginx reverse proxy configuration for production
- **Features:**
  - Frontend routing to port 3000
  - API routing to backend port 8000
  - Test client widget routing
  - Proper CORS headers

#### 3. Rasa Endpoints Configuration
- **File:** `endpoints-aws.yml`
- **Purpose:** AWS-specific Rasa endpoints configuration
- **Configuration:** Action endpoint pointing to rasa-actions:5055

### Deployment Commands
```bash
# Build and start all services in production
docker-compose -f docker-compose.production.yml up -d --build

# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f [service_name]
```

### Service Health Checks
- **Backend API:** `http://localhost:8000/health`
- **Rasa Core:** `http://localhost:5005/version`
- **Frontend:** `http://localhost:3000`
- **Test Widget:** `http://localhost/test-client-widget.html`

---
**Last Updated:** January 2025 - Added AWS deployment configuration sync and fixed Unicode encoding issues