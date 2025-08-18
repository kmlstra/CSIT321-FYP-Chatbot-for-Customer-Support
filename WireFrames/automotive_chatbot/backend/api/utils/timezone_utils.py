"""Timezone utilities for the automotive chatbot API.

Provides centralized timezone handling functions.
"""

from datetime import datetime
import pytz

# Singapore timezone constant
SINGAPORE_TZ = pytz.timezone('Asia/Singapore')

def get_singapore_time() -> datetime:
    """Get current time in Singapore timezone.
    
    Returns:
        datetime: Current time in Singapore timezone
    """
    return datetime.now(SINGAPORE_TZ)

def localize_to_singapore(dt: datetime) -> datetime:
    """Localize a naive datetime to Singapore timezone.
    
    Args:
        dt: Naive datetime object
        
    Returns:
        datetime: Datetime localized to Singapore timezone
    """
    if dt.tzinfo is None:
        return SINGAPORE_TZ.localize(dt)
    return dt.astimezone(SINGAPORE_TZ)

def convert_to_singapore(dt: datetime) -> datetime:
    """Convert a timezone-aware datetime to Singapore timezone.
    
    Args:
        dt: Timezone-aware datetime object
        
    Returns:
        datetime: Datetime converted to Singapore timezone
    """
    return dt.astimezone(SINGAPORE_TZ)