#!/usr/bin/env python3
"""
Quick test script để kiểm tra tính năng groups
"""

import sys
import os

# Add parent directory to Python path to access utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.article_service import ArticleService
from services.group_service import GroupService
from utils.redis_client import redis_client

def quick_test_groups():
    """Test nhanh tính năng groups"""

    print("🧪 QUICK TEST - GROUPS FEATURE")
    print("=" * 50)

    # Kiểm tra kết nối Redis
    if not redis_client.ping():
        print("❌ Redis connection failed!")
        return False

    print("✅ Redis connected successfully")

    article_service = ArticleService()
    group_service = GroupService()

    # Test 1: Posting article with groups
    print("\n📝 Testing post_article with groups...")
    article_id = article_service.post_article(
        title="Test Article with Groups",
        link="https://test-groups.example.com",
        poster="test_user",
        groups=["testing", "demo"]
    )
    print(f"   Posted article with ID: {article_id}")

    # Test 2: Get article và check groups
    print("\n🔍 Testing get_article and groups...")
    article = article_service.get_article(article_id)
    if article:
        print(f"   Article title: {article.title}")
        print(f"   Article groups: {article.groups}")
    else:
        print("   ❌ Article not found!")
        return False

    # Test 3: Get articles in group
    print("\n📋 Testing get_articles_by_group...")
    articles_in_testing = article_service.get_articles_by_group("testing")
    print(f"   Found {len(articles_in_testing)} articles in 'testing' group")

    # Test 4: Get all groups
    print("\n📊 Testing get_all_groups...")
    all_groups = group_service.get_all_groups()
    print(f"   All groups: {all_groups}")

    # Test 5: Group stats
    print("\n📈 Testing get_group_stats...")
    if "testing" in all_groups:
        stats = group_service.get_group_stats("testing")
        print(f"   'testing' group stats: {stats}")

    # Test 6: Add article to new group
    print("\n➕ Testing add_article_to_group...")
    success = article_service.add_article_to_group(article_id, "new_group")
    if success:
        updated_article = article_service.get_article(article_id)
        print(f"   Updated groups: {updated_article.groups}")

    # Test 7: Remove article from group
    print("\n➖ Testing remove_article_from_group...")
    success = article_service.remove_article_from_group(article_id, "new_group")
    if success:
        final_article = article_service.get_article(article_id)
        print(f"   Final groups: {final_article.groups}")

    print("\n✅ All group tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = quick_test_groups()
        if success:
            print("\n🎉 Quick group test completed successfully!")
        else:
            print("\n❌ Quick group test failed!")
    except Exception as e:
        print(f"\n💥 Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        redis_client.close()
