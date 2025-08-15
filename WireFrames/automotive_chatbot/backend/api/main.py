from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import Optional
from .config import Settings
from .middleware.conversation_middleware import ConversationAPI
from .middleware.auto_logger import ConversationLogger

# Configure logger
logger = logging.getLogger(__name__)
# from .database import startup_database, shutdown_database, get_database

# Load environment variables - look in multiple locations
from pathlib import Path
import os

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "../.env")
if Path(env_path).exists():
    load_dotenv(dotenv_path=env_path)
else:
    print("⚠️ Warning: backend/.env file not found. API may not function properly.")

settings = Settings()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - using static information.py, no database needed
    print("Starting Automotive Chatbot API v2.0...")
    yield
    # Shutdown
    print("Shutting down Automotive Chatbot API v2.0...")

app = FastAPI(
    title="Automotive Chatbot Platform",
    description="Advanced AI-powered automotive assistant with RAG capabilities",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_path = os.path.join(os.path.dirname(__file__), "../static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Automotive Chatbot API v2.0",
        "features": [
            "Real-time COE pricing from LTA",
            "RAG-enhanced AI responses",
            "Embeddable widget API",
            "VectorDB knowledge base",
            "LangChain integration"
        ],
        "documentation": "/docs",
        "health": "/health",
        "widget_demo": "/api/widget/embed.js?widget_id=demo"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "api": "running",
            "information_service": "available",
            "coe_service": "available",
            "rag_service": "available" if os.getenv("OPENAI_API_KEY") else "limited"
        }
    }

from fastapi import APIRouter

# Essential boundaries for RASA actions
vehicle_router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])
coe_router = APIRouter(prefix="/api/coe", tags=["coe"])

@vehicle_router.get("/")
async def get_vehicles_fallback():
    return {"success": True, "vehicles": [], "message": "Vehicle service initializing"}

@coe_router.get("/prices")
async def get_coe_prices_fallback():
    return {"success": True, "data": {"category_a": {"current": 95000}}, "message": "COE service initializing"}

app.include_router(vehicle_router)
app.include_router(coe_router)

# Conversation Management API
conversation_router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@conversation_router.get("/history/{session_id}")
async def get_conversation_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to retrieve")
):
    """Get conversation history for a specific session."""
    try:
        result = ConversationAPI.get_conversation_history(session_id, limit)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation history: {str(e)}")

@conversation_router.get("/sessions/active")
async def get_active_sessions():
    """Get information about currently active sessions."""
    try:
        result = ConversationAPI.get_active_sessions()
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving active sessions: {str(e)}")

