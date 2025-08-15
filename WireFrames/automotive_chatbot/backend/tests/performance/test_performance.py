#!/usr/bin/env python3
"""
Performance tests for concurrent usage and load testing
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
import secrets
from bson import ObjectId
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import httpx

@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentUsage:
    """Test concurrent usage scenarios"""
    
    async def test_concurrent_client_logins(self, async_client, clean_db, performance_test_clients):
        """Test concurrent client login performance"""
        clients_data = performance_test_clients
        
        # Prepare login tasks
        login_tasks = []
        for client_data in clients_data:
            login_data = {
                "email": client_data["admin_user"]["email"],
                "password": client_data["admin_user"]["password"]
            }
            task = async_client.post("/api/auth/client-login", json=login_data)
            login_tasks.append(task)
        
        # Measure concurrent login performance
        start_time = time.time()
        responses = await asyncio.gather(*login_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_logins = 0
        
        for response in responses:
            if not isinstance(response, Exception) and hasattr(response, 'status_code'):
                if response.status_code == status.HTTP_200_OK:
                    successful_logins += 1
        
        # Performance assertions
        assert total_time < 10.0  # Should complete within 10 seconds
        assert successful_logins >= len(clients_data) * 0.8  # At least 80% success rate
        
        # Calculate average response time
        avg_response_time = total_time / len(clients_data)
        assert avg_response_time < 2.0  # Average response time under 2 seconds
    
    async def test_concurrent_widget_chat_requests(self, async_client, clean_db, test_client_with_user):
        """Test concurrent widget chat request performance"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Prepare concurrent chat requests
        chat_tasks = []
        num_concurrent_requests = 20
        
        for i in range(num_concurrent_requests):
            chat_data = {
                "message": f"Concurrent test message {i}",
                "session_id": f"perf_session_{i}",
                "client_id": client_id
            }
            task = async_client.post("/api/widget/chat", json=chat_data)
            chat_tasks.append(task)
        
        # Measure performance
        start_time = time.time()
        responses = await asyncio.gather(*chat_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_requests = 0
        response_times = []
        
        for response in responses:
            if not isinstance(response, Exception) and hasattr(response, 'status_code'):
                if response.status_code == status.HTTP_200_OK:
                    successful_requests += 1
        
        # Performance assertions
        assert total_time < 15.0  # Should complete within 15 seconds
        assert successful_requests >= num_concurrent_requests * 0.7  # At least 70% success rate
        
        # Calculate throughput
        throughput = successful_requests / total_time
        assert throughput >= 1.0  # At least 1 request per second
    
    async def test_concurrent_appointment_bookings(self, async_client, clean_db, test_client_with_user):
        """Test concurrent appointment booking performance"""
        client_data = test_client_with_user
        headers = {"Authorization": f"Bearer {client_data['token']}"}
        
        # Prepare concurrent appointment bookings
        booking_tasks = []
        num_bookings = 10
        
        for i in range(num_bookings):
            appointment_data = {
                "customer_name": f"Concurrent Customer {i}",
                "customer_email": f"customer{i}@concurrent.com",
                "customer_phone": f"+65 61{i:02d} 4567",
                "appointment_datetime": (datetime.utcnow() + timedelta(days=i+1)).isoformat(),
                "service_type": "test_drive",
                "vehicle_interest": "Toyota Camry"
            }
            task = async_client.post("/api/appointments/", json=appointment_data, headers=headers)
            booking_tasks.append(task)
        
        # Measure performance
        start_time = time.time()
        responses = await asyncio.gather(*booking_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_bookings = 0
        
        for response in responses:
            if not isinstance(response, Exception) and hasattr(response, 'status_code'):
                if response.status_code == status.HTTP_201_CREATED:
                    successful_bookings += 1
        
        # Performance assertions
        assert total_time < 10.0  # Should complete within 10 seconds
        assert successful_bookings >= num_bookings * 0.8  # At least 80% success rate
    
    async def test_concurrent_multi_client_operations(self, async_client, clean_db, performance_test_clients):
        """Test concurrent operations across multiple clients"""
        clients_data = performance_test_clients[:3]  # Use first 3 clients
        
        # Create authenticated clients
        authenticated_clients = []
        for client_data in clients_data:
            auth_client = await self._authenticate_client(async_client, clean_db, client_data)
            if auth_client:
                authenticated_clients.append(auth_client)
        
        if len(authenticated_clients) < 2:
            pytest.skip("Need at least 2 authenticated clients for multi-client test")
        
        # Prepare mixed operations for each client
        all_tasks = []
        
        for auth_client in authenticated_clients:
            client_id = auth_client["client_id"]
            headers = auth_client["headers"]
            
            # Chat request
            chat_task = async_client.post("/api/widget/chat", json={
                "message": f"Multi-client test from {client_id}",
                "session_id": f"multi_{client_id}_{secrets.token_hex(4)}",
                "client_id": client_id
            })
            all_tasks.append(chat_task)
            
            # Appointment booking
            appointment_task = async_client.post("/api/appointments/", json={
                "customer_name": f"Multi Customer {client_id[:8]}",
                "customer_email": f"multi{client_id[:8]}@test.com",
                "customer_phone": f"+65 6{len(client_id) % 10}00 0000",
                "appointment_datetime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "service_type": "consultation"
            }, headers=headers)
            all_tasks.append(appointment_task)
            
            # Stats request
            stats_task = async_client.get("/api/conversation/stats", headers=headers)
            all_tasks.append(stats_task)
        
        # Execute all operations concurrently
        start_time = time.time()
        responses = await asyncio.gather(*all_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_operations = 0
        
        for response in responses:
            if not isinstance(response, Exception) and hasattr(response, 'status_code'):
                if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
                    successful_operations += 1
        
        # Performance assertions
        assert total_time < 20.0  # Should complete within 20 seconds
        assert successful_operations >= len(all_tasks) * 0.6  # At least 60% success rate
    
    async def _authenticate_client(self, async_client, clean_db, client_data):
        """Helper to authenticate a client and return client info"""
        try:
            # Create client if not exists
            client_id = await self._ensure_client_exists(clean_db, client_data)
            
            # Login
            login_data = {
                "email": client_data["admin_user"]["email"],
                "password": client_data["admin_user"]["password"]
            }
            
            response = await async_client.post("/api/auth/client-login", json=login_data)
            
            if response.status_code == status.HTTP_200_OK:
                token_data = response.json()
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                
                return {
                    "client_id": client_id,
                    "headers": headers,
                    "token": token_data["access_token"]
                }
        except Exception:
            pass
        
        return None
    
    async def _ensure_client_exists(self, db, client_data):
        """Helper to ensure client exists in database"""
        from conftest import hash_password
        
        # Check if client exists
        existing_client = await db.clients.find_one({"domain": client_data["domain"]})
        
        if existing_client:
            return str(existing_client["_id"])
        
        # Create client
        client_doc = {
            "business_name": client_data["business_name"],
            "domain": client_data["domain"],
            "contact_email": client_data["contact_email"],
            "status": "active",
            "api_key": f"cc_{secrets.token_urlsafe(32)}",
            "created_at": datetime.utcnow()
        }
        
        client_result = await db.clients.insert_one(client_doc)
        client_id = str(client_result.inserted_id)
        
        # Create user
        user_doc = {
            "client_id": client_id,
            "name": client_data["admin_user"]["name"],
            "email": client_data["admin_user"]["email"],
            "password_hash": hash_password(client_data["admin_user"]["password"]),
            "role": "admin",
            "status": "active",
            "created_at": datetime.utcnow()
        }
        
        await db.client_users.insert_one(user_doc)
        
        return client_id

@pytest.mark.performance
@pytest.mark.slow
class TestLoadTesting:
    """Test system load and scalability"""
    
    async def test_widget_endpoint_load(self, async_client, clean_db, test_client_with_user):
        """Test widget endpoint under load"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test widget config endpoint load
        num_requests = 50
        config_tasks = []
        
        for i in range(num_requests):
            task = async_client.get(f"/api/widget/config/{client_id}")
            config_tasks.append(task)
        
        # Measure load performance
        start_time = time.time()
        responses = await asyncio.gather(*config_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_requests = 0
        response_times = []
        
        for response in responses:
            if not isinstance(response, Exception) and hasattr(response, 'status_code'):
                if response.status_code == status.HTTP_200_OK:
                    successful_requests += 1
        
        # Load testing assertions
        assert total_time < 30.0  # Should handle load within 30 seconds
        assert successful_requests >= num_requests * 0.9  # At least 90% success rate
        
        # Calculate throughput
        throughput = successful_requests / total_time
        assert throughput >= 2.0  # At least 2 requests per second
    
    async def test_authentication_endpoint_load(self, async_client, clean_db, performance_test_clients):
        """Test authentication endpoint under load"""
        clients_data = performance_test_clients
        
        # Create multiple login attempts
        login_tasks = []
        num_attempts_per_client = 5
        
        for client_data in clients_data:
            for _ in range(num_attempts_per_client):
                login_data = {
                    "email": client_data["admin_user"]["email"],
                    "password": client_data["admin_user"]["password"]
                }
                task = async_client.post("/api/auth/client-login", json=login_data)
                login_tasks.append(task)
        
        # Measure authentication load
        start_time = time.time()
        responses = await asyncio.gather(*login_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_logins = 0
        
        for response in responses:
            if not isinstance(response, Exception) and hasattr(response, 'status_code'):
                if response.status_code == status.HTTP_200_OK:
                    successful_logins += 1
        
        # Load testing assertions
        assert total_time < 25.0  # Should handle auth load within 25 seconds
        assert successful_logins >= len(login_tasks) * 0.8  # At least 80% success rate
    
    async def test_database_query_performance(self, clean_db, test_client_with_user):
        """Test database query performance under load"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Create test data for performance testing
        await self._create_performance_test_data(clean_db, client_id)
        
        # Test concurrent database queries
        query_tasks = []
        num_queries = 30
        
        for i in range(num_queries):
            # Mix different types of queries
            if i % 3 == 0:
                # Client lookup
                task = clean_db.clients.find_one({"_id": ObjectId(client_id)})
            elif i % 3 == 1:
                # Conversation queries
                task = clean_db.conversations.find({"client_id": client_id}).limit(10).to_list(length=None)
            else:
                # Appointment queries
                task = clean_db.appointments.find({"client_id": client_id}).limit(10).to_list(length=None)
            
            query_tasks.append(task)
        
        # Measure database performance
        start_time = time.time()
        results = await asyncio.gather(*query_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_queries = 0
        
        for result in results:
            if not isinstance(result, Exception):
                successful_queries += 1
        
        # Database performance assertions
        assert total_time < 5.0  # Database queries should be fast
        assert successful_queries >= num_queries * 0.95  # At least 95% success rate
        
        # Calculate query throughput
        query_throughput = successful_queries / total_time
        assert query_throughput >= 10.0  # At least 10 queries per second
    
    async def test_memory_usage_under_load(self, async_client, clean_db, test_client_with_user):
        """Test memory usage patterns under load"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Create large payload requests
        large_message = "A" * 1000  # 1KB message
        chat_tasks = []
        num_large_requests = 20
        
        for i in range(num_large_requests):
            chat_data = {
                "message": f"{large_message} - Request {i}",
                "session_id": f"memory_test_{i}",
                "client_id": client_id
            }
            task = async_client.post("/api/widget/chat", json=chat_data)
            chat_tasks.append(task)
        
        # Process requests in batches to test memory handling
        batch_size = 5
        successful_requests = 0
        
        for i in range(0, len(chat_tasks), batch_size):
            batch = chat_tasks[i:i + batch_size]
            
            start_time = time.time()
            responses = await asyncio.gather(*batch, return_exceptions=True)
            end_time = time.time()
            
            batch_time = end_time - start_time
            
            for response in responses:
                if not isinstance(response, Exception) and hasattr(response, 'status_code'):
                    if response.status_code == status.HTTP_200_OK:
                        successful_requests += 1
            
            # Each batch should complete reasonably quickly
            assert batch_time < 10.0
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        # Memory usage assertions
        assert successful_requests >= num_large_requests * 0.8  # At least 80% success rate
    
    async def _create_performance_test_data(self, db, client_id):
        """Helper to create test data for performance testing"""
        # Create conversations
        conversations = [
            {
                "client_id": client_id,
                "session_id": f"perf_session_{i}",
                "content": f"Performance test conversation {i}",
                "timestamp": datetime.utcnow() - timedelta(hours=i),
                "message_count": i + 1
            }
            for i in range(20)
        ]
        
        await db.conversations.insert_many(conversations)
        
        # Create appointments
        appointments = [
            {
                "client_id": client_id,
                "appointment_id": f"perf_apt_{i}",
                "customer_name": f"Performance Customer {i}",
                "customer_email": f"perf{i}@test.com",
                "customer_phone": f"+65 6{i:03d} 0000",
                "appointment_datetime": datetime.utcnow() + timedelta(days=i),
                "service_type": "test_drive",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            for i in range(15)
        ]
        
        await db.appointments.insert_many(appointments)

@pytest.mark.performance
@pytest.mark.slow
class TestResponseTimeAnalysis:
    """Test response time analysis and optimization"""
    
    async def test_api_response_times(self, async_client, clean_db, test_client_with_user):
        """Test API endpoint response times"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        headers = {"Authorization": f"Bearer {client_data['token']}"}
        
        # Test different endpoints and measure response times
        endpoints_to_test = [
            ("/api/conversation/stats", "GET", headers),
            ("/api/appointments/", "GET", headers),
            (f"/api/widget/config/{client_id}", "GET", None),
            (f"/api/widget/embed/{client_id}", "GET", None)
        ]
        
        response_times = {}
        
        for endpoint, method, test_headers in endpoints_to_test:
            times = []
            
            # Test each endpoint multiple times
            for _ in range(5):
                start_time = time.time()
                
                if method == "GET":
                    response = await async_client.get(endpoint, headers=test_headers)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if hasattr(response, 'status_code') and response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]:
                    times.append(response_time)
                
                # Small delay between requests
                await asyncio.sleep(0.1)
            
            if times:
                avg_time = statistics.mean(times)
                max_time = max(times)
                min_time = min(times)
                
                response_times[endpoint] = {
                    "average": avg_time,
                    "max": max_time,
                    "min": min_time,
                    "samples": len(times)
                }
                
                # Response time assertions
                assert avg_time < 3.0  # Average response time under 3 seconds
                assert max_time < 5.0  # Maximum response time under 5 seconds
        
        # Verify we tested at least some endpoints
        assert len(response_times) > 0
    
    async def test_widget_chat_response_time(self, async_client, clean_db, test_client_with_user):
        """Test widget chat response time performance"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        chat_response_times = []
        num_tests = 10
        
        for i in range(num_tests):
            chat_data = {
                "message": f"Response time test message {i}",
                "session_id": f"response_time_test_{i}",
                "client_id": client_id
            }
            
            start_time = time.time()
            response = await async_client.post("/api/widget/chat", json=chat_data)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if hasattr(response, 'status_code') and response.status_code == status.HTTP_200_OK:
                chat_response_times.append(response_time)
            
            # Small delay between requests
            await asyncio.sleep(0.2)
        
        if chat_response_times:
            avg_chat_time = statistics.mean(chat_response_times)
            max_chat_time = max(chat_response_times)
            p95_chat_time = statistics.quantiles(chat_response_times, n=20)[18] if len(chat_response_times) >= 5 else max_chat_time
            
            # Chat response time assertions
            assert avg_chat_time < 5.0  # Average chat response under 5 seconds
            assert max_chat_time < 10.0  # Maximum chat response under 10 seconds
            assert p95_chat_time < 8.0  # 95th percentile under 8 seconds
    
    async def test_database_operation_timing(self, clean_db, test_client_with_user):
        """Test database operation timing"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test different database operations
        db_operation_times = {}
        
        # Test client lookup
        start_time = time.time()
        client = await clean_db.clients.find_one({"_id": ObjectId(client_id)})
        end_time = time.time()
        db_operation_times["client_lookup"] = end_time - start_time
        
        # Test conversation insert
        conversation_doc = {
            "client_id": client_id,
            "session_id": "timing_test",
            "content": "Database timing test",
            "timestamp": datetime.utcnow(),
            "message_count": 1
        }
        
        start_time = time.time()
        await clean_db.conversations.insert_one(conversation_doc)
        end_time = time.time()
        db_operation_times["conversation_insert"] = end_time - start_time
        
        # Test conversation query
        start_time = time.time()
        conversations = await clean_db.conversations.find({"client_id": client_id}).limit(10).to_list(length=None)
        end_time = time.time()
        db_operation_times["conversation_query"] = end_time - start_time
        
        # Database timing assertions
        for operation, timing in db_operation_times.items():
            assert timing < 1.0  # All database operations under 1 second
        
        # Specific operation assertions
        assert db_operation_times["client_lookup"] < 0.1  # Client lookup very fast
        assert db_operation_times["conversation_insert"] < 0.5  # Insert reasonably fast
        assert db_operation_times["conversation_query"] < 0.3  # Query reasonably fast