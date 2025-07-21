#!/usr/bin/env python3
"""
Demo script cho tính năng Posting và Fetching Articles
"""

import sys
import os
import time

# Add parent directory to Python path to access utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.article_service import ArticleService
from utils.redis_client import redis_client

def print_separator(title: str):
    """In dòng phân cách đẹp"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_article(article, index: int = None):
    """In thông tin bài viết đẹp"""
    prefix = f"{index}. " if index is not None else "  "
    print(f"{prefix}📰 {article.title}")
    print(f"    🔗 Link: {article.link}")
    print(f"    👤 Poster: {article.poster}")
    print(f"    ⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(article.time_created))}")
    print(f"    👍 Votes: {article.votes}")
    print(f"    ⭐ Score: {article.get_score():.2f}")
    print(f"    🆔 ID: {article.id}")
    print()

def demo_posting_articles():
    """Demo đăng bài viết"""
    print_separator("🚀 DEMO POSTING ARTICLES")

    service = ArticleService()

    # Danh sách bài viết mẫu
    sample_articles = [
        {
            "title": "Redis Best Practices for Scaling Applications",
            "link": "https://redis.io/docs/manual/scaling/",
            "poster": "redis_admin"
        },
        {
            "title": "Python Redis Integration Tutorial",
            "link": "https://python-redis-tutorial.com",
            "poster": "python_dev"
        },
        {
            "title": "Building Real-time Voting System with Redis",
            "link": "https://realtime-voting.example.com",
            "poster": "system_architect"
        },
        {
            "title": "Redis Data Structures Deep Dive",
            "link": "https://redis-data-structures.dev",
            "poster": "data_engineer"
        },
        {
            "title": "Microservices with Redis as Message Broker",
            "link": "https://microservices-redis.guide",
            "poster": "backend_dev"
        }
    ]

    posted_ids = []

    for i, article_data in enumerate(sample_articles, 1):
        print(f"Đăng bài viết {i}/5...")
        article_id = service.post_article(
            title=article_data["title"],
            link=article_data["link"],
            poster=article_data["poster"]
        )
        posted_ids.append(article_id)

        # Delay nhỏ để có sự khác biệt về thời gian
        time.sleep(0.1)

    print(f"\n✅ Đã đăng thành công {len(posted_ids)} bài viết!")
    return posted_ids

def demo_fetching_articles():
    """Demo lấy bài viết"""
    print_separator("📖 DEMO FETCHING ARTICLES")

    service = ArticleService()

    # 1. Đếm tổng số bài viết
    total_count = service.get_article_count()
    print(f"📊 Tổng số bài viết trong hệ thống: {total_count}")

    # 2. Lấy bài viết mới nhất
    print(f"\n🕒 TOP 3 BÀI VIẾT MỚI NHẤT:")
    recent_articles = service.get_recent_articles(limit=3)
    for i, article in enumerate(recent_articles, 1):
        print_article(article, i)

    # 3. Lấy bài viết theo điểm cao nhất
    print(f"\n⭐ TOP 3 BÀI VIẾT CÓ ĐIỂM CAO NHẤT:")
    top_articles = service.get_top_articles(limit=3)
    for i, article in enumerate(top_articles, 1):
        print_article(article, i)

    # 4. Lấy tất cả bài viết sắp xếp theo thời gian
    print(f"\n📝 TẤT CẢ BÀI VIẾT (SẮP XẾP THEO THỜI GIAN):")
    all_articles = service.get_articles_by_time()
    for i, article in enumerate(all_articles, 1):
        print_article(article, i)

def demo_get_single_article():
    """Demo lấy một bài viết cụ thể"""
    print_separator("🔍 DEMO GET SINGLE ARTICLE")

    service = ArticleService()

    # Lấy bài viết đầu tiên từ danh sách
    recent_articles = service.get_recent_articles(limit=1)

    if recent_articles:
        article = recent_articles[0]
        print(f"🎯 CHI TIẾT BÀI VIẾT:")
        print_article(article)

        # Lấy lại bài viết theo ID để verify
        fetched_article = service.get_article(article.id)
        if fetched_article:
            print(f"✅ Verify: Lấy bài viết theo ID thành công!")
        else:
            print(f"❌ Error: Không thể lấy bài viết theo ID!")
    else:
        print("❌ Không có bài viết nào trong hệ thống!")

def demo_time_range_query():
    """Demo lấy bài viết trong khoảng thời gian"""
    print_separator("⏱️  DEMO TIME RANGE QUERY")

    service = ArticleService()

    # Lấy bài viết trong 1 phút gần đây
    current_time = time.time()
    one_minute_ago = current_time - 60  # 60 seconds ago

    articles = service.get_articles_in_time_range(one_minute_ago, current_time)

    print(f"📅 Bài viết đăng trong 1 phút gần đây: {len(articles)} bài")
    for i, article in enumerate(articles, 1):
        print_article(article, i)

def main():
    """Hàm main chạy demo"""
    print_separator("🎉 REDIS VOTING SYSTEM - ARTICLE DEMO")

    # Kiểm tra kết nối Redis
    if not redis_client.ping():
        print("❌ Không thể kết nối Redis! Vui lòng kiểm tra:")
        print("   - Redis server đã chạy chưa?")
        print("   - Cấu hình connection trong config.py")
        return

    print("✅ Kết nối Redis thành công!")

    try:
        # Chạy các demo
        demo_posting_articles()
        demo_fetching_articles()
        demo_get_single_article()
        demo_time_range_query()

        print_separator("🎊 DEMO HOÀN THÀNH")
        print("Tất cả tính năng posting và fetching articles đã hoạt động!")

    except Exception as e:
        print(f"❌ Lỗi trong quá trình demo: {str(e)}")
        raise

    finally:
        # Đóng kết nối Redis
        redis_client.close()

if __name__ == "__main__":
    main()
