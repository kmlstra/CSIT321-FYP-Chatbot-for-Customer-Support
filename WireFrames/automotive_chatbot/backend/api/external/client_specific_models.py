"""
Client-Specific RASA Models (Optional Enhancement)
For maximum security - each client gets their own trained model
"""

import os
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import shutil

class ClientModelManager:
    """Manages individual RASA models per client"""
    
    def __init__(self, base_model_path: str = "backend/models"):
        self.base_model_path = Path(base_model_path)
        self.client_models_path = Path("backend/client_models")
        self.client_models_path.mkdir(exist_ok=True)
    
    async def create_client_model(self, client_id: str, client_config: Dict[str, Any]) -> bool:
        """Create a client-specific RASA model"""
        try:
            client_model_dir = self.client_models_path / client_id
            client_model_dir.mkdir(exist_ok=True)
            
            # Copy base training data
            await self._copy_base_training_data(client_model_dir)
            
            # Customize training data for client
            await self._customize_training_data(client_model_dir, client_config)
            
            # Train client-specific model
            model_path = await self._train_client_model(client_id, client_model_dir)
            
            return model_path is not None
            
        except Exception as e:
            print(f"Failed to create model for client {client_id}: {e}")
            return False
    
    async def _copy_base_training_data(self, client_dir: Path):
        """Copy base training data to client directory"""
        base_data_dir = Path("backend/data")
        client_data_dir = client_dir / "data"
        client_data_dir.mkdir(exist_ok=True)
        
        # Copy base files
        for file in ["nlu.yml", "stories.yml", "rules.yml"]:
            if (base_data_dir / file).exists():
                shutil.copy2(base_data_dir / file, client_data_dir / file)
        
        # Copy config files
        for file in ["config.yml", "domain.yml", "endpoints.yml"]:
            if (Path("backend") / file).exists():
                shutil.copy2(Path("backend") / file, client_dir / file)
    
    async def _customize_training_data(self, client_dir: Path, client_config: Dict[str, Any]):
        """Customize training data with client-specific information"""
        
        # Update domain.yml with client-specific responses
        domain_path = client_dir / "domain.yml"
        if domain_path.exists():
            with open(domain_path, 'r') as f:
                domain = yaml.safe_load(f)
            
            # Customize responses with client branding
            company_name = client_config.get("branding", {}).get("company_name", "CleverCompanion")
            
            # Update greeting response
            if "responses" in domain and "utter_greet" in domain["responses"]:
                domain["responses"]["utter_greet"] = [
                    {"text": f"👋 Hi there! I'm the {company_name} automotive assistant. How can I help you today?"}
                ]
            
            # Save updated domain
            with open(domain_path, 'w') as f:
                yaml.dump(domain, f, default_flow_style=False)
        
        # Add client-specific training examples
        await self._add_client_training_examples(client_dir, client_config)
    
    async def _add_client_training_examples(self, client_dir: Path, client_config: Dict[str, Any]):
        """Add client-specific training examples"""
        nlu_path = client_dir / "data" / "nlu.yml"
        
        if nlu_path.exists():
            company_name = client_config.get("branding", {}).get("company_name", "CleverCompanion")
            
            # Add company-specific examples
            client_examples = f"""
# Client-specific examples for {company_name}
- intent: greet
  examples: |
    - hello {company_name}
    - hi there {company_name}
    - good morning {company_name}

- intent: ask_contact
  examples: |
    - how to contact {company_name}
    - {company_name} phone number
    - {company_name} location
"""
            
            # Append to existing NLU file
            with open(nlu_path, 'a') as f:
                f.write(client_examples)
    
    async def _train_client_model(self, client_id: str, client_dir: Path) -> Optional[str]:
        """Train RASA model for specific client"""
        try:
            # Change to client directory
            original_dir = os.getcwd()
            os.chdir(client_dir)
            
            # Train model
            result = subprocess.run([
                "python", "-m", "rasa", "train",
                "--out", f"../models/{client_id}",
                "--force"
            ], capture_output=True, text=True)
            
            # Return to original directory
            os.chdir(original_dir)
            
            if result.returncode == 0:
                print(f"✅ Model trained successfully for client {client_id}")
                return f"backend/models/{client_id}"
            else:
                print(f"❌ Model training failed for client {client_id}: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Training error for client {client_id}: {e}")
            return None
    
    def get_client_model_path(self, client_id: str) -> Optional[str]:
        """Get path to client's trained model"""
        model_dir = Path(f"backend/models/{client_id}")
        if model_dir.exists():
            # Find the latest model file
            model_files = list(model_dir.glob("*.tar.gz"))
            if model_files:
                return str(max(model_files, key=os.path.getctime))
        return None
    
    async def delete_client_model(self, client_id: str) -> bool:
        """Delete client's model and training data"""
        try:
            # Delete training data
            client_dir = self.client_models_path / client_id
            if client_dir.exists():
                shutil.rmtree(client_dir)
            
            # Delete trained model
            model_dir = Path(f"backend/models/{client_id}")
            if model_dir.exists():
                shutil.rmtree(model_dir)
            
            print(f"✅ Deleted model for client {client_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete model for client {client_id}: {e}")
            return False

# Usage example:
"""
# Create client-specific model
model_manager = ClientModelManager()
client_config = {
    "branding": {
        "company_name": "ABC Motors Singapore"
    },
    "features": {
        "coe_prices": True,
        "loan_calculator": True
    }
}

success = await model_manager.create_client_model("client_123", client_config)
if success:
    model_path = model_manager.get_client_model_path("client_123")
    print(f"Client model ready at: {model_path}")
"""