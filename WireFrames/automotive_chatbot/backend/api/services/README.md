# API Services Documentation

## 📋 Overview

The `api/services/` directory contains business logic services that handle core functionality for the CleverCompanion automotive chatbot. These services provide reusable business logic that can be consumed by actions, API endpoints, and other components.

## 🏗️ Service Architecture

Services follow a layered architecture pattern:

- **Service Layer:** Business logic and data processing
- **Data Access Layer:** Database and external API interactions
- **Integration Layer:** Third-party service connections
- **Utility Layer:** Helper functions and common operations

## 📁 File Documentation

### 🔧 Core Files

#### `__init__.py`
**Purpose:** Python package initialization and service exports  
**Function:** 
- Makes services directory a Python package
- Exports key service classes and instances
- Handles dependency injection and service registration

**Exports:**
```python
from .conversation_storage import conversation_storage, ConversationStorage
from .coe_auto_updater import COEAutoUpdater, coe_updater
from .notifications import NotificationService, notification_service
```

---

### 💬 Conversation Management

#### `conversation_storage.py`
**Purpose:** Core conversation storage and retrieval service  
**Function:**
- Manages conversation data persistence
- Handles session management and expiry
- Provides conversation history and analytics
- Implements local timestamp support (Singapore timezone)

**Key Features:**

##### ConversationStorage Class
**Responsibilities:**
- Store and retrieve conversation messages
- Manage user sessions with automatic expiry
- Consolidate messages into single conversation entries
- Handle MongoDB integration with fallback mode

**Core Methods:**
```python
def store_message(self, session_id: str, message_type: str, content: str, 
                 sender: str, metadata: dict = None) -> bool
def get_conversation_history(self, session_id: str, limit: int = 50) -> List[dict]
def create_session(self, user_id: str = None) -> str
def cleanup_expired_sessions(self) -> int
def get_active_session_count(self) -> int
```

**Recent Enhancements:**
- **Local Timestamps:** Singapore timezone (UTC+8) with ISO format
- **Message Consolidation:** All messages appended to single conversation record per conversation_id
- **Improved Formatting:** Proper line breaks and message structure
- **Timezone Conversion:** Automatic conversion to local time for retrieval

**Database Schema:**
```python
# Sessions Collection
{
    "session_id": "uuid4-string",
    "user_id": "optional-user-identifier", 
    "created_at": "2025-01-30T20:56:16+08:00",
    "last_activity": "2025-01-30T20:56:16+08:00",
    "expires_at": "2025-01-30T21:26:16+08:00",
    "message_count": 5
}

# Conversations Collection (Consolidated)
{
    "conversation_id": "uuid4-string",
    "session_id": "uuid4-string",
    "timestamp": "2025-01-30T20:56:16+08:00",
    "content": "User: Hello\nSystem: Action executed: action_greet\nBot: Hello! How can I help you today?",
    "message_count": 3,
    "last_updated": "2025-01-30T20:56:16+08:00"
}
```

**Configuration:**
```python
# Environment Variables
MONGODB_URL = "mongodb://localhost:27017"
MONGODB_DB = "automotive_chatbot_saas"
SESSION_TIMEOUT_MINUTES = 30
TIMEZONE = "Asia/Singapore"
```

**Fallback Mode:**
- Graceful operation when MongoDB is unavailable
- In-memory session tracking for development
- Console logging for debugging
- No data persistence in fallback mode

---

### 📊 COE Data Management

#### `coe_auto_updater.py`
**Purpose:** Automated COE price monitoring and updates  
**Function:**
- Fetches real-time COE prices from LTA Singapore
- Monitors price changes and trends
- Provides automated notifications for significant changes
- Maintains historical COE data for analysis

**Key Features:**

##### COEAutoUpdater Class
**Responsibilities:**
- Schedule automatic COE price updates
- Fetch data from LTA API with rate limiting
- Detect price changes and trends
- Store historical data for analysis
- Trigger notifications for significant changes

