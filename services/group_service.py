from typing import List, Set, Optional
from models.article import Article
from utils.redis_client import redis_client
from config import Config

class GroupService:
    """Service quản lý groups của articles"""
    
    def __init__(self):
        self.redis = redis_client.client
    
    def add_article_to_group(self, article_id: str, group_name: str, article_score: float = None):
        """Thêm article vào group"""
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        groups_key = f"{Config.GROUPS_SET_PREFIX}{group_name}"
        group_score_key = f"{Config.GROUP_SCORE_PREFIX}{group_name}"
        
        pipe = self.redis.pipeline()
        
        # Thêm article vào SET groups:group_name
        pipe.sadd(groups_key, article_key)
        
        # Nếu có score, thêm vào ZSET score:group_name
        if article_score is not None:
            pipe.zadd(group_score_key, {article_key: article_score})
        
        pipe.execute()
    
    def remove_article_from_group(self, article_id: str, group_name: str):
        """Xóa article khỏi group"""
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        groups_key = f"{Config.GROUPS_SET_PREFIX}{group_name}"
        group_score_key = f"{Config.GROUP_SCORE_PREFIX}{group_name}"
        
        pipe = self.redis.pipeline()
        
        # Xóa khỏi SET groups:group_name
        pipe.srem(groups_key, article_key)
        
        # Xóa khỏi ZSET score:group_name
        pipe.zrem(group_score_key, article_key)
        
        pipe.execute()
    
    def get_articles_in_group(self, group_name: str) -> List[str]:
        """Lấy danh sách article IDs trong group"""
        groups_key = f"{Config.GROUPS_SET_PREFIX}{group_name}"
        article_keys = self.redis.smembers(groups_key)
        
        # Chuyển từ article:12345 thành 12345
        return [key.replace(Config.ARTICLE_KEY_PREFIX, "") for key in article_keys]
    
    def get_articles_in_group_by_score(self, group_name: str, start: int = 0, end: int = -1) -> List[str]:
        """Lấy danh sách article IDs trong group sắp xếp theo score"""
        group_score_key = f"{Config.GROUP_SCORE_PREFIX}{group_name}"
        article_keys = self.redis.zrevrange(group_score_key, start, end)
        
        # Chuyển từ article:12345 thành 12345
        return [key.replace(Config.ARTICLE_KEY_PREFIX, "") for key in article_keys]
    
    def get_group_article_count(self, group_name: str) -> int:
        """Đếm số articles trong group"""
        groups_key = f"{Config.GROUPS_SET_PREFIX}{group_name}"
        return self.redis.scard(groups_key)
    
    def get_all_groups(self) -> List[str]:
        """Lấy danh sách tất cả groups"""
        pattern = f"{Config.GROUPS_SET_PREFIX}*"
        group_keys = self.redis.keys(pattern)
        
        # Chuyển từ groups:programming thành programming
        return [key.replace(Config.GROUPS_SET_PREFIX, "") for key in group_keys]
    
    def update_article_score_in_groups(self, article_id: str, new_score: float, groups: List[str]):
        """Cập nhật score của article trong tất cả groups mà nó thuộc về"""
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        
        pipe = self.redis.pipeline()
        
        for group_name in groups:
            group_score_key = f"{Config.GROUP_SCORE_PREFIX}{group_name}"
            # Kiểm tra xem article có trong group không
            if self.redis.sismember(f"{Config.GROUPS_SET_PREFIX}{group_name}", article_key):
                pipe.zadd(group_score_key, {article_key: new_score})
        
        pipe.execute()
    
    def delete_group(self, group_name: str):
        """Xóa hoàn toàn một group"""
        groups_key = f"{Config.GROUPS_SET_PREFIX}{group_name}"
        group_score_key = f"{Config.GROUP_SCORE_PREFIX}{group_name}"
        
        pipe = self.redis.pipeline()
        pipe.delete(groups_key)
        pipe.delete(group_score_key)
        pipe.execute()
    
    def get_article_groups(self, article_id: str) -> List[str]:
        """Lấy danh sách groups mà article thuộc về"""
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        all_groups = self.get_all_groups()
        
        groups = []
        for group_name in all_groups:
            groups_key = f"{Config.GROUPS_SET_PREFIX}{group_name}"
            if self.redis.sismember(groups_key, article_key):
                groups.append(group_name)
        
        return groups
    
    def get_group_stats(self, group_name: str) -> dict:
        """Lấy thống kê của group"""
        groups_key = f"{Config.GROUPS_SET_PREFIX}{group_name}"
        group_score_key = f"{Config.GROUP_SCORE_PREFIX}{group_name}"
        
        article_count = self.redis.scard(groups_key)
        
        # Lấy score cao nhất và thấp nhất
        highest_score = self.redis.zrevrange(group_score_key, 0, 0, withscores=True)
        lowest_score = self.redis.zrange(group_score_key, 0, 0, withscores=True)
        
        return {
            'name': group_name,
            'article_count': article_count,
            'highest_score': highest_score[0][1] if highest_score else 0,
            'lowest_score': lowest_score[0][1] if lowest_score else 0
        } 