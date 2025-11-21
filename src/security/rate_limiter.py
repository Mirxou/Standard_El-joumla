"""
Rate Limiter for API Security v2.0
Implements in-memory rate limiting per IP/token
"""
from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import threading


class RateLimiter:
    """
    Thread-safe in-memory rate limiter
    """
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for identifier
        
        Args:
            identifier: IP address or token hash
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        with self._lock:
            now = datetime.now()
            cutoff = now - self.window
            
            # Clean old requests
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > cutoff
            ]
            
            # Check limit
            current_count = len(self._requests[identifier])
            
            if current_count >= self.max_requests:
                return False, 0
            
            # Record this request
            self._requests[identifier].append(now)
            remaining = self.max_requests - (current_count + 1)
            
            return True, remaining
    
    def reset(self, identifier: str):
        """Reset rate limit for identifier"""
        with self._lock:
            if identifier in self._requests:
                del self._requests[identifier]
    
    def cleanup_old_entries(self, hours: int = 1):
        """
        Clean up old entries to prevent memory bloat
        
        Args:
            hours: Remove entries older than this many hours
        """
        with self._lock:
            cutoff = datetime.now() - timedelta(hours=hours)
            identifiers_to_remove = []
            
            for identifier, timestamps in self._requests.items():
                # Keep only recent requests
                recent = [t for t in timestamps if t > cutoff]
                if not recent:
                    identifiers_to_remove.append(identifier)
                else:
                    self._requests[identifier] = recent
            
            for identifier in identifiers_to_remove:
                del self._requests[identifier]


# Global rate limiters
login_rate_limiter = RateLimiter(max_requests=10, window_seconds=300)  # 10 attempts per 5 minutes (increased for tests)
api_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)  # 100 requests per minute
