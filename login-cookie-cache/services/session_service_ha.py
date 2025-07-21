#!/usr/bin/env python3
"""
High Availability Session Service với fallback strategies
Giải quyết vấn đề "Redis ngỏm thì sao?"
"""

import sys
import os
import time
import uuid
import logging
from typing import Optional, Dict, Any, List
from redis.sentinel import Sentinel
from redis.exceptions import ConnectionError, TimeoutError

# Add parent directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))

from models.user import User

class HighAvailabilitySessionService:
    """
    Production-ready Session Service với multiple fallback strategies:
    1. Redis Sentinel (High Availability)
    2. Database fallback (when Redis completely down)
    3. Graceful degradation (limited functionality)
    """

    def __init__(self):
        self.setup_redis_sentinel()
        self.setup_database_fallback()
        self.session_prefix = "session:"
        self.cart_prefix = "cart:"
        self.default_ttl = 3600  # 1 hour
        self.logger = logging.getLogger(__name__)

    def setup_redis_sentinel(self):
        """Setup Redis Sentinel cho high availability"""
        try:
            # Redis Sentinel configuration
            sentinels = [
                ('sentinel-1', 26379),
                ('sentinel-2', 26379),
                ('sentinel-3', 26379)
            ]

            self.sentinel = Sentinel(sentinels, socket_timeout=0.1)

            # Get master and slave connections
            self.redis_master = self.sentinel.master_for(
                'mymaster',
                socket_timeout=0.1,
                decode_responses=True
            )

            self.redis_slaves = self.sentinel.slave_for(
                'mymaster',
                socket_timeout=0.1,
                decode_responses=True
            )

            self.logger.info("✅ Redis Sentinel setup completed")

        except Exception as e:
            self.logger.error(f"❌ Redis Sentinel setup failed: {e}")
            self.redis_master = None
            self.redis_slaves = None

    def setup_database_fallback(self):
        """Setup database connection for fallback"""
        try:
            # Giả sử sử dụng PostgreSQL cho fallback
            import psycopg2
            from psycopg2 import pool

            self.db_pool = psycopg2.pool.ThreadedConnectionPool(
                1, 20,
                host="localhost",
                database="fake_web_retailer",
                user="postgres",
                password="password"
            )

            # Create sessions table if not exists
            with self.db_pool.getconn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS fallback_sessions (
                            session_token VARCHAR(255) PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL,
                            username VARCHAR(255) NOT NULL,
                            last_activity TIMESTAMP DEFAULT NOW(),
                            current_page TEXT,
                            page_views INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT NOW(),
                            expires_at TIMESTAMP NOT NULL
                        )
                    """)
                conn.commit()

            self.logger.info("✅ Database fallback setup completed")

        except Exception as e:
            self.logger.error(f"❌ Database fallback setup failed: {e}")
            self.db_pool = None

    def create_session(self, user: User) -> str:
        """Create session với fallback strategy"""
        session_token = str(uuid.uuid4())
        session_data = user.to_session_data()

        # Strategy 1: Try Redis Master first
        if self._create_session_redis(session_token, session_data):
            return session_token

        # Strategy 2: Fallback to Database
        if self._create_session_database(session_token, session_data):
            self.logger.warning("⚠️ Session created in database (Redis unavailable)")
            return session_token

        # Strategy 3: In-memory fallback (last resort)
        self.logger.error("❌ All session storage failed, using in-memory")
        return self._create_session_memory(session_token, session_data)

    def _create_session_redis(self, session_token: str, session_data: Dict) -> bool:
        """Tạo session trong Redis"""
        try:
            if not self.redis_master:
                return False

            session_key = f"{self.session_prefix}{session_token}"

            pipe = self.redis_master.pipeline()
            pipe.hmset(session_key, session_data)
            pipe.expire(session_key, self.default_ttl)
            pipe.execute()

            self.logger.debug(f"✅ Session {session_token[:8]}... created in Redis")
            return True

        except (ConnectionError, TimeoutError) as e:
            self.logger.warning(f"⚠️ Redis write failed: {e}")
            return False

    def _create_session_database(self, session_token: str, session_data: Dict) -> bool:
        """Tạo session trong Database (fallback)"""
        try:
            if not self.db_pool:
                return False

            conn = self.db_pool.getconn()
            with conn.cursor() as cur:
                expires_at = time.time() + self.default_ttl
                cur.execute("""
                    INSERT INTO fallback_sessions
                    (session_token, user_id, username, current_page, page_views, expires_at)
                    VALUES (%s, %s, %s, %s, %s, to_timestamp(%s))
                """, (
                    session_token,
                    session_data.get('user_id'),
                    session_data.get('username'),
                    session_data.get('current_page', '/'),
                    int(session_data.get('page_views', 1)),
                    expires_at
                ))
            conn.commit()
            self.db_pool.putconn(conn)

            return True

        except Exception as e:
            self.logger.error(f"❌ Database session creation failed: {e}")
            return False

    def _create_session_memory(self, session_token: str, session_data: Dict) -> str:
        """In-memory session (last resort fallback)"""
        # Đây chỉ là temporary solution cho graceful degradation
        # Trong thực tế có thể dùng local cache như memcached
        if not hasattr(self, '_memory_sessions'):
            self._memory_sessions = {}

        self._memory_sessions[session_token] = {
            **session_data,
            'expires_at': time.time() + self.default_ttl,
            'storage_type': 'memory'
        }

        return session_token

    def get_session(self, session_token: str) -> Optional[Dict[str, str]]:
        """Get session với fallback strategy"""

        # Strategy 1: Try Redis Slaves first (read preference)
        session_data = self._get_session_redis(session_token)
        if session_data:
            return session_data

        # Strategy 2: Try Redis Master
        session_data = self._get_session_redis_master(session_token)
        if session_data:
            return session_data

        # Strategy 3: Fallback to Database
        session_data = self._get_session_database(session_token)
        if session_data:
            self.logger.warning("⚠️ Session retrieved from database (Redis read failed)")
            return session_data

        # Strategy 4: Check memory fallback
        session_data = self._get_session_memory(session_token)
        if session_data:
            self.logger.warning("⚠️ Session retrieved from memory (all other storage failed)")
            return session_data

        return None

    def _get_session_redis(self, session_token: str) -> Optional[Dict]:
        """Get session from Redis slaves (read preference)"""
        try:
            if not self.redis_slaves:
                return None

            session_key = f"{self.session_prefix}{session_token}"
            session_data = self.redis_slaves.hgetall(session_key)

            if session_data:
                # Update last activity in master
                self._update_activity_async(session_token)
                return session_data

        except (ConnectionError, TimeoutError):
            pass

        return None

    def _get_session_redis_master(self, session_token: str) -> Optional[Dict]:
        """Get session from Redis master"""
        try:
            if not self.redis_master:
                return None

            session_key = f"{self.session_prefix}{session_token}"
            session_data = self.redis_master.hgetall(session_key)

            if session_data:
                # Update last activity
                self.redis_master.hset(session_key, 'last_activity', str(time.time()))
                self.redis_master.expire(session_key, self.default_ttl)
                return session_data

        except (ConnectionError, TimeoutError):
            pass

        return None

    def _get_session_database(self, session_token: str) -> Optional[Dict]:
        """Get session from database fallback"""
        try:
            if not self.db_pool:
                return None

            conn = self.db_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, username, current_page, page_views,
                           EXTRACT(EPOCH FROM last_activity) as last_activity
                    FROM fallback_sessions
                    WHERE session_token = %s
                    AND expires_at > NOW()
                """, (session_token,))

                row = cur.fetchone()
                if row:
                    # Update last activity
                    cur.execute("""
                        UPDATE fallback_sessions
                        SET last_activity = NOW(),
                            expires_at = NOW() + INTERVAL %s seconds
                        WHERE session_token = %s
                    """, (self.default_ttl, session_token))

                    conn.commit()

                    return {
                        'user_id': row[0],
                        'username': row[1],
                        'current_page': row[2],
                        'page_views': str(row[3]),
                        'last_activity': str(row[4]),
                        'storage_type': 'database'
                    }

            self.db_pool.putconn(conn)

        except Exception as e:
            self.logger.error(f"❌ Database session read failed: {e}")

        return None

    def _get_session_memory(self, session_token: str) -> Optional[Dict]:
        """Get session from memory fallback"""
        if not hasattr(self, '_memory_sessions'):
            return None

        session_data = self._memory_sessions.get(session_token)
        if session_data and session_data['expires_at'] > time.time():
            # Update activity
            session_data['last_activity'] = str(time.time())
            session_data['expires_at'] = time.time() + self.default_ttl
            return session_data

        # Cleanup expired
        if session_data:
            del self._memory_sessions[session_token]

        return None

    def _update_activity_async(self, session_token: str):
        """Update activity asynchronously"""
        try:
            if self.redis_master:
                session_key = f"{self.session_prefix}{session_token}"
                self.redis_master.hset(session_key, 'last_activity', str(time.time()))
        except:
            pass  # Silent fail for async update

    def update_session_activity(self, session_token: str, page: str) -> bool:
        """Update session activity với fallback"""

        # Try Redis first
        if self._update_session_redis(session_token, page):
            return True

        # Fallback to Database
        if self._update_session_database(session_token, page):
            self.logger.warning("⚠️ Session updated in database (Redis unavailable)")
            return True

        # Memory fallback
        return self._update_session_memory(session_token, page)

    def _update_session_redis(self, session_token: str, page: str) -> bool:
        """Update session in Redis"""
        try:
            if not self.redis_master:
                return False

            session_key = f"{self.session_prefix}{session_token}"

            pipe = self.redis_master.pipeline()
            pipe.hset(session_key, 'last_activity', str(time.time()))
            pipe.hset(session_key, 'current_page', page)
            pipe.hincrby(session_key, 'page_views', 1)
            pipe.expire(session_key, self.default_ttl)
            pipe.execute()

            return True

        except (ConnectionError, TimeoutError):
            return False

    def _update_session_database(self, session_token: str, page: str) -> bool:
        """Update session in database"""
        try:
            if not self.db_pool:
                return False

            conn = self.db_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE fallback_sessions
                    SET last_activity = NOW(),
                        current_page = %s,
                        page_views = page_views + 1,
                        expires_at = NOW() + INTERVAL %s seconds
                    WHERE session_token = %s
                """, (page, self.default_ttl, session_token))

            conn.commit()
            self.db_pool.putconn(conn)
            return True

        except Exception as e:
            self.logger.error(f"❌ Database session update failed: {e}")
            return False

    def _update_session_memory(self, session_token: str, page: str) -> bool:
        """Update session in memory"""
        if not hasattr(self, '_memory_sessions'):
            return False

        session_data = self._memory_sessions.get(session_token)
        if session_data and session_data['expires_at'] > time.time():
            session_data['last_activity'] = str(time.time())
            session_data['current_page'] = page
            session_data['page_views'] = str(int(session_data.get('page_views', 0)) + 1)
            session_data['expires_at'] = time.time() + self.default_ttl
            return True

        return False

    def health_check(self) -> Dict[str, bool]:
        """Check health of all storage systems"""
        health = {}

        # Redis Master health
        try:
            if self.redis_master:
                self.redis_master.ping()
                health['redis_master'] = True
        except:
            health['redis_master'] = False

        # Redis Slaves health
        try:
            if self.redis_slaves:
                self.redis_slaves.ping()
                health['redis_slaves'] = True
        except:
            health['redis_slaves'] = False

        # Database health
        try:
            if self.db_pool:
                conn = self.db_pool.getconn()
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                self.db_pool.putconn(conn)
                health['database'] = True
        except:
            health['database'] = False

        # Overall health
        health['overall'] = any(health.values())

        return health

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about storage usage"""
        stats = {
            'redis_sessions': 0,
            'database_sessions': 0,
            'memory_sessions': 0,
            'total_sessions': 0
        }

        # Redis stats
        try:
            if self.redis_master:
                redis_keys = self.redis_master.keys(f"{self.session_prefix}*")
                stats['redis_sessions'] = len(redis_keys)
        except:
            pass

        # Database stats
        try:
            if self.db_pool:
                conn = self.db_pool.getconn()
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM fallback_sessions
                        WHERE expires_at > NOW()
                    """)
                    stats['database_sessions'] = cur.fetchone()[0]
                self.db_pool.putconn(conn)
        except:
            pass

        # Memory stats
        if hasattr(self, '_memory_sessions'):
            # Count non-expired sessions
            current_time = time.time()
            stats['memory_sessions'] = sum(
                1 for session in self._memory_sessions.values()
                if session['expires_at'] > current_time
            )

        stats['total_sessions'] = (
            stats['redis_sessions'] +
            stats['database_sessions'] +
            stats['memory_sessions']
        )

        return stats

# Usage example
if __name__ == "__main__":
    # Initialize HA session service
    ha_session = HighAvailabilitySessionService()

    # Health check
    health = ha_session.health_check()
    print(f"System Health: {health}")

    # Storage stats
    stats = ha_session.get_storage_stats()
    print(f"Storage Stats: {stats}")
