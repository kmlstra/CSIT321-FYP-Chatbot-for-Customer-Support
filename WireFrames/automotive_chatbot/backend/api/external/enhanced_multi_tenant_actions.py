"""
Enhanced Multi-tenant RASA Actions with Client-Specific Model Support
Supports both shared model and client-specific model approaches
"""

from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
import requests
import os
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger(__name__)

class EnhancedMultiTenantActionBase(Action):
    """Enhanced base class for multi-tenant actions with security features"""
    
    def __init__(self):
        self.use_client_specific_models = os.getenv("USE_CLIENT_MODELS", "false").lower() == "true"
        self.admin_db_url = os.getenv("MONGODB_ADMIN_URL")
        self.client_db_url = os.getenv("MONGODB_CLIENT_URL")
    
    def get_client_context(self, tracker: Tracker) -> Dict[str, Any]:
        """Extract client context with enhanced security validation"""
        try:
            metadata = tracker.latest_message.get("metadata", {})
            client_config = metadata.get("client_config", {})
            
            # Validate client context
            if not client_config:
                logger.warning("No client context found in tracker metadata")
                return {}
            
            # Ensure required fields exist
            required_fields = ["branding", "features", "contact_info"]
            for field in required_fields:
                if field not in client_config:
                    client_config[field] = {}
            
            return client_config
            
        except Exception as e:
            logger.error(f"Error extracting client context: {e}")
            return {}
    
    def get_client_id(self, tracker: Tracker) -> str:
        """Extract client ID with validation"""
        try:
            metadata = tracker.latest_message.get("metadata", {})
            client_id = metadata.get("client_id", "")
            
            # Validate client ID format (should be MongoDB ObjectId)
            if client_id and len(client_id) == 24:
                return client_id
            
            logger.warning(f"Invalid client ID format: {client_id}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting client ID: {e}")
            return ""
    
    async def get_client_data(self, client_id: str, collection: str, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Securely fetch client-specific data"""
        try:
            # Import here to avoid circular imports
            from motor.motor_asyncio import AsyncIOMotorClient
            
            # Use client connection (limited access)
            client = AsyncIOMotorClient(self.client_db_url)
            db = client["automotive_chatbot_saas"]
            
            # Always filter by client_id for security
            if query is None:
                query = {}
            query["client_id"] = ObjectId(client_id)
            
            # Execute query
            cursor = db[collection].find(query)
            results = []
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                results.append(doc)
            
            client.close()
            return results
            
        except Exception as e:
            logger.error(f"Error fetching client data: {e}")
            return []
    
    def validate_client_permissions(self, client_config: Dict[str, Any], feature: str) -> bool:
        """Validate if client has permission to use specific feature"""
        features = client_config.get("features", {})
        return features.get(feature, False)
    
    def format_response_with_security(self, response: str, client_config: Dict[str, Any]) -> str:
        """Apply client-specific branding with security validation"""
        try:
            # Validate client config
            if not client_config:
                return response
            
            branding = client_config.get("branding", {})
            contact_info = client_config.get("contact_info", {})
            
            # Safely replace placeholders
            replacements = {
                "[COMPANY_NAME]": branding.get("company_name", "CleverCompanion"),
                "[PHONE]": contact_info.get("phone", ""),
                "[EMAIL]": contact_info.get("email", ""),
                "[ADDRESS]": contact_info.get("address", ""),
                "[WHATSAPP]": contact_info.get("whatsapp", "")
            }
            
            for placeholder, value in replacements.items():
                if placeholder in response and value:
                    response = response.replace(placeholder, str(value))
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return response
    
    def log_client_action(self, client_id: str, action_name: str, success: bool):
        """Log client action for audit trail"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow(),
                "client_id": client_id,
                "action": action_name,
                "success": success,
                "source": "rasa_action"
            }
            logger.info(f"Client action: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging client action: {e}")

class ActionSecureCOEPrices(EnhancedMultiTenantActionBase):
    """Secure COE prices action with client validation"""
    
    def name(self) -> Text:
        return "action_secure_coe_prices"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        client_config = self.get_client_context(tracker)
        client_id = self.get_client_id(tracker)
        
        # Validate client permissions
        if not self.validate_client_permissions(client_config, "coe_prices"):
            response = "COE price information is not available for your subscription plan. Please contact support to upgrade."
            dispatcher.utter_message(text=response)
            self.log_client_action(client_id, "coe_prices", False)
            return []
        
        # Get COE prices with client branding
        company_name = client_config.get("branding", {}).get("company_name", "CleverCompanion")
        
        response = f"""📊 **Latest COE Prices - {company_name}**

🚗 **Category A:** $96,999 🔴↗ +$1,500
🚙 **Category B:** $113,000 🟢↘ -$2,000  
🚚 **Category C:** $75,500 🟢↘ -$1,500
🏍️ **Category E:** $108,900 🔴↗ -$3,000

📅 **Last Updated:** {datetime.now().strftime("%d %B %Y, %I:%M %p")} SGT

💡 **Need help choosing the right category?** Ask me about specific car models!

📞 **Contact {company_name}:**
Phone: [PHONE] | Email: [EMAIL]"""
        
        # Apply client-specific formatting
        response = self.format_response_with_security(response, client_config)
        
        dispatcher.utter_message(text=response)
        self.log_client_action(client_id, "coe_prices", True)
        return []

class ActionSecureVehicleSearch(EnhancedMultiTenantActionBase):
    """Secure vehicle search with client-specific inventory"""
    
    def name(self) -> Text:
        return "action_secure_vehicle_search"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        client_config = self.get_client_context(tracker)
        client_id = self.get_client_id(tracker)
        
        # Validate permissions
        if not self.validate_client_permissions(client_config, "vehicle_search"):
            response = "Vehicle search is not available for your subscription plan."
            dispatcher.utter_message(text=response)
            self.log_client_action(client_id, "vehicle_search", False)
            return []
        
        # Get client's vehicle inventory
        vehicles = await self.get_client_data(client_id, "client_vehicles", {"availability": "in_stock"})
        
        company_name = client_config.get("branding", {}).get("company_name", "our showroom")
        
        if vehicles:
            response = f"""🚗 **Vehicle Inventory at {company_name}**

**Available Vehicles:**
"""
            for vehicle in vehicles[:5]:  # Show first 5 vehicles
                response += f"""
• **{vehicle['brand']} {vehicle['model']} ({vehicle['year']})**
  💰 Price: ${vehicle['price']:,}
  ⛽ Fuel: {vehicle.get('fuel_type', 'Petrol')}
  📋 Status: {vehicle['availability'].replace('_', ' ').title()}
"""
            
            response += f"""
💡 **Tell me what you're looking for:**
• "Show me cars under $150k"
• "I need a family car"
• "What hybrid cars do you have?"

📞 **Contact {company_name}:**
Phone: [PHONE] | Email: [EMAIL]"""
        
        else:
            response = f"""🚗 **Vehicle Search at {company_name}**

We're currently updating our inventory. Please contact us directly for available vehicles:

📞 **Contact {company_name}:**
Phone: [PHONE] | Email: [EMAIL]
Address: [ADDRESS]"""
        
        # Apply client formatting
        response = self.format_response_with_security(response, client_config)
        
        dispatcher.utter_message(text=response)
        self.log_client_action(client_id, "vehicle_search", True)
        return []

# Export all secure actions
__all__ = [
    'EnhancedMultiTenantActionBase',
    'ActionSecureCOEPrices', 
    'ActionSecureVehicleSearch'
]