from typing import Optional
import time

# In-memory session storage for simple tracking
active_sessions = {}

def create_session(api_key: str) -> str:
    """Create a simple session for API key usage tracking"""
    session_id = f"api_key_{hash(api_key)}_{int(time.time())}"
    active_sessions[session_id] = {
        "api_key_hash": hash(api_key),
        "created_at": time.time(),
        "request_count": 0,
        "last_request_time": time.time()
    }
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    return active_sessions.get(session_id)

def update_session_activity(session_id: str):
    if session_id in active_sessions:
        active_sessions[session_id]["request_count"] += 1
        active_sessions[session_id]["last_request_time"] = time.time()

def cleanup_expired_sessions():
    current_time = time.time()
    expired_sessions = []
    for session_id, session_data in active_sessions.items():
        # Remove sessions older than 24 hours
        if current_time - session_data["created_at"] > 86400:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del active_sessions[session_id]
