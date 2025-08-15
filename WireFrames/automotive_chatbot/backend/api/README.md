# API Root Directory Documentation

## 📋 Overview

The `api/` directory contains the core FastAPI application and main API endpoints for the CleverCompanion automotive chatbot platform. This directory serves as the entry point for all HTTP requests and orchestrates the various services, middleware, and business logic components.

## 🏗️ API Architecture

The API follows a layered architecture pattern:

- **Presentation Layer:** FastAPI routes and endpoints (`main.py`, `rasa_proxy.py`)
- **Security Layer:** Authentication and authorization (`auth.py`)
- **Configuration Layer:** Application settings and environment management (`config.py`)
- **Business Logic Layer:** Services and middleware (subdirectories)
- **Data Layer:** Database and external API integrations

## 📁 Root Files Documentation

### 🔧 Core Application Files

#### `__init__.py`
**Purpose:** Python package initialization for the API module  
**Function:** 
- Makes the api directory a Python package
- Handles package-level imports and exports
- Provides convenient access to main API components

**Usage:**
```python
from api import app  # FastAPI application instance
from api.config import settings  # Configuration settings
```

---

#### `main.py`
**Purpose:** Main FastAPI application entry point and route configuration  
**Function:**
- Initializes the FastAPI application with middleware
- Configures CORS, static file serving, and lifespan management
- Defines core API endpoints and health checks
- Orchestrates router inclusion and API composition

**Key Features:**

##### FastAPI Application Setup
```python
app = FastAPI(
    title="Automotive Chatbot Platform",
    description="Advanced AI-powered automotive assistant with RAG capabilities",
    version="2.0.0",
    lifespan=lifespan
)
```

##### Core Endpoints
- **`GET /`** - API welcome and feature overview
- **`GET /health`** - System health check and service status
- **`GET /docs`** - Interactive API documentation (Swagger UI)
- **`GET /redoc`** - Alternative API documentation (ReDoc)

##### Middleware Configuration
- **CORS Middleware:** Cross-origin request handling
- **Static Files:** Serves static assets from `/static` path
- **Conversation Middleware:** Automatic conversation tracking

##### Router Integration
```python
# Conversation management
app.include_router(conversation_router, prefix="/api/conversations")

# RASA proxy for chat functionality
app.include_router(rasa_proxy_router, prefix="/api/rasa")

# Vehicle and COE services (fallback implementations)
app.include_router(vehicle_router, prefix="/api/vehicles")
app.include_router(coe_router, prefix="/api/coe")
```

##### Health Check Response
```json
{
    "status": "healthy",
    "version": "2.0.0",
    "services": {
        "api": "running",
        "information_service": "available",
        "coe_service": "available",
        "rag_service": "available"
    }
}
```

##### Conversation API Endpoints
- **`GET /api/conversations/history/{session_id}`** - Retrieve conversation history
- **`GET /api/conversations/sessions/active`** - Get active session count
- **`POST /api/conversations/cleanup`** - Trigger expired session cleanup
- **`GET /api/conversations/stats`** - Conversation statistics

---

#### `config.py`
**Purpose:** Application configuration and environment variable management  
**Function:**
- Defines configuration schema using Pydantic BaseSettings
- Manages environment variables with type validation
- Provides default values and configuration validation
- Centralizes all application settings

**Configuration Categories:**

##### API Settings
```python
API_HOST: str = "0.0.0.0"  # Server host
API_PORT: int = 8000       # Server port
DEBUG: bool = True         # Debug mode
```

##### Security Configuration
```python
SECRET_KEY: str = "development-secret-key-change-in-production"
ALGORITHM: str = "HS256"   # JWT algorithm
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Token expiry
```

##### Database Settings
```python
MONGODB_URL: str = "mongodb://localhost:27017"
MONGODB_DB: str = "automotive_chatbot_saas"
```

##### RASA Integration
```python
RASA_HOST: str = "localhost"
RASA_PORT: int = 5005
RASA_TOKEN: Optional[str] = None  # RASA authentication token
```

##### External API Configuration
```python
# COE Data API (data.gov.sg)
COE_DATASET_ID: str = "d_69b3380ad7e51aff3a7dcc84eba52b8a1"
COE_API_URL: str = "https://data.gov.sg/api/action/datastore_search"

# LTA DataMall API (legacy)
LTA_API_KEY: str = "MISSING_LTA_API_KEY"
LTA_BASE_URL: str = "https://datamall2.mytransport.sg/ltaodataservice/"
```

