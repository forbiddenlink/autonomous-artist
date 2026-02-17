from flask import (
    Flask, render_template, jsonify, request,
    Response, send_file, send_from_directory
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_talisman import Talisman
from typing import Dict, Any, Tuple
from autonomous_artist import AutonomousArtist
import json
import requests
import os
import time
import logging
import zipfile
import io
from pathlib import Path
from dotenv import load_dotenv
from config import Config
from utils import (
    generate_image_api, analyze_image_api,
    post_to_facebook_api, upload_to_imgur
)
from cache_manager import get_cache_manager
from monitoring import monitoring, trace_function, time_function

logger = logging.getLogger("autonomous_artist")

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Security: Rate limiting to prevent DoS attacks
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    headers_enabled=True  # Enable rate limit headers
)

# Add rate limit headers to all responses
@app.after_request
def add_rate_limit_headers(response: Response) -> Response:
    """Add standard rate limit headers to responses"""
    # Headers are automatically added by flask-limiter when headers_enabled=True
    # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
    return response

# Security: CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Security: Security headers (only in production)
if not Config.DEBUG:
    csp = {
        'default-src': ["'self'"],
        'img-src': ["'self'", 'data:', 'https:'],
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'"]
    }
    Talisman(
        app,
        force_https=False,  # Set to True in production with HTTPS
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src']
    )

artist = AutonomousArtist(name=Config.DEFAULT_ARTIST_NAME)

# Initialize monitoring if enabled
monitoring.instrument_flask(app)

# Ensure static/generations exists
Config.create_directories()

def normalize_image_url(image_url: str) -> str:
    """Convert absolute file paths to web-relative URLs"""
    if not image_url or image_url.startswith('http'):
        return image_url
    
    # If it's already a web path, return as-is
    if image_url.startswith('/static/'):
        return image_url
    
    # Check if it's an absolute file path
    if image_url.startswith('/') or '\\' in image_url or image_url.startswith('static'):
        # Extract just the filename
        filename = Path(image_url).name
        return f'/static/generations/{filename}'
    
    # If it's just a filename
    if not image_url.startswith('/'):
        return f'/static/generations/{image_url}'
    
    return image_url


# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    """Custom rate limit error handler"""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please try again later.",
        "retry_after": getattr(e, 'description', 'Please wait before retrying')
    }), 429


