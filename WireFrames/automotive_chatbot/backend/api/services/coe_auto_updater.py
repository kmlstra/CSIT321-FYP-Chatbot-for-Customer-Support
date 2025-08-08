#!/usr/bin/env python3
"""
🔄 COE REAL-TIME UPDATER SYSTEM
Monitors LTA COE data and updates automatically when new data is available
"""

import time
import logging
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from api.actions.coe_actions import get_live_coe_prices, get_historical_coe_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coe_auto_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class COEAutoUpdater:
    """Real-time COE data updater that monitors LTA updates"""
    
    def __init__(self):
        self.last_update = None
        self.update_history = []
        self.cache_dir = Path("cache/coe_data")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.check_interval = 300  # Check every 5 minutes (300 seconds)
        self.last_check = None
        self.bidding_day_interval = 120  # Check every 2 minutes on bidding days
        self.normal_day_interval = 600   # Check every 10 minutes on normal days
    
    def _is_potential_bidding_day(self):
        """Check if today could be a COE bidding day (1st or 3rd Wednesday of month)"""
        today = datetime.now()
        
        # Check if today is Wednesday (weekday 2)
        if today.weekday() != 2:
            return False
        
        # Get the first day of the month
        first_day = today.replace(day=1)
        
        # Find the first Wednesday of the month
        days_to_first_wednesday = (2 - first_day.weekday()) % 7
        first_wednesday = first_day + timedelta(days=days_to_first_wednesday)
        
        # Calculate the third Wednesday
        third_wednesday = first_wednesday + timedelta(days=14)
        
        # Check if today is the 1st or 3rd Wednesday
        return today.date() in [first_wednesday.date(), third_wednesday.date()]
    
    def _get_smart_check_interval(self):
        """Get intelligent check interval based on bidding schedule"""
        if self._is_potential_bidding_day():
            # More frequent checks on bidding days
            return self.bidding_day_interval
        else:
            # Less frequent checks on normal days
            return self.normal_day_interval
        
    def update_coe_data(self):
        """Main update function - fetches new data and updates predictions"""
        logger.info("🔄 Starting COE data update process...")
        
        try:
            # 1. Fetch latest COE prices
            current_data = get_live_coe_prices()
            if current_data is None:
                logger.warning("⚠️ Could not fetch current COE data")
                return False
            
            # 2. Check if data is new
            if self._is_data_new(current_data):
                logger.info("✅ New COE data detected - updating cache")
                
                # 3. Update cached data
                self._update_cache(current_data)
                
                # 4. Refresh predictions
                self._refresh_predictions()
                
                # 5. Update historical data
                self._update_historical_data()
                
                # 6. Send notification if significant changes
                self._check_for_significant_changes(current_data)
                
                self.last_update = datetime.now()
                logger.info("🎉 COE data update completed successfully")
                return True
            else:
                logger.info("📊 COE data unchanged - no update needed")
                return True
                
        except Exception as e:
            logger.error(f"❌ COE data update failed: {e}")
            return False
    
    def _is_data_new(self, current_data):
        """Check if the current data is different from cached data"""
        cache_file = self.cache_dir / "latest_coe_data.json"
        
        if not cache_file.exists():
            logger.info("📄 No cached data found - treating as new data")
            return True
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Compare current prices
            current_prices = current_data['current_prices']
            cached_prices = cached_data.get('current_prices', {})
            
            # Check bidding period (if available)
            current_period = current_data.get('bidding_period', '')
            cached_period = cached_data.get('bidding_period', '')
            
            if current_period != cached_period:
                logger.info(f"📅 New bidding period detected: {current_period}")
                return True
            
            # Compare prices for each category
            changes_detected = []
            for category in ['A', 'B', 'C', 'D', 'E']:
                current_price = current_prices.get(category, 0)
                cached_price = cached_prices.get(category, 0)
                
                if current_price != cached_price:
                    change = current_price - cached_price
                    changes_detected.append(f"Cat {category}: ${cached_price:,} → ${current_price:,} ({change:+,})")
            
            if changes_detected:
                logger.info("💰 Price changes detected:")
                for change in changes_detected:
                    logger.info(f"   • {change}")
                return True
            
            # If we reach here, no changes detected
            logger.info("📊 No changes in COE data")
            return False
            
        except Exception as e:
            logger.warning(f"Could not read cache file: {e}")
            return True
    
    def _update_cache(self, current_data):
        """Update the cached COE data"""
        cache_file = self.cache_dir / "latest_coe_data.json"
        
        # Add timestamp to data
        current_data['last_updated'] = datetime.now().isoformat()
        current_data['auto_updated'] = True
        
        with open(cache_file, 'w') as f:
            json.dump(current_data, f, indent=2, default=str)
        
        logger.info(f"💾 COE data cached to {cache_file}")
    
    def _refresh_predictions(self):
        """Refresh prediction calculations with new data"""
        logger.info("🔮 Refreshing COE predictions...")
        
        try:
            # This would trigger recalculation of predictions
            # The prediction algorithms will use the new cached data
            predictions_cache = self.cache_dir / "predictions_cache.json"
            
            # Get historical data for predictions
            historical_data = get_historical_coe_data()
            current_data = get_live_coe_prices()
            
            if current_data and historical_data:
                # Store prediction metadata
                current_prices = current_data.get('current_prices', {})
                prediction_metadata = {
                    'last_prediction_update': datetime.now().isoformat(),
                    'data_points_used': len(historical_data),
                    'prediction_confidence': 'Auto-updated',
                    'categories_processed': list(current_prices.keys()) if current_prices else []
                }
                
                with open(predictions_cache, 'w') as f:
                    json.dump(prediction_metadata, f, indent=2)
                
                logger.info("✅ Predictions refreshed successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh predictions: {e}")
    
    def _update_historical_data(self):
        """Update historical data archive"""
        logger.info("📚 Updating historical data archive...")
        
        try:
            historical_file = self.cache_dir / "historical_archive.json"
            current_data = get_live_coe_prices()
            
            # Check if current_data is None
            if current_data is None:
                logger.warning("⚠️ Cannot update historical data - no current data available")
                return
            
            # Load existing historical data
            if historical_file.exists():
                with open(historical_file, 'r') as f:
                    historical_archive = json.load(f)
            else:
                historical_archive = []
            
            # Add current data to archive
            archive_entry = {
                'date': datetime.now().isoformat(),
                'prices': current_data.get('current_prices', {}),
                'pqp_prices': current_data.get('pqp_prices', {}),
                'period': current_data.get('bidding_period', ''),
                'auto_archived': True
            }
            
            historical_archive.append(archive_entry)
            
            # Keep only last 100 entries to prevent file from growing too large
            if len(historical_archive) > 100:
                historical_archive = historical_archive[-100:]
            
            with open(historical_file, 'w') as f:
                json.dump(historical_archive, f, indent=2, default=str)
            
            logger.info(f"📊 Historical data updated - {len(historical_archive)} entries")
            
        except Exception as e:
            logger.error(f"❌ Failed to update historical data: {e}")
    
    def _check_for_significant_changes(self, current_data):
        """Check for significant price changes and log alerts"""
        cache_file = self.cache_dir / "latest_coe_data.json"
        
        if not cache_file.exists():
            return
        
        # Check if current_data is None
        if current_data is None:
            logger.warning("⚠️ Cannot check for significant changes - no current data available")
            return
        
        try:
            with open(cache_file, 'r') as f:
                previous_data = json.load(f)
            
            current_prices = current_data.get('current_prices', {})
            previous_prices = previous_data.get('current_prices', {})
            
            significant_changes = []
            
            for category in ['A', 'B', 'C', 'D', 'E']:
                current_price = current_prices.get(category, 0)
                previous_price = previous_prices.get(category, 0)
                
                if previous_price > 0:
                    change_percent = abs(current_price - previous_price) / previous_price
                    change_amount = current_price - previous_price
                    
                    # Alert for changes > 5% or > $5000
                    if change_percent > 0.05 or abs(change_amount) > 5000:
                        direction = "increased" if change_amount > 0 else "decreased"
                        significant_changes.append(
                            f"Category {category}: {direction} by ${abs(change_amount):,} "
                            f"({change_percent:.1%}) - from ${previous_price:,} to ${current_price:,}"
                        )
            
            if significant_changes:
                logger.warning("🚨 SIGNIFICANT COE PRICE CHANGES DETECTED:")
                for change in significant_changes:
                    logger.warning(f"   • {change}")
                
                # Save alert to file
                alert_file = self.cache_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(alert_file, 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'alert_type': 'significant_price_change',
                        'changes': significant_changes,
                        'current_prices': current_prices,
                        'previous_prices': previous_prices
                    }, f, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Failed to check for significant changes: {e}")
    
    def get_update_status(self):
        """Get current update status"""
        return {
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_count': len(self.update_history),
            'cache_directory': str(self.cache_dir),
            'auto_update_enabled': True
        }
    
    def manual_update(self):
        """Trigger manual update"""
        logger.info("🔧 Manual update triggered")
        return self.update_coe_data()

