import time
from fastapi import HTTPException, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .config import settings

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# In-memory rate limiting storage for more granular control
rate_limit_storage = {}

def check_rate_limit(request: Request, user_id: str = None):
    """
    Custom rate limiting function that checks both per-minute and per-hour limits
    """
    current_time = time.time()
    
    # Use user_id if available, otherwise use IP address
    key = user_id if user_id else get_remote_address(request)
    
    # Initialize storage for this key if not exists
    if key not in rate_limit_storage:
        rate_limit_storage[key] = {
            "requests": [],
            "last_cleanup": current_time
        }
    
    user_data = rate_limit_storage[key]
    
    # Clean up old requests (older than 1 hour)
    if current_time - user_data["last_cleanup"] > 300:  # Cleanup every 5 minutes
        user_data["requests"] = [req_time for req_time in user_data["requests"] 
                               if current_time - req_time < 3600]  # Keep last hour
        user_data["last_cleanup"] = current_time
    
    # Count requests in the last minute and hour
    requests_last_minute = len([req_time for req_time in user_data["requests"] 
                              if current_time - req_time < 60])
    requests_last_hour = len(user_data["requests"])
    
    # Check limits
    if requests_last_minute >= settings.REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {settings.REQUESTS_PER_MINUTE} requests per minute"
        )
    
    if requests_last_hour >= settings.REQUESTS_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {settings.REQUESTS_PER_HOUR} requests per hour"
        )
    
    # Add current request to storage
    user_data["requests"].append(current_time)
    
    return True

def cleanup_rate_limit_storage():
    """
    Cleanup old entries from rate limit storage
    """
    current_time = time.time()
    expired_keys = []
    
    for key, data in rate_limit_storage.items():
        # Remove entries with no requests in the last hour
        recent_requests = [req_time for req_time in data["requests"] 
                         if current_time - req_time < 3600]
        if not recent_requests:
            expired_keys.append(key)
        else:
            data["requests"] = recent_requests
    
    for key in expired_keys:
        del rate_limit_storage[key]
