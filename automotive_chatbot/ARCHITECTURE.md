# 🏗️ Architecture Documentation
## *Automotive Chatbot Platform - RASA + FastAPI + React*

---

## 📁 Project Structure Overview

```
automotive_chatbot/
├── 📄 README.md                    # Main installation & user guide
├── 📄 ARCHITECTURE.md              # This file - architecture documentation
├── 📄 setup.py                     # Automated installation script
├── 📄 package.json                 # Root project dependencies
├── 📄 .env                         # Environment variables
│
├── 🔧 backend/                     # Python Backend (BCE Pattern)
│   ├── 📄 requirements.txt         # Python dependencies
│   │
│   ├── 🤖 rasa/                    # RASA Configuration (Consolidated)
│   │   ├── 📄 config.yml           # RASA ML pipeline configuration
│   │   ├── 📄 domain.yml           # Intents, entities, responses
│   │   ├── 📄 endpoints.yml        # Action server endpoints
│   │   └── 📄 credentials.yml      # Channel credentials
│   │
│   ├── 📊 data/                    # RASA Training Data
│   │   ├── 📄 nlu.yml              # Natural Language Understanding examples
│   │   ├── 📄 stories.yml          # Conversation training stories
│   │   ├── 📄 rules.yml            # Conversation rules
│   │   ├── 📄 vehicle_inventory.xlsx    # Vehicle data
│   │   └── 📄 maintenance_schedules.xlsx # Maintenance schedules
│   │
│   ├── 🧪 tests/                   # RASA Model Testing
│   │   └── 📄 test_stories.yml     # Test conversation scenarios
│   │
│   ├── 🎬 actions/                 # RASA Custom Actions (Separate from API)
│   │   └── 📄 actions.py           # Custom action implementations
│   │
│   ├── 📦 models/                  # Trained RASA Models
│   │   └── 📄 *.tar.gz             # Compressed trained models
│   │
│   └── ⚡ api/                     # FastAPI Backend (BCE Architecture)
│       ├── 📄 main.py              # FastAPI application entry point
│       ├── 📄 auth.py              # Authentication utilities
│       │
│       ├── 🌐 boundaries/          # HTTP Interface Layer (BCE)
│       │   ├── 📄 chatbots.py      # Chatbot HTTP endpoints
│       │   ├── 📄 users.py         # User HTTP endpoints  
│       │   ├── 📄 admin.py         # Admin HTTP endpoints
│       │   ├── 📄 analytics.py     # Analytics HTTP endpoints
│       │   └── 📄 widget_api.py    # Chat widget HTTP endpoints
│       │
│       ├── 🎯 controllers/         # Business Logic Layer (BCE)
│       │   ├── 📄 chatbot_controller.py     # Chatbot business logic
│       │   ├── 📄 user_controller.py        # User business logic
│       │   ├── 📄 admin_controller.py       # Admin business logic
│       │   ├── 📄 analytics_controller.py   # Analytics business logic
│       │   ├── 📄 coe_controller.py         # COE scraping business logic
│       │   ├── 📄 rag_controller.py         # RAG business logic
│       │   └── 📄 loan_controller.py        # Loan calculation business logic
│       │
│       └── 🗄️ entities/            # Data Access Layer (BCE)
│           ├── 📄 chatbot_entity.py         # Chatbot database operations
│           ├── 📄 user_entity.py            # User database operations
│           ├── 📄 admin_entity.py           # Admin file operations
│           ├── 📄 analytics_entity.py       # Analytics database operations
│           └── 📄 vehicle_entity.py         # Vehicle database operations
│
└── 🎨 frontend/                    # React Frontend (Standard Pattern)
    ├── 📄 package.json             # Frontend dependencies
    ├── 📄 next.config.js           # Next.js configuration
    ├── 📄 tailwind.config.js       # Tailwind CSS configuration
    ├── 📄 tsconfig.json            # TypeScript configuration
    │
    ├── 📁 public/                  # Static Assets
    │   ├── 📄 favicon.ico          # Site icon
    │   └── 📄 logo.png             # Application logo
    │
    └── 📁 src/                     # Source Code (Clean React Structure)
        ├── 📁 components/          # Reusable React Components
        │   ├── 📄 ChatInterface.tsx        # Main chat component
        │   ├── 📄 EmbeddableWidget.tsx     # Embeddable chat widget
        │   └── 📄 DemoButton.tsx           # Demo functionality
        │
        ├── 📁 pages/               # Page Components (Next.js)
        │   ├── 📄 page.tsx         # Homepage component
        │   └── 📄 layout.tsx       # Layout wrapper
        │
        ├── 📁 services/            # API Communication Services
        │   ├── 📄 chatbot-api.ts   # Chatbot API calls
        │   ├── 📄 auth-api.ts      # Authentication API calls
        │   └── 📄 config.ts        # API configuration
        │
        ├── 📁 styles/              # CSS Stylesheets
        │   ├── 📄 globals.css      # Global styles
        │   └── 📄 components.css   # Component styles
        │
        └── 📁 config/              # Configuration Files
            ├── 📄 constants.ts     # Application constants
            └── 📄 types.ts         # TypeScript type definitions
```

