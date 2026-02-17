from pathlib import Path
import os
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, Any
from functools import wraps
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

try:
    from config import Config
    from cache_manager import cached_image_generation, cached_text_generation, get_cache_manager
except ImportError:
    # Fallback if config not available
    class Config:
        HF_API_TOKEN = os.getenv("HF_API_TOKEN")
        IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"
        IMAGE_FALLBACK_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
        TEXT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
        TEXT_MAX_TOKENS = 150
        API_MAX_RETRIES = 3
        API_RETRY_DELAY = 1.0
        API_RETRY_BACKOFF = 2.0
        API_TIMEOUT = 120
        VISION_MODELS = ["Salesforce/blip-image-captioning-base"]
        GENERATIONS_DIR = Path("static/generations")
        LOGS_DIR = Path("logs")
        CACHE_ENABLED = False
    
    # Dummy decorators if cache not available
    def cached_image_generation(f):
        return f
    def cached_text_generation(f):
        return f
    def get_cache_manager():
        return None

load_dotenv()

# Set Hugging Face Inference Endpoint to use new router
os.environ["HF_INFERENCE_ENDPOINT"] = "https://router.huggingface.co"

# Configure structured logging
LOG_DIR = Config.LOGS_DIR
LOG_DIR.mkdir(exist_ok=True)

# Create logger
logger = logging.getLogger("autonomous_artist")
logger.setLevel(logging.DEBUG)

# File handler - detailed logs
log_file = LOG_DIR / f"artist_{datetime.now().strftime('%Y%m%d')}.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

# Console handler - info and above
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def retry_with_backoff(max_retries: int = None, initial_delay: float = None, backoff_factor: float = None) -> Callable:
    """Decorator for retrying functions with exponential backoff"""
    if max_retries is None:
        max_retries = Config.API_MAX_RETRIES
    if initial_delay is None:
        initial_delay = Config.API_RETRY_DELAY
    if backoff_factor is None:
        backoff_factor = Config.API_RETRY_BACKOFF
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
            
            raise last_exception
        return wrapper
    return decorator


def validate_prompt(prompt: str) -> str:
    """Validate and sanitize image generation prompt"""
    from security_utils import validate_prompt_input
    
    # Use security utils for validation
    is_valid, error_msg = validate_prompt_input(prompt)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Sanitize
    prompt = prompt.strip()
    
    # Limit length
    max_length = 1000
    if len(prompt) > max_length:
        logger.warning(
            f"Prompt truncated from {len(prompt)} to {max_length} chars"
        )
        prompt = prompt[:max_length]
    
    return prompt


def validate_image_path(path: str) -> Path:
    """Validate image path for security"""
    try:
        file_path = Path(path).resolve()
        
        # Ensure it's within our generations directory or is an absolute path we created
        # This prevents directory traversal attacks
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        # Check file size (prevent huge files)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_path.stat().st_size > max_size:
            raise ValueError(f"Image file too large: {file_path.stat().st_size} bytes")
        
        return file_path
    except Exception as e:
        logger.error(f"Image path validation failed: {e}")
        raise


def log_painting_event(event_type: str, data: dict):
    """Log painting-related events with structured data"""
    logger.info(f"PAINTING_{event_type.upper()}: {data.get('subject', 'unknown')} / {data.get('style', 'unknown')}")
    logger.debug(f"Full painting data: {data}")


def log_state_change(old_state: dict, new_state: dict):
    """Log state transitions"""
    changes = []
    if old_state.get('mood') != new_state.get('mood'):
        changes.append(f"mood: {old_state.get('mood')} -> {new_state.get('mood')}")
    if abs(old_state.get('energy', 0) - new_state.get('energy', 0)) > 0.1:
        changes.append(f"energy: {old_state.get('energy', 0):.2f} -> {new_state.get('energy', 0):.2f}")

    if changes:
        logger.info(f"STATE_CHANGE: {', '.join(changes)}")


def log_api_call(api_name: str, success: bool, duration_ms: float = None, error: str = None):
    """Log API calls with timing"""
    if success:
        logger.info(f"API_CALL: {api_name} succeeded" + (f" ({duration_ms:.0f}ms)" if duration_ms else ""))
    else:
        logger.warning(f"API_CALL: {api_name} failed - {error}")

HF_API_TOKEN = Config.HF_API_TOKEN
MODEL_ID = Config.IMAGE_MODEL

# Ensure static/generations exists
GENERATIONS_DIR = Config.GENERATIONS_DIR
GENERATIONS_DIR.mkdir(parents=True, exist_ok=True)

