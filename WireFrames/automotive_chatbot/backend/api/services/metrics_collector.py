"""\nMetrics Collector Service\nCollects and stores system performance metrics for analysis and monitoring\n"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json

from ..utils.performance_monitor import get_performance_monitor, PerformanceMetric
from ..utils.health_monitor import HealthMonitor
from ..services.database_pool import get_database_pool
from ..services.cache_service import get_cache_service

logger = logging.getLogger(__name__)

@dataclass
class MetricSnapshot:
    """Represents a point-in-time system metric snapshot"""
    timestamp: datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any]
    source: str
    tags: List[str]

@dataclass
class SystemSnapshot:
    """Comprehensive system state snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    response_times: Dict[str, float]
    error_counts: Dict[str, int]
    service_status: Dict[str, str]
    custom_metrics: Dict[str, Any]

class MetricsCollector:
    """Service for collecting and storing system metrics"""
    
    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.performance_monitor = get_performance_monitor()
        self.health_monitor = HealthMonitor()
        self.is_running = False
        self._collection_task = None
        self._metrics_buffer = []
        self._buffer_size = 1000
        
    async def start_collection(self):
        """Start the metrics collection process"""
        if self.is_running:
            logger.warning("Metrics collection is already running")
            return
            
        self.is_running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info(f"Started metrics collection with {self.collection_interval}s interval")
        
    async def stop_collection(self):
        """Stop the metrics collection process"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
                
        # Flush remaining metrics
        await self._flush_metrics_buffer()
        logger.info("Stopped metrics collection")
        
    async def _collection_loop(self):
        """Main collection loop"""
        while self.is_running:
            try:
                await self._collect_system_snapshot()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {str(e)}")
                await asyncio.sleep(5)  # Short delay before retry
                
    async def _collect_system_snapshot(self):
        """Collect a comprehensive system snapshot"""
        try:
            timestamp = datetime.utcnow()
            
            # Collect system resources
            system_resources = self.health_monitor.check_system_resources()
            
            # Collect service status
            service_status = await self.health_monitor.monitor_all_services()
            service_status_simple = {k: v.get('status', 'unknown') for k, v in service_status.items()}
            
            # Collect performance metrics
            recent_metrics = self.performance_monitor.get_recent_metrics(minutes=1)
            
            # Calculate response times by endpoint
            response_times = self._calculate_response_times(recent_metrics)
            
            # Calculate error counts
            error_counts = self._calculate_error_counts(recent_metrics)
            
            # Get custom metrics
            custom_metrics = await self._collect_custom_metrics()
            
            # Create system snapshot
            snapshot = SystemSnapshot(
                timestamp=timestamp,
                cpu_percent=system_resources.get('cpu_percent', 0),
                memory_percent=system_resources.get('memory_percent', 0),
                disk_percent=system_resources.get('disk_percent', 0),
                network_bytes_sent=system_resources.get('network_bytes_sent', 0),
                network_bytes_recv=system_resources.get('network_bytes_recv', 0),
                active_connections=self.performance_monitor.active_connections,
                response_times=response_times,
                error_counts=error_counts,
                service_status=service_status_simple,
                custom_metrics=custom_metrics
            )
            
            # Store snapshot
            await self._store_snapshot(snapshot)
            
            # Add individual metrics to buffer
            await self._add_individual_metrics(snapshot)
            
        except Exception as e:
            logger.error(f"Failed to collect system snapshot: {str(e)}")
            
    def _calculate_response_times(self, metrics: List[PerformanceMetric]) -> Dict[str, float]:
        """Calculate average response times by endpoint"""
        endpoint_times = {}
        endpoint_counts = {}
        
        for metric in metrics:
            if metric.metric_type == 'response_time':
                endpoint = metric.metadata.get('endpoint', 'unknown')
                if endpoint not in endpoint_times:
                    endpoint_times[endpoint] = 0
                    endpoint_counts[endpoint] = 0
                    
                endpoint_times[endpoint] += metric.value
                endpoint_counts[endpoint] += 1
                
        # Calculate averages
        return {
            endpoint: endpoint_times[endpoint] / endpoint_counts[endpoint]
            for endpoint in endpoint_times
            if endpoint_counts[endpoint] > 0
        }
        
    def _calculate_error_counts(self, metrics: List[PerformanceMetric]) -> Dict[str, int]:
        """Calculate error counts by type"""
        error_counts = {}
        
        for metric in metrics:
            if metric.metric_type == 'error':
                error_type = metric.metadata.get('error_type', 'unknown')
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
        return error_counts
        
    async def _collect_custom_metrics(self) -> Dict[str, Any]:
        """Collect custom application-specific metrics"""
        custom_metrics = {}
        
        try:
            # Database metrics
            db_pool = get_database_pool()
            db_stats = db_pool.get_pool_stats()
            custom_metrics['database'] = db_stats
            
            # Cache metrics
            cache_service = get_cache_service()
            cache_stats = await cache_service.get_stats()
            custom_metrics['cache'] = cache_stats
            
            # Performance monitor metrics
            perf_summary = self.performance_monitor.get_performance_summary()
            custom_metrics['performance_summary'] = perf_summary
            
        except Exception as e:
            logger.error(f"Failed to collect custom metrics: {str(e)}")
            
        return custom_metrics
        
    async def _store_snapshot(self, snapshot: SystemSnapshot):
        """Store system snapshot in database"""
        try:
            db_pool = get_database_pool()
            db = await db_pool.get_database()
            
            # Convert snapshot to dict
            snapshot_dict = asdict(snapshot)
            snapshot_dict['timestamp'] = snapshot.timestamp.isoformat()
            
            # Store in metrics collection
            await db.system_snapshots.insert_one(snapshot_dict)
            
            # Also cache recent snapshot
            cache_service = get_cache_service()
            await cache_service.set(
                'latest_system_snapshot',
                snapshot_dict,
                ttl=300  # 5 minutes
            )
            
        except Exception as e:
            logger.error(f"Failed to store system snapshot: {str(e)}")
            
    async def _add_individual_metrics(self, snapshot: SystemSnapshot):
        """Add individual metrics to buffer for detailed analysis"""
        timestamp = snapshot.timestamp
        
        # System resource metrics
        metrics = [
            MetricSnapshot(
                timestamp=timestamp,
                metric_type='cpu_usage',
                value=snapshot.cpu_percent,
                metadata={'unit': 'percent'},
                source='system',
                tags=['system', 'cpu']
            ),
            MetricSnapshot(
                timestamp=timestamp,
                metric_type='memory_usage',
                value=snapshot.memory_percent,
                metadata={'unit': 'percent'},
                source='system',
                tags=['system', 'memory']
            ),
            MetricSnapshot(
                timestamp=timestamp,
                metric_type='disk_usage',
                value=snapshot.disk_percent,
                metadata={'unit': 'percent'},
                source='system',
                tags=['system', 'disk']
            ),
            MetricSnapshot(
                timestamp=timestamp,
                metric_type='active_connections',
                value=snapshot.active_connections,
                metadata={'unit': 'count'},
                source='application',
                tags=['network', 'connections']
            )
        ]
        
        # Response time metrics
        for endpoint, response_time in snapshot.response_times.items():
            metrics.append(MetricSnapshot(
                timestamp=timestamp,
                metric_type='response_time',
                value=response_time,
                metadata={'endpoint': endpoint, 'unit': 'milliseconds'},
                source='application',
                tags=['performance', 'response_time']
            ))
            
        # Error count metrics
        for error_type, count in snapshot.error_counts.items():
            metrics.append(MetricSnapshot(
                timestamp=timestamp,
                metric_type='error_count',
                value=count,
                metadata={'error_type': error_type, 'unit': 'count'},
                source='application',
                tags=['errors', error_type]
            ))
            
        # Add to buffer
        self._metrics_buffer.extend(metrics)
        
        # Flush buffer if it's getting full
        if len(self._metrics_buffer) >= self._buffer_size:
            await self._flush_metrics_buffer()
            
    async def _flush_metrics_buffer(self):
        """Flush metrics buffer to database"""
        if not self._metrics_buffer:
            return
            
        try:
            db_pool = get_database_pool()
            db = await db_pool.get_database()
            
            # Convert metrics to dicts
            metrics_dicts = []
            for metric in self._metrics_buffer:
                metric_dict = asdict(metric)
                metric_dict['timestamp'] = metric.timestamp.isoformat()
                metrics_dicts.append(metric_dict)
                
            # Bulk insert
            if metrics_dicts:
                await db.metrics.insert_many(metrics_dicts)
                logger.debug(f"Flushed {len(metrics_dicts)} metrics to database")
                
            # Clear buffer
            self._metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics buffer: {str(e)}")
            
    async def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for the specified time period"""
        try:
            db_pool = get_database_pool()
            db = await db_pool.get_database()
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Query metrics
            pipeline = [
                {
                    '$match': {
                        'timestamp': {
                            '$gte': start_time.isoformat(),
                            '$lte': end_time.isoformat()
                        }
                    }
                },
                {
                    '$group': {
                        '_id': '$metric_type',
                        'avg_value': {'$avg': '$value'},
                        'min_value': {'$min': '$value'},
                        'max_value': {'$max': '$value'},
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            results = await db.metrics.aggregate(pipeline).to_list(None)
            
            # Format results
            summary = {
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'hours': hours
                },
                'metrics': {}
            }
            
            for result in results:
                metric_type = result['_id']
                summary['metrics'][metric_type] = {
                    'average': round(result['avg_value'], 2),
                    'minimum': round(result['min_value'], 2),
                    'maximum': round(result['max_value'], 2),
                    'count': result['count']
                }
                
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {str(e)}")
            return {'error': str(e)}
            
    async def cleanup_old_metrics(self, days: int = 30):
        """Clean up old metrics data"""
        try:
            db_pool = get_database_pool()
            db = await db_pool.get_database()
            
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            # Delete old metrics
            result = await db.metrics.delete_many({
                'timestamp': {'$lt': cutoff_time.isoformat()}
            })
            
            # Delete old snapshots
            snapshot_result = await db.system_snapshots.delete_many({
                'timestamp': {'$lt': cutoff_time.isoformat()}
            })
            
            logger.info(
                f"Cleaned up {result.deleted_count} metrics and "
                f"{snapshot_result.deleted_count} snapshots older than {days} days"
            )
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {str(e)}")

# Global metrics collector instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

async def start_metrics_collection():
    """Start the global metrics collection"""
    collector = get_metrics_collector()
    await collector.start_collection()

async def stop_metrics_collection():
    """Stop the global metrics collection"""
    collector = get_metrics_collector()
    await collector.stop_collection()