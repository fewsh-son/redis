import redis
from typing import Optional
from config import Config

class RedisClient:
    _instance: Optional['RedisClient'] = None
    _redis_client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                health_check_interval=30
            )
    
    @property
    def client(self) -> redis.Redis:
        return self._redis_client
    
    def ping(self) -> bool:
        """Kiểm tra kết nối Redis"""
        try:
            return self._redis_client.ping()
        except redis.ConnectionError:
            return False
    
    def close(self):
        """Đóng kết nối Redis"""
        if self._redis_client:
            self._redis_client.close()

# Global instance
redis_client = RedisClient() 