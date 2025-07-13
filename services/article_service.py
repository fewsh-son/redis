from typing import List, Optional, Dict, Any
import uuid
import time
from models.article import Article
from utils.redis_client import redis_client
from config import Config
from services.group_service import GroupService
from services.voting_service import VotingService

class ArticleService:
    """Service xử lý logic posting và fetching articles"""
    
    def __init__(self):
        self.redis = redis_client.client
        self.group_service = GroupService()
        self.voting_service = VotingService()
    
    def post_article(self, title: str, link: str, poster: str, groups: List[str] = None) -> str:
        """
        Đăng bài viết mới
        Returns: article_id
        """
        # Tạo ID duy nhất cho bài viết
        article_id = str(uuid.uuid4())
        
        # Tạo Article object
        article = Article(
            id=article_id,
            title=title,
            link=link,
            poster=poster,
            groups=groups or []
        )
        
        # Pipeline để thực hiện nhiều operations cùng lúc
        pipe = self.redis.pipeline()
        
        # 1. Lưu metadata vào Hash
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        pipe.hmset(article_key, article.to_dict())
        
        # 2. Thêm vào ZSET time (sắp xếp theo thời gian)
        pipe.zadd(Config.TIME_ZSET_KEY, {article_key: article.time_created})
        
        # 3. Thêm vào ZSET score (sắp xếp theo điểm)
        pipe.zadd(Config.SCORE_ZSET_KEY, {article_key: article.get_score()})
        
        # 4. Tạo SET rỗng cho người vote
        voted_key = f"{Config.VOTED_KEY_PREFIX}{article_id}"
        pipe.sadd(voted_key, "dummy")  # Thêm dummy member để tạo set
        pipe.srem(voted_key, "dummy")  # Xóa dummy member ngay lập tức
        
        # Execute pipeline
        pipe.execute()
        
        # 5. Thêm vào groups (nếu có)
        if groups:
            for group_name in groups:
                self.group_service.add_article_to_group(article_id, group_name, article.get_score())
        
        print(f"✅ Đã đăng bài viết: {title} (ID: {article_id})")
        return article_id
    
    def get_article(self, article_id: str) -> Optional[Article]:
        """Lấy thông tin một bài viết theo ID"""
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        data = self.redis.hgetall(article_key)
        
        if not data:
            return None
        
        return Article.from_dict(article_id, data)
    
    def get_articles_by_time(self, start: int = 0, end: int = -1) -> List[Article]:
        """
        Lấy danh sách bài viết sắp xếp theo thời gian (mới nhất trước)
        start: vị trí bắt đầu (0-based)
        end: vị trí kết thúc (-1 = tất cả)
        """
        # Lấy danh sách article keys từ ZSET time (reverse order)
        article_keys = self.redis.zrevrange(Config.TIME_ZSET_KEY, start, end)
        
        return self._get_articles_from_keys(article_keys)
    
    def get_articles_by_score(self, start: int = 0, end: int = -1) -> List[Article]:
        """
        Lấy danh sách bài viết sắp xếp theo điểm (cao nhất trước)
        """
        # Lấy danh sách article keys từ ZSET score (reverse order)
        article_keys = self.redis.zrevrange(Config.SCORE_ZSET_KEY, start, end)
        
        return self._get_articles_from_keys(article_keys)
    
    def get_articles_in_time_range(self, start_time: float, end_time: float) -> List[Article]:
        """Lấy bài viết trong khoảng thời gian"""
        article_keys = self.redis.zrangebyscore(
            Config.TIME_ZSET_KEY, 
            start_time, 
            end_time
        )
        
        return self._get_articles_from_keys(article_keys)
    
    def get_top_articles(self, limit: int = 10) -> List[Article]:
        """Lấy top bài viết có điểm cao nhất"""
        return self.get_articles_by_score(0, limit - 1)
    
    def get_recent_articles(self, limit: int = 10) -> List[Article]:
        """Lấy bài viết gần đây nhất"""
        return self.get_articles_by_time(0, limit - 1)
    
    def _get_articles_from_keys(self, article_keys: List[str]) -> List[Article]:
        """Helper method: lấy thông tin Article từ danh sách keys"""
        if not article_keys:
            return []
        
        articles = []
        
        # Sử dụng pipeline để lấy data của nhiều articles cùng lúc
        pipe = self.redis.pipeline()
        for key in article_keys:
            pipe.hgetall(key)
        
        results = pipe.execute()
        
        # Tạo Article objects
        for i, data in enumerate(results):
            if data:  # Nếu có data
                # Extract article_id từ key
                article_id = article_keys[i].replace(Config.ARTICLE_KEY_PREFIX, "")
                article = Article.from_dict(article_id, data)
                articles.append(article)
        
        return articles
    
    def update_article_score(self, article_id: str):
        """Cập nhật lại score của bài viết trong ZSET và groups"""
        article = self.get_article(article_id)
        if article:
            article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
            new_score = article.get_score()
            
            # Cập nhật ZSET chính
            self.redis.zadd(Config.SCORE_ZSET_KEY, {article_key: new_score})
            
            # Cập nhật score trong tất cả groups
            if article.groups:
                self.group_service.update_article_score_in_groups(article_id, new_score, article.groups)
    
    def delete_article(self, article_id: str) -> bool:
        """Xóa bài viết"""
        # Lấy thông tin article để biết các groups
        article = self.get_article(article_id)
        
        article_key = f"{Config.ARTICLE_KEY_PREFIX}{article_id}"
        voted_key = f"{Config.VOTED_KEY_PREFIX}{article_id}"
        
        pipe = self.redis.pipeline()
        
        # Xóa hash metadata
        pipe.delete(article_key)
        
        # Xóa khỏi ZSET time và score
        pipe.zrem(Config.TIME_ZSET_KEY, article_key)
        pipe.zrem(Config.SCORE_ZSET_KEY, article_key)
        
        # Xóa SET người vote
        pipe.delete(voted_key)
        
        results = pipe.execute()
        
        # Xóa khỏi tất cả groups
        if article and article.groups:
            for group_name in article.groups:
                self.group_service.remove_article_from_group(article_id, group_name)
        
        # Xóa tất cả votes của article
        self.voting_service.cleanup_article_votes(article_id)
        
        # Kiểm tra xem có xóa được không (ít nhất 1 operation thành công)
        return any(results)
    
    def get_article_count(self) -> int:
        """Đếm tổng số bài viết"""
        return self.redis.zcard(Config.TIME_ZSET_KEY)
    
    def get_articles_by_group(self, group_name: str) -> List[Article]:
        """Lấy tất cả articles trong group"""
        article_ids = self.group_service.get_articles_in_group(group_name)
        return [self.get_article(article_id) for article_id in article_ids if self.get_article(article_id)]
    
    def get_articles_by_group_score(self, group_name: str, start: int = 0, end: int = -1) -> List[Article]:
        """Lấy articles trong group sắp xếp theo score"""
        article_ids = self.group_service.get_articles_in_group_by_score(group_name, start, end)
        return [self.get_article(article_id) for article_id in article_ids if self.get_article(article_id)]
    
    def get_top_articles_in_group(self, group_name: str, limit: int = 10) -> List[Article]:
        """Lấy top articles trong group"""
        return self.get_articles_by_group_score(group_name, 0, limit - 1)
    
    def add_article_to_group(self, article_id: str, group_name: str):
        """Thêm article vào group"""
        article = self.get_article(article_id)
        if article:
            # Cập nhật groups trong article
            if group_name not in article.groups:
                article.groups.append(group_name)
                
                # Cập nhật Redis Hash
                self.redis.hset(f"{Config.ARTICLE_KEY_PREFIX}{article_id}", "groups", 
                               ','.join(article.groups))
                
                # Thêm vào group structures
                self.group_service.add_article_to_group(article_id, group_name, article.get_score())
                
                print(f"✅ Đã thêm bài viết {article_id} vào group {group_name}")
                return True
        return False
    
    def remove_article_from_group(self, article_id: str, group_name: str):
        """Xóa article khỏi group"""
        article = self.get_article(article_id)
        if article and group_name in article.groups:
            # Cập nhật groups trong article
            article.groups.remove(group_name)
            
            # Cập nhật Redis Hash
            self.redis.hset(f"{Config.ARTICLE_KEY_PREFIX}{article_id}", "groups", 
                           ','.join(article.groups))
            
            # Xóa khỏi group structures
            self.group_service.remove_article_from_group(article_id, group_name)
            
            print(f"✅ Đã xóa bài viết {article_id} khỏi group {group_name}")
            return True
        return False
    
    def upvote_article(self, user_id: str, article_id: str) -> bool:
        """
        Upvote một bài viết
        Returns: True nếu thành công, False nếu thất bại
        """
        success = self.voting_service.upvote(user_id, article_id)
        if success:
            # Cập nhật score trong ZSETs
            self.update_article_score(article_id)
            print(f"✅ User {user_id} đã upvote bài viết {article_id}")
        return success
    
    def downvote_article(self, user_id: str, article_id: str) -> bool:
        """
        Downvote một bài viết
        Returns: True nếu thành công, False nếu thất bại
        """
        success = self.voting_service.downvote(user_id, article_id)
        if success:
            # Cập nhật score trong ZSETs
            self.update_article_score(article_id)
            print(f"✅ User {user_id} đã downvote bài viết {article_id}")
        return success
    
    def remove_vote_from_article(self, user_id: str, article_id: str) -> bool:
        """
        Xóa vote của user cho article
        Returns: True nếu thành công, False nếu không có vote để xóa
        """
        success = self.voting_service.remove_vote(user_id, article_id)
        if success:
            # Cập nhật score trong ZSETs
            self.update_article_score(article_id)
            print(f"✅ User {user_id} đã xóa vote cho bài viết {article_id}")
        return success
    
    def get_user_vote_for_article(self, user_id: str, article_id: str):
        """
        Lấy vote của user cho article
        Returns: Vote object nếu có, None nếu không có
        """
        return self.voting_service.get_user_vote(user_id, article_id)
    
    def get_article_vote_stats(self, article_id: str) -> Dict[str, int]:
        """
        Lấy thống kê votes cho article
        Returns: Dict với upvotes, downvotes, total
        """
        return self.voting_service.get_vote_stats(article_id)
    
    def get_article_voted_users(self, article_id: str) -> Dict[str, List[str]]:
        """
        Lấy danh sách users đã vote cho article
        Returns: Dict với keys 'upvoted' và 'downvoted'
        """
        return self.voting_service.get_voted_users(article_id)
    
    def get_user_vote_history(self, user_id: str):
        """
        Lấy lịch sử vote của user
        Returns: List các Vote objects
        """
        return self.voting_service.get_user_vote_history(user_id) 