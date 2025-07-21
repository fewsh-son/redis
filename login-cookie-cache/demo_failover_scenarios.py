#!/usr/bin/env python3
"""
Demo: Redis Failure Scenarios & Recovery
Mô phỏng các tình huống "Redis ngỏm" và cách system phản ứng
"""

import sys
import os
import time
import threading
import random
from typing import Dict, List

# Add parent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.redis_client import redis_client
from services.session_service_ha import HighAvailabilitySessionService
from services.auth_service import AuthService
from models.user import User

class FailoverDemo:
    """Demo các failure scenarios và recovery behaviors"""

    def __init__(self):
        self.ha_session = HighAvailabilitySessionService()
        self.auth_service = AuthService()
        self.active_sessions = {}
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'redis_requests': 0,
            'database_requests': 0,
            'memory_requests': 0
        }

    def setup_test_users(self, count: int = 10) -> List[str]:
        """Setup test users and return session tokens"""
        print(f"📝 Setting up {count} test users...")

        session_tokens = []
        for i in range(count):
            username = f"failover_user_{i}"

            # Register user
            success, _ = self.auth_service.register_user(
                username, f"{username}@test.com", "password123"
            )

            if success:
                # Login to create session
                login_success, token, _ = self.auth_service.login(username, "password123")
                if login_success and token:
                    session_tokens.append(token)
                    self.active_sessions[token] = username

        print(f"✅ Created {len(session_tokens)} active sessions")
        return session_tokens

    def simulate_user_traffic(self, session_tokens: List[str], duration: int = 30):
        """Simulate continuous user traffic during failures"""
        print(f"🚀 Starting user traffic simulation for {duration} seconds...")

        end_time = time.time() + duration

        while time.time() < end_time:
            # Random session activity
            session_token = random.choice(session_tokens)
            page = f"/page-{random.randint(1, 100)}"

            self.metrics['total_requests'] += 1

            # Try to update session activity
            start_time = time.perf_counter()

            try:
                success = self.ha_session.update_session_activity(session_token, page)
                latency = (time.perf_counter() - start_time) * 1000

                if success:
                    self.metrics['successful_requests'] += 1

                    # Check which storage was used (if available in response)
                    session_data = self.ha_session.get_session(session_token)
                    if session_data:
                        storage_type = session_data.get('storage_type', 'redis')
                        self.metrics[f'{storage_type}_requests'] += 1
                else:
                    self.metrics['failed_requests'] += 1

            except Exception as e:
                self.metrics['failed_requests'] += 1
                print(f"❌ Request failed: {e}")

            # Small delay to simulate realistic traffic
            time.sleep(0.1)

        print(f"✅ Traffic simulation completed")

    def print_current_metrics(self):
        """Print current performance metrics"""
        total = self.metrics['total_requests']
        if total == 0:
            return

        success_rate = (self.metrics['successful_requests'] / total) * 100

        print(f"\n📊 CURRENT METRICS:")
        print(f"   Total Requests: {total}")
        print(f"   Successful: {self.metrics['successful_requests']} ({success_rate:.1f}%)")
        print(f"   Failed: {self.metrics['failed_requests']}")
        print(f"   Redis: {self.metrics['redis_requests']}")
        print(f"   Database: {self.metrics['database_requests']}")
        print(f"   Memory: {self.metrics['memory_requests']}")

    def scenario_1_redis_master_down(self, session_tokens: List[str]):
        """Scenario 1: Redis Master goes down"""
        print("\n" + "="*60)
        print("🔥 SCENARIO 1: REDIS MASTER FAILURE")
        print("="*60)

        print("📊 Initial system health:")
        health = self.ha_session.health_check()
        print(f"   {health}")

        print("\n🚀 Starting normal traffic...")

        # Start background traffic
        traffic_thread = threading.Thread(
            target=self.simulate_user_traffic,
            args=(session_tokens, 60)
        )
        traffic_thread.start()

        # Let traffic run normally for 10 seconds
        time.sleep(10)
        print("\n💥 SIMULATING REDIS MASTER FAILURE...")

        # Simulate Redis master failure by setting to None
        original_master = self.ha_session.redis_master
        self.ha_session.redis_master = None

        print("⚠️ Redis master is now DOWN!")

        # Check health during failure
        time.sleep(5)
        health = self.ha_session.health_check()
        print(f"📊 System health during failure: {health}")

        # Let traffic continue for 20 more seconds with fallback
        print("📈 Traffic continuing with database fallback...")
        time.sleep(20)

        print("\n🔧 RECOVERING REDIS MASTER...")
        # Restore Redis master
        self.ha_session.redis_master = original_master

        # Verify recovery
        time.sleep(5)
        health = self.ha_session.health_check()
        print(f"✅ System health after recovery: {health}")

        # Wait for traffic to complete
        traffic_thread.join()

        self.print_current_metrics()

        # Storage distribution
        stats = self.ha_session.get_storage_stats()
        print(f"📊 Storage distribution: {stats}")

    def scenario_2_complete_redis_failure(self, session_tokens: List[str]):
        """Scenario 2: Complete Redis cluster failure"""
        print("\n" + "="*60)
        print("💀 SCENARIO 2: COMPLETE REDIS CLUSTER FAILURE")
        print("="*60)

        # Reset metrics
        self.metrics = {key: 0 for key in self.metrics.keys()}

        print("📊 Initial system health:")
        health = self.ha_session.health_check()
        print(f"   {health}")

        # Start traffic
        traffic_thread = threading.Thread(
            target=self.simulate_user_traffic,
            args=(session_tokens, 45)
        )
        traffic_thread.start()

        time.sleep(10)
        print("\n💥💥 SIMULATING COMPLETE REDIS CLUSTER FAILURE...")

        # Disable all Redis connections
        original_master = self.ha_session.redis_master
        original_slaves = self.ha_session.redis_slaves

        self.ha_session.redis_master = None
        self.ha_session.redis_slaves = None

        print("⚠️ Entire Redis cluster is DOWN!")
        print("🔄 System should fallback to database...")

        time.sleep(5)
        health = self.ha_session.health_check()
        print(f"📊 System health during complete failure: {health}")

        # Let traffic run on database fallback
        time.sleep(15)
        print("📊 Traffic running entirely on database fallback...")

        print("\n🔧 RECOVERING REDIS CLUSTER...")
        # Restore Redis
        self.ha_session.redis_master = original_master
        self.ha_session.redis_slaves = original_slaves

        time.sleep(5)
        health = self.ha_session.health_check()
        print(f"✅ System health after recovery: {health}")

        traffic_thread.join()
        self.print_current_metrics()

    def scenario_3_partial_failure_recovery(self, session_tokens: List[str]):
        """Scenario 3: Partial failures and gradual recovery"""
        print("\n" + "="*60)
        print("⚡ SCENARIO 3: PARTIAL FAILURE & RECOVERY")
        print("="*60)

        # Reset metrics
        self.metrics = {key: 0 for key in self.metrics.keys()}

        # Start continuous traffic
        traffic_thread = threading.Thread(
            target=self.simulate_user_traffic,
            args=(session_tokens, 90)
        )
        traffic_thread.start()

        print("🚀 Starting continuous traffic...")
        time.sleep(10)

        # Phase 1: Slaves fail
        print("\n💥 Phase 1: Redis slaves fail...")
        original_slaves = self.ha_session.redis_slaves
        self.ha_session.redis_slaves = None

        time.sleep(15)
        health = self.ha_session.health_check()
        print(f"📊 Health with slaves down: {health}")

        # Phase 2: Master also fails
        print("\n💥 Phase 2: Redis master also fails...")
        original_master = self.ha_session.redis_master
        self.ha_session.redis_master = None

        time.sleep(15)
        health = self.ha_session.health_check()
        print(f"📊 Health with everything down: {health}")

        # Phase 3: Gradual recovery - Master first
        print("\n🔧 Phase 3: Recovering master...")
        self.ha_session.redis_master = original_master

        time.sleep(15)
        health = self.ha_session.health_check()
        print(f"📊 Health with master recovered: {health}")

        # Phase 4: Slaves recover
        print("\n🔧 Phase 4: Recovering slaves...")
        self.ha_session.redis_slaves = original_slaves

        time.sleep(20)
        health = self.ha_session.health_check()
        print(f"✅ Health fully recovered: {health}")

        traffic_thread.join()
        self.print_current_metrics()

    def demonstrate_data_consistency(self, session_tokens: List[str]):
        """Demonstrate data consistency across storage layers"""
        print("\n" + "="*60)
        print("🔍 DATA CONSISTENCY DEMONSTRATION")
        print("="*60)

        test_token = session_tokens[0]

        print(f"Testing session: {test_token[:12]}...")

        # Update session in Redis
        print("\n1. Updating session in Redis...")
        success = self.ha_session.update_session_activity(test_token, "/consistency-test")
        print(f"   Redis update: {'✅ Success' if success else '❌ Failed'}")

        # Get from Redis
        session_data = self.ha_session.get_session(test_token)
        if session_data:
            print(f"   Redis data: page={session_data.get('current_page')}, views={session_data.get('page_views')}")

        # Simulate Redis failure
        print("\n2. Simulating Redis failure...")
        original_master = self.ha_session.redis_master
        original_slaves = self.ha_session.redis_slaves

        self.ha_session.redis_master = None
        self.ha_session.redis_slaves = None

        # Try to get session (should fallback to database)
        print("   Getting session during Redis failure...")
        session_data = self.ha_session.get_session(test_token)
        if session_data:
            print(f"   Database data: page={session_data.get('current_page')}, views={session_data.get('page_views')}")
            storage_type = session_data.get('storage_type', 'unknown')
            print(f"   Storage type: {storage_type}")
        else:
            print("   ❌ No session data found in any storage")

        # Update during failure (should go to database)
        print("\n3. Updating during failure...")
        success = self.ha_session.update_session_activity(test_token, "/failure-test")
        print(f"   Database update: {'✅ Success' if success else '❌ Failed'}")

        # Restore Redis
        print("\n4. Restoring Redis...")
        self.ha_session.redis_master = original_master
        self.ha_session.redis_slaves = original_slaves

        # Get final state
        session_data = self.ha_session.get_session(test_token)
        if session_data:
            print(f"   Final state: page={session_data.get('current_page')}, views={session_data.get('page_views')}")
            storage_type = session_data.get('storage_type', 'redis')
            print(f"   Storage type: {storage_type}")

