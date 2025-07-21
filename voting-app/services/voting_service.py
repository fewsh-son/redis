from typing import List, Dict, Optional
import time
import sys
import os

# Add parent directory to Python path to access utils
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))

from models.vote import Vote, VoteType
from models.article import Article
from utils.redis_client import redis_client
from config import Config

class VotingService:
    """Service xử lý logic voting (upvote/downvote)"""

    def __init__(self):
        self.redis = redis_client.client

    def upvote(self, user_id: str, article_id: str) -> bool:
        """
        Upvote một bài viết
        Returns: True nếu thành công, False nếu thất bại
        """
        # Kiểm tra user có thể vote không
        if not self.can_user_vote(user_id, article_id):
            print(f"❌ User {user_id} không thể upvote bài viết {article_id}")
            return False

        # Xóa vote cũ nếu có
        current_vote = self.get_user_vote(user_id, article_id)
        if current_vote:
            self._remove_vote_from_sets(user_id, article_id, current_vote.vote_type)

        pipe = self.redis.pipeline()

        # Thêm vào upvoted set
        upvoted_key = f"{Config.UPVOTED_KEY_PREFIX}{article_id}"
        pipe.sadd(upvoted_key, user_id)

        # Cập nhật upvotes trong article hash
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        pipe.hincrby(article_key, "upvotes", 1)

        # Nếu user đã downvote trước đó, giảm downvotes
        if current_vote and current_vote.vote_type == VoteType.DOWNVOTE:
            pipe.hincrby(article_key, "downvotes", -1)

        # Lưu vote history
        self._save_user_vote_history(user_id, article_id, VoteType.UPVOTE, pipe)

        pipe.execute()
        return True

    def downvote(self, user_id: str, article_id: str) -> bool:
        """
        Downvote một bài viết
        Returns: True nếu thành công, False nếu thất bại
        """
        # Kiểm tra user có thể vote không
        if not self.can_user_vote(user_id, article_id):
            print(f"❌ User {user_id} không thể downvote bài viết {article_id}")
            return False

        # Xóa vote cũ nếu có
        current_vote = self.get_user_vote(user_id, article_id)
        if current_vote:
            self._remove_vote_from_sets(user_id, article_id, current_vote.vote_type)

        pipe = self.redis.pipeline()

        # Thêm vào downvoted set
        downvoted_key = f"{Config.DOWNVOTED_KEY_PREFIX}{article_id}"
        pipe.sadd(downvoted_key, user_id)

        # Cập nhật downvotes trong article hash
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        pipe.hincrby(article_key, "downvotes", 1)

        # Nếu user đã upvote trước đó, giảm upvotes
        if current_vote and current_vote.vote_type == VoteType.UPVOTE:
            pipe.hincrby(article_key, "upvotes", -1)

        # Lưu vote history
        self._save_user_vote_history(user_id, article_id, VoteType.DOWNVOTE, pipe)

        pipe.execute()
        return True

    def remove_vote(self, user_id: str, article_id: str) -> bool:
        """
        Xóa vote của user cho article
        Returns: True nếu thành công, False nếu không có vote để xóa
        """
        current_vote = self.get_user_vote(user_id, article_id)
        if not current_vote:
            return False

        # Xóa từ vote sets
        self._remove_vote_from_sets(user_id, article_id, current_vote.vote_type)

        # Cập nhật vote counts trong article hash
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        if current_vote.vote_type == VoteType.UPVOTE:
            self.redis.hincrby(article_key, "upvotes", -1)
        else:
            self.redis.hincrby(article_key, "downvotes", -1)

        # Xóa từ vote history
        user_votes_key = f"{Config.USER_VOTES_PREFIX}{user_id}"
        self.redis.hdel(user_votes_key, article_id)

        return True

    def get_user_vote(self, user_id: str, article_id: str) -> Optional[Vote]:
        """
        Lấy vote của user cho article
        Returns: Vote object nếu có, None nếu không có
        """
        user_votes_key = f"{Config.USER_VOTES_PREFIX}{user_id}"
        vote_data = self.redis.hget(user_votes_key, article_id)

        if vote_data:
            return Vote.from_string(user_id, article_id, vote_data)

        return None

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

    def get_user_vote_history(self, user_id: str) -> List[Vote]:
        """
        Lấy lịch sử vote của user
        Returns: List các Vote objects
        """
        user_votes_key = f"{Config.USER_VOTES_PREFIX}{user_id}"
        vote_data = self.redis.hgetall(user_votes_key)

        votes = []
        for article_id, vote_string in vote_data.items():
            vote = Vote.from_string(user_id, article_id, vote_string)
            if vote:
                votes.append(vote)

        # Sắp xếp theo thời gian (mới nhất trước)
        return sorted(votes, key=lambda v: v.timestamp, reverse=True)

    def can_user_vote(self, user_id: str, article_id: str) -> bool:
        """
        Kiểm tra xem user có thể vote cho article không
        Returns: True nếu có thể vote (bao gồm thay đổi vote)
        """
        # Ở đây có thể thêm logic phức tạp hơn như:
        # - Kiểm tra user có tồn tại không
        # - Kiểm tra article có tồn tại không
        # - Kiểm tra rate limiting
        # - Etc.

        # Hiện tại chỉ kiểm tra article có tồn tại
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        return self.redis.exists(article_key)

    def cleanup_article_votes(self, article_id: str):
        """
        Xóa tất cả votes liên quan đến article (khi delete article)
        """
        upvoted_key = f"{Config.UPVOTED_KEY_PREFIX}{article_id}"
        downvoted_key = f"{Config.DOWNVOTED_KEY_PREFIX}{article_id}"

        # Lấy danh sách users đã vote
        upvoted_users = self.redis.smembers(upvoted_key)
        downvoted_users = self.redis.smembers(downvoted_key)
        all_users = upvoted_users.union(downvoted_users)

        pipe = self.redis.pipeline()

        # Xóa vote sets của article
        pipe.delete(upvoted_key)
        pipe.delete(downvoted_key)

        # Xóa vote history của từng user
        for user_id in all_users:
            user_votes_key = f"{Config.USER_VOTES_PREFIX}{user_id}"
            pipe.hdel(user_votes_key, article_id)

        pipe.execute()

    def _remove_vote_from_sets(self, user_id: str, article_id: str, vote_type: VoteType):
        """Helper method: xóa vote khỏi vote sets"""
        upvoted_key = f"{Config.UPVOTED_KEY_PREFIX}{article_id}"
        downvoted_key = f"{Config.DOWNVOTED_KEY_PREFIX}{article_id}"

        # Xóa khỏi cả hai sets (tránh trường hợp data inconsistent)
        pipe = self.redis.pipeline()
        pipe.srem(upvoted_key, user_id)
        pipe.srem(downvoted_key, user_id)
        pipe.execute()

    def _save_user_vote_history(self, user_id: str, article_id: str, vote_type: VoteType, pipe=None):
        """Helper method: lưu vote history của user"""
        user_votes_key = f"{Config.USER_VOTES_PREFIX}{user_id}"
        vote_string = f"{vote_type.value}|{time.time()}"

        if pipe:
            pipe.hset(user_votes_key, article_id, vote_string)
        else:
            self.redis.hset(user_votes_key, article_id, vote_string)
