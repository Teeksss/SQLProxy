import pytest
import redis
import rejson
from redis.exceptions import ConnectionError

class TestRedisConnection:
    @pytest.fixture
    def redis_client(self):
        return redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
    def test_redis_connection(self, redis_client):
        """Redis bağlantısını test eder"""
        try:
            response = redis_client.ping()
            assert response == True
            
        except ConnectionError as e:
            pytest.fail(f"Redis connection failed: {str(e)}")
            
    def test_rejson_module(self, redis_client):
        """ReJSON modülünü test eder"""
        try:
            # Test data
            test_data = {
                "name": "test",
                "value": 42
            }
            
            # Set JSON
            redis_client.json().set('test', '.', test_data)
            
            # Get JSON
            result = redis_client.json().get('test')
            
            assert result == test_data
            
        except Exception as e:
            pytest.fail(f"ReJSON module test failed: {str(e)}")
            
    def test_search_module(self, redis_client):
        """Search modülünü test eder"""
        try:
            # Create index
            redis_client.ft('test').create_index([
                redis.commands.search.TextField('name'),
                redis.commands.search.NumericField('value')
            ])
            
            # Test search
            result = redis_client.ft('test').search('test')
            assert result is not None
            
        except Exception as e:
            pytest.fail(f"Search module test failed: {str(e)}")