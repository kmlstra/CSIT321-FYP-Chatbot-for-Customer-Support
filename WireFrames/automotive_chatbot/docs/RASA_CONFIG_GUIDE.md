# 🤖 RASA Configuration Guide

## 📖 Overview

This guide explains all RASA configuration files (`.yml`) and their roles in the automotive chatbot.

## 📁 RASA File Structure

```
backend/
├── domain.yml          # Conversation domain definition
├── config.yml          # NLU pipeline & policies
├── endpoints.yml       # Action server & webhook endpoints  
├── credentials.yml     # Channel configurations
├── data/               # Training data (if needed)
│   ├── nlu.yml        # NLU training examples
│   ├── stories.yml    # Conversation stories
│   └── rules.yml      # Conversation rules
└── models/             # Trained RASA models
```

## 🎯 Core Configuration Files

### **domain.yml - Conversation Domain**

**Purpose**: Defines the complete conversation scope and capabilities

```yaml
# Key Sections:
version: "3.1"
intents:           # What users can say
entities:          # Information to extract
slots:             # Memory/context storage
responses:         # Bot template responses
actions:           # Custom business logic
forms:             # Data collection workflows
session_config:    # Conversation session settings
```

**Example Structure**:
```yaml
intents:
  - ask_coe_prices     # User wants COE information
  - book_test_drive    # User wants to schedule test drive
  - ask_vehicle_info   # User asks about vehicle specs

entities:
  - vehicle_brand      # Extract car brands (Toyota, BMW)
  - coe_category      # Extract COE categories (A, B, C, E)
  - date_time         # Extract dates/times for booking

slots:
  customer_name:      # Store customer information
    type: text
  preferred_vehicle:  # Remember user preferences
    type: text

actions:
  - action_coe_prices        # Get real-time COE data
  - action_book_test_drive   # Handle test drive booking
  - action_get_vehicle_info  # Provide vehicle information
```

### **config.yml - NLU Pipeline & Policies**

**Purpose**: Configures how RASA processes language and manages conversations

```yaml
# Key Components:
version: "3.1"
recipe: default.v1        # Training recipe
language: en             # Language model
pipeline:               # NLU processing steps
policies:               # Conversation management
```

**Pipeline Explanation**:
```yaml
pipeline:
  - name: WhitespaceTokenizer    # Split text into words
  - name: RegexFeaturizer       # Extract pattern features  
  - name: LexicalSyntacticFeaturizer  # Language features
  - name: CountVectorsFeaturizer     # Word frequency features
  - name: DIETClassifier            # Intent classification
  - name: EntitySynonymMapper       # Handle entity synonyms
  - name: ResponseSelector          # Select appropriate responses
```

**Policies Explanation**:
```yaml
policies:
  - name: MemoizationPolicy     # Remember exact conversation patterns
  - name: RulePolicy           # Follow defined rules strictly
  - name: UnexpecTEDIntentPolicy  # Handle unexpected intents
  - name: TEDPolicy            # Transformer-based dialog management
```

### **endpoints.yml - Service Connections**

**Purpose**: Defines external service endpoints and webhooks

```yaml
# Key Endpoints:
action_endpoint:        # Custom action server
  url: "http://localhost:5055/webhook"

# Optional endpoints:
tracker_store:          # Conversation storage
event_broker:          # Event streaming
model_server:          # Model serving
lock_store:            # Conversation locking
```

**Action Server Configuration**:
```yaml
action_endpoint:
  url: "http://localhost:5055/webhook"  # Local action server
  # OR for production:
  # url: "https://your-domain.com/webhook"
  # token: "your-security-token"
```

### **credentials.yml - Channel Configuration**

**Purpose**: Configures communication channels (REST, WebSocket, etc.)

```yaml
# Key Channels:
rest:                   # REST API channel
  # Default settings

socketio:              # WebSocket for real-time chat
  user_message_evt: user_uttered
  bot_message_evt: bot_uttered

# Optional channels:
slack:                 # Slack integration
telegram:              # Telegram bot
facebook:              # Facebook Messenger
```

