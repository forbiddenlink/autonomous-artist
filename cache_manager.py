"""
Caching system for API responses to reduce costs and improve performance
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from functools import wraps
import logging

logger = logging.getLogger("autonomous_artist")

try:
    from config import Config
except ImportError:
    class Config:
        CACHE_DIR = Path("cache")
        CACHE_ENABLED = True
        CACHE_TTL_IMAGES = 86400 * 7  # 7 days
        CACHE_TTL_TEXT = 3600  # 1 hour


class CacheManager:
    """Manages caching of API responses"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Separate directories for different cache types
        self.image_cache_dir = self.cache_dir / "images"
        self.text_cache_dir = self.cache_dir / "text"
        self.metadata_cache_dir = self.cache_dir / "metadata"
        
        for directory in [self.image_cache_dir, self.text_cache_dir, self.metadata_cache_dir]:
            directory.mkdir(exist_ok=True)
    
    def _get_cache_key(self, data: str) -> str:
        """Generate a hash key for cache lookup"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _get_metadata_path(self, cache_key: str, cache_type: str) -> Path:
        """Get path to metadata file"""
        return self.metadata_cache_dir / f"{cache_type}_{cache_key}.json"
    
    def _is_expired(self, metadata: Dict[str, Any], ttl: int) -> bool:
        """Check if cache entry is expired"""
        timestamp = metadata.get("timestamp", 0)
        return (time.time() - timestamp) > ttl
    
    def get_image_cache(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get cached image generation result"""
        cache_key = self._get_cache_key(prompt)
        metadata_path = self._get_metadata_path(cache_key, "image")
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Check if expired
            if self._is_expired(metadata, Config.CACHE_TTL_IMAGES):
                logger.debug(f"Cache expired for prompt: {prompt[:50]}...")
                return None
            
            # Verify image file exists
            image_path = Path(metadata.get("image_path", ""))
            if not image_path.exists():
                logger.warning(f"Cached image file missing: {image_path}")
                return None
            
            logger.info(f"Cache HIT for image: {prompt[:50]}...")
            return metadata
            
        except Exception as e:
            logger.error(f"Error reading image cache: {e}")
            return None
    
    def set_image_cache(self, prompt: str, image_path: str, metadata: Dict[str, Any]) -> None:
        """Store image generation result in cache"""
        cache_key = self._get_cache_key(prompt)
        metadata_path = self._get_metadata_path(cache_key, "image")
        
        cache_data = {
            "prompt": prompt,
            "image_path": image_path,
            "timestamp": time.time(),
            **metadata
        }
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Cached image result for: {prompt[:50]}...")
        except Exception as e:
            logger.error(f"Error writing image cache: {e}")
    
    def get_text_cache(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Get cached text generation result"""
        cache_key = self._get_cache_key(system_prompt + user_prompt)
        metadata_path = self._get_metadata_path(cache_key, "text")
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Check if expired
            if self._is_expired(metadata, Config.CACHE_TTL_TEXT):
                logger.debug("Text cache expired")
                return None
            
            logger.info("Cache HIT for text generation")
            return metadata.get("response")
            
        except Exception as e:
            logger.error(f"Error reading text cache: {e}")
            return None
    
    def set_text_cache(self, system_prompt: str, user_prompt: str, response: str) -> None:
        """Store text generation result in cache"""
        cache_key = self._get_cache_key(system_prompt + user_prompt)
        metadata_path = self._get_metadata_path(cache_key, "text")
        
        cache_data = {
            "system_prompt": system_prompt[:100] + "..." if len(system_prompt) > 100 else system_prompt,
            "user_prompt": user_prompt[:100] + "..." if len(user_prompt) > 100 else user_prompt,
            "response": response,
            "timestamp": time.time()
        }
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug("Cached text generation result")
        except Exception as e:
            logger.error(f"Error writing text cache: {e}")
    
    def clear_expired(self) -> int:
        """Remove expired cache entries"""
        cleared = 0
        
        for metadata_file in self.metadata_cache_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                cache_type = metadata_file.stem.split('_')[0]
                ttl = Config.CACHE_TTL_IMAGES if cache_type == "image" else Config.CACHE_TTL_TEXT
                
                if self._is_expired(metadata, ttl):
                    metadata_file.unlink()
                    cleared += 1
                    
                    # Also remove the associated image file if it exists
                    if cache_type == "image" and "image_path" in metadata:
                        image_path = Path(metadata["image_path"])
                        if image_path.exists():
                            image_path.unlink()
                            
            except Exception as e:
                logger.error(f"Error clearing cache entry {metadata_file}: {e}")
        
        logger.info(f"Cleared {cleared} expired cache entries")
        return cleared
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        image_count = len(list(self.metadata_cache_dir.glob("image_*.json")))
        text_count = len(list(self.metadata_cache_dir.glob("text_*.json")))
        
        total_size = sum(
            f.stat().st_size 
            for f in self.cache_dir.rglob("*") 
            if f.is_file()
        )
        
        return {
            "image_entries": image_count,
            "text_entries": text_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir)
        }


# Global cache instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached_image_generation(func: Callable) -> Callable:
    """Decorator to cache image generation results"""
    @wraps(func)
    def wrapper(prompt: str, *args, **kwargs):
        if not Config.CACHE_ENABLED:
            return func(prompt, *args, **kwargs)
        
        cache = get_cache_manager()
        
        # Try to get from cache
        cached_result = cache.get_image_cache(prompt)
        if cached_result:
            return {
                "success": True,
                "image_url": cached_result["image_path"],
                "web_url": f"/static/generations/{Path(cached_result['image_path']).name}",
                "prompt": prompt,
                "from_cache": True
            }
        
        # Generate new image
        result = func(prompt, *args, **kwargs)
        
        # Cache if successful
        if result.get("success") and result.get("image_url"):
            cache.set_image_cache(prompt, result["image_url"], {
                "web_url": result.get("web_url"),
                "model_used": result.get("model_used", "unknown")
            })
        
        return result
    
    return wrapper


def cached_text_generation(func: Callable) -> Callable:
    """Decorator to cache text generation results"""
    @wraps(func)
    def wrapper(system_prompt: str, user_prompt: str, *args, **kwargs):
        if not Config.CACHE_ENABLED:
            return func(system_prompt, user_prompt, *args, **kwargs)
        
        cache = get_cache_manager()
        
        # Try to get from cache
        cached_result = cache.get_text_cache(system_prompt, user_prompt)
        if cached_result:
            return cached_result
        
        # Generate new text
        result = func(system_prompt, user_prompt, *args, **kwargs)
        
        # Cache the result
        if result and isinstance(result, str):
            cache.set_text_cache(system_prompt, user_prompt, result)
        
        return result
    
    return wrapper
