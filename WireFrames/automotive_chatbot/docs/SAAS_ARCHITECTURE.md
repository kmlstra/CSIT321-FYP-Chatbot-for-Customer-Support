# 🏢 SaaS Automotive Chatbot Platform Architecture

## 🎯 Overview

Transform the current single-tenant chatbot into a multi-tenant SaaS platform where:
- **Clients** can deploy customized chatbots on their websites
- **Client Admin Panel** for managing their chatbot configuration
- **Super Admin Panel** for managing all clients and activating accounts
- **Embeddable Widget** that adapts to each client's branding and data

## 🏗️ Proposed Architecture

### **1. Multi-Tenant Database Structure**

```javascript
// MongoDB Collections

// Clients (Automotive Businesses)
clients: {
  _id: ObjectId,
  business_name: "ABC Motors Singapore",
  domain: "abcmotors.com.sg",
  contact_email: "admin@abcmotors.com.sg",
  subscription_plan: "premium", // basic, premium, enterprise
  status: "active", // pending, active, suspended
  created_at: Date,
  settings: {
    branding: {
      logo_url: "https://abcmotors.com.sg/logo.png",
      primary_color: "#FF6B35",
      secondary_color: "#4A90E2",
      company_name: "ABC Motors"
    },
    features: {
      coe_prices: true,
      loan_calculator: true,
      test_drive_booking: true,
      maintenance_tips: true,
      vehicle_search: true
    },
    contact_info: {
      phone: "+65 6XXX XXXX",
      email: "sales@abcmotors.com.sg",
      address: "123 Automotive Street, Singapore",
      whatsapp: "+65 9XXX XXXX"
    },
    business_hours: {
      monday: "9:00 AM - 7:00 PM",
      tuesday: "9:00 AM - 7:00 PM",
      // ... other days
    }
  }
}

// Client Users (Staff who manage the chatbot)
client_users: {
  _id: ObjectId,
  client_id: ObjectId,
  email: "manager@abcmotors.com.sg",
  name: "John Tan",
  role: "admin", // admin, manager, viewer
  password_hash: "...",
  status: "active", // pending, active, inactive
  created_at: Date,
  last_login: Date
}

// Client Vehicles (Each client's inventory)
client_vehicles: {
  _id: ObjectId,
  client_id: ObjectId,
  brand: "Toyota",
  model: "Camry",
  year: 2024,
  price: 180000,
  availability: "in_stock",
  features: ["Hybrid", "Sunroof", "Leather Seats"],
  images: ["url1", "url2"],
  created_at: Date
}

// Conversations (Multi-tenant)
conversations: {
  _id: ObjectId,
  client_id: ObjectId,
  session_id: "session_123",
  user_id: "anonymous_user_456",
  messages: [
    {
      role: "user",
      content: "What's the price of Toyota Camry?",
      timestamp: Date
    },
    {
      role: "assistant",
      content: "The Toyota Camry at ABC Motors starts from $180,000...",
      timestamp: Date
    }
  ],
  created_at: Date
}

// Analytics (Per Client)
analytics: {
  _id: ObjectId,
  client_id: ObjectId,
  date: Date,
  metrics: {
    total_conversations: 45,
    unique_users: 32,
    popular_queries: ["COE prices", "Test drive", "Loan calculator"],
    conversion_rate: 0.12,
    avg_response_time: 1.2
  }
}
```

### **2. Application Structure**