**REST API Channel**:
```yaml
rest:
  # No additional configuration needed
  # Accessible at: http://localhost:5005/webhooks/rest/webhook
```

## 📊 Training Data Files

### **nlu.yml - NLU Training Examples**

**Purpose**: Train the NLU model to understand user inputs

```yaml
# Structure:
version: "3.1"
nlu:
  - intent: ask_coe_prices
    examples: |
      - What are the current COE prices?
      - COE prices today
      - How much is COE category A?
      - Tell me COE pricing

  - intent: book_test_drive
    examples: |
      - I want to book a test drive
      - Schedule test drive for BMW X5
      - Can I test the Toyota Camry?
```

### **stories.yml - Conversation Stories**

**Purpose**: Define conversation flows and patterns

```yaml
# Example Story:
stories:
  - story: COE price inquiry
    steps:
      - intent: greet
      - action: utter_greet
      - intent: ask_coe_prices
      - action: action_coe_prices      # Custom action
      - intent: thank
      - action: utter_goodbye
```

### **rules.yml - Conversation Rules**

**Purpose**: Define strict conversation rules that must always be followed

```yaml
# Example Rules:
rules:
  - rule: Say goodbye anytime user says goodbye
    steps:
    - intent: goodbye
    - action: utter_goodbye

  - rule: Activate loan calculator form
    steps:
    - intent: ask_loan_calculation
    - action: loan_calculator_form
    - active_loop: loan_calculator_form
```

## 🔧 Advanced Configuration

### **Session Management**
```yaml
# In domain.yml
session_config:
  session_expiration_time: 60    # Minutes before session expires
  carry_over_slots_to_new_session: true  # Maintain context
```

### **Custom Actions Integration**
```yaml
# In domain.yml
actions:
  - action_coe_prices           # Real-time COE data
  - action_book_test_drive      # Test drive booking
  - action_calculate_loan       # Loan calculations
  - action_get_vehicle_info     # Vehicle information
  - action_schedule_maintenance # Service booking
```

### **Entity Extraction**
```yaml
# In domain.yml
entities:
  - vehicle_brand:             # Car manufacturers
      influence_conversation: true
  - coe_category:             # COE categories (A,B,C,E)
      influence_conversation: true
  - PERSON:                   # Customer names
      influence_conversation: false
```

## 🚀 Development Workflow

### **1. Training Process**
```bash
# Train new model
rasa train

# Train only NLU
rasa train nlu

# Train only Core (stories/rules)
rasa train core
```

### **2. Testing**
```bash
# Interactive testing
rasa shell

# Test NLU specifically
rasa shell nlu

# Test with action server
rasa shell --endpoints endpoints.yml
```

### **3. Validation**
```bash
# Validate configuration
rasa data validate

# Check for inconsistencies
rasa data validate stories
```

## 🔍 Troubleshooting

### **Common Configuration Issues**

| **Issue** | **File** | **Solution** |
|-----------|----------|--------------|
| Actions not found | `domain.yml` | Add action to actions list |
| NLU accuracy low | `nlu.yml` | Add more training examples |
| Unexpected responses | `stories.yml` | Add conversation stories |
| Connection errors | `endpoints.yml` | Check action server URL |

### **Validation Commands**
```bash
# Check domain file
rasa data validate domain

# Check stories consistency  
rasa data validate stories

# Check NLU training data
rasa data validate nlu
```

## 📈 Performance Optimization

### **NLU Pipeline Tuning**
- Adjust `CountVectorsFeaturizer` parameters
- Fine-tune `DIETClassifier` epochs
- Add `RegexFeaturizer` for patterns

### **Policy Configuration**
- Increase `TEDPolicy` max_history for complex conversations
- Use `AugmentedMemoizationPolicy` for better memorization
- Configure `FallbackPolicy` for unknown inputs

### **Memory Management**
- Set appropriate session expiration
- Limit slot carryover for performance
- Use efficient entity extraction

---

*For specific configuration examples, refer to the actual RASA files in your backend directory.* 