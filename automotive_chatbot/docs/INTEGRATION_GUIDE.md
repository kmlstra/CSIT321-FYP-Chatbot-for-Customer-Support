# 🔌 Automotive Chatbot Integration Guide

## Overview

This guide explains how to integrate the Automotive Chatbot as an API or module into your existing websites and applications.

## 🚀 Quick Integration (1-minute setup)

### **Option 1: One-line Integration**
```html
<!-- Add this single line to your website -->
<script src="https://your-api-domain.com/api/widget/embed.js?widget_id=your-widget-id"></script>
```

### **Option 2: Custom Configuration**
```html
<script>
// Load and configure the widget
fetch('https://your-api-domain.com/api/widget/embed.js?widget_id=custom')
  .then(response => response.text())
  .then(script => {
    eval(script);
    
    // Create custom widget
    const widget = window.createAutomotiveWidget({
      apiUrl: 'https://your-api-domain.com/api/widget',
      widgetId: 'custom-automotive',
      theme: {
        primary_color: '#your-brand-color',
        secondary_color: '#your-secondary-color',
        font_family: 'Your Brand Font'
      },
      autoOpen: false // Don't auto-open on load
    });
  });
</script>
```

## 🏗️ API-First Approach

### **Direct API Integration**

If you prefer to build your own UI, use our REST API directly:

```javascript
// Send a message to the chatbot
async function sendMessage(message) {
  const response = await fetch('https://your-api-domain.com/api/widget/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      user_id: 'your-user-id',
      session_id: 'session-123',
      context: {
        widget_id: 'your-widget',
        url: window.location.href,
        user_preferences: {
          vehicle_type: 'car',
          budget_range: '50000-100000'
        }
      }
    })
  });

  const data = await response.json();
  
  if (data.success) {
    console.log('Bot response:', data.response);
    console.log('Response source:', data.source); // 'ai_enhanced' or 'rule_based'
    console.log('Confidence:', data.metadata.confidence);
  }
}
```

### **Response Format**
```json
{
  "success": true,
  "response": "🚗 Latest COE Bidding Results (2025-01-15)...",
  "user_id": "user_abc123",
  "session_id": "session_xyz789",
  "source": "ai_enhanced",
  "metadata": {
    "timestamp": "2025-01-15T10:30:00Z",
    "confidence": 0.92
  }
}
```

## 🎨 Customization Options

### **Theme Configuration**
```javascript
const customTheme = {
  primary_color: '#1e40af',      // Main brand color
  secondary_color: '#3b82f6',    // Secondary color
  font_family: 'Inter, sans-serif',
  border_radius: '8px',          // Corner roundness
  position: 'bottom-left',       // Widget position
  width: '400px',                // Custom width
  height: '600px'                // Custom height
};
```

### **Behavioral Configuration**
```javascript
const widgetConfig = {
  autoOpen: true,                // Open widget automatically
  minimized: false,              // Start minimized
  showWelcome: true,             // Show welcome message
  enableTyping: true,            // Show typing indicators
  sessionPersistence: true,      // Remember conversations
  maxMessages: 50,               // Message history limit
  placeholder: 'Ask about COE prices...'
};
```

## 🏢 Business Integration Examples

### **1. Automotive Dealership**
```html
<!DOCTYPE html>
<html>
<head>
  <title>ABC Motors Singapore</title>
</head>
<body>
  <!-- Your existing website content -->
  
  <!-- Automotive Chatbot Integration -->
  <script>
    // Configure for automotive dealership
    window.createAutomotiveWidget({
      widgetId: 'abc-motors-sg',
      theme: {
        primary_color: '#c41e3a',  // Dealership brand color
        secondary_color: '#8b1538'
      },
      context: {
        business_type: 'dealership',
        location: 'singapore',
        specialization: ['new_cars', 'used_cars', 'financing']
      },
      welcome_message: '👋 Welcome to ABC Motors! I can help with COE prices, vehicle information, and financing options.'
    });
  </script>
  <script src="https://your-api.com/api/widget/embed.js?widget_id=abc-motors"></script>
</body>
</html>
```

