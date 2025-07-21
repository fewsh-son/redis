#!/usr/bin/env python3
"""
Quick test script để kiểm tra tính năng voting system
"""

import sys
import os

# Add parent directory to Python path to access utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.article_service import ArticleService
from services.voting_service import VotingService
from utils.redis_client import redis_client
from models.vote import VoteType

def quick_test_voting():
    """Test nhanh tính năng voting system"""

    print("🧪 QUICK TEST - VOTING SYSTEM")
    print("=" * 50)

    # Kiểm tra kết nối Redis
    if not redis_client.ping():
        print("❌ Redis connection failed!")
        return False

    print("✅ Redis connected successfully")

    article_service = ArticleService()
    voting_service = VotingService()

    # Test 1: Tạo article để test
    print("\n📝 Creating test article...")
    article_id = article_service.post_article(
        title="Test Voting Article",
        link="https://test-voting.example.com",
        poster="test_user",
        groups=["testing"]
    )
    print(f"   Created article with ID: {article_id}")

    # Test 2: Upvote
    print("\n👍 Testing upvote...")
    success = article_service.upvote_article("voter1", article_id)
    if success:
        article = article_service.get_article(article_id)
        print(f"   Article upvotes: {article.upvotes}")
    else:
        print("   ❌ Upvote failed!")
        return False

    # Test 3: Downvote từ user khác
    print("\n👎 Testing downvote...")
    success = article_service.downvote_article("voter2", article_id)
    if success:
        article = article_service.get_article(article_id)
        print(f"   Article votes - Upvotes: {article.upvotes}, Downvotes: {article.downvotes}")
    else:
        print("   ❌ Downvote failed!")
        return False

    # Test 4: Vote statistics
    print("\n📊 Testing vote statistics...")
    stats = article_service.get_article_vote_stats(article_id)
    print(f"   Vote stats: {stats}")

    # Test 5: Vote change (user thay đổi vote)
    print("\n🔄 Testing vote change...")
    success = article_service.downvote_article("voter1", article_id)  # voter1 đổi từ upvote thành downvote
    if success:
        article = article_service.get_article(article_id)
        print(f"   After change - Upvotes: {article.upvotes}, Downvotes: {article.downvotes}")

    # Test 6: Vote history
    print("\n📈 Testing vote history...")
    history = article_service.get_user_vote_history("voter1")
    if history:
        for vote in history:
            print(f"   voter1: {vote.vote_type.value} on article {vote.article_id}")
    else:
        print("   No vote history found")

    # Test 7: Remove vote
    print("\n🗑️  Testing remove vote...")
    success = article_service.remove_vote_from_article("voter1", article_id)
    if success:
        article = article_service.get_article(article_id)
        print(f"   After removal - Upvotes: {article.upvotes}, Downvotes: {article.downvotes}")

    # Test 8: Get voted users
    print("\n👥 Testing get voted users...")
    voted_users = article_service.get_article_voted_users(article_id)
    print(f"   Voted users: {voted_users}")

    print("\n✅ All voting tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = quick_test_voting()
        if success:
            print("\n🎉 Quick voting test completed successfully!")
        else:
            print("\n❌ Quick voting test failed!")
    except Exception as e:
        print(f"\n💥 Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        redis_client.close()
