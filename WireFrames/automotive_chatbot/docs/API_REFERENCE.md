# 🔌 API Reference Guide

## 📋 Overview

This document explains all API files and their functions in the automotive chatbot backend.

## 🏗️ API Structure

```
backend/api/
├── main.py              # FastAPI application & routes
├── config.py            # Configuration management
├── auth.py              # Authentication & authorization
├── lta_rate_limiter.py  # Rate limiting utility
└── actions/             # RASA action handlers
    ├── coe_actions.py   # COE pricing services
    ├── vehicle_actions.py # Vehicle information
    ├── testdrive_actions.py # Test drive booking
    ├── loan_actions.py  # Financial calculations
    └── [other actions]
```

## 📄 Core API Files

### **main.py - Application Entry Point**

**Purpose**: FastAPI application setup, CORS, health monitoring

```python
# Key Endpoints:
GET  /              # Welcome message & features
GET  /health        # System health check
GET  /docs          # API documentation
```

**Key Components**:
- `lifespan()` - MongoDB connection management
- `CORSMiddleware` - Cross-origin request handling
- Router inclusion for modular endpoints

### **config.py - Settings Management**

**Purpose**: Centralized configuration using pydantic

```python
# Key Settings:
- API_HOST, API_PORT     # Server configuration
- SECRET_KEY, ALGORITHM  # JWT security
- MONGODB_URL, MONGODB_DB # Database connection
- LTA_API_KEY, LTA_BASE_URL # LTA integration
- Rate limiting parameters
```

**Security Features**:
- Environment variable loading
- Type validation with pydantic
- Secure defaults for development

### **auth.py - Authentication System**

**Purpose**: JWT-based authentication and user management

```python
# Key Functions:
- get_current_user()     # Extract user from JWT
- get_optional_user()    # Optional authentication
- require_admin()        # Admin-only access
```

**Features**:
- Mock user for development
- JWT token validation
- Role-based access control
- HTTPBearer security scheme

### **lta_rate_limiter.py - API Protection**

**Purpose**: Prevent LTA API abuse and caching

```python
# Key Components:
- LTAAPIRateLimiter       # Rate limiting class
- @rate_limited_lta_request # Decorator for API calls
- Smart caching system    # 30-minute data retention
```

**Protection Features**:
- 100 requests/hour limit
- 10-second minimum intervals
- Automatic cache fallback
- Usage monitoring

## 🎯 Business Logic Actions

### **coe_actions.py - COE Services**

**RASA Actions**:
```python
- ActionCOEPrices         # Current COE pricing
- ActionCOECategoryA/B/C/E # Specific categories
- ActionExplainCOECategories # Category explanations
- ActionCOEPredictionsConfirm # Price predictions
```

**LTA Integration**:
- Real-time COE data from LTA API
- Historical data queries
- Price change calculations
- Fallback pricing when API unavailable

### **vehicle_actions.py - Vehicle Information**

**RASA Actions**:
```python
- ActionGetVehicleInfo    # Vehicle specifications
- ActionBookTestDrive     # Test drive scheduling
- ActionSearchVehicles    # Vehicle search
- ActionRecommendEconomicCars # Budget recommendations
- ActionRecommendFamilyCars   # Family vehicle suggestions
```

**Data Sources**:
- Excel-based vehicle database
- Brand and model extraction
- Price range filtering
- Feature matching

### **testdrive_actions.py - Booking System**

**RASA Actions**:
```python
- ActionBookTestDrive     # Schedule test drives
- ActionConfirmTestDrive  # Booking confirmations
- ActionCancelTestDrive   # Cancellation handling
```

**Features**:
- Date/time validation
- Customer information capture
- Confirmation emails
- Calendar integration

### **loan_actions.py - Financial Services**

**RASA Actions**:
```python
- ActionCalculateLoan     # EMI calculations
- ActionLoanEligibility   # Eligibility checks
- ActionLoanAdvice        # Financial guidance
```

**Calculations**:
- Monthly payment estimation
- Interest rate scenarios
- Down payment options
- Affordability assessment

### **maintenance_actions.py - Service Management**

**RASA Actions**:
```python
- ActionScheduleMaintenance # Service booking
- ActionMaintenanceReminder # Scheduled reminders
- ActionMaintenanceHistory  # Service records
```

**Service Types**:
- Regular maintenance
- Emergency repairs
- Warranty services
- Parts replacement

### **contact_actions.py - Business Information**

**RASA Actions**:
```python
- ActionProvideContact    # Contact information
- ActionBusinessHours     # Operating hours
- ActionLocationInfo      # Branch locations
```

**Information Provided**:
- Phone numbers, emails
- Physical addresses
- Google Maps integration
- WhatsApp contact

### **feedback_actions.py - Customer Experience**

**RASA Actions**:
```python
- ActionFeedbackRequest   # Collect feedback
- ActionRating           # Rating collection
- ActionComplaintHandling # Issue resolution
```

**Feedback Types**:
- Service ratings (1-5 stars)
- Written feedback
- Complaint categorization
- Follow-up scheduling

## 🔒 Security Implementation

### **Rate Limiting**
```python
@rate_limited_lta_request(cache_key="coe_prices", cache_minutes=30)
def get_live_coe_prices():
    # Protected LTA API call
```

### **Authentication**
```python
@app.get("/admin/analytics")
async def get_analytics(user: dict = Depends(require_admin)):
    # Admin-only endpoint
```

### **Environment Security**
```python
# All sensitive data in .env file
LTA_API_KEY = settings.LTA_API_KEY  # From environment
SECRET_KEY = settings.SECRET_KEY    # JWT secret
```

## 🚀 Usage Examples

### **Making Authenticated Requests**
```python
headers = {"Authorization": "Bearer <jwt_token>"}
response = requests.get("/api/admin/users", headers=headers)
```

### **Rate-Limited API Calls**
```python
# Automatically cached for 30 minutes
coe_data = get_live_coe_prices()
```

### **Error Handling**
```python
try:
    result = api_call()
except RateLimitExceeded:
    return cached_data
except APIError:
    send_admin_notification()
```

## 📊 Monitoring

### **Health Check Response**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "services": {
    "api": "running",
    "mongodb": "connected",
    "coe_service": "available",
    "rag_service": "available"
  }
}
```

### **Rate Limit Monitoring**
```python
# Check current usage
usage = len(lta_rate_limiter.request_history)
print(f"API calls in last hour: {usage}/100")
```

---

*For detailed implementation examples, see the source code in each respective file.* 