def run_realtime_monitor():
    """Run the real-time LTA monitor"""
    updater = COEAutoUpdater()
    
    logger.info("🔄 COE Real-Time Monitor starting:")
    logger.info("   • Smart monitoring based on LTA bidding schedule")
    logger.info("   • Bidding days (1st/3rd Wed): Check every 2 minutes")
    logger.info("   • Normal days: Check every 10 minutes")
    logger.info("   • Updates only when LTA publishes new COE data")
    logger.info("   • Smart caching to avoid unnecessary API calls")
    
    # Run initial update
    logger.info("🚀 Running initial COE data check...")
    updater.update_coe_data()
    
    # Keep monitoring for LTA updates
    while True:
        try:
            current_time = datetime.now()
            smart_interval = updater._get_smart_check_interval()
            
            # Log current monitoring mode
            if updater._is_potential_bidding_day():
                mode = "🔥 BIDDING DAY MODE"
            else:
                mode = "🌙 NORMAL MODE"
            
            # Only check if enough time has passed since last check
            if (updater.last_check is None or 
                (current_time - updater.last_check).total_seconds() >= smart_interval):
                
                logger.info(f"🔍 {mode} - Checking for new LTA COE data...")
                updater.last_check = current_time
                
                # Check for updates
                if updater.update_coe_data():
                    logger.info("✅ Check completed successfully")
                else:
                    logger.warning("⚠️ Check encountered issues")
            
            # Sleep for a shorter interval to be more responsive
            time.sleep(30)  # Check every 30 seconds if it's time for update
            
        except Exception as e:
            logger.error(f"❌ Monitor error: {e}")
            time.sleep(60)  # Wait longer on errors

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='COE Real-Time Updater System')
    parser.add_argument('--mode', choices=['monitor', 'manual'], default='monitor',
                       help='Run mode: monitor (real-time) or manual (one-time)')
    
    args = parser.parse_args()
    
    if args.mode == 'manual':
        # Manual update
        updater = COEAutoUpdater()
        success = updater.manual_update()
        if success:
            print("✅ Manual update completed successfully")
            status = updater.get_update_status()
            print(f"📊 Update Status: {json.dumps(status, indent=2)}")
        else:
            print("❌ Manual update failed")
    else:
        # Real-time monitoring
        try:
            run_realtime_monitor()
        except KeyboardInterrupt:
            logger.info("🛑 COE Real-Time Monitor stopped by user")
        except Exception as e:
            logger.error(f"❌ COE Real-Time Monitor crashed: {e}")

if __name__ == "__main__":
    main()