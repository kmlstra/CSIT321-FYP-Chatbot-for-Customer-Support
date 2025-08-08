# API Actions Documentation

## 📋 Overview

The `api/actions/` directory contains RASA custom actions that handle specific business logic for the CleverCompanion automotive chatbot. These actions are executed when RASA determines that specific intents require custom processing beyond simple text responses.

## 🏗️ Architecture

All actions inherit from RASA's `Action` base class and implement the `run()` method. They integrate with the conversation storage system to automatically log interactions and maintain conversation history.

## 📁 File Documentation

### 🔧 Core Files

#### `__init__.py`
**Purpose:** Python package initialization file  
**Function:** Makes the actions directory a Python package and handles imports  
**Dependencies:** None  
**Usage:** Automatically loaded by Python when importing from this package

#### `rasa_actions.py`
**Purpose:** Main RASA actions registry and action server configuration  
**Function:** 
- Registers all custom actions with RASA
- Configures action server endpoints
- Handles action routing and execution
- Integrates with conversation middleware

**Key Features:**
- Action registration and discovery
- Error handling and logging
- Conversation tracking integration
- Response formatting

**Dependencies:** 
- RASA SDK
- Conversation storage system
- All other action modules

---

### 🚗 Business Logic Actions

#### `coe_actions.py`
**Purpose:** Certificate of Entitlement (COE) price queries and analysis  
**Function:**
- Fetches real-time COE prices from LTA Singapore
- Provides category-wise COE pricing (A, B, C, D, E)
- Calculates historical trends and recommendations
- Formats COE data for user-friendly display

**Key Actions:**
- `ActionCOEPrices` - Get current COE prices
- `ActionCOETrends` - Historical price analysis
- `ActionCOERecommendations` - Buying advice based on trends

**Data Sources:**
- Land Transport Authority (LTA) Singapore API
- Internal COE price database

**Response Format:**
```
📊 Latest COE Prices (Live Data)
🚗 Category A: $101,102 ↔️ No change
🚙 Category B: $119,101 ↘️ $-499
...
```

#### `contact_actions.py`
**Purpose:** Contact information and support channel management  
**Function:**
- Provides contact details for different support types
- Handles contact form submissions
- Routes users to appropriate support channels
- Manages business hours and availability

**Key Actions:**
- `ActionContactUs` - General contact information
- `ActionBusinessHours` - Operating hours display
- `ActionSupportChannels` - Available support options
- `ActionContactForm` - Handle contact form data

**Features:**
- Multi-channel support (WhatsApp, Email, Phone)
- Business hours validation
- Automatic routing based on query type
- Contact form validation and storage

#### `live_support_actions.py`
**Purpose:** Live agent support and escalation handling  
**Function:**
- Connects users with live support agents
- Manages support queue and availability
- Handles escalation from bot to human agents
- Provides real-time support status

**Key Actions:**
- `ActionLiveSupport` - Connect to live agent
- `ActionSupportStatus` - Check agent availability
- `ActionEscalate` - Escalate complex queries
- `ActionSupportQueue` - Queue management

**Integration:**
- WhatsApp Business API
- Support ticket system
- Agent availability tracking
- Queue management system

**Response Features:**
```
🔗 Connect with Live Support
🔴 We're currently offline
💬 Our live agents are ready to help...
**WhatsApp:** https://wa.me/6591234567
⏰ Support Hours: Monday-Friday: 9:00 AM - 7:00 PM
```

#### `default_actions.py`
**Purpose:** Default fallback actions and error handling  
**Function:**
- Handles unrecognized user inputs
- Provides fallback responses
- Manages conversation flow errors
- Implements graceful degradation

**Key Actions:**
- `ActionDefaultFallback` - Handle unrecognized intents
- `ActionRestart` - Restart conversation
- `ActionSessionStart` - Initialize new sessions
- `ActionListen` - Return control to NLU

**Features:**
- Intelligent fallback suggestions
- Context-aware error messages
- Conversation recovery mechanisms
- User guidance for unclear inputs

---

## 🔄 Action Execution Flow

1. **Intent Recognition:** RASA NLU identifies user intent
2. **Action Prediction:** RASA Core predicts next action
3. **Action Execution:** Custom action runs business logic
4. **Response Generation:** Action formats and sends response
5. **Conversation Logging:** Middleware logs interaction
6. **State Update:** Conversation state is updated

## 🛠️ Development Guidelines

### Adding New Actions

1. **Create Action Class:**
```python
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker

class ActionNewFeature(Action):
    def name(self) -> str:
        return "action_new_feature"
    
    def run(self, dispatcher, tracker, domain):
        # Implementation here
        return []
```

2. **Register in Domain:** Add to `domain.yml` actions list
3. **Add Training Data:** Include in stories and rules
4. **Test Action:** Verify functionality and logging

### Best Practices

- **Error Handling:** Always implement try-catch blocks
- **Logging:** Use conversation middleware for automatic logging
- **Response Formatting:** Use consistent emoji and formatting
- **Data Validation:** Validate all external API responses
- **Performance:** Cache frequently accessed data

### Testing Actions

```bash
# Test individual actions
rasa test actions

# Test with conversation flow
rasa test stories

# Interactive testing
rasa interactive
```

## 📊 Monitoring & Analytics

- **Action Success Rate:** Tracked via conversation logs
- **Response Times:** Monitored for performance optimization
- **Error Rates:** Logged for debugging and improvement
- **User Satisfaction:** Tracked through conversation outcomes

## 🔗 Dependencies

- **RASA SDK:** Core action framework
- **Conversation Storage:** Message logging and history
- **External APIs:** LTA, WhatsApp, etc.
- **Database:** MongoDB for data persistence

---

**Last Updated:** January 2025  
**Maintainer:** CleverCompanion Development Team  
**RASA Version:** 3.6