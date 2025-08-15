# Conversation Storage System

This document explains the conversation storage system implemented for the CleverCompanion chatbot platform.

## Overview

The conversation storage system captures and stores all chatbot interactions with automatic session management and 30-minute session expiry. It's designed to work with or without MongoDB, providing a fallback mode when the database is unavailable.

## Features

- **Session Management**: Automatic session creation and expiry (30 minutes)
- **Message Storage**: Stores user messages, bot responses, and action executions
- **Fallback Mode**: Works without MongoDB for development/testing
- **API Endpoints**: RESTful API for conversation management
- **Automatic Cleanup**: Expired sessions are automatically cleaned up

## Architecture

### Components

1. **ConversationStorage** (`api/conversation_storage.py`)
   - Core storage engine
   - MongoDB integration with fallback mode
   - Session and message management

2. **ConversationMiddleware** (`api/conversation_middleware.py`)
   - RASA integration layer
   - Automatic conversation tracking
   - Helper functions for actions

3. **API Endpoints** (`api/main.py`)
   - RESTful endpoints for conversation management
   - Statistics and cleanup operations

### Database Schema

#### Sessions Collection (`chat_sessions`)
```json
{
  "session_id": "uuid4-string",
  "user_id": "optional-user-identifier",
  "created_at": "2025-01-30T20:56:16.000Z",
  "last_activity": "2025-01-30T20:56:16.000Z",
  "expires_at": "2025-01-30T21:26:16.000Z",
  "message_count": 5
}
```

#### Conversations Collection (`conversations`)
```json
{
  "session_id": "uuid4-string",
  "message_id": "uuid4-string",
  "timestamp": "2025-01-30T20:56:16.000Z",
  "message_type": "user_message|bot_response|action_execution",
  "content": "Message content",
  "sender": "user|bot|system",
  "metadata": {
    "intent": "ask_contact",
    "entities": [],
    "action_name": "action_contact_us"
  },
  "expires_at": "2025-01-30T21:26:16.000Z"
}
```

## Configuration

### Environment Variables

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=automotive_chatbot_saas
```

### Session Settings

- **Session Timeout**: 30 minutes (configurable)
- **Auto Cleanup**: Expired sessions are automatically removed
- **Fallback Mode**: Enabled when MongoDB is unavailable

## API Endpoints

### Get Conversation History
```http
GET /api/conversations/history/{session_id}?limit=50
```

Returns conversation history for a specific session.

**Response:**
```json
{
  "session_id": "session-uuid",
  "session_info": {
    "created_at": "2025-01-30T20:56:16.000Z",
    "message_count": 5
  },
  "messages": [
    {
      "message_id": "msg-uuid",
      "timestamp": "2025-01-30T20:56:16.000Z",
      "content": "Hello",
      "sender": "user"
    }
  ],
  "message_count": 1
}
```

### Get Active Sessions
```http
GET /api/conversations/sessions/active
```

Returns count of currently active sessions.

### Cleanup Expired Sessions
```http
POST /api/conversations/cleanup
```

Triggers cleanup of expired sessions (runs in background).

### Get Statistics
```http
GET /api/conversations/stats
```

Returns conversation statistics.

## Integration with RASA Actions

### Automatic Logging

All contact actions now automatically log conversations:

```python
from api.conversation_middleware import log_bot_response, log_action_execution

class ActionContactUs(Action):
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        
        # Log action execution
        log_action_execution(sender_id, "action_contact_us", success=True)
        
        # Send response
        dispatcher.utter_message(text=response)
        
        # Log bot response
        log_bot_response(sender_id, "Contact information provided", "action_contact_us")
        
        return []
```

### Helper Functions

- `log_bot_response(sender_id, message, action_name)`: Log bot responses
- `log_action_execution(sender_id, action_name, success, error_message)`: Log action executions
- `ConversationTracker.store_user_message()`: Store user messages

## Fallback Mode

When MongoDB is not available, the system operates in fallback mode:

- Sessions are created but not persisted
- Messages are logged to console but not stored
- API endpoints return empty results
- All functionality continues to work without errors

## Usage Examples

### Starting the System

1. **With MongoDB** (recommended for production):
   ```bash
   # Start MongoDB
   mongod --dbpath /path/to/data
   
   # Start RASA action server
   rasa run actions --actions actions --port 5055
   
   # Start backend API
   uvicorn api.main:app --reload --host localhost --port 8001
   ```

2. **Without MongoDB** (development/testing):
   ```bash
   # Start RASA action server
   rasa run actions --actions actions --port 5055
   
   # Start backend API (will run in fallback mode)
   uvicorn api.main:app --reload --host localhost --port 8001
   ```

### Accessing Conversation Data

```bash
# Get conversation history
curl "http://localhost:8001/api/conversations/history/session-id?limit=10"

# Get active sessions count
curl "http://localhost:8001/api/conversations/sessions/active"

# Get statistics
curl "http://localhost:8001/api/conversations/stats"

# Trigger cleanup
curl -X POST "http://localhost:8001/api/conversations/cleanup"
```

## Monitoring and Maintenance

### Logs

- Conversation events are logged at DEBUG level
- MongoDB connection issues are logged at WARNING level
- Errors are logged at ERROR level

### Performance

- MongoDB indexes are automatically created for optimal performance
- Sessions expire automatically after 30 minutes
- Background cleanup prevents database bloat

### Scaling

- Horizontal scaling: Multiple API instances can share the same MongoDB
- Vertical scaling: MongoDB can be scaled independently
- Caching: Consider adding Redis for high-traffic scenarios

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check if MongoDB is running
   - Verify connection string in .env
   - System will run in fallback mode

2. **Sessions Not Persisting**
   - Check MongoDB connection
   - Verify database permissions
   - Check logs for errors

3. **High Memory Usage**
   - Run cleanup endpoint regularly
   - Consider reducing session timeout
   - Monitor MongoDB storage

### Debug Commands

```bash
# Test MongoDB connection
python -c "from api.conversation_storage import conversation_storage; print('MongoDB:', 'Connected' if conversation_storage.client else 'Fallback mode')"

# Test conversation storage
python -c "from api.conversation_storage import conversation_storage; print('Active sessions:', conversation_storage.get_active_sessions_count())"
```

## Security Considerations

- Session IDs are UUIDs (not predictable)
- Automatic session expiry prevents data accumulation
- No sensitive data is stored in conversations
- MongoDB should be secured in production

## Future Enhancements

- User authentication integration
- Conversation analytics and insights
- Export functionality
- Real-time conversation monitoring
- Integration with external analytics platforms