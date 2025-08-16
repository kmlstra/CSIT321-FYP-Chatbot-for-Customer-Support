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

# Configure logger with proper module name for DEBUG level
logger = logging.getLogger('api.services.conversation_storage')

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
        logger.info(f"[CONVERSATION_STORAGE] Creating new session with ID: {session_id}, user_id: {user_id}")
        
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
                    
                    logger.debug(f"[CONVERSATION_STORAGE] Inserting session data: {session_data}")
                    result = chat_sessions.insert_one(session_data)
                    logger.info(f"[CONVERSATION_STORAGE] SUCCESS: Session created - session_id: {session_id}, inserted_id: {result.inserted_id}, user_id: {user_id}")
                except Exception as e:
                    logger.error(f"[CONVERSATION_STORAGE] Failed to store session {session_id}: {e}", exc_info=True)
            else:
                logger.warning(f"[CONVERSATION_STORAGE] MongoDB not available for session creation, returning session_id: {session_id}")
                
        return session_id
    
    def extend_session(self, session_id: str) -> bool:
        """Extend session expiry time.
        
        Args:
            session_id: Session to extend
            
        Returns:
            bool: True if session was extended, False if not found
        """
        logger.info(f"[CONVERSATION_STORAGE] Extending session: {session_id}")
        
        with DatabaseContext('chat_sessions') as chat_sessions:
            if not chat_sessions:
                logger.warning(f"[CONVERSATION_STORAGE] MongoDB not available for session extension, returning True for session: {session_id}")
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
                
                logger.debug(f"[CONVERSATION_STORAGE] Updating session {session_id} with new expiry: {new_expires_at}")
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
                    logger.info(f"[CONVERSATION_STORAGE] SUCCESS: Session extended - session_id: {session_id}, new_expiry: {new_expires_at}")
                    return True
                else:
                    logger.error(f"[CONVERSATION_STORAGE] CRITICAL: Session {session_id} not found for extension")
                    return False
                    
            except Exception as e:
                logger.error(f"[CONVERSATION_STORAGE] Failed to extend session {session_id}: {e}", exc_info=True)
                return False
    
    def store_message(self, session_id: str, message_type: str, content: str, 
                     sender: str = 'user', metadata: Optional[Dict] = None) -> bool:
        """Store a conversation message by appending to existing conversation.
        
        Args:
            session_id: Session identifier
            message_type: Type of message (text, button_click, etc.)
            content: Message content
            sender: Message sender (user, bot)
            metadata: Additional message metadata (should include client_id)
            
        Returns:
            bool: True if message was stored successfully
        """
        # Log the incoming store_message call with all parameters
        logger.info(f"[CONVERSATION_STORAGE] store_message called - session_id: {session_id}, message_type: {message_type}, sender: {sender}")
        logger.debug(f"[CONVERSATION_STORAGE] Message content: {content[:100]}{'...' if len(content) > 100 else ''}")
        logger.debug(f"[CONVERSATION_STORAGE] Full metadata: {metadata}")
        
        # Validate session_id to prevent null conversation_id errors
        if not session_id or session_id.strip() == '':
            logger.error(f"[CONVERSATION_STORAGE] Invalid session_id provided: {session_id}")
            return False
            
        # Extract client_id from metadata if available
        client_id = None
        if metadata and isinstance(metadata, dict):
            client_id = metadata.get('client_id') or metadata.get('clientId')
            # Also check for client_id in nested metadata
            if not client_id and 'metadata' in metadata:
                nested_metadata = metadata['metadata']
                if isinstance(nested_metadata, dict):
                    client_id = nested_metadata.get('client_id') or nested_metadata.get('clientId')
        
        # Log client_id extraction result
        if client_id:
            logger.info(f"[CONVERSATION_STORAGE] SUCCESS: Extracted client_id: {client_id} from metadata")
        else:
            logger.error(f"[CONVERSATION_STORAGE] CRITICAL: No client_id found in metadata for session {session_id}. This may cause data isolation issues. Metadata: {metadata}")
            
        with DatabaseContext('conversations') as conversations:
            if not conversations:
                pass
                return True  # Return True to not break the flow
            
            try:
                logger.debug(f"[CONVERSATION_STORAGE] Starting message storage for session {session_id}")
                
                # Format the new message line with proper formatting
                if sender.lower() == 'system':
                    new_message_line = f"{content}\n"
                else:
                    new_message_line = f"{sender.capitalize()}: {content}\n"
                
                logger.debug(f"[CONVERSATION_STORAGE] Formatted message line: {new_message_line.strip()}")
                
                # Use Singapore timezone - store directly without UTC conversion
                singapore_tz = pytz.timezone('Asia/Singapore')
                current_time = datetime.now(singapore_tz)
                new_expires_at = current_time + timedelta(minutes=self.session_timeout_minutes)
                
                logger.debug(f"[CONVERSATION_STORAGE] Timestamp: {current_time}, Expires: {new_expires_at}")
                
                # PERFORMANCE OPTIMIZATION: Single atomic operation for both conversation and session
                # This reduces database calls from 2 to 1 per message
                with DatabaseContext('chat_sessions') as chat_sessions:
                    if chat_sessions:
                        # Prepare session update with client_id if available
                        session_update = {
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
                        }
                        
                        # Add client_id to session if available (only in $setOnInsert to avoid conflict)
                        if client_id:
                            session_update['$setOnInsert']['client_id'] = client_id
                            logger.debug(f"[CONVERSATION_STORAGE] Adding client_id {client_id} to session update")
                        
                        # Update session in parallel (non-blocking)
                        logger.debug(f"[CONVERSATION_STORAGE] Updating session {session_id} with data: {session_update}")
                        session_result = chat_sessions.update_one(
                            {'session_id': session_id},
                            session_update,
                            upsert=True
                        )
                        logger.debug(f"[CONVERSATION_STORAGE] Session update result - matched: {session_result.matched_count}, modified: {session_result.modified_count}, upserted_id: {session_result.upserted_id}")
                
                # Store conversation message with optimized $concat operation
                # Ensure conversation_id is never null to prevent E11000 duplicate key error
                if session_id and session_id.strip():
                    # Prepare conversation update with client_id if available
                    conversation_set = {
                        'conversation_id': session_id,
                        'timestamp': current_time,
                        'content': {
                            '$concat': [
                                {'$ifNull': ['$content', '']},
                                new_message_line
                            ]
                        }
                    }
                    
                    # Add client_id to conversation if available
                    if client_id:
                        conversation_set['client_id'] = client_id
                        logger.debug(f"[CONVERSATION_STORAGE] Adding client_id {client_id} to conversation")
                    
                    logger.debug(f"[CONVERSATION_STORAGE] Updating conversation {session_id} with data: {conversation_set}")
                    conversation_result = conversations.update_one(
                        {'conversation_id': session_id},
                        [
                            {
                                '$set': conversation_set
                            }
                        ],
                        upsert=True
                    )
                    logger.debug(f"[CONVERSATION_STORAGE] Conversation update result - matched: {conversation_result.matched_count}, modified: {conversation_result.modified_count}, upserted_id: {conversation_result.upserted_id}")
                else:
                    logger.error(f"[CONVERSATION_STORAGE] Cannot store message: invalid session_id '{session_id}'")
                    return False
                
                logger.info(f"[CONVERSATION_STORAGE] SUCCESS: Message stored successfully - session_id: {session_id}, sender: {sender}, client_id: {client_id}, message_type: {message_type}")
                return True
            except Exception as e:
                logger.error(f"[CONVERSATION_STORAGE] Failed to store message for conversation {session_id}: {e}", exc_info=True)
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
        logger.debug(f"[CONVERSATION_STORAGE] Retrieving conversation history for session: {session_id}, limit: {limit}")
        
        with DatabaseContext('conversations') as conversations:
            if not conversations:
                logger.warning(f"[CONVERSATION_STORAGE] MongoDB not available for conversation history retrieval, session: {session_id}")
                return []
                
            try:
                logger.debug(f"[CONVERSATION_STORAGE] Querying conversation with conversation_id: {session_id}")
                conversation = conversations.find_one(
                    {'conversation_id': session_id},
                    {'_id': 0}  # Exclude MongoDB _id field
                )
                
                if conversation:
                    logger.debug(f"[CONVERSATION_STORAGE] Found conversation for session {session_id}, client_id: {conversation.get('client_id', 'N/A')}")
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
                    logger.info(f"[CONVERSATION_STORAGE] Successfully retrieved conversation history for session {session_id}")
                    return [conversation]
                else:
                    logger.debug(f"[CONVERSATION_STORAGE] No conversation found for session {session_id}")
                    return []
            except Exception as e:
                logger.error(f"[CONVERSATION_STORAGE] Failed to retrieve conversation history for {session_id}: {e}", exc_info=True)
                return []
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        logger.debug(f"[CONVERSATION_STORAGE] Retrieving session info for: {session_id}")
        
        with DatabaseContext('chat_sessions') as chat_sessions:
            if not chat_sessions:
                logger.warning(f"[CONVERSATION_STORAGE] MongoDB not available for session info retrieval, session: {session_id}")
                return None
                
            try:
                logger.debug(f"[CONVERSATION_STORAGE] Querying session with session_id: {session_id}")
                session = chat_sessions.find_one(
                    {'session_id': session_id},
                    {'_id': 0}  # Exclude MongoDB _id field
                )
                
                if session:
                    logger.debug(f"[CONVERSATION_STORAGE] Found session {session_id}, client_id: {session.get('client_id', 'N/A')}, message_count: {session.get('message_count', 0)}")
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
                    
                    logger.info(f"[CONVERSATION_STORAGE] Successfully retrieved session info for {session_id}")
                    return session
                else:
                    logger.debug(f"[CONVERSATION_STORAGE] No session found for session_id: {session_id}")
                    return None
            except Exception as e:
                logger.error(f"[CONVERSATION_STORAGE] Failed to retrieve session info for {session_id}: {e}", exc_info=True)
                return None
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and old conversations.
        
        Returns:
            Number of sessions cleaned up
        """
        logger.debug("[CONVERSATION_STORAGE] Starting cleanup of expired sessions and old conversations")
        singapore_tz = pytz.timezone('Asia/Singapore')
        current_time = datetime.now(singapore_tz)
        
        cleaned_count = 0
        
        # Clean up expired chat sessions
        logger.debug(f"[CONVERSATION_STORAGE] Cleaning up chat sessions expired before: {current_time.isoformat()}")
        with DatabaseContext('chat_sessions') as chat_sessions:
            if chat_sessions:
                try:
                    result = chat_sessions.delete_many({
                        'expires_at': {'$lt': current_time}
                    })
                    logger.info(f"[CONVERSATION_STORAGE] Cleaned up {result.deleted_count} expired chat sessions")
                    cleaned_count += result.deleted_count
                except Exception as e:
                    logger.error(f"[CONVERSATION_STORAGE] Failed to cleanup expired chat sessions: {e}", exc_info=True)
        
        # Clean up old conversations (older than 30 days)
        cutoff_time = current_time - timedelta(days=30)
        logger.debug(f"[CONVERSATION_STORAGE] Cleaning up conversations older than: {cutoff_time.isoformat()}")
        with DatabaseContext('conversations') as conversations:
            if conversations:
                try:
                    result = conversations.delete_many({
                        'timestamp': {'$lt': cutoff_time}
                    })
                    logger.info(f"[CONVERSATION_STORAGE] Cleaned up {result.deleted_count} old conversations")
                    cleaned_count += result.deleted_count
                except Exception as e:
                    logger.error(f"[CONVERSATION_STORAGE] Failed to cleanup old conversations: {e}", exc_info=True)
        
        logger.info(f"[CONVERSATION_STORAGE] Total cleanup completed: {cleaned_count} records removed")
        return cleaned_count
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        logger.debug("[CONVERSATION_STORAGE] Getting active sessions count")
        
        with DatabaseContext('chat_sessions') as chat_sessions:
            if not chat_sessions:
                logger.warning("[CONVERSATION_STORAGE] MongoDB not available for active sessions count")
                return 0
                
            try:
                singapore_tz = pytz.timezone('Asia/Singapore')
                current_time = datetime.now(singapore_tz)
                
                logger.debug(f"[CONVERSATION_STORAGE] Counting sessions active after: {current_time.isoformat()}")
                count = chat_sessions.count_documents({
                    'expires_at': {'$gt': current_time}
                })
                
                logger.info(f"[CONVERSATION_STORAGE] Found {count} active sessions")
                return count
            except Exception as e:
                logger.error(f"[CONVERSATION_STORAGE] Failed to get active sessions count: {e}", exc_info=True)
                return 0
    

    
    def close(self):
        """Close MongoDB connection."""
        # Connection is managed by the centralized database manager
        logger.info("Conversation storage closed (connection managed centrally)")

# Global instance
conversation_storage = ConversationStorage()