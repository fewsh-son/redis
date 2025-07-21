#!/usr/bin/env python3
"""
Quick test script - Basic functionality test
"""

import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.redis_client import redis_client
from services.auth_service import AuthService
from services.session_service import SessionService

def quick_test():
    """Test nhanh các tính năng cơ bản"""

    print("🧪 QUICK TEST - LOGIN COOKIE CACHE SYSTEM")
    print("=" * 50)

    # Check Redis connection
    if not redis_client.ping():
        print("❌ Redis connection failed!")
        return False

    print("✅ Redis connected successfully")

    auth_service = AuthService()
    session_service = SessionService()

    try:
        # Test 1: Register user
        print("\n📝 Testing user registration...")
        success, msg = auth_service.register_user("testuser", "test@example.com", "password123")
        if success:
            print(f"   ✅ Registration: {msg}")
        else:
            print(f"   ❌ Registration failed: {msg}")
            return False

        # Test 2: Login
        print("\n🔑 Testing login...")
        success, session_token, msg = auth_service.login("testuser", "password123")
        if success and session_token:
            print(f"   ✅ Login successful")
            print(f"   📋 Session token: {session_token[:16]}...")
        else:
            print(f"   ❌ Login failed: {msg}")
            return False

        # Test 3: Session validation
        print("\n🔍 Testing session validation...")
        is_valid = auth_service.validate_session(session_token)
        if is_valid:
            print("   ✅ Session validation passed")
        else:
            print("   ❌ Session validation failed")
            return False

        # Test 4: Session updates
        print("\n📊 Testing session updates...")
        success = session_service.update_session_activity(session_token, "/test-page")
        if success:
            session_data = session_service.get_session(session_token)
            print(f"   ✅ Session updated")
            print(f"   📄 Current page: {session_data.get('current_page', 'N/A')}")
            print(f"   👀 Page views: {session_data.get('page_views', 0)}")
        else:
            print("   ❌ Session update failed")
            return False

        # Test 5: Shopping cart
        print("\n🛒 Testing shopping cart...")
        success = session_service.add_to_cart(session_token, "item123", "Test Product", 2, 29.99)
        if success:
            cart_data = session_service.get_cart(session_token)
            print(f"   ✅ Item added to cart")
            print(f"   📦 Total items: {cart_data.get('total_items', 0)}")
            print(f"   💰 Total value: ${cart_data.get('total_value', '0.00')}")
        else:
            print("   ❌ Cart update failed")
            return False

        # Test 6: Performance test
        print("\n⚡ Testing performance (100 rapid updates)...")
        start_time = __import__('time').time()
        session_service.simulate_high_load_update(session_token, 100)
        end_time = __import__('time').time()
        duration = end_time - start_time
        ops_per_second = 100 / duration if duration > 0 else 0
        print(f"   ⚡ Performance: {ops_per_second:.0f} operations/second")

        # Test 7: Session statistics
        print("\n📈 Testing session statistics...")
        stats = session_service.get_session_stats()
        print(f"   📊 Active sessions: {stats['active_sessions']}")
        print(f"   🛒 Active carts: {stats['active_carts']}")
        print(f"   💾 Memory used: {stats['memory_used']}")

        # Test 8: Logout
        print("\n👋 Testing logout...")
        success = auth_service.logout(session_token)
        if success:
            print("   ✅ Logout successful")
        else:
            print("   ❌ Logout failed")
            return False

        print("\n🎉 ALL TESTS PASSED!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        try:
            auth_service.cleanup_test_users("testuser", 1)
            print("🧹 Test cleanup completed")
        except:
            pass

if __name__ == "__main__":
    success = quick_test()
    redis_client.close()
    exit(0 if success else 1)
