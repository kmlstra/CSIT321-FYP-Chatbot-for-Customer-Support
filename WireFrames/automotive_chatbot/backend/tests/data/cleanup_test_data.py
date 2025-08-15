#!/usr/bin/env python3
"""
Test data cleanup script for removing test data from database
"""

import asyncio
import motor.motor_asyncio
import os
import json
from datetime import datetime
from bson import ObjectId
from typing import Dict, List, Any, Optional

class TestDataCleanup:
    """Cleanup test data from database"""
    
    def __init__(self, db):
        self.db = db
        self.cleanup_stats = {
            "clients": 0,
            "users": 0,
            "conversations": 0,
            "appointments": 0,
            "vehicles": 0,
            "services": 0
        }
    
    async def cleanup_all_test_data(self, confirm: bool = False):
        """Clean up all test data from database"""
        if not confirm:
            print("WARNING: This will delete ALL test data from the database!")
            print("To confirm, call this method with confirm=True")
            return
        
        print("Starting comprehensive test data cleanup...")
        
        # Clean up in order of dependencies (child -> parent)
        await self.cleanup_services()
        await self.cleanup_vehicles()
        await self.cleanup_appointments()
        await self.cleanup_conversations()
        await self.cleanup_users()
        await self.cleanup_clients()
        
        print("\nCleanup Summary:")
        for collection, count in self.cleanup_stats.items():
            print(f"  {collection}: {count} documents deleted")
        
        total_deleted = sum(self.cleanup_stats.values())
        print(f"\nTotal documents deleted: {total_deleted}")
        print("Test data cleanup completed successfully!")
    
    async def cleanup_specific_test_data(self, test_data_info: Dict[str, Any]):
        """Clean up specific test data based on test data info"""
        print("Cleaning up specific test data...")
        
        summary = test_data_info.get("summary", {})
        
        # Clean up in reverse order of dependencies
        collections_to_clean = [
            ("services", summary.get("services", [])),
            ("vehicles", summary.get("vehicles", [])),
            ("appointments", summary.get("appointments", [])),
            ("conversations", summary.get("conversations", [])),
            ("client_users", summary.get("users", [])),
            ("clients", summary.get("clients", []))
        ]
        
        for collection_name, ids in collections_to_clean:
            if ids:
                count = await self._cleanup_by_ids(collection_name, ids)
                self.cleanup_stats[collection_name.replace("client_", "")] = count
        
        print("\nSpecific cleanup completed!")
        self._print_cleanup_stats()
    
    async def cleanup_clients(self):
        """Clean up test clients"""
        print("Cleaning up test clients...")
        
        # Identify test clients by domain patterns or test markers
        test_domains = [
            "abcmotors.com",
            "xyzauto.com",
            "premiumauto.sg",
            "citymotors.sg",
            "elitecar.sg",
            "test.com",
            "example.com"
        ]
        
        # Also clean up clients with test API keys
        query = {
            "$or": [
                {"domain": {"$in": test_domains}},
                {"api_key": {"$regex": "^cc_(abc|xyz|test)"}},
                {"business_name": {"$regex": "(Test|ABC Motors|XYZ Auto|Premium Auto|City Motors|Elite Car)"}}
            ]
        }
        
        result = await self.db.clients.delete_many(query)
        self.cleanup_stats["clients"] = result.deleted_count
        print(f"Deleted {result.deleted_count} test clients")
    
    async def cleanup_users(self):
        """Clean up test users"""
        print("Cleaning up test users...")
        
        # Clean up users with test email patterns
        test_email_patterns = [
            "@abcmotors.com",
            "@xyzauto.com",
            "@premiumauto.sg",
            "@citymotors.sg",
            "@elitecar.sg",
            "@test.com",
            "@example.com"
        ]
        
        query = {
            "$or": [
                {"email": {"$regex": "|".join(test_email_patterns)}},
                {"name": {"$regex": "(Test User|John Smith|Sarah Johnson|Mike Chen|Lisa Wong|David Tan)"}}
            ]
        }
        
        result = await self.db.client_users.delete_many(query)
        self.cleanup_stats["users"] = result.deleted_count
        print(f"Deleted {result.deleted_count} test users")
    
    async def cleanup_conversations(self):
        """Clean up test conversations"""
        print("Cleaning up test conversations...")
        
        # Clean up conversations with test session IDs or test customer info
        query = {
            "$or": [
                {"session_id": {"$regex": "(test|conv_|abc_|xyz_|performance|analytics)"}},
                {"customer_info.email": {"$regex": "@(test|example)\.com"}},
                {"tags": {"$in": ["test", "performance_test", "load_test"]}}
            ]
        }
        
        result = await self.db.conversations.delete_many(query)
        self.cleanup_stats["conversations"] = result.deleted_count
        print(f"Deleted {result.deleted_count} test conversations")
    
    async def cleanup_appointments(self):
        """Clean up test appointments"""
        print("Cleaning up test appointments...")
        
        # Clean up appointments with test data patterns
        query = {
            "$or": [
                {"appointment_id": {"$regex": "(test|apt_|perf_)"}},
                {"customer_email": {"$regex": "@(test|example|concurrent)\.com"}},
                {"customer_name": {"$regex": "(Test|Concurrent|Performance|Alice Tan|Bob Wilson|Carol Lee|David Kumar)"}},
                {"notes": {"$regex": "(test|performance|concurrent)"}}
            ]
        }
        
        result = await self.db.appointments.delete_many(query)
        self.cleanup_stats["appointments"] = result.deleted_count
        print(f"Deleted {result.deleted_count} test appointments")
    
    async def cleanup_vehicles(self):
        """Clean up test vehicles"""
        print("Cleaning up test vehicles...")
        
        # Clean up vehicles with test vehicle IDs or test data
        query = {
            "$or": [
                {"vehicle_id": {"$regex": "(test|veh_)"}},
                {"images": {"$regex": "example\.com"}},
                {"status": "test"}
            ]
        }
        
        result = await self.db.vehicles.delete_many(query)
        self.cleanup_stats["vehicles"] = result.deleted_count
        print(f"Deleted {result.deleted_count} test vehicles")
    
    async def cleanup_services(self):
        """Clean up test services"""
        print("Cleaning up test services...")
        
        # Clean up services with test service IDs
        query = {
            "$or": [
                {"service_id": {"$regex": "(test|svc_)"}},
                {"name": {"$regex": "Test"}},
                {"description": {"$regex": "test"}}
            ]
        }
        
        result = await self.db.services.delete_many(query)
        self.cleanup_stats["services"] = result.deleted_count
        print(f"Deleted {result.deleted_count} test services")
    
    async def cleanup_by_client_ids(self, client_ids: List[str]):
        """Clean up all data for specific client IDs"""
        print(f"Cleaning up data for {len(client_ids)} clients...")
        
        # Convert string IDs to ObjectIds for clients collection
        client_object_ids = [ObjectId(id) for id in client_ids]
        
        # Clean up dependent collections first
        collections_with_client_id = [
            ("services", "client_id"),
            ("vehicles", "client_id"),
            ("appointments", "client_id"),
            ("conversations", "client_id"),
            ("client_users", "client_id")
        ]
        
        for collection_name, field_name in collections_with_client_id:
            collection = getattr(self.db, collection_name)
            result = await collection.delete_many({field_name: {"$in": client_ids}})
            stats_key = collection_name.replace("client_", "")
            self.cleanup_stats[stats_key] = result.deleted_count
            print(f"Deleted {result.deleted_count} {collection_name} for specified clients")
        
        # Finally clean up clients
        result = await self.db.clients.delete_many({"_id": {"$in": client_object_ids}})
        self.cleanup_stats["clients"] = result.deleted_count
        print(f"Deleted {result.deleted_count} clients")
    
    async def cleanup_old_test_data(self, days_old: int = 7):
        """Clean up test data older than specified days"""
        print(f"Cleaning up test data older than {days_old} days...")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Collections with created_at field
        collections_with_dates = [
            "clients",
            "client_users",
            "conversations",
            "appointments",
            "vehicles",
            "services"
        ]
        
        for collection_name in collections_with_dates:
            collection = getattr(self.db, collection_name)
            
            # Combine date filter with test data patterns
            query = {
                "$and": [
                    {"created_at": {"$lt": cutoff_date}},
                    {
                        "$or": [
                            {"_id": {"$regex": "test"}},
                            # Add other test data identifiers as needed
                        ]
                    }
                ]
            }
            
            result = await collection.delete_many(query)
            stats_key = collection_name.replace("client_", "")
            self.cleanup_stats[stats_key] += result.deleted_count
            print(f"Deleted {result.deleted_count} old {collection_name}")
    
    async def _cleanup_by_ids(self, collection_name: str, ids: List[str]) -> int:
        """Helper method to clean up by specific IDs"""
        if not ids:
            return 0
        
        collection = getattr(self.db, collection_name)
        object_ids = [ObjectId(id) for id in ids]
        result = await collection.delete_many({"_id": {"$in": object_ids}})
        print(f"Deleted {result.deleted_count} documents from {collection_name}")
        return result.deleted_count
    
    def _print_cleanup_stats(self):
        """Print cleanup statistics"""
        print("\nCleanup Summary:")
        for collection, count in self.cleanup_stats.items():
            if count > 0:
                print(f"  {collection}: {count} documents deleted")
        
        total_deleted = sum(self.cleanup_stats.values())
        print(f"\nTotal documents deleted: {total_deleted}")
    
    async def verify_cleanup(self) -> Dict[str, int]:
        """Verify cleanup by counting remaining test data"""
        print("Verifying cleanup...")
        
        remaining_counts = {}
        
        # Check for remaining test clients
        test_domains = ["abcmotors.com", "xyzauto.com", "test.com", "example.com"]
        remaining_clients = await self.db.clients.count_documents({
            "domain": {"$in": test_domains}
        })
        remaining_counts["clients"] = remaining_clients
        
        # Check for remaining test users
        remaining_users = await self.db.client_users.count_documents({
            "email": {"$regex": "@(test|example|abcmotors|xyzauto)\.com"}
        })
        remaining_counts["users"] = remaining_users
        
        # Check for remaining test conversations
        remaining_conversations = await self.db.conversations.count_documents({
            "session_id": {"$regex": "(test|conv_|abc_|xyz_)"}
        })
        remaining_counts["conversations"] = remaining_conversations
        
        # Check for remaining test appointments
        remaining_appointments = await self.db.appointments.count_documents({
            "appointment_id": {"$regex": "(test|apt_)"}
        })
        remaining_counts["appointments"] = remaining_appointments
        
        print("\nRemaining test data:")
        for collection, count in remaining_counts.items():
            if count > 0:
                print(f"  {collection}: {count} documents remaining")
            else:
                print(f"  {collection}: ✓ Clean")
        
        return remaining_counts

