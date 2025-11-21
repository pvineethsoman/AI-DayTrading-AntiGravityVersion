import json
import os
from typing import Optional, Any
from datetime import timedelta, datetime
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    """Wrapper for Redis caching with fallback to in-memory cache."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.use_redis = False
        self.memory_cache = {}  # Fallback in-memory cache
        
        try:
            import redis
            self.client = redis.Redis(
                host=os.getenv('REDIS_HOST', host),
                port=int(os.getenv('REDIS_PORT', port)),
                db=int(os.getenv('REDIS_DB', db)),
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.client.ping()
            self.use_redis = True
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory cache: {e}")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if self.use_redis:
            try:
                data = self.client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to memory cache
        if key in self.memory_cache:
            item = self.memory_cache[key]
            if item['expires_at'] > datetime.now():
                return item['value']
            else:
                del self.memory_cache[key]
        return None

    def set(self, key: str, value: Any, expire: int = 3600):
        if self.use_redis:
            try:
                self.client.setex(key, timedelta(seconds=expire), json.dumps(value))
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Fallback to memory cache
        self.memory_cache[key] = {
            'value': value,
            'expires_at': datetime.now() + timedelta(seconds=expire)
        }
        
    def exists(self, key: str) -> bool:
        if self.use_redis:
            try:
                return self.client.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis exists error: {e}")
        
        # Fallback to memory cache
        if key in self.memory_cache:
            if self.memory_cache[key]['expires_at'] > datetime.now():
                return True
            else:
                del self.memory_cache[key]
        return False
