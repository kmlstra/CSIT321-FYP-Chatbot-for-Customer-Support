# CleverCompanion Widget Configuration Guide

## Backend URL Configuration

The CleverCompanion widget uses **universal backend URL detection** to serve SVG arrow indicators and other static assets. This means the widget will automatically detect the appropriate backend URL based on your deployment environment.

### Automatic Detection

By default, the widget will:
1. **Development**: Use `http://localhost:8000` when running locally
2. **Production**: Auto-detect from current domain and use port 8000
3. **Custom**: Use manually configured URL if provided

### Manual Configuration

To manually configure the backend URL, set the global variable **before** loading the widget:

```html
<!-- Configure backend URL for CleverCompanion Widget -->
<script>
    // Development Environment
    window.CLEVERCOMPANION_BACKEND_URL = 'http://localhost:8000';
    
    // Production Environment
    window.CLEVERCOMPANION_BACKEND_URL = 'https://your-backend-domain.com';
    
    // Custom API Domain
    window.CLEVERCOMPANION_BACKEND_URL = 'https://api.yourcompany.com';
    
    // Different Port
    window.CLEVERCOMPANION_BACKEND_URL = 'http://localhost:3001';
</script>

<!-- Load the widget -->
<script src="clevercompanion-widget.js"></script>
```

### Environment-Specific Examples

#### Local Development
```html
<script>
    window.CLEVERCOMPANION_BACKEND_URL = 'http://localhost:8000';
</script>
<script src="clevercompanion-widget.js"></script>
```

#### Production (Same Domain)
```html
<script>
    window.CLEVERCOMPANION_BACKEND_URL = 'https://yourwebsite.com:8000';
</script>
<script src="clevercompanion-widget.js"></script>
```

#### Production (API Subdomain)
```html
<script>
    window.CLEVERCOMPANION_BACKEND_URL = 'https://api.yourwebsite.com';
</script>
<script src="clevercompanion-widget.js"></script>
```

#### Docker/Container Deployment
```html
<script>
    window.CLEVERCOMPANION_BACKEND_URL = 'http://chatbot-backend:8000';
</script>
<script src="clevercompanion-widget.js"></script>
```

### PNG Arrow Indicators

The widget serves professional PNG arrow indicators from the backend:

- **Up Arrow (Red)**: `{backend_url}/static/media/arrow_indicator/up_arrow_red.png`
- **Down Arrow (Green)**: `{backend_url}/static/media/arrow_indicator/down_arrow_green.png`
- **No Change (Grey)**: `{backend_url}/static/media/arrow_indicator/no_change_grey.png`

### Verification

To verify your configuration is working:

1. **Check Console**: Open browser DevTools → Console
2. **Test Backend**: Visit `{your_backend_url}/health` 
3. **Test PNG**: Visit `{your_backend_url}/static/media/arrow_indicator/up_arrow_red.png`

Example verification URLs:
- Backend Health: `http://localhost:8000/health`
- PNG Test: `http://localhost:8000/static/media/arrow_indicator/up_arrow_red.png`

### Troubleshooting

#### PNG Not Found Errors
- Ensure backend server is running
- Check that static files are properly mounted
- Verify `CLEVERCOMPANION_BACKEND_URL` is set correctly

#### CORS Issues
- Ensure backend allows requests from your domain
- Check FastAPI CORS middleware configuration

#### Port Issues
- Verify backend is running on expected port
- Check firewall settings
- Ensure port is not blocked by proxy/load balancer

### Advanced Configuration

For complex deployments, you can override the detection function:

```javascript
// Override detection logic
window.CLEVERCOMPANION_BACKEND_URL = (function() {
    // Your custom detection logic
    if (window.location.hostname === 'localhost') {
        return 'http://localhost:8000';
    } else if (window.location.hostname.includes('staging')) {
        return 'https://staging-api.yourcompany.com';
    } else {
        return 'https://api.yourcompany.com';
    }
})();
```

This approach ensures the widget works seamlessly across different environments without hardcoded URLs.