##### Rate Limiting
```python
LTA_RATE_LIMIT_REQUESTS: int = 100  # Max requests per hour
LTA_RATE_LIMIT_WINDOW: int = 3600   # 1 hour window
LTA_MIN_REQUEST_INTERVAL: int = 10  # Min seconds between requests
CACHE_EXPIRY_MINUTES: int = 30      # Cache duration
```

##### Environment File Loading
```python
class Config:
    env_file = "backend/.env"  # Environment file location
    case_sensitive = True      # Case-sensitive variable names
    extra = "allow"           # Allow extra variables
```

**Usage:**
```python
from api.config import settings

# Access configuration values
db_url = settings.MONGODB_URL
api_key = settings.LTA_API_KEY
debug_mode = settings.DEBUG
```

---

#### `auth.py`
**Purpose:** Authentication and authorization utilities  
**Function:**
- Provides authentication middleware and dependencies
- Handles JWT token validation and user management
- Implements role-based access control
- Supports both development and production authentication modes

**Key Components:**

##### Security Scheme
```python
security = HTTPBearer(auto_error=False)  # Bearer token authentication
```

##### User Authentication
```python
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user with JWT validation."""
```

##### Development Mock User
```python
MOCK_USER = {
    "id": "dev_user_123",
    "email": "developer@automotive-chatbot.com",
    "name": "Development User",
    "role": "admin",
    "created_at": datetime.utcnow().isoformat()
}
```

##### Optional Authentication
```python
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get user if authenticated, otherwise return None."""
```

##### Role-Based Access Control
```python
async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require admin role for protected endpoints."""
```

**Authentication Modes:**

##### Development Mode
- Returns mock user for all requests
- No token validation required
- Enabled when `DEBUG=true`

##### Production Mode
- Validates JWT tokens
- Requires proper authentication headers
- Implements role-based access control

**Usage in Endpoints:**
```python
# Protected endpoint requiring authentication
@app.get("/api/admin/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    return {"users": [], "current_user": current_user}

# Admin-only endpoint
@app.post("/api/admin/settings")
async def update_settings(admin_user: dict = Depends(require_admin)):
    return {"message": "Settings updated", "admin": admin_user}

# Optional authentication
@app.get("/api/public/info")
async def get_info(user: Optional[dict] = Depends(get_optional_user)):
    return {"info": "public data", "personalized": user is not None}
```

---

#### `rasa_proxy.py`
**Purpose:** RASA integration proxy and conversation data capture  
**Function:**
- Acts as middleware between frontend and RASA service
- Captures and logs all conversation interactions
- Handles RASA service communication and error handling
- Provides RASA health monitoring and status checks

**Key Features:**

##### Chat Proxy Endpoint
```python
@router.post("/chat")
async def chat_with_rasa(chat_request: ChatMessage):
    """Proxy chat requests to RASA and capture conversation data."""
```

**Request Flow:**
1. **Receive Chat Request:** Frontend sends user message
2. **Store User Message:** Log to conversation storage
3. **Forward to RASA:** Send request to RASA NLU/Core
4. **Process RASA Response:** Handle bot responses and actions
5. **Store Bot Response:** Log bot messages to storage
6. **Return Response:** Send formatted response to frontend

##### RASA Service Integration
```python
# Forward request to RASA
rasa_payload = {
    "sender": sender_id,
    "message": user_message
}

response = await client.post(
    "http://localhost:5005/webhooks/rest/webhook",
    json=rasa_payload,
    timeout=30.0
)
```

##### Conversation Logging
```python
# Store user message
conversation_storage.store_message(
    session_id=sender_id,
    message_type='user_message',
    content=user_message,
    sender='user',
    metadata={
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'api_proxy',
        **chat_request.metadata
    }
)

# Store bot responses
for bot_response in rasa_responses:
    conversation_storage.store_message(
        session_id=sender_id,
        message_type='bot_response',
        content=bot_text,
        sender='bot',
        metadata={
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'api_proxy',
            'response_data': bot_response
        }
    )
```

##### Error Handling
```python
try:
    response = await client.post(rasa_url, json=payload)
    response.raise_for_status()
except httpx.RequestError as e:
    logger.error(f"Error connecting to RASA: {e}")
    raise HTTPException(status_code=503, detail="RASA service unavailable")
except httpx.HTTPStatusError as e:
    logger.error(f"RASA returned error: {e}")
    raise HTTPException(status_code=502, detail="RASA service error")
```