@app.errorhandler(500)
def internal_error_handler(e):
    """Custom internal error handler"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again later."
    }), 500


# Routes
@app.route('/health')
@limiter.limit("30 per minute")
def health_check() -> Tuple[Response, int]:
    """Health check endpoint for monitoring"""
    try:
        cache_manager = get_cache_manager()
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "artist": {
                "name": artist.name,
                "mood": artist.mood,
                "painting_count": artist.painting_count
            },
            "config": Config.get_summary(),
            "cache": cache_manager.get_cache_stats() if cache_manager else {}
        }
        return jsonify(health_status), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route('/metrics')
@limiter.limit("60 per minute")
def metrics_endpoint() -> Tuple[Response, int]:
    """Prometheus-compatible metrics endpoint"""
    try:
        metrics_data = monitoring.get_metrics()
        return jsonify(metrics_data), 200
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cache/stats')
def get_cache_stats() -> Tuple[Response, int]:
    """Get cache statistics"""
    try:
        cache_manager = get_cache_manager()
        if cache_manager:
            stats = cache_manager.get_cache_stats()
            return jsonify(stats), 200
        return jsonify({"error": "Cache not available"}), 503
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache() -> Tuple[Response, int]:
    """Clear expired cache entries"""
    try:
        cache_manager = get_cache_manager()
        if cache_manager:
            cleared = cache_manager.clear_expired()
            return jsonify({"success": True, "cleared": cleared}), 200
        return jsonify({"error": "Cache not available"}), 503
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """Main gallery page"""
    return render_template('index.html')

@app.route('/api/state')
def get_state() -> Tuple[Response, int]:
    """Get artist's current state"""
    try:
        return jsonify(artist.get_current_state()), 200
    except Exception as e:
        logger.error(f"Error getting state: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/statement')
def get_statement() -> Tuple[Response, int]:
    """Get artist's statement"""
    try:
        return jsonify({
            "statement": artist.get_artist_statement()
        }), 200
    except Exception as e:
        logger.error(f"Error getting statement: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/paint', methods=['POST'])
@limiter.limit("10 per hour")  # Strict limit for expensive AI generation
def paint() -> Tuple[Response, int]:
    """Let the artist create a new painting with critique"""
    try:
        # Input validation
        data = request.get_json() or {}
        
        # Validate use_critique parameter
        use_critique = data.get('use_critique', True)
        if not isinstance(use_critique, bool):
            return jsonify({
                "error": "use_critique must be a boolean",
                "success": False
            }), 400
        
        # Generate concept with or without critique
        if use_critique:
            painting_data, critique_history = artist.create_with_critique(max_iterations=2)
        else:
            painting_data = artist.generate_prompt()
            critique_history = []
        
        # Generate the actual image
        image_result = generate_image_api(painting_data["prompt"])
        
        image_url = "placeholder.jpg"
        public_url = None
        visual_description = None
        from_cache = image_result.get("from_cache", False)
        
        if image_result["success"]:
            image_url = image_result["image_url"]  # Keep absolute path for internal use
            web_url = image_result.get("web_url", image_url)  # Use web_url for frontend
            
            # Upload to Imgur for public sharing
            imgur_result = upload_to_imgur(image_result["image_url"])
            if imgur_result["success"]:
                public_url = imgur_result["url"]
            
            # Vision Analysis
            visual_description = analyze_image_api(image_result["image_url"], prompt_context=painting_data["prompt"])
        else:
            web_url = "placeholder.jpg"
        
        # Record the painting (use absolute path for storage)
        record = artist.record_painting(painting_data, image_url, visual_description)
        
        # Add public URL to record for sharing
        if public_url:
            record["public_url"] = public_url
        
        # Extract thinking narrative
        thinking = painting_data.get('thinking', {})
        
        result = {
            "painting_data": painting_data,
            "subject": painting_data["subject"],
            "style": painting_data["style"],
            "prompt": painting_data["prompt"],
            "reflection": record["reflection"],
            "thinking": thinking.get('narrative', ''),
            "critique_history": critique_history,
            "state": artist.get_current_state(),
            "image_url": web_url,  # Use web_url for frontend display
            "public_url": public_url,
            "visual_description": visual_description,
            "success": image_result["success"],
            "from_cache": from_cache,
            "number": record.get("number", 0)
        }
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error in paint endpoint: {e}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/latest')
def get_latest() -> Tuple[Response, int]:
    """Get latest painting and current state"""
    try:
        latest_painting = None
        if artist.portfolio:
            latest_painting = artist.portfolio[-1].copy()
            # Normalize image URL for latest painting
            if latest_painting and 'image_url' in latest_painting:
                latest_painting['image_url'] = normalize_image_url(latest_painting['image_url'])
            
        state = artist.get_current_state()
        
        # Normalize image URLs in portfolio before sending to frontend
        normalized_portfolio = []
        for painting in artist.portfolio:
            p = painting.copy()
            if 'image_url' in p:
                p['image_url'] = normalize_image_url(p['image_url'])
            normalized_portfolio.append(p)
        
        state['portfolio'] = normalized_portfolio
            
        return jsonify({
            "state": state,
            "latest_painting": latest_painting,
            "painting_count": artist.painting_count
        }), 200
    except Exception as e:
        logger.error(f"Error getting latest: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio')
def get_portfolio() -> Tuple[Response, int]:
    """Get artist's complete portfolio"""
    try:
        return jsonify({
            "count": len(artist.portfolio),
            "paintings": artist.portfolio[-20:]  # Last 20 paintings
        }), 200
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/evolve', methods=['POST'])
def evolve() -> Tuple[Response, int]:
    """Force state evolution"""
    try:
        artist.evolve_state()
        return jsonify({
            "success": True,
            "new_state": artist.get_current_state()
        }), 200
    except Exception as e:
        logger.error(f"Error evolving state: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/share_latest', methods=['POST'])
def share_latest() -> Tuple[Response, int]:
    """Share the latest painting to Facebook"""
    try:
        if not artist.portfolio:
            return jsonify({"success": False, "error": "No paintings to share."}), 400
            
        latest = artist.portfolio[-1]
        
        # Construct caption
        caption = f"{latest['journal']}\n\nMood: {latest['mood'].upper() if 'mood' in latest else 'UNKNOWN'}"
        if 'image_url' in latest:
            result = post_to_facebook_api(latest['image_url'], caption)
            return jsonify(result), 200 if result.get("success") else 500
            
        return jsonify({"success": False, "error": "Latest painting has no image."}), 400
    except Exception as e:
        logger.error(f"Error sharing to Facebook: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download/<int:painting_number>')
def download_painting(painting_number: int) -> Tuple[Response, int]:
    """Download a specific painting"""
    try:
        # Find the painting
        painting = next((p for p in artist.portfolio if p.get('number') == painting_number), None)
        if not painting:
            return jsonify({"error": "Painting not found"}), 404
        
        image_path = Path(painting.get('image_url', ''))
        if not image_path.exists():
            return jsonify({"error": "Image file not found"}), 404
        
        # Send file with a nice filename
        filename = f"aria_painting_{painting_number}_{painting.get('subject', 'artwork')}.jpg"
        return send_file(
            image_path,
            as_attachment=True,
            download_name=filename,
            mimetype='image/jpeg'
        ), 200
    except Exception as e:
        logger.error(f"Error downloading painting: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/portfolio')
def download_portfolio() -> Tuple[Response, int]:
    """Download entire portfolio as a zip file"""
    try:
        if not artist.portfolio:
            return jsonify({"error": "No paintings in portfolio"}), 404
        
        # Create zip file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add each painting
            for painting in artist.portfolio:
                image_path = Path(painting.get('image_url', ''))
                if image_path.exists():
                    filename = f"painting_{painting.get('number', 0):03d}_{painting.get('subject', 'artwork')}.jpg"
                    zf.write(image_path, filename)
            
            # Add metadata JSON
            metadata = json.dumps([
                {
                    "number": p.get('number'),
                    "subject": p.get('subject'),
                    "style": p.get('style'),
                    "mood": p.get('mood'),
                    "prompt": p.get('prompt'),
                    "reflection": p.get('reflection'),
                    "timestamp": p.get('timestamp')
                }
                for p in artist.portfolio
            ], indent=2)
            zf.writestr('portfolio_metadata.json', metadata)
        
        memory_file.seek(0)
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=f'aria_portfolio_{time.strftime("%Y%m%d")}.zip',
            mimetype='application/zip'
        ), 200
    except Exception as e:
        logger.error(f"Error creating portfolio zip: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/json')
def export_json() -> Tuple[Response, int]:
    """Export artist state and portfolio as JSON"""
    try:
        export_data = {
            "artist": {
                "name": artist.name,
                "state": artist.get_current_state()
            },
            "portfolio": artist.portfolio,
            "exported_at": time.time()
        }
        
        return jsonify(export_data), 200
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting {Config.APP_NAME} v{Config.APP_VERSION}")
    logger.info(f"Artist: {artist.name}")
    Config.validate()
    app.run(debug=Config.DEBUG, port=Config.PORT, host=Config.HOST)
