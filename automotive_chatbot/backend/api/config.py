from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "chatbot_platform"

    # RASA
    RASA_HOST: str = "localhost"
    RASA_PORT: int = 5005
    RASA_TOKEN: Optional[str] = None

    # OpenAI (Optional)
    OPENAI_API_KEY: Optional[str] = None

    # Frontend URLs (for CORS)
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 