##### RASA Status Monitoring
```python
@router.get("/status")
async def rasa_status():
    """Check RASA service status and availability."""
    try:
        response = await client.get("http://localhost:5005/status")
        return {
            "rasa_status": "available",
            "rasa_response": response.json()
        }
    except Exception as e:
        return {
            "rasa_status": "unavailable",
            "error": str(e)
        }
```

**Response Format:**
```json
{
    "success": true,
    "sender": "user_123",
    "user_message": "What are the current COE prices?",
    "bot_responses": [
        "📊 Latest COE Prices (Live Data)\n🚗 Category A: $101,102..."
    ],
    "raw_rasa_response": [
        {
            "text": "📊 Latest COE Prices...",
            "recipient_id": "user_123"
        }
    ]
}
```

---

## 🔄 API Request Flow

### Typical Request Processing
1. **Request Reception:** FastAPI receives HTTP request
2. **CORS Processing:** CORS middleware validates origin
3. **Authentication:** Auth middleware validates user (if required)
4. **Route Matching:** FastAPI routes request to appropriate handler
5. **Business Logic:** Handler executes business logic via services
6. **Data Processing:** Services interact with database/external APIs
7. **Response Formation:** Handler formats response data
8. **Middleware Processing:** Response middleware processes output
9. **Response Delivery:** FastAPI sends response to client

### Error Handling Flow
1. **Exception Capture:** Try-catch blocks capture errors
2. **Error Logging:** Errors logged with context information
3. **Error Classification:** Determine error type and severity
4. **Response Formation:** Create appropriate HTTP error response
5. **Client Notification:** Send error response with helpful message

## 📊 API Monitoring & Metrics

### Health Check Endpoints
```python
# System health
GET /health
{
    "status": "healthy",
    "version": "2.0.0",
    "services": {
        "api": "running",
        "rasa": "available",
        "mongodb": "connected",
        "external_apis": "available"
    }
}

# RASA service health
GET /api/rasa/status
{
    "rasa_status": "available",
    "response_time_ms": 45,
    "model_loaded": true
}
```

### Performance Metrics
- **Request Rate:** Requests per second/minute
- **Response Time:** Average and percentile response times
- **Error Rate:** Percentage of failed requests
- **Service Availability:** Uptime percentage
- **Resource Usage:** CPU, memory, and disk utilization

## 🛠️ Development Guidelines

### Adding New Endpoints

1. **Create Router:**
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/new-feature", tags=["new-feature"])

@router.get("/")
async def get_feature_data():
    return {"data": "feature data"}
```

2. **Include in Main App:**
```python
# In main.py
from .new_feature import router as new_feature_router
app.include_router(new_feature_router)
```

3. **Add Authentication (if needed):**
```python
@router.get("/protected")
async def protected_endpoint(user: dict = Depends(get_current_user)):
    return {"user": user, "data": "protected data"}
```

### Configuration Management

1. **Add to Settings:**
```python
# In config.py
class Settings(BaseSettings):
    NEW_FEATURE_ENABLED: bool = False
    NEW_FEATURE_API_KEY: Optional[str] = None
```

2. **Use in Code:**
```python
from .config import settings

if settings.NEW_FEATURE_ENABLED:
    # Feature implementation
    pass
```

### Error Handling Best Practices

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@router.get("/example")
async def example_endpoint():
    try:
        # Business logic here
        result = await some_service_call()
        return result
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

## 🔗 Dependencies

### Core Dependencies
- **FastAPI:** Web framework and API development
- **Uvicorn:** ASGI server for running the application
- **Pydantic:** Data validation and settings management
- **python-dotenv:** Environment variable loading

### Integration Dependencies
- **httpx:** HTTP client for external API calls
- **python-jose:** JWT token handling
- **passlib:** Password hashing and verification
- **pymongo:** MongoDB database integration

### Development Dependencies
- **pytest:** Testing framework
- **pytest-asyncio:** Async testing support
- **black:** Code formatting
- **flake8:** Code linting

## 🚀 Deployment

### Development Server
```bash
# Start development server
uvicorn api.main:app --reload --host localhost --port 8001

# With environment variables
DEBUG=true uvicorn api.main:app --reload
```

### Production Deployment
```bash
# Production server with Gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001

# Docker deployment
docker run -p 8001:8001 -e DEBUG=false automotive-chatbot-api
```

---

**Last Updated:** January 2025  
**Maintainer:** CleverCompanion Development Team  
**API Version:** 2.0.0 (with conversation storage and RASA proxy)