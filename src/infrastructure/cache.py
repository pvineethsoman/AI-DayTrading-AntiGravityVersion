import redis
import json
import os
from typing import Optional, Any
from datetime import timedelta

class RedisCache:
    """Wrapper for Redis caching."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', host),
            port=int(os.getenv('REDIS_PORT', port)),
            db=int(os.getenv('REDIS_DB', db)),
            decode_responses=True
        )

    def get(self, key: str) -> Optional[Any]:
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value: Any, expire: int = 3600):
        self.client.setex(key, timedelta(seconds=expire), json.dumps(value))
        
    def exists(self, key: str) -> bool:
        return self.client.exists(key) > 0