---

## 🏗️ BCE Architecture Pattern (Backend Only)

### **Strict 3-Layer Architecture**

```
🌐 BOUNDARIES ────► 🎯 CONTROLLERS ────► 🗄️ ENTITIES
(HTTP Interface)    (Business Logic)     (Data Access)
     │                     │                   │
     ▼                     ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ • FastAPI Routes│ │ • Validation    │ │ • MongoDB Ops   │
│ • Request/Resp  │ │ • Business Rules│ │ • File I/O      │  
│ • HTTP Status   │ │ • Orchestration │ │ • External APIs │
│ • Input Parsing │ │ • Error Handling│ │ • Raw Data      │
│                 │ │ • Workflows     │ │                 │
│ ❌ NO DB Access │ │ ❌ NO HTTP Logic│ │ ❌ NO Bus Logic │
│ ❌ NO Bus Logic │ │ ❌ NO DB Direct │ │ ❌ NO HTTP      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### **🌐 BOUNDARIES Layer**
**Purpose**: HTTP request/response handling ONLY
**Responsibilities**:
- ✅ Receive HTTP requests 
- ✅ Parse request parameters
- ✅ Validate input format
- ✅ Transform responses to HTTP format
- ✅ Handle HTTP status codes
- ✅ **DELEGATE** all logic to controllers

**Strict Rules**:
- ❌ **NO database access**
- ❌ **NO business logic** 
- ❌ **NO direct service calls**
- ✅ **ONLY HTTP concerns**

**Example**:
```python
@router.post("/chatbots")
async def create_chatbot(chatbot: ChatbotCreate, user = Depends(get_user)):
    """🌐 BOUNDARY: Create chatbot - delegates to controller"""
    try:
        # Delegate business logic to controller
        controller = ChatbotController()
        result = await controller.create_chatbot(
            name=chatbot.name,
            owner_id=user["id"]
        )
        
        # Transform to HTTP response
        return {"success": True, "chatbot_id": result["id"]}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### **🎯 CONTROLLERS Layer**
**Purpose**: Business logic and orchestration
**Responsibilities**:
- ✅ **ALL business logic here**
- ✅ Input validation and business rules
- ✅ Workflow orchestration  
- ✅ Error handling and logging
- ✅ **DELEGATE** data operations to entities

**Strict Rules**:
- ❌ **NO HTTP concerns**
- ❌ **NO direct database calls**
- ❌ **NO direct external API calls**
- ✅ **PURE business logic**

**Example**:
```python
class ChatbotController:
    async def create_chatbot(self, name: str, owner_id: str):
        # Business logic: validation
        if len(name) < 3:
            raise ValueError("Name must be at least 3 characters")
        
        # Business logic: user limits  
        if await self._count_user_chatbots(owner_id) >= 10:
            raise ValueError("Maximum chatbots reached")
        
        # Business logic: prepare data
        chatbot_data = {
            "name": name.strip(),
            "owner_id": owner_id,
            "created_at": datetime.utcnow()
        }
        
        # Delegate to entity for storage
        entity = ChatbotEntity()
        return await entity.create_chatbot(chatbot_data)
```

### **🗄️ ENTITIES Layer** 
**Purpose**: Pure data access operations
**Responsibilities**:
- ✅ **ONLY database CRUD operations**
- ✅ File I/O operations
- ✅ External API calls (raw data)
- ✅ Data transformation (database format)

**Strict Rules**:
- ❌ **NO business logic**
- ❌ **NO validation** (controller handles this)
- ❌ **NO HTTP concerns**
- ✅ **PURE data operations**

**Example**:
```python
class ChatbotEntity:
    async def create_chatbot(self, chatbot_data: Dict) -> Dict:
        """🗄️ ENTITY: Pure database insert - NO business logic"""
        try:
            db = await self._get_database()
            result = await db["chatbots"].insert_one(chatbot_data)
            return {"_id": result.inserted_id, "success": True}
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            raise
```

