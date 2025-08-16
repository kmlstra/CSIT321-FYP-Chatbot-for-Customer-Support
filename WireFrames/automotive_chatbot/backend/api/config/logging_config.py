"""Logging Configuration for CleverCompanion Backend
Configures logging levels and formatters for different modules
"""

import logging
import logging.config
import os
from pathlib import Path

def setup_logging():
    """Setup logging configuration for the entire application"""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(os.path.dirname(__file__)).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Logging configuration
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(logs_dir / 'clevercompanion.log'),
                'mode': 'a',
                'encoding': 'utf-8'
            },
            'appointment_file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(logs_dir / 'appointments.log'),
                'mode': 'a',
                'encoding': 'utf-8'
            },
            'conversation_file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(logs_dir / 'conversations.log'),
                'mode': 'a',
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            # Root logger
            '': {
                'level': 'INFO',
                'handlers': ['console', 'file']
            },
            # Appointment actions - DEBUG level with dedicated file
            'api.actions.appointment_actions': {
                'level': 'DEBUG',
                'handlers': ['console', 'appointment_file'],
                'propagate': False
            },
            # Conversation storage - DEBUG level with dedicated file
            'api.services.conversation_storage': {
                'level': 'DEBUG',
                'handlers': ['console', 'conversation_file'],
                'propagate': False
            },
            # FastAPI and uvicorn
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'fastapi': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            # MongoDB motor
            'motor': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            # Other modules at INFO level
            'api': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        }
    }
    
    # Apply the logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Log that logging has been configured
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration applied successfully")
    logger.info(f"Log files will be written to: {logs_dir}")
    logger.debug("DEBUG level logging enabled for appointment_actions and conversation_storage")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)