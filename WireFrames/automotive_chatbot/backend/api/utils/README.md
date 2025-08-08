# API Utils Documentation

## 📋 Overview

The `api/utils/` directory contains utility functions and helper modules that provide common functionality across the CleverCompanion automotive chatbot platform. These utilities handle cross-cutting concerns like health monitoring, data visualization, and information processing.

## 🏗️ Utility Architecture

Utilities follow a modular design pattern:

- **Helper Functions:** Reusable functions for common operations
- **Data Processing:** Data transformation and formatting utilities
- **Monitoring Tools:** Health checks and system monitoring
- **Visualization:** Chart and graph generation utilities
- **Information Services:** Data retrieval and processing helpers

## 📁 File Documentation

### 🔧 Core Files

#### `__init__.py`
**Purpose:** Python package initialization and utility exports  
**Function:** 
- Makes utils directory a Python package
- Exports key utility functions and classes
- Handles import organization and convenience imports

**Exports:**
```python
from .health_monitor import HealthMonitor, system_health_check
from .information import InformationService, format_response
from .visualization_utils import ChartGenerator, create_coe_chart
```

---

### 🏥 System Monitoring

#### `health_monitor.py`
**Purpose:** Comprehensive system health monitoring and diagnostics  
**Function:**
- Monitors system resources and service health
- Provides real-time health status reporting
- Handles automated health checks and alerts
- Generates health reports and metrics

**Key Features:**

##### HealthMonitor Class
**Responsibilities:**
- Monitor system resources (CPU, memory, disk)
- Check service availability and response times
- Track database connectivity and performance
- Monitor external API health and rate limits

**Core Methods:**
```python
def check_system_resources(self) -> dict
def check_service_health(self, service_name: str) -> dict
def check_database_connectivity(self) -> dict
def check_external_apis(self) -> dict
def generate_health_report(self) -> dict
def start_continuous_monitoring(self, interval: int = 60) -> None
```

**Health Check Categories:**

##### System Resources
```python
# System resource monitoring
{
    "cpu": {
        "usage_percent": 45.2,
        "cores": 8,
        "status": "healthy"
    },
    "memory": {
        "used_gb": 4.2,
        "total_gb": 16.0,
        "usage_percent": 26.25,
        "status": "healthy"
    },
    "disk": {
        "used_gb": 120.5,
        "total_gb": 500.0,
        "usage_percent": 24.1,
        "status": "healthy"
    }
}
```

##### Service Health
```python
# Service availability monitoring
{
    "rasa_nlu": {
        "url": "http://localhost:5005/status",
        "status": "healthy",
        "response_time_ms": 45,
        "last_check": "2025-01-30T20:56:16+08:00"
    },
    "rasa_actions": {
        "url": "http://localhost:5055/health",
        "status": "healthy",
        "response_time_ms": 23,
        "last_check": "2025-01-30T20:56:16+08:00"
    },
    "mongodb": {
        "status": "healthy",
        "connection_count": 5,
        "response_time_ms": 12,
        "last_check": "2025-01-30T20:56:16+08:00"
    }
}
```

##### External API Health
```python
# External service monitoring
{
    "lta_api": {
        "status": "healthy",
        "rate_limit_remaining": 850,
        "rate_limit_reset": "2025-01-30T21:00:00+08:00",
        "response_time_ms": 234,
        "last_successful_call": "2025-01-30T20:55:30+08:00"
    },
    "whatsapp_api": {
        "status": "healthy",
        "quota_remaining": 9500,
        "response_time_ms": 156,
        "last_successful_call": "2025-01-30T20:54:12+08:00"
    }
}
```

**Monitoring Features:**
- **Real-time Monitoring:** Continuous health checks
- **Threshold Alerts:** Configurable warning and critical thresholds
- **Historical Tracking:** Health metrics over time
- **Automated Recovery:** Self-healing capabilities where possible
- **Dashboard Integration:** Health status visualization

**Configuration:**
```python
# Health monitoring configuration
HEALTH_CHECK_INTERVAL = 60  # seconds
CPU_WARNING_THRESHOLD = 80  # percent
CPU_CRITICAL_THRESHOLD = 95  # percent
MEMORY_WARNING_THRESHOLD = 85  # percent
MEMORY_CRITICAL_THRESHOLD = 95  # percent
DISK_WARNING_THRESHOLD = 80  # percent
DISK_CRITICAL_THRESHOLD = 90  # percent
RESPONSE_TIME_WARNING = 1000  # milliseconds
RESPONSE_TIME_CRITICAL = 5000  # milliseconds
```

---

### 📊 Data Visualization

#### `visualization_utils.py`
**Purpose:** Chart and graph generation for data visualization  
**Function:**
- Creates interactive charts and graphs
- Generates COE price trend visualizations
- Provides conversation analytics charts
- Handles data formatting for visualization

**Key Features:**

##### ChartGenerator Class
**Responsibilities:**
- Generate various chart types (line, bar, pie, scatter)
- Create interactive visualizations with hover effects
- Export charts in multiple formats (PNG, SVG, HTML)
- Handle responsive design for different screen sizes

