import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def pytest_configure(config):
    """Configure test environment"""
    # Set testing flag
    os.environ["TESTING"] = "1"
    
    # Add project root to PYTHONPATH
    if "PYTHONPATH" in os.environ:
        os.environ["PYTHONPATH"] = f"{PROJECT_ROOT}:{os.environ['PYTHONPATH']}"
    else:
        os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

@pytest.fixture(scope="session")
def test_db():
    """Database test fixture"""
    from sqlproxy.core.database import Database
    db = Database(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        database=os.getenv("DB_NAME", "test_db")
    )
    yield db
    db.close()

@pytest.fixture(scope="session")
def test_redis():
    """Redis test fixture"""
    from sqlproxy.core.redis_client import RedisClient
    client = RedisClient(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379))
    )
    yield client
    client.close()