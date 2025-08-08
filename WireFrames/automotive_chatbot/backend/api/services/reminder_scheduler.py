"""Appointment Reminder Scheduler
Schedules and runs daily appointment reminders
"""

import schedule
import time
import logging
from datetime import datetime
from appointment_reminder import AppointmentReminderService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reminder_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Scheduler for appointment reminders"""
    
    def __init__(self):
        self.reminder_service = AppointmentReminderService()
    
    def run_daily_reminders(self):
        """Run the daily reminder job"""
        logger.info(f"Starting scheduled reminder job at {datetime.now()}")
        
        try:
            result = self.reminder_service.send_daily_reminders()
            
            if result['success']:
                logger.info(
                    f"Reminder job completed successfully: "
                    f"{result['reminders_sent']} reminders sent, "
                    f"{result['errors']} errors"
                )
            else:
                logger.error(f"Reminder job failed: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error in scheduled reminder job: {e}")
    
    def start_scheduler(self):
        """Start the reminder scheduler"""
        logger.info("Starting appointment reminder scheduler...")
        
        # Schedule reminders to run daily at 9:00 AM Singapore time
        schedule.every().day.at("09:00").do(self.run_daily_reminders)
        
        # Also schedule a test run every hour for debugging (remove in production)
        # schedule.every().hour.do(self.run_daily_reminders)
        
        logger.info("Scheduler configured. Reminders will be sent daily at 9:00 AM.")
        logger.info("Press Ctrl+C to stop the scheduler.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")

def main():
    """Main function"""
    scheduler = ReminderScheduler()
    
    # Option to run reminders immediately for testing
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--run-now':
        logger.info("Running reminders immediately for testing...")
        scheduler.run_daily_reminders()
    else:
        # Start the scheduler
        scheduler.start_scheduler()

if __name__ == '__main__':
    main()