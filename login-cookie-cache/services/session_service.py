import sys
import os
import uuid
import time
from typing import Optional, Dict, Any

# Add parent directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))

from utils.redis_client import redis_client
from models.user import User

class SessionService:
    """
    Service quản lý sessions sử dụng Redis HASH
    Thay thế database quan hệ cho Fake Web Retailer
    """

    def __init__(self):
        self.redis = redis_client.client
        self.session_prefix = "session:"
        self.cart_prefix = "cart:"
        self.default_ttl = 3600  # 1 hour
        self.cart_ttl = 86400   # 24 hours

    def create_session(self, user: User) -> str:
        """
        Tạo session mới cho user
        Returns: session_token
        """
        # Tạo unique session token
        session_token = str(uuid.uuid4())
        session_key = f"{self.session_prefix}{session_token}"

        # Prepare session data
        session_data = user.to_session_data()

        pipe = self.redis.pipeline()

        # Store session data in Redis HASH
        pipe.hmset(session_key, session_data)

        # Set TTL for auto-expiration
        pipe.expire(session_key, self.default_ttl)

        # Initialize empty shopping cart
        cart_key = f"{self.cart_prefix}{session_token}"
        pipe.hmset(cart_key, {
            'total_items': '0',
            'total_value': '0.00',
            'created_at': str(time.time())
        })
        pipe.expire(cart_key, self.cart_ttl)

        pipe.execute()

        print(f"✅ Created session {session_token} for user {user.username}")
        return session_token

    def get_session(self, session_token: str) -> Optional[Dict[str, str]]:
        """
        Lấy session data từ Redis HASH
        Returns: session_data dict hoặc None
        """
        session_key = f"{self.session_prefix}{session_token}"

        # Get all session data from HASH
        session_data = self.redis.hgetall(session_key)

        if not session_data:
            return None

        # Update last_activity (simulating user activity)
        self.redis.hset(session_key, 'last_activity', str(time.time()))

        # Refresh TTL
        self.redis.expire(session_key, self.default_ttl)

        return session_data

    def update_session_activity(self, session_token: str, page: str) -> bool:
        """
        Cập nhật user activity - Đây là operation tốn nhiều writes nhất
        Thay thế cho UPDATE queries trong database
        """
        session_key = f"{self.session_prefix}{session_token}"

        # Check if session exists
        if not self.redis.exists(session_key):
            return False

        pipe = self.redis.pipeline()

        # Atomic updates using HASH commands
        pipe.hset(session_key, 'last_activity', str(time.time()))
        pipe.hset(session_key, 'current_page', page)
        pipe.hincrby(session_key, 'page_views', 1)

        # Refresh TTL
        pipe.expire(session_key, self.default_ttl)

        pipe.execute()
        return True

    def add_to_cart(self, session_token: str, item_id: str,
                   item_name: str, quantity: int, price: float) -> bool:
        """
        Thêm item vào shopping cart (high-frequency operation)
        """
        cart_key = f"{self.cart_prefix}{session_token}"

        if not self.redis.exists(cart_key):
            return False

        pipe = self.redis.pipeline()

        # Add item to cart
        item_key = f"item:{item_id}"
        item_value = f"{item_name}|{quantity}|${price:.2f}"
        pipe.hset(cart_key, item_key, item_value)

        # Update totals
        pipe.hincrby(cart_key, 'total_items', quantity)
        current_total = float(self.redis.hget(cart_key, 'total_value') or '0.00')
        new_total = current_total + (quantity * price)
        pipe.hset(cart_key, 'total_value', f"{new_total:.2f}")

        # Update timestamp
        pipe.hset(cart_key, 'updated_at', str(time.time()))

        # Refresh TTL
        pipe.expire(cart_key, self.cart_ttl)

        pipe.execute()
        return True

    def get_cart(self, session_token: str) -> Dict[str, str]:
        """Lấy shopping cart data"""
        cart_key = f"{self.cart_prefix}{session_token}"
        return self.redis.hgetall(cart_key) or {}

    def destroy_session(self, session_token: str) -> bool:
        """
        Xóa session (logout)
        """
        session_key = f"{self.session_prefix}{session_token}"
        cart_key = f"{self.cart_prefix}{session_token}"

        pipe = self.redis.pipeline()
        pipe.delete(session_key)
        pipe.delete(cart_key)
        result = pipe.execute()

        return any(result)

    def cleanup_expired_sessions(self) -> int:
        """
        Manual cleanup (Redis TTL sẽ tự động handle)
        Chỉ để demo - trong thực tế không cần
        """
        # Redis TTL will handle this automatically
        # This is just for demonstration
        pattern = f"{self.session_prefix}*"
        keys = self.redis.keys(pattern)

        expired_count = 0
        for key in keys:
            ttl = self.redis.ttl(key)
            if ttl == -1:  # No expiration set
                self.redis.expire(key, self.default_ttl)
            elif ttl == -2:  # Key doesn't exist
                expired_count += 1

        return expired_count

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Lấy statistics về sessions
        """
        session_pattern = f"{self.session_prefix}*"
        cart_pattern = f"{self.cart_prefix}*"

        active_sessions = len(self.redis.keys(session_pattern))
        active_carts = len(self.redis.keys(cart_pattern))

        # Memory usage info
        info = self.redis.info('memory')

        return {
            'active_sessions': active_sessions,
            'active_carts': active_carts,
            'memory_used': info.get('used_memory_human', 'N/A'),
            'redis_version': self.redis.info()['redis_version']
        }

    def simulate_high_load_update(self, session_token: str, updates_count: int = 100):
        """
        Simulate high-frequency updates như Fake Web Retailer
        Đây là những operations mà database không handle được
        """
        session_key = f"{self.session_prefix}{session_token}"

        if not self.redis.exists(session_key):
            return False

        start_time = time.time()

        # Batch updates using pipeline
        pipe = self.redis.pipeline()

        for i in range(updates_count):
            pipe.hset(session_key, 'last_activity', str(time.time()))
            pipe.hincrby(session_key, 'page_views', 1)
            pipe.hset(session_key, 'current_page', f'/page-{i}')

        pipe.execute()

        end_time = time.time()
        duration = end_time - start_time
        ops_per_second = updates_count / duration if duration > 0 else 0

        print(f"⚡ Completed {updates_count} updates in {duration:.3f}s")
        print(f"📊 Performance: {ops_per_second:.0f} operations/second")

        return True
