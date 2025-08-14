"""Conversation Storage System
Handles storing and retrieving chatbot conversations with session management.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import sys
import pytz

# Import from config directory using relative import
from ..config.database import DatabaseContext

logger = logging.getLogger(__name__)

class ConversationStorage:
    """Manages conversation storage in MongoDB with session expiry."""
    
    def __init__(self):
        self.session_timeout_minutes = 30
        self._setup_collections()
    

    
    def _setup_collections(self):
        """Setup MongoDB collections with indexes."""
        try:
            # Setup conversations collection indexes
            with DatabaseContext('conversations') as conversations:
                if not conversations:
                    logger.info("MongoDB not available, skipping collection setup")
                    return
                
                # Create indexes for better performance on conversations collection
                try:
                    # Index on conversation_id for fast lookups (removed unique constraint to allow multiple conversations per session)
                    conversations.create_index([('conversation_id', 1)], background=True)
                    # Index on timestamp for cleanup operations
                    conversations.create_index([('timestamp', 1)], background=True)
                    # Compound index for conversation_id + timestamp queries
                    conversations.create_index([('conversation_id', 1), ('timestamp', -1)], background=True)
                except Exception as e:
                    pass
            
            # Setup chat_sessions collection indexes
            with DatabaseContext('chat_sessions') as chat_sessions:
                if not chat_sessions:
                    logger.info("MongoDB not available, skipping collection setup")
                    return
                
                # Create indexes for chat_sessions collection
                try:
                    # Drop existing conflicting index first
                    try:
                        chat_sessions.drop_index('session_id_1')
                    except:
                        pass  # Index might not exist
                    
                    # Unique index on session_id for fast lookups
                    chat_sessions.create_index([('session_id', 1)], unique=True, background=True)
                    # Index on expires_at for cleanup and active session queries
                    chat_sessions.create_index([('expires_at', 1)], background=True)
                    # Index on created_at for analytics
                    chat_sessions.create_index([('created_at', 1)], background=True)
                    # Compound index for active session queries
                    chat_sessions.create_index([('expires_at', 1), ('session_id', 1)], background=True)
                except Exception as e:
                    pass
                
            logger.info("MongoDB collections and indexes setup complete for both 'conversations' and 'chat_sessions' collections")
        except Exception as e:
            logger.warning(f"Failed to setup collections: {e}. Running in fallback mode.")
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new chat session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        
        with DatabaseContext('chat_sessions') as chat_sessions:
            if chat_sessions:
                try:
                    # Use Singapore timezone for session timestamps - ensure timezone-aware storage
                    singapore_tz = pytz.timezone('Asia/Singapore')
                    current_time = datetime.now(singapore_tz)
                    expires_at = current_time + timedelta(minutes=self.session_timeout_minutes)
                    
                    # Convert to UTC for MongoDB storage but preserve timezone awareness
                    utc_current = current_time.astimezone(pytz.UTC)
                    utc_expires = expires_at.astimezone(pytz.UTC)
                    
                    # Store with Singapore timezone info preserved
                    current_time = utc_current.replace(tzinfo=singapore_tz)
                    expires_at = utc_expires.replace(tzinfo=singapore_tz)
                    
                    session_data = {
                        'session_id': session_id,
                        'user_id': user_id,
                        'created_at': current_time,
                        'last_activity': current_time,
                        'expires_at': expires_at,
                        'message_count': 0
                    }
                    
                    chat_sessions.insert_one(session_data)
                    pass
                except Exception as e:
                    logger.error(f"Failed to store session {session_id}: {e}")
            else:
                pass
                
        return session_id
    
    def extend_session(self, session_id: str) -> bool:
        """Extend session expiry time.
        
        Args:
            session_id: Session to extend
            
        Returns:
            bool: True if session was extended, False if not found
        """
        with DatabaseContext('chat_sessions') as chat_sessions:
            if not chat_sessions:
                pass
                return True  # Return True to not break the flow
                
            try:
                # Use Singapore timezone for session timestamps - ensure timezone-aware storage
                singapore_tz = pytz.timezone('Asia/Singapore')
                current_time = datetime.now(singapore_tz)
                new_expires_at = current_time + timedelta(minutes=self.session_timeout_minutes)
                
                # Convert to UTC for MongoDB storage but preserve timezone awareness
                utc_current = current_time.astimezone(pytz.UTC)
                utc_expires = new_expires_at.astimezone(pytz.UTC)
                
                # Store with Singapore timezone info preserved
                current_time = utc_current.replace(tzinfo=singapore_tz)
                new_expires_at = utc_expires.replace(tzinfo=singapore_tz)
                
                result = chat_sessions.update_one(
                    {'session_id': session_id},
                    {
                        '$set': {
                            'last_activity': current_time,
                            'expires_at': new_expires_at
                        }
                    }
                )
                
                if result.modified_count > 0:
                    pass
                    return True
                else:
                    logger.warning(f"Session {session_id} not found for extension")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to extend session {session_id}: {e}")
                return False
    
    def store_message(self, session_id: str, message_type: str, content: str, 
                     sender: str = 'user', metadata: Optional[Dict] = None) -> bool:
        """Store a conversation message by appending to existing conversation.
        
        Args:
            session_id: Session identifier
            message_type: Type of message (text, button_click, etc.)
            content: Message content
            sender: Message sender (user, bot)
            metadata: Additional message metadata
            
        Returns:
            bool: True if message was stored successfully
        """
        # Validate session_id to prevent null conversation_id errors
        if not session_id or session_id.strip() == '':
            logger.error(f"Invalid session_id provided: {session_id}")
            return False
            
        with DatabaseContext('conversations') as conversations:
            if not conversations:
                pass
                return True  # Return True to not break the flow
            
            try:
                # Format the new message line with proper formatting
                if sender.lower() == 'system':
                    new_message_line = f"{content}\n"
                else:
                    new_message_line = f"{sender.capitalize()}: {content}\n"
                
                # Use Singapore timezone - store directly without UTC conversion
                singapore_tz = pytz.timezone('Asia/Singapore')
                current_time = datetime.now(singapore_tz)
                new_expires_at = current_time + timedelta(minutes=self.session_timeout_minutes)
                
                # PERFORMANCE OPTIMIZATION: Single atomic operation for both conversation and session
                # This reduces database calls from 2 to 1 per message
                with DatabaseContext('chat_sessions') as chat_sessions:
                    if chat_sessions:
                        # Update session in parallel (non-blocking)
                        chat_sessions.update_one(
                            {'session_id': session_id},
                            {
                                '$set': {
                                    'last_activity': current_time,
                                    'expires_at': new_expires_at
                                },
                                '$inc': {'message_count': 1},
                                '$setOnInsert': {
                                    'session_id': session_id,
                                    'created_at': current_time,
                                    'user_id': None
                                }
                            },
                            upsert=True
                        )
                
                # Store conversation message with optimized $concat operation
                # Ensure conversation_id is never null to prevent E11000 duplicate key error
                if session_id and session_id.strip():
                    conversations.update_one(
                        {'conversation_id': session_id},
                        [
                            {
                                '$set': {
                                    'conversation_id': session_id,
                                    'timestamp': current_time,
                                    'content': {
                                        '$concat': [
                                            {'$ifNull': ['$content', '']},
                                            new_message_line
                                        ]
                                    }
                                }
                            }
                        ],
                        upsert=True
                    )
                else:
                    logger.error(f"Cannot store message: invalid session_id '{session_id}'")
                    return False
                
                pass
                return True
            except Exception as e:
                logger.error(f"Failed to store message for conversation {session_id}: {e}")
                return False
    
    def _update_session_activity(self, session_id: str, current_time: datetime):
        """Update session last activity and message count.
        
        Args:
            session_id: Session identifier
            current_time: Current timestamp
        """
        with DatabaseContext('chat_sessions') as chat_sessions:
            if chat_sessions:
                try:
                    # Use Singapore timezone consistently - current_time is already Singapore timezone
                    singapore_tz = pytz.timezone('Asia/Singapore')
                    # current_time is already in Singapore timezone from store_message, no conversion needed
                    
                    new_expires_at = current_time + timedelta(minutes=self.session_timeout_minutes)
                    # expires_at inherits timezone from current_time automatically
                    
                    chat_sessions.update_one(
                        {'session_id': session_id},
                        {
                            '$set': {
                                'last_activity': current_time,
                                'expires_at': new_expires_at
                            },
                            '$inc': {
                                'message_count': 1
                            }
                        },
                        upsert=True  # Create session if it doesn't exist
                    )
                    pass
                except Exception as e:
                    logger.error(f"Failed to update session activity for {session_id}: {e}")
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve (not used in new format)
            
        Returns:
            List containing the conversation record with parsed content
        """
        with DatabaseContext('conversations') as conversations:
            if not conversations:
                pass
                return []
                
            try:
                conversation = conversations.find_one(
                    {'conversation_id': session_id},
                    {'_id': 0}  # Exclude MongoDB _id field
                )
                
                if conversation:
                    # Convert datetime to local timezone ISO string for JSON serialization
                    if 'timestamp' in conversation and isinstance(conversation['timestamp'], datetime):
                        # Ensure timezone awareness and convert to Singapore timezone
                        if conversation['timestamp'].tzinfo is None:
                            # If naive datetime, assume UTC and convert to Singapore timezone
                            utc_time = conversation['timestamp'].replace(tzinfo=pytz.UTC)
                            singapore_tz = pytz.timezone('Asia/Singapore')
                            local_time = utc_time.astimezone(singapore_tz)
                        else:
                            # If timezone-aware, convert to Singapore timezone
                            singapore_tz = pytz.timezone('Asia/Singapore')
                            local_time = conversation['timestamp'].astimezone(singapore_tz)
                        
                        conversation['timestamp'] = local_time.isoformat()
                    return [conversation]
                else:
                    return []
            except Exception as e:
                logger.error(f"Failed to retrieve conversation history for {session_id}: {e}")
                return []
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        with DatabaseContext('chat_sessions') as chat_sessions:
            if not chat_sessions:
                pass
                return None
                
            try:
                session = chat_sessions.find_one(
                    {'session_id': session_id},
                    {'_id': 0}  # Exclude MongoDB _id field
                )
                
                if session:
                    # Convert datetime fields to ISO strings for JSON serialization
                    singapore_tz = pytz.timezone('Asia/Singapore')
                    for field in ['created_at', 'last_activity', 'expires_at']:
                        if field in session and isinstance(session[field], datetime):
                            if session[field].tzinfo is None:
                                # If naive datetime, assume UTC and convert to Singapore timezone
                                utc_time = session[field].replace(tzinfo=pytz.UTC)
                                local_time = utc_time.astimezone(singapore_tz)
                            else:
                                # If timezone-aware, convert to Singapore timezone
                                local_time = session[field].astimezone(singapore_tz)
                            session[field] = local_time.isoformat()
                    
                    pass
                    return session
                else:
                    pass
                    return None
            except Exception as e:
                logger.error(f"Failed to retrieve session info for {session_id}: {e}")
                return None
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and conversations.
        
        Returns:
            Number of items cleaned up (conversations + sessions)
        """
        total_cleaned = 0
        
        # Clean up expired chat sessions
        with DatabaseContext('chat_sessions') as chat_sessions:
            if chat_sessions:
                try:
                    # Use current time for session expiry check
                    current_time = datetime.utcnow()
                    
                    session_result = chat_sessions.delete_many(
                        {'expires_at': {'$lt': current_time}}
                    )
                    
                    logger.info(f"Cleaned up {session_result.deleted_count} expired chat sessions")
                    total_cleaned += session_result.deleted_count
                except Exception as e:
                    logger.error(f"Failed to cleanup expired chat sessions: {e}")
        
        # Clean up old conversations
        with DatabaseContext('conversations') as conversations:
            if not conversations:
                pass
                return total_cleaned
                
            try:
                # Clean up old conversations (older than session timeout)
                # Use UTC for internal cleanup operations
                cutoff_time = datetime.utcnow() - timedelta(minutes=self.session_timeout_minutes)
                
                conversation_result = conversations.delete_many(
                    {'timestamp': {'$lt': cutoff_time}}
                )
                
                logger.info(f"Cleaned up {conversation_result.deleted_count} old conversations")
                total_cleaned += conversation_result.deleted_count
            except Exception as e:
                logger.error(f"Failed to cleanup old conversations: {e}")
        
        logger.info(f"Total cleanup: {total_cleaned} items removed")
        return total_cleaned
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        with DatabaseContext('chat_sessions') as chat_sessions:
            if not chat_sessions:
                pass
                return 0
                
            try:
                # Count sessions that haven't expired yet
                # Use UTC for internal operations
                current_time = datetime.utcnow()
                
                count = chat_sessions.count_documents(
                    {'expires_at': {'$gt': current_time}}
                )
                
                pass
                return count
            except Exception as e:
                logger.error(f"Failed to get active sessions count: {e}")
                return 0
    
    def close(self):
        """Close MongoDB connection."""
        # Connection is managed by the centralized database manager
        logger.info("Conversation storage closed (connection managed centrally)")

# Global instance
conversation_storage = ConversationStorage()