### **2. Insurance Company**
```javascript
// Insurance company integration
const insuranceWidget = window.createAutomotiveWidget({
  widgetId: 'insurance-helper',
  theme: {
    primary_color: '#059669',
    secondary_color: '#047857'
  },
  context: {
    business_type: 'insurance',
    services: ['vehicle_insurance', 'coe_coverage', 'claims']
  },
  welcome_message: '🛡️ Hi! I can help with vehicle insurance, COE coverage, and claims information.'
});
```

### **3. Government Portal**
```javascript
// Government service integration
const govWidget = window.createAutomotiveWidget({
  widgetId: 'lta-helper',
  theme: {
    primary_color: '#1e3a8a',
    secondary_color: '#1e40af'
  },
  context: {
    business_type: 'government',
    department: 'lta',
    services: ['registration', 'licensing', 'regulations']
  },
  welcome_message: '🏛️ Welcome to LTA services. I can help with vehicle registration, COE information, and regulations.'
});
```

## 📱 Framework-Specific Integrations

### **React Integration**
```jsx
import { useEffect, useRef } from 'react';

const AutomotiveChatWidget = ({ config }) => {
  const widgetRef = useRef(null);

  useEffect(() => {
    // Load widget script
    const script = document.createElement('script');
    script.src = `${config.apiUrl}/widget/embed.js?widget_id=${config.widgetId}`;
    script.onload = () => {
      // Initialize widget with custom config
      widgetRef.current = window.createAutomotiveWidget(config);
    };
    document.head.appendChild(script);

    return () => {
      // Cleanup on component unmount
      document.head.removeChild(script);
    };
  }, [config]);

  return null; // Widget is injected by script
};

// Usage in React app
function App() {
  const widgetConfig = {
    apiUrl: 'https://your-api.com/api/widget',
    widgetId: 'react-automotive',
    theme: {
      primary_color: '#3b82f6'
    }
  };

  return (
    <div>
      <h1>My Automotive Website</h1>
      <AutomotiveChatWidget config={widgetConfig} />
    </div>
  );
}
```

### **Vue.js Integration**
```vue
<template>
  <div>
    <!-- Your Vue app content -->
  </div>
</template>

<script>
export default {
  name: 'App',
  mounted() {
    // Load automotive widget
    this.loadWidget();
  },
  methods: {
    loadWidget() {
      const script = document.createElement('script');
      script.src = 'https://your-api.com/api/widget/embed.js?widget_id=vue-automotive';
      script.onload = () => {
        window.createAutomotiveWidget({
          widgetId: 'vue-automotive',
          theme: {
            primary_color: '#10b981'
          }
        });
      };
      document.head.appendChild(script);
    }
  }
};
</script>
```

### **WordPress Integration**
```php
<?php
// Add to functions.php or create a plugin

function add_automotive_chatbot() {
    $widget_id = get_option('automotive_widget_id', 'wordpress-auto');
    $api_url = get_option('automotive_api_url', 'https://your-api.com');
    
    echo "<script>
        window.automotiveConfig = {
            widgetId: '{$widget_id}',
            theme: {
                primary_color: '" . get_theme_mod('primary_color', '#667eea') . "'
            }
        };
    </script>";
    
    echo "<script src='{$api_url}/api/widget/embed.js?widget_id={$widget_id}'></script>";
}

add_action('wp_footer', 'add_automotive_chatbot');
```

## 🔧 Advanced Configuration

### **Custom Event Handlers**
```javascript
const widget = window.createAutomotiveWidget({
  widgetId: 'advanced-automotive',
  
  // Event callbacks
  onMessageSent: (message) => {
    console.log('User sent:', message);
    // Track analytics
    gtag('event', 'chatbot_message_sent', {
      'custom_parameter': message.length
    });
  },
  
  onResponseReceived: (response) => {
    console.log('Bot responded:', response);
    // Custom response processing
    if (response.includes('COE')) {
      gtag('event', 'coe_query', {
        'response_type': response.source
      });
    }
  },
  
  onWidgetOpened: () => {
    console.log('Widget opened');
    gtag('event', 'chatbot_opened');
  },
  
  onWidgetClosed: () => {
    console.log('Widget closed');
    gtag('event', 'chatbot_closed');
  }
});
```

