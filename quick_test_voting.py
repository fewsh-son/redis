#!/usr/bin/env python3
"""
Quick test script để kiểm tra tính năng voting system
"""

from services.article_service import ArticleService
from services.voting_service import VotingService
from models.vote import VoteType
from utils.redis_client import redis_client

def quick_test_voting():
    """Test nhanh tính năng voting"""
    
    print("🧪 QUICK TEST - VOTING SYSTEM")
    print("=" * 50)
    
    # Kiểm tra kết nối Redis
    if not redis_client.ping():
        print("❌ Redis connection failed!")
        return False
    
    print("✅ Redis connected successfully")
    
    article_service = ArticleService()
    voting_service = VotingService()
    
    # Test 1: Tạo article để voting
    print("\n📝 Testing article creation...")
    article_id = article_service.post_article(
        title="Test Article for Voting",
        link="https://test-voting.example.com",
        poster="test_user",
        groups=["testing"]
    )
    print(f"   Created article with ID: {article_id}")
    
    # Test 2: Upvote article
    print("\n👍 Testing upvote...")
    success = article_service.upvote_article("user1", article_id)
    if success:
        article = article_service.get_article(article_id)
        print(f"   ✅ Upvote successful! Upvotes: {article.upvotes}")
    else:
        print("   ❌ Upvote failed!")
        return False
    
    # Test 3: Downvote article
    print("\n👎 Testing downvote...")
    success = article_service.downvote_article("user2", article_id)
    if success:
        article = article_service.get_article(article_id)
        print(f"   ✅ Downvote successful! Downvotes: {article.downvotes}")
    else:
        print("   ❌ Downvote failed!")
        return False
    
    # Test 4: Check vote stats
    print("\n📊 Testing vote stats...")
    stats = article_service.get_article_vote_stats(article_id)
    print(f"   Upvotes: {stats['upvotes']}")
    print(f"   Downvotes: {stats['downvotes']}")
    print(f"   Total: {stats['total']}")
    
    # Test 5: Check user vote
    print("\n🔍 Testing get user vote...")
    user_vote = article_service.get_user_vote_for_article("user1", article_id)
    if user_vote:
        print(f"   User1 vote: {user_vote.vote_type}")
    else:
        print("   ❌ No vote found!")
        return False
    
    # Test 6: Test vote change
    print("\n🔄 Testing vote change...")
    success = article_service.downvote_article("user1", article_id)  # Change from upvote to downvote
    if success:
        user_vote = article_service.get_user_vote_for_article("user1", article_id)
        print(f"   ✅ Vote changed to: {user_vote.vote_type}")
    else:
        print("   ❌ Vote change failed!")
        return False
    
    # Test 7: Test prevent double voting
    print("\n🚫 Testing prevent double voting...")
    success = article_service.downvote_article("user1", article_id)  # Try to downvote again
    if not success:
        print("   ✅ Double voting prevented!")
    else:
        print("   ❌ Double voting not prevented!")
        return False
    
    # Test 8: Test remove vote
    print("\n➖ Testing remove vote...")
    success = article_service.remove_vote_from_article("user1", article_id)
    if success:
        user_vote = article_service.get_user_vote_for_article("user1", article_id)
        print(f"   ✅ Vote removed! Current vote: {user_vote.vote_type if user_vote else 'None'}")
    else:
        print("   ❌ Remove vote failed!")
        return False
    
    # Test 9: Test vote history
    print("\n📚 Testing vote history...")
    # Create some vote history
    article_service.upvote_article("user_history", article_id)
    vote_history = article_service.get_user_vote_history("user_history")
    print(f"   Vote history entries: {len(vote_history)}")
    
    # Test 10: Test voted users
    print("\n👥 Testing voted users...")
    voted_users = article_service.get_article_voted_users(article_id)
    print(f"   Upvoted users: {len(voted_users['upvoted'])}")
    print(f"   Downvoted users: {len(voted_users['downvoted'])}")
    
    # Test 11: Test final article state
    print("\n📰 Testing final article state...")
    final_article = article_service.get_article(article_id)
    print(f"   Final upvotes: {final_article.upvotes}")
    print(f"   Final downvotes: {final_article.downvotes}")
    print(f"   Final total votes: {final_article.votes}")
    print(f"   Final score: {final_article.get_score():.2f}")
    
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