import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from sqlproxy.core import QueryExecutor
from sqlproxy.models import QueryRequest

class TestQueryPerformance:
    @pytest.fixture
    def large_dataset(self):
        return [
            {"id": i, "data": f"test_{i}"}
            for i in range(10000)
        ]
        
    def test_query_response_time(self, executor, large_dataset):
        # Arrange
        query = "SELECT * FROM large_table WHERE id = $1"
        
        # Act
        start_time = time.time()
        result = executor.execute(
            QueryRequest(
                query=query,
                parameters=[5000]
            )
        )
        end_time = time.time()
        
        # Assert
        response_time = end_time - start_time
        assert response_time < 0.1  # 100ms threshold
        
    def test_concurrent_queries(self, executor):
        # Arrange
        num_concurrent = 100
        query = "SELECT * FROM users WHERE id = $1"
        
        def execute_query(i):
            return executor.execute(
                QueryRequest(
                    query=query,
                    parameters=[i]
                )
            )
            
        # Act
        with ThreadPoolExecutor(max_workers=10) as pool:
            start_time = time.time()
            results = list(pool.map(
                execute_query,
                range(num_concurrent)
            ))
            end_time = time.time()
            
        # Assert
        total_time = end_time - start_time
        avg_time = total_time / num_concurrent
        assert avg_time < 0.2  # 200ms average threshold