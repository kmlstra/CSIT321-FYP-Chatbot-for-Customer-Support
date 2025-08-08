# Automotive Chatbot - Embedding Guide

## Overview
Our automotive chatbot can be easily embedded into any website with just a few lines of code. The widget is responsive, customizable, and works across all modern browsers.

## Quick Start

### 1. Basic Integration
Add this code to your website's HTML, just before the closing `</body>` tag:

```html
<script>
  window.AutomotiveChatbotConfig = {
    apiEndpoint: 'https://your-chatbot-domain.com/api/chat',
    title: 'Car Assistant',
    primaryColor: '#2563EB'
  };
</script>
<script src="https://your-chatbot-domain.com/embed.js"></script>
```

### 2. Full Configuration
```html
<script>
  window.AutomotiveChatbotConfig = {
    // Required
    apiEndpoint: 'https://your-chatbot-domain.com/api/chat',
    
    // Appearance
    title: 'Automotive Assistant',
    subtitle: 'How can I help you today?',
    primaryColor: '#3B82F6',
    backgroundColor: '#FFFFFF',
    textColor: '#1F2937',
    
    // Position
    position: 'bottom-right', // bottom-right, bottom-left, top-right, top-left
    
    // Size
    height: '500px',
    width: '400px',
    
    // Messages
    welcomeMessage: 'Hello! How can I help you with your automotive needs?',
    placeholder: 'Ask me about cars...',
  };
</script>
<script src="https://your-chatbot-domain.com/embed.js"></script>
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiEndpoint` | string | Required | Your chatbot API endpoint |
| `title` | string | "Automotive Assistant" | Widget header title |
| `subtitle` | string | "How can I help you today?" | Widget header subtitle |
| `primaryColor` | string | "#3B82F6" | Primary brand color (hex) |
| `backgroundColor` | string | "#FFFFFF" | Widget background color |
| `textColor` | string | "#1F2937" | Text color |
| `position` | string | "bottom-right" | Widget position on screen |
| `height` | string | "500px" | Widget height |
| `width` | string | "400px" | Widget width |
| `welcomeMessage` | string | Auto-generated | First message shown |
| `placeholder` | string | "Type your message..." | Input placeholder text |

## JavaScript API

The widget exposes a global API for programmatic control:

```javascript
// Open the chat widget
window.AutomotiveChatbot.open();

// Close the chat widget
window.AutomotiveChatbot.close();

// Send a message programmatically
window.AutomotiveChatbot.sendMessage("Hello!");
```

## Styling Examples

### Brand Color Matching
```javascript
window.AutomotiveChatbotConfig = {
  apiEndpoint: 'https://your-api.com/chat',
  primaryColor: '#FF6B35', // Your brand color
  title: 'Honda Assistant'
};
```

### Dark Theme
```javascript
window.AutomotiveChatbotConfig = {
  apiEndpoint: 'https://your-api.com/chat',
  primaryColor: '#10B981',
  backgroundColor: '#1F2937',
  textColor: '#F9FAFB'
};
```

### Compact Size
```javascript
window.AutomotiveChatbotConfig = {
  apiEndpoint: 'https://your-api.com/chat',
  height: '400px',
  width: '320px'
};
```

## Advanced Integration

### With Analytics
```html
<script>
  window.AutomotiveChatbotConfig = {
    apiEndpoint: 'https://your-api.com/chat',
    onMessage: function(message) {
      // Track user messages
      gtag('event', 'chatbot_message', {
        message_content: message
      });
    }
  };
</script>
```

### Conditional Loading
```html
<script>
  // Only load chatbot on certain pages
  if (window.location.pathname.includes('/cars/')) {
    window.AutomotiveChatbotConfig = {
      apiEndpoint: 'https://your-api.com/chat',
      welcomeMessage: 'Interested in this car? Ask me anything!'
    };
    
    const script = document.createElement('script');
    script.src = 'https://your-chatbot-domain.com/embed.js';
    document.head.appendChild(script);
  }
</script>
```

### React Integration
```jsx
import { useEffect } from 'react';

function ChatbotWidget() {
  useEffect(() => {
    // Configure chatbot
    window.AutomotiveChatbotConfig = {
      apiEndpoint: process.env.REACT_APP_CHATBOT_API,
      primaryColor: '#3B82F6'
    };

    // Load script
    const script = document.createElement('script');
    script.src = `${process.env.REACT_APP_CHATBOT_DOMAIN}/embed.js`;
    script.async = true;
    document.body.appendChild(script);

    return () => {
      // Cleanup
      const widget = document.getElementById('automotive-chatbot-widget');
      if (widget) {
        widget.remove();
      }
    };
  }, []);

  return null; // Widget is injected via script
}
```

### WordPress Integration
Add to your theme's `functions.php`:

```php
function add_automotive_chatbot() {
    ?>
    <script>
        window.AutomotiveChatbotConfig = {
            apiEndpoint: '<?php echo get_option('chatbot_api_endpoint'); ?>',
            title: '<?php echo get_bloginfo('name'); ?> Assistant',
            primaryColor: '<?php echo get_theme_mod('primary_color', '#3B82F6'); ?>'
        };
    </script>
    <script src="https://your-chatbot-domain.com/embed.js"></script>
    <?php
}
add_action('wp_footer', 'add_automotive_chatbot');
```

## Testing

### Local Development
For local testing, use:
```javascript
window.AutomotiveChatbotConfig = {
  apiEndpoint: 'http://localhost:8000/api/chat'
};
```

### CORS Configuration
Ensure your API allows requests from your domain:
- Add your domain to CORS origins
- Include credentials if using authentication

## Troubleshooting

### Common Issues

1. **Widget not appearing**
   - Check browser console for errors
   - Verify script URL is accessible
   - Ensure configuration is set before script loads

2. **API connection failed**
   - Verify apiEndpoint URL
   - Check CORS settings
   - Test API endpoint directly

3. **Styling conflicts**
   - Widget uses high z-index (2147483647)
   - All styles are scoped to avoid conflicts
   - Check for CSS overrides

### Debug Mode
Enable debug logging:
```javascript
window.AutomotiveChatbotConfig = {
  debug: true,
  apiEndpoint: 'https://your-api.com/chat'
};
```

## Support

For technical support or custom integrations:
- Email: support@your-domain.com
- Documentation: https://your-domain.com/docs
- GitHub: https://github.com/your-repo

## Examples

See live examples at:
- Basic Integration: https://your-domain.com/examples/basic
- Custom Styling: https://your-domain.com/examples/styled
- Advanced Features: https://your-domain.com/examples/advanced 