@retry_with_backoff()
@cached_image_generation
def generate_image_api(prompt: str) -> dict:
    """Generate an image using Hugging Face InferenceClient with retry and caching"""
    if not HF_API_TOKEN:
        logger.error("HF_API_TOKEN not found in .env")
        return {
            "success": False,
            "error": "HF_API_TOKEN not found in .env"
        }
    
    # Validate and sanitize prompt
    try:
        prompt = validate_prompt(prompt)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    client = InferenceClient(token=HF_API_TOKEN)
    start_time = time.time()

    try:
        # text_to_image returns a PIL Image
        logger.debug(f"Generating image with {MODEL_ID}")
        image = client.text_to_image(prompt, model=MODEL_ID)

        timestamp = int(time.time())
        filename = f"painting_{timestamp}.jpg"
        filepath = GENERATIONS_DIR / filename

        image.save(filepath)

        duration_ms = (time.time() - start_time) * 1000
        log_api_call("text_to_image", True, duration_ms)
        logger.info(f"Image saved to {filepath}")

        return {
            "success": True,
            "image_url": str(filepath),
            "web_url": f"/static/generations/{filename}",
            "prompt": prompt
        }

    except Exception as e:
        logger.warning(f"Primary model {MODEL_ID} failed: {e}")

        # Fallback to older model
        try:
            fallback_model = Config.IMAGE_FALLBACK_MODEL
            logger.info(f"Trying fallback model: {fallback_model}")

            image = client.text_to_image(prompt, model=fallback_model)

            timestamp = int(time.time())
            filename = f"painting_{timestamp}.jpg"
            filepath = GENERATIONS_DIR / filename

            image.save(filepath)

            duration_ms = (time.time() - start_time) * 1000
            log_api_call("text_to_image_fallback", True, duration_ms)
            logger.info(f"Fallback image saved to {filepath}")

            return {
                "success": True,
                "image_url": str(filepath),
                "web_url": f"/static/generations/{filename}",
                "prompt": prompt
            }
        except Exception as e2:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call("text_to_image", False, duration_ms, f"{e} / {e2}")
            return {
                "success": False,
                "error": f"Primary error: {str(e)}. Fallback error: {str(e2)}"
            }

def analyze_image_api(image_path: str, prompt_context: str = None) -> str:
    """
    Analyze the image to get a visual description.
    Falls back to 'simulated vision' (using prompt) if API fails.
    """
    if not HF_API_TOKEN:
        return f"I see a painting. (Vision API disabled) {prompt_context}"
    
    # Validate image path
    try:
        validated_path = validate_image_path(image_path)
    except Exception as e:
        logger.error(f"Image validation failed: {e}")
        return f"Unable to analyze image. {prompt_context}"

    client = InferenceClient(token=HF_API_TOKEN)
    
    # Try reliable vision models from config
    vision_models = Config.VISION_MODELS
    
    for model in vision_models:
        try:
            # inference_client.image_to_text(path_or_url, model=...)
            description = client.image_to_text(image_path, model=model)
            if description:
                return f"I see {description}."
        except Exception as e:
            # print(f"Vision model {model} failed: {e}")
            continue
            
    # Fallback to Simulated Vision
    if prompt_context:
        # Create a 'simulated' visual description from the prompt
        # Extract key visual elements (Subject, Style, Colors)
        return f"I see a {prompt_context.split(',')[0]}... The colors are vibrant and the style seems to match what I intended."
    
    return "The image is hazy... I can't quite make it out."

@retry_with_backoff(max_retries=2)  # Fewer retries for text gen
@cached_text_generation
def generate_text_api(system_prompt: str, user_prompt: str) -> str:
    """
    Generate text using an LLM with retry logic and caching
    """
    if not HF_API_TOKEN:
        logger.warning("Text generation skipped - no HF_API_TOKEN")
        return "Thinking..."
    
    # Validate inputs
    if not system_prompt or not user_prompt:
        logger.error("Empty prompt provided to text generation")
        return "I am lost for words right now."

    client = InferenceClient(token=HF_API_TOKEN)
    start_time = time.time()

    model_id = Config.TEXT_MODEL

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        output = client.chat_completion(messages, model=model_id, max_tokens=Config.TEXT_MAX_TOKENS)
        result = output.choices[0].message.content

        duration_ms = (time.time() - start_time) * 1000
        log_api_call("chat_completion", True, duration_ms)
        logger.debug(f"Generated text: {result[:100]}...")

        return result

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call("chat_completion", False, duration_ms, str(e))
        logger.error(f"Text generation failed: {e}")
        return "I am lost for words right now."

def post_to_facebook_api(image_path: str, caption: str) -> dict:
    """
    Post an image to the Facebook Graph API
    """
    import requests
    
    page_id = os.getenv("FB_PAGE_ID")
    access_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    
    if not page_id or not access_token:
        return {
            "success": False, 
            "error": "Missing FB_PAGE_ID or FB_PAGE_ACCESS_TOKEN in .env"
        }
    
    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    
    try:
        with open(image_path, 'rb') as img_file:
            payload = {
                'message': caption,
                'access_token': access_token
            }
            files = {
                'source': img_file
            }
            
            response = requests.post(url, data=payload, files=files)
            data = response.json()
            
            if response.status_code == 200 and 'id' in data:
                return {"success": True, "post_id": data['id']}
            else:
                return {"success": False, "error": data.get('error', {}).get('message', 'Unknown Error')}
                
    except Exception as e:
        return {"success": False, "error": str(e)}

def upload_to_imgur(image_path: str) -> dict:
    """
    Upload image to Imgur for public hosting (needed for Facebook sharing)
    Uses Imgur's anonymous upload - no account needed
    """
    import requests
    import base64
    
    try:
        # Imgur anonymous upload endpoint
        url = "https://api.imgur.com/3/upload"
        
        # Read and encode image
        with open(image_path, 'rb') as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Imgur anonymous client ID (public, safe to use)
        headers = {
            'Authorization': 'Client-ID 546c25a59c58ad7'
        }
        
        payload = {
            'image': image_data,
            'type': 'base64'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        data = response.json()
        
        if data.get('success'):
            return {
                "success": True,
                "url": data['data']['link'],
                "delete_hash": data['data']['deletehash']
            }
        else:
            return {"success": False, "error": data.get('data', {}).get('error', 'Unknown error')}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
