#!/usr/bin/env python3
"""
Quick test script để kiểm tra posting và fetching articles
"""

import sys
import os

# Add parent directory to Python path to access utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.article_service import ArticleService
from utils.redis_client import redis_client

def quick_test():
    """Test nhanh các tính năng cơ bản"""

    print("🧪 QUICK TEST - POSTING & FETCHING ARTICLES")
    print("=" * 50)

    # Kiểm tra kết nối Redis
    if not redis_client.ping():
        print("❌ Redis connection failed!")
        return False

    print("✅ Redis connected successfully")

    service = ArticleService()

    # Test posting
    print("\n📝 Testing post_article...")
    article_id = service.post_article(
        title="Test Article",
        link="https://test.example.com",
        poster="test_user"
    )
    print(f"   Posted article with ID: {article_id}")

    # Test fetching single article
    print("\n🔍 Testing get_article...")
    article = service.get_article(article_id)
    if article:
        print(f"   Found article: {article.title}")
        print(f"   Score: {article.get_score():.2f}")
    else:
        print("   ❌ Article not found!")
        return False

    # Test fetching recent articles
    print("\n📰 Testing get_recent_articles...")
    recent = service.get_recent_articles(limit=5)
    print(f"   Found {len(recent)} recent articles")

    # Test article count
    print("\n📊 Testing get_article_count...")
    count = service.get_article_count()
    print(f"   Total articles: {count}")

    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = quick_test()
        if success:
            print("\n🎉 Quick test completed successfully!")
        else:
            print("\n❌ Quick test failed!")
    except Exception as e:
        print(f"\n💥 Error during test: {str(e)}")
    finally:
        redis_client.close()
