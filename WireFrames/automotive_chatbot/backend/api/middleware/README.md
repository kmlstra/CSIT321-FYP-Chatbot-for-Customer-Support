# API Middleware Documentation

## 📋 Overview

The `api/middleware/` directory contains middleware components that handle cross-cutting concerns like logging, rate limiting, and conversation tracking. These components intercept requests and responses to provide additional functionality without modifying core business logic.

## 🏗️ Middleware Architecture

Middleware components operate in a pipeline pattern, processing requests before they reach actions and responses before they return to clients. They provide:

- **Request/Response Interception**
- **Automatic Logging and Tracking**
- **Rate Limiting and Throttling**
- **Error Handling and Recovery**
- **Performance Monitoring**

## 📁 File Documentation

### 🔧 Core Files

#### `__init__.py`
**Purpose:** Python package initialization and middleware exports  
**Function:** 
- Makes middleware directory a Python package
- Exports key middleware classes and functions
- Handles import organization

**Exports:**
```python
from .conversation_middleware import ConversationTracker, ConversationAPI
from .auto_logger import AutoLoggedAction, ConversationLogger
from .lta_rate_limiter import LTARateLimiter
```

---

### 🗣️ Conversation Management

#### `conversation_middleware.py`
**Purpose:** Core conversation tracking and session management  
**Function:**
- Tracks user conversations across sessions
- Manages conversation state and history
- Provides conversation retrieval APIs
- Handles session expiry and cleanup

**Key Classes:**

##### `ConversationTracker`
**Responsibilities:**
- Store user messages, bot responses, and action executions
- Manage conversation sessions with 30-minute expiry
- Consolidate messages into single conversation entries
- Handle local timestamp conversion (Singapore timezone)

**Key Methods:**
```python
def store_user_message(sender_id: str, message: str, metadata: dict = None)
def store_bot_response(sender_id: str, response: str, action_name: str = None)
def store_action_execution(sender_id: str, action_name: str, success: bool, error_message: str = None)
```

##### `ConversationAPI`
**Responsibilities:**
- RESTful API endpoints for conversation management
- Conversation history retrieval with pagination
- Session statistics and monitoring
- Cleanup operations for expired sessions

**API Endpoints:**
- `GET /api/conversations/history/{session_id}` - Get conversation history
- `GET /api/conversations/sessions/active` - Active session count
- `POST /api/conversations/cleanup` - Trigger cleanup
- `GET /api/conversations/stats` - Conversation statistics

**Features:**
- **Message Consolidation:** All messages for a conversation_id are appended to a single record
- **Local Timestamps:** Singapore timezone (UTC+8) with ISO format
- **Automatic Expiry:** 30-minute session timeout with automatic cleanup
- **Fallback Mode:** Graceful degradation when MongoDB is unavailable

#### `auto_logger.py`
**Purpose:** Automatic conversation logging for RASA actions  
**Function:**
- Provides base class for auto-logged actions
- Handles automatic conversation tracking
- Manages session initialization and cleanup
- Integrates with conversation storage system

**Key Classes:**

##### `AutoLoggedAction`
**Purpose:** Base class for RASA actions with automatic logging  
**Usage:**
```python
class ActionContactUs(AutoLoggedAction):
    def name(self) -> str:
        return "action_contact_us"
    
    def run(self, dispatcher, tracker, domain):
        # Business logic here
        response = "Contact information..."
        dispatcher.utter_message(text=response)
        return []
```

**Features:**
- Automatic logging of action execution
- Error handling and logging
- Performance tracking
- Integration with conversation middleware

##### `ConversationLogger`
**Purpose:** Manual conversation logging utilities  
**Function:**
- Provides helper functions for manual logging
- Handles custom logging scenarios
- Supports batch logging operations
- Manages log formatting and metadata

**Key Methods:**
```python
def log_user_input(session_id: str, message: str, metadata: dict = None)
def log_bot_response(session_id: str, response: str, action_name: str = None)
def log_action_execution(session_id: str, action_name: str, success: bool = True)
def start_session(sender_id: Optional[str] = None) -> str
```

**Recent Fix:**
- Fixed type annotation: `sender_id: Optional[str] = None` (was causing type errors)
- Improved session ID generation when None is provided
- Enhanced error handling for session management

---

### 🚦 Rate Limiting

#### `lta_rate_limiter.py`
**Purpose:** Rate limiting for Land Transport Authority (LTA) API calls  
**Function:**
- Implements rate limiting for external API calls
- Prevents API quota exhaustion
- Handles retry logic with exponential backoff
- Manages API key rotation and load balancing

