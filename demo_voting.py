#!/usr/bin/env python3
"""
Demo script cho tính năng Voting System (Upvote/Downvote)
"""

from services.article_service import ArticleService
from services.voting_service import VotingService
from models.vote import VoteType
from utils.redis_client import redis_client
import time

def print_separator(title: str):
    """In dòng phân cách đẹp"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_article_with_votes(article, index: int = None):
    """In thông tin bài viết với votes"""
    prefix = f"{index}. " if index is not None else "  "
    groups_str = f"🏷️  Groups: {', '.join(article.groups)}" if article.groups else "🏷️  Groups: None"
    
    print(f"{prefix}📰 {article.title}")
    print(f"    🔗 Link: {article.link}")
    print(f"    👤 Poster: {article.poster}")
    print(f"    ⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(article.time_created))}")
    print(f"    👍 Upvotes: {article.upvotes}")
    print(f"    👎 Downvotes: {article.downvotes}")
    print(f"    📊 Total: {article.votes}")
    print(f"    ⭐ Score: {article.get_score():.2f}")
    print(f"    {groups_str}")
    print(f"    🆔 ID: {article.id}")
    print()

def print_vote_stats(article_id: str, service: ArticleService):
    """In thống kê votes của article"""
    stats = service.get_article_vote_stats(article_id)
    voted_users = service.get_article_voted_users(article_id)
    
    print(f"📊 VOTE STATS:")
    print(f"   👍 Upvotes: {stats['upvotes']}")
    print(f"   👎 Downvotes: {stats['downvotes']}")
    print(f"   📊 Total: {stats['total']}")
    print(f"   👥 Users upvoted: {', '.join(voted_users['upvoted']) if voted_users['upvoted'] else 'None'}")
    print(f"   👥 Users downvoted: {', '.join(voted_users['downvoted']) if voted_users['downvoted'] else 'None'}")
    print()

def demo_setup_articles():
    """Demo tạo articles để voting"""
    print_separator("🚀 DEMO SETUP - CREATING ARTICLES")
    
    service = ArticleService()
    
    # Tạo vài bài viết để demo voting
    sample_articles = [
        {
            "title": "Redis vs MongoDB: Performance Comparison",
            "link": "https://redis-vs-mongodb.com",
            "poster": "db_expert",
            "groups": ["database", "performance"]
        },
        {
            "title": "Python Async/Await Best Practices",
            "link": "https://python-async-guide.dev",
            "poster": "python_guru",
            "groups": ["programming", "python"]
        },
        {
            "title": "Building Scalable Microservices",
            "link": "https://microservices-guide.com",
            "poster": "architect",
            "groups": ["architecture", "microservices"]
        }
    ]
    
    article_ids = []
    for i, article_data in enumerate(sample_articles, 1):
        print(f"Tạo bài viết {i}/{len(sample_articles)}...")
        article_id = service.post_article(
            title=article_data["title"],
            link=article_data["link"],
            poster=article_data["poster"],
            groups=article_data["groups"]
        )
        article_ids.append(article_id)
        time.sleep(0.1)
    
    print(f"\n✅ Đã tạo {len(article_ids)} bài viết để demo voting!")
    return article_ids

def demo_basic_voting():
    """Demo upvote/downvote cơ bản"""
    print_separator("👍👎 DEMO BASIC VOTING")
    
    service = ArticleService()
    
    # Lấy bài viết gần đây nhất
    recent_articles = service.get_recent_articles(limit=1)
    if not recent_articles:
        print("❌ Không có bài viết nào để vote!")
        return
    
    article = recent_articles[0]
    print(f"🎯 Bài viết để demo: {article.title}")
    print(f"   Initial state:")
    print_article_with_votes(article)
    
    print(f"📝 DEMO VOTING ACTIONS:")
    
    # User 1 upvote
    print("   👤 user1 upvote...")
    success = service.upvote_article("user1", article.id)
    if success:
        updated_article = service.get_article(article.id)
        print(f"      ✅ Success! New upvotes: {updated_article.upvotes}")
    
    # User 2 upvote
    print("   👤 user2 upvote...")
    service.upvote_article("user2", article.id)
    
    # User 3 downvote
    print("   👤 user3 downvote...")
    service.downvote_article("user3", article.id)
    
    # User 4 upvote
    print("   👤 user4 upvote...")
    service.upvote_article("user4", article.id)
    
    # User 5 downvote
    print("   👤 user5 downvote...")
    service.downvote_article("user5", article.id)
    
    # Xem kết quả
    print(f"\n🎊 AFTER VOTING:")
    final_article = service.get_article(article.id)
    print_article_with_votes(final_article)
    
    print_vote_stats(article.id, service)

def demo_vote_changes():
    """Demo thay đổi vote (upvote -> downvote)"""
    print_separator("🔄 DEMO VOTE CHANGES")
    
    service = ArticleService()
    
    # Lấy bài viết
    recent_articles = service.get_recent_articles(limit=1)
    if not recent_articles:
        return
    
    article = recent_articles[0]
    print(f"🎯 Bài viết: {article.title}")
    
    # User upvote trước
    print("   👤 user_change upvote...")
    service.upvote_article("user_change", article.id)
    
    # Xem vote của user
    user_vote = service.get_user_vote_for_article("user_change", article.id)
    print(f"      Current vote: {user_vote.vote_type if user_vote else 'None'}")
    
    # User change thành downvote
    print("   👤 user_change change to downvote...")
    service.downvote_article("user_change", article.id)
    
    # Xem vote mới
    user_vote = service.get_user_vote_for_article("user_change", article.id)
    print(f"      New vote: {user_vote.vote_type if user_vote else 'None'}")
    
    # User remove vote
    print("   👤 user_change remove vote...")
    service.remove_vote_from_article("user_change", article.id)
    
    user_vote = service.get_user_vote_for_article("user_change", article.id)
    print(f"      Final vote: {user_vote.vote_type if user_vote else 'None'}")

def demo_prevent_double_voting():
    """Demo ngăn chặn double voting"""
    print_separator("🚫 DEMO PREVENT DOUBLE VOTING")
    
    service = ArticleService()
    
    # Lấy bài viết
    recent_articles = service.get_recent_articles(limit=1)
    if not recent_articles:
        return
    
    article = recent_articles[0]
    print(f"🎯 Bài viết: {article.title}")
    
    # User upvote lần đầu
    print("   👤 user_double upvote lần 1...")
    success1 = service.upvote_article("user_double", article.id)
    print(f"      Result: {'✅ Success' if success1 else '❌ Failed'}")
    
    # User upvote lần 2 (sẽ bị chặn)
    print("   👤 user_double upvote lần 2...")
    success2 = service.upvote_article("user_double", article.id)
    print(f"      Result: {'✅ Success' if success2 else '❌ Failed (prevented double voting)'}")
    
    # Xem vote hiện tại
    user_vote = service.get_user_vote_for_article("user_double", article.id)
    print(f"      Current vote: {user_vote.vote_type if user_vote else 'None'}")

def demo_vote_history():
    """Demo lịch sử vote của user"""
    print_separator("📚 DEMO VOTE HISTORY")
    
    service = ArticleService()
    
    # Lấy nhiều bài viết
    recent_articles = service.get_recent_articles(limit=3)
    if len(recent_articles) < 2:
        print("❌ Cần ít nhất 2 bài viết để demo vote history!")
        return
    
    # User vote cho nhiều bài viết
    print("   👤 user_history voting on multiple articles...")
    service.upvote_article("user_history", recent_articles[0].id)
    service.downvote_article("user_history", recent_articles[1].id)
    if len(recent_articles) > 2:
        service.upvote_article("user_history", recent_articles[2].id)
    
    # Xem lịch sử vote
    vote_history = service.get_user_vote_history("user_history")
    print(f"\n📖 Vote history của user_history:")
    for vote in vote_history:
        print(f"   - Article {vote.article_id}: {vote.vote_type.value} at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(vote.timestamp))}")

def demo_article_ranking_by_votes():
    """Demo ranking articles theo votes"""
    print_separator("🏆 DEMO ARTICLE RANKING BY VOTES")
    
    service = ArticleService()
    
    # Lấy tất cả bài viết và sắp xếp theo score
    top_articles = service.get_top_articles(limit=10)
    
    print("🏆 TOP ARTICLES BY SCORE:")
    for i, article in enumerate(top_articles, 1):
        print_article_with_votes(article, i)

def demo_group_voting():
    """Demo voting trong groups"""
    print_separator("🏷️  DEMO GROUP VOTING")
    
    service = ArticleService()
    
    # Lấy articles trong group programming
    programming_articles = service.get_top_articles_in_group("programming", limit=3)
    
    if programming_articles:
        print("🏷️  TOP PROGRAMMING ARTICLES:")
        for i, article in enumerate(programming_articles, 1):
            print_article_with_votes(article, i)
    else:
        print("❌ Không có bài viết nào trong group programming!")

def main():
    """Hàm main chạy demo"""
    print_separator("🎉 REDIS VOTING SYSTEM - VOTING DEMO")
    
    # Kiểm tra kết nối Redis
    if not redis_client.ping():
        print("❌ Không thể kết nối Redis! Vui lòng kiểm tra:")
        print("   - Redis server đã chạy chưa?")
        print("   - Cấu hình connection trong config.py")
        return
    
    print("✅ Kết nối Redis thành công!")
    
    try:
        # Chạy các demo
        demo_setup_articles()
        demo_basic_voting()
        demo_vote_changes()
        demo_prevent_double_voting()
        demo_vote_history()
        demo_article_ranking_by_votes()
        demo_group_voting()
        
        print_separator("🎊 DEMO VOTING HOÀN THÀNH")
        print("Tất cả tính năng voting system đã hoạt động!")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình demo: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Đóng kết nối Redis
        redis_client.close()

if __name__ == "__main__":
    main() 