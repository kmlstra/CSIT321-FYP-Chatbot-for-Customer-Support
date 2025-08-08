"""Appointment Reminder Service
Sends email reminders for upcoming appointments
"""

import os
import sys
from datetime import datetime, timedelta
import pytz
import logging
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.config.database import DatabaseContext
from backend.api.services.email_service import send_appointment_reminder_email, is_email_enabled

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AppointmentReminderService:
    """Service for sending appointment reminders"""
    
    def __init__(self):
        self.sg_tz = pytz.timezone('Asia/Singapore')
    
    def send_daily_reminders(self) -> Dict[str, Any]:
        """Send reminders for appointments in the next 24 hours"""
        try:
            if not is_email_enabled():
                logger.info("Email service not enabled - skipping reminder notifications")
                return {
                    'success': True,
                    'message': 'Email service not enabled',
                    'reminders_sent': 0,
                    'errors': 0
                }
            
            # Get appointments for tomorrow (24 hours from now)
            now = datetime.now(self.sg_tz)
            tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_end = tomorrow_start + timedelta(days=1)
            
            appointments = self._get_upcoming_appointments(tomorrow_start, tomorrow_end)
            
            reminders_sent = 0
            errors = 0
            
            for appointment in appointments:
                try:
                    # Skip if no email address
                    if not appointment.get('customer_email'):
                        logger.info(f"No email address for appointment {appointment['appointment_id'][:8]} - skipping reminder")
                        continue
                    
                    # Prepare email data
                    email_data = {
                        'customer_name': appointment.get('customer_name', 'Customer'),
                        'customer_email': appointment['customer_email'],
                        'appointment_id': appointment['appointment_id'],
                        'appointment_date': appointment['appointment_datetime'].strftime('%B %d, %Y'),
                        'appointment_time': appointment['appointment_datetime'].strftime('%I:%M %p'),
                        'service_type': appointment['service_type']
                    }
                    
                    # Send reminder email
                    email_sent = send_appointment_reminder_email(email_data)
                    
                    if email_sent:
                        reminders_sent += 1
                        logger.info(f"Email reminder sent for appointment {appointment['appointment_id'][:8]}")
                        
                        # Update appointment to mark reminder as sent
                        self._mark_reminder_sent(appointment['appointment_id'])
                    else:
                        errors += 1
                        logger.error(f"Failed to send email reminder for appointment {appointment['appointment_id'][:8]}")
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"Error sending reminder for appointment {appointment.get('appointment_id', 'unknown')[:8]}: {e}")
            
            logger.info(f"Reminder service completed: {reminders_sent} sent, {errors} errors")
            
            return {
                'success': True,
                'message': f'Reminder service completed successfully',
                'reminders_sent': reminders_sent,
                'errors': errors,
                'total_appointments': len(appointments)
            }
            
        except Exception as e:
            logger.error(f"Error in send_daily_reminders: {e}")
            return {
                'success': False,
                'message': f'Error in reminder service: {str(e)}',
                'reminders_sent': 0,
                'errors': 1
            }
    
    def _get_upcoming_appointments(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get appointments within the specified time range"""
        try:
            with DatabaseContext('appointments') as collection:
                if not collection:
                    return []
                
                # Convert to UTC for database query
                start_utc = start_time.astimezone(pytz.UTC).replace(tzinfo=None)
                end_utc = end_time.astimezone(pytz.UTC).replace(tzinfo=None)
                
                appointments = list(collection.find({
                    'appointment_datetime': {
                        '$gte': start_utc,
                        '$lt': end_utc
                    },
                    'status': {'$in': ['confirmed', 'pending']},
                    'reminder_sent': {'$ne': True}  # Only get appointments where reminder hasn't been sent
                }).sort('appointment_datetime', 1))
                
                return appointments
                
        except Exception as e:
            logger.error(f"Error getting upcoming appointments: {e}")
            return []
    
    def _mark_reminder_sent(self, appointment_id: str) -> bool:
        """Mark appointment as having reminder sent"""
        try:
            with DatabaseContext('appointments') as collection:
                if not collection:
                    return False
                
                result = collection.update_one(
                    {'appointment_id': appointment_id},
                    {
                        '$set': {
                            'reminder_sent': True,
                            'reminder_sent_at': datetime.utcnow()
                        }
                    }
                )
                
                return result.modified_count > 0
                
        except Exception as e:
            logger.error(f"Error marking reminder as sent: {e}")
            return False

def main():
    """Main function for running the reminder service"""
    logger.info("Starting appointment reminder service...")
    
    reminder_service = AppointmentReminderService()
    result = reminder_service.send_daily_reminders()
    
    if result['success']:
        logger.info(f"Reminder service completed successfully: {result['reminders_sent']} reminders sent")
    else:
        logger.error(f"Reminder service failed: {result['message']}")
    
    return result

if __name__ == '__main__':
    main()