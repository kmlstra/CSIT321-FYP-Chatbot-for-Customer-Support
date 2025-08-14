"""
Email Notification Service
Handles all IT notifications for system failures and alerts
"""

import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logger first
logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "../../.env")
if Path(env_path).exists():
    load_dotenv(dotenv_path=env_path)
else:
    logger.warning("⚠️ backend/.env file not found. Email notifications may not work.")

def send_it_notification(subject: str, message: str) -> bool:
    """
    Simplified IT notification function for all service failures.
    Sends email to IT personnel only - never to customers.
    
    Args:
        subject (str): Email subject line
        message (str): Email message body
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Check if email is configured
        app_password = os.getenv('EMAIL_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
        
        if not app_password or app_password in ['your-gmail-app-password-here', 'MISSING_EMAIL_PASSWORD_ENV_VAR']:
            logger.warning("⚠️ Email notifications not configured. Set EMAIL_PASSWORD in .env file.")
            return False

        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "clevercompanion349@gmail.com"
        recipient_email = "clevercompanion349@gmail.com"  # IT personnel only
        
        # Create and send email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        
        logger.info("✅ IT notification sent successfully")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Gmail authentication failed. Check EMAIL_PASSWORD in .env file.")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to send IT notification: {e}")
        return False

# ========================================
# SERVER MONITORING NOTIFICATIONS
# ========================================

def notify_server_down(server_name: str, server_url: str, error_details: str = ""):
    """
    Critical alert when any server goes down
    
    Args:
        server_name (str): Name of the server (e.g., "RASA Chatbot", "FastAPI Backend", "Frontend")
        server_url (str): Server URL that's not responding
        error_details (str): Optional error details
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    subject = f"🚨 CRITICAL: {server_name} Server DOWN"
    message = f"""
        CRITICAL SERVER OUTAGE

        Timestamp: {timestamp} SGT
        Server: {server_name}
        URL: {server_url}
        Status: OFFLINE/UNREACHABLE
        Severity: CRITICAL

        {f"Error Details: {error_details}" if error_details else ""}

        IMMEDIATE ACTION REQUIRED:
        1. Check server process status
        2. Verify server connectivity
        3. Check system resources (CPU, Memory, Disk)
        4. Review server logs for errors
        5. Restart server if necessary
        6. Monitor service restoration

        User Impact: Complete service unavailable
        System: CleverCompanion Automotive Chatbot
        Alert Type: CRITICAL SERVER OUTAGE
        Priority: HIGH

        This is an automated alert. Please respond immediately.
        """
    
    return send_it_notification(subject, message)

def notify_rasa_server_down():
    """Alert when RASA chatbot server is down"""
    import os
    # Use unified domain:port approach
    domain = os.getenv('DOMAIN', 'http://localhost')
    rasa_port = os.getenv('RASA_PORT', '5005')
    rasa_url = f"{domain}:{rasa_port}"
    return notify_server_down(
        "RASA Chatbot", 
        rasa_url, 
        "RASA server not responding to health checks"
    )

def notify_backend_server_down():
    """Alert when FastAPI backend server is down"""
    import os
    # Use unified domain:port approach
    domain = os.getenv('DOMAIN', 'http://localhost')
    backend_port = os.getenv('BACKEND_PORT', '8001')
    backend_url = f"{domain}:{backend_port}"
    return notify_server_down(
        "FastAPI Backend", 
        backend_url, 
        "Backend API server not responding"
    )

def notify_frontend_server_down():
    """Alert when Frontend/Widget server is down"""
    import os
    # Use unified domain:port approach
    domain = os.getenv('DOMAIN', 'http://localhost')
    frontend_port = os.getenv('FRONTEND_PORT', '3000')
    frontend_url = f"{domain}:{frontend_port}"
    return notify_server_down(
        "Frontend Server", 
        frontend_url, 
        "Frontend/Widget server not responding"
    )

