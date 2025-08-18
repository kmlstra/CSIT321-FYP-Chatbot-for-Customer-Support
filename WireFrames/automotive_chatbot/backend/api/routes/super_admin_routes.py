"""
Super Admin API Routes
Handles super admin operations for managing all clients
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import pytz

from ..client_management.client_crud import ClientCRUD
from ..auth.client_auth import get_super_admin_user
from ..config.database import get_real_admin_db
from ..utils.performance_monitor import get_performance_monitor
from ..utils.health_monitor import HealthMonitor

router = APIRouter()

class ClientApprovalRequest(BaseModel):
    action: str  # "approve" or "reject"
    reason: Optional[str] = None

class SystemMetricsResponse(BaseModel):
    total_clients: int
    active_clients: int
    pending_approvals: int
    total_conversations_today: int
    revenue_this_month: float
    system_uptime: float

@router.get("/clients", dependencies=[Depends(get_super_admin_user)])
async def get_all_clients(
    status: Optional[str] = None,
    database = Depends(get_real_admin_db)
):
    """Get all clients with optional status filter"""
    
    try:
        client_crud = ClientCRUD(database)
        clients = await client_crud.get_all_clients(status)
        
        return {
            "clients": clients,
            "total": len(clients),
            "filtered_by": status if status else "all"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch clients: {str(e)}"
        )

@router.get("/clients/pending", dependencies=[Depends(get_super_admin_user)])
async def get_pending_clients(database = Depends(get_real_admin_db)):
    """Get all clients pending approval"""
    
    try:
        client_crud = ClientCRUD(database)
        pending_clients = await client_crud.get_all_clients("pending")
        
        return {
            "pending_clients": pending_clients,
            "count": len(pending_clients)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending clients: {str(e)}"
        )

@router.post("/clients/{client_id}/approve", dependencies=[Depends(get_super_admin_user)])
async def approve_client(
    client_id: str,
    database = Depends(get_real_admin_db)
):
    """Approve a pending client account"""
    
    try:
        client_crud = ClientCRUD(database)
        success = await client_crud.activate_client(client_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found or already processed"
            )
        
        return {
            "success": True,
            "message": f"Client {client_id} approved successfully",
            "client_id": client_id,
            "approved_at": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve client: {str(e)}"
        )

@router.post("/clients/{client_id}/suspend", dependencies=[Depends(get_super_admin_user)])
async def suspend_client(
    client_id: str,
    reason: str = "Administrative action",
    database = Depends(get_real_admin_db)
):
    """Suspend a client account"""
    
    try:
        client_crud = ClientCRUD(database)
        success = await client_crud.suspend_client(client_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return {
            "success": True,
            "message": f"Client {client_id} suspended successfully",
            "client_id": client_id,
            "reason": reason,
            "suspended_at": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suspend client: {str(e)}"
        )

@router.post("/clients/{client_id}/activate", dependencies=[Depends(get_super_admin_user)])
async def activate_client(
    client_id: str,
    database = Depends(get_real_admin_db)
):
    """Activate a suspended client account"""
    
    try:
        client_crud = ClientCRUD(database)
        success = await client_crud.activate_client(client_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return {
            "success": True,
            "message": f"Client {client_id} activated successfully",
            "client_id": client_id,
            "activated_at": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate client: {str(e)}"
        )

@router.get("/metrics", dependencies=[Depends(get_super_admin_user)])
async def get_system_metrics(database = Depends(get_real_admin_db)) -> SystemMetricsResponse:
    """Get system-wide metrics for super admin dashboard"""
    
    try:
        # Get all clients
        all_clients = await database.clients.find({}).to_list(None)
        
        # Calculate metrics
        total_clients = len(all_clients)
        active_clients = len([c for c in all_clients if c.get("status") == "active"])
        pending_approvals = len([c for c in all_clients if c.get("status") == "pending"])
        
        # Get today's conversations
        today = datetime.now(pytz.timezone('Asia/Singapore')).replace(hour=0, minute=0, second=0, microsecond=0)
        today_conversations = await database.conversations.count_documents({
            "created_at": {"$gte": today}
        })
        
        # Calculate revenue (mock calculation)
        revenue_this_month = active_clients * 299.0  # Assuming $299/month average
        
        return SystemMetricsResponse(
            total_clients=total_clients,
            active_clients=active_clients,
            pending_approvals=pending_approvals,
            total_conversations_today=today_conversations,
            revenue_this_month=revenue_this_month,
            system_uptime=99.9  # Mock uptime
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {str(e)}"
        )

@router.get("/clients/{client_id}/details", dependencies=[Depends(get_super_admin_user)])
async def get_client_details(
    client_id: str,
    database = Depends(get_real_admin_db)
):
    """Get detailed information about a specific client"""
    
    try:
        client_crud = ClientCRUD(database)
        client = await client_crud.get_client(client_id)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        # Get additional metrics
        conversations_count = await database.conversations.count_documents({
            "client_id": client_id
        })
        
        vehicles_count = await database.client_vehicles.count_documents({
            "client_id": client_id
        })
        
        users_count = await database.client_users.count_documents({
            "client_id": client_id
        })
        
        return {
            "client": client,
            "metrics": {
                "total_conversations": conversations_count,
                "total_vehicles": vehicles_count,
                "total_users": users_count,
                "current_month_conversations": client.get("current_month_conversations", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch client details: {str(e)}"
        )

# User Management Endpoints
@router.get("/clients/{client_id}/users", dependencies=[Depends(get_super_admin_user)])
async def get_client_users(
    client_id: str,
    database = Depends(get_real_admin_db)
):
    """Get all users for a specific client"""
    
    try:
        client_crud = ClientCRUD(database)
        
        # Verify client exists
        client = await client_crud.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        users = await client_crud.get_client_users(client_id)
        
        return {
            "client_id": client_id,
            "client_name": client.get("business_name", "Unknown"),
            "users": users,
            "total_users": len(users)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch client users: {str(e)}"
        )

class CreateUserRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "admin"

@router.post("/clients/{client_id}/users", dependencies=[Depends(get_super_admin_user)])
async def create_client_user(
    client_id: str,
    user_request: CreateUserRequest,
    database = Depends(get_real_admin_db)
):
    """Create a new user for a specific client"""
    
    try:
        client_crud = ClientCRUD(database)
        
        # Verify client exists
        client = await client_crud.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        # Create user
        user_data = {
            "email": user_request.email,
            "name": user_request.name,
            "password": user_request.password
        }
        
        user_id = await client_crud.create_client_user(
            client_id=client_id,
            user_data=user_data,
            role=user_request.role
        )
        
        return {
            "success": True,
            "message": f"User {user_request.email} created successfully",
            "user_id": user_id,
            "client_id": client_id,
            "created_at": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client user: {str(e)}"
        )

@router.post("/users/{user_id}/deactivate", dependencies=[Depends(get_super_admin_user)])
async def deactivate_user(
    user_id: str,
    database = Depends(get_real_admin_db)
):
    """Deactivate a user account"""
    
    try:
        client_crud = ClientCRUD(database)
        
        # Verify user exists
        user = await client_crud.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        success = await client_crud.deactivate_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deactivate user"
            )
        
        return {
            "success": True,
            "message": f"User {user.get('email', user_id)} deactivated successfully",
            "user_id": user_id,
            "deactivated_at": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )

@router.post("/users/{user_id}/activate", dependencies=[Depends(get_super_admin_user)])
async def activate_user(
    user_id: str,
    database = Depends(get_real_admin_db)
):
    """Activate a user account"""
    
    try:
        client_crud = ClientCRUD(database)
        
        # Verify user exists
        user = await client_crud.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        success = await client_crud.activate_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to activate user"
            )
        
        return {
            "success": True,
            "message": f"User {user.get('email', user_id)} activated successfully",
            "user_id": user_id,
            "activated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )

@router.put("/users/{user_id}/role", dependencies=[Depends(get_super_admin_user)])
async def update_user_role(
    user_id: str,
    role: str,
    database = Depends(get_real_admin_db)
):
    """Update user role"""
    
    try:
        client_crud = ClientCRUD(database)
        
        # Verify user exists
        user = await client_crud.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        success = await client_crud.update_user_role(user_id, role)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user role"
            )
        
        return {
            "success": True,
            "message": f"User {user.get('email', user_id)} role updated to {role}",
            "user_id": user_id,
            "new_role": role,
            "updated_at": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}"
        )

@router.get("/system/health", dependencies=[Depends(get_super_admin_user)])
async def get_system_health():
    """Get detailed system health information for super admin dashboard"""
    
    try:
        # Get performance monitor and health monitor
        perf_monitor = get_performance_monitor()
        health_monitor = HealthMonitor()
        
        # Get comprehensive health data
        services_status = await health_monitor.monitor_all_services()
        performance_summary = perf_monitor.get_health_summary()
        system_snapshot = perf_monitor.get_current_snapshot()
        
        # Calculate health scores
        total_services = len(services_status)
        healthy_services = sum(1 for service in services_status.values() if service.get('status') == 'healthy')
        service_health_score = (healthy_services / total_services * 100) if total_services > 0 else 0
        
        return {
            "overall_health": {
                "status": "healthy" if service_health_score >= 80 else "degraded" if service_health_score >= 60 else "unhealthy",
                "score": round(service_health_score, 1),
                "last_updated": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
            },
            "services": services_status,
            "performance": {
                "avg_response_time": f"{performance_summary.get('avg_response_time', 0):.2f}ms",
                "error_rate": f"{performance_summary.get('error_rate', 0):.2f}%",
                "requests_per_minute": performance_summary.get('requests_per_minute', 0),
                "active_connections": performance_summary.get('active_connections', 0)
            },
            "system_resources": {
                "cpu_usage": f"{system_snapshot.cpu_percent:.1f}%" if system_snapshot else "N/A",
                "memory_usage": f"{system_snapshot.memory_percent:.1f}%" if system_snapshot else "N/A",
                "disk_usage": f"{system_snapshot.disk_percent:.1f}%" if system_snapshot else "N/A",
                "network_io": {
                    "bytes_sent": system_snapshot.network_io_sent if system_snapshot else 0,
                    "bytes_recv": system_snapshot.network_io_recv if system_snapshot else 0
                }
            },
            "alerts": {
                "active_alerts": len(performance_summary.get('active_alerts', [])),
                "warnings": len(performance_summary.get('warnings', [])),
                "critical_issues": len([alert for alert in performance_summary.get('active_alerts', []) if alert.get('severity') == 'critical'])
            }
        }
        
    except Exception as e:
        # Fallback to basic health info if monitoring fails
        return {
            "overall_health": {
                "status": "unknown",
                "score": 0,
                "error": str(e),
                "last_updated": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
            },
            "services": {
                "api": {"status": "healthy", "uptime": "available"},
                "database": {"status": "unknown", "connections": "unknown"},
                "rasa": {"status": "unknown", "response_time": "unknown"},
                "widget_api": {"status": "unknown", "requests_per_minute": 0}
            },
            "performance": {
                "avg_response_time": "unknown",
                "error_rate": "unknown",
                "requests_per_minute": 0,
                "active_connections": 0
            },
            "system_resources": {
                "cpu_usage": "unknown",
                "memory_usage": "unknown",
                "disk_usage": "unknown",
                "network_io": {"bytes_sent": 0, "bytes_recv": 0}
            },
            "alerts": {
                "active_alerts": 0,
                "warnings": 0,
                "critical_issues": 0
            }
        }