---

## 🎯 BCE Implementation by Functionality

### **1. 👤 User Management**

```
🌐 users.py ────► 🎯 user_controller.py ────► 🗄️ user_entity.py
     │                     │                        │
     ▼                     ▼                        ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ /register       │ │ register_user() │ │ create_user()   │
│ /login          │ │ authenticate()  │ │ get_user_by_email()│
│ /profile        │ │ get_profile()   │ │ update_user()   │
│ /update         │ │ update_profile()│ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘

Business Rules in Controller:
• Email validation
• Password strength requirements  
• Duplicate email checking
• JWT token generation
• Profile update validation
```

### **2. 🤖 Chatbot Management**

```
🌐 chatbots.py ──► 🎯 chatbot_controller.py ──► 🗄️ chatbot_entity.py
     │                     │                           │
     ▼                     ▼                           ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ /chatbots       │ │ create_chatbot()│ │ create_chatbot()│
│ /chatbots/{id}  │ │ get_chatbots()  │ │ get_user_chatbots()│
│ /pricing        │ │ update_chatbot()│ │ update_chatbot()│
│ /coe-prices     │ │ delete_chatbot()│ │ soft_delete()   │
└─────────────────┘ └─────────────────┘ └─────────────────┘

Business Rules in Controller:
• Chatbot name validation (min 3 chars)
• User chatbot limits (max 10 per user)  
• Ownership validation
• Status management
• Configuration validation
```

### **3. 🛠️ Admin Management**

```
🌐 admin.py ─────► 🎯 admin_controller.py ─────► 🗄️ admin_entity.py
     │                     │                           │
     ▼                     ▼                           ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ /stories        │ │ get_stories()   │ │ load_stories()  │
│ /train          │ │ create_story()  │ │ save_stories()  │
│ /models         │ │ train_model()   │ │ train_command() │
│ /backup         │ │ create_backup() │ │ backup_files()  │
└─────────────────┘ └─────────────────┘ └─────────────────┘

Business Rules in Controller:
• Story validation (min steps, format)
• Training data completeness check
• Backup before training
• Model file management
• RASA configuration validation
```

### **4. 📊 Analytics**

```
🌐 analytics.py ──► 🎯 analytics_controller.py ──► 🗄️ analytics_entity.py
     │                     │                             │
     ▼                     ▼                             ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ /events         │ │ track_event()   │ │ store_event()   │
│ /reports        │ │ get_reports()   │ │ query_events()  │
│ /metrics        │ │ calc_metrics()  │ │ aggregate_data()│
└─────────────────┘ └─────────────────┘ └─────────────────┘

Business Rules in Controller:
• Event validation
• Privacy filtering
• Report generation logic
• Metrics calculation
• Data aggregation rules
```

### **5. 🚗 COE & Vehicle Data**

```
🌐 chatbots.py ───► 🎯 coe_controller.py ───► 🗄️ vehicle_entity.py
     │                     │                         │
     ▼                     ▼                         ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ /coe-prices     │ │ get_coe_data()  │ │ scrape_lta_api()│
│ /vehicle-info   │ │ format_response()│ │ store_vehicle() │
│ /compare        │ │ compare_models()│ │ query_vehicles()│
└─────────────────┘ └─────────────────┘ └─────────────────┘

Business Rules in Controller:
• COE category validation
• Data freshness checks
• Response formatting
• Comparison logic
• Pricing calculations
```

---

## 🎨 Frontend Architecture (React Standard)

### **Clean React Structure (NO BCE)**

```
Frontend (React/Next.js)
│
├── 📁 components/          # Reusable UI Components
│   ├── ChatInterface       # Main chat component
│   ├── EmbeddableWidget    # Embeddable widget
│   └── DemoButton          # Demo functionality
│
├── 📁 pages/              # Page Components (Next.js routing)
│   ├── HomePage           # Landing page
│   ├── Dashboard          # User dashboard
│   └── AdminPanel         # Admin interface
│
├── 📁 services/           # API Communication Layer
│   ├── chatbot-api.ts     # Chatbot API calls
│   ├── auth-api.ts        # Authentication API calls
│   └── analytics-api.ts   # Analytics API calls
│
├── 📁 styles/             # CSS Stylesheets
│   ├── globals.css        # Global styles
│   └── components.css     # Component-specific styles
│
└── 📁 config/             # Configuration
    ├── constants.ts       # App constants
    └── types.ts           # TypeScript types
```

### **Frontend Data Flow**

