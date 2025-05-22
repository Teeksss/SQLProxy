"""Test utilities and helpers"""

from datetime import datetime, timezone

def get_test_timestamp():
    """Return current UTC timestamp for tests"""
    return datetime.now(timezone.utc)

def get_test_connection_string():
    """Return test database connection string"""
    return "postgresql://postgres:postgres@localhost:5432/test_db"

def get_test_redis_config():
    """Return test Redis configuration"""
    return {
        "host": "localhost",
        "port": 6379,
        "db": 0
    }

__all__ = [
    'get_test_timestamp',
    'get_test_connection_string',
    'get_test_redis_config'
]