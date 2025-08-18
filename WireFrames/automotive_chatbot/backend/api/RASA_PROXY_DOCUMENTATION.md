# RASA Proxy Documentation

## 📋 Overview

The `rasa_proxy.py` file serves as a **middleware proxy** between the frontend chat interface and the RASA conversational AI service. It acts as an intelligent intermediary that captures, processes, and logs all conversation interactions while providing seamless communication with the RASA NLU/Core engine.

## 🎯 Primary Functions

### 1. **Conversation Proxy & Data Capture**
The proxy intercepts all chat requests and responses, ensuring complete conversation tracking:

```python
@router.post("/chat")
async def chat_with_rasa(chat_request: ChatMessage):
    """Main proxy endpoint that handles all chat interactions"""
```

**What it does:**
- Receives user messages from the frontend
- Forwards messages to RASA service
- Captures RASA responses
- Logs all interactions to conversation storage
- Returns formatted responses to frontend

### 2. **RASA Service Integration**
Manages communication with the RASA conversational AI engine:

```python
# RASA webhook endpoint
rasa_url = f"http://{settings.RASA_HOST}:{settings.RASA_PORT}/webhooks/rest/webhook"

# Payload format for RASA
rasa_payload = {
    "sender": sender_id,
    "message": user_message
}
```

**Integration Features:**
- HTTP client communication with RASA service
- Proper payload formatting for RASA webhooks
- Error handling for RASA service failures
- Timeout management for RASA requests

### 3. **Conversation Storage & Logging**
Automatic capture and storage of all conversation data:

```python
# Store user message using unified conversation service
unified_conversation_service.store_message(
    session_id=sender_id,
    message=user_message,
    message_type=MessageType.USER,
    metadata={
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'api_proxy',
        **chat_request.metadata
    }
)

# Store bot responses using unified conversation service
for bot_response in rasa_responses:
    unified_conversation_service.store_message(
        session_id=sender_id,
        message=bot_text,
        message_type=MessageType.ASSISTANT,
        metadata={
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'api_proxy',
            'response_data': bot_response
        }
    )
```

**Storage Benefits:**
- Complete conversation history tracking
- Session-based message organization
- Metadata capture for analytics
- Audit trail for debugging and improvement

### 4. **Service Health Monitoring**
Provides RASA service status and health checks:

```python
@router.get("/status")
async def rasa_status():
    """Check RASA service availability and health"""
    try:
        response = await client.get(f"http://{settings.RASA_HOST}:{settings.RASA_PORT}/status")
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

## 🔄 Request Flow Diagram

```
Frontend Chat Widget
        ↓
   [User Message]
        ↓
   RASA Proxy (/api/rasa/chat)
        ↓
   [Store User Message]
        ↓
   Forward to RASA Service
        ↓
   [RASA Processing]
        ↓
   Receive RASA Response
        ↓
   [Store Bot Response]
        ↓
   Format & Return Response
        ↓
   Frontend Chat Widget
```

## 📊 Data Flow & Processing

### Input Processing
```python
class ChatMessage(BaseModel):
    message: str                    # User's text message
    sender: str                     # Session/User identifier
    metadata: Optional[Dict] = {}   # Additional context data
```

### RASA Communication
```python
# Request to RASA
{
    "sender": "user_session_123",
    "message": "What are the current COE prices?"
}

# Response from RASA
[
    {
        "text": "📊 Latest COE Prices (Live Data)\n🚗 Category A: $101,102...",
        "recipient_id": "user_session_123"
    }
]
```

### Output Response
```python
{
    "success": true,
    "sender": "user_session_123",
    "user_message": "What are the current COE prices?",
    "bot_responses": [
        "📊 Latest COE Prices (Live Data)\n🚗 Category A: $101,102..."
    ],
    "raw_rasa_response": [
        {
            "text": "📊 Latest COE Prices...",
            "recipient_id": "user_session_123"
        }
    ]
}
```

## 🛡️ Error Handling & Resilience

### RASA Service Errors
```python
try:
    response = await client.post(rasa_url, json=rasa_payload, timeout=30.0)
    response.raise_for_status()
except httpx.RequestError as e:
    logger.error(f"Error connecting to RASA: {e}")
    # Store error in conversation log using unified service
    unified_conversation_service.store_message(
        session_id=sender_id,
        message=f"RASA connection error: {str(e)}",
        message_type=MessageType.ERROR,
        metadata={'source': 'api_proxy'}
    )
    raise HTTPException(status_code=503, detail="RASA service unavailable")
```

### Fallback Responses
```python
# When RASA is unavailable
fallback_response = {
    "success": false,
    "error": "RASA service temporarily unavailable",
    "fallback_message": "I'm sorry, I'm having trouble connecting to my AI brain right now. Please try again in a moment."
}
```

## 🔧 Configuration & Setup

### Environment Variables
```python
# RASA service configuration
RASA_HOST: str = "localhost"        # RASA server host
RASA_PORT: int = 5005               # RASA server port
RASA_TOKEN: Optional[str] = None    # RASA authentication token
```

### RASA Service Requirements
- RASA server running on configured host:port
- REST webhook endpoint available at `/webhooks/rest/webhook`
- Status endpoint available at `/status`
- Proper CORS configuration for API access

## 📈 Analytics & Monitoring

### Conversation Metrics
The proxy automatically captures metrics for:

- **Message Volume:** Total messages per session/day
- **Response Times:** RASA processing duration
- **Error Rates:** Failed RASA requests
- **Session Duration:** Length of conversations
- **Popular Intents:** Most common user requests

### Logging & Debugging
```python
import logging

