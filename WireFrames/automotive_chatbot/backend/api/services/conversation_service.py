"""Unified Conversation Service
Centralized conversation management system that handles message storage,
retrieval, and conversation lifecycle management.
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
from .unified_session_manager import unified_session_manager, SessionStatus

# Configure logger
logger = logging.getLogger('api.services.conversation_service')

class MessageType(Enum):
    """Message type enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

class ConversationStatus(Enum):
    """Conversation status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"

class UnifiedConversationService:
    """Unified conversation management service.
    
    This service provides centralized conversation management that:
    1. Integrates with the unified session manager
    2. Handles message storage and retrieval
    3. Maintains conversation history and context
    4. Ensures data consistency across all conversation operations
    """
    
    def __init__(self):
        """Initialize the unified conversation service."""
        self.singapore_tz = pytz.timezone('Asia/Singapore')
        self._setup_collections()
        logger.info("[UNIFIED_CONVERSATION] Service initialized")
    
    def _setup_collections(self):
        """Setup MongoDB collections with optimized indexes for conversation management."""
        try:
            # Setup unified_conversations collection
            with DatabaseContext('unified_conversations') as conversations:
                if not conversations:
                    logger.info("[UNIFIED_CONVERSATION] MongoDB not available, skipping collection setup")
                    return
                
                # Create optimized indexes for conversation management
                try:
                    # Primary index on conversation_id
                    conversations.create_index([('conversation_id', 1)], background=True)
                    # Index for session-based queries
                    conversations.create_index([('session_id', 1)], background=True)
                    # Index for client-based queries
                    conversations.create_index([('client_id', 1)], background=True)
                    # Index for message ordering
                    conversations.create_index([('conversation_id', 1), ('timestamp', 1)], background=True)
                    # Index for analytics and cleanup
                    conversations.create_index([('created_at', 1)], background=True)
                    # Index for status-based queries
                    conversations.create_index([('status', 1)], background=True)
                    
                    logger.info("[UNIFIED_CONVERSATION] MongoDB indexes created successfully")
                except Exception as e:
                    logger.warning(f"[UNIFIED_CONVERSATION] Index creation warning: {e}")
                    
        except Exception as e:
            logger.error(f"[UNIFIED_CONVERSATION] Failed to setup collections: {e}")
    
    def store_message(self, session_id: str, message: str, message_type: MessageType,
                     metadata: Optional[Dict] = None, client_id: Optional[str] = None) -> bool:
        """Store a message in the conversation.
        
        Args:
            session_id: Session identifier
            message: Message content
            message_type: Type of message (user, assistant, system, error)
            metadata: Additional message metadata
            client_id: Client identifier (optional, will be retrieved from session if not provided)
            
        Returns:
            bool: True if message was stored successfully
        """
        logger.debug(f"[UNIFIED_CONVERSATION] Storing message for session: {session_id}")
        
        # Validate and extend session
        status, session_data = unified_session_manager.validate_session(session_id)
        
        if status != SessionStatus.ACTIVE:
            logger.error(f"[UNIFIED_CONVERSATION] Cannot store message for inactive session: {session_id}")
            return False
        
        # Extend session activity
        unified_session_manager.extend_session(session_id, {
            'action': 'message_stored',
            'message_type': message_type.value
        })
        
        # Get conversation_id and client_id from session
        conversation_id = session_data.get('conversation_id')
        if not client_id:
            client_id = session_data.get('client_id')
        
        if not conversation_id or not client_id:
            logger.error(f"[UNIFIED_CONVERSATION] Missing conversation_id or client_id for session: {session_id}")
            return False
        
        current_time = datetime.now(self.singapore_tz)
        message_id = str(uuid.uuid4())
        
        message_data = {
            'message_id': message_id,
            'conversation_id': conversation_id,
            'session_id': session_id,
            'client_id': client_id,
            'message': message,
            'message_type': message_type.value,
            'timestamp': current_time,
            'created_at': current_time,
            'metadata': metadata or {},
            'processed': True,
            'version': '2.0'  # Version for tracking unified system messages
        }
        
        with DatabaseContext('unified_conversations') as conversations:
            if not conversations:
                logger.error(f"[UNIFIED_CONVERSATION] MongoDB not available for message storage")
                return False
            
            try:
                # Store the message
                result = conversations.insert_one(message_data)
                
                # Increment message count in session
                unified_session_manager.increment_message_count(session_id)
                
                logger.info(f"[UNIFIED_CONVERSATION] Message stored successfully - message_id: {message_id}, conversation_id: {conversation_id}")
                return True
                
            except Exception as e:
                logger.error(f"[UNIFIED_CONVERSATION] Failed to store message: {e}")
                return False
    
    def get_conversation_history(self, session_id: str, limit: int = 50, 
                               include_metadata: bool = False) -> List[Dict[str, Any]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
            include_metadata: Whether to include message metadata
            
        Returns:
            List of message dictionaries ordered by timestamp
        """
        logger.debug(f"[UNIFIED_CONVERSATION] Getting conversation history for session: {session_id}")
        
        # Validate session
        status, session_data = unified_session_manager.validate_session(session_id)
        
        if status == SessionStatus.INVALID:
            logger.error(f"[UNIFIED_CONVERSATION] Invalid session for history retrieval: {session_id}")
            return []
        
        conversation_id = session_data.get('conversation_id') if session_data else None
        
        if not conversation_id:
            logger.error(f"[UNIFIED_CONVERSATION] No conversation_id found for session: {session_id}")
            return []
        
        with DatabaseContext('unified_conversations') as conversations:
            if not conversations:
                logger.error(f"[UNIFIED_CONVERSATION] MongoDB not available for history retrieval")
                return []
            
            try:
                # Build projection based on include_metadata flag
                projection = {
                    '_id': 0,
                    'message_id': 1,
                    'message': 1,
                    'message_type': 1,
                    'timestamp': 1,
                    'conversation_id': 1,
                    'session_id': 1
                }
                
                if include_metadata:
                    projection['metadata'] = 1
                    projection['client_id'] = 1
                
                # Retrieve messages ordered by timestamp
                messages = list(conversations.find(
                    {'conversation_id': conversation_id},
                    projection
                ).sort('timestamp', 1).limit(limit))
                
                # Convert datetime fields to ISO strings for JSON serialization
                for message in messages:
                    if 'timestamp' in message and isinstance(message['timestamp'], datetime):
                        if message['timestamp'].tzinfo is None:
                            message['timestamp'] = message['timestamp'].replace(tzinfo=self.singapore_tz)
                        message['timestamp'] = message['timestamp'].isoformat()
                
                logger.info(f"[UNIFIED_CONVERSATION] Retrieved {len(messages)} messages for conversation: {conversation_id}")
                return messages
                
            except Exception as e:
                logger.error(f"[UNIFIED_CONVERSATION] Error retrieving conversation history: {e}")
                return []
    
    def get_conversation_history_by_id(self, conversation_id: str, limit: int = 50, 
                                     include_metadata: bool = False) -> List[Dict[str, Any]]:
        """Get conversation history directly by conversation_id.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to retrieve
            include_metadata: Whether to include message metadata
            
        Returns:
            List of message dictionaries ordered by timestamp
        """
        logger.debug(f"[UNIFIED_CONVERSATION] Getting conversation history by ID: {conversation_id}")
        
        with DatabaseContext('unified_conversations') as conversations:
            if not conversations:
                logger.error(f"[UNIFIED_CONVERSATION] MongoDB not available for history retrieval")
                return []
            
            try:
                # Build projection based on include_metadata flag
                projection = {
                    '_id': 0,
                    'message_id': 1,
                    'message': 1,
                    'message_type': 1,
                    'timestamp': 1,
                    'conversation_id': 1,
                    'session_id': 1
                }
                
                if include_metadata:
                    projection['metadata'] = 1
                    projection['client_id'] = 1
                
                # Retrieve messages ordered by timestamp
                messages = list(conversations.find(
                    {'conversation_id': conversation_id},
                    projection
                ).sort('timestamp', 1).limit(limit))
                
                # Convert datetime fields to ISO strings for JSON serialization
                for message in messages:
                    if 'timestamp' in message and isinstance(message['timestamp'], datetime):
                        if message['timestamp'].tzinfo is None:
                            message['timestamp'] = message['timestamp'].replace(tzinfo=self.singapore_tz)
                        message['timestamp'] = message['timestamp'].isoformat()
                
                logger.info(f"[UNIFIED_CONVERSATION] Retrieved {len(messages)} messages for conversation by ID: {conversation_id}")
                return messages
                
            except Exception as e:
                logger.error(f"[UNIFIED_CONVERSATION] Error retrieving conversation history by ID: {e}")
                return []
    
    def get_conversation_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation summary and statistics.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary containing conversation summary or None if not found
        """
        logger.debug(f"[UNIFIED_CONVERSATION] Getting conversation summary for session: {session_id}")
        
        # Get session info
        session_info = unified_session_manager.get_session_info(session_id)
        
        if not session_info:
            logger.error(f"[UNIFIED_CONVERSATION] Session not found for summary: {session_id}")
            return None
        
        conversation_id = session_info.get('conversation_id')
        
        if not conversation_id:
            logger.error(f"[UNIFIED_CONVERSATION] No conversation_id in session: {session_id}")
            return None
        
        with DatabaseContext('unified_conversations') as conversations:
            if not conversations:
                return None
            
            try:
                # Get message statistics
                pipeline = [
                    {'$match': {'conversation_id': conversation_id}},
                    {
                        '$group': {
                            '_id': '$message_type',
                            'count': {'$sum': 1},
                            'first_message': {'$min': '$timestamp'},
                            'last_message': {'$max': '$timestamp'}
                        }
                    }
                ]
                
                stats = list(conversations.aggregate(pipeline))
                
                # Process statistics
                message_counts = {}
                first_message_time = None
                last_message_time = None
                
                for stat in stats:
                    message_type = stat['_id']
                    message_counts[message_type] = stat['count']
                    
                    if first_message_time is None or stat['first_message'] < first_message_time:
                        first_message_time = stat['first_message']
                    
                    if last_message_time is None or stat['last_message'] > last_message_time:
                        last_message_time = stat['last_message']
                
                # Calculate conversation duration
                duration_minutes = 0
                if first_message_time and last_message_time:
                    duration = last_message_time - first_message_time
                    duration_minutes = duration.total_seconds() / 60
                
                summary = {
                    'conversation_id': conversation_id,
                    'session_id': session_id,
                    'client_id': session_info.get('client_id'),
                    'message_counts': message_counts,
                    'total_messages': sum(message_counts.values()),
                    'duration_minutes': round(duration_minutes, 2),
                    'first_message_at': first_message_time.isoformat() if first_message_time else None,
                    'last_message_at': last_message_time.isoformat() if last_message_time else None,
                    'session_created_at': session_info.get('created_at'),
                    'session_status': session_info.get('status'),
                    'session_expires_at': session_info.get('expires_at')
                }
                
                logger.info(f"[UNIFIED_CONVERSATION] Summary generated for conversation: {conversation_id}")
                return summary
                
            except Exception as e:
                logger.error(f"[UNIFIED_CONVERSATION] Error generating conversation summary: {e}")
                return None
    
    def archive_conversation(self, session_id: str, archive_reason: str = "completed") -> bool:
        """Archive a conversation.
        
        Args:
            session_id: Session identifier
            archive_reason: Reason for archiving
            
        Returns:
            bool: True if conversation was archived successfully
        """
        logger.info(f"[UNIFIED_CONVERSATION] Archiving conversation for session: {session_id}")
        
        # Get session info
        session_info = unified_session_manager.get_session_info(session_id)
        
        if not session_info:
            logger.error(f"[UNIFIED_CONVERSATION] Session not found for archiving: {session_id}")
            return False
        
        conversation_id = session_info.get('conversation_id')
        
        if not conversation_id:
            logger.error(f"[UNIFIED_CONVERSATION] No conversation_id in session: {session_id}")
            return False
        
        current_time = datetime.now(self.singapore_tz)
        
        with DatabaseContext('unified_conversations') as conversations:
            if not conversations:
                return False
            
            try:
                # Update all messages in the conversation with archive status
                result = conversations.update_many(
                    {'conversation_id': conversation_id},
                    {
                        '$set': {
                            'status': ConversationStatus.ARCHIVED.value,
                            'archived_at': current_time,
                            'archive_reason': archive_reason
                        }
                    }
                )
                
                logger.info(f"[UNIFIED_CONVERSATION] Archived {result.modified_count} messages for conversation: {conversation_id}")
                return result.modified_count > 0
                
            except Exception as e:
                logger.error(f"[UNIFIED_CONVERSATION] Error archiving conversation: {e}")
                return False
    
    def cleanup_old_conversations(self, days_old: int = 30) -> int:
        """Clean up old conversations.
        
        Args:
            days_old: Number of days after which conversations should be cleaned up
            
        Returns:
            Number of conversations cleaned up
        """
        logger.info(f"[UNIFIED_CONVERSATION] Starting cleanup of conversations older than {days_old} days")
        
        cutoff_date = datetime.now(self.singapore_tz) - timedelta(days=days_old)
        
        with DatabaseContext('unified_conversations') as conversations:
            if not conversations:
                return 0
            
            try:
                # First archive old conversations
                archive_result = conversations.update_many(
                    {
                        'created_at': {'$lt': cutoff_date},
                        'status': {'$ne': ConversationStatus.ARCHIVED.value}
                    },
                    {
                        '$set': {
                            'status': ConversationStatus.ARCHIVED.value,
                            'archived_at': datetime.now(self.singapore_tz),
                            'archive_reason': 'automatic_cleanup'
                        }
                    }
                )
                
                # Then delete very old archived conversations (older than 90 days)
                very_old_cutoff = datetime.now(self.singapore_tz) - timedelta(days=90)
                delete_result = conversations.delete_many({
                    'created_at': {'$lt': very_old_cutoff},
                    'status': ConversationStatus.ARCHIVED.value
                })
                
                total_cleaned = archive_result.modified_count + delete_result.deleted_count
                logger.info(f"[UNIFIED_CONVERSATION] Cleanup completed: {archive_result.modified_count} archived, {delete_result.deleted_count} deleted")
                
                return total_cleaned
                
            except Exception as e:
                logger.error(f"[UNIFIED_CONVERSATION] Error during cleanup: {e}")
                return 0
    
    def get_client_conversations(self, client_id: str, limit: int = 100, 
                               include_archived: bool = False) -> List[Dict[str, Any]]:
        """Get conversations for a specific client.
        
        Args:
            client_id: Client identifier
            limit: Maximum number of conversations to retrieve
            include_archived: Whether to include archived conversations
            
        Returns:
            List of conversation summaries
        """
        logger.debug(f"[UNIFIED_CONVERSATION] Getting conversations for client: {client_id}")
        
        with DatabaseContext('unified_conversations') as conversations:
            if not conversations:
                return []
            
            try:
                # Build query filter
                query_filter = {'client_id': client_id}
                
                if not include_archived:
                    query_filter['status'] = {'$ne': ConversationStatus.ARCHIVED.value}
                
                # Aggregate conversations by conversation_id
                pipeline = [
                    {'$match': query_filter},
                    {
                        '$group': {
                            '_id': '$conversation_id',
                            'session_id': {'$first': '$session_id'},
                            'client_id': {'$first': '$client_id'},
                            'message_count': {'$sum': 1},
                            'first_message': {'$min': '$timestamp'},
                            'last_message': {'$max': '$timestamp'},
                            'status': {'$first': '$status'}
                        }
                    },
                    {'$sort': {'last_message': -1}},
                    {'$limit': limit}
                ]
                
                conversation_summaries = list(conversations.aggregate(pipeline))
                
                # Format the results
                formatted_conversations = []
                for conv in conversation_summaries:
                    formatted_conv = {
                        'conversation_id': conv['_id'],
                        'session_id': conv['session_id'],
                        'client_id': conv['client_id'],
                        'message_count': conv['message_count'],
                        'first_message_at': conv['first_message'].isoformat() if conv['first_message'] else None,
                        'last_message_at': conv['last_message'].isoformat() if conv['last_message'] else None,
                        'status': conv.get('status', ConversationStatus.ACTIVE.value)
                    }
                    formatted_conversations.append(formatted_conv)
                
                logger.info(f"[UNIFIED_CONVERSATION] Retrieved {len(formatted_conversations)} conversations for client: {client_id}")
                return formatted_conversations
                
            except Exception as e:
                logger.error(f"[UNIFIED_CONVERSATION] Error getting client conversations: {e}")
                return []
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """Get conversation statistics for monitoring.
        
        Returns:
            Dictionary containing conversation statistics
        """
        logger.debug("[UNIFIED_CONVERSATION] Getting conversation statistics")
        
        with DatabaseContext('unified_conversations') as conversations:
            if not conversations:
                return {'error': 'MongoDB not available'}
            
            try:
                current_time = datetime.now(self.singapore_tz)
                
                # Count total messages
                total_messages = conversations.count_documents({})
                
                # Count messages by type
                type_pipeline = [
                    {'$group': {'_id': '$message_type', 'count': {'$sum': 1}}}
                ]
                type_stats = list(conversations.aggregate(type_pipeline))
                message_type_counts = {stat['_id']: stat['count'] for stat in type_stats}
                
                # Count unique conversations
                unique_conversations = len(conversations.distinct('conversation_id'))
                
                # Count messages in last 24 hours
                last_24h = current_time - timedelta(hours=24)
                recent_messages = conversations.count_documents({
                    'created_at': {'$gt': last_24h}
                })
                
                # Count active conversations (with messages in last 24 hours)
                active_conversations = len(conversations.distinct('conversation_id', {
                    'created_at': {'$gt': last_24h}
                }))
                
                stats = {
                    'total_messages': total_messages,
                    'message_type_counts': message_type_counts,
                    'unique_conversations': unique_conversations,
                    'active_conversations_24h': active_conversations,
                    'recent_messages_24h': recent_messages,
                    'timestamp': current_time.isoformat()
                }
                
                logger.info(f"[UNIFIED_CONVERSATION] Conversation statistics: {stats}")
                return stats
                
            except Exception as e:
                logger.error(f"[UNIFIED_CONVERSATION] Error getting conversation statistics: {e}")
                return {'error': str(e)}

# Global instance
unified_conversation_service = UnifiedConversationService()