**Core Methods:**
```python
def create_line_chart(self, data: dict, title: str, x_label: str, y_label: str) -> str
def create_bar_chart(self, data: dict, title: str, orientation: str = "vertical") -> str
def create_pie_chart(self, data: dict, title: str) -> str
def create_coe_trend_chart(self, coe_data: List[dict], categories: List[str]) -> str
def create_conversation_analytics_chart(self, analytics_data: dict) -> str
def export_chart(self, chart_html: str, format: str = "png") -> bytes
```

**Chart Types:**

##### COE Price Trends
```python
# COE price trend visualization
coe_chart_config = {
    "type": "line",
    "data": {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
        "datasets": [
            {
                "label": "Category A",
                "data": [95000, 98000, 101000, 99000, 101102],
                "borderColor": "#FF6384",
                "backgroundColor": "rgba(255, 99, 132, 0.2)"
            },
            {
                "label": "Category B", 
                "data": [110000, 115000, 120000, 118000, 119101],
                "borderColor": "#36A2EB",
                "backgroundColor": "rgba(54, 162, 235, 0.2)"
            }
        ]
    },
    "options": {
        "responsive": True,
        "plugins": {
            "title": {
                "display": True,
                "text": "COE Price Trends - 6 Months"
            }
        },
        "scales": {
            "y": {
                "beginAtZero": False,
                "title": {
                    "display": True,
                    "text": "Price (SGD)"
                }
            }
        }
    }
}
```

##### Conversation Analytics
```python
# Conversation analytics visualization
analytics_chart_config = {
    "type": "bar",
    "data": {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "datasets": [
            {
                "label": "Conversations",
                "data": [45, 52, 38, 67, 73, 29, 31],
                "backgroundColor": "rgba(75, 192, 192, 0.6)",
                "borderColor": "rgba(75, 192, 192, 1)",
                "borderWidth": 1
            }
        ]
    },
    "options": {
        "responsive": True,
        "plugins": {
            "title": {
                "display": True,
                "text": "Daily Conversation Volume"
            }
        }
    }
}
```

**Visualization Libraries:**
- **Chart.js:** Interactive web charts
- **Plotly:** Advanced statistical charts
- **D3.js:** Custom data visualizations
- **Matplotlib:** Static chart generation

**Export Formats:**
- **HTML:** Interactive web charts
- **PNG:** Static image export
- **SVG:** Vector graphics
- **PDF:** Print-ready reports

---

### 📋 Information Processing

#### `information.py`
**Purpose:** Information retrieval, processing, and formatting utilities  
**Function:**
- Processes and formats response data
- Handles information extraction and transformation
- Provides data validation and sanitization
- Manages content formatting for different channels

**Key Features:**

##### InformationService Class
**Responsibilities:**
- Format responses for different output channels
- Extract and process information from various sources
- Validate and sanitize user input and system data
- Handle content localization and personalization

**Core Methods:**
```python
def format_response(self, data: dict, format_type: str = "text") -> str
def extract_entities(self, text: str) -> dict
def validate_input(self, input_data: dict, schema: dict) -> bool
def sanitize_content(self, content: str) -> str
def localize_content(self, content: str, language: str = "en") -> str
def personalize_response(self, template: str, user_data: dict) -> str
```

**Response Formatting:**

##### Text Formatting
```python
# Text response formatting
def format_coe_response(coe_data: dict) -> str:
    response = "📊 **Latest COE Prices (Live Data)**\n\n"
    
    for category, data in coe_data['categories'].items():
        trend_icon = "↗️" if data['change'] > 0 else "↘️" if data['change'] < 0 else "↔️"
        response += f"🚗 **Category {category}:** ${data['price']:,} {trend_icon} "
        
        if data['change'] != 0:
            response += f"${data['change']:+,}\n"
        else:
            response += "No change\n"
    
    return response
```

##### HTML Formatting
```python
# HTML response formatting
def format_coe_html(coe_data: dict) -> str:
    html = "<div class='coe-prices'>\n"
    html += "<h3>📊 Latest COE Prices</h3>\n"
    html += "<table class='price-table'>\n"
    
    for category, data in coe_data['categories'].items():
        trend_class = "up" if data['change'] > 0 else "down" if data['change'] < 0 else "stable"
        html += f"<tr class='{trend_class}'>\n"
        html += f"<td>Category {category}</td>\n"
        html += f"<td>${data['price']:,}</td>\n"
        html += f"<td>{data['change']:+,}</td>\n"
        html += "</tr>\n"
    
    html += "</table>\n</div>"
    return html
```

##### JSON API Formatting
```python
# JSON API response formatting
def format_coe_json(coe_data: dict) -> dict:
    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "coe_prices": coe_data['categories'],
            "pqp_prices": coe_data['pqp'],
            "period": coe_data['period'],
            "last_updated": coe_data['timestamp']
        },
        "metadata": {
            "source": "LTA Singapore",
            "currency": "SGD",
            "timezone": "Asia/Singapore"
        }
    }
```

