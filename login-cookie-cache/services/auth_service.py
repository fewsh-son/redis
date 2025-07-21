import sys
import os
import time
from typing import Optional, Tuple

# Add parent directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))

from utils.redis_client import redis_client
from models.user import User
from services.session_service import SessionService

class AuthService:
    """
    Service xử lý authentication
    Sử dụng Redis để store user data và manage sessions
    """

    def __init__(self):
        self.redis = redis_client.client
        self.session_service = SessionService()
        self.user_prefix = "user:"
        self.username_index = "username_to_id:"

    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Đăng ký user mới
        Returns: (success, message)
        """
        # Check if username exists
        username_key = f"{self.username_index}{username}"
        if self.redis.exists(username_key):
            return False, "Username already exists"

        # Generate user ID
        user_id = f"user_{int(time.time() * 1000)}"

        # Create user
        user = User.create(user_id, username, email, password)

        pipe = self.redis.pipeline()

        # Store user data
        user_key = f"{self.user_prefix}{user_id}"
        pipe.hmset(user_key, user.to_dict())

        # Create username index for quick lookup
        pipe.set(username_key, user_id)

        pipe.execute()

        print(f"✅ Registered user: {username} ({user_id})")
        return True, f"User {username} registered successfully"

    def login(self, username: str, password: str) -> Tuple[bool, Optional[str], str]:
        """
        Đăng nhập user
        Returns: (success, session_token, message)
        """
        # Find user by username
        username_key = f"{self.username_index}{username}"
        user_id = self.redis.get(username_key)

        if not user_id:
            return False, None, "Invalid username or password"

        # Get user data
        user_key = f"{self.user_prefix}{user_id}"
        user_data = self.redis.hgetall(user_key)

        if not user_data:
            return False, None, "User not found"

        # Create user object and verify password
        user = User.from_dict(user_data)
        if not user.verify_password(password):
            return False, None, "Invalid username or password"

        if not user.is_active:
            return False, None, "Account is deactivated"

        # Update last login time
        user.last_login = time.time()
        self.redis.hmset(user_key, {'last_login': str(user.last_login)})

        # Create session
        session_token = self.session_service.create_session(user)

        print(f"✅ User {username} logged in successfully")
        return True, session_token, "Login successful"

    def logout(self, session_token: str) -> bool:
        """
        Đăng xuất user
        """
        if self.session_service.destroy_session(session_token):
            print(f"✅ Session {session_token[:8]}... logged out")
            return True
        return False

    def get_user_from_session(self, session_token: str) -> Optional[dict]:
        """
        Lấy user data từ session token
        Thay thế cho query database trong mỗi request
        """
        session_data = self.session_service.get_session(session_token)
        if session_data:
            return session_data
        return None

    def validate_session(self, session_token: str) -> bool:
        """
        Validate session token (equivalent của middleware authentication)
        """
        return self.session_service.get_session(session_token) is not None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Lấy user data từ Redis (thay thế database query)
        """
        user_key = f"{self.user_prefix}{user_id}"
        user_data = self.redis.hgetall(user_key)

        if user_data:
            return User.from_dict(user_data)
        return None

    def simulate_concurrent_logins(self, base_username: str, count: int = 100) -> dict:
        """
        Simulate concurrent logins như peak load của Fake Web Retailer
        """
        print(f"🚀 Simulating {count} concurrent logins...")

        start_time = time.time()
        successful_logins = 0
        session_tokens = []

        # Create test users first
        for i in range(count):
            username = f"{base_username}_{i}"
            success, _ = self.register_user(username, f"{username}@test.com", "password123")
            if success:
                # Login immediately
                login_success, token, _ = self.login(username, "password123")
                if login_success and token:
                    successful_logins += 1
                    session_tokens.append(token)

        end_time = time.time()
        duration = end_time - start_time
        logins_per_second = successful_logins / duration if duration > 0 else 0

        print(f"⚡ {successful_logins}/{count} logins completed in {duration:.3f}s")
        print(f"📊 Performance: {logins_per_second:.0f} logins/second")

        return {
            'total_attempted': count,
            'successful_logins': successful_logins,
            'duration': duration,
            'logins_per_second': logins_per_second,
            'session_tokens': session_tokens[:10]  # Return first 10 for testing
        }

    def cleanup_test_users(self, base_username: str, count: int):
        """
        Cleanup test users
        """
        pipe = self.redis.pipeline()

        for i in range(count):
            username = f"{base_username}_{i}"

            # Get user_id from username index
            username_key = f"{self.username_index}{username}"
            user_id = self.redis.get(username_key)

            if user_id:
                # Delete user data
                user_key = f"{self.user_prefix}{user_id}"
                pipe.delete(user_key)

            # Delete username index
            pipe.delete(username_key)

        result = pipe.execute()
        deleted_count = sum(1 for r in result if r)
        print(f"🧹 Cleaned up {deleted_count} test users")

        return deleted_count
