"""
Comprehensive monitoring and metrics collection for AI Prompt Toolkit.
"""

import time
from typing import Dict, Any, Optional, List
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
from contextlib import contextmanager

logger = structlog.get_logger(__name__)

# Prometheus metrics
REGISTRY = CollectorRegistry()

# Request metrics
REQUEST_COUNT = Counter(
    'ai_prompt_toolkit_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'ai_prompt_toolkit_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# Optimization metrics
OPTIMIZATION_COUNT = Counter(
    'ai_prompt_toolkit_optimizations_total',
    'Total number of optimizations',
    ['strategy', 'status'],
    registry=REGISTRY
)

OPTIMIZATION_DURATION = Histogram(
    'ai_prompt_toolkit_optimization_duration_seconds',
    'Optimization duration in seconds',
    ['strategy'],
    registry=REGISTRY
)

OPTIMIZATION_COST_REDUCTION = Histogram(
    'ai_prompt_toolkit_cost_reduction_ratio',
    'Cost reduction ratio achieved',
    ['strategy'],
    registry=REGISTRY
)

# LLM metrics
LLM_REQUEST_COUNT = Counter(
    'ai_prompt_toolkit_llm_requests_total',
    'Total LLM requests',
    ['provider', 'model', 'status'],
    registry=REGISTRY
)

LLM_REQUEST_DURATION = Histogram(
    'ai_prompt_toolkit_llm_request_duration_seconds',
    'LLM request duration',
    ['provider', 'model'],
    registry=REGISTRY
)

LLM_TOKEN_COUNT = Counter(
    'ai_prompt_toolkit_llm_tokens_total',
    'Total tokens processed',
    ['provider', 'model', 'type'],  # type: input/output
    registry=REGISTRY
)

LLM_COST = Counter(
    'ai_prompt_toolkit_llm_cost_total',
    'Total LLM costs',
    ['provider', 'model'],
    registry=REGISTRY
)

# Security metrics
SECURITY_SCAN_COUNT = Counter(
    'ai_prompt_toolkit_security_scans_total',
    'Total security scans',
    ['scan_type', 'result'],
    registry=REGISTRY
)

INJECTION_DETECTION_COUNT = Counter(
    'ai_prompt_toolkit_injection_detections_total',
    'Injection detections',
    ['threat_level', 'injection_type'],
    registry=REGISTRY
)

GUARDRAIL_VIOLATION_COUNT = Counter(
    'ai_prompt_toolkit_guardrail_violations_total',
    'Guardrail violations',
    ['rule_type', 'severity'],
    registry=REGISTRY
)

# System metrics
ACTIVE_CONNECTIONS = Gauge(
    'ai_prompt_toolkit_active_connections',
    'Number of active connections',
    registry=REGISTRY
)

CACHE_HIT_RATE = Gauge(
    'ai_prompt_toolkit_cache_hit_rate',
    'Cache hit rate',
    ['cache_type'],
    registry=REGISTRY
)

DATABASE_CONNECTIONS = Gauge(
    'ai_prompt_toolkit_database_connections',
    'Database connection pool size',
    ['pool_type'],
    registry=REGISTRY
)


@dataclass
class MetricEvent:
    """Represents a metric event."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Centralized metrics collection and reporting."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._events: List[MetricEvent] = []
        self._start_time = datetime.utcnow()
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        self._events.append(MetricEvent(
            name="http_request",
            value=duration,
            labels={"method": method, "endpoint": endpoint, "status": str(status_code)}
        ))
    
    def record_optimization(self, strategy: str, status: str, duration: float, cost_reduction: Optional[float] = None):
        """Record optimization metrics."""
        OPTIMIZATION_COUNT.labels(strategy=strategy, status=status).inc()
        OPTIMIZATION_DURATION.labels(strategy=strategy).observe(duration)
        
        if cost_reduction is not None:
            OPTIMIZATION_COST_REDUCTION.labels(strategy=strategy).observe(cost_reduction)
        
        self._events.append(MetricEvent(
            name="optimization",
            value=duration,
            labels={"strategy": strategy, "status": status},
            metadata={"cost_reduction": cost_reduction}
        ))
    
    def record_llm_request(self, provider: str, model: str, status: str, duration: float, 
                          input_tokens: int, output_tokens: int, cost: float):
        """Record LLM request metrics."""
        LLM_REQUEST_COUNT.labels(provider=provider, model=model, status=status).inc()
        LLM_REQUEST_DURATION.labels(provider=provider, model=model).observe(duration)
        LLM_TOKEN_COUNT.labels(provider=provider, model=model, type="input").inc(input_tokens)
        LLM_TOKEN_COUNT.labels(provider=provider, model=model, type="output").inc(output_tokens)
        LLM_COST.labels(provider=provider, model=model).inc(cost)
        
        self._events.append(MetricEvent(
            name="llm_request",
            value=duration,
            labels={"provider": provider, "model": model, "status": status},
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost
            }
        ))
    
    def record_security_scan(self, scan_type: str, result: str, threat_level: Optional[str] = None,
                           injection_type: Optional[str] = None, violations: Optional[List[Dict]] = None):
        """Record security scan metrics."""
        SECURITY_SCAN_COUNT.labels(scan_type=scan_type, result=result).inc()
        
        if threat_level and injection_type:
            INJECTION_DETECTION_COUNT.labels(threat_level=threat_level, injection_type=injection_type).inc()
        
        if violations:
            for violation in violations:
                rule_type = violation.get("rule_type", "unknown")
                severity = violation.get("severity", "unknown")
                GUARDRAIL_VIOLATION_COUNT.labels(rule_type=rule_type, severity=severity).inc()
        
        self._events.append(MetricEvent(
            name="security_scan",
            value=1.0,
            labels={"scan_type": scan_type, "result": result},
            metadata={
                "threat_level": threat_level,
                "injection_type": injection_type,
                "violations_count": len(violations) if violations else 0
            }
        ))
    
    def update_system_metrics(self, active_connections: int, cache_stats: Dict[str, float], 
                            db_connections: Dict[str, int]):
        """Update system-level metrics."""
        ACTIVE_CONNECTIONS.set(active_connections)
        
        for cache_type, hit_rate in cache_stats.items():
            CACHE_HIT_RATE.labels(cache_type=cache_type).set(hit_rate)
        
        for pool_type, count in db_connections.items():
            DATABASE_CONNECTIONS.labels(pool_type=pool_type).set(count)
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics."""
        return generate_latest(REGISTRY).decode('utf-8')
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        now = datetime.utcnow()
        uptime = (now - self._start_time).total_seconds()
        
        # Calculate event statistics
        event_counts = {}
        for event in self._events:
            event_counts[event.name] = event_counts.get(event.name, 0) + 1
        
        # Recent events (last hour)
        recent_events = [e for e in self._events if (now - e.timestamp).total_seconds() < 3600]
        
        return {
            "uptime_seconds": uptime,
            "total_events": len(self._events),
            "recent_events_1h": len(recent_events),
            "event_types": event_counts,
            "metrics_collected": {
                "requests": sum(1 for e in self._events if e.name == "http_request"),
                "optimizations": sum(1 for e in self._events if e.name == "optimization"),
                "llm_requests": sum(1 for e in self._events if e.name == "llm_request"),
                "security_scans": sum(1 for e in self._events if e.name == "security_scan")
            }
        }
    
    def get_recent_events(self, limit: int = 100) -> List[MetricEvent]:
        """Get recent metric events."""
        return sorted(self._events, key=lambda x: x.timestamp, reverse=True)[:limit]


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Decorators for automatic metrics collection
def track_request_metrics(endpoint: str):
    """Decorator to automatically track request metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = getattr(e, 'status_code', 500)
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_request("POST", endpoint, status_code, duration)
        
        return wrapper
    return decorator


def track_optimization_metrics(strategy: str):
    """Decorator to track optimization metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            cost_reduction = None
            
            try:
                result = await func(*args, **kwargs)
                if hasattr(result, 'results') and result.results:
                    cost_reduction = result.results.get('cost_reduction')
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_optimization(strategy, status, duration, cost_reduction)
        
        return wrapper
    return decorator


@contextmanager
def track_llm_request(provider: str, model: str):
    """Context manager to track LLM request metrics."""
    start_time = time.time()
    status = "success"
    input_tokens = 0
    output_tokens = 0
    cost = 0.0
    
    try:
        yield {
            'set_tokens': lambda inp, out: globals().update({'input_tokens': inp, 'output_tokens': out}),
            'set_cost': lambda c: globals().update({'cost': c})
        }
    except Exception as e:
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        metrics_collector.record_llm_request(provider, model, status, duration, input_tokens, output_tokens, cost)


def track_security_scan(scan_type: str):
    """Decorator to track security scan metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Extract metrics from result
                if isinstance(result, dict):
                    is_safe = result.get('is_injection', False) == False
                    threat_level = result.get('threat_level')
                    injection_type = result.get('injection_type')
                    violations = result.get('violations', [])
                else:
                    is_safe = getattr(result, 'is_safe', True)
                    violations = getattr(result, 'violations', [])
                    threat_level = None
                    injection_type = None
                
                scan_result = "safe" if is_safe else "unsafe"
                metrics_collector.record_security_scan(scan_type, scan_result, threat_level, injection_type, violations)
                
                return result
            except Exception as e:
                metrics_collector.record_security_scan(scan_type, "error")
                raise
        
        return wrapper
    return decorator