```
saas-automotive-chatbot/
├── backend/
│   ├── api/
│   │   ├── auth/                    # Authentication & Authorization
│   │   │   ├── client_auth.py       # Client user authentication
│   │   │   ├── super_admin_auth.py  # Super admin authentication
│   │   │   └── jwt_handler.py       # JWT token management
│   │   ├── client_management/       # Client Management APIs
│   │   │   ├── client_crud.py       # Client CRUD operations
│   │   │   ├── user_management.py   # Client user management
│   │   │   └── subscription.py      # Subscription management
│   │   ├── chatbot_config/          # Chatbot Configuration APIs
│   │   │   ├── branding.py          # Branding customization
│   │   │   ├── features.py          # Feature toggles
│   │   │   ├── responses.py         # Custom responses
│   │   │   └── vehicle_inventory.py # Vehicle management
│   │   ├── widget_api/              # Multi-tenant Widget API
│   │   │   ├── chat_endpoint.py     # Chat processing
│   │   │   ├── widget_config.py     # Widget configuration
│   │   │   └── embed_generator.py   # Dynamic embed code
│   │   ├── analytics/               # Analytics APIs
│   │   │   ├── conversation_analytics.py
│   │   │   ├── usage_metrics.py
│   │   │   └── reports.py
│   │   └── super_admin/             # Super Admin APIs
│   │       ├── client_approval.py   # Account activation
│   │       ├── system_monitoring.py # System-wide monitoring
│   │       └── billing.py           # Billing management
│   ├── rasa_multi_tenant/           # Multi-tenant RASA setup
│   │   ├── tenant_router.py         # Route to correct tenant data
│   │   ├── dynamic_actions.py       # Client-specific actions
│   │   └── context_manager.py       # Tenant context management
│   └── models/                      # Database models
│       ├── client.py
│       ├── user.py
│       ├── conversation.py
│       └── analytics.py
├── frontend/
│   ├── client-dashboard/            # Client Management Interface
│   │   ├── pages/
│   │   │   ├── login.tsx            # Client login
│   │   │   ├── dashboard.tsx        # Main dashboard
│   │   │   ├── chatbot-config.tsx   # Chatbot configuration
│   │   │   ├── branding.tsx         # Branding customization
│   │   │   ├── vehicle-inventory.tsx # Vehicle management
│   │   │   ├── analytics.tsx        # Analytics dashboard
│   │   │   └── embed-code.tsx       # Widget embed instructions
│   │   └── components/
│   │       ├── BrandingEditor.tsx
│   │       ├── FeatureToggle.tsx
│   │       ├── VehicleManager.tsx
│   │       └── AnalyticsChart.tsx
│   ├── super-admin/                 # Super Admin Interface
│   │   ├── pages/
│   │   │   ├── login.tsx            # Super admin login
│   │   │   ├── clients.tsx          # Client management
│   │   │   ├── approvals.tsx        # Account approvals
│   │   │   ├── system-monitor.tsx   # System monitoring
│   │   │   └── billing.tsx          # Billing management
│   │   └── components/
│   │       ├── ClientList.tsx
│   │       ├── ApprovalQueue.tsx
│   │       └── SystemMetrics.tsx
│   ├── public-registration/         # Public Registration
│   │   ├── signup.tsx               # Client signup form
│   │   ├── pricing.tsx              # Pricing plans
│   │   └── demo.tsx                 # Demo chatbot
│   └── shared/                      # Shared components
│       ├── components/
│       └── utils/
└── widget/                          # Dynamic Widget Generation
    ├── widget-template.js           # Base widget template
    ├── config-injector.js           # Inject client config
    └── tenant-router.js             # Route to correct tenant
```

### **3. User Flows**

#### **A. Client Registration & Setup Flow**
```
1. Client visits registration page
2. Fills signup form (business details, contact info)
3. Account created with "pending" status
4. Super admin receives notification
5. Super admin reviews and activates account
6. Client receives activation email
7. Client logs in and configures chatbot
8. Client gets embed code for their website
```

#### **B. Client Dashboard Flow**
```
1. Client logs in to dashboard
2. Configure chatbot settings:
   - Branding (logo, colors, company name)
   - Features (enable/disable COE, loans, etc.)
   - Contact information
   - Business hours
   - Vehicle inventory
   - Custom responses
3. Preview chatbot
4. Get embed code
5. View analytics and conversations
```

#### **C. Super Admin Flow**
```
1. Super admin logs in
2. View all clients and their status
3. Approve/reject pending accounts
4. Monitor system-wide metrics
5. Manage subscriptions and billing
6. View system health and performance
```

## 🛠️ Implementation Plan

### **Phase 1: Database & Authentication (Week 1-2)**
1. Design multi-tenant database schema
2. Implement JWT-based authentication
3. Create client and user management APIs
4. Set up role-based access control

### **Phase 2: Client Dashboard (Week 3-4)**
1. Build client registration flow
2. Create client dashboard interface
3. Implement chatbot configuration UI
4. Add branding customization tools

