"""Services package for the automotive chatbot API.

This package contains business logic and data services.
"""

from .conversation_service import UnifiedConversationService, MessageType
from .database_pool import get_database_pool, initialize_database_pool, close_database_pool
from .cache_service import get_cache_service, initialize_cache_service, close_cache_service
from .metrics_collector import MetricsCollector
from .notifications import (
    send_it_notification,
    notify_server_down,
    notify_rasa_server_down,
    notify_backend_server_down,
    notify_frontend_server_down,
    notify_database_down,
    notify_coe_api_failure,
    notify_api_failure,
    notify_system_error,
    notify_service_recovery
)

__all__ = [
    'UnifiedConversationService',
    'MessageType',
    'get_database_pool',
    'initialize_database_pool',
    'close_database_pool',
    'get_cache_service',
    'initialize_cache_service',
    'close_cache_service',
    'MetricsCollector',
    'send_it_notification',
    'notify_server_down',
    'notify_rasa_server_down',
    'notify_backend_server_down',
    'notify_frontend_server_down',
    'notify_database_down',
    'notify_coe_api_failure',
    'notify_api_failure',
    'notify_system_error',
    'notify_service_recovery'
]