#!/usr/bin/env python3
"""
Intent Validation Enhancement Module

This module provides enhanced intent validation with confidence scoring,
context awareness, and fallback handling for the automotive chatbot.

Features:
- Confidence threshold validation
- Context-aware intent verification
- Multi-intent detection and handling
- Fallback intent suggestions
- Intent history tracking
- Conversation flow validation
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
from functools import lru_cache

# Enhanced cache for intent validation
from ..cache.enhanced_cache import enhanced_cache

logger = logging.getLogger(__name__)

@dataclass
class IntentValidationResult:
    """Result of intent validation"""
    is_valid: bool
    confidence_score: float
    validated_intent: str
    original_intent: str
    context_score: float
    suggestions: List[str]
    validation_reason: str
    requires_clarification: bool = False
    fallback_action: Optional[str] = None

@dataclass
class ConversationContext:
    """Conversation context for intent validation"""
    user_id: str
    conversation_id: str
    previous_intents: deque
    current_entities: Dict[str, Any]
    conversation_stage: str
    last_action: Optional[str]
    timestamp: datetime
    session_duration: timedelta

class IntentValidator:
    """Enhanced intent validator with confidence and context awareness"""
    
    def __init__(self):
        self.confidence_threshold = 0.5  # 降低默认阈值以减少fallback触发
        self.context_weight = 0.3
        self.intent_patterns = self._load_intent_patterns()
        self.context_rules = self._load_context_rules()
        self.conversation_contexts = {}
        self.intent_history = defaultdict(list)
        
        # Intent confidence thresholds by category
        self.intent_thresholds = {
            'book_appointment': 0.75,
            'cancel_appointment': 0.8,  # Higher threshold for destructive actions
            'view_appointments': 0.65,
            'ask_contact': 0.6,  # Contact information queries
            'ask_operating_hours': 0.55,  # Operating hours queries
            'ask_business_hours': 0.55,  # Business hours queries
            'ask_public_holiday_hours': 0.6,  # Holiday hours queries
            'calculate_loan': 0.6,  # Lowered to match action decorator
            'ask_coe_prices': 0.6,  # COE price queries
            'ask_coe_category': 0.6,  # COE category queries
            'ask_coe_category_a': 0.6,
            'ask_coe_category_b': 0.6,
            'ask_coe_category_c': 0.6,
            'ask_coe_category_d': 0.6,
            'ask_coe_category_e': 0.6,
            'ask_coe_bidding_process': 0.65,
            'ask_coe_trends': 0.65,
            'ask_coe_prediction': 0.65,
            'ask_coe_timing_recommendation': 0.65,
            'ask_coe_renewal': 0.6,  # COE renewal queries
            'ask_coe_renewal_assistance': 0.6,
            'ask_coe_bidding_assistance': 0.65,
            'ask_pqp_checker': 0.65,
            'greet': 0.5,
            'goodbye': 0.5,
            'affirm': 0.6,
            'deny': 0.6,
            'out_of_scope': 0.4,  # Lower threshold for fallback
            'nlu_fallback': 0.3
        }
        
        # Context-aware intent transitions
        self.valid_transitions = {
            'greet': ['book_appointment', 'view_appointments', 'ask_contact', 'ask_operating_hours', 'calculate_loan', 'ask_coe_prices', 'ask_coe_renewal'],
            'book_appointment': ['book_appointment', 'cancel_appointment', 'view_appointments', 'goodbye'],
            'cancel_appointment': ['view_appointments', 'book_appointment', 'goodbye'],
            'view_appointments': ['book_appointment', 'cancel_appointment', 'goodbye'],
            'ask_contact': ['book_appointment', 'ask_operating_hours', 'goodbye'],
            'ask_operating_hours': ['book_appointment', 'ask_contact', 'goodbye'],
            'ask_business_hours': ['book_appointment', 'ask_contact', 'goodbye'],
            'calculate_loan': ['book_appointment', 'ask_coe_prices', 'goodbye'],
            'ask_coe_prices': ['calculate_loan', 'book_appointment', 'ask_coe_renewal', 'ask_coe_trends', 'goodbye'],
            'ask_coe_renewal': ['ask_coe_prices', 'book_appointment', 'goodbye'],
            'ask_coe_trends': ['ask_coe_prices', 'ask_coe_timing_recommendation', 'goodbye'],
            'ask_coe_timing_recommendation': ['ask_coe_prices', 'ask_coe_trends', 'goodbye'],
            'affirm': ['book_appointment', 'cancel_appointment', 'view_appointments'],
            'deny': ['book_appointment', 'goodbye'],
            'out_of_scope': ['greet', 'ask_contact', 'goodbye'],
            'nlu_fallback': ['greet', 'ask_contact', 'goodbye']
        }
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent-specific patterns for validation"""
        return {
            'book_appointment': [
                r'\b(book|schedule|make|arrange)\b.*\b(appointment|visit|service)\b',
                r'\b(need|want|would like)\b.*\b(appointment|booking)\b',
                r'\b(set up|plan)\b.*\b(meeting|appointment)\b'
            ],
            'cancel_appointment': [
                r'\b(cancel|remove|delete)\b.*\b(appointment|booking)\b',
                r'\b(don\'t need|no longer need)\b.*\b(appointment)\b',
                r'\b(change of plans|can\'t make it)\b'
            ],
            'view_appointments': [
                r'\b(view|see|show|check|display|list)\b.*\b(appointment|booking)s?\b',
                r'\b(what|when|which)\b.*\b(appointment|booking)s?\b',
                r'\b(my|existing|current|scheduled)\b.*\b(appointment|booking)s?\b',
                r'\b(appointment|booking)s?\b.*\b(list|schedule|calendar)\b',
                r'\b(do i have|have i got)\b.*\b(appointment|booking)s?\b',
                r'^\s*(appointment|booking)s?\s*$',  # 单独的"appointments"
                r'\b(upcoming|future|next)\b.*\b(appointment|booking)s?\b'
            ],
            'calculate_loan': [
                r'\b(calculate|compute|estimate)\b.*\b(loan|financing)\b',
                r'\b(how much|what would)\b.*\b(monthly|payment)\b',
                r'\b(loan|financing|payment)\b.*\b(calculator|calculation)\b'
            ],
            'ask_coe_prices': [
                r'\b(coe|certificate of entitlement)\b.*\b(price|cost|rate)\b',
                r'\b(current|latest|today)\b.*\b(coe)\b',
                r'\b(how much|what is)\b.*\b(coe)\b',
                r'\b(coe)\b.*\b(pricing|rates|fees)\b'
            ],
            'ask_operating_hours': [
                r'\b(operating|business|opening|office)\b.*\b(hours|time)\b',
                r'\b(what time|when)\b.*\b(open|close)\b',
                r'\b(hours|time)\b.*\b(operation|business)\b',
                r'\b(open|close)\b.*\b(time|hours)\b',
                r'\b(what.*your)\b.*\b(operating|business)\b.*\b(hour|time)\b'
            ],
            'ask_business_hours': [
                r'\b(business|working)\b.*\b(hours|time)\b',
                r'\b(when.*open|when.*close)\b',
                r'\b(store|shop)\b.*\b(hours|timing)\b'
            ],
            'ask_contact': [
                r'\b(contact|phone|email|address)\b.*\b(information|details)\b',
                r'\b(how to|where to)\b.*\b(contact|reach)\b',
                r'\b(phone|email|address)\b.*\b(number|details)\b'
            ],
            'ask_coe_renewal': [
                r'\b(renew|renewal)\b.*\b(coe)\b',
                r'\b(how to)\b.*\b(renew)\b.*\b(coe)\b',
                r'\b(coe)\b.*\b(renewal|renew)\b',
                r'\b(extend|extension)\b.*\b(coe)\b'
            ],
            'ask_coe_trends': [
                r'\b(coe)\b.*\b(trend|trends|market)\b',
                r'\b(market)\b.*\b(analysis|trend)\b.*\b(coe)\b',
                r'\b(good time|best time)\b.*\b(buy|purchase)\b.*\b(coe)\b'
            ],
            'ask_coe_timing_recommendation': [
                r'\b(good time|best time|when)\b.*\b(buy|purchase|bid)\b.*\b(coe)\b',
                r'\b(should i|when to)\b.*\b(buy|bid)\b.*\b(coe)\b',
                r'\b(timing|when)\b.*\b(coe)\b.*\b(purchase|buy)\b'
            ]
        }
    
    def _load_context_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load context-aware validation rules"""
        return {
            'appointment_flow': {
                'required_entities': ['appointment_date', 'service_type'],
                'optional_entities': ['appointment_time', 'customer_name'],
                'context_intents': ['book_appointment', 'cancel_appointment', 'view_appointments']
            },
            'loan_calculation_flow': {
                'required_entities': ['loan_amount', 'loan_term'],
                'optional_entities': ['interest_rate', 'down_payment'],
                'context_intents': ['calculate_loan']
            },
            'contact_flow': {
                'required_entities': [],
                'optional_entities': ['contact_method'],
                'context_intents': ['ask_contact']
            }
        }
    
    async def validate_intent(
        self,
        intent: str,
        confidence: float,
        user_message: str,
        user_id: str,
        conversation_id: str,
        entities: Dict[str, Any] = None,
        previous_intent: str = None
    ) -> IntentValidationResult:
        """Validate intent with enhanced confidence and context checking"""
        
        entities = entities or {}
        
        # Get or create conversation context
        context = self._get_conversation_context(user_id, conversation_id)
        
        # Update context with current information
        context.current_entities = entities
        context.timestamp = datetime.now()
        
        # Add previous intent to history
        if previous_intent:
            context.previous_intents.append(previous_intent)
        
        # Perform validation checks
        confidence_valid = await self._validate_confidence(intent, confidence)
        pattern_valid = await self._validate_pattern(intent, user_message)
        context_valid = await self._validate_context(intent, context)
        transition_valid = await self._validate_transition(intent, context)
        
        # Calculate overall validation score
        validation_score = self._calculate_validation_score(
            confidence_valid, pattern_valid, context_valid, transition_valid
        )
        
        # Determine if intent is valid
        is_valid = validation_score['overall_score'] >= 0.4
        
        # Generate suggestions if needed
        suggestions = []
        fallback_action = None
        requires_clarification = False
        
        if not is_valid:
            suggestions = await self._generate_suggestions(intent, user_message, context)
            fallback_action = await self._determine_fallback_action(intent, context)
            requires_clarification = validation_score['overall_score'] < 0.4
        
        # Create validation result
        result = IntentValidationResult(
            is_valid=is_valid,
            confidence_score=confidence,
            validated_intent=intent if is_valid else suggestions[0] if suggestions else 'nlu_fallback',
            original_intent=intent,
            context_score=validation_score['context_score'],
            suggestions=suggestions,
            validation_reason=self._get_validation_reason(validation_score),
            requires_clarification=requires_clarification,
            fallback_action=fallback_action
        )
        
        # Cache the result
        cache_key = f"intent_validation:{user_id}:{conversation_id}:{intent}:{hash(user_message)}"
        enhanced_cache.set(cache_key, result, ttl=300)  # 5 minutes
        
        # Update conversation context
        self._update_conversation_context(context, result)
        
        return result
    
    async def _validate_confidence(self, intent: str, confidence: float) -> bool:
        """Validate intent confidence against thresholds"""
        threshold = self.intent_thresholds.get(intent, self.confidence_threshold)
        return confidence >= threshold
    
    async def _validate_pattern(self, intent: str, user_message: str) -> bool:
        """Validate intent against known patterns"""
        patterns = self.intent_patterns.get(intent, [])
        if not patterns:
            return True  # No patterns defined, assume valid
        
        message_lower = user_message.lower()
        return any(re.search(pattern, message_lower, re.IGNORECASE) for pattern in patterns)
    
    async def _validate_context(self, intent: str, context: ConversationContext) -> bool:
        """Validate intent against conversation context"""
        # Check if intent makes sense in current conversation stage
        if context.conversation_stage == 'greeting' and intent not in ['greet', 'ask_contact', 'out_of_scope', 'calculate_loan', 'get_coe_prices', 'ask_coe_prices', 'ask_coe_renewal', 'ask_coe_trends', 'ask_coe_timing_recommendation', 'ask_operating_hours', 'ask_business_hours', 'book_appointment', 'view_appointments']:
            return False
        
        # Check entity requirements for specific flows
        for flow_name, rules in self.context_rules.items():
            if intent in rules['context_intents']:
                required_entities = rules['required_entities']
                if required_entities:
                    missing_entities = set(required_entities) - set(context.current_entities.keys())
                    if missing_entities and context.conversation_stage != 'entity_collection':
                        return False
        
        return True
    
    async def _validate_transition(self, intent: str, context: ConversationContext) -> bool:
        """Validate intent transition from previous intent"""
        if not context.previous_intents:
            return True  # First intent in conversation
        
        last_intent = context.previous_intents[-1]
        valid_next_intents = self.valid_transitions.get(last_intent, [])
        
        # Allow any intent if no restrictions defined
        if not valid_next_intents:
            return True
        
        return intent in valid_next_intents
    
    def _calculate_validation_score(self, confidence_valid: bool, pattern_valid: bool, 
                                  context_valid: bool, transition_valid: bool) -> Dict[str, float]:
        """Calculate overall validation score"""
        confidence_score = 1.0 if confidence_valid else 0.0
        pattern_score = 1.0 if pattern_valid else 0.0
        context_score = 1.0 if context_valid else 0.0
        transition_score = 1.0 if transition_valid else 0.0
        
        # Weighted average
        overall_score = (
            confidence_score * 0.4 +
            pattern_score * 0.3 +
            context_score * 0.2 +
            transition_score * 0.1
        )
        
        return {
            'overall_score': overall_score,
            'confidence_score': confidence_score,
            'pattern_score': pattern_score,
            'context_score': context_score,
            'transition_score': transition_score
        }
    
    async def _generate_suggestions(self, intent: str, user_message: str, 
                                  context: ConversationContext) -> List[str]:
        """Generate alternative intent suggestions"""
        suggestions = []
        
        # Check for similar intents based on patterns
        message_lower = user_message.lower()
        
        for candidate_intent, patterns in self.intent_patterns.items():
            if candidate_intent != intent:
                for pattern in patterns:
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        suggestions.append(candidate_intent)
                        break
        
        # Add context-based suggestions
        if context.previous_intents:
            last_intent = context.previous_intents[-1]
            valid_next = self.valid_transitions.get(last_intent, [])
            suggestions.extend([i for i in valid_next if i not in suggestions])
        
        # Limit to top 3 suggestions
        return suggestions[:3]
    
    async def _determine_fallback_action(self, intent: str, context: ConversationContext) -> Optional[str]:
        """Determine appropriate fallback action"""
        if context.conversation_stage == 'greeting':
            return 'utter_greet'
        elif len(context.previous_intents) == 0:
            return 'utter_greet'
        elif intent in ['out_of_scope', 'nlu_fallback']:
            return 'utter_ask_rephrase'
        else:
            return 'utter_default'
    
    def _get_validation_reason(self, validation_score: Dict[str, float]) -> str:
        """Get human-readable validation reason"""
        if validation_score['overall_score'] >= 0.8:
            return "High confidence validation"
        elif validation_score['overall_score'] >= 0.6:
            return "Moderate confidence validation"
        elif validation_score['confidence_score'] == 0.0:
            return "Low confidence score"
        elif validation_score['pattern_score'] == 0.0:
            return "Pattern mismatch"
        elif validation_score['context_score'] == 0.0:
            return "Context validation failed"
        elif validation_score['transition_score'] == 0.0:
            return "Invalid intent transition"
        else:
            return "Multiple validation issues"
    
    def _get_conversation_context(self, user_id: str, conversation_id: str) -> ConversationContext:
        """Get or create conversation context"""
        context_key = f"{user_id}:{conversation_id}"
        
        if context_key not in self.conversation_contexts:
            self.conversation_contexts[context_key] = ConversationContext(
                user_id=user_id,
                conversation_id=conversation_id,
                previous_intents=deque(maxlen=5),  # Keep last 5 intents
                current_entities={},
                conversation_stage='greeting',
                last_action=None,
                timestamp=datetime.now(),
                session_duration=timedelta(0)
            )
        
        return self.conversation_contexts[context_key]
    
    def _update_conversation_context(self, context: ConversationContext, 
                                   result: IntentValidationResult) -> None:
        """Update conversation context after validation"""
        if result.is_valid:
            context.previous_intents.append(result.validated_intent)
            
            # Update conversation stage based on intent
            if result.validated_intent == 'greet':
                context.conversation_stage = 'active'
            elif result.validated_intent in ['book_appointment', 'cancel_appointment']:
                context.conversation_stage = 'appointment_flow'
            elif result.validated_intent == 'calculate_loan':
                context.conversation_stage = 'loan_flow'
            elif result.validated_intent == 'goodbye':
                context.conversation_stage = 'ending'
        
        # Update session duration
        context.session_duration = datetime.now() - context.timestamp
    
    @lru_cache(maxsize=100)
    def get_intent_confidence_threshold(self, intent: str) -> float:
        """Get confidence threshold for specific intent"""
        return self.intent_thresholds.get(intent, self.confidence_threshold)
    
    async def validate_entity_extraction(self, entities: Dict[str, Any], 
                                       intent: str) -> Dict[str, Any]:
        """Validate extracted entities for given intent"""
        validated_entities = {}
        
        # Intent-specific entity validation
        if intent == 'book_appointment':
            validated_entities = await self._validate_appointment_entities(entities)
        elif intent == 'calculate_loan':
            validated_entities = await self._validate_loan_entities(entities)
        else:
            validated_entities = entities
        
        return validated_entities
    
    async def _validate_appointment_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Validate appointment-related entities"""
        validated = {}
        
        # Validate date
        if 'appointment_date' in entities:
            date_value = entities['appointment_date']
            # Add date validation logic here
            validated['appointment_date'] = date_value
        
        # Validate time
        if 'appointment_time' in entities:
            time_value = entities['appointment_time']
            # Add time validation logic here
            validated['appointment_time'] = time_value
        
        # Validate service type
        if 'service_type' in entities:
            service_value = entities['service_type']
            # Add service type validation logic here
            validated['service_type'] = service_value
        
        return validated
    
    async def _validate_loan_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Validate loan calculation entities"""
        validated = {}
        
        # Validate loan amount
        if 'loan_amount' in entities:
            amount = entities['loan_amount']
            try:
                amount_float = float(amount)
                if amount_float > 0:
                    validated['loan_amount'] = amount_float
            except (ValueError, TypeError):
                pass
        
        # Validate loan term
        if 'loan_term' in entities:
            term = entities['loan_term']
            try:
                term_int = int(term)
                if 1 <= term_int <= 10:  # 1-10 years
                    validated['loan_term'] = term_int
            except (ValueError, TypeError):
                pass
        
        return validated
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total_contexts = len(self.conversation_contexts)
        active_contexts = sum(1 for ctx in self.conversation_contexts.values() 
                            if ctx.conversation_stage != 'ending')
        
        return {
            'total_conversations': total_contexts,
            'active_conversations': active_contexts,
            'intent_thresholds': self.intent_thresholds,
            'validation_cache_size': len(enhanced_cache._cache)
        }

# Global intent validator instance
intent_validator = IntentValidator()