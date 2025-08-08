# Automotive Chatbot Platform - User Manual

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture: BCE Framework](#architecture-bce-framework)
3. [Project Structure](#project-structure)
4. [RASA Configuration Explained](#rasa-configuration-explained)
5. [Quick Start Guide](#quick-start-guide)
6. [Development Guide](#development-guide)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

## Project Overview

The Automotive Chatbot Platform is a modular, scalable chatbot system built specifically for automotive assistance. It provides expert advice on car maintenance, repairs, and troubleshooting through an intelligent conversational interface.

### Key Features
- **Intelligent Automotive Assistant**: Powered by RASA NLU/Core
- **Modern React Frontend**: Built with Next.js and TypeScript
- **Robust Backend**: FastAPI with MongoDB integration
- **BCE Architecture**: Clean separation of concerns
- **Real-time Communication**: WebSocket support for instant responses

## Architecture: BCE Framework

This project strictly follows the **BCE (Business-Controller-Entity)** framework for clean architecture:

### 🏢 **Business Layer** (`frontend/src/business/`)
Contains all business logic and rules:
- **ChatService.ts**: Handles chat operations, message validation, API communication
- **UserService.ts**: User management and preferences
- **AnalyticsService.ts**: Usage tracking and analytics

### 🎮 **Controller Layer** (`frontend/src/controllers/`)
Manages UI interactions and coordinates between Business and Entity layers:
- **ChatController.ts**: Manages chat state, user interactions
- **UserController.ts**: Handles user authentication and profile management
- **NavigationController.ts**: Manages app navigation and routing

### 📊 **Entity Layer** (`frontend/src/entities/`)
Defines data structures and models:
- **ChatMessage.ts**: Message entities, session models, user profiles
- **User.ts**: User-related entities
- **Analytics.ts**: Analytics and tracking entities

### Benefits of BCE Framework
1. **Separation of Concerns**: Each layer has a specific responsibility
2. **Testability**: Easy to unit test each layer independently
3. **Maintainability**: Changes in one layer don't affect others
4. **Scalability**: Easy to extend functionality
5. **Code Reusability**: Business logic can be reused across components

## Project Structure

```
automotive_chatbot/
├── backend/                    # Python Backend (FastAPI + RASA)
│   ├── api/                   # FastAPI application
│   │   ├── main.py           # Main application entry
│   │   ├── routes/           # API endpoints
│   │   ├── models/           # Database models
│   │   └── services/         # Business services
│   ├── data/                 # RASA Training Data (Root Level)
│   │   ├── nlu.yml          # Natural Language Understanding
│   │   ├── stories.yml      # Conversation flows
│   │   └── rules.yml        # Conversation rules
│   ├── rasa/                # RASA Project Directory
│   │   ├── config.yml       # RASA configuration
│   │   ├── data/           # Symlinked to ../data/
│   │   └── models/         # Trained models
│   ├── config.yml           # Main RASA config
│   ├── domain.yml           # RASA domain definition
│   └── requirements.txt     # Python dependencies
├── frontend/                  # React Frontend (Next.js)
│   ├── src/
│   │   ├── business/        # Business Logic Layer
│   │   ├── controllers/     # Controller Layer
│   │   ├── entities/        # Entity/Model Layer
│   │   ├── components/      # React Components
│   │   └── app/            # Next.js App Router
│   └── package.json
├── scripts/                  # Automation Scripts
│   ├── start_all.bat       # Start all services
│   ├── start_rasa.bat      # Start RASA server
│   ├── start_fastapi.bat   # Start FastAPI server
│   └── start_frontend.bat  # Start React frontend
├── web-interface/           # Static Web Interfaces
│   ├── chat.html           # Simple chat interface
│   └── chat-widget.html    # Advanced chat widget
└── docs/                   # Documentation
    └── USER_MANUAL.md      # This file
```

## RASA Configuration Explained

### Why Two Data Locations?

#### 1. **`backend/data/`** - Primary Training Data
This is the **main source of truth** for all RASA training data:
- **Purpose**: Central location for all training data
- **Contents**: 
  - `nlu.yml`: Intent examples and entity training data
  - `stories.yml`: Conversation flow examples
  - `rules.yml`: Fixed conversation rules
- **Why needed**: RASA requires training data to understand user intents and generate appropriate responses

#### 2. **`backend/rasa/`** - RASA Project Directory
This is the **RASA project workspace**:
- **Purpose**: Contains RASA-specific configuration and generated files
- **Contents**:
  - `config.yml`: RASA pipeline configuration
  - `data/`: Symlinked to `../data/` (avoids duplication)
  - `models/`: Trained RASA models
- **Why needed**: RASA CLI expects a specific project structure

### RASA Training Data Structure

#### **NLU (Natural Language Understanding)**
```yaml
# backend/data/nlu.yml
nlu:
- intent: ask_oil_change
  examples: |
    - When should I change my oil?
    - How often do I need an oil change?
    - Oil change frequency for my car

- intent: check_engine_light
  examples: |
    - What does check engine light mean?
    - My check engine light is on
    - Check engine light troubleshooting
```

#### **Stories (Conversation Flows)**
```yaml
# backend/data/stories.yml
stories:
- story: oil change inquiry
  steps:
  - intent: ask_oil_change
  - action: utter_oil_change_info
  - intent: ask_oil_type
  - action: utter_oil_type_recommendation
```

#### **Rules (Fixed Responses)**
```yaml
# backend/data/rules.yml
rules:
- rule: Say goodbye anytime the user says goodbye
  steps:
  - intent: goodbye
  - action: utter_goodbye
```

### Configuration Files

#### **Domain (`backend/domain.yml`)**
Defines the chatbot's universe:
- **Intents**: What users can say
- **Entities**: Important information to extract
- **Responses**: What the bot can say back
- **Actions**: Custom actions the bot can perform

#### **Config (`backend/config.yml`)**
Defines the RASA pipeline:
- **Language**: Language model to use
- **Pipeline**: NLU processing steps
- **Policies**: How to decide what to do next

## Quick Start Guide

### Prerequisites
- Python 3.8+ with pip
- Node.js 18+ with npm
- MongoDB (local or cloud)

### 1. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

### 2. Start All Services

```bash
# Use the all-in-one script
cd scripts
./start_all.bat
```

This will start:
- MongoDB (if not running)
- RASA server (http://localhost:5005)
- FastAPI backend (http://localhost:8000)
- React frontend (http://localhost:3000)

### 3. Access the Application

- **Main Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Simple Chat Interface**: Open `web-interface/chat.html`
- **Advanced Chat Widget**: Open `web-interface/chat-widget.html`

## Development Guide

### Adding New Intents

1. **Add training examples** in `backend/data/nlu.yml`:
```yaml
- intent: new_intent_name
  examples: |
    - Example user message 1
    - Example user message 2
```

2. **Add responses** in `backend/domain.yml`:
```yaml
responses:
  utter_new_response:
  - text: "Response to the new intent"
```

3. **Create conversation flows** in `backend/data/stories.yml`:
```yaml
- story: new intent story
  steps:
  - intent: new_intent_name
  - action: utter_new_response
```

4. **Retrain the model**:
```bash
cd backend
rasa train
```

### Frontend Development with BCE

#### Adding New Business Logic
```typescript
// frontend/src/business/NewService.ts
export class NewService {
  // Business logic here
}
```

#### Adding New Controller
```typescript
// frontend/src/controllers/NewController.ts
export class NewController {
  private service: NewService;
  
  // Controller logic here
}
```

#### Adding New Entity
```typescript
// frontend/src/entities/NewEntity.ts
export interface NewEntity {
  // Entity properties here
}
```

### Backend API Development

The FastAPI backend follows RESTful principles:

```python
# backend/api/routes/new_route.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "New endpoint"}
```

## Deployment

### Production Deployment

1. **Environment Variables**:
```bash
# .env file
MONGODB_URL=mongodb://localhost:27017
RASA_URL=http://localhost:5005
API_URL=http://localhost:8000
```

2. **Build Frontend**:
```bash
cd frontend
npm run build
npm start
```

3. **Start Backend Services**:
```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000
rasa run --enable-api --cors "*" --port 5005
```

### Docker Deployment

```dockerfile
# Dockerfile example for backend
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

#### 1. **Dependency Conflicts**
```bash
# Solution: Use the fixed requirements.txt
pip install -r backend/requirements.txt
```

#### 2. **RASA Training Fails**
```bash
# Check data format
rasa data validate

# Retrain with debug
rasa train --debug
```

#### 3. **Frontend Build Errors**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### 4. **API Connection Issues**
- Check if all services are running
- Verify CORS settings in FastAPI
- Check firewall/port settings

### Performance Optimization

1. **RASA Model Optimization**:
   - Use appropriate pipeline components
   - Optimize training data quality
   - Regular model retraining

2. **Frontend Optimization**:
   - Implement proper caching
   - Use React.memo for expensive components
   - Optimize bundle size

3. **Backend Optimization**:
   - Use async/await properly
   - Implement database indexing
   - Add response caching

### Monitoring and Logging

1. **RASA Logging**:
```yaml
# config.yml
debug_plots: true
```

2. **FastAPI Logging**:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

3. **Frontend Error Tracking**:
```typescript
// Error boundary implementation
class ErrorBoundary extends React.Component {
  // Error handling logic
}
```

## Support

For technical support or questions:
1. Check this user manual
2. Review the code documentation
3. Check the troubleshooting section
4. Create an issue in the project repository

---

**Last Updated**: January 2025  
**Version**: 2.0.0  
**Framework**: BCE (Business-Controller-Entity) 