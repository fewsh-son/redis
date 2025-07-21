#!/usr/bin/env python3
"""
Demo script cho tính năng Voting System
"""

import sys
import os
import time

# Add parent directory to Python path to access utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.article_service import ArticleService
from services.voting_service import VotingService
from utils.redis_client import redis_client

def print_separator(title: str):
    """In dòng phân cách đẹp"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_article_with_votes(article, index: int = None):
    """In thông tin bài viết với vote stats"""
    prefix = f"{index}. " if index is not None else "  "

    print(f"{prefix}📰 {article.title}")
    print(f"    🔗 Link: {article.link}")
    print(f"    👤 Poster: {article.poster}")
    print(f"    👍 Upvotes: {article.upvotes}")
    print(f"    👎 Downvotes: {article.downvotes}")
    print(f"    📊 Total Votes: {article.votes}")
    print(f"    ⭐ Score: {article.get_score():.2f}")
    if article.groups:
        print(f"    🏷️  Groups: {', '.join(article.groups)}")
    print(f"    🆔 ID: {article.id}")
    print()

def demo_setup_articles():
    """Demo tạo articles để test voting"""
    print_separator("🚀 SETUP ARTICLES FOR VOTING DEMO")

    service = ArticleService()

    # Tạo một vài bài viết để test
    articles_data = [
        {
            "title": "Redis Voting System Implementation",
            "link": "https://redis-voting.example.com",
            "poster": "system_dev",
            "groups": ["programming", "redis"]
        },
        {
            "title": "Python Data Structures Guide",
            "link": "https://python-ds.guide.com",
            "poster": "python_expert",
            "groups": ["programming", "python"]
        },
        {
            "title": "Microservices Architecture Best Practices",
            "link": "https://microservices-guide.dev",
            "poster": "architect",
            "groups": ["architecture", "cloud"]
        }
    ]

    posted_ids = []
    for article_data in articles_data:
        print(f"Tạo article: {article_data['title']}")
        article_id = service.post_article(
            title=article_data["title"],
            link=article_data["link"],
            poster=article_data["poster"],
            groups=article_data["groups"]
        )
        posted_ids.append(article_id)
        time.sleep(0.1)

    print(f"\n✅ Đã tạo {len(posted_ids)} articles cho voting demo")
    return posted_ids

def demo_basic_voting():
    """Demo basic voting operations"""
    print_separator("👍👎 DEMO BASIC VOTING")

    service = ArticleService()
    voting_service = VotingService()

    # Lấy articles để test
    recent_articles = service.get_recent_articles(limit=3)
    if not recent_articles:
        print("❌ Không có articles để test voting!")
        return

    article = recent_articles[0]
    print(f"🎯 Testing với article: {article.title}")
    print_article_with_votes(article)

    # Test upvote
    print("Test upvote từ user1...")
    success = service.upvote_article("user1", article.id)
    if success:
        updated_article = service.get_article(article.id)
        print_article_with_votes(updated_article)

    # Test downvote từ user khác
    print("Test downvote từ user2...")
    success = service.downvote_article("user2", article.id)
    if success:
        updated_article = service.get_article(article.id)
        print_article_with_votes(updated_article)

    # Test thêm upvotes
    print("Test thêm upvotes từ user3, user4...")
    service.upvote_article("user3", article.id)
    service.upvote_article("user4", article.id)

    final_article = service.get_article(article.id)
    print("📊 Kết quả cuối cùng:")
    print_article_with_votes(final_article)

def demo_vote_changes():
    """Demo thay đổi vote (upvote -> downvote và ngược lại)"""
    print_separator("🔄 DEMO VOTE CHANGES")

    service = ArticleService()

    # Lấy article thứ 2
    recent_articles = service.get_recent_articles(limit=3)
    if len(recent_articles) < 2:
        print("❌ Không đủ articles để test!")
        return

    article = recent_articles[1]
    print(f"🎯 Testing với article: {article.title}")

    # User5 upvote trước
    print("User5 upvote article...")
    service.upvote_article("user5", article.id)
    updated_article = service.get_article(article.id)
    print_article_with_votes(updated_article)

    # User5 đổi thành downvote
    print("User5 đổi thành downvote...")
    service.downvote_article("user5", article.id)
    updated_article = service.get_article(article.id)
    print_article_with_votes(updated_article)

    # User5 remove vote
    print("User5 xóa vote...")
    service.remove_vote_from_article("user5", article.id)
    final_article = service.get_article(article.id)
    print_article_with_votes(final_article)

def demo_prevent_double_voting():
    """Demo ngăn chặn double voting"""
    print_separator("🚫 DEMO PREVENT DOUBLE VOTING")

    service = ArticleService()
    voting_service = VotingService()

    recent_articles = service.get_recent_articles(limit=3)
    if len(recent_articles) < 3:
        print("❌ Không đủ articles để test!")
        return

    article = recent_articles[2]
    print(f"🎯 Testing với article: {article.title}")

    # User6 vote lần đầu
    print("User6 upvote lần đầu...")
    success1 = service.upvote_article("user6", article.id)
    print(f"Kết quả: {success1}")

    # Check vote của user6
    user_vote = service.get_user_vote_for_article("user6", article.id)
    if user_vote:
        print(f"Vote hiện tại của user6: {user_vote.vote_type.value}")

    # User6 cố gắng upvote lại (sẽ không tăng thêm)
    print("User6 cố upvote lại (không nên tăng thêm)...")
    success2 = service.upvote_article("user6", article.id)
    print(f"Kết quả: {success2}")

    final_article = service.get_article(article.id)
    print_article_with_votes(final_article)

def demo_vote_history():
    """Demo vote history của user"""
    print_separator("📈 DEMO VOTE HISTORY")

    service = ArticleService()

    # Lấy vote history của các users
    users_to_check = ["user1", "user2", "user3", "user5"]

    for user_id in users_to_check:
        print(f"\n👤 Vote history của {user_id}:")
        vote_history = service.get_user_vote_history(user_id)

        if vote_history:
            for vote in vote_history:
                article = service.get_article(vote.article_id)
                article_title = article.title if article else "Unknown Article"
                print(f"  {vote.vote_type.value} - {article_title[:50]}...")
        else:
            print("  Chưa có vote nào")

def demo_article_ranking():
    """Demo ranking articles theo votes"""
    print_separator("🏆 DEMO ARTICLE RANKING BY VOTES")

    service = ArticleService()

    # Lấy top articles theo score
    print("🥇 TOP ARTICLES BY SCORE:")
    top_articles = service.get_top_articles(limit=5)

    for i, article in enumerate(top_articles, 1):
        print_article_with_votes(article, i)

def demo_vote_stats():
    """Demo thống kê votes cho articles"""
    print_separator("📊 DEMO VOTE STATISTICS")

    service = ArticleService()

    recent_articles = service.get_recent_articles(limit=3)

    for article in recent_articles:
        print(f"\n📰 {article.title}")

        # Lấy vote stats
        vote_stats = service.get_article_vote_stats(article.id)
        print(f"   📊 Stats: {vote_stats}")

        # Lấy danh sách users đã vote
        voted_users = service.get_article_voted_users(article.id)
        print(f"   👍 Upvoted users: {voted_users['upvoted']}")
        print(f"   👎 Downvoted users: {voted_users['downvoted']}")

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
        demo_article_ranking()
        demo_vote_stats()

        print_separator("🎊 VOTING DEMO HOÀN THÀNH")
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