# Utility functions
async def cleanup_all_test_data(db, confirm: bool = False):
    """Convenience function to clean up all test data"""
    cleanup = TestDataCleanup(db)
    await cleanup.cleanup_all_test_data(confirm=confirm)
    return await cleanup.verify_cleanup()

async def cleanup_from_file(db, test_data_file: str = "test_data_info.json"):
    """Clean up test data based on info file"""
    try:
        with open(test_data_file, "r") as f:
            test_data_info = json.load(f)
        
        cleanup = TestDataCleanup(db)
        await cleanup.cleanup_specific_test_data(test_data_info)
        return await cleanup.verify_cleanup()
    
    except FileNotFoundError:
        print(f"Test data info file '{test_data_file}' not found")
        print("Falling back to general cleanup...")
        return await cleanup_all_test_data(db, confirm=True)

async def cleanup_by_client_names(db, client_names: List[str]):
    """Clean up test data for specific client names"""
    # Find client IDs by business names
    clients = await db.clients.find({
        "business_name": {"$in": client_names}
    }).to_list(length=None)
    
    if not clients:
        print(f"No clients found with names: {client_names}")
        return
    
    client_ids = [str(client["_id"]) for client in clients]
    print(f"Found {len(client_ids)} clients to clean up")
    
    cleanup = TestDataCleanup(db)
    await cleanup.cleanup_by_client_ids(client_ids)
    return await cleanup.verify_cleanup()

