#!/usr/bin/env python3
"""
Intent Validation Middleware

This middleware integrates intent validation into the RASA conversation flow,
providing enhanced confidence checking and context awareness.

Features:
- Pre-action intent validation
- Automatic fallback handling
- Context-aware validation
- Performance monitoring
- Validation logging
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
import asyncio
from datetime import datetime

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, UserUtteranceReverted

# Import our intent validator
from ..utils.intent_validator import intent_validator, IntentValidationResult
from ..cache.enhanced_cache import enhanced_cache

logger = logging.getLogger(__name__)

class IntentValidationMiddleware:
    """Middleware for intent validation in RASA actions"""
    
    def __init__(self):
        self.validation_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'fallback_triggered': 0,
            'clarification_requested': 0
        }
        self.performance_metrics = {
            'avg_validation_time': 0.0,
            'max_validation_time': 0.0,
            'min_validation_time': float('inf')
        }
    
    def validate_intent(self, require_validation: bool = True, 
                       confidence_threshold: Optional[float] = None):
        """Decorator for intent validation in RASA actions"""
        def decorator(action_func: Callable):
            @wraps(action_func)
            async def wrapper(self_action, dispatcher: CollectingDispatcher, 
                           tracker: Tracker, domain: Dict[str, Any]):
                
                start_time = time.time()
                
                try:
                    # Extract intent information from tracker
                    latest_message = tracker.latest_message
                    intent_name = latest_message.get('intent', {}).get('name', '')
                    intent_confidence = latest_message.get('intent', {}).get('confidence', 0.0)
                    user_message = latest_message.get('text', '')
                    entities = latest_message.get('entities', [])
                    
                    # Get user and conversation IDs
                    user_id = tracker.sender_id
                    conversation_id = tracker.sender_id  # Using sender_id as conversation_id
                    
                    # Get previous intent
                    previous_intent = None
                    events = tracker.events
                    for event in reversed(events[:-1]):  # Exclude current event
                        if event.get('event') == 'user' and event.get('parse_data', {}).get('intent'):
                            previous_intent = event['parse_data']['intent']['name']
                            break
                    
                    # Convert entities to dict
                    entities_dict = {entity['entity']: entity['value'] for entity in entities}
                    
                    # Perform intent validation if required
                    validation_result = None
                    if require_validation:
                        validation_result = await intent_validator.validate_intent(
                            intent=intent_name,
                            confidence=intent_confidence,
                            user_message=user_message,
                            user_id=user_id,
                            conversation_id=conversation_id,
                            entities=entities_dict,
                            previous_intent=previous_intent
                        )
                        
                        # Update statistics
                        self._update_validation_stats(validation_result)
                        
                        # Handle validation failure
                        if not validation_result.is_valid:
                            return await self._handle_validation_failure(
                                validation_result, dispatcher, tracker, domain
                            )
                    
                    # Validate entities if validation passed
                    if validation_result and validation_result.is_valid:
                        validated_entities = await intent_validator.validate_entity_extraction(
                            entities_dict, intent_name
                        )
                        
                        # Update tracker with validated entities
                        entity_slots = []
                        for entity_name, entity_value in validated_entities.items():
                            entity_slots.append(SlotSet(entity_name, entity_value))
                        
                        # Add validation metadata to tracker
                        entity_slots.extend([
                            SlotSet('intent_confidence', intent_confidence),
                            SlotSet('validation_score', validation_result.context_score),
                            SlotSet('validation_timestamp', datetime.now().isoformat())
                        ])
                    
                    # Execute the original action
                    result = await action_func(self_action, dispatcher, tracker, domain)
                    
                    # Add entity slots to result if validation occurred
                    if validation_result and validation_result.is_valid and 'entity_slots' in locals():
                        if isinstance(result, list):
                            result.extend(entity_slots)
                        else:
                            result = entity_slots
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Intent validation middleware error: {str(e)}", exc_info=True)
                    # Continue with original action on middleware error
                    return await action_func(self_action, dispatcher, tracker, domain)
                
                finally:
                    # Update performance metrics
                    validation_time = time.time() - start_time
                    self._update_performance_metrics(validation_time)
            
            return wrapper
        return decorator
    
    async def _handle_validation_failure(self, validation_result: IntentValidationResult,
                                       dispatcher: CollectingDispatcher, 
                                       tracker: Tracker, 
                                       domain: Dict[str, Any]) -> List[Any]:
        """Handle intent validation failure"""
        
        events = []
        
        if validation_result.requires_clarification:
            # Request clarification from user
            clarification_message = self._generate_clarification_message(
                validation_result, tracker.latest_message.get('text', '')
            )
            dispatcher.utter_message(text=clarification_message)
            
            # Add suggestions if available
            if validation_result.suggestions:
                suggestions_text = "Did you mean:\n" + "\n".join(
                    f"• {suggestion.replace('_', ' ').title()}" 
                    for suggestion in validation_result.suggestions[:3]
                )
                dispatcher.utter_message(text=suggestions_text)
            
            self.validation_stats['clarification_requested'] += 1
            
        else:
            # Use fallback action
            if validation_result.fallback_action:
                dispatcher.utter_message(template=validation_result.fallback_action)
            else:
                dispatcher.utter_message(
                    text="I'm not sure I understood that correctly. Could you please rephrase?"
                )
            
            self.validation_stats['fallback_triggered'] += 1
        
        # Set validation metadata slots
        events.extend([
            SlotSet('last_validation_failed', True),
            SlotSet('validation_reason', validation_result.validation_reason),
            SlotSet('original_intent', validation_result.original_intent),
            SlotSet('suggested_intents', validation_result.suggestions)
        ])
        
        # Revert user utterance if confidence is very low
        if validation_result.confidence_score < 0.3:
            events.append(UserUtteranceReverted())
        
        return events
    
    def _generate_clarification_message(self, validation_result: IntentValidationResult, 
                                      user_message: str) -> str:
        """Generate clarification message based on validation failure"""
        
        if validation_result.validation_reason == "Low confidence score":
            return f"I'm not quite sure what you meant by '{user_message}'. Could you please be more specific?"
        
        elif validation_result.validation_reason == "Pattern mismatch":
            return "I understand you're trying to do something, but I'm not sure exactly what. Could you rephrase that?"
        
        elif validation_result.validation_reason == "Context validation failed":
            return "That doesn't seem to fit with our current conversation. What would you like to do?"
        
        elif validation_result.validation_reason == "Invalid intent transition":
            return "Let's take a step back. What would you like to help you with?"
        
        else:
            return "I'm having trouble understanding. Could you please tell me what you'd like to do?"
    
    def _update_validation_stats(self, validation_result: IntentValidationResult) -> None:
        """Update validation statistics"""
        self.validation_stats['total_validations'] += 1
        
        if validation_result.is_valid:
            self.validation_stats['successful_validations'] += 1
        else:
            self.validation_stats['failed_validations'] += 1
    
    def _update_performance_metrics(self, validation_time: float) -> None:
        """Update performance metrics"""
        total_validations = self.validation_stats['total_validations']
        
        if total_validations == 1:
            self.performance_metrics['avg_validation_time'] = validation_time
            self.performance_metrics['min_validation_time'] = validation_time
        else:
            # Update average
            current_avg = self.performance_metrics['avg_validation_time']
            self.performance_metrics['avg_validation_time'] = (
                (current_avg * (total_validations - 1) + validation_time) / total_validations
            )
            
            # Update min
            self.performance_metrics['min_validation_time'] = min(
                self.performance_metrics['min_validation_time'], validation_time
            )
        
        # Update max
        self.performance_metrics['max_validation_time'] = max(
            self.performance_metrics['max_validation_time'], validation_time
        )
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total = self.validation_stats['total_validations']
        success_rate = (
            self.validation_stats['successful_validations'] / total * 100 
            if total > 0 else 0
        )
        
        return {
            **self.validation_stats,
            'success_rate_percent': round(success_rate, 2),
            'performance_metrics': self.performance_metrics
        }
    
    async def validate_conversation_flow(self, tracker: Tracker) -> Dict[str, Any]:
        """Validate overall conversation flow"""
        events = tracker.events
        user_events = [e for e in events if e.get('event') == 'user']
        
        if len(user_events) < 2:
            return {'is_valid': True, 'reason': 'Insufficient conversation history'}
        
        # Check for conversation loops
        recent_intents = []
        for event in user_events[-5:]:  # Last 5 user messages
            intent_data = event.get('parse_data', {}).get('intent', {})
            if intent_data:
                recent_intents.append(intent_data.get('name', ''))
        
        # Detect loops (same intent repeated 3+ times)
        if len(recent_intents) >= 3:
            if recent_intents[-1] == recent_intents[-2] == recent_intents[-3]:
                return {
                    'is_valid': False, 
                    'reason': 'Conversation loop detected',
                    'repeated_intent': recent_intents[-1]
                }
        
        # Check conversation length
        if len(user_events) > 50:
            return {
                'is_valid': False,
                'reason': 'Conversation too long',
                'message_count': len(user_events)
            }
        
        return {'is_valid': True, 'reason': 'Conversation flow is healthy'}
    
    def reset_stats(self) -> None:
        """Reset validation statistics"""
        self.validation_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'fallback_triggered': 0,
            'clarification_requested': 0
        }
        self.performance_metrics = {
            'avg_validation_time': 0.0,
            'max_validation_time': 0.0,
            'min_validation_time': float('inf')
        }

# Global middleware instance
intent_validation_middleware = IntentValidationMiddleware()

# Convenience decorators
def validate_intent(require_validation: bool = True, confidence_threshold: Optional[float] = None):
    """Convenience decorator for intent validation"""
    return intent_validation_middleware.validate_intent(require_validation, confidence_threshold)

def validate_high_confidence(confidence_threshold: float = 0.8):
    """Decorator for high-confidence intent validation"""
    return intent_validation_middleware.validate_intent(True, confidence_threshold)

def validate_medium_confidence(confidence_threshold: float = 0.6):
    """Decorator for medium-confidence intent validation"""
    return intent_validation_middleware.validate_intent(True, confidence_threshold)

def no_validation():
    """Decorator to skip intent validation"""
    return intent_validation_middleware.validate_intent(False)