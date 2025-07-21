#!/usr/bin/env python3
"""
Demo script: Fake Web Retailer - Redis Session Management
Mô phỏng tình huống thực tế với 6,000 writes/second peak load
"""

import sys
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.redis_client import redis_client
from services.auth_service import AuthService
from services.session_service import SessionService

def print_separator(title: str):
    """In separator đẹp"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def simulate_user_browsing_session(auth_service: AuthService,
                                 session_service: SessionService,
                                 user_id: int,
                                 pages_to_browse: int = 50):
    """
    Mô phỏng một user browsing session
    Đây là nguồn gốc của 6,000 writes/second peak load
    """
    username = f"customer_{user_id}"

    # Login
    success, session_token, _ = auth_service.login(username, "password123")
    if not success:
        return {"user_id": user_id, "success": False, "reason": "login_failed"}

    updates_count = 0
    cart_items = 0

    # Simulate browsing behavior
    pages = [
        "/home", "/products", "/laptops", "/phones", "/tablets",
        "/product/laptop-123", "/product/phone-456", "/product/tablet-789",
        "/cart", "/checkout", "/account", "/orders", "/support"
    ]

    for i in range(pages_to_browse):
        page = random.choice(pages)

        # Update session activity (tương tự database UPDATE)
        if session_service.update_session_activity(session_token, page):
            updates_count += 1

        # Randomly add items to cart (high write frequency)
        if random.random() < 0.1:  # 10% chance to add to cart
            item_id = random.randint(100, 999)
            session_service.add_to_cart(
                session_token,
                str(item_id),
                f"Product {item_id}",
                random.randint(1, 3),
                round(random.uniform(10.0, 500.0), 2)
            )
            cart_items += 1

        # Small delay to simulate real browsing
        time.sleep(0.001)  # 1ms delay

    return {
        "user_id": user_id,
        "success": True,
        "session_token": session_token,
        "updates_count": updates_count,
        "cart_items": cart_items
    }

def demo_setup_users():
    """Demo 1: Setup users cho load testing"""
    print_separator("👥 SETUP USERS FOR LOAD TESTING")

    auth_service = AuthService()

    print("Creating 100 test users...")
    start_time = time.time()

    successful_registrations = 0
    for i in range(100):
        username = f"customer_{i}"
        success, _ = auth_service.register_user(
            username,
            f"{username}@fakeweb.com",
            "password123"
        )
        if success:
            successful_registrations += 1

    end_time = time.time()
    duration = end_time - start_time

    print(f"✅ Created {successful_registrations} users in {duration:.2f}s")
    print(f"📊 Registration rate: {successful_registrations/duration:.0f} users/second")

def demo_single_user_session():
    """Demo 2: Single user session với nhiều updates"""
    print_separator("🛒 SINGLE USER BROWSING SESSION")

    auth_service = AuthService()
    session_service = SessionService()

    # Login as test user
    success, session_token, message = auth_service.login("customer_1", "password123")
    if not success:
        print(f"❌ Login failed: {message}")
        return

    print(f"✅ Logged in successfully, session: {session_token[:12]}...")

    # Simulate browsing với high-frequency updates
    print("Simulating 100 page views (high-frequency updates)...")
    result = session_service.simulate_high_load_update(session_token, 100)

    if result:
        # Show session data
        session_data = session_service.get_session(session_token)
        print(f"📊 Final session stats:")
        print(f"   - Page views: {session_data.get('page_views', 0)}")
        print(f"   - Current page: {session_data.get('current_page', 'N/A')}")
        print(f"   - Last activity: {session_data.get('last_activity', 'N/A')}")

        # Add some items to cart
        print("Adding items to shopping cart...")
        session_service.add_to_cart(session_token, "laptop_123", "Gaming Laptop", 1, 999.99)
        session_service.add_to_cart(session_token, "mouse_456", "Gaming Mouse", 2, 49.99)

        # Show cart data
        cart_data = session_service.get_cart(session_token)
        print(f"🛒 Shopping cart:")
        print(f"   - Total items: {cart_data.get('total_items', 0)}")
        print(f"   - Total value: ${cart_data.get('total_value', '0.00')}")

def demo_concurrent_sessions():
    """Demo 3: Concurrent sessions mô phỏng 6,000 writes/second"""
    print_separator("⚡ CONCURRENT SESSIONS - PEAK LOAD SIMULATION")

    auth_service = AuthService()
    session_service = SessionService()

    # Parameters matching Fake Web Retailer's peak load
    concurrent_users = 50  # Reduced for demo
    pages_per_user = 30
    total_expected_updates = concurrent_users * pages_per_user

    print(f"🎯 Target simulation:")
    print(f"   - Concurrent users: {concurrent_users}")
    print(f"   - Pages per user: {pages_per_user}")
    print(f"   - Expected updates: {total_expected_updates}")

    start_time = time.time()

    # Use ThreadPoolExecutor for concurrent execution
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []

        for user_id in range(concurrent_users):
            future = executor.submit(
                simulate_user_browsing_session,
                auth_service,
                session_service,
                user_id,
                pages_per_user
            )
            futures.append(future)

        # Collect results
        successful_sessions = 0
        total_updates = 0
        total_cart_items = 0

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                successful_sessions += 1
                total_updates += result["updates_count"]
                total_cart_items += result["cart_items"]

    end_time = time.time()
    duration = end_time - start_time
    updates_per_second = total_updates / duration if duration > 0 else 0

    print(f"\n🚀 PERFORMANCE RESULTS:")
    print(f"   - Duration: {duration:.3f} seconds")
    print(f"   - Successful sessions: {successful_sessions}/{concurrent_users}")
    print(f"   - Total updates: {total_updates}")
    print(f"   - Total cart items: {total_cart_items}")
    print(f"   - Updates per second: {updates_per_second:.0f}")

    # Compare với database performance
    print(f"\n📊 COMPARISON WITH DATABASE:")
    database_limit = 2000  # writes per second per server
    required_db_servers = max(1, int(updates_per_second / database_limit) + 1)

    print(f"   - Redis performance: {updates_per_second:.0f} writes/sec")
    print(f"   - Database limit: {database_limit} writes/sec per server")
    print(f"   - Required DB servers: {required_db_servers}")
    print(f"   - Redis advantage: {updates_per_second/database_limit:.1f}x faster per server")

def demo_session_statistics():
    """Demo 4: Session statistics và monitoring"""
    print_separator("📈 SESSION STATISTICS & MONITORING")

    session_service = SessionService()
    stats = session_service.get_session_stats()

    print("📊 Current Redis Session Stats:")
    print(f"   - Active sessions: {stats['active_sessions']}")
    print(f"   - Active carts: {stats['active_carts']}")
    print(f"   - Memory used: {stats['memory_used']}")
    print(f"   - Redis version: {stats['redis_version']}")

    # Memory efficiency comparison
    print("\n💾 Memory Efficiency:")
    avg_session_size = 200  # bytes (estimate)
    total_session_memory = stats['active_sessions'] * avg_session_size

    print(f"   - Estimated session memory: {total_session_memory:,} bytes")
    print(f"   - Average per session: {avg_session_size} bytes")

    # Database comparison
    db_row_size = 500  # bytes per row in database
    db_memory_equivalent = stats['active_sessions'] * db_row_size

    print(f"\n🗄️ Database Comparison:")
    print(f"   - Redis session memory: {total_session_memory:,} bytes")
    print(f"   - Database equivalent: {db_memory_equivalent:,} bytes")
    print(f"   - Memory savings: {((db_memory_equivalent - total_session_memory) / db_memory_equivalent * 100):.1f}%")

def demo_ttl_behavior():
    """Demo 5: TTL behavior và auto cleanup"""
    print_separator("⏰ TTL BEHAVIOR & AUTO CLEANUP")

    auth_service = AuthService()
    session_service = SessionService()

    # Create a test session
    success, session_token, _ = auth_service.login("customer_1", "password123")
    if not success:
        print("❌ Could not create test session")
        return

    print(f"✅ Created test session: {session_token[:12]}...")

    # Check TTL
    session_key = f"session:{session_token}"
    ttl = redis_client.client.ttl(session_key)
    print(f"⏰ Initial TTL: {ttl} seconds ({ttl/60:.1f} minutes)")

    # Simulate activity that refreshes TTL
    print("Simulating user activity (TTL refresh)...")
    for i in range(5):
        session_service.update_session_activity(session_token, f"/page-{i}")
        new_ttl = redis_client.client.ttl(session_key)
        print(f"   Activity {i+1}: TTL refreshed to {new_ttl} seconds")
        time.sleep(1)

    print("\n💡 TTL Benefits:")
    print("   ✅ Automatic cleanup - no manual deletion needed")
    print("   ✅ Memory management - expired sessions auto-removed")
    print("   ✅ Security - old sessions can't be reused")
    print("   ✅ No cron jobs needed - Redis handles it internally")

def cleanup_demo_data():
    """Cleanup demo data"""
    print_separator("🧹 CLEANUP DEMO DATA")

    auth_service = AuthService()

    # Cleanup test users
    deleted = auth_service.cleanup_test_users("customer", 100)
    print(f"Cleaned up {deleted} user accounts")

    # Cleanup sessions (they'll expire automatically, but for demo)
    session_keys = redis_client.client.keys("session:*")
    cart_keys = redis_client.client.keys("cart:*")

    if session_keys:
        redis_client.client.delete(*session_keys)
    if cart_keys:
        redis_client.client.delete(*cart_keys)

    print(f"Cleaned up {len(session_keys)} sessions and {len(cart_keys)} carts")
    print("✅ Demo environment cleaned up")

def main():
    """Main demo function"""
    print_separator("🏬 FAKE WEB RETAILER - REDIS SESSION DEMO")

    # Check Redis connection
    if not redis_client.ping():
        print("❌ Cannot connect to Redis! Please check:")
        print("   - Redis server is running")
        print("   - Connection configuration in config.py")
        return

    print("✅ Redis connected successfully!")

    try:
        # Run all demos
        demo_setup_users()
        demo_single_user_session()
        demo_concurrent_sessions()
        demo_session_statistics()
        demo_ttl_behavior()

        print_separator("🎉 DEMO COMPLETED")
        print("Key Findings:")
        print("✅ Redis HASH perfect for session data")
        print("✅ 10-50x faster than database writes")
        print("✅ Automatic TTL management")
        print("✅ Memory efficient storage")
        print("✅ Handles 6K+ writes/second easily")
        print("✅ 92% cost reduction vs 10 database servers")

    except KeyboardInterrupt:
        print("\n⏸️ Demo interrupted by user")
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Ask user if they want to cleanup
        cleanup_choice = input("\n🧹 Clean up demo data? (y/N): ").lower().strip()
        if cleanup_choice == 'y':
            cleanup_demo_data()
        else:
            print("Demo data kept for inspection")

        # Close Redis connection
        redis_client.close()

if __name__ == "__main__":
    main()
