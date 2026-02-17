# API Documentation

## Base URL
- Development: `http://localhost:5001`
- Production: `https://your-domain.com`

## Authentication
Currently, the API is open for public use with rate limiting. For production, consider adding authentication.

---

## Endpoints

### 1. Health Check
Check if the application is running and get system status.

**Endpoint**: `GET /health`

**Rate Limit**: 30 requests/minute

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": 1704648000.0,
  "artist": {
    "name": "Aria",
    "mood": "contemplative",
    "painting_count": 42
  },
  "config": {
    "app_name": "Autonomous Artist",
    "version": "1.0.0",
    "cache_enabled": true
  },
  "cache": {
    "images": 15,
    "text": 30,
    "total_size_mb": 150.5
  }
}
```

---

### 2. Get Artist State
Retrieve the current state of the artist's mind.

**Endpoint**: `GET /api/state`

**Rate Limit**: 50 requests/hour

**Response** (200 OK):
```json
{
  "mood": "contemplative",
  "energy": 0.75,
  "complexity_tolerance": 0.6,
  "painting_count": 42,
  "personality": {
    "openness": 0.85,
    "conscientiousness": 0.65,
    "extraversion": 0.55,
    "agreeableness": 0.45,
    "neuroticism": 0.50
  },
  "style_affinities": {
    "impressionist": 0.75,
    "abstract_expressionism": 0.60,
    "surreal": 0.45
  },
  "subject_interests": {
    "nature": 0.80,
    "urban": 0.50,
    "cosmic": 0.65
  }
}
```

---

### 3. Generate Painting
Let the artist create a new painting.

**Endpoint**: `POST /api/paint`

**Rate Limit**: 10 requests/hour (strict due to AI generation costs)

**Request Body**:
```json
{
  "use_critique": true
}
```

**Parameters**:
- `use_critique` (boolean, optional, default: true): Whether to use the critic agent for iterative improvement

**Response** (200 OK):
```json
{
  "success": true,
  "painting_data": {
    "subject": "nature",
    "style": "impressionist",
    "prompt": "A serene impressionist painting featuring natural landscapes...",
    "colors": ["emerald", "sage"],
    "mood": "contemplative"
  },
  "subject": "nature",
  "style": "impressionist",
  "prompt": "Full generation prompt...",
  "reflection": "As I painted this piece, I felt...",
  "thinking": "My thought process narrative...",
  "critique_history": [
    {
      "iteration": 1,
      "critique": "Analysis of the prompt...",
      "suggestions": ["Enhance detail...", "Consider adding..."]
    }
  ],
  "state": {
    "mood": "contemplative",
    "energy": 0.72
  },
  "image_url": "/static/generations/painting_123.png",
  "public_url": "https://i.imgur.com/abc123.png",
  "visual_description": "The image shows a beautiful landscape...",
  "from_cache": false,
  "number": 43
}
```

**Response** (400 Bad Request):
```json
{
  "error": "use_critique must be a boolean",
  "success": false
}
```

**Response** (500 Internal Server Error):
```json
{
  "error": "Error message",
  "success": false
}
```

---

### 4. Get Latest Painting
Retrieve the most recent painting and current state.

**Endpoint**: `GET /api/latest`

**Rate Limit**: 50 requests/hour

**Response** (200 OK):
```json
{
  "latest_painting": {
    "number": 42,
    "subject": "urban",
    "style": "cyberpunk",
    "image_url": "/static/generations/painting_042.png",
    "prompt": "Full prompt...",
    "reflection": "Artist's reflection...",
    "satisfaction": 0.85,
    "timestamp": "2024-01-01T12:00:00",
    "visual_description": "Description of the image..."
  },
  "state": {
    "mood": "energized",
    "energy": 0.88,
    "painting_count": 42
  }
}
```

---

### 5. Get Artist Statement
Retrieve the artist's self-written statement about their work and philosophy.

**Endpoint**: `GET /api/statement`

**Rate Limit**: 50 requests/hour

**Response** (200 OK):
```json
{
  "statement": "As an artist, I seek to explore the boundaries between..."
}
```

---

### 6. Get Full Portfolio
Download all paintings and metadata.

**Endpoint**: `GET /api/portfolio/download`

**Rate Limit**: 10 requests/hour

**Response**: ZIP file containing:
- All generated images
- `portfolio.json` with metadata for all paintings

---

### 7. Cache Management

#### Get Cache Statistics
**Endpoint**: `GET /api/cache/stats`

**Rate Limit**: 50 requests/hour

**Response** (200 OK):
```json
{
  "images": 25,
  "text": 50,
  "metadata": 75,
  "total_size_mb": 250.5,
  "oldest_entry": "2024-01-01T10:00:00",
  "newest_entry": "2024-01-07T15:30:00"
}
```

#### Clear Expired Cache
**Endpoint**: `POST /api/cache/clear`

**Rate Limit**: 10 requests/hour

**Response** (200 OK):
```json
{
  "success": true,
  "cleared": 15
}
```

---

## Rate Limiting

All endpoints are rate-limited to prevent abuse. Rate limits are per IP address.

**Default Limits**:
- 200 requests per day
- 50 requests per hour

**Specific Limits**:
- `/api/paint`: 10 requests/hour (expensive AI generation)
- `/health`: 30 requests/minute (monitoring)
- `/api/portfolio/download`: 10 requests/hour (large download)

**Rate Limit Response** (429 Too Many Requests):
```json
{
  "error": "Rate limit exceeded. Try again in X seconds."
}
```

---

## CORS Policy

Cross-Origin requests are restricted by the `ALLOWED_ORIGINS` environment variable.

**Development**: Usually set to `*` (all origins)
**Production**: Set to specific domains (e.g., `https://yourdomain.com`)

