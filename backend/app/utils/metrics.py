"""
Metrics Module
Prometheus metrics for observability
"""

import time
from functools import wraps
from typing import Callable, Any

# Prometheus client (optional import)
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


# Define metrics
if PROMETHEUS_AVAILABLE:
    # API Metrics
    http_requests_total = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status']
    )
    
    http_request_duration_seconds = Histogram(
        'http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint']
    )
    
    # Calendar Metrics
    events_created_total = Counter(
        'events_created_total',
        'Total events created',
        ['user_id']
    )
    
    events_updated_total = Counter(
        'events_updated_total',
        'Total events updated',
        ['user_id']
    )
    
    events_deleted_total = Counter(
        'events_deleted_total',
        'Total events deleted',
        ['user_id']
    )
    
    events_fetched_total = Counter(
        'events_fetched_total',
        'Total events fetched from Google Calendar'
    )
    
    # Cache Metrics
    cache_hits_total = Counter(
        'cache_hits_total',
        'Total cache hits'
    )
    
    cache_misses_total = Counter(
        'cache_misses_total',
        'Total cache misses'
    )
    
    # Agent Metrics
    agent_queries_total = Counter(
        'agent_queries_total',
        'Total agent queries',
        ['user_id', 'intent']
    )
    
    agent_response_duration_seconds = Histogram(
        'agent_response_duration_seconds',
        'Agent response time in seconds'
    )
    
    agent_tool_calls_total = Counter(
        'agent_tool_calls_total',
        'Total agent tool calls',
        ['tool_name', 'success']
    )
    
    # System Metrics
    active_users = Gauge(
        'active_users',
        'Number of currently active users'
    )
    
    google_api_quota_remaining = Gauge(
        'google_api_quota_remaining',
        'Google API quota remaining'
    )


def track_latency(endpoint: str = "unknown"):
    """Decorator to track request latency"""
    
    def decorator(func: Callable) -> Callable:
        if not PROMETHEUS_AVAILABLE:
            return func
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                http_request_duration_seconds.labels(
                    method="POST",
                    endpoint=endpoint
                ).observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                http_request_duration_seconds.labels(
                    method="GET",
                    endpoint=endpoint
                ).observe(duration)
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def increment_counter(counter: Counter, **labels):
    """Safely increment a counter"""
    if PROMETHEUS_AVAILABLE:
        try:
            counter.labels(**labels).inc()
        except:
            pass


def set_gauge(gauge: Gauge, value: float, **labels):
    """Safely set a gauge value"""
    if PROMETHEUS_AVAILABLE:
        try:
            gauge.labels(**labels).set(value)
        except:
            pass


class MetricsCollector:
    """Collect and expose metrics"""
    
    @staticmethod
    def get_metrics() -> str:
        """Get Prometheus metrics in text format"""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus not available"
        
        return generate_latest()
    
    @staticmethod
    def record_event_action(user_id: str, action: str):
        """Record event CRUD action"""
        if action == "create":
            increment_counter(events_created_total, user_id=user_id)
        elif action == "update":
            increment_counter(events_updated_total, user_id=user_id)
        elif action == "delete":
            increment_counter(events_deleted_total, user_id=user_id)
    
    @staticmethod
    def record_cache_hit():
        """Record cache hit"""
        increment_counter(cache_hits_total)
    
    @staticmethod
    def record_cache_miss():
        """Record cache miss"""
        increment_counter(cache_misses_total)
    
    @staticmethod
    def record_agent_query(user_id: str, intent: str):
        """Record agent query"""
        increment_counter(agent_queries_total, user_id=user_id, intent=intent)
    
    @staticmethod
    def record_tool_call(tool_name: str, success: bool):
        """Record tool call"""
        increment_counter(
            agent_tool_calls_total,
            tool_name=tool_name,
            success=str(success).lower()
        )