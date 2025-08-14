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
            
            logger.info(f"[USER MESSAGE] Sender: {sender_id}, Message: {user_message}")
            
        except Exception as e:
            logger.error(f"Error logging user message: {str(e)}")
    
    def log_action_execution(self, action_name: str, tracker: Tracker) -> None:
        """Log action execution details.
        
        Args:
            action_name: Name of the action being executed
            tracker: The conversation tracker
        """
        try:
            sender_id = tracker.sender_id
            intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
            
            logger.info(f"[ACTION EXECUTION] Sender: {sender_id}, Action: {action_name}, Intent: {intent}")
            
        except Exception as e:
            logger.error(f"Error logging action execution: {str(e)}")
    
    def log_bot_response(self, dispatcher: CollectingDispatcher, tracker: Tracker) -> None:
        """Log the bot's response.
        
        Args:
            dispatcher: The message dispatcher containing bot responses
            tracker: The conversation tracker
        """
        try:
            sender_id = tracker.sender_id
            
            # Get the messages that were sent
            messages = getattr(dispatcher, 'messages', [])
            
            for message in messages:
                if 'text' in message:
                    logger.info(f"[BOT RESPONSE] Sender: {sender_id}, Response: {message['text']}")
                elif 'template' in message:
                    logger.info(f"[BOT RESPONSE] Sender: {sender_id}, Template: {message['template']}")
                else:
                    logger.info(f"[BOT RESPONSE] Sender: {sender_id}, Message: {str(message)}")
                    
        except Exception as e:
            logger.error(f"Error logging bot response: {str(e)}")
    
    # Note: Subclasses should override the run() method directly
    # The logging methods above can be called manually if needed