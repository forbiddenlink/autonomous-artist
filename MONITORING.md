# Monitoring & Observability Guide

## Comprehensive Monitoring Setup for Autonomous Artist

This guide covers setting up comprehensive monitoring, logging, and observability for your production deployment.

---

## Table of Contents
1. [Monitoring Stack Overview](#monitoring-stack-overview)
2. [Application Metrics](#application-metrics)
3. [Structured Logging](#structured-logging)
4. [Alerting](#alerting)
5. [Health Checks](#health-checks)
6. [Performance Metrics](#performance-metrics)
7. [Error Tracking](#error-tracking)
8. [Dashboard Setup](#dashboard-setup)

---

## Monitoring Stack Overview

### Recommended Stack (Open Source)

1. **Prometheus** - Metrics collection
2. **Grafana** - Visualization and dashboards
3. **Loki** - Log aggregation
4. **Alertmanager** - Alert routing and management

### Alternative: Managed Services

- **Datadog** - All-in-one APM solution
- **New Relic** - Application performance monitoring
- **Sentry** - Error tracking and monitoring
- **CloudWatch** - AWS native monitoring

---

## Application Metrics

### 1. Install Prometheus Exporter

```bash
# requirements.txt
prometheus-flask-exporter>=0.23.0
```

```python
# app.py - Add at the top after app creation
from prometheus_flask_exporter import PrometheusMetrics

# Initialize metrics
metrics = PrometheusMetrics(app)

# Default metrics provided:
# - flask_http_request_duration_seconds
# - flask_http_request_total
# - flask_http_request_exceptions_total

# Custom metrics
from prometheus_client import Counter, Histogram, Gauge

# Painting generation metrics
paintings_generated = Counter(
    'paintings_generated_total',
    'Total number of paintings generated',
    ['style', 'subject']
)

painting_generation_time = Histogram(
    'painting_generation_seconds',
    'Time spent generating paintings',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

artist_energy = Gauge(
    'artist_energy_level',
    'Current energy level of the artist'
)

# HuggingFace API metrics
hf_api_calls = Counter(
    'hf_api_calls_total',
    'Total HuggingFace API calls',
    ['endpoint', 'status']
)

hf_api_duration = Histogram(
    'hf_api_duration_seconds',
    'HuggingFace API call duration',
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120]
)

# Cache metrics
cache_hits = Counter('cache_hits_total', 'Total cache hits', ['cache_type'])
cache_misses = Counter('cache_misses_total', 'Total cache misses', ['cache_type'])
cache_size = Gauge('cache_size_bytes', 'Current cache size in bytes')

# Usage in endpoints
@app.route('/api/paint', methods=['POST'])
@limiter.limit("10 per hour")
def paint():
    start_time = time.time()
    
    try:
        result = artist.paint()
        
        # Record metrics
        paintings_generated.labels(
            style=result['style'],
            subject=result['subject']
        ).inc()
        
        duration = time.time() - start_time
        painting_generation_time.observe(duration)
        
        artist_energy.set(artist.state['energy'])
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Paint error: {e}")
        hf_api_calls.labels(endpoint='generate', status='error').inc()
        raise
```

### 2. Prometheus Configuration

```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'autonomous-artist'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

---

## Structured Logging

### 1. JSON Logging Setup

```bash
# requirements.txt
python-json-logger>=2.0.7
```

```python
# logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_structured_logging():
    """Configure structured JSON logging"""
    
    # Create formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler('logs/app.json')
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger

# app.py
from logging_config import setup_structured_logging
logger = setup_structured_logging()

# Usage with structured fields
logger.info(
    "Painting generated",
    extra={
        "painting_id": painting_id,
        "style": style,
        "subject": subject,
        "generation_time": duration,
        "cache_hit": from_cache,
        "artist_mood": artist.mood,
        "user_ip": request.remote_addr
    }
)
```

### 2. Request Logging Middleware

```python
# app.py
import uuid
from flask import g

@app.before_request
def before_request_logging():
    """Add request ID and log incoming requests"""
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()
    
    logger.info(
        "Request started",
        extra={
            "request_id": g.request_id,
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.user_agent.string
        }
    )

@app.after_request
def after_request_logging(response):
    """Log request completion"""
    duration = time.time() - g.get('start_time', time.time())
    
    logger.info(
        "Request completed",
        extra={
            "request_id": g.request_id,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_seconds": duration
        }
    )
    
    # Add request ID to response headers
    response.headers['X-Request-ID'] = g.request_id
    
    return response
```

---

## Alerting

### 1. Alertmanager Configuration

```yaml
# /etc/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'email-notifications'

receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'ops@yourdomain.com'
        from: 'alertmanager@yourdomain.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

### 2. Alert Rules

```yaml
# /etc/prometheus/rules/autonomous-artist.yml
groups:
  - name: autonomous_artist_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(flask_http_request_exceptions_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      # Service down
      - alert: ServiceDown
        expr: up{job="autonomous-artist"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Autonomous Artist service is down"
          description: "Service has been down for > 1 minute"
      
      # High response time
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"
      
      # High memory usage
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes > 1e9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanize }}B"
      
      # HuggingFace API errors
      - alert: HuggingFaceAPIErrors
        expr: rate(hf_api_calls_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High HuggingFace API error rate"
          description: "Error rate is {{ $value }} errors/sec"
      
      # Low cache hit rate
      - alert: LowCacheHitRate
        expr: rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"
```

---

## Health Checks

### 1. Enhanced Health Check

```python
# app.py
@app.route('/health')
@limiter.limit("30 per minute")
def health_check():
    """Comprehensive health check"""
    start_time = time.time()
    health_status = {"status": "healthy", "checks": {}}
    overall_healthy = True
    
    # Check artist initialization
    try:
        _ = artist.mood
        health_status["checks"]["artist"] = {"status": "up"}
    except Exception as e:
        health_status["checks"]["artist"] = {
            "status": "down",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check cache
    try:
        cache_mgr = get_cache_manager()
        cache_stats = cache_mgr.get_cache_stats()
        health_status["checks"]["cache"] = {
            "status": "up",
            "stats": cache_stats
        }
    except Exception as e:
        health_status["checks"]["cache"] = {
            "status": "down",
            "error": str(e)
        }
        # Cache failure is not critical
    
    # Check memory file
    try:
        if Path(Config.MEMORY_FILE).exists():
            health_status["checks"]["memory_file"] = {"status": "up"}
        else:
            health_status["checks"]["memory_file"] = {
                "status": "warning",
                "message": "Memory file not found"
            }
    except Exception as e:
        health_status["checks"]["memory_file"] = {
            "status": "down",
            "error": str(e)
        }
    
    # Check disk space
    try:
        import shutil
        disk = shutil.disk_usage(Config.GENERATIONS_DIR)
        disk_free_percent = (disk.free / disk.total) * 100
        
        if disk_free_percent < 10:
            health_status["checks"]["disk"] = {
                "status": "critical",
                "free_percent": disk_free_percent
            }
            overall_healthy = False
        elif disk_free_percent < 20:
            health_status["checks"]["disk"] = {
                "status": "warning",
                "free_percent": disk_free_percent
            }
        else:
            health_status["checks"]["disk"] = {
                "status": "up",
                "free_percent": disk_free_percent
            }
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Overall status
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    health_status["duration_ms"] = (time.time() - start_time) * 1000
    health_status["timestamp"] = time.time()
    
    status_code = 200 if overall_healthy else 503
    return jsonify(health_status), status_code

# Readiness probe (simpler, for load balancer)
@app.route('/ready')
def readiness_check():
    """Simple readiness check for load balancers"""
    try:
        _ = artist.mood
        return jsonify({"status": "ready"}), 200
    except:
        return jsonify({"status": "not ready"}), 503

# Liveness probe (even simpler)
@app.route('/alive')
def liveness_check():
    """Simple liveness check"""
    return jsonify({"status": "alive"}), 200
```

---

## Dashboard Setup

### 1. Grafana Dashboard JSON

Create a dashboard with these panels:

**Request Rate Panel**:
```promql
rate(flask_http_request_total[5m])
```

**Response Time (95th percentile)**:
```promql
histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))
```

**Error Rate**:
```promql
rate(flask_http_request_exceptions_total[5m])
```

**Paintings Generated**:
```promql
rate(paintings_generated_total[1h])
```

**Cache Hit Rate**:
```promql
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

### 2. Quick Monitoring Script

```bash
#!/bin/bash
# monitor_app.sh - Simple monitoring script

API_URL="http://localhost:8000"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Check health
HEALTH=$(curl -sf "${API_URL}/health" | jq -r '.status')

if [ "$HEALTH" != "healthy" ]; then
    # Send alert
    curl -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"⚠️ Autonomous Artist health check failed: $HEALTH\"}"
fi

# Check metrics
METRICS=$(curl -sf "${API_URL}/metrics")
ERROR_RATE=$(echo "$METRICS" | grep flask_http_request_exceptions_total | tail -1 | awk '{print $2}')

if (( $(echo "$ERROR_RATE > 10" | bc -l) )); then
    curl -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"⚠️ High error rate detected: $ERROR_RATE errors\"}"
fi
```

---

## Error Tracking with Sentry

### 1. Install Sentry

```bash
# requirements.txt
sentry-sdk[flask]>=2.0.0
```

```python
# app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Initialize Sentry
if not Config.DEBUG and os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,  # 10% of requests
        profiles_sample_rate=0.1,
        environment=os.getenv('ENVIRONMENT', 'production')
    )

# Automatic error tracking - Sentry captures all uncaught exceptions

# Manual error capture
from sentry_sdk import capture_exception, capture_message

try:
    result = generate_image_api(prompt)
except Exception as e:
    capture_exception(e)
    # Add extra context
    sentry_sdk.set_context("painting", {
        "prompt": prompt,
        "style": style,
        "subject": subject
    })
    raise
```

---

## Quick Monitoring Checklist

### Daily Checks
- [ ] Check Grafana dashboards for anomalies
- [ ] Review error logs
- [ ] Check disk space usage
- [ ] Verify backup completion

### Weekly Checks
- [ ] Review performance trends
- [ ] Analyze cache hit rates
- [ ] Check for memory leaks
- [ ] Review security logs

### Monthly Checks
- [ ] Update dependencies
- [ ] Review and tune alert thresholds
- [ ] Capacity planning review
- [ ] Security audit

---

## Useful Queries

### Prometheus Queries

```promql
# Request rate by endpoint
sum(rate(flask_http_request_total[5m])) by (path)

# Error percentage
100 * sum(rate(flask_http_request_exceptions_total[5m])) / sum(rate(flask_http_request_total[5m]))

# Average painting generation time
rate(painting_generation_seconds_sum[5m]) / rate(painting_generation_seconds_count[5m])

# Most popular styles
topk(5, sum(rate(paintings_generated_total[1h])) by (style))
```

### Log Queries (if using Loki)

```logql
# All errors
{job="autonomous-artist"} |= "ERROR"

# Slow requests (> 1 second)
{job="autonomous-artist"} | json | duration_seconds > 1

# HuggingFace API errors
{job="autonomous-artist"} | json | message =~ "HuggingFace.*error"
```

---

**Last Updated**: February 6, 2026
**Monitoring Guide Version**: 1.0.0
