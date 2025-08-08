"""Email Notification Service for Appointments
Handles email notifications for appointment confirmations, reminders, and cancellations
"""

import os
import smtplib
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "../../.env")
if Path(env_path).exists():
    load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

class EmailService:
    """Email notification service for appointments using Gmail"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "clevercompanion349@gmail.com"
        self.app_password = None
        self._initialize_email()
    
    def _initialize_email(self):
        """Initialize email service with credentials from environment variables"""
        self.app_password = os.getenv('EMAIL_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
        
        if not self.app_password or self.app_password in ['your-gmail-app-password-here', 'MISSING_EMAIL_PASSWORD_ENV_VAR']:
            logger.warning("⚠️ Email credentials not configured. Set EMAIL_PASSWORD in .env file.")
            return
        
        logger.info("✅ Email service initialized successfully")
    
    def is_enabled(self) -> bool:
        """Check if email service is properly configured and enabled"""
        return self.app_password is not None and self.app_password not in ['your-gmail-app-password-here', 'MISSING_EMAIL_PASSWORD_ENV_VAR']
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Send email using Gmail SMTP
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject line
            html_content (str): HTML email content
            text_content (str): Plain text fallback (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.is_enabled():
            logger.warning("Email service not enabled. Message not sent.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.app_password is None:
                    raise ValueError("Email password not configured")
                server.login(self.sender_email, self.app_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            logger.info(f"✅ Email sent successfully to {to_email[:10]}***")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Gmail authentication failed. Check EMAIL_PASSWORD in .env file.")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email to {to_email[:10]}***: {e}")
            return False
    
    def send_appointment_confirmation(self, appointment_data: Dict[str, Any]) -> bool:
        """Send appointment confirmation email
        
        Args:
            appointment_data (dict): Appointment details
            
        Returns:
            bool: True if email sent successfully
        """
        if not appointment_data.get('customer_email'):
            logger.warning("No email address provided for appointment confirmation")
            return False
        
        # Format appointment details
        appointment_id = appointment_data.get('appointment_id', '')[:8]
        customer_name = appointment_data.get('customer_name', 'Customer')
        service_type = appointment_data.get('service_type', 'Service')
        appointment_date = appointment_data.get('appointment_date', '')
        appointment_time = appointment_data.get('appointment_time', '')
        
        subject = f"🚗 CleverCompanion Appointment Confirmed - {appointment_id}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .appointment-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #333; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 Appointment Confirmed!</h1>
                    <p>Thank you for choosing CleverCompanion</p>
                </div>
                <div class="content">
                    <p>Hi <strong>{customer_name}</strong>!</p>
                    <p>Your appointment has been successfully booked. Here are the details:</p>
                    
                    <div class="appointment-details">
                        <div class="detail-row">
                            <span class="label">📅 Date:</span>
                            <span class="value">{appointment_date}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">⏰ Time:</span>
                            <span class="value">{appointment_time}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">🔧 Service:</span>
                            <span class="value">{service_type.title()}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">🆔 Appointment ID:</span>
                            <span class="value">{appointment_id}</span>
                        </div>
                    </div>
                    
                    <p><strong>What's Next?</strong></p>
                    <ul>
                        <li>We'll send you a reminder email 24 hours before your appointment</li>
                        <li>Please arrive 10 minutes early</li>
                        <li>Bring any relevant documents or vehicle information</li>
                        <li>Need to make changes? Contact us as soon as possible</li>
                    </ul>
                    
                    <div class="footer">
                        <p>Thank you for choosing CleverCompanion! 🙏</p>
                        <p>For any questions or changes, please contact us.</p>
                        <p><em>This is an automated confirmation email.</em></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        CleverCompanion Appointment Confirmed!
        
        Hi {customer_name}!
        
        Your appointment has been successfully booked:
        
        Date: {appointment_date}
        Time: {appointment_time}
        Service: {service_type.title()}
        Appointment ID: {appointment_id}
        
        We'll send you a reminder email 24 hours before your appointment.
        Please arrive 10 minutes early.
        
        Thank you for choosing CleverCompanion!
        """
        
        return self._send_email(appointment_data['customer_email'], subject, html_content, text_content)
    
    def send_appointment_reminder(self, appointment_data: Dict[str, Any]) -> bool:
        """Send appointment reminder email (24 hours before)
        
        Args:
            appointment_data (dict): Appointment details
            
        Returns:
            bool: True if email sent successfully
        """
        if not appointment_data.get('customer_email'):
            logger.warning("No email address provided for appointment reminder")
            return False
        
        appointment_id = appointment_data.get('appointment_id', '')[:8]
        customer_name = appointment_data.get('customer_name', 'Customer')
        service_type = appointment_data.get('service_type', 'Service')
        appointment_date = appointment_data.get('appointment_date', '')
        appointment_time = appointment_data.get('appointment_time', '')
        
        subject = f"⏰ Appointment Reminder - Tomorrow at {appointment_time}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .reminder-box {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .appointment-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f5576c; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #333; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Appointment Reminder</h1>
                    <p>Your appointment is tomorrow!</p>
                </div>
                <div class="content">
                    <p>Hi <strong>{customer_name}</strong>!</p>
                    
                    <div class="reminder-box">
                        <h3>🔔 Don't forget - Your appointment is tomorrow!</h3>
                    </div>
                    
                    <div class="appointment-details">
                        <div class="detail-row">
                            <span class="label">📅 Date:</span>
                            <span class="value">{appointment_date}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">⏰ Time:</span>
                            <span class="value">{appointment_time}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">🔧 Service:</span>
                            <span class="value">{service_type.title()}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">🆔 Appointment ID:</span>
                            <span class="value">{appointment_id}</span>
                        </div>
                    </div>
                    
                    <p><strong>Important Reminders:</strong></p>
                    <ul>
                        <li>Please arrive 10 minutes early</li>
                        <li>Bring any relevant documents or vehicle information</li>
                        <li>Need to reschedule? Contact us ASAP!</li>
                    </ul>
                    
                    <div class="footer">
                        <p>See you soon! 🚗</p>
                        <p>CleverCompanion Team</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Appointment Reminder - CleverCompanion
        
        Hi {customer_name}!
        
        Your appointment is tomorrow:
        
        Date: {appointment_date}
        Time: {appointment_time}
        Service: {service_type.title()}
        Appointment ID: {appointment_id}
        
        Please arrive 10 minutes early. Need to reschedule? Contact us ASAP!
        
        See you soon!
        CleverCompanion Team
        """
        
        return self._send_email(appointment_data['customer_email'], subject, html_content, text_content)
    
    def send_appointment_cancellation(self, appointment_data: Dict[str, Any]) -> bool:
        """Send appointment cancellation email
        
        Args:
            appointment_data (dict): Appointment details
            
        Returns:
            bool: True if email sent successfully
        """
        if not appointment_data.get('customer_email'):
            logger.warning("No email address provided for appointment cancellation")
            return False
        
        appointment_id = appointment_data.get('appointment_id', '')[:8]
        customer_name = appointment_data.get('customer_name', 'Customer')
        service_type = appointment_data.get('service_type', 'Service')
        appointment_date = appointment_data.get('appointment_date', '')
        appointment_time = appointment_data.get('appointment_time', '')
        
        subject = f"❌ Appointment Cancelled - {appointment_id}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .cancellation-box {{ background: #ffe6e6; border: 1px solid #ff9999; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .appointment-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff6b6b; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #333; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>❌ Appointment Cancelled</h1>
                    <p>CleverCompanion</p>
                </div>
                <div class="content">
                    <p>Hi <strong>{customer_name}</strong>!</p>
                    
                    <div class="cancellation-box">
                        <h3>Your appointment has been cancelled</h3>
                    </div>
                    
                    <div class="appointment-details">
                        <div class="detail-row">
                            <span class="label">📅 Date:</span>
                            <span class="value">{appointment_date}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">⏰ Time:</span>
                            <span class="value">{appointment_time}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">🔧 Service:</span>
                            <span class="value">{service_type.title()}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">🆔 Appointment ID:</span>
                            <span class="value">{appointment_id}</span>
                        </div>
                    </div>
                    
                    <p>Need to book a new appointment? Just message us anytime!</p>
                    
                    <div class="footer">
                        <p>Thank you for choosing CleverCompanion! 🙏</p>
                        <p>We look forward to serving you in the future.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Appointment Cancelled - CleverCompanion
        
        Hi {customer_name}!
        
        Your appointment has been cancelled:
        
        Date: {appointment_date}
        Time: {appointment_time}
        Service: {service_type.title()}
        Appointment ID: {appointment_id}
        
        Need to book a new appointment? Just message us anytime!
        
        Thank you for choosing CleverCompanion!
        """
        
        return self._send_email(appointment_data['customer_email'], subject, html_content, text_content)

# Global email service instance
email_service = EmailService()

# Convenience functions for easy import
def send_appointment_confirmation_email(appointment_data: Dict[str, Any]) -> bool:
    """Send appointment confirmation email"""
    return email_service.send_appointment_confirmation(appointment_data)

def send_appointment_reminder_email(appointment_data: Dict[str, Any]) -> bool:
    """Send appointment reminder email"""
    return email_service.send_appointment_reminder(appointment_data)

def send_appointment_cancellation_email(appointment_data: Dict[str, Any]) -> bool:
    """Send appointment cancellation email"""
    return email_service.send_appointment_cancellation(appointment_data)

def is_email_enabled() -> bool:
    """Check if email service is enabled"""
    return email_service.is_enabled()