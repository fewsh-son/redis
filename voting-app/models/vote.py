from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time

class VoteType(Enum):
    """Enum cho loại vote"""
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"

@dataclass
class Vote:
    """Model cho vote của user"""
    user_id: str
    article_id: str
    vote_type: VoteType
    timestamp: float

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    @classmethod
    def from_string(cls, user_id: str, article_id: str, vote_string: str) -> Optional['Vote']:
        """Tạo Vote từ string format 'vote_type|timestamp'"""
        try:
            parts = vote_string.split('|')
            if len(parts) != 2:
                return None

            vote_type_str, timestamp_str = parts
            vote_type = VoteType(vote_type_str)
            timestamp = float(timestamp_str)

            return cls(
                user_id=user_id,
                article_id=article_id,
                vote_type=vote_type,
                timestamp=timestamp
            )
        except (ValueError, TypeError):
            return None

    def to_string(self) -> str:
        """Chuyển Vote thành string format 'vote_type|timestamp'"""
        return f"{self.vote_type.value}|{self.timestamp}"
