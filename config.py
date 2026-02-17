"""
Configuration management for Autonomous Artist
Centralizes all configurable values and environment variables
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration class"""
    
    # Application Settings
    APP_NAME: str = "Autonomous Artist"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5001"))
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent
    STATIC_DIR: Path = BASE_DIR / "static"
    GENERATIONS_DIR: Path = STATIC_DIR / "generations"
    LOGS_DIR: Path = BASE_DIR / "logs"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    CACHE_DIR: Path = BASE_DIR / "cache"
    
    # Cache Settings
    CACHE_ENABLED: bool = os.getenv(
        "CACHE_ENABLED", "True"
    ).lower() == "true"
    # 7 days
    CACHE_TTL_IMAGES: int = int(
        os.getenv("CACHE_TTL_IMAGES", str(86400 * 7))
    )
    CACHE_TTL_TEXT: int = int(
        os.getenv("CACHE_TTL_TEXT", "3600")
    )  # 1 hour
    
    # Memory Settings
    MEMORY_FILE: str = os.getenv("MEMORY_FILE", "artist_memory.json")
    MAX_PORTFOLIO_SIZE: int = int(os.getenv("MAX_PORTFOLIO_SIZE", "50"))
    MAX_THEMES_TRACKED: int = int(os.getenv("MAX_THEMES_TRACKED", "100"))
    MAX_COLORS_TRACKED: int = int(os.getenv("MAX_COLORS_TRACKED", "20"))
    MAX_MOOD_HISTORY: int = int(os.getenv("MAX_MOOD_HISTORY", "10"))
    
    # AI/ML Settings
    HF_API_TOKEN: Optional[str] = os.getenv("HF_API_TOKEN")
    IMAGE_MODEL: str = os.getenv(
        "IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell"
    )
    IMAGE_FALLBACK_MODEL: str = os.getenv(
        "IMAGE_FALLBACK_MODEL",
        "stabilityai/stable-diffusion-xl-base-1.0"
    )
    TEXT_MODEL: str = os.getenv(
        "TEXT_MODEL", "Qwen/Qwen2.5-7B-Instruct"
    )
    
    # Vision Models (tried in order)
    VISION_MODELS: list = [
        "Salesforce/blip-image-captioning-base",
        "nlpconnect/vit-gpt2-image-captioning",
        "microsoft/git-base"
    ]
    
    # API Settings
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "120"))
    API_MAX_RETRIES: int = int(os.getenv("API_MAX_RETRIES", "3"))
    API_RETRY_DELAY: float = float(
        os.getenv("API_RETRY_DELAY", "1.0")
    )
    # Exponential multiplier
    API_RETRY_BACKOFF: float = float(
        os.getenv("API_RETRY_BACKOFF", "2.0")
    )
    
    # Text Generation Settings
    TEXT_MAX_TOKENS: int = int(os.getenv("TEXT_MAX_TOKENS", "150"))
    
    # Facebook Integration
    FB_PAGE_ID: Optional[str] = os.getenv("FB_PAGE_ID")
    FB_PAGE_ACCESS_TOKEN: Optional[str] = os.getenv("FB_PAGE_ACCESS_TOKEN")
    FB_API_VERSION: str = os.getenv("FB_API_VERSION", "v19.0")
    
    # Imgur Integration (use env var in production)
    IMGUR_CLIENT_ID: str = os.getenv(
        "IMGUR_CLIENT_ID", "546c25a59c58ad7"
    )
    
    # Artist Behavior Settings
    DEFAULT_ARTIST_NAME: str = os.getenv("ARTIST_NAME", "Aria")
    MOOD_SHIFT_PROBABILITY: float = float(
        os.getenv("MOOD_SHIFT_PROBABILITY", "0.6")
    )
    WILDCARD_EXPLORATION_CHANCE: float = float(
        os.getenv("WILDCARD_EXPLORATION_CHANCE", "0.15")
    )
    LEARNING_RATE: float = float(os.getenv("LEARNING_RATE", "0.08"))
    
    # Satisfaction Thresholds
    HIGH_SATISFACTION_THRESHOLD: float = float(
        os.getenv("HIGH_SATISFACTION_THRESHOLD", "0.75")
    )
    LOW_SATISFACTION_THRESHOLD: float = float(
        os.getenv("LOW_SATISFACTION_THRESHOLD", "0.35")
    )
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE: bool = (
        os.getenv("LOG_TO_FILE", "True").lower() == "true"
    )
    LOG_TO_CONSOLE: bool = (
        os.getenv("LOG_TO_CONSOLE", "True").lower() == "true"
    )
    
    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration values"""
        errors = []
        
        if not cls.HF_API_TOKEN:
            errors.append(
                "HF_API_TOKEN is not set - AI features will be limited"
            )
        
        if cls.MAX_PORTFOLIO_SIZE < 10:
            errors.append("MAX_PORTFOLIO_SIZE should be at least 10")
        
        if not (0.0 <= cls.MOOD_SHIFT_PROBABILITY <= 1.0):
            errors.append(
                "MOOD_SHIFT_PROBABILITY must be between 0 and 1"
            )
        
        if not (0.0 <= cls.WILDCARD_EXPLORATION_CHANCE <= 1.0):
            errors.append(
                "WILDCARD_EXPLORATION_CHANCE must be between 0 and 1"
            )
        
        if not (0.0 <= cls.LEARNING_RATE <= 1.0):
            errors.append("LEARNING_RATE must be between 0 and 1")
        
        if errors:
            import logging
            logger = logging.getLogger("autonomous_artist")
            for error in errors:
                logger.warning(f"Configuration warning: {error}")
            return False
        
        return True
    
    @classmethod
    def create_directories(cls) -> None:
        """Create required directories if they don't exist"""
        directories = [
            cls.STATIC_DIR,
            cls.GENERATIONS_DIR,
            cls.LOGS_DIR,
            cls.TEMPLATES_DIR,
            cls.CACHE_DIR,
            cls.CACHE_DIR / "images",
            cls.CACHE_DIR / "text",
            cls.CACHE_DIR / "metadata",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_summary(cls) -> dict:
        """Get a summary of current configuration (safe for logging)"""
        return {
            "app_name": cls.APP_NAME,
            "version": cls.APP_VERSION,
            "debug": cls.DEBUG,
            "cache_enabled": cls.CACHE_ENABLED,
            "models": {
                "image": cls.IMAGE_MODEL,
                "text": cls.TEXT_MODEL
            },
            "artist": {
                "name": cls.DEFAULT_ARTIST_NAME,
                "max_portfolio": cls.MAX_PORTFOLIO_SIZE
            },
            "api_configured": bool(cls.HF_API_TOKEN),
            "facebook_configured": bool(
                cls.FB_PAGE_ID and cls.FB_PAGE_ACCESS_TOKEN
            ),
        }


# Validate configuration on import
if __name__ != "__main__":
    Config.validate()
    Config.create_directories()