def notify_database_down(db_type: str = "MongoDB"):
    """Alert when database server is down"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    subject = f"🚨 CRITICAL: {db_type} Database DOWN"
    message = f"""
        CRITICAL DATABASE OUTAGE

        Timestamp: {timestamp} SGT
        Database: {db_type}
        Connection: {os.getenv('MONGODB_URL', 'mongodb+srv://CleverAdmin:P%40ssw0rd%211@clevercompanioncluster.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot')}
        Status: OFFLINE/UNREACHABLE
        Severity: CRITICAL

        IMMEDIATE ACTION REQUIRED:
        1. Check {db_type} service status
        2. Verify database connectivity
        3. Check disk space and memory
        4. Review database logs
        5. Restart database service if needed
        6. Test database connections

        User Impact: Data cannot be saved/retrieved
        System: CleverCompanion Automotive Chatbot
        Alert Type: CRITICAL DATABASE OUTAGE
        Priority: HIGH

        This is an automated alert. Please respond immediately.
        """
    
    return send_it_notification(subject, message)

# ========================================
# API FAILURE NOTIFICATIONS
# ========================================

def notify_coe_api_failure():
    """Send COE API failure notification to IT team"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    subject = "🚨 COE API Service Alert"
    message = f"""
    URGENT: COE Price API Service Failure

    Timestamp: {timestamp} SGT
    Service: Singapore Data.gov.sg COE Bidding Results API
    Status: FAILED
    Impact: Users cannot retrieve current COE prices

    Action Required:
    1. Check data.gov.sg API status
    2. Verify network connectivity  
    3. Monitor service restoration

    System: CleverCompanion Automotive Chatbot
    Alert Type: Automatic API Failure Detection
    """
    
    return send_it_notification(subject, message)

def notify_api_failure(service_name: str, api_endpoint: str, error_details: str = ""):
    """
    Generic API failure notification for any service
    
    Args:
        service_name (str): Name of the failed service
        api_endpoint (str): The API endpoint that failed
        error_details (str): Optional error details
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    subject = f"🚨 {service_name} API Service Alert"
    message = f"""
        URGENT: {service_name} API Service Failure

        Timestamp: {timestamp} SGT
        Service: {service_name}
        Endpoint: {api_endpoint}
        Status: FAILED
        Impact: Users cannot access {service_name} functionality

        {f"Error Details: {error_details}" if error_details else ""}

        Action Required:
        1. Check API status and connectivity
        2. Verify endpoint configuration
        3. Monitor service restoration

        System: CleverCompanion Automotive Chatbot
        Alert Type: Automatic API Failure Detection
        """
    
    return send_it_notification(subject, message)

# ========================================
# GENERAL SYSTEM NOTIFICATIONS
# ========================================

def notify_system_error(component: str, error_message: str, user_impact: str = ""):
    """
    General system error notification
    
    Args:
        component (str): System component that failed
        error_message (str): Error message or details
        user_impact (str): Description of user impact
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    subject = f"⚠️ System Error - {component}"
    message = f"""
    System Error Alert

    Timestamp: {timestamp} SGT
    Component: {component}
    Error: {error_message}
    {f"User Impact: {user_impact}" if user_impact else ""}

    System: CleverCompanion Automotive Chatbot
    Alert Type: Automatic Error Detection
    """
    
    return send_it_notification(subject, message)

def notify_service_recovery(service_name: str, downtime_duration: str = ""):
    """
    Positive notification when a service recovers
    
    Args:
        service_name (str): Name of the recovered service
        downtime_duration (str): How long the service was down
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    subject = f"✅ Service Restored: {service_name}"
    message = f"""
    SERVICE RECOVERY NOTIFICATION

    Timestamp: {timestamp} SGT
    Service: {service_name}
    Status: ONLINE/OPERATIONAL
    {f"Downtime Duration: {downtime_duration}" if downtime_duration else ""}

    The service has been automatically restored and is now operational.
    Users can resume normal activities.

    System: CleverCompanion Automotive Chatbot
    Alert Type: Service Recovery
    Priority: INFO
    """
    
    return send_it_notification(subject, message)