**Core Methods:**
```python
def fetch_latest_coe_prices(self) -> dict
def update_coe_database(self) -> bool
def detect_price_changes(self, new_prices: dict, old_prices: dict) -> dict
def schedule_updates(self, interval_minutes: int = 30) -> None
def get_price_trends(self, category: str, days: int = 30) -> dict
```

**Data Structure:**
```python
# COE Price Data
{
    "timestamp": "2025-01-30T20:56:16+08:00",
    "period": "2025-07",
    "bidding_round": 2,
    "categories": {
        "A": {"price": 101102, "change": 0, "trend": "stable"},
        "B": {"price": 119101, "change": -499, "trend": "down"},
        "C": {"price": 68600, "change": 1911, "trend": "up"},
        "D": {"price": 9511, "change": 122, "trend": "up"},
        "E": {"price": 120000, "change": 1500, "trend": "up"}
    },
    "pqp": {
        "A": 101102, "B": 119600, "C": 66689, 
        "D": 9389, "E": 118500
    }
}
```

**Update Schedule:**
- **Frequency:** Every 30 minutes during bidding periods
- **Bidding Days:** 1st and 3rd Wednesday of each month
- **Off-Peak:** Every 2 hours during non-bidding periods
- **Emergency Updates:** Manual trigger for urgent updates

**Integration:**
- **LTA API:** Official data source
- **Rate Limiter:** Prevents API quota exhaustion
- **Notification Service:** Alerts for significant changes
- **Database:** Historical data storage

**Monitoring Features:**
- **Price Alerts:** Notifications for significant changes (>5%)
- **Trend Analysis:** 7-day, 30-day, and 90-day trends
- **Anomaly Detection:** Unusual price movements
- **Health Checks:** Service availability monitoring

---

### 📢 Notification Management

#### `notifications.py`
**Purpose:** Multi-channel notification service  
**Function:**
- Sends notifications across multiple channels
- Manages notification templates and formatting
- Handles delivery tracking and retry logic
- Provides notification history and analytics

**Key Features:**

##### NotificationService Class
**Responsibilities:**
- Send notifications via multiple channels (Email, SMS, WhatsApp, Push)
- Manage notification templates and personalization
- Handle delivery failures and retry logic
- Track notification metrics and engagement

**Core Methods:**
```python
def send_notification(self, recipient: str, message: str, 
                     channel: str = "email", template: str = None) -> bool
def send_bulk_notifications(self, recipients: List[str], message: str, 
                          channel: str = "email") -> dict
def create_template(self, name: str, content: str, variables: List[str]) -> bool
def get_delivery_status(self, notification_id: str) -> dict
def get_notification_history(self, recipient: str, days: int = 30) -> List[dict]
```

**Supported Channels:**

##### Email Notifications
- **SMTP Integration:** Configurable email providers
- **HTML Templates:** Rich formatting with branding
- **Attachment Support:** PDF reports and documents
- **Delivery Tracking:** Open rates and click tracking

##### Email Notifications (Primary)
- **SMTP Integration:** Gmail and other providers
- **HTML Templates:** Rich formatting with appointment details
- **Automated Scheduling:** Confirmations, reminders, and cancellations
- **Delivery Tracking:** Email delivery status monitoring

##### WhatsApp Business
- **WhatsApp API:** Official business integration
- **Rich Media:** Images, documents, and buttons
- **Template Messages:** Pre-approved message templates
- **Interactive Elements:** Quick replies and buttons

##### Push Notifications
- **Mobile Apps:** iOS and Android support
- **Web Push:** Browser notifications
- **Targeting:** User segmentation and personalization
- **Analytics:** Engagement and conversion tracking

**Notification Types:**

##### COE Price Alerts
```python
# Price Change Alert
{
    "type": "coe_price_alert",
    "category": "B",
    "old_price": 119600,
    "new_price": 119101,
    "change": -499,
    "percentage": -0.42,
    "recommendation": "Good time to buy"
}
```

##### System Notifications
- **Service Status:** Uptime and downtime alerts
- **Maintenance:** Scheduled maintenance notifications
- **Security:** Security alerts and updates
- **Performance:** System performance reports

