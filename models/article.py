from dataclasses import dataclass
from typing import Optional, Dict, Any
import time

@dataclass
class Article:
    """Model cho bài viết"""
    id: str
    title: str
    link: str
    poster: str
    time_created: Optional[float] = None
    upvotes: int = 0
    downvotes: int = 0
    groups: Optional[list] = None  # Danh sách các groups mà article thuộc về
    
    @property
    def votes(self) -> int:
        """Tính tổng votes (upvotes - downvotes)"""
        return self.upvotes - self.downvotes
    
    def __post_init__(self):
        if self.time_created is None:
            self.time_created = time.time()
        if self.groups is None:
            self.groups = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi Article thành dictionary để lưu vào Redis Hash"""
        return {
            'title': self.title,
            'link': self.link,
            'poster': self.poster,
            'time': str(self.time_created),
            'upvotes': str(self.upvotes),
            'downvotes': str(self.downvotes),
            'groups': ','.join(self.groups) if self.groups else ''
        }
    
    @classmethod
    def from_dict(cls, article_id: str, data: Dict[str, str]) -> 'Article':
        """Tạo Article từ dữ liệu Redis Hash"""
        groups_str = data.get('groups', '')
        groups = [g.strip() for g in groups_str.split(',') if g.strip()] if groups_str else []
        
        # Backward compatibility: nếu có votes cũ thì dùng làm upvotes
        upvotes = int(data.get('upvotes', data.get('votes', 0)))
        downvotes = int(data.get('downvotes', 0))
        
        return cls(
            id=article_id,
            title=data.get('title', ''),
            link=data.get('link', ''),
            poster=data.get('poster', ''),
            time_created=float(data.get('time', time.time())),
            upvotes=upvotes,
            downvotes=downvotes,
            groups=groups
        )
    
    def get_score(self) -> float:
        """Tính score cho bài viết (votes + time bonus)"""
        # Score = votes + time_bonus
        # Time bonus giảm dần theo thời gian (để bài viết mới có cơ hội)
        current_time = time.time()
        time_diff_hours = (current_time - self.time_created) / 3600
        time_bonus = max(0, 100 - time_diff_hours * 0.1)  # Giảm 0.1 điểm mỗi giờ
        return self.votes + time_bonus 