### **Phase 3: Multi-tenant RASA (Week 5-6)**
1. Modify RASA actions for multi-tenancy
2. Implement tenant context routing
3. Create dynamic response system
4. Test client-specific data isolation

### **Phase 4: Super Admin Panel (Week 7-8)**
1. Build super admin interface
2. Implement account approval system
3. Add system monitoring dashboard
4. Create billing management tools

### **Phase 5: Dynamic Widget (Week 9-10)**
1. Create dynamic widget generator
2. Implement client-specific styling
3. Add tenant routing to widget
4. Test embed functionality

### **Phase 6: Analytics & Optimization (Week 11-12)**
1. Build analytics dashboard
2. Implement usage tracking
3. Add performance monitoring
4. Optimize for scale

## 🔧 Technical Implementation Details

### **1. Multi-tenant RASA Actions**

```python
# backend/api/external/multi_tenant_actions.py
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionGetClientVehicles(Action):
    def name(self) -> str:
        return "action_get_client_vehicles"
    
    def run(self, dispatcher, tracker, domain):
        # Extract client_id from session metadata
        client_id = tracker.get_slot("client_id")
        
        # Get client-specific vehicle data
        vehicles = self.get_client_vehicles(client_id)
        
        # Get client branding
        client_config = self.get_client_config(client_id)
        
        # Format response with client branding
        response = self.format_vehicle_response(vehicles, client_config)
        
        dispatcher.utter_message(text=response)
        return []
    
    def get_client_vehicles(self, client_id):
        # Query client-specific vehicle inventory
        pass
    
    def get_client_config(self, client_id):
        # Get client configuration and branding
        pass
```

### **2. Dynamic Widget Generation**

```javascript
// widget/dynamic-widget-generator.js
class DynamicChatbotWidget {
    constructor(clientId) {
        this.clientId = clientId;
        this.config = null;
        this.init();
    }
    
    async init() {
        // Fetch client configuration
        this.config = await this.fetchClientConfig();
        this.createWidget();
        this.applyBranding();
    }
    
    async fetchClientConfig() {
        const response = await fetch(`/api/widget/config/${this.clientId}`);
        return response.json();
    }
    
    createWidget() {
        // Create widget HTML with client-specific config
        const widget = document.createElement('div');
        widget.innerHTML = this.getWidgetTemplate();
        document.body.appendChild(widget);
    }
    
    applyBranding() {
        // Apply client-specific colors, logo, etc.
        const header = document.querySelector('.chatbot-header');
        header.style.background = this.config.branding.primary_color;
        
        const logo = document.querySelector('.chatbot-logo');
        logo.src = this.config.branding.logo_url;
    }
    
    async sendMessage(message) {
        // Send message with client context
        const response = await fetch('/api/widget/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                client_id: this.clientId,
                session_id: this.sessionId
            })
        });
        return response.json();
    }
}

// Auto-initialize based on script src
(function() {
    const script = document.currentScript;
    const clientId = script.getAttribute('data-client-id');
    new DynamicChatbotWidget(clientId);
})();
```

### **3. Client Dashboard Component**