@conversation_router.post("/cleanup")
async def cleanup_expired_sessions(background_tasks: BackgroundTasks):
    """Clean up expired conversation sessions."""
    try:
        # Run cleanup in background to avoid blocking
        def cleanup_task():
            return ConversationAPI.cleanup_expired_sessions()
        
        background_tasks.add_task(cleanup_task)
        return JSONResponse(content={
            "message": "Cleanup task started",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting cleanup task: {str(e)}")

@conversation_router.get("/stats")
async def get_conversation_stats():
    """Get conversation statistics."""
    try:
        active_sessions = ConversationAPI.get_active_sessions()
        return JSONResponse(content={
            "active_sessions": active_sessions.get("active_sessions", 0),
            "session_timeout_minutes": 30,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation stats: {str(e)}")

app.include_router(conversation_router)

# Chat History Viewer API (for frontend compatibility)
chat_history_router = APIRouter(prefix="/api/conversation", tags=["chat-history"])

@chat_history_router.get("/history")
async def get_all_conversations(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of conversations to retrieve")
):
    """Get all conversation history for chat history viewer."""
    try:
        # Get all active sessions and their conversation data
        active_sessions = ConversationAPI.get_active_sessions()
        all_conversations = []
        
        # For now, return a sample structure that matches frontend expectations
        # In a real implementation, you'd iterate through all stored conversations
        sample_conversations = [
            {
                "id": "conv_001",
                "timestamp": "2024-01-15T10:30:00Z",
                "content": "User: Hello\nBot: Hi there! How can I help you today?\nUser: I need information about car loans\nBot: I'd be happy to help you with car loan information.",
                "message_count": 4
            },
            {
                "id": "conv_002", 
                "timestamp": "2024-01-15T11:45:00Z",
                "content": "User: What are the COE prices?\nBot: Let me get the latest COE prices for you.",
                "message_count": 2
            },
            {
                "id": "conv_003",
                "timestamp": "2024-01-15T14:20:00Z", 
                "content": "User: I want to contact support\nBot: Here's how you can reach our support team.",
                "message_count": 2
            }
        ]
        
        return JSONResponse(content={
            "success": True,
            "conversations": sample_conversations[:limit]
        })
    except Exception as e:
        logger.error(f"Error in get_all_conversations: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error retrieving conversations: {str(e)}"
        }, status_code=500)

@chat_history_router.get("/history/{conversation_id}")
async def get_conversation_for_viewer(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to retrieve")
):
    """Get conversation history for chat history viewer (frontend compatibility endpoint)."""
    try:
        # Use the existing ConversationAPI with session_id as conversation_id
        result = ConversationAPI.get_conversation_history(conversation_id, limit)
        
        # Transform the response to match frontend expectations
        if result and result.get('messages') and len(result['messages']) > 0:
            # Frontend expects: {"success": true, "conversation": [conversation_data]}
            conversation_data = result['messages'][0]  # Get the first (and likely only) conversation record
            
            # Ensure the conversation data has the expected structure
            formatted_conversation = {
                "conversation_id": conversation_id,
                "timestamp": conversation_data.get('timestamp', ''),
                "content": conversation_data.get('content', ''),
                "message_count": result.get('message_count', 0)
            }
            
            return JSONResponse(content={
                "success": True,
                "conversation": [formatted_conversation]
            })
        else:
            # No conversation found
            return JSONResponse(content={
                "success": False,
                "message": f"No conversation found with ID: {conversation_id}"
            })
    except Exception as e:
        logger.error(f"Error in get_conversation_for_viewer: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error retrieving conversation history: {str(e)}"
        }, status_code=500)

app.include_router(chat_history_router)

# Appointment Management API
appointment_router = APIRouter(prefix="/api/appointments", tags=["appointments"])

@appointment_router.get("/")
async def get_all_appointments(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of appointments to retrieve"),
    status: str = Query(None, description="Filter by appointment status")
):
    """Get all appointments for admin dashboard."""
    try:
        from backend.config.database import DatabaseContext
        
        with DatabaseContext('appointments') as collection:
            if not collection:
                return JSONResponse(content={
                    "success": False,
                    "error": "Database not available"
                }, status_code=500)
            
            # Build query filter
            query_filter = {}
            if status:
                query_filter["status"] = status
            
            # Get appointments sorted by date (newest first)
            appointments = list(collection.find(query_filter).sort("appointment_datetime", -1).limit(limit))
            
            # Convert ObjectId to string and format datetime
            for apt in appointments:
                apt["_id"] = str(apt["_id"])
                if isinstance(apt["appointment_datetime"], datetime):
                    apt["appointment_datetime"] = apt["appointment_datetime"].isoformat()
                if "created_at" in apt and isinstance(apt["created_at"], datetime):
                    apt["created_at"] = apt["created_at"].isoformat()
            
            return JSONResponse(content={
                "success": True,
                "appointments": appointments,
                "total": len(appointments)
            })
            
    except Exception as e:
        logger.error(f"Error in get_all_appointments: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error retrieving appointments: {str(e)}"
        }, status_code=500)

@appointment_router.get("/customer/{phone}")
async def get_customer_appointments(
    phone: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of appointments to retrieve")
):
    """Get appointments for a specific customer by phone number."""
    try:
        from backend.config.database import DatabaseContext
        
        with DatabaseContext('appointments') as collection:
            if not collection:
                return JSONResponse(content={
                    "success": False,
                    "error": "Database not available"
                }, status_code=500)
            
            # Get customer appointments
            appointments = list(collection.find({
                "customer_phone": phone
            }).sort("appointment_datetime", -1).limit(limit))
            
            # Convert ObjectId to string and format datetime
            for apt in appointments:
                apt["_id"] = str(apt["_id"])
                if isinstance(apt["appointment_datetime"], datetime):
                    apt["appointment_datetime"] = apt["appointment_datetime"].isoformat()
                if "created_at" in apt and isinstance(apt["created_at"], datetime):
                    apt["created_at"] = apt["created_at"].isoformat()
            
            return JSONResponse(content={
                "success": True,
                "appointments": appointments,
                "customer_phone": phone
            })
            
    except Exception as e:
        logger.error(f"Error in get_customer_appointments: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error retrieving customer appointments: {str(e)}"
        }, status_code=500)

@appointment_router.put("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: str,
    status_data: dict
):
    """Update appointment status."""
    try:
        from backend.config.database import DatabaseContext
        
        new_status = status_data.get("status")
        if new_status not in ["confirmed", "pending", "cancelled", "completed"]:
            return JSONResponse(content={
                "success": False,
                "error": "Invalid status. Must be one of: confirmed, pending, cancelled, completed"
            }, status_code=400)
        
        with DatabaseContext('appointments') as collection:
            if not collection:
                return JSONResponse(content={
                    "success": False,
                    "error": "Database not available"
                }, status_code=500)
            
            result = collection.update_one(
                {"appointment_id": appointment_id},
                {
                    "$set": {
                        "status": new_status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                return JSONResponse(content={
                    "success": True,
                    "message": f"Appointment status updated to {new_status}"
                })
            else:
                return JSONResponse(content={
                    "success": False,
                    "error": "Appointment not found"
                }, status_code=404)
            
    except Exception as e:
        logger.error(f"Error in update_appointment_status: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error updating appointment status: {str(e)}"
        }, status_code=500)

app.include_router(appointment_router)

# RASA Proxy for conversation logging
from .rasa_proxy import router as rasa_proxy_router
app.include_router(rasa_proxy_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)