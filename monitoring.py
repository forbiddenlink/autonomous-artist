"""
OpenTelemetry Monitoring Setup for Autonomous Artist
Provides observability through metrics, traces, and logs
"""

import os
import logging
from functools import wraps
from time import time
from typing import Callable, Any

# Optional OpenTelemetry imports (install with: pip install opentelemetry-api opentelemetry-sdk)
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logging.warning("OpenTelemetry not installed. Run: pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-flask")


class MonitoringManager:
    """Centralized monitoring and observability management"""
    
    def __init__(self, app_name: str = "autonomous-artist", version: str = "1.0.0"):
        self.app_name = app_name
        self.version = version
        self.enabled = OTEL_AVAILABLE and os.getenv('MONITORING_ENABLED', 'false').lower() == 'true'
        
        # Metrics storage for basic monitoring when OpenTelemetry isn't available
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'paintings_generated': 0,
            'api_latency_sum': 0.0,
            'api_calls_total': 0,
        }
        
        if self.enabled:
            self._setup_telemetry()
        else:
            logging.info(f"Monitoring: Using basic metrics (OpenTelemetry {'not available' if not OTEL_AVAILABLE else 'disabled'})")
    
    def _setup_telemetry(self):
        """Configure OpenTelemetry providers"""
        resource = Resource.create({
            "service.name": self.app_name,
            "service.version": self.version,
        })
        
        # Tracing setup
        tracer_provider = TracerProvider(resource=resource)
        otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'localhost:4317')
        span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(tracer_provider)
        
        # Metrics setup
        meter_provider = MeterProvider(resource=resource)
        metrics.set_meter_provider(meter_provider)
        
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # Create custom metrics
        self.request_counter = self.meter.create_counter(
            "http_requests_total",
            description="Total HTTP requests",
        )
        self.painting_counter = self.meter.create_counter(
            "paintings_generated_total",
            description="Total paintings generated",
        )
        self.api_latency = self.meter.create_histogram(
            "api_latency_seconds",
            description="API call latency in seconds",
        )
        
        logging.info(f"OpenTelemetry monitoring enabled - exporting to {otlp_endpoint}")
    
    def instrument_flask(self, app):
        """Instrument Flask application for automatic tracing"""
        if self.enabled and OTEL_AVAILABLE:
            FlaskInstrumentor().instrument_app(app)
            RequestsInstrumentor().instrument()
            logging.info("Flask application instrumented for tracing")
    
    def track_request(self, endpoint: str, status_code: int, duration: float):
        """Track HTTP request metrics"""
        self.metrics['requests_total'] += 1
        if 200 <= status_code < 400:
            self.metrics['requests_success'] += 1
        else:
            self.metrics['requests_error'] += 1
        
        if self.enabled:
            self.request_counter.add(
                1,
                {"endpoint": endpoint, "status": str(status_code)}
            )
    
    def track_painting(self, success: bool = True):
        """Track painting generation"""
        if success:
            self.metrics['paintings_generated'] += 1
            if self.enabled:
                self.painting_counter.add(1, {"success": "true"})
    
    def track_api_call(self, api_name: str, duration: float, success: bool = True):
        """Track external API call metrics"""
        self.metrics['api_calls_total'] += 1
        self.metrics['api_latency_sum'] += duration
        
        if self.enabled:
            self.api_latency.record(
                duration,
                {"api": api_name, "success": str(success).lower()}
            )
    
    def get_metrics(self) -> dict:
        """Get current metrics snapshot"""
        avg_latency = 0.0
        if self.metrics['api_calls_total'] > 0:
            avg_latency = self.metrics['api_latency_sum'] / self.metrics['api_calls_total']
        
        return {
            "requests": {
                "total": self.metrics['requests_total'],
                "success": self.metrics['requests_success'],
                "error": self.metrics['requests_error'],
            },
            "paintings": {
                "generated": self.metrics['paintings_generated'],
            },
            "api_calls": {
                "total": self.metrics['api_calls_total'],
                "avg_latency_ms": round(avg_latency * 1000, 2),
            }
        }


# Decorator for tracing functions
def trace_function(name: str = None):
    """Decorator to trace function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            span_name = name or func.__name__
            
            # If OpenTelemetry is available and enabled, use it
            if OTEL_AVAILABLE and os.getenv('MONITORING_ENABLED', 'false').lower() == 'true':
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span(span_name):
                    return func(*args, **kwargs)
            else:
                # Otherwise just call the function
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Decorator for timing functions
def time_function(func: Callable) -> Callable:
    """Decorator to time function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time()
        try:
            result = func(*args, **kwargs)
            duration = time() - start
            logging.debug(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time() - start
            logging.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise
    
    return wrapper


# Global monitoring instance
monitoring = MonitoringManager()


if __name__ == "__main__":
    # Test monitoring setup
    print("Monitoring Manager Test")
    print(f"OpenTelemetry Available: {OTEL_AVAILABLE}")
    print(f"Monitoring Enabled: {monitoring.enabled}")
    print(f"\nCurrent Metrics: {monitoring.get_metrics()}")
