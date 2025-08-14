"""
Health Monitoring Service
Monitors all critical services and sends alerts when they're down
"""

import requests
import logging
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
import asyncio
import aiohttp
import psutil
import os

from ..services.notifications import (
    notify_rasa_server_down,
    notify_backend_server_down, 
    notify_frontend_server_down,
    notify_database_down,
    notify_service_recovery,
    notify_system_error
)

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitors all critical services for the CleverCompanion chatbot system"""
    
    def __init__(self):
        # Use unified domain:port approach for all service URLs
        domain = os.getenv('DOMAIN', 'http://localhost')
        rasa_port = os.getenv('RASA_PORT', '5005')
        backend_port = os.getenv('BACKEND_PORT', '8001')
        frontend_port = os.getenv('FRONTEND_PORT', '3000')
        
        self.services = {
            'rasa': {
                'url': f"{domain}:{rasa_port}",
                'endpoint': '/status',
                'timeout': 10
            },
            'backend': {
                'url': f"{domain}:{backend_port}",
                'endpoint': '/health',
                'timeout': 5
            },
            'frontend': {
                'url': f"{domain}:{frontend_port}",
                'endpoint': '/',
                'timeout': 5
            },
            'mongodb': {
                'url': os.getenv('MONGODB_URL', 'mongodb+srv://CleverAdmin:P%40ssw0rd%211@clevercompanioncluster.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot'),
                'timeout': 10
            }
        }
        self.last_status = {}
        self.downtime_start = {}
        
    def check_rasa_server(self) -> Tuple[bool, str]:
        """Check if RASA server is responding"""
        try:
            rasa_url = self.services["RASA"]["url"]
            response = requests.post(
                rasa_url,
                json={"sender": "health_check", "message": "ping"},
                timeout=5
            )
            if response.status_code == 200:
                return True, "RASA server responding normally"
            else:
                return False, f"RASA server returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "RASA server connection refused - server may be down"
        except requests.exceptions.Timeout:
            return False, "RASA server timeout - server may be overloaded"
        except Exception as e:
            return False, f"RASA server error: {str(e)}"
    
    def check_backend_server(self) -> Tuple[bool, str]:
        """Check if FastAPI backend server is responding"""
        try:
            backend_url = self.services["Backend"]["url"]
            response = requests.get(backend_url, timeout=5)
            if response.status_code == 200:
                return True, "Backend server responding normally"
            else:
                return False, f"Backend server returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Backend server connection refused - server may be down"
        except requests.exceptions.Timeout:
            return False, "Backend server timeout - server may be overloaded"
        except Exception as e:
            return False, f"Backend server error: {str(e)}"
    
    def check_frontend_server(self) -> Tuple[bool, str]:
        """Check if Frontend server is responding"""
        try:
            frontend_url = self.services["Frontend"]["url"]
            response = requests.get(frontend_url, timeout=5)
            if response.status_code == 200:
                return True, "Frontend server responding normally"
            else:
                return False, f"Frontend server returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Frontend server connection refused - server may be down"
        except requests.exceptions.Timeout:
            return False, "Frontend server timeout - server may be overloaded"
        except Exception as e:
            return False, f"Frontend server error: {str(e)}"
    
    def check_mongodb_server(self) -> Tuple[bool, str]:
        """Check if MongoDB server is responding"""
        try:
            # Use centralized database connection
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
            
            from api.config.database import DatabaseContext
            
            # Test MongoDB connection using DatabaseContext
            try:
                with DatabaseContext('clients') as collection:
                    if collection is not None:
                        # Test the connection by attempting a simple operation
                        collection.database.client.admin.command('ping')
                        return True, "MongoDB server responding normally"
                    else:
                        return False, "MongoDB connection not available"
            except Exception as db_error:
                return False, f"MongoDB connection failed: {str(db_error)}"
        except Exception as e:
            return False, f"MongoDB server error: {str(e)}"
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available": memory.available / (1024**3),  # GB
                "disk_usage": disk.percent,
                "disk_free": disk.free / (1024**3)  # GB
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {}
    
    def monitor_all_services(self) -> Dict[str, bool]:
        """Monitor all services and return their status"""
        results = {}
        
        # Check RASA server
        rasa_ok, rasa_msg = self.check_rasa_server()
        results["RASA"] = rasa_ok
        if not rasa_ok:
            logger.error(f"RASA server down: {rasa_msg}")
            notify_rasa_server_down()
        
        # Check Backend server
        backend_ok, backend_msg = self.check_backend_server()
        results["Backend"] = backend_ok
        if not backend_ok:
            logger.error(f"Backend server down: {backend_msg}")
            notify_backend_server_down()
        
        # Check Frontend server
        frontend_ok, frontend_msg = self.check_frontend_server()
        results["Frontend"] = frontend_ok
        if not frontend_ok:
            logger.error(f"Frontend server down: {frontend_msg}")
            notify_frontend_server_down()
        
        # Check MongoDB
        mongodb_ok, mongodb_msg = self.check_mongodb_server()
        results["MongoDB"] = mongodb_ok
        if not mongodb_ok:
            logger.error(f"MongoDB server down: {mongodb_msg}")
            notify_database_down()
        
        # Check system resources
        resources = self.check_system_resources()
        if resources:
            # Alert if system resources are critically low
            if resources.get("cpu_usage", 0) > 90:
                notify_system_error("CPU", f"CPU usage at {resources['cpu_usage']:.1f}%", "System performance degraded")
            
            if resources.get("memory_usage", 0) > 90:
                notify_system_error("Memory", f"Memory usage at {resources['memory_usage']:.1f}%", "System may become unstable")
            
            if resources.get("disk_usage", 0) > 90:
                notify_system_error("Disk", f"Disk usage at {resources['disk_usage']:.1f}%", "System may fail to write data")
        
        return results
    
    def continuous_monitoring(self, interval_seconds: int = 60):
        """Run continuous monitoring with specified interval"""
        logger.info(f"Starting continuous health monitoring (interval: {interval_seconds}s)")
        
        while True:
            try:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"[{timestamp}] Running health check...")
                
                status = self.monitor_all_services()
                
                # Log status summary
                online_services = sum(1 for s in status.values() if s)
                total_services = len(status)
                logger.info(f"Health check complete: {online_services}/{total_services} services online")
                
                # Check for service recovery
                for service, is_online in status.items():
                    if service in self.last_status:
                        # Service recovered
                        if not self.last_status[service] and is_online:
                            if service in self.downtime_start:
                                downtime = datetime.now() - self.downtime_start[service]
                                duration_str = str(downtime).split('.')[0]  # Remove microseconds
                                logger.info(f"Service {service} recovered after {duration_str}")
                                notify_service_recovery(service, duration_str)
                                del self.downtime_start[service]
                        # Service went down
                        elif self.last_status[service] and not is_online:
                            self.downtime_start[service] = datetime.now()
                    
                    self.last_status[service] = is_online
                
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Health monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                time.sleep(interval_seconds)

def run_health_check():
    """Run a single health check"""
    monitor = HealthMonitor()
    return monitor.monitor_all_services()

def start_monitoring(interval: int = 60):
    """Start continuous monitoring"""
    monitor = HealthMonitor()
    monitor.continuous_monitoring(interval)

if __name__ == "__main__":
    # Run continuous monitoring when script is executed directly
    print("🏥 CleverCompanion Health Monitor Starting...")
    print("📊 Monitoring all critical services...")
    print("✉️ Email alerts will be sent to IT team when services are down")
    print("⏹️ Press Ctrl+C to stop monitoring")
    
    start_monitoring(interval=30)  # Check every 30 seconds