if __name__ == "__main__":
    import argparse
    from datetime import timedelta
    
    async def main():
        parser = argparse.ArgumentParser(description="Clean up test data from database")
        parser.add_argument("--confirm", action="store_true", help="Confirm cleanup operation")
        parser.add_argument("--file", type=str, help="Test data info file to use for cleanup")
        parser.add_argument("--clients", nargs="+", help="Specific client names to clean up")
        parser.add_argument("--days", type=int, help="Clean up test data older than N days")
        parser.add_argument("--verify-only", action="store_true", help="Only verify remaining test data")
        
        args = parser.parse_args()
        
        # Connect to test database
        mongo_url = os.getenv("MONGODB_TEST_URL", "mongodb://localhost:27017/automotive_chatbot_test")
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        db = client.get_default_database()
        
        cleanup = TestDataCleanup(db)
        
        try:
            if args.verify_only:
                await cleanup.verify_cleanup()
            elif args.file:
                await cleanup_from_file(db, args.file)
            elif args.clients:
                await cleanup_by_client_names(db, args.clients)
            elif args.days:
                await cleanup.cleanup_old_test_data(args.days)
            else:
                await cleanup.cleanup_all_test_data(confirm=args.confirm)
        
        finally:
            client.close()
    
    asyncio.run(main())