```tsx
// frontend/client-dashboard/pages/chatbot-config.tsx
import { useState, useEffect } from 'react';

interface ChatbotConfig {
  branding: {
    logo_url: string;
    primary_color: string;
    secondary_color: string;
    company_name: string;
  };
  features: {
    coe_prices: boolean;
    loan_calculator: boolean;
    test_drive_booking: boolean;
    maintenance_tips: boolean;
    vehicle_search: boolean;
  };
  contact_info: {
    phone: string;
    email: string;
    address: string;
    whatsapp: string;
  };
}

export default function ChatbotConfigPage() {
  const [config, setConfig] = useState<ChatbotConfig | null>(null);
  const [previewMode, setPreviewMode] = useState(false);
  
  useEffect(() => {
    fetchConfig();
  }, []);
  
  const fetchConfig = async () => {
    const response = await fetch('/api/client/chatbot-config');
    const data = await response.json();
    setConfig(data);
  };
  
  const saveConfig = async () => {
    await fetch('/api/client/chatbot-config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
  };
  
  const generateEmbedCode = () => {
    return `<script src="https://your-domain.com/widget.js" data-client-id="${clientId}"></script>`;
  };
  
  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Configuration Panel */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Branding</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Company Name</label>
                <input
                  type="text"
                  value={config?.branding.company_name || ''}
                  onChange={(e) => setConfig({
                    ...config!,
                    branding: { ...config!.branding, company_name: e.target.value }
                  })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Primary Color</label>
                <input
                  type="color"
                  value={config?.branding.primary_color || '#4F46E5'}
                  onChange={(e) => setConfig({
                    ...config!,
                    branding: { ...config!.branding, primary_color: e.target.value }
                  })}
                  className="w-full h-10 border rounded-lg"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Logo URL</label>
                <input
                  type="url"
                  value={config?.branding.logo_url || ''}
                  onChange={(e) => setConfig({
                    ...config!,
                    branding: { ...config!.branding, logo_url: e.target.value }
                  })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Features</h2>
            <div className="space-y-3">
              {Object.entries(config?.features || {}).map(([feature, enabled]) => (
                <label key={feature} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={(e) => setConfig({
                      ...config!,
                      features: { ...config!.features, [feature]: e.target.checked }
                    })}
                    className="mr-3"
                  />
                  <span className="capitalize">{feature.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Contact Information</h2>
            <div className="space-y-4">
              <input
                type="tel"
                placeholder="Phone Number"
                value={config?.contact_info.phone || ''}
                onChange={(e) => setConfig({
                  ...config!,
                  contact_info: { ...config!.contact_info, phone: e.target.value }
                })}
                className="w-full border rounded-lg px-3 py-2"
              />
              <input
                type="email"
                placeholder="Email Address"
                value={config?.contact_info.email || ''}
                onChange={(e) => setConfig({
                  ...config!,
                  contact_info: { ...config!.contact_info, email: e.target.value }
                })}
                className="w-full border rounded-lg px-3 py-2"
              />
              <textarea
                placeholder="Business Address"
                value={config?.contact_info.address || ''}
                onChange={(e) => setConfig({
                  ...config!,
                  contact_info: { ...config!.contact_info, address: e.target.value }
                })}
                className="w-full border rounded-lg px-3 py-2 h-20"
              />
            </div>
          </div>
          
          <div className="flex space-x-4">
            <button
              onClick={saveConfig}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
            >
              Save Configuration
            </button>
            <button
              onClick={() => setPreviewMode(!previewMode)}
              className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700"
            >
              {previewMode ? 'Hide Preview' : 'Show Preview'}
            </button>
          </div>
        </div>
        
        {/* Preview Panel */}
        <div className="space-y-6">
          {previewMode && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Chatbot Preview</h2>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 h-96">
                {/* Chatbot preview component */}
                <div className="text-center text-gray-500">
                  Chatbot preview will appear here
                </div>
              </div>
            </div>
          )}
          
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Embed Code</h2>
            <div className="bg-gray-100 rounded-lg p-4">
              <code className="text-sm">
                {generateEmbedCode()}
              </code>
            </div>
            <button
              onClick={() => navigator.clipboard.writeText(generateEmbedCode())}
              className="mt-3 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
            >
              Copy Embed Code
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

## 🚀 Deployment Strategy

### **Local Development**
- Each client gets a subdomain: `client1.localhost:3000`
- Shared RASA instance with tenant routing
- Local MongoDB with multi-tenant collections

### **Cloud Deployment**
- **Frontend**: Vercel/Netlify with custom domains
- **Backend**: AWS/GCP with auto-scaling
- **Database**: MongoDB Atlas with proper indexing
- **CDN**: CloudFlare for widget delivery
- **Monitoring**: DataDog/New Relic for system monitoring

### **Scaling Considerations**
- **Database sharding** by client_id
- **RASA model caching** per tenant
- **Redis caching** for frequently accessed data
- **Load balancing** for high traffic clients

## 💰 Monetization Model

### **Subscription Tiers**
- **Basic**: $99/month - 1,000 conversations, basic features
- **Premium**: $299/month - 5,000 conversations, all features
- **Enterprise**: $999/month - Unlimited, custom integrations

### **Usage-Based Pricing**
- Additional conversations: $0.10 per conversation
- Custom integrations: $500 setup fee
- White-label solution: $2,000/month

This architecture provides a scalable, multi-tenant SaaS platform that can serve multiple automotive businesses while maintaining data isolation and customization capabilities.