**Key Features:**

##### Rate Limiting Strategy
- **Request Throttling:** Limits requests per minute/hour
- **Burst Protection:** Prevents sudden API spikes
- **Queue Management:** Queues requests during high load
- **Circuit Breaker:** Temporarily stops requests on repeated failures

##### Implementation Details
```python
class LTARateLimiter:
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.rpm_limit = requests_per_minute
        self.rph_limit = requests_per_hour
        self.request_queue = []
        self.circuit_breaker = CircuitBreaker()
    
    async def make_request(self, url: str, params: dict = None) -> dict:
        # Rate limiting logic
        # Circuit breaker check
        # Request execution
        # Error handling
```

**Configuration:**
- **Default Limits:** 60 requests/minute, 1000 requests/hour
- **Retry Policy:** 3 attempts with exponential backoff
- **Circuit Breaker:** Opens after 5 consecutive failures
- **Recovery Time:** 5 minutes before retry

**Integration:**
- Used by COE actions for LTA API calls
- Integrated with conversation logging
- Provides metrics for monitoring
- Supports multiple API endpoints

---

## 🔄 Middleware Pipeline

### Request Flow
1. **Rate Limiter:** Check API limits and throttle if needed
2. **Auto Logger:** Initialize session and prepare logging
3. **Conversation Tracker:** Load conversation context
4. **Action Execution:** Run business logic
5. **Response Logging:** Log bot responses and action results
6. **Cleanup:** Update session activity and cleanup expired data

### Error Handling
- **Graceful Degradation:** Continue operation even if middleware fails
- **Fallback Modes:** Alternative behavior when external services are down
- **Error Logging:** Comprehensive error tracking and reporting
- **Recovery Mechanisms:** Automatic retry and recovery strategies

## 🛠️ Configuration

### Environment Variables
```bash
# Conversation Storage
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=automotive_chatbot_saas
SESSION_TIMEOUT_MINUTES=30

# Rate Limiting
LTA_API_KEY=your_lta_api_key
LTA_REQUESTS_PER_MINUTE=60
LTA_REQUESTS_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
CONVERSATION_LOG_ENABLED=true
```

### Middleware Registration
```python
# In main.py or app initialization
from api.middleware import ConversationTracker, LTARateLimiter

# Initialize middleware
conversation_tracker = ConversationTracker()
lta_limiter = LTARateLimiter()

# Register with FastAPI
app.add_middleware(ConversationMiddleware)
app.add_middleware(RateLimitMiddleware)
```

## 📊 Monitoring & Metrics

### Conversation Metrics
- **Active Sessions:** Real-time session count
- **Message Volume:** Messages per hour/day
- **Session Duration:** Average conversation length
- **Response Times:** Action execution performance

### Rate Limiting Metrics
- **API Usage:** Requests per minute/hour
- **Throttling Events:** Rate limit hits
- **Circuit Breaker Status:** API health monitoring
- **Error Rates:** Failed request tracking

### Performance Monitoring
```python
# Example metrics collection
metrics = {
    "active_sessions": conversation_tracker.get_active_session_count(),
    "api_requests_today": lta_limiter.get_daily_request_count(),
    "average_response_time": auto_logger.get_average_response_time(),
    "error_rate": auto_logger.get_error_rate()
}
```

## 🔧 Development Guidelines

### Adding New Middleware

1. **Create Middleware Class:**
```python
class CustomMiddleware:
    def __init__(self, config: dict):
        self.config = config
    
    async def __call__(self, request, call_next):
        # Pre-processing
        response = await call_next(request)
        # Post-processing
        return response
```

2. **Register Middleware:** Add to application startup
3. **Add Configuration:** Include in environment variables
4. **Add Tests:** Verify middleware functionality
5. **Update Documentation:** Document new middleware

### Best Practices

- **Performance:** Keep middleware lightweight and fast
- **Error Handling:** Always provide fallback behavior
- **Logging:** Log important events and errors
- **Configuration:** Make middleware configurable
- **Testing:** Unit test all middleware components

## 🔗 Dependencies

- **FastAPI:** Web framework and middleware support
- **MongoDB:** Conversation storage backend
- **RASA SDK:** Action framework integration
- **asyncio:** Asynchronous operation support
- **pytz:** Timezone handling for local timestamps

---

**Last Updated:** January 2025  
**Maintainer:** CleverCompanion Development Team  
**Version:** 2.0 (with local timestamp support)