##### User Engagement
- **Welcome Messages:** New user onboarding
- **Feature Updates:** New feature announcements
- **Tips and Advice:** Automotive tips and recommendations
- **Feedback Requests:** User satisfaction surveys

**Template System:**
```python
# Email Template Example
template = {
    "name": "coe_price_alert",
    "subject": "🚗 COE Price Alert: Category {{category}} {{trend}}",
    "html_content": """
    <h2>COE Price Update</h2>
    <p>Category {{category}} price: <strong>${{new_price}}</strong></p>
    <p>Change: {{change_indicator}} ${{change}} ({{percentage}}%)</p>
    <p>{{recommendation}}</p>
    """,
    "variables": ["category", "new_price", "change", "percentage", "recommendation"]
}
```

**Configuration:**
```python
# Environment Variables
EMAIL_SMTP_HOST = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = "notifications@clevercompanion.sg"
EMAIL_PASSWORD = "app_password"

SMS_PROVIDER = "twilio"
TWILIO_ACCOUNT_SID = "your_account_sid"
TWILIO_AUTH_TOKEN = "your_auth_token"

WHATSAPP_BUSINESS_ID = "your_business_id"
WHATSAPP_ACCESS_TOKEN = "your_access_token"
```

---

## 🔄 Service Integration

### Inter-Service Communication
```python
# Example: COE Update triggering notifications
class COEAutoUpdater:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
    
    def process_price_changes(self, changes: dict):
        for category, change in changes.items():
            if abs(change['percentage']) > 5:  # Significant change
                self.notification_service.send_notification(
                    recipient="subscribers",
                    message=f"COE Category {category} changed by {change['percentage']}%",
                    channel="whatsapp",
                    template="coe_price_alert"
                )
```

### Event-Driven Architecture
- **Event Bus:** Service-to-service communication
- **Async Processing:** Non-blocking operations
- **Error Handling:** Graceful failure recovery
- **Monitoring:** Service health and performance

## 📊 Monitoring & Analytics

### Service Metrics
```python
# Example metrics collection
metrics = {
    "conversation_storage": {
        "active_sessions": conversation_storage.get_active_session_count(),
        "messages_today": conversation_storage.get_daily_message_count(),
        "storage_size": conversation_storage.get_storage_size()
    },
    "coe_updater": {
        "last_update": coe_updater.get_last_update_time(),
        "update_success_rate": coe_updater.get_success_rate(),
        "api_calls_today": coe_updater.get_api_call_count()
    },
    "notifications": {
        "sent_today": notification_service.get_daily_sent_count(),
        "delivery_rate": notification_service.get_delivery_rate(),
        "engagement_rate": notification_service.get_engagement_rate()
    }
}
```

### Health Checks
```python
# Service health monitoring
health_status = {
    "conversation_storage": conversation_storage.health_check(),
    "coe_updater": coe_updater.health_check(),
    "notification_service": notification_service.health_check()
}
```

## 🛠️ Development Guidelines

### Adding New Services

1. **Create Service Class:**
```python
class NewService:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def health_check(self) -> dict:
        return {"status": "healthy", "timestamp": datetime.now()}
```

2. **Add to __init__.py:** Export service for use
3. **Add Configuration:** Include environment variables
4. **Add Tests:** Unit and integration tests
5. **Add Monitoring:** Health checks and metrics
6. **Update Documentation:** Document service functionality

### Best Practices

- **Single Responsibility:** Each service has one clear purpose
- **Dependency Injection:** Services receive dependencies via constructor
- **Error Handling:** Comprehensive error handling and logging
- **Configuration:** Externalized configuration via environment variables
- **Testing:** Unit tests with mocking for external dependencies
- **Monitoring:** Health checks and performance metrics

## 🔗 Dependencies

- **MongoDB:** Primary data storage
- **Redis:** Caching and session storage
- **External APIs:** LTA, WhatsApp, Email providers
- **asyncio:** Asynchronous operation support
- **pytz:** Timezone handling
- **httpx:** HTTP client for external API calls

---

**Last Updated:** January 2025  
**Maintainer:** CleverCompanion Development Team  
**Version:** 2.0 (with local timestamp and message consolidation)