logger = logging.getLogger(__name__)

# Request logging
logger.info(f"Chat request from {sender_id}: {user_message}")

# Response logging
logger.info(f"RASA response for {sender_id}: {len(rasa_responses)} messages")

# Error logging
logger.error(f"RASA error for {sender_id}: {error_message}", exc_info=True)
```

## 🚀 Performance Optimization

### Async Processing
```python
# Non-blocking RASA communication
async with httpx.AsyncClient() as client:
    response = await client.post(rasa_url, json=payload, timeout=30.0)
```

### Connection Pooling
```python
# Reuse HTTP connections for better performance
client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
    timeout=httpx.Timeout(30.0)
)
```

### Caching Strategy
```python
# Cache frequent responses (if implemented)
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(message_hash: str):
    # Return cached response for identical messages
    pass
```

## 🔗 Integration Points

### Frontend Integration
```javascript
// Frontend chat request
fetch('/api/rasa/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: userMessage,
        sender: sessionId,
        metadata: {
            timestamp: new Date().toISOString(),
            source: 'web_widget'
        }
    })
})
```

### RASA Actions Integration
```python
# RASA custom actions can access conversation history
from api.services.conversation_storage import conversation_storage

class ActionGetHistory(Action):
    def run(self, dispatcher, tracker, domain):
        session_id = tracker.sender_id
        history = conversation_storage.get_conversation_history(session_id)
        # Use history in action logic
```

### Database Integration
```python
# Conversation data stored in MongoDB
{
    "_id": ObjectId("..."),
    "session_id": "user_session_123",
    "message_type": "user_message",
    "content": "What are COE prices?",
    "sender": "user",
    "timestamp": "2025-01-27T10:30:00Z",
    "metadata": {
        "source": "api_proxy",
        "user_agent": "Mozilla/5.0...",
        "ip_address": "192.168.1.100"
    }
}
```

## 🛠️ Development & Testing

### Local Development
```bash
# Start RASA server
rasa run --enable-api --cors "*" --port 5005

# Start API server
uvicorn api.main:app --reload --port 8000

# Test proxy endpoint
curl -X POST "http://localhost:8000/api/rasa/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello", "sender": "test_user"}'
```

### Unit Testing
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_proxy():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/rasa/chat", json={
            "message": "Hello",
            "sender": "test_user"
        })
    assert response.status_code == 200
    assert "bot_responses" in response.json()
```

### Integration Testing
```python
@pytest.mark.asyncio
async def test_rasa_integration():
    # Test with actual RASA service
    response = await chat_with_rasa(ChatMessage(
        message="What are COE prices?",
        sender="integration_test"
    ))
    assert response["success"] is True
    assert len(response["bot_responses"]) > 0
```

## 🔒 Security Considerations

### Input Validation
```python
class ChatMessage(BaseModel):
    message: str = Field(..., max_length=1000)  # Limit message length
    sender: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')  # Validate sender ID
    metadata: Optional[Dict] = Field(default_factory=dict)
```

### Rate Limiting
```python
# Implement rate limiting per session
from slowapi import Limiter

limiter = Limiter(key_func=lambda request: request.json().get("sender", "anonymous"))

@router.post("/chat")
@limiter.limit("10/minute")  # 10 messages per minute per session
async def chat_with_rasa(request: Request, chat_request: ChatMessage):
    # Chat logic here
    pass
```

### Data Privacy
```python
# Sanitize sensitive data before storage
def sanitize_message(message: str) -> str:
    # Remove or mask sensitive information
    import re
    # Remove potential credit card numbers
    message = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD_NUMBER]', message)
    # Remove potential phone numbers
    message = re.sub(r'\b\d{8,}\b', '[PHONE_NUMBER]', message)
    return message
```

## 📋 Maintenance & Troubleshooting

### Common Issues

1. **RASA Service Unavailable**
   - Check RASA server status
   - Verify network connectivity
   - Review RASA logs for errors

2. **Slow Response Times**
   - Monitor RASA processing time
   - Check database connection performance
   - Review conversation storage efficiency

3. **Memory Issues**
   - Implement conversation cleanup
   - Monitor session storage growth
   - Optimize message storage format

### Health Monitoring
```python
# Monitor proxy health
@router.get("/health")
async def proxy_health():
    return {
        "proxy_status": "healthy",
        "rasa_connection": await check_rasa_connection(),
        "storage_connection": await check_storage_connection(),
        "active_sessions": conversation_storage.get_active_session_count()
    }
```

---

## 🎯 Summary

The `rasa_proxy.py` file is a **critical middleware component** that:

1. **Bridges** frontend chat interface with RASA AI service
2. **Captures** all conversation data for analytics and improvement
3. **Handles** errors and provides fallback responses
4. **Monitors** RASA service health and availability
5. **Enables** conversation history and session management
6. **Provides** a unified API interface for chat functionality

This proxy ensures that all chat interactions are properly logged, monitored, and managed while maintaining seamless communication between the user interface and the AI conversational engine.

---

**File Location:** `backend/api/rasa_proxy.py`  
**Last Updated:** January 2025  
**Maintainer:** CleverCompanion Development Team