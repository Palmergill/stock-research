"""
Monitoring and Performance Tracking
- API response time tracking
- Performance metrics collection
- Integration with logging
"""
import time
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

from .config import Config, get_logger

logger = get_logger()


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    path: str
    method: str
    duration_ms: float
    status_code: int
    timestamp: float = field(default_factory=time.time)


class PerformanceMonitor:
    """Track API performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._requests: List[RequestMetrics] = []
        self._endpoint_stats: Dict[str, Dict] = defaultdict(lambda: {
            "count": 0,
            "total_ms": 0.0,
            "min_ms": float('inf'),
            "max_ms": 0.0,
            "durations": []
        })
    
    def record_request(self, path: str, method: str, duration_ms: float, status_code: int) -> None:
        """Record a request's performance metrics"""
        metrics = RequestMetrics(
            path=path,
            method=method,
            duration_ms=duration_ms,
            status_code=status_code
        )
        
        # Add to history
        self._requests.append(metrics)
        if len(self._requests) > self.max_history:
            self._requests.pop(0)
        
        # Update endpoint stats
        key = f"{method} {path}"
        stats = self._endpoint_stats[key]
        stats["count"] += 1
        stats["total_ms"] += duration_ms
        stats["min_ms"] = min(stats["min_ms"], duration_ms)
        stats["max_ms"] = max(stats["max_ms"], duration_ms)
        stats["durations"].append(duration_ms)
        
        # Keep only last 100 durations for memory efficiency
        if len(stats["durations"]) > 100:
            stats["durations"] = stats["durations"][-100:]
        
        # Log slow requests
        if duration_ms > Config.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                f"Slow request detected: {method} {path} took {duration_ms:.2f}ms "
                f"(status={status_code})",
                extra={
                    "path": path,
                    "method": method,
                    "duration_ms": duration_ms,
                    "status_code": status_code,
                    "slow_request": True
                }
            )
    
    def get_stats(self) -> Dict:
        """Get aggregated performance statistics"""
        if not self._requests:
            return {"message": "No requests recorded yet"}
        
        # Calculate overall stats
        durations = [r.duration_ms for r in self._requests]
        
        stats = {
            "total_requests": len(self._requests),
            "avg_response_ms": statistics.mean(durations),
            "median_response_ms": statistics.median(durations),
            "p95_response_ms": self._percentile(durations, 95),
            "p99_response_ms": self._percentile(durations, 99),
            "min_response_ms": min(durations),
            "max_response_ms": max(durations),
            "slow_requests": sum(1 for d in durations if d > Config.SLOW_REQUEST_THRESHOLD_MS),
            "endpoints": {}
        }
        
        # Per-endpoint stats
        for key, endpoint_stats in self._endpoint_stats.items():
            count = endpoint_stats["count"]
            if count > 0:
                durations_list = endpoint_stats["durations"]
                stats["endpoints"][key] = {
                    "count": count,
                    "avg_ms": endpoint_stats["total_ms"] / count,
                    "min_ms": endpoint_stats["min_ms"],
                    "max_ms": endpoint_stats["max_ms"],
                    "p95_ms": self._percentile(durations_list, 95) if durations_list else 0
                }
        
        return stats
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile from a list of values"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100.0))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def reset(self) -> None:
        """Reset all metrics"""
        self._requests.clear()
        self._endpoint_stats.clear()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


async def performance_middleware(request, call_next: Callable):
    """FastAPI middleware to track request performance"""
    if not Config.ENABLE_PERFORMANCE_MONITORING:
        return await call_next(request)
    
    start_time = time.perf_counter()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        # Record failed request
        duration_ms = (time.perf_counter() - start_time) * 1000
        performance_monitor.record_request(
            path=request.url.path,
            method=request.method,
            duration_ms=duration_ms,
            status_code=500
        )
        raise
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Skip health checks from monitoring to reduce noise
    if not request.url.path.endswith("/health"):
        performance_monitor.record_request(
            path=request.url.path,
            method=request.method,
            duration_ms=duration_ms,
            status_code=status_code
        )
    
    # Add performance headers
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
    
    return response
