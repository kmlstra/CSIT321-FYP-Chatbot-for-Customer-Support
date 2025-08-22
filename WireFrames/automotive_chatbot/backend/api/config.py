from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    MONGODB_URL: str = "mongodb+srv://CleverAdmin:P%40ssw0rd%211@clevercompanioncluster.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"
    MONGODB_DB: str = "automotive_chatbot_saas"

    # RASA
    RASA_HOST: str = "0.0.0.0"
    RASA_PORT: int = 5005
    RASA_TOKEN: Optional[str] = None

    # OpenAI (Optional)
    OPENAI_API_KEY: Optional[str] = None

    # COE Data API Configuration (data.gov.sg)
    COE_DATASET_ID: str = "d_69b3380ad7e51aff3a7dcc84eba52b8a"
    COE_API_URL: str = "https://data.gov.sg/api/action/datastore_search"
    
    # Legacy LTA DataMall API (kept for other services if needed)
    LTA_API_KEY: str = "MISSING_LTA_API_KEY"  # Should be set in .env file
    LTA_BASE_URL: str = "https://datamall2.mytransport.sg/ltaodataservice/"
    
    # Rate Limiting Configuration (to prevent API abuse)
    LTA_RATE_LIMIT_REQUESTS: int = 100  # Max requests per hour
    LTA_RATE_LIMIT_WINDOW: int = 3600   # 1 hour in seconds
    LTA_MIN_REQUEST_INTERVAL: int = 10  # Minimum 10 seconds between requests
    CACHE_EXPIRY_MINUTES: int = 30      # Cache COE data for 30 minutes

    # Frontend URLs (for CORS) - Hardcoded to AWS IP
    # URLs Configuration - All hardcoded to AWS server IP 13.215.240.173
    DOMAIN: str = "http://13.215.240.173"
    FRONTEND_URL: str = "http://13.215.240.173:3000"
    BACKEND_URL: str = "http://13.215.240.173:8000"
    RASA_URL: str = "http://13.215.240.173:5005"
    RASA_ACTIONS_URL: str = "http://13.215.240.173:5055"
    class Config:
        env_file = "backend/.env"
        case_sensitive = True
        extra = "allow"

settings = Settings()