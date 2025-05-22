import pytest
import asyncio
from locust import HttpUser, task, between
from sqlproxy.core import QueryExecutor

class QueryLoadTest(HttpUser):
    wait_time = between(1, 2)
    
    @task
    def execute_simple_query(self):
        self.client.post("/query", json={
            "query": "SELECT * FROM users LIMIT 10"
        })
        
    @task
    def execute_complex_query(self):
        self.client.post("/query", json={
            "query": """
                SELECT u.*, COUNT(o.id) as order_count
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                GROUP BY u.id
                HAVING COUNT(o.id) > 5
                LIMIT 10
            """
        })
        
    @task
    def execute_write_query(self):
        self.client.post("/query", json={
            "query": """
                INSERT INTO audit_log (action, timestamp)
                VALUES ($1, NOW())
            """,
            "parameters": ["test_action"]
        })

class TestLoadCapacity:
    @pytest.fixture
    async def setup_test_data(self, database):
        # Setup large test dataset
        await database.execute("""
            INSERT INTO users (name, email)
            SELECT 
                'User ' || i,
                'user' || i || '@example.com'
            FROM generate_series(1, 10000) i
        """)
        
    async def test_sustained_load(self, database, setup_test_data):
        executor = QueryExecutor(database)
        
        # Simulate sustained load
        async def execute_queries():
            for _ in range(1000):
                await executor.execute(
                    QueryRequest(
                        query="SELECT * FROM users WHERE id = $1",
                        parameters=[random.randint(1, 10000)]
                    )
                )
                await asyncio.sleep(0.01)
                
        # Run multiple clients
        clients = [execute_queries() for _ in range(10)]
        await asyncio.gather(*clients)