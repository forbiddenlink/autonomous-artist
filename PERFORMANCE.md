# Performance Optimization Guide

## Optimizing Autonomous Artist for Production

This guide covers advanced performance optimization techniques for your Flask-based Autonomous Artist application.

---

## Table of Contents
1. [Application-Level Optimizations](#application-level-optimizations)
2. [External API Optimization](#external-api-optimization)
3. [Database & Caching](#database--caching)
4. [Connection Pooling](#connection-pooling)
5. [Async Processing](#async-processing)
6. [Monitoring & Profiling](#monitoring--profiling)
7. [Load Testing](#load-testing)

---

## Application-Level Optimizations

### 1. Enable Response Compression
Add gzip compression for JSON responses:

```python
# Add to requirements.txt
flask-compress>=1.14

# Add to app.py
from flask_compress import Compress

Compress(app)
```

Configure compression:
```python
app.config['COMPRESS_MIMETYPES'] = [
    'text/html', 'text/css', 'text/xml',
    'application/json', 'application/javascript'
]
app.config['COMPRESS_LEVEL'] = 6
app.config['COMPRESS_MIN_SIZE'] = 500
```

### 2. Implement Connection Pooling

For external API calls, use connection pooling:

```python
# utils.py - Add connection pooling
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create a session with connection pooling
def create_session():
    session = requests.Session()
    
    # Retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
        backoff_factor=1
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=20,
        pool_maxsize=20,
        pool_block=False
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Global session instance
http_session = create_session()
```

### 3. Optimize JSON Serialization

Use faster serialization libraries:

```python
# requirements.txt
orjson>=3.9.0

# config.py
import orjson

class Config:
    JSON_SORT_KEYS = False
    
    # Use orjson for faster JSON serialization
    @staticmethod
    def json_encoder(obj):
        return orjson.dumps(obj).decode()
```

---

## External API Optimization

### 1. Implement Circuit Breaker Pattern

Protect against cascading failures when external APIs are down:

```python
# utils.py
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
    
    def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = 'half_open'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'half_open':
                self.state = 'closed'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
            raise e

# Usage
hf_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def generate_image_with_circuit_breaker(prompt):
    return hf_circuit_breaker.call(generate_image_api, prompt)
```

### 2. Request Batching

If possible, batch multiple requests:

```python
def batch_generate_images(prompts, batch_size=5):
    results = []
    for i in range(0, len(prompts), batch_size):
        batch = prompts[i:i + batch_size]
        # Process batch concurrently or sequentially
        batch_results = [generate_image_api(p) for p in batch]
        results.extend(batch_results)
    return results
```

### 3. Timeout Management

Always set explicit timeouts:

```python
# config.py
API_TIMEOUT = 120  # seconds
API_CONNECT_TIMEOUT = 10  # seconds

# Usage in utils.py
response = http_session.get(
    url,
    timeout=(Config.API_CONNECT_TIMEOUT, Config.API_TIMEOUT)
)
```

---

## Database & Caching

### 1. Redis for Distributed Caching

Upgrade to Redis for better caching:

```python
# requirements.txt
redis>=5.0.0
flask-caching>=2.1.0

# config.py
CACHE_TYPE = "redis"
CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_DEFAULT_TIMEOUT = 86400  # 1 day

# app.py
from flask_caching import Cache

cache = Cache(app)

# Usage
@cache.cached(timeout=300, key_prefix='artist_state')
def get_cached_state():
    return artist.get_state()
```

### 2. Cache Warming

Pre-populate frequently accessed data:

```python
def warm_cache():
    """Warm up cache with frequently accessed data"""
    logger.info("Warming cache...")
    
    # Pre-cache artist state
    cache.set('artist_state', artist.get_state(), timeout=300)
    
    # Pre-cache common prompts
    common_subjects = ['nature', 'urban', 'abstract']
    for subject in common_subjects:
        # Pre-generate or cache metadata
        pass
    
    logger.info("Cache warming complete")

# Call on application startup
if __name__ == '__main__':
    warm_cache()
    app.run()
```

### 3. Cache Invalidation Strategy

```python
def invalidate_related_caches(painting_id):
    """Invalidate caches when data changes"""
    cache.delete('artist_state')
    cache.delete('latest_painting')
    cache.delete(f'painting_{painting_id}')
```

---

## Async Processing

### 1. Background Task Queue

For long-running tasks, use Celery:

```python
# requirements.txt
celery>=5.3.0
redis>=5.0.0

# celery_app.py
from celery import Celery

celery_app = Celery(
    'autonomous_artist',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
)

@celery_app.task(bind=True, max_retries=3)
def generate_painting_task(self, use_critique=True):
    try:
        result = artist.paint(use_critique=use_critique)
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

# app.py
@app.route('/api/paint/async', methods=['POST'])
@limiter.limit("20 per hour")
def paint_async():
    """Initiate async painting generation"""
    data = request.get_json() or {}
    use_critique = data.get('use_critique', True)
    
    task = generate_painting_task.delay(use_critique)
    
    return jsonify({
        "task_id": task.id,
        "status": "pending",
        "check_url": f"/api/paint/status/{task.id}"
    }), 202

@app.route('/api/paint/status/<task_id>')
def paint_status(task_id):
    """Check async task status"""
    task = generate_painting_task.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Pending...'}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'result': task.result}
    else:
        response = {'state': task.state, 'status': str(task.info)}
    
    return jsonify(response)
```

---

## Monitoring & Profiling

### 1. Application Performance Monitoring (APM)

Integrate with Prometheus:

```python
# requirements.txt
prometheus-flask-exporter>=0.22.0

# app.py
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)

# Custom metrics
painting_counter = metrics.counter(
    'paintings_generated_total',
    'Total number of paintings generated'
)

hf_api_duration = metrics.histogram(
    'hf_api_request_duration_seconds',
    'HuggingFace API request duration'
)

# Usage
@app.route('/api/paint', methods=['POST'])
def paint():
    with hf_api_duration.time():
        result = generate_image_api(prompt)
    painting_counter.inc()
    return jsonify(result)
```

### 2. Structured Logging

```python
# requirements.txt
python-json-logger>=2.0.7

# config.py
import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    return logger

logger = setup_logging()

# Usage
logger.info("Painting generated", extra={
    "painting_id": painting_id,
    "style": style,
    "generation_time": duration,
    "cache_hit": from_cache
})
```

### 3. Request Tracing

Add request IDs for tracing:

```python
import uuid

@app.before_request
def add_request_id():
    request.request_id = str(uuid.uuid4())
    g.request_id = request.request_id

@app.after_request
def add_request_id_header(response):
    response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
    return response

# Log with request ID
logger.info("API request", extra={
    "request_id": g.request_id,
    "endpoint": request.endpoint,
    "method": request.method
})
```

---

## Load Testing

### 1. Using Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class ArtistUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_state(self):
        self.client.get("/api/state")
    
    @task(2)
    def get_latest(self):
        self.client.get("/api/latest")
    
    @task(1)
    def generate_painting(self):
        self.client.post("/api/paint", json={"use_critique": True})
    
    @task(5)
    def health_check(self):
        self.client.get("/health")

# Run with:
# locust -f locustfile.py --host=http://localhost:5001
```

### 2. Using Apache Bench

```bash
# Test health endpoint
ab -n 1000 -c 10 http://localhost:5001/health

# Test API endpoint
ab -n 100 -c 5 -p paint_request.json -T application/json http://localhost:5001/api/paint
```

### 3. Continuous Load Testing

```bash
#!/bin/bash
# load_test.sh
echo "Running load tests..."

# Test health endpoint
echo "Testing /health..."
ab -n 1000 -c 10 http://localhost:5001/health > results/health_test.txt

# Test state endpoint  
echo "Testing /api/state..."
ab -n 500 -c 5 http://localhost:5001/api/state > results/state_test.txt

# Test paint endpoint (light load)
echo "Testing /api/paint..."
ab -n 10 -c 2 -p paint_request.json -T application/json \
   http://localhost:5001/api/paint > results/paint_test.txt

echo "Load tests complete. Check results/ directory."
```

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Good | Needs Improvement |
|--------|--------|------|-------------------|
| Health Check | < 50ms | < 100ms | > 100ms |
| API State | < 150ms | < 300ms | > 300ms |
| Generate (cached) | < 200ms | < 500ms | > 500ms |
| Generate (new) | 5-30s | < 60s | > 60s |
| Memory Usage | < 500MB | < 1GB | > 1GB |
| CPU Usage (idle) | < 5% | < 15% | > 15% |

### Monitoring Commands

```bash
# Monitor CPU and memory
htop

# Monitor network
iftop

# Monitor disk I/O
iotop

# Monitor application logs
tail -f logs/artist_$(date +%Y%m%d).log

# Monitor Gunicorn processes
ps aux | grep gunicorn

# Check connection count
netstat -an | grep :8000 | wc -l
```

---

## Optimization Checklist

- [ ] Gzip compression enabled
- [ ] Connection pooling implemented
- [ ] Redis caching configured
- [ ] Circuit breaker for external APIs
- [ ] Celery for async tasks (optional)
- [ ] Prometheus metrics exported
- [ ] Structured logging enabled
- [ ] Request tracing implemented
- [ ] Load testing performed
- [ ] Performance benchmarks met
- [ ] Database queries optimized (if applicable)
- [ ] Static file CDN configured (optional)
- [ ] HTTP/2 enabled in Nginx
- [ ] Worker count optimized
- [ ] Memory leaks tested

---

## Next Level Optimizations

### 1. CDN for Static Assets
- Use CloudFlare, AWS CloudFront, or similar
- Serve generated images from S3 + CloudFront
- Reduces origin server load

### 2. Horizontal Scaling
- Multiple application servers behind load balancer
- Shared Redis for rate limiting and caching
- Shared file storage (S3, NFS)

### 3. Database Optimization
- If migrating from JSON to PostgreSQL:
  - Add appropriate indexes
  - Use connection pooling
  - Implement read replicas

### 4. Advanced Monitoring
- Set up Grafana dashboards
- Configure alerting rules
- Implement distributed tracing with Jaeger

---

**Last Updated**: February 6, 2026
**Performance Guide Version**: 1.0.0
