"""Configuration package for the automotive chatbot backend.

This package contains centralized configuration and database management.
"""

from .database import (
    get_mongodb_client,
    get_database,
    get_collection,
    is_database_connected,
    close_database_connection,
    get_database_info,
    DatabaseContext,
    db_manager
)

__all__ = [
    'get_mongodb_client',
    'get_database', 
    'get_collection',
    'is_database_connected',
    'close_database_connection',
    'get_database_info',
    'DatabaseContext',
    'db_manager'
]