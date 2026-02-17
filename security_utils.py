"""
Security utilities for input validation and sanitization
"""
import re
from typing import Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger("autonomous_artist")


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent directory traversal and injection
    
    Args:
        filename: The filename to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    # Remove any path components
    filename = Path(filename).name
    
    # Remove or replace dangerous characters
    # Allow alphanumeric, dash, underscore, and dot
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Prevent hidden files
    if filename.startswith('.'):
        filename = 'file' + filename
    
    # Limit length
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (
            filename, ''
        )
        filename = name[:max_length - len(ext) - 1] + '.' + ext
    
    return filename


def validate_prompt_input(prompt: str, max_length: int = 1000) -> tuple[
    bool, Optional[str]
]:
    """
    Validate user-provided prompt for image generation
    
    Args:
        prompt: The prompt to validate
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not prompt:
        return False, "Prompt cannot be empty"
    
    if not isinstance(prompt, str):
        return False, "Prompt must be a string"
    
    if len(prompt) > max_length:
        return False, f"Prompt too long (max {max_length} characters)"
    
    # Check for potential injection patterns
    suspicious_patterns = [
        r'<script[^>]*>',  # Script tags
        r'javascript:',     # JavaScript protocol
        r'on\w+\s*=',      # Event handlers
        r'<!--',           # HTML comments
        r'<iframe',        # Iframes
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            logger.warning(f"Suspicious pattern detected in prompt: {pattern}")
            return False, "Invalid characters in prompt"
    
    return True, None


def validate_json_input(data: Any, required_fields: list = None) -> tuple[
    bool, Optional[str]
]:
    """
    Validate JSON input data
    
    Args:
        data: The data to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Invalid JSON data format"
    
    if required_fields:
        missing = [f for f in required_fields if f not in data]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
    
    return True, None


def validate_boolean_param(
    value: Any, param_name: str
) -> tuple[bool, Optional[str]]:
    """
    Validate boolean parameter
    
    Args:
        value: The value to validate
        param_name: Name of the parameter for error messages
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, bool):
        return False, f"{param_name} must be a boolean"
    
    return True, None


def validate_integer_param(
    value: Any,
    param_name: str,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None
) -> tuple[bool, Optional[str]]:
    """
    Validate integer parameter with optional bounds
    
    Args:
        value: The value to validate
        param_name: Name of the parameter for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, int):
        return False, f"{param_name} must be an integer"
    
    if min_val is not None and value < min_val:
        return False, f"{param_name} must be at least {min_val}"
    
    if max_val is not None and value > max_val:
        return False, f"{param_name} must be at most {max_val}"
    
    return True, None


def validate_api_key(api_key: str) -> bool:
    """
    Basic validation for API key format
    
    Args:
        api_key: The API key to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Basic checks: reasonable length, alphanumeric with some special chars
    if len(api_key) < 10 or len(api_key) > 200:
        return False
    
    # Should contain only safe characters
    if not re.match(r'^[a-zA-Z0-9._-]+$', api_key):
        return False
    
    return True


def sanitize_log_message(message: str, max_length: int = 500) -> str:
    """
    Sanitize message before logging to prevent log injection
    
    Args:
        message: The message to sanitize
        max_length: Maximum length
        
    Returns:
        Sanitized message
    """
    # Remove newlines and control characters that could break logs
    message = re.sub(r'[\r\n\t]', ' ', str(message))
    
    # Limit length
    if len(message) > max_length:
        message = message[:max_length] + '...'
    
    return message
