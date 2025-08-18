"""Auto Logger for RASA Actions

This module provides automatic conversation logging functionality specifically
for RASA action classes. It includes rasa_sdk dependencies and is designed
to work within the RASA actions server environment.
"""

import logging
from typing import Dict, Text, Any, List
from datetime import datetime
from abc import ABC, abstractmethod

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

# Import conversation middleware for logging
from api.middleware.conversation_middleware import ConversationTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoLoggedAction(Action, ABC):
    """Base action class with automatic conversation logging for RASA actions.
    
    This class extends rasa_sdk.Action and provides automatic logging of:
    - User messages
    - Action execution
    - Bot responses
    
    All action classes should inherit from this class to enable automatic logging.
    """
    
    @abstractmethod
    def name(self) -> Text:
        """Return the name of this action.
        
        This method must be implemented by subclasses to provide the action name.
        
        Returns:
            The name of the action
        """
        pass
    
    def log_user_message(self, tracker: Tracker) -> None:
        """Log the user's message.
        
        Args:
            tracker: The conversation tracker containing user message
        """
        try:
            user_message = tracker.latest_message.get('text', '')
            sender_id = tracker.sender_id
            intent = tracker.latest_message.get('intent', {}).get('name')
            entities = tracker.latest_message.get('entities', [])
            
            # Store user message using conversation tracker
            ConversationTracker.store_user_message(
                sender_id=sender_id,
                message=user_message,
                intent=intent,
                entities=entities
            )
            
        except Exception as e:
            logger.error(f"Error logging user message: {e}")
    
    def log_action_execution(self, action_name: str, tracker: Tracker, success: bool = True, error_message: str = None) -> None:
        """Log action execution details.
        
        Args:
            action_name: Name of the action being executed
            tracker: The conversation tracker
            success: Whether action executed successfully
            error_message: Error message if action failed
        """
        try:
            sender_id = tracker.sender_id
            
            # Store action execution using conversation tracker
            ConversationTracker.store_action_execution(
                sender_id=sender_id,
                action_name=action_name,
                success=success,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Error logging action execution: {e}")
    
    def log_bot_response(self, dispatcher: CollectingDispatcher, tracker: Tracker, action_name: str = None) -> None:
        """Log the bot's response.
        
        Args:
            dispatcher: The message dispatcher containing bot responses
            tracker: The conversation tracker
            action_name: Name of the action that generated the response
        """
        try:
            sender_id = tracker.sender_id
            
            # Get the messages that were sent
            messages = getattr(dispatcher, 'messages', [])
            
            for message in messages:
                # Extract text content from message
                if isinstance(message, dict):
                    text_content = message.get('text', '')
                    if text_content:
                        # Store bot response using conversation tracker
                        ConversationTracker.store_bot_response(
                            sender_id=sender_id,
                            response=text_content,
                            action_name=action_name or self.name()
                        )
                elif isinstance(message, str):
                    # Store bot response using conversation tracker
                    ConversationTracker.store_bot_response(
                        sender_id=sender_id,
                        response=message,
                        action_name=action_name or self.name()
                    )
                    
        except Exception as e:
            logger.error(f"Error logging bot response: {e}")
    
    # Note: Subclasses should override the run() method directly
    # The logging methods above can be called manually if needed