### **Multi-language Support**
```javascript
const multiLangWidget = window.createAutomotiveWidget({
  widgetId: 'multilang-automotive',
  language: 'en', // 'en', 'zh', 'ms', 'ta'
  
  messages: {
    en: {
      welcome: 'Hi! I can help with Singapore automotive matters.',
      placeholder: 'Ask about COE, registration, or financing...'
    },
    zh: {
      welcome: '您好！我可以帮助您了解新加坡汽车相关事务。',
      placeholder: '询问COE、注册或融资...'
    }
  }
});
```

## 📊 Analytics Integration

### **Google Analytics 4**
```javascript
// Track chatbot interactions
const widget = window.createAutomotiveWidget({
  widgetId: 'analytics-automotive',
  
  onMessageSent: (message) => {
    gtag('event', 'chatbot_interaction', {
      'event_category': 'Chatbot',
      'event_label': 'Message Sent',
      'custom_parameter_1': message.toLowerCase().includes('coe') ? 'coe_query' : 'general_query'
    });
  },
  
  onResponseReceived: (response) => {
    gtag('event', 'chatbot_response', {
      'event_category': 'Chatbot',
      'event_label': 'Response Received',
      'custom_parameter_1': response.source, // 'ai_enhanced' or 'rule_based'
      'custom_parameter_2': response.metadata.confidence
    });
  }
});
```

### **Custom Analytics**
```javascript
// Send analytics to your own system
const widget = window.createAutomotiveWidget({
  widgetId: 'custom-analytics-automotive',
  
  onMessageSent: async (message) => {
    await fetch('/api/analytics/chatbot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: 'message_sent',
        message: message,
        timestamp: new Date().toISOString(),
        user_id: widget.getUserId(),
        session_id: widget.sessionId
      })
    });
  }
});
```

## 🔒 Security Considerations

### **Domain Restrictions**
```javascript
// Restrict widget to specific domains
const widget = window.createAutomotiveWidget({
  widgetId: 'secure-automotive',
  allowedDomains: [
    'yourdomain.com',
    'subdomain.yourdomain.com',
    'localhost' // For development
  ],
  
  // Validate domain before initialization
  beforeInit: () => {
    const currentDomain = window.location.hostname;
    if (!widget.config.allowedDomains.includes(currentDomain)) {
      console.error('Automotive widget not authorized for this domain');
      return false;
    }
    return true;
  }
});
```

### **Content Security Policy**
```html
<!-- Add to your HTML head -->
<meta http-equiv="Content-Security-Policy" 
      content="script-src 'self' https://your-api.com; 
               connect-src 'self' https://your-api.com; 
               style-src 'self' 'unsafe-inline';">
```

## 🚀 Production Deployment

### **CDN Hosting**
```html
<!-- Production widget script -->
<script src="https://cdn.yourdomain.com/automotive-widget/v2.0/embed.js?widget_id=production"></script>
```

### **Environment Configuration**
```javascript
// Environment-specific configuration
const isProduction = window.location.hostname !== 'localhost';

const widget = window.createAutomotiveWidget({
  widgetId: isProduction ? 'prod-automotive' : 'dev-automotive',
  apiUrl: isProduction 
    ? 'https://api.yourdomain.com/api/widget'
    : 'http://localhost:8000/api/widget',
  
  enableAnalytics: isProduction,
  debugMode: !isProduction
});
```

## 📞 Support & Troubleshooting

### **Common Issues**

1. **Widget not appearing**
   ```javascript
   // Check console for errors
   console.log('Widget loaded:', window.AutomotiveWidget);
   
   // Verify API connectivity
   fetch('https://your-api.com/health')
     .then(r => r.json())
     .then(data => console.log('API Status:', data));
   ```

2. **CORS errors**
   ```javascript
   // Ensure your domain is whitelisted in the API CORS settings
   // Contact support to add your domain
   ```

3. **Styling conflicts**
   ```css
   /* Override widget styles if needed */
   .automotive-widget {
     z-index: 99999 !important;
   }
   ```

### **Debug Mode**
```javascript
const widget = window.createAutomotiveWidget({
  widgetId: 'debug-automotive',
  debugMode: true, // Enable detailed logging
  
  onError: (error) => {
    console.error('Widget error:', error);
    // Send error to your logging system
  }
});
```

---

**Need Help?** Contact our integration support team or check the [API documentation](http://localhost:8000/docs) for more details. 