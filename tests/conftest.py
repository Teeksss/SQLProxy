import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test database configurations
TEST_DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'database': os.getenv('DB_NAME', 'test_db')
}

# Test Redis configurations
TEST_REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': 0
}

@pytest.fixture(scope="session")
def db_config():
    """Return database configuration"""
    return TEST_DB_CONFIG

@pytest.fixture(scope="session")
def redis_config():
    """Return Redis configuration"""
    return TEST_REDIS_CONFIG

@pytest.fixture(scope="session")
def db_connection():
    """Create database connection"""
    from sqlproxy.core.database.integration import DatabaseIntegration
    db = DatabaseIntegration(
        f"postgresql://{TEST_DB_CONFIG['user']}:{TEST_DB_CONFIG['password']}@"
        f"{TEST_DB_CONFIG['host']}:{TEST_DB_CONFIG['port']}/{TEST_DB_CONFIG['database']}"
    )
    yield db

@pytest.fixture(scope="session")
def redis_connection():
    """Create Redis connection"""
    from sqlproxy.core.redis.connection import RedisConnection
    redis = RedisConnection(**TEST_REDIS_CONFIG)
    yield redis