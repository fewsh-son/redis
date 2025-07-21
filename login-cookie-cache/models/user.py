from dataclasses import dataclass
from typing import Optional, Dict, Any
import hashlib
import time

@dataclass
class User:
    """Model cho User với password hashing"""
    user_id: str
    username: str
    email: str
    password_hash: str
    created_at: Optional[float] = None
    last_login: Optional[float] = None
    is_active: bool = True

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 (demo purposes only)"""
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def create(cls, user_id: str, username: str, email: str, password: str) -> 'User':
        """Tạo user mới với password được hash"""
        return cls(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=cls.hash_password(password),
            created_at=time.time()
        )

    def verify_password(self, password: str) -> bool:
        """Verify password"""
        return self.password_hash == self.hash_password(password)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': str(self.created_at),
            'last_login': str(self.last_login) if self.last_login else '',
            'is_active': str(self.is_active)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'User':
        """Create User from Redis data"""
        last_login = float(data['last_login']) if data.get('last_login') else None

        return cls(
            user_id=data['user_id'],
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            created_at=float(data['created_at']),
            last_login=last_login,
            is_active=data.get('is_active', 'True') == 'True'
        )

    def to_session_data(self) -> Dict[str, str]:
        """Convert to session data (without sensitive info)"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'last_login': str(self.last_login) if self.last_login else str(time.time()),
            'login_time': str(time.time()),
            'page_views': '1',
            'current_page': '/dashboard'
        }
