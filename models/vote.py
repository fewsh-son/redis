from enum import Enum
from dataclasses import dataclass
from typing import Optional
import time

class VoteType(Enum):
    """Enum định nghĩa loại vote"""
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    
    def __str__(self):
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> Optional['VoteType']:
        """Chuyển đổi từ string sang VoteType"""
        for vote_type in cls:
            if vote_type.value == value:
                return vote_type
        return None

@dataclass
class Vote:
    """Model cho vote"""
    user_id: str
    article_id: str
    vote_type: VoteType
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> dict:
        """Chuyển đổi Vote thành dictionary"""
        return {
            'user_id': self.user_id,
            'article_id': self.article_id,
            'vote_type': self.vote_type.value,
            'timestamp': str(self.timestamp)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Vote':
        """Tạo Vote từ dictionary"""
        return cls(
            user_id=data['user_id'],
            article_id=data['article_id'],
            vote_type=VoteType.from_string(data['vote_type']),
            timestamp=float(data.get('timestamp', time.time()))
        )
    
    def get_score_value(self) -> int:
        """Lấy giá trị điểm của vote"""
        return 1 if self.vote_type == VoteType.UPVOTE else -1 