```
React Component ────► API Service ────► Backend API
      │                    │                 │
      ▼                    ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ • User Actions  │ │ • HTTP Requests │ │ • BCE Processing│
│ • State Mgmt    │ │ • Response Hand │ │ • Business Logic│
│ • UI Rendering  │ │ • Error Handling│ │ • Data Storage  │
│ • Event Handling│ │ • Auth Headers  │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Frontend Responsibilities**:
- ✅ User interface rendering
- ✅ User interaction handling
- ✅ Client-side state management
- ✅ API service calls
- ✅ Response formatting for UI
- ❌ **NO business logic** (backend handles this)
- ❌ **NO direct database access**

**Example API Service**:
```typescript
// services/chatbot-api.ts
export class ChatbotApiService {
  async createChatbot(data: CreateChatbotRequest) {
    const response = await fetch('/api/chatbots', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
}
```

---

## 🚀 Service Interaction Flow

### **Complete Request Flow**

```
1. User clicks "Create Chatbot" in React
        ↓
2. ChatInterface.tsx calls chatbot-api.createChatbot()
        ↓  
3. API service makes HTTP POST to /api/chatbots
        ↓
4. 🌐 boundaries/chatbots.py receives request
        ↓
5. Boundary validates HTTP input & delegates to controller
        ↓
6. 🎯 controllers/chatbot_controller.py handles business logic
   • Validates chatbot name (min 3 chars)
   • Checks user chatbot limit (max 10)
   • Prepares chatbot data with defaults
        ↓
7. Controller delegates to entity for storage
        ↓
8. 🗄️ entities/chatbot_entity.py stores in MongoDB
        ↓
9. Entity returns database result to controller
        ↓
10. Controller returns formatted result to boundary
        ↓
11. Boundary returns HTTP response to frontend
        ↓
12. Frontend updates UI with new chatbot
```

### **RASA Integration Flow**

```
User Message ────► Widget API ────► RASA Server ────► Custom Actions
      │                │                │                   │
      ▼                ▼                ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ "What's COE?"   │ │ Process request │ │ NLU + Dialogue │ │ action_coe_data │
│ Frontend Widget │ │ Route to RASA   │ │ Intent: coe_q   │ │ Fetch LTA data  │
│                 │ │ Format response │ │ Action triggered│ │ Return response │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 🛠️ Development Guidelines

### **Adding New Functionality**

**1. Backend (BCE Pattern)**:
```bash
# 1. Create entity for data access
touch backend/api/entities/feature_entity.py

# 2. Create controller for business logic  
touch backend/api/controllers/feature_controller.py

# 3. Create boundary for HTTP interface
touch backend/api/boundaries/feature.py

# 4. Update main.py to include routes
# 5. Test each layer independently
```

**2. Frontend (React Pattern)**:
```bash
# 1. Create API service
touch frontend/src/services/feature-api.ts

# 2. Create React component
touch frontend/src/components/FeatureComponent.tsx

# 3. Add to pages if needed
# 4. Update routing if required
```

### **Testing Strategy**

**BCE Layer Testing**:
- **Boundaries**: HTTP request/response testing
- **Controllers**: Business logic unit tests
- **Entities**: Database operation tests

**Frontend Testing**:
- **Components**: React component testing
- **Services**: API integration testing
- **Pages**: End-to-end testing

---

## 📊 Key Benefits of This Architecture

### **Backend BCE Benefits**:
1. **🔒 Separation of Concerns**: Each layer has single responsibility
2. **🧪 Testability**: Each layer can be tested independently  
3. **🔄 Maintainability**: Changes isolated to specific layers
4. **📈 Scalability**: Easy to scale individual components
5. **🛡️ Security**: Business logic protected from HTTP layer

### **Frontend Standard Benefits**:
1. **⚡ Performance**: Optimized for UI rendering
2. **🔄 Reusability**: Components can be reused across pages
3. **📱 Responsiveness**: Clean separation of UI concerns
4. **🧩 Modularity**: Service layer for API communication
5. **🎯 Simplicity**: Standard React patterns, no unnecessary complexity

### **Overall System Benefits**:
1. **🔗 Clear Interfaces**: Well-defined boundaries between layers
2. **📚 Documentation**: Each layer's purpose is explicit
3. **🚀 Development Speed**: Developers know exactly where to put code
4. **🔧 Debugging**: Issues can be isolated to specific layers
5. **👥 Team Collaboration**: Multiple developers can work on different layers

---

*🏗️ This architecture ensures maintainable, scalable, and testable code while leveraging the strengths of both RASA's conversational AI and modern web development patterns.* 