---

## Error Handling

### Standard Error Response
```json
{
  "error": "Description of the error",
  "success": false
}
```

### HTTP Status Codes
- `200 OK`: Successful request
- `400 Bad Request`: Invalid input or parameters
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Caching

The application implements response caching to improve performance and reduce API costs:

- **Image generations**: Cached for 7 days
- **Text generations**: Cached for 1 hour

Identical prompts will return cached results when available.

---

## Best Practices

### 1. Use Critique Mode
For best results, use `use_critique: true` when calling `/api/paint`. This enables the critic agent to improve the prompt through multiple iterations.

### 2. Handle Rate Limits
Implement exponential backoff when you hit rate limits:
```python
import time
import requests

def call_api_with_retry(url, max_retries=3):
    for i in range(max_retries):
        response = requests.post(url)
        if response.status_code == 429:
            wait_time = 2 ** i  # Exponential backoff
            time.sleep(wait_time)
            continue
        return response
    return None
```

### 3. Check Health
Use the `/health` endpoint to monitor application status before making expensive calls.

### 4. Save Public URLs
When you get a painting, save both the local `image_url` and `public_url` (Imgur). The public URL is permanent and shareable.

### 5. Monitor Cache
Periodically check `/api/cache/stats` and clear old entries with `/api/cache/clear` to manage storage.

---

## Examples

### Python Example
```python
import requests

BASE_URL = "http://localhost:5001"

# Check health
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Generate a painting
response = requests.post(
    f"{BASE_URL}/api/paint",
    json={"use_critique": True}
)
painting = response.json()

if painting["success"]:
    print(f"Generated painting #{painting['number']}")
    print(f"Style: {painting['style']}")
    print(f"Image: {painting['image_url']}")
    print(f"Public URL: {painting['public_url']}")
```

### JavaScript Example
```javascript
const BASE_URL = "http://localhost:5001";

// Get artist state
fetch(`${BASE_URL}/api/state`)
  .then(response => response.json())
  .then(data => {
    console.log(`Artist mood: ${data.mood}`);
    console.log(`Energy level: ${data.energy}`);
  });

// Generate painting
fetch(`${BASE_URL}/api/paint`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ use_critique: true })
})
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log(`Created painting: ${data.image_url}`);
    }
  })
  .catch(error => console.error('Error:', error));
```

### cURL Example
```bash
# Check health
curl http://localhost:5001/health

# Get current state
curl http://localhost:5001/api/state

# Generate painting
curl -X POST http://localhost:5001/api/paint \
  -H "Content-Type: application/json" \
  -d '{"use_critique": true}'

# Get latest painting
curl http://localhost:5001/api/latest

# Download portfolio
curl -o portfolio.zip http://localhost:5001/api/portfolio/download
```

---

## Webhooks (Future Feature)

In future versions, you may be able to subscribe to webhooks for:
- New painting created
- Artist mood changed
- Memory milestone reached

---

## Support

For issues, questions, or feature requests:
- Check the main README.md
- Review SECURITY.md for security concerns
- See DEPLOYMENT.md for deployment help
