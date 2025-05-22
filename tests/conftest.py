import os
import sys
import pytest

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

@pytest.fixture(scope='session')
def test_app():
    from sqlproxy.main import app
    return app

@pytest.fixture(scope='session')
def test_client():
    from fastapi.testclient import TestClient
    from sqlproxy.main import app
    return TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_env():
    """Test environment setup"""
    os.environ['TESTING'] = 'true'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['REDIS_HOST'] = 'localhost'
    yield
    os.environ.pop('TESTING', None)