# CleverCompanion Chatbot Widget

A standalone, embeddable chatbot widget for automotive assistance in Singapore.

## 🚀 Quick Start

Add the CleverCompanion chatbot to any website with just 2 lines of code:

```html
<link rel="stylesheet" href="clevercompanion-widget.css">
<script src="clevercompanion-widget.js"></script>
```

The widget will automatically initialize and appear on your page.

## 📁 Files

- `clevercompanion-widget.js` - Main widget JavaScript (self-contained)
- `clevercompanion-widget.css` - Widget styles (separate for easy customization)
- `embed-example.html` - Complete embedding example with demos

## ✨ Features

- 🎨 Modern, responsive design
- 📱 Mobile-friendly interface
- 🤖 AI-powered automotive assistance
- 💰 Real-time COE prices
- 🚗 Vehicle recommendations
- 🔧 Maintenance scheduling
- 💳 Loan calculations
- 📞 Contact integration
- ⚡ Fast and lightweight (~50KB total)
- 🔧 Easy to customize

## 🛠️ API Usage

### Basic Initialization

```javascript
// Widget auto-initializes, but you can configure it:
CleverCompanionWidget.init({
    title: "Your Custom Title",
    subtitle: "Your Custom Subtitle",
    apiUrl: "https://your-api-endpoint.com",
    primaryColor: "#4F46E5",
    welcomeMessage: "Hello! How can I help you?"
});
```

### Programmatic Control

```javascript
// Open the chat widget
CleverCompanionWidget.open();

// Close the chat widget
CleverCompanionWidget.close();

// Send a message programmatically
CleverCompanionWidget.sendMessage("Show me COE prices");

// Configure widget settings
CleverCompanionWidget.configure({
    title: "New Title",
    subtitle: "New Subtitle"
});
```

## 🎨 Customization

### CSS Customization

The widget uses a separate CSS file (`clevercompanion-widget.css`) for easy customization. All styles are prefixed with `.cc-` to avoid conflicts.

Key CSS classes:
- `.cc-chatbot-container` - Main widget container
- `.cc-chatbot-header` - Header section
- `.cc-chatbot-messages` - Messages area
- `.cc-chatbot-input` - Input field
- `.cc-chatbot-toggle` - Toggle button

### Color Scheme

Default colors can be customized by modifying the CSS variables or overriding specific classes:

```css
.cc-chatbot-header {
    background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
}
```

## 🔧 Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | "CleverCompanion" | Widget title |
| `subtitle` | string | "Your AI Automotive Assistant" | Widget subtitle |
| `apiUrl` | string | "http://localhost:5005/webhooks/rest/webhook" | RASA API endpoint |
| `primaryColor` | string | "#4F46E5" | Primary color |
| `secondaryColor` | string | "#7C3AED" | Secondary color |
| `accentColor` | string | "#10B981" | Accent color |
| `welcomeMessage` | string | Default welcome message | Initial bot message |
| `showQuickActions` | boolean | true | Show quick action menu |

## 📱 Responsive Design

The widget is fully responsive and adapts to different screen sizes:

- **Desktop**: Fixed position widget (420px × 650px)
- **Mobile**: Full-screen overlay for better usability
- **Tablet**: Optimized sizing for touch interaction

## 🌐 Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🔒 Security Features

- XSS protection through content sanitization
- CORS-compliant API requests
- No external dependencies (security through isolation)
- CSP-friendly implementation

## 🚀 Performance

- **Size**: ~50KB total (JS + CSS)
- **Load time**: <100ms on modern browsers
- **Memory usage**: <5MB typical
- **No external dependencies**: Zero third-party libraries

## 🔌 Integration Examples

### WordPress

```php
// Add to your theme's functions.php
function add_clevercompanion_widget() {
    wp_enqueue_style('clevercompanion-css', 'path/to/clevercompanion-widget.css');
    wp_enqueue_script('clevercompanion-js', 'path/to/clevercompanion-widget.js');
}
add_action('wp_enqueue_scripts', 'add_clevercompanion_widget');
```

### React

```jsx
import { useEffect } from 'react';

function App() {
    useEffect(() => {
        // Load CSS
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/clevercompanion-widget.css';
        document.head.appendChild(link);

        // Load JS
        const script = document.createElement('script');
        script.src = '/clevercompanion-widget.js';
        document.body.appendChild(script);

        return () => {
            document.head.removeChild(link);
            document.body.removeChild(script);
        };
    }, []);

    return <div>Your React App</div>;
}
```

### Vue.js

```vue
<template>
    <div>Your Vue App</div>
</template>

<script>
export default {
    mounted() {
        // Load CSS
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/clevercompanion-widget.css';
        document.head.appendChild(link);

        // Load JS
        const script = document.createElement('script');
        script.src = '/clevercompanion-widget.js';
        document.body.appendChild(script);
    }
}
</script>
```

## 🐛 Troubleshooting

### Widget not appearing
- Check console for JavaScript errors
- Ensure CSS file is loaded correctly
- Verify API endpoint is accessible

### Styling conflicts
- All widget styles are prefixed with `.cc-`
- Use CSS specificity to override if needed
- Check for conflicting z-index values

### API connection issues
- Verify RASA backend is running
- Check CORS configuration
- Ensure API URL is correct

## 📞 Support

For technical support or feature requests:
- Email: support@clevercompanion.sg
- Documentation: See embed-example.html for live demos
- Issues: Check browser console for error messages

## 📄 License

© 2024 CleverCompanion. All rights reserved. 