**Data Validation:**
```python
# Input validation schemas
validation_schemas = {
    "coe_query": {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
            "period": {"type": "string", "pattern": "^\\d{4}-\\d{2}$"},
            "format": {"type": "string", "enum": ["text", "html", "json"]}
        },
        "required": []
    },
    "contact_form": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 2, "maxLength": 100},
            "email": {"type": "string", "format": "email"},
            "phone": {"type": "string", "pattern": "^\\+?[1-9]\\d{1,14}$"},
            "message": {"type": "string", "minLength": 10, "maxLength": 1000}
        },
        "required": ["name", "email", "message"]
    }
}
```

**Content Sanitization:**
```python
# Content sanitization functions
def sanitize_html(content: str) -> str:
    """Remove potentially dangerous HTML tags and attributes."""
    allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3']
    return bleach.clean(content, tags=allowed_tags, strip=True)

def sanitize_user_input(input_text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove SQL injection patterns
    sql_patterns = [r"';\s*--", r"\bunion\b", r"\bselect\b", r"\bdrop\b"]
    for pattern in sql_patterns:
        input_text = re.sub(pattern, "", input_text, flags=re.IGNORECASE)
    
    # Remove script tags
    input_text = re.sub(r"<script.*?</script>", "", input_text, flags=re.IGNORECASE | re.DOTALL)
    
    return input_text.strip()
```

---

## 🔄 Utility Integration

### Cross-Utility Communication
```python
# Example: Health monitoring with visualization
class SystemDashboard:
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.chart_generator = ChartGenerator()
        self.info_service = InformationService()
    
    def generate_health_dashboard(self) -> str:
        # Get health data
        health_data = self.health_monitor.generate_health_report()
        
        # Create visualizations
        cpu_chart = self.chart_generator.create_line_chart(
            health_data['cpu_history'], "CPU Usage", "Time", "Percentage"
        )
        
        # Format for display
        dashboard_html = self.info_service.format_response(
            {"health_data": health_data, "charts": [cpu_chart]},
            format_type="html"
        )
        
        return dashboard_html
```

### Utility Composition
```python
# Composing utilities for complex operations
class ReportGenerator:
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.chart_generator = ChartGenerator()
        self.info_service = InformationService()
    
    def generate_daily_report(self) -> dict:
        # Collect data from multiple sources
        health_data = self.health_monitor.generate_health_report()
        conversation_data = self.get_conversation_analytics()
        coe_data = self.get_coe_analytics()
        
        # Generate visualizations
        charts = {
            "health": self.chart_generator.create_health_chart(health_data),
            "conversations": self.chart_generator.create_conversation_analytics_chart(conversation_data),
            "coe_trends": self.chart_generator.create_coe_trend_chart(coe_data)
        }
        
        # Format report
        report = self.info_service.format_response(
            {"data": {"health": health_data, "conversations": conversation_data, "coe": coe_data},
             "charts": charts},
            format_type="html"
        )
        
        return report
```

## 📊 Performance & Monitoring

### Utility Metrics
```python
# Performance monitoring for utilities
metrics = {
    "health_monitor": {
        "checks_per_minute": health_monitor.get_check_rate(),
        "average_check_time": health_monitor.get_average_check_time(),
        "failed_checks": health_monitor.get_failed_check_count()
    },
    "visualization": {
        "charts_generated_today": chart_generator.get_daily_chart_count(),
        "average_generation_time": chart_generator.get_average_generation_time(),
        "cache_hit_rate": chart_generator.get_cache_hit_rate()
    },
    "information_service": {
        "responses_formatted_today": info_service.get_daily_format_count(),
        "validation_success_rate": info_service.get_validation_success_rate(),
        "sanitization_events": info_service.get_sanitization_count()
    }
}
```

## 🛠️ Development Guidelines

### Adding New Utilities

1. **Create Utility Module:**
```python
class NewUtility:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def utility_function(self, input_data: Any) -> Any:
        """Main utility function with proper error handling."""
        try:
            # Implementation here
            result = self.process_data(input_data)
            return result
        except Exception as e:
            self.logger.error(f"Utility function failed: {e}")
            raise
```

2. **Add to __init__.py:** Export for easy importing
3. **Add Tests:** Unit tests with edge cases
4. **Add Documentation:** Function and class documentation
5. **Add Configuration:** Environment variables if needed

### Best Practices

- **Pure Functions:** Prefer stateless utility functions
- **Error Handling:** Comprehensive error handling and logging
- **Performance:** Optimize for common use cases
- **Caching:** Cache expensive operations where appropriate
- **Testing:** Unit tests with high coverage
- **Documentation:** Clear docstrings and examples

## 🔗 Dependencies

- **psutil:** System resource monitoring
- **requests/httpx:** HTTP client for health checks
- **chart.js/plotly:** Chart generation libraries
- **bleach:** HTML sanitization
- **jsonschema:** Data validation
- **Pillow:** Image processing for chart export

---

**Last Updated:** January 2025  
**Maintainer:** CleverCompanion Development Team  
**Version:** 2.0 (with enhanced monitoring and visualization)