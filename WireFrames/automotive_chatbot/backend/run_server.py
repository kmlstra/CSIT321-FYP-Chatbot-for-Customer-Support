#!/usr/bin/env python3
"""Simple server startup script for the consolidated backend"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Add the project root to Python path for imports
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

try:
    import uvicorn
    from api.main import app
    
    if __name__ == "__main__":
        print("Starting Automotive Chatbot API Server...")
        print(f"Backend directory: {backend_dir}")
        print(f"Project root: {project_root}")
        print("Server will be available at: http://localhost:8000")
        print("API documentation: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop the server\n")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(backend_dir)]
        )
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install fastapi uvicorn motor python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)