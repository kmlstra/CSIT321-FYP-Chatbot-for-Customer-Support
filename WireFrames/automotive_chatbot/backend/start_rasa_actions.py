#!/usr/bin/env python3
"""
Rasa Actions Server Startup Script with Environment Variable Loading
Loads environment variables from .env file and starts Rasa actions server
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    # Get the backend directory path
    backend_dir = Path(__file__).parent
    env_file = backend_dir / '.env'
    
    if env_file.exists():
        print(f"Loading environment variables from: {env_file}")
        load_dotenv(env_file)
        print("Environment variables loaded successfully")
    else:
        print(f"Warning: .env file not found at {env_file}")
        print("Using default environment variables")

def start_rasa_actions():
    """Start Rasa actions server with loaded environment variables"""
    try:
        # Change to backend directory
        backend_dir = Path(__file__).parent
        os.chdir(backend_dir)
        
        # Get port from environment or use default
        actions_port = os.getenv('RASA_ACTIONS_PORT', '5055')
        
        # Rasa actions command arguments
        rasa_actions_cmd = [
            sys.executable, '-m', 'rasa', 'run', 'actions',
            '--actions', 'actions',
            '--port', actions_port
        ]
        
        print(f"Starting Rasa actions server with command: {' '.join(rasa_actions_cmd)}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Actions port: {actions_port}")
        
        # Start Rasa actions server
        subprocess.run(rasa_actions_cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error starting Rasa actions server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nRasa actions server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("[ACTIONS] Starting Rasa actions server with environment configuration...")
    load_environment()
    start_rasa_actions()