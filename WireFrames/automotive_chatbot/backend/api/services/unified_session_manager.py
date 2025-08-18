"""Unified Session Manager
Centralized session management system that unifies frontend and backend session handling.
This manager ensures consistent session lifecycle across the entire application.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging
import pytz
from enum import Enum

# Import from config directory using relative import
from ..config.database import DatabaseContext

# Configure logger
logger = logging.getLogger('api.services.unified_session_manager')

class SessionStatus(Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALID = "invalid"

class UnifiedSessionManager:
    """Unified session management system.
    
    This class provides centralized session management that:
    1. Unifies frontend localStorage and backend MongoDB session handling
    2. Ensures consistent session expiry across all components
    3. Prevents session conflicts and duplication
    4. Maintains session persistence throughout the conversation lifecycle
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        """Initialize the unified session manager.
        
        Args:
            session_timeout_minutes: Session timeout in minutes (default: 30)
        """
        self.session_timeout_minutes = session_timeout_minutes
        # Use UTC to avoid timezone issues
        self.timezone = timezone.utc
        self._setup_collections()
        logger.info(f"[UNIFIED_SESSION] Initialized with {session_timeout_minutes} minute timeout")
    
    def _setup_collections(self):
        """Setup MongoDB collections with optimized indexes for session management."""
        try:
            # Setup unified_sessions collection with comprehensive indexes
            with DatabaseContext('unified_sessions') as sessions:
                if not sessions:
                    logger.info("[UNIFIED_SESSION] MongoDB not available, skipping collection setup")
                    return
                
                # Create optimized indexes for session management
                try:
                    # Primary index on session_id (unique)
                    sessions.create_index([('session_id', 1)], unique=True, background=True)
                    # Index for expiry cleanup and active session queries
                    sessions.create_index([('expires_at', 1)], background=True)
                    # Index for client-based queries
                    sessions.create_index([('client_id', 1)], background=True)
                    # Compound index for active sessions by client
                    sessions.create_index([('client_id', 1), ('expires_at', 1)], background=True)
                    # Index for analytics and monitoring
                    sessions.create_index([('created_at', 1)], background=True)
                    # Index for conversation tracking
                    sessions.create_index([('conversation_id', 1)], background=True)
                    
                    logger.info("[UNIFIED_SESSION] MongoDB indexes created successfully")
                except Exception as e:
                    logger.warning(f"[UNIFIED_SESSION] Index creation warning: {e}")
                    
        except Exception as e:
            logger.error(f"[UNIFIED_SESSION] Failed to setup collections: {e}")
    
    def create_session(self, client_id: str, user_id: Optional[str] = None, 
                      metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """Create a new unified session.
        
        Args:
            client_id: Client identifier (required for multi-tenant support)
            user_id: Optional user identifier
            metadata: Additional session metadata
            
        Returns:
            Tuple[session_id, conversation_id]: Session and conversation identifiers
        """
        session_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        
        logger.info(f"[UNIFIED_SESSION] Creating session - session_id: {session_id}, client_id: {client_id}")
        
        current_time = datetime.now(self.timezone)
        expires_at = current_time + timedelta(minutes=self.session_timeout_minutes)
        
        session_data = {
            'session_id': session_id,
            'conversation_id': conversation_id,
            'client_id': client_id,
            'user_id': user_id,
            'status': SessionStatus.ACTIVE.value,
            'created_at': current_time,
            'last_activity': current_time,
            'expires_at': expires_at,
            'message_count': 0,
            'metadata': metadata or {},
            'frontend_sync': True,  # Flag to indicate frontend synchronization needed
            'backend_sync': True    # Flag to indicate backend synchronization status
        }
        
        with DatabaseContext('unified_sessions') as sessions:
            if sessions:
                try:
                    result = sessions.insert_one(session_data)
                    logger.info(f"[UNIFIED_SESSION] Session created successfully - session_id: {session_id}, conversation_id: {conversation_id}")
                except Exception as e:
                    logger.error(f"[UNIFIED_SESSION] Failed to create session: {e}")
                    raise Exception(f"Database error during session creation: {e}")
            else:
                logger.error(f"[UNIFIED_SESSION] MongoDB not available, cannot create session")
                raise Exception("Database connection failed - cannot create session")
        
        return session_id, conversation_id
    
    def validate_session(self, session_id: str) -> Tuple[SessionStatus, Optional[Dict]]:
        """Validate session and return status with session data.
        
        Args:
            session_id: Session identifier to validate
            
        Returns:
            Tuple[SessionStatus, session_data]: Status and session data if valid
        """
        logger.debug(f"[UNIFIED_SESSION] Validating session: {session_id}")
        
        if not session_id or session_id.strip() == '':
            logger.warning(f"[UNIFIED_SESSION] Invalid session_id provided: {session_id}")
            return SessionStatus.INVALID, None
        
        with DatabaseContext('unified_sessions') as sessions:
            if not sessions:
                logger.warning(f"[UNIFIED_SESSION] MongoDB not available for validation")
                return SessionStatus.INVALID, None
            
            try:
                session_data = sessions.find_one({'session_id': session_id})
                
                if not session_data:
                    logger.info(f"[UNIFIED_SESSION] Session not found: {session_id}")
                    return SessionStatus.INVALID, None
                
                current_time = datetime.now(self.timezone)
                expires_at = session_data.get('expires_at')
                
                # Handle timezone-aware comparison
                if expires_at:
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=self.timezone)
                    elif expires_at.tzinfo != self.timezone:
                        expires_at = expires_at.astimezone(self.timezone)
                
                if expires_at and current_time > expires_at:
                    logger.info(f"[UNIFIED_SESSION] Session expired: {session_id}")
                    # Mark session as expired
                    sessions.update_one(
                        {'session_id': session_id},
                        {'$set': {'status': SessionStatus.EXPIRED.value}}
                    )
                    return SessionStatus.EXPIRED, session_data
                
                logger.debug(f"[UNIFIED_SESSION] Session valid: {session_id}")
                return SessionStatus.ACTIVE, session_data
                
            except Exception as e:
                logger.error(f"[UNIFIED_SESSION] Error validating session {session_id}: {e}")
                return SessionStatus.INVALID, None
    
    def extend_session(self, session_id: str, activity_metadata: Optional[Dict] = None) -> bool:
        """Extend session expiry and update activity.
        
        Args:
            session_id: Session identifier
            activity_metadata: Optional metadata about the activity
            
        Returns:
            bool: True if session was extended successfully
        """
        logger.debug(f"[UNIFIED_SESSION] Extending session: {session_id}")
        
        status, session_data = self.validate_session(session_id)
        
        if status != SessionStatus.ACTIVE:
            logger.warning(f"[UNIFIED_SESSION] Cannot extend inactive session: {session_id}")
            return False
        
        current_time = datetime.now(self.timezone)
        new_expires_at = current_time + timedelta(minutes=self.session_timeout_minutes)
        
        update_data = {
            'last_activity': current_time,
            'expires_at': new_expires_at,
            'status': SessionStatus.ACTIVE.value
        }
        
        # Add activity metadata if provided
        if activity_metadata:
            update_data['last_activity_metadata'] = activity_metadata
        
        with DatabaseContext('unified_sessions') as sessions:
            if not sessions:
                logger.warning(f"[UNIFIED_SESSION] MongoDB not available for extension")
                return False
            
            try:
                result = sessions.update_one(
                    {'session_id': session_id},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    logger.info(f"[UNIFIED_SESSION] Session extended successfully: {session_id}")
                    return True
                else:
                    logger.error(f"[UNIFIED_SESSION] Failed to extend session: {session_id}")
                    return False
                    
            except Exception as e:
                logger.error(f"[UNIFIED_SESSION] Error extending session {session_id}: {e}")
                return False
    
    def increment_message_count(self, session_id: str) -> bool:
        """Increment message count for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if count was incremented successfully
        """
        with DatabaseContext('unified_sessions') as sessions:
            if not sessions:
                return False
            
            try:
                result = sessions.update_one(
                    {'session_id': session_id},
                    {'$inc': {'message_count': 1}}
                )
                return result.modified_count > 0
            except Exception as e:
                logger.error(f"[UNIFIED_SESSION] Error incrementing message count for {session_id}: {e}")
                return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        logger.debug(f"[UNIFIED_SESSION] Getting session info: {session_id}")
        
        with DatabaseContext('unified_sessions') as sessions:
            if not sessions:
                return None
            
            try:
                session_data = sessions.find_one(
                    {'session_id': session_id},
                    {'_id': 0}  # Exclude MongoDB _id
                )
                
                if session_data:
                    # Convert datetime fields to ISO strings for JSON serialization
                    for field in ['created_at', 'last_activity', 'expires_at']:
                        if field in session_data and isinstance(session_data[field], datetime):
                            if session_data[field].tzinfo is None:
                                session_data[field] = session_data[field].replace(tzinfo=self.timezone)
                            session_data[field] = session_data[field].isoformat()
                    
                    logger.debug(f"[UNIFIED_SESSION] Session info retrieved: {session_id}")
                    return session_data
                
                return None
                
            except Exception as e:
                logger.error(f"[UNIFIED_SESSION] Error getting session info for {session_id}: {e}")
                return None
    
    def get_conversation_id(self, session_id: str) -> Optional[str]:
        """Get conversation ID for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation ID or None if session not found
        """
        session_info = self.get_session_info(session_id)
        return session_info.get('conversation_id') if session_info else None
    
    def ensure_session_exists(self, session_id: str, client_id: str, user_id: Optional[str] = None) -> Tuple[str, str]:
        """Ensure session exists, create if not found (for frontend compatibility).
        
        This method handles frontend-generated session IDs that may not exist in the database.
        If the session doesn't exist, it creates a new session record using the provided session_id.
        If the session exists but is expired/invalid, it reactivates it.
        
        Args:
            session_id: Session identifier (can be frontend-generated format)
            client_id: Client identifier
            user_id: Optional user identifier
            
        Returns:
            Tuple[session_id, conversation_id]: Session and conversation identifiers
        """
        logger.debug(f"[UNIFIED_SESSION] Ensuring session exists: {session_id}")
        
        # First check if session already exists
        status, existing_session_data = self.validate_session(session_id)
        
        if status == SessionStatus.ACTIVE and existing_session_data:
            logger.debug(f"[UNIFIED_SESSION] Session already active: {session_id}")
            return session_id, existing_session_data.get('conversation_id')
        
        # Check if session exists but is expired/invalid
        with DatabaseContext('unified_sessions') as sessions:
            if not sessions:
                logger.error(f"[UNIFIED_SESSION] MongoDB not available, cannot ensure session")
                raise Exception("Database connection failed - cannot ensure session")
            
            try:
                existing_session = sessions.find_one({'session_id': session_id})
                
                current_time = datetime.now(self.timezone)
                expires_at = current_time + timedelta(minutes=self.session_timeout_minutes)
                
                if existing_session:
                    # Session exists but is expired/invalid, reactivate it
                    logger.info(f"[UNIFIED_SESSION] Reactivating existing session: {session_id}")
                    conversation_id = existing_session.get('conversation_id')
                    
                    # If no conversation_id exists, create a new one
                    if not conversation_id:
                        conversation_id = str(uuid.uuid4())
                    
                    # Update session to active status
                    update_data = {
                        'status': SessionStatus.ACTIVE.value,
                        'last_activity': current_time,
                        'expires_at': expires_at,
                        'client_id': client_id,  # Update client_id in case it changed
                        'user_id': user_id,
                        'frontend_sync': True,
                        'backend_sync': True
                    }
                    
                    # Add conversation_id if it was missing
                    if not existing_session.get('conversation_id'):
                        update_data['conversation_id'] = conversation_id
                    
                    result = sessions.update_one(
                        {'session_id': session_id},
                        {'$set': update_data}
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"[UNIFIED_SESSION] Session reactivated successfully - session_id: {session_id}, conversation_id: {conversation_id}")
                        return session_id, conversation_id
                    else:
                        logger.error(f"[UNIFIED_SESSION] Failed to reactivate session: {session_id}")
                        raise Exception(f"Failed to reactivate session: {session_id}")
                else:
                    # Session doesn't exist, create new one
                    logger.info(f"[UNIFIED_SESSION] Creating new session with frontend ID: {session_id}")
                    
                    conversation_id = str(uuid.uuid4())
                    
                    session_data = {
                        'session_id': session_id,  # Use the frontend-provided session_id
                        'conversation_id': conversation_id,
                        'client_id': client_id,
                        'user_id': user_id,
                        'status': SessionStatus.ACTIVE.value,
                        'created_at': current_time,
                        'last_activity': current_time,
                        'expires_at': expires_at,
                        'message_count': 0,
                        'metadata': {'source': 'frontend_widget', 'format': 'timestamp_random'},
                        'frontend_sync': True,
                        'backend_sync': True
                    }
                    
                    result = sessions.insert_one(session_data)
                    
                    if result.inserted_id:
                        logger.info(f"[UNIFIED_SESSION] New session created successfully - session_id: {session_id}, conversation_id: {conversation_id}")
                        return session_id, conversation_id
                    else:
                        logger.error(f"[UNIFIED_SESSION] Failed to create session: {session_id}")
                        raise Exception(f"Failed to create session: {session_id}")
                        
            except Exception as e:
                logger.error(f"[UNIFIED_SESSION] Error ensuring session {session_id}: {e}")
                raise Exception(f"Database error during session creation: {e}")
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        logger.info("[UNIFIED_SESSION] Starting cleanup of expired sessions")
        
        current_time = datetime.now(self.timezone)
        
        with DatabaseContext('unified_sessions') as sessions:
            if not sessions:
                return 0
            
            try:
                # First mark expired sessions
                mark_result = sessions.update_many(
                    {
                        'expires_at': {'$lt': current_time},
                        'status': {'$ne': SessionStatus.EXPIRED.value}
                    },
                    {'$set': {'status': SessionStatus.EXPIRED.value}}
                )
                
                # Then delete sessions expired more than 24 hours ago
                cleanup_cutoff = current_time - timedelta(hours=24)
                delete_result = sessions.delete_many({
                    'expires_at': {'$lt': cleanup_cutoff},
                    'status': SessionStatus.EXPIRED.value
                })
                
                total_cleaned = mark_result.modified_count + delete_result.deleted_count
                logger.info(f"[UNIFIED_SESSION] Cleanup completed: {mark_result.modified_count} marked expired, {delete_result.deleted_count} deleted")
                
                return total_cleaned
                
            except Exception as e:
                logger.error(f"[UNIFIED_SESSION] Error during cleanup: {e}")
                return 0
    
    def get_active_sessions_by_client(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a specific client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of active session data
        """
        logger.debug(f"[UNIFIED_SESSION] Getting active sessions for client: {client_id}")
        
        current_time = datetime.now(self.timezone)
        
        with DatabaseContext('unified_sessions') as sessions:
            if not sessions:
                return []
            
            try:
                active_sessions = list(sessions.find(
                    {
                        'client_id': client_id,
                        'expires_at': {'$gt': current_time},
                        'status': SessionStatus.ACTIVE.value
                    },
                    {'_id': 0}
                ))
                
                # Convert datetime fields for JSON serialization
                for session in active_sessions:
                    for field in ['created_at', 'last_activity', 'expires_at']:
                        if field in session and isinstance(session[field], datetime):
                            if session[field].tzinfo is None:
                                session[field] = session[field].replace(tzinfo=self.timezone)
                            session[field] = session[field].isoformat()
                
                logger.info(f"[UNIFIED_SESSION] Found {len(active_sessions)} active sessions for client {client_id}")
                return active_sessions
                
            except Exception as e:
                logger.error(f"[UNIFIED_SESSION] Error getting active sessions for client {client_id}: {e}")
                return []
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics for monitoring.
        
        Returns:
            Dictionary containing session statistics
        """
        logger.debug("[UNIFIED_SESSION] Getting session statistics")
        
        current_time = datetime.now(self.timezone)
        
        with DatabaseContext('unified_sessions') as sessions:
            if not sessions:
                return {'error': 'MongoDB not available'}
            
            try:
                # Count active sessions
                active_count = sessions.count_documents({
                    'expires_at': {'$gt': current_time},
                    'status': SessionStatus.ACTIVE.value
                })
                
                # Count expired sessions
                expired_count = sessions.count_documents({
                    'status': SessionStatus.EXPIRED.value
                })
                
                # Count total sessions
                total_count = sessions.count_documents({})
                
                # Get sessions created in last 24 hours
                last_24h = current_time - timedelta(hours=24)
                recent_count = sessions.count_documents({
                    'created_at': {'$gt': last_24h}
                })
                
                stats = {
                    'active_sessions': active_count,
                    'expired_sessions': expired_count,
                    'total_sessions': total_count,
                    'recent_sessions_24h': recent_count,
                    'timestamp': current_time.isoformat()
                }
                
                logger.info(f"[UNIFIED_SESSION] Session statistics: {stats}")
                return stats
                
            except Exception as e:
                logger.error(f"[UNIFIED_SESSION] Error getting session statistics: {e}")
                return {'error': str(e)}

# Global instance
unified_session_manager = UnifiedSessionManager()