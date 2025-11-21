import time
import threading
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Thread-safe rate limiter decorator.
    Ensures that a function is not called more than `max_calls` times in `period` seconds.
    """
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                current_time = time.time()
                # Remove calls older than the period
                self.calls = [t for t in self.calls if current_time - t < self.period]
                
                if len(self.calls) >= self.max_calls:
                    # Calculate wait time
                    oldest_call = self.calls[0]
                    wait_time = self.period - (current_time - oldest_call)
                    if wait_time > 0:
                        logger.warning(f"Rate limit reached for {func.__name__}. Waiting {wait_time:.2f}s")
                        time.sleep(wait_time)
                        # Update current time after sleep
                        current_time = time.time()
                        # Clean up again just in case
                        self.calls = [t for t in self.calls if current_time - t < self.period]
                
                self.calls.append(time.time())
                
            return func(*args, **kwargs)
        return wrapper
