"""Centralized Automatic Conversation Logger
Provides base classes and decorators for automatic conversation logging.
"""

import logging
import uuid
from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from .conversation_middleware import ConversationTracker, log_bot_response, log_action_execution
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class AutoLoggedAction(Action):
    """Base action class that automatically logs all conversations.
    
    All RASA actions should inherit from this class instead of Action
    to enable automatic conversation logging without manual integration.
    """
    
    def name(self) -> Text:
        """Return the name of this action. Child classes should override this method."""
        return self.__class__.__name__
    
    def __init__(self):
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Execute the main action first (immediate response)
        result = self.execute_action(dispatcher, tracker, domain)
        
        # Log to database in background (non-blocking)
        self.executor.submit(self._log_conversation_async, tracker, dispatcher)
        
        return result
    
    def _log_conversation_async(self, tracker: Tracker, dispatcher: CollectingDispatcher):
        """Log conversation to database asynchronously"""
        try:
            sender_id = tracker.sender_id
            action_name = self.name()
            
            try:
                # Log user message if available (only once per action)
                latest_message = tracker.latest_message
                if latest_message and latest_message.get('text'):
                    ConversationTracker.store_user_message(
                        sender_id=sender_id,
                        message=latest_message.get('text', ''),
                        intent=latest_message.get('intent', {}).get('name'),
                        entities=latest_message.get('entities', [])
                    )
                    logger.debug(f"Logged user message for sender {sender_id}: {latest_message.get('text', '')[:50]}...")
                
                # Log action execution
                log_action_execution(sender_id, action_name, success=True)
                
                # Log bot responses automatically
                if hasattr(dispatcher, 'messages') and dispatcher.messages:
                    for message in dispatcher.messages:
                        if message.get('text'):
                            log_bot_response(sender_id, message['text'], action_name)
                            logger.debug(f"Logged bot response for sender {sender_id}: {message['text'][:50]}...")
                
            except Exception as e:
                # Log action execution failure
                log_action_execution(sender_id, action_name, success=False, error_message=str(e))
                logger.error(f"Error in action {action_name}: {e}")
                
        except Exception as e:
            logger.error(f"Background logging failed: {e}")
    
    def execute_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Override this method in child classes instead of run().
        
        This method contains the actual action logic.
        The run() method handles automatic logging.
        """
        raise NotImplementedError("Child classes must implement execute_action()")

class ConversationLogger:
    """Centralized conversation logger for manual logging when needed."""
    
    @staticmethod
    def log_user_input(sender_id: str, message: str, intent: Optional[str] = None, entities: Optional[list] = None):
        """Log user input message."""
        try:
            ConversationTracker.store_user_message(
                sender_id=sender_id,
                message=message,
                intent=intent,
                entities=entities or []
            )
        except Exception as e:
            logger.error(f"Error logging user input: {e}")
    
    @staticmethod
    def log_bot_output(sender_id: str, message: str, action_name: Optional[str] = None):
        """Log bot output message."""
        try:
            log_bot_response(sender_id, message, action_name)
        except Exception as e:
            logger.error(f"Error logging bot output: {e}")
    
    @staticmethod
    def log_action(sender_id: str, action_name: str, success: bool = True, error_message: Optional[str] = None):
        """Log action execution."""
        try:
            log_action_execution(sender_id, action_name, success, error_message)
        except Exception as e:
            logger.error(f"Error logging action execution: {e}")
    
    @staticmethod
    def start_session(sender_id: Optional[str] = None) -> str:
        """Start a new conversation session and return session ID."""
        try:
            if not sender_id:
                sender_id = str(uuid.uuid4())
            
            session_id = ConversationTracker.get_or_create_session(sender_id)
            logger.info(f"Started conversation session {session_id} for sender {sender_id}")
            return session_id
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return sender_id or str(uuid.uuid4())  # Fallback to sender_id or new UUID

def auto_log_conversation(func):
    """Decorator for automatic conversation logging in non-Action functions."""
    def wrapper(*args, **kwargs):
        try:
            # Extract sender_id if available
            sender_id = kwargs.get('sender_id') or (args[1].sender_id if len(args) > 1 and hasattr(args[1], 'sender_id') else None)
            
            if sender_id:
                # Log function execution
                ConversationLogger.log_action(sender_id, func.__name__)
            
            return func(*args, **kwargs)
            
        except Exception as e:
            if sender_id:
                ConversationLogger.log_action(sender_id, func.__name__, success=False, error_message=str(e))
            raise e
    
    return wrapper