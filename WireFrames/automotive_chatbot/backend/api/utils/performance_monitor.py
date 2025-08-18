"""Performance Monitoring System
Collects and analyzes system performance metrics in real-time
"""

import time
import psutil
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
import json
import os
from threading import Thread, Lock
import statistics

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Single performance metric data point"""
    timestamp: datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'metric_type': self.metric_type,
            'value': self.value,
            'metadata': self.metadata or {}
        }

@dataclass
class SystemSnapshot:
    """System resource snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ResponseTimeMetrics:
    """Response time analysis"""
    count: int
    mean: float
    median: float
    p95: float
    p99: float
    min_time: float
    max_time: float
    std_dev: float

class PerformanceMonitor:
    """Real-time performance monitoring system"""
    
    def __init__(self, max_metrics: int = 10000, collection_interval: int = 5):
        self.max_metrics = max_metrics
        self.collection_interval = collection_interval
        
        # Thread-safe metric storage
        self._metrics_lock = Lock()
        self._metrics: deque = deque(maxlen=max_metrics)
        self._response_times: deque = deque(maxlen=1000)
        self._error_counts: deque = deque(maxlen=1000)
        
        # System monitoring
        self._system_snapshots: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self._monitoring_active = False
        self._monitor_thread: Optional[Thread] = None
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0,
            'response_time_warning': 1000.0,  # ms
            'response_time_critical': 5000.0,  # ms
        }
        
        # Alert callbacks
        self._alert_callbacks: List[callable] = []
        
    def add_alert_callback(self, callback: callable):
        """Add callback function for performance alerts"""
        self._alert_callbacks.append(callback)
        
    def record_metric(self, metric_type: str, value: float, metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_type=metric_type,
            value=value,
            metadata=metadata
        )
        
        with self._metrics_lock:
            self._metrics.append(metric)
            
        # Check for alerts
        self._check_alerts(metric_type, value)
        
    def record_response_time(self, endpoint: str, response_time_ms: float, status_code: int = 200):
        """Record API response time"""
        with self._metrics_lock:
            self._response_times.append({
                'timestamp': datetime.now(),
                'endpoint': endpoint,
                'response_time_ms': response_time_ms,
                'status_code': status_code
            })
            
        self.record_metric('response_time', response_time_ms, {
            'endpoint': endpoint,
            'status_code': status_code
        })
        
    def record_error(self, error_type: str, endpoint: str = None, details: str = None):
        """Record system error"""
        with self._metrics_lock:
            self._error_counts.append({
                'timestamp': datetime.now(),
                'error_type': error_type,
                'endpoint': endpoint,
                'details': details
            })
            
        self.record_metric('error_count', 1, {
            'error_type': error_type,
            'endpoint': endpoint,
            'details': details
        })
        
    def _collect_system_metrics(self) -> SystemSnapshot:
        """Collect current system metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Active connections
            connections = len(psutil.net_connections())
            
            snapshot = SystemSnapshot(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_gb=memory.available / (1024**3),
                disk_percent=disk.percent,
                disk_free_gb=disk.free / (1024**3),
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_connections=connections
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
            
    def _monitor_system(self):
        """Background system monitoring thread"""
        logger.info("Starting system performance monitoring")
        
        while self._monitoring_active:
            try:
                snapshot = self._collect_system_metrics()
                if snapshot:
                    with self._metrics_lock:
                        self._system_snapshots.append(snapshot)
                    
                    # Record individual metrics
                    self.record_metric('cpu_usage', snapshot.cpu_percent)
                    self.record_metric('memory_usage', snapshot.memory_percent)
                    self.record_metric('disk_usage', snapshot.disk_percent)
                    
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(self.collection_interval)
                
    def start_monitoring(self):
        """Start background performance monitoring"""
        if not self._monitoring_active:
            self._monitoring_active = True
            self._monitor_thread = Thread(target=self._monitor_system, daemon=True)
            self._monitor_thread.start()
            logger.info("Performance monitoring started")
            
    def stop_monitoring(self):
        """Stop background performance monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
        
    def _check_alerts(self, metric_type: str, value: float):
        """Check if metric value triggers alerts"""
        alerts = []
        
        if metric_type == 'cpu_usage':
            if value >= self.thresholds['cpu_critical']:
                alerts.append(('critical', f"CPU usage critical: {value:.1f}%"))
            elif value >= self.thresholds['cpu_warning']:
                alerts.append(('warning', f"CPU usage high: {value:.1f}%"))
                
        elif metric_type == 'memory_usage':
            if value >= self.thresholds['memory_critical']:
                alerts.append(('critical', f"Memory usage critical: {value:.1f}%"))
            elif value >= self.thresholds['memory_warning']:
                alerts.append(('warning', f"Memory usage high: {value:.1f}%"))
                
        elif metric_type == 'disk_usage':
            if value >= self.thresholds['disk_critical']:
                alerts.append(('critical', f"Disk usage critical: {value:.1f}%"))
            elif value >= self.thresholds['disk_warning']:
                alerts.append(('warning', f"Disk usage high: {value:.1f}%"))
                
        elif metric_type == 'response_time':
            if value >= self.thresholds['response_time_critical']:
                alerts.append(('critical', f"Response time critical: {value:.1f}ms"))
            elif value >= self.thresholds['response_time_warning']:
                alerts.append(('warning', f"Response time high: {value:.1f}ms"))
        
        # Trigger alert callbacks
        for severity, message in alerts:
            for callback in self._alert_callbacks:
                try:
                    callback(severity, metric_type, value, message)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
                    
    def get_response_time_analysis(self, minutes: int = 60) -> ResponseTimeMetrics:
        """Analyze response times for the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self._metrics_lock:
            recent_times = [
                rt['response_time_ms'] for rt in self._response_times
                if rt['timestamp'] >= cutoff_time
            ]
            
        if not recent_times:
            return ResponseTimeMetrics(0, 0, 0, 0, 0, 0, 0, 0)
            
        recent_times.sort()
        count = len(recent_times)
        
        return ResponseTimeMetrics(
            count=count,
            mean=statistics.mean(recent_times),
            median=statistics.median(recent_times),
            p95=recent_times[int(0.95 * count)] if count > 0 else 0,
            p99=recent_times[int(0.99 * count)] if count > 0 else 0,
            min_time=min(recent_times),
            max_time=max(recent_times),
            std_dev=statistics.stdev(recent_times) if count > 1 else 0
        )
        
    def get_error_rate(self, minutes: int = 60) -> Dict[str, Any]:
        """Calculate error rate for the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self._metrics_lock:
            recent_errors = [
                err for err in self._error_counts
                if err['timestamp'] >= cutoff_time
            ]
            
            recent_responses = [
                rt for rt in self._response_times
                if rt['timestamp'] >= cutoff_time
            ]
            
        total_requests = len(recent_responses)
        total_errors = len(recent_errors)
        
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Group errors by type
        error_types = {}
        for error in recent_errors:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate_percent': error_rate,
            'error_types': error_types
        }
        
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get current system health summary"""
        with self._metrics_lock:
            latest_snapshot = self._system_snapshots[-1] if self._system_snapshots else None
            
        if not latest_snapshot:
            return {'status': 'unknown', 'message': 'No system data available'}
            
        # Determine overall health status
        status = 'healthy'
        issues = []
        
        if latest_snapshot.cpu_percent >= self.thresholds['cpu_critical']:
            status = 'critical'
            issues.append(f"CPU usage critical: {latest_snapshot.cpu_percent:.1f}%")
        elif latest_snapshot.cpu_percent >= self.thresholds['cpu_warning']:
            status = 'warning' if status == 'healthy' else status
            issues.append(f"CPU usage high: {latest_snapshot.cpu_percent:.1f}%")
            
        if latest_snapshot.memory_percent >= self.thresholds['memory_critical']:
            status = 'critical'
            issues.append(f"Memory usage critical: {latest_snapshot.memory_percent:.1f}%")
        elif latest_snapshot.memory_percent >= self.thresholds['memory_warning']:
            status = 'warning' if status == 'healthy' else status
            issues.append(f"Memory usage high: {latest_snapshot.memory_percent:.1f}%")
            
        if latest_snapshot.disk_percent >= self.thresholds['disk_critical']:
            status = 'critical'
            issues.append(f"Disk usage critical: {latest_snapshot.disk_percent:.1f}%")
        elif latest_snapshot.disk_percent >= self.thresholds['disk_warning']:
            status = 'warning' if status == 'healthy' else status
            issues.append(f"Disk usage high: {latest_snapshot.disk_percent:.1f}%")
            
        return {
            'status': status,
            'timestamp': latest_snapshot.timestamp.isoformat(),
            'cpu_percent': latest_snapshot.cpu_percent,
            'memory_percent': latest_snapshot.memory_percent,
            'disk_percent': latest_snapshot.disk_percent,
            'active_connections': latest_snapshot.active_connections,
            'issues': issues
        }
        
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Response time analysis
        response_analysis = self.get_response_time_analysis(minutes=hours*60)
        
        # Error rate analysis
        error_analysis = self.get_error_rate(minutes=hours*60)
        
        # System resource trends
        with self._metrics_lock:
            recent_snapshots = [
                snap for snap in self._system_snapshots
                if snap.timestamp >= cutoff_time
            ]
            
        if recent_snapshots:
            avg_cpu = statistics.mean([s.cpu_percent for s in recent_snapshots])
            avg_memory = statistics.mean([s.memory_percent for s in recent_snapshots])
            avg_disk = statistics.mean([s.disk_percent for s in recent_snapshots])
        else:
            avg_cpu = avg_memory = avg_disk = 0
            
        return {
            'report_period_hours': hours,
            'generated_at': datetime.now().isoformat(),
            'response_times': asdict(response_analysis),
            'error_analysis': error_analysis,
            'system_resources': {
                'average_cpu_percent': avg_cpu,
                'average_memory_percent': avg_memory,
                'average_disk_percent': avg_disk,
                'snapshots_count': len(recent_snapshots)
            },
            'health_summary': self.get_system_health_summary()
        }
        
    def export_metrics(self, filepath: str, hours: int = 24):
        """Export metrics to JSON file"""
        report = self.get_performance_report(hours)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Performance metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        _performance_monitor.start_monitoring()
    return _performance_monitor

def record_api_performance(endpoint: str, response_time_ms: float, status_code: int = 200):
    """Convenience function to record API performance"""
    monitor = get_performance_monitor()
    monitor.record_response_time(endpoint, response_time_ms, status_code)

def record_system_error(error_type: str, endpoint: str = None, details: str = None):
    """Convenience function to record system errors"""
    monitor = get_performance_monitor()
    monitor.record_error(error_type, endpoint, details)

def get_health_summary() -> Dict[str, Any]:
    """Convenience function to get system health summary"""
    monitor = get_performance_monitor()
    return monitor.get_system_health_summary()

# Create a global instance for backward compatibility
performance_monitor = get_performance_monitor()

if __name__ == "__main__":
    # Test the performance monitor
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Add some test metrics
    import random
    for i in range(10):
        monitor.record_response_time('/api/test', random.uniform(100, 500))
        time.sleep(1)
        
    # Generate report
    report = monitor.get_performance_report(hours=1)
    print(json.dumps(report, indent=2, default=str))
    
    monitor.stop_monitoring()