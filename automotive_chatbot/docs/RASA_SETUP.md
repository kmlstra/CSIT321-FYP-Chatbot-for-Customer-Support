# 🤖 Rasa Setup and Training Guide

## Overview

Rasa is the conversational AI engine that handles:
- **Natural Language Understanding (NLU)** - Understanding user intent
- **Dialogue Management** - Managing conversation flow  
- **Response Generation** - Generating appropriate responses
- **Custom Actions** - Executing automotive-specific queries

## 🚀 Quick Setup

### 1. Install Rasa (Already included in requirements.txt)
```bash
# Activate virtual environment
.venv\Scripts\activate

# Rasa is automatically installed with:
pip install -r backend/requirements.txt

# Download language model
python -m spacy download en_core_web_sm
```

### 2. Train the Model
```bash
# Method 1: Using npm script
npm run rasa:train

# Method 2: Direct command
cd backend
rasa train
```

### 3. Start Rasa Server
```bash
# Option 1: With all services
npm run dev:all-with-rasa

# Option 2: Rasa only
cd backend
rasa run --enable-api --cors "*" --port 5005
```

## 📁 Training Data Structure

```
backend/
├── data/
│   ├── nlu.yml          # User intents and examples
│   ├── stories.yml      # Conversation flows
│   └── domain.yml       # Bot's universe definition
├── config.yml           # Pipeline configuration
└── models/              # Trained models (auto-generated)
```

## 📚 Training Data Overview

### **`backend/data/nlu.yml`**
Contains intents and example phrases:
```yaml
- intent: greet
  examples: |
    - hello
    - hi there
    - good morning

- intent: ask_car_price
  examples: |
    - How much does a [Toyota Camry](car_model) cost?
    - What's the price of [Honda Civic](car_model)?
```

### **`backend/data/stories.yml`**
Defines conversation flows:
```yaml
- story: car price inquiry
  steps:
  - intent: greet
  - action: utter_greet
  - intent: ask_car_price
  - action: utter_car_price
```

### **`backend/data/domain.yml`**
Defines the chatbot's universe:
```yaml
intents:
  - greet
  - ask_car_price

responses:
  utter_greet:
  - text: "Hello! How can I help you with automotive queries today?"
```

## 🔄 Retraining the Model

When you modify training data:

```bash
# Force retrain (recommended)
cd backend
rasa train --force

# Quick retrain (only if data changed)
cd backend  
rasa train
```

**The trained model is saved in `backend/models/`**

## 🛠️ Customizing Training Data

### Adding New Intents

1. **Edit `backend/data/nlu.yml`**:
```yaml
- intent: book_test_drive
  examples: |
    - I want to book a test drive
    - Can I schedule a test drive for [Toyota Camry](car_model)?
    - Book test drive for tomorrow
```

2. **Update `backend/data/domain.yml`**:
```yaml
intents:
  - book_test_drive

responses:
  utter_book_test_drive:
  - text: "I'd be happy to help you book a test drive! Which car interests you?"
```

3. **Add to `backend/data/stories.yml`**:
```yaml
- story: test drive booking
  steps:
  - intent: book_test_drive
  - action: utter_book_test_drive
```

4. **Retrain**:
```bash
rasa train --force
```

## 🔧 Configuration

### **`backend/config.yml`**
Pipeline configuration for NLU and dialogue policies:
```yaml
language: en

pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: DIETClassifier
    epochs: 100

policies:
  - name: TEDPolicy
    max_history: 5
    epochs: 100
```

## 🚨 Troubleshooting

### **Model Training Fails**
```bash
# Validate training data
cd backend
rasa data validate

# Train with debug output
rasa train --debug
```

### **Server Won't Start**
```bash
# Check if port 5005 is available
netstat -an | findstr :5005

# Try different port
rasa run --enable-api --cors "*" --port 5006
```

### **API Integration Issues**
Ensure FastAPI can connect to Rasa:
```python
# In backend/api/routes/chatbots.py
RASA_URL = "http://localhost:5005"

# Test connection
curl http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "hello"}'
```

## 📊 Git Best Practices

### ✅ **Include in Git:**
- `backend/data/*.yml` - Training data
- `backend/domain.yml` - Domain configuration  
- `backend/config.yml` - Pipeline configuration
- `backend/credentials.yml` - API credentials template

### ❌ **Exclude from Git (.gitignore):**
```gitignore
# Rasa trained models (large binary files)
backend/models/
.rasa/
```

## 🔄 Training Workflow

```bash
# 1. Modify training data
vim backend/data/nlu.yml

# 2. Validate data
rasa data validate

# 3. Train model
rasa train --force

# 4. Test model
rasa shell

# 5. Start API server
rasa run --enable-api --cors "*" --port 5005
```

## 🎯 Advanced Features

### **Custom Actions**
Create custom actions in `backend/actions/`:
```python
# actions.py
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionCheckCarPrice(Action):
    def name(self) -> str:
        return "action_check_car_price"
    
    def run(self, dispatcher, tracker, domain):
        car_model = tracker.get_slot("car_model")
        # Fetch price from database/API
        response = f"The {car_model} starts from $X,XXX"
        dispatcher.utter_message(text=response)
        return []
```

### **Conversation Analytics**
Enable in `backend/endpoints.yml`:
```yaml
tracker_store:
  type: mongod
  url: mongodb://localhost:27017
  db: automotive_chatbot
  collection: conversations
```

## 🚀 Production Deployment

```bash
# Build optimized model
rasa train --config config.yml --domain domain.yml --data data/

# Start production server
rasa run --enable-api --cors "*" --port 5005 --endpoints endpoints.yml
```

## 📱 API Testing

Test your trained model:
```bash
# Test message
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "user123",
    "message": "Hello, I want to know about Toyota Camry price"
  }'
```

## 🎉 You're Ready!

Your Rasa chatbot is now configured and ready to handle automotive conversations! The AI will understand user intents and respond intelligently based on your training data. 