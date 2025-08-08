# 🚗 Automotive Chatbot - User Manual

## 📖 Overview

The Automotive Chatbot is an AI-powered customer service platform designed for car dealerships and automotive businesses. It provides real-time COE pricing, vehicle information, test drive booking, and comprehensive automotive services.

## 🏗️ Architecture

```
automotive_chatbot/
├── backend/
│   ├── api/                    # API Layer (FastAPI)
│   │   ├── main.py            # Main application entry point
│   │   ├── config.py          # Configuration management
│   │   ├── auth.py            # Authentication utilities
│   │   ├── lta_rate_limiter.py# LTA API rate limiting
│   │   └── actions/           # RASA action handlers
│   ├── domain.yml             # RASA conversation domain
│   ├── endpoints.yml          # RASA endpoint configuration
│   ├── config.yml             # RASA model configuration
│   ├── credentials.yml        # RASA channel credentials
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React.js frontend
├── docs/                      # Documentation
└── .env                       # Environment variables (secure)
```

## 🔧 Core Components

### **1. RASA Framework**
- **Purpose**: Natural Language Understanding (NLU) and Dialog Management
- **Files**:
  - `domain.yml` - Defines intents, entities, responses, and actions
  - `config.yml` - Pipeline configuration for NLU and policies
  - `endpoints.yml` - Webhook and action server endpoints
  - `credentials.yml` - Channel configurations (REST, WebSocket)

### **2. FastAPI Backend**
- **Purpose**: RESTful API services and RASA action server
- **Files**:
  - `main.py` - Application entry point, CORS, health checks
  - `config.py` - Settings management with pydantic
  - `auth.py` - JWT authentication and user management
  - `lta_rate_limiter.py` - LTA API abuse prevention

### **3. RASA Action Handlers**
- **Location**: `backend/api/actions/`
- **Purpose**: Handle specific business operations

## 📁 RASA Actions Explained

| **File** | **Purpose** | **Key Functions** |
|----------|-------------|-------------------|
| `coe_actions.py` | COE price queries from LTA API | Real-time pricing, historical data, predictions |
| `vehicle_actions.py` | Vehicle information and search | Specifications, recommendations, inventory |
| `testdrive_actions.py` | Test drive booking | Schedule management, confirmations |
| `loan_actions.py` | Finance calculations | EMI calculator, eligibility checks |
| `maintenance_actions.py` | Service scheduling | Maintenance reminders, booking |
| `contact_actions.py` | Contact information | Business details, locations, support |
| `feedback_actions.py` | Customer feedback | Ratings, reviews, satisfaction surveys |
| `fuel_actions.py` | Fuel-related queries | Efficiency, costs, comparisons |
| `default_actions.py` | Fallback handlers | Default responses, error handling |
| `rasa_actions.py` | RASA integration | Custom action utilities |

## 🔒 Security Features

### **Environment Variables (.env)**
```bash
# LTA API Security
LTA_API_KEY=your-lta-api-key
LTA_RATE_LIMIT_REQUESTS=100
LTA_MIN_REQUEST_INTERVAL=10

# Application Security
SECRET_KEY=jwt-secret-key
DEBUG=false

# Database
MONGODB_URL=mongodb://localhost:27017
```

### **Rate Limiting**
- **Max requests**: 100 per hour to LTA API
- **Min interval**: 10 seconds between requests
- **Caching**: 30-minute cache for COE data
- **Fallback**: Graceful degradation on API limits

## 🚀 Quick Start

### **1. Installation**
```bash
python setup.py
```

### **2. Configuration**
```bash
cp env_template_secure.txt .env
# Edit .env with your API keys
```

### **3. Run Services**
```bash
# Start RASA
rasa run --enable-api --cors "*"

# Start Action Server  
rasa run actions

# Start FastAPI
python backend/api/main.py
```

### **4. Access Points**
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **RASA API**: http://localhost:5005
- **Frontend**: http://localhost:3000

## 📊 Monitoring & Analytics

### **API Usage Tracking**
```python
from backend.api.lta_rate_limiter import lta_rate_limiter
print(f"Current usage: {len(lta_rate_limiter.request_history)} requests/hour")
```

### **Health Monitoring**
- GET `/health` - System status
- GET `/api/analytics` - Usage statistics
- Logs in console for debugging

## 🛠️ Development Guide

### **Adding New Actions**
1. Create new file in `backend/api/actions/`
2. Import in `domain.yml` actions list
3. Add corresponding stories in RASA
4. Test with `rasa shell`

### **Modifying API Endpoints**
1. Edit `backend/api/main.py`
2. Add new routers as needed
3. Update authentication if required
4. Test with FastAPI docs

### **Environment Setup**
- Python 3.9+ required
- RASA 3.6.4 compatibility
- MongoDB for persistent data
- Redis for caching (optional)

## 🔧 Troubleshooting

### **Common Issues**
1. **Import errors**: Check virtual environment activation
2. **LTA API limits**: Check rate limiter logs
3. **RASA not responding**: Verify action server connection
4. **Authentication errors**: Check JWT secret key

### **Support Contacts**
- **Technical**: Check logs in console
- **API Issues**: Verify `.env` configuration
- **RASA Problems**: Check `domain.yml` syntax

---

*Last updated: December 2024*
*Version: 2.0.0* 