# 🔧 Backend Configuration Files Explained

This document explains what each configuration file in the `backend/` folder does and why it's needed.

## 📁 File Overview

```
backend/
├── config.yml       # Rasa AI model configuration
├── credentials.yml   # Chat platform credentials
├── domain.yml        # Chatbot conversation domain
├── endpoints.yml     # Service endpoint configurations
└── requirements.txt  # Python dependencies
```

## 🤖 config.yml - Rasa AI Model Configuration

**Purpose**: Defines how your AI chatbot learns and processes conversations.

```yaml
# What it contains:
- recipe: default.v1           # Rasa training recipe
- assistant_id: unique-id      # Your chatbot's unique identifier
- language: en                 # Language (English)
- pipeline: null               # NLU (Natural Language Understanding) pipeline
- policies: null               # Conversation management policies
```

**What it does**:
- **NLU Pipeline**: How the bot understands user messages (tokenization, intent classification, entity extraction)
- **Policies**: How the bot decides what to say next in conversations
- **Training Configuration**: Epochs, thresholds, and model parameters

**When you need to modify**:
- Changing AI model performance
- Adding new languages
- Customizing conversation flow logic
- Improving intent recognition accuracy

---

## 🔐 credentials.yml - Chat Platform Credentials

**Purpose**: Stores API keys and credentials for different chat platforms (Facebook, Slack, etc.)

```yaml
# What it contains:
rest:                          # REST API channel (for web integration)
# facebook:                    # Facebook Messenger credentials
# slack:                       # Slack bot credentials  
# socketio:                    # WebSocket credentials
rasa:                         # Rasa Enterprise credentials
  url: "http://localhost:5002/api"
```

**What it does**:
- **Platform Integration**: Connect your bot to different messaging platforms
- **Authentication**: Secure API access to external services
- **Channel Configuration**: How users can interact with your bot

**When you need to modify**:
- Adding Facebook Messenger integration
- Connecting to Slack workspace
- Setting up WhatsApp Business API
- Configuring custom chat widgets

---

## 🎯 domain.yml - Chatbot Conversation Domain

**Purpose**: Defines what your chatbot can understand and say - the "brain" of your bot.

```yaml
# What it contains:
intents:                       # What users can ask about
  - greet                      # "Hello", "Hi there"
  - ask_coe_prices            # "What are COE prices?"
  - ask_vehicle_info          # "Tell me about Toyota Camry"

entities:                      # Important information to extract
  - car_brand                  # Toyota, Honda, BMW
  - car_model                  # Camry, Civic, X5

responses:                     # What the bot can say back
  utter_greet:
  - text: "Hi! I'm your automotive assistant!"
  
  utter_coe_prices:
  - text: "Current COE prices: Category A: $95,000..."

actions:                       # Custom functions the bot can execute
  - action_get_coe_prices      # Fetch real-time COE data
  - action_get_vehicle_info    # Get car specifications
```

**What it does**:
- **Intent Recognition**: Maps user messages to intentions
- **Entity Extraction**: Identifies important information (car brands, models)
- **Response Templates**: Pre-written responses for common queries
- **Custom Actions**: Connects to your backend API for dynamic data

**When you need to modify**:
- Adding new conversation topics
- Creating new response templates
- Adding custom business logic
- Improving conversation flow

---

## 🔗 endpoints.yml - Service Endpoint Configuration

**Purpose**: Tells Rasa where to find other services it needs to work with.

```yaml
# What it contains:
action_endpoint:               # Where custom actions run
  url: "http://localhost:5055/webhook"

# tracker_store:               # Where to save conversation history
#   type: mongod
#   url: mongodb://localhost:27017

# event_broker:                # Where to send conversation events
#   url: localhost
```

**What it does**:
- **Action Server**: Connects to your FastAPI backend for custom actions
- **Tracker Store**: Where conversation history is saved (memory, Redis, MongoDB)
- **Event Broker**: Sends conversation events to analytics systems
- **Model Storage**: Where trained AI models are stored

**When you need to modify**:
- Changing backend API URL
- Setting up MongoDB for conversation storage
- Adding analytics integration
- Configuring model deployment

---

## 🚀 How They Work Together

1. **User sends message** → credentials.yml (platform integration)
2. **Message processed** → config.yml (NLU pipeline)
3. **Intent recognized** → domain.yml (intent matching)
4. **Action decided** → domain.yml (policy decision)
5. **Custom action called** → endpoints.yml (backend connection)
6. **Response generated** → domain.yml (response template)
7. **Reply sent to user** → credentials.yml (platform delivery)

## 🛠️ Quick Configuration Tips

### For Development
```yaml
# config.yml - Fast training
policies:
  - name: TEDPolicy
    epochs: 10  # Reduce for faster training

# endpoints.yml - Local development
action_endpoint:
  url: "http://localhost:8000/api/rasa/webhook"
```

### For Production
```yaml
# credentials.yml - Add your platforms
facebook:
  verify: "your-verify-token"
  secret: "your-app-secret"
  page-access-token: "your-page-token"

# endpoints.yml - Production database
tracker_store:
  type: mongod
  url: "mongodb://your-production-db:27017"
  db: "automotive_chatbot"
```

## 🔍 Common Issues & Solutions

**Issue**: Bot doesn't understand new intents
**Solution**: Add intents to `domain.yml` and retrain with `rasa train`

**Issue**: Custom actions not working
**Solution**: Check `endpoints.yml` action_endpoint URL matches your backend

**Issue**: Conversations not saved
**Solution**: Configure tracker_store in `endpoints.yml`

**Issue**: Platform integration fails
**Solution**: Verify credentials in `credentials.yml`

---

## 📚 Further Reading

- [Rasa Domain Documentation](https://rasa.com/docs/rasa/domain)
- [Rasa Configuration Guide](https://rasa.com/docs/rasa/model-configuration)
- [Custom Actions Tutorial](https://rasa.com/docs/rasa/custom-actions)
- [Platform Integration Guide](https://rasa.com/docs/rasa/messaging-and-voice-channels)

**💡 Pro Tip**: Start with the default configurations and modify incrementally. Always backup your working configs before making changes! 