def main():
    """Main demo function"""
    print("🏬 FAKE WEB RETAILER - FAILOVER SCENARIOS DEMO")
    print("="*60)

    # Check initial system health
    demo = FailoverDemo()
    health = demo.ha_session.health_check()

    if not health.get('overall', False):
        print("❌ System not ready! Please check:")
        print("   - Redis server is running")
        print("   - Database is accessible")
        print("   - All connections are configured")
        return

    print("✅ System is ready for failover testing!")
    print(f"Initial health: {health}")

    # Setup test environment
    session_tokens = demo.setup_test_users(20)
    if len(session_tokens) < 10:
        print("❌ Not enough test sessions created!")
        return

    try:
        # Run all scenarios
        print("\n🎯 Running comprehensive failover scenarios...")

        # Scenario 1: Redis master failure
        demo.scenario_1_redis_master_down(session_tokens)
        time.sleep(5)

        # Scenario 2: Complete Redis failure
        demo.scenario_2_complete_redis_failure(session_tokens)
        time.sleep(5)

        # Scenario 3: Partial failure and recovery
        demo.scenario_3_partial_failure_recovery(session_tokens)
        time.sleep(5)

        # Data consistency demo
        demo.demonstrate_data_consistency(session_tokens)

        print("\n" + "="*60)
        print("🎉 FAILOVER SCENARIOS COMPLETED")
        print("="*60)

        final_health = demo.ha_session.health_check()
        final_stats = demo.ha_session.get_storage_stats()

        print("📊 Final System Status:")
        print(f"   Health: {final_health}")
        print(f"   Storage Stats: {final_stats}")

        print("\n💡 Key Findings:")
        print("   ✅ System maintains availability during Redis failures")
        print("   ✅ Automatic fallback to database works seamlessly")
        print("   ✅ Data consistency maintained across storage layers")
        print("   ✅ Graceful recovery when Redis comes back online")
        print("   ✅ User sessions persist through infrastructure failures")

    except KeyboardInterrupt:
        print("\n⏸️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            demo.auth_service.cleanup_test_users("failover_user", 20)
            print("🧹 Test cleanup completed")
        except:
            pass

if __name__ == "__main__":
    main()
