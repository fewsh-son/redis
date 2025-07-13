from typing import Optional, Dict, List
from models.vote import Vote, VoteType
from models.article import Article
from utils.redis_client import redis_client
from config import Config
import time

class VotingService:
    """Service xử lý logic voting (upvote/downvote)"""
    
    def __init__(self):
        self.redis = redis_client.client
    
    def upvote(self, user_id: str, article_id: str) -> bool:
        """
        Upvote một bài viết
        Returns: True nếu thành công, False nếu thất bại
        """
        return self._vote(user_id, article_id, VoteType.UPVOTE)
    
    def downvote(self, user_id: str, article_id: str) -> bool:
        """
        Downvote một bài viết
        Returns: True nếu thành công, False nếu thất bại
        """
        return self._vote(user_id, article_id, VoteType.DOWNVOTE)
    
    def _vote(self, user_id: str, article_id: str, vote_type: VoteType) -> bool:
        """
        Internal method để xử lý vote
        """
        # Kiểm tra xem article có tồn tại không
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        if not self.redis.exists(article_key):
            return False
        
        # Lấy vote hiện tại của user
        current_vote = self.get_user_vote(user_id, article_id)
        
        # Nếu user đã vote cùng loại rồi thì return False
        if current_vote and current_vote.vote_type == vote_type:
            return False
        
        # Xóa vote cũ nếu có
        if current_vote:
            self._remove_vote_from_redis(user_id, article_id, current_vote.vote_type)
        
        # Thêm vote mới
        self._add_vote_to_redis(user_id, article_id, vote_type)
        
        # Cập nhật vote counts trong article
        self._update_article_vote_counts(article_id)
        
        # Lưu vote history
        self._save_vote_history(user_id, article_id, vote_type)
        
        return True
    
    def remove_vote(self, user_id: str, article_id: str) -> bool:
        """
        Xóa vote của user cho article
        Returns: True nếu thành công, False nếu không có vote để xóa
        """
        current_vote = self.get_user_vote(user_id, article_id)
        
        if not current_vote:
            return False
        
        # Xóa vote khỏi Redis
        self._remove_vote_from_redis(user_id, article_id, current_vote.vote_type)
        
        # Cập nhật vote counts trong article
        self._update_article_vote_counts(article_id)
        
        # Xóa khỏi vote history
        self._remove_vote_history(user_id, article_id)
        
        return True
    
    def get_user_vote(self, user_id: str, article_id: str) -> Optional[Vote]:
        """
        Lấy vote của user cho article
        Returns: Vote object nếu có, None nếu không có
        """
        upvoted_key = f"{Config.UPVOTED_KEY_PREFIX}{article_id}"
        downvoted_key = f"{Config.DOWNVOTED_KEY_PREFIX}{article_id}"
        
        # Kiểm tra xem user có trong upvoted set không
        if self.redis.sismember(upvoted_key, user_id):
            return Vote(user_id, article_id, VoteType.UPVOTE)
        
        # Kiểm tra xem user có trong downvoted set không
        if self.redis.sismember(downvoted_key, user_id):
            return Vote(user_id, article_id, VoteType.DOWNVOTE)
        
        return None
    
    def can_user_vote(self, user_id: str, article_id: str) -> bool:
        """
        Kiểm tra xem user có thể vote không
        Returns: True nếu có thể vote, False nếu không
        """
        # Kiểm tra xem article có tồn tại không
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        return self.redis.exists(article_key)
    
    def get_voted_users(self, article_id: str) -> Dict[str, List[str]]:
        """
        Lấy danh sách users đã vote cho article
        Returns: Dict với keys 'upvoted' và 'downvoted'
        """
        upvoted_key = f"{Config.UPVOTED_KEY_PREFIX}{article_id}"
        downvoted_key = f"{Config.DOWNVOTED_KEY_PREFIX}{article_id}"
        
        upvoted_users = list(self.redis.smembers(upvoted_key))
        downvoted_users = list(self.redis.smembers(downvoted_key))
        
        return {
            'upvoted': upvoted_users,
            'downvoted': downvoted_users
        }
    
    def get_vote_stats(self, article_id: str) -> Dict[str, int]:
        """
        Lấy thống kê votes cho article
        Returns: Dict với upvotes, downvotes, total
        """
        upvoted_key = f"{Config.UPVOTED_KEY_PREFIX}{article_id}"
        downvoted_key = f"{Config.DOWNVOTED_KEY_PREFIX}{article_id}"
        
        upvotes = self.redis.scard(upvoted_key)
        downvotes = self.redis.scard(downvoted_key)
        
        return {
            'upvotes': upvotes,
            'downvotes': downvotes,
            'total': upvotes - downvotes
        }
    
    def get_user_vote_history(self, user_id: str) -> List[Vote]:
        """
        Lấy lịch sử vote của user
        Returns: List các Vote objects
        """
        user_votes_key = f"{Config.USER_VOTES_PREFIX}{user_id}"
        vote_data = self.redis.hgetall(user_votes_key)
        
        votes = []
        for article_id, vote_info in vote_data.items():
            vote_type_str, timestamp_str = vote_info.split('|')
            vote_type = VoteType.from_string(vote_type_str)
            if vote_type:
                votes.append(Vote(
                    user_id=user_id,
                    article_id=article_id,
                    vote_type=vote_type,
                    timestamp=float(timestamp_str)
                ))
        
        return votes
    
    def _add_vote_to_redis(self, user_id: str, article_id: str, vote_type: VoteType):
        """Helper: Thêm vote vào Redis structures"""
        if vote_type == VoteType.UPVOTE:
            key = f"{Config.UPVOTED_KEY_PREFIX}{article_id}"
        else:
            key = f"{Config.DOWNVOTED_KEY_PREFIX}{article_id}"
        
        self.redis.sadd(key, user_id)
    
    def _remove_vote_from_redis(self, user_id: str, article_id: str, vote_type: VoteType):
        """Helper: Xóa vote khỏi Redis structures"""
        if vote_type == VoteType.UPVOTE:
            key = f"{Config.UPVOTED_KEY_PREFIX}{article_id}"
        else:
            key = f"{Config.DOWNVOTED_KEY_PREFIX}{article_id}"
        
        self.redis.srem(key, user_id)
    
    def _update_article_vote_counts(self, article_id: str):
        """Helper: Cập nhật vote counts trong article Hash"""
        stats = self.get_vote_stats(article_id)
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        
        pipe = self.redis.pipeline()
        pipe.hset(article_key, "upvotes", stats['upvotes'])
        pipe.hset(article_key, "downvotes", stats['downvotes'])
        pipe.execute()
    
    def _save_vote_history(self, user_id: str, article_id: str, vote_type: VoteType):
        """Helper: Lưu vote history"""
        user_votes_key = f"{Config.USER_VOTES_PREFIX}{user_id}"
        vote_info = f"{vote_type.value}|{time.time()}"
        self.redis.hset(user_votes_key, article_id, vote_info)
    
    def _remove_vote_history(self, user_id: str, article_id: str):
        """Helper: Xóa vote history"""
        user_votes_key = f"{Config.USER_VOTES_PREFIX}{user_id}"
        self.redis.hdel(user_votes_key, article_id)
    
    def cleanup_article_votes(self, article_id: str):
        """
        Xóa tất cả votes của article (dùng khi xóa article)
        """
        upvoted_key = f"{Config.UPVOTED_KEY_PREFIX}{article_id}"
        downvoted_key = f"{Config.DOWNVOTED_KEY_PREFIX}{article_id}"
        
        pipe = self.redis.pipeline()
        pipe.delete(upvoted_key)
        pipe.delete(downvoted_key)
        pipe.execute()
        
        # Cũng cần xóa khỏi user vote history
        # Lấy tất cả users đã vote
        voted_users = self.get_voted_users(article_id)
        all_users = set(voted_users['upvoted'] + voted_users['downvoted'])
        
        # Xóa article khỏi vote history của từng user
        for user_id in all_users:
            self._remove_vote_history(user_id, article_id) 