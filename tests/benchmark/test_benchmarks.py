import pytest
import psutil
import cProfile
import pstats
import io
from datetime import datetime, timedelta
from sqlproxy.core.benchmark import BenchmarkRunner
from sqlproxy.models import BenchmarkConfig, BenchmarkResult

class TestBenchmarks:
    @pytest.fixture
    def benchmark_runner(self):
        return BenchmarkRunner()

    @pytest.fixture
    def benchmark_config(self):
        return BenchmarkConfig(
            iterations=1000,
            concurrent_users=[1, 10, 50, 100],
            query_types=['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
            dataset_sizes=[100, 1000, 10000],
            wait_time=0.1
        )

    def test_select_performance(self, benchmark_runner, benchmark_config):
        """SELECT sorgu performansını test eder"""
        queries = [
            # Basit sorgular
            "SELECT * FROM users LIMIT 100",
            "SELECT id, name FROM users WHERE id = $1",
            
            # Orta karmaşıklıkta sorgular
            """
            SELECT u.*, COUNT(o.id) as order_count 
            FROM users u 
            LEFT JOIN orders o ON u.id = o.user_id 
            GROUP BY u.id
            """,
            
            # Kompleks sorgular
            """
            WITH RECURSIVE subordinates AS (
                SELECT employee_id, manager_id, name
                FROM employees
                WHERE manager_id = $1
                UNION
                SELECT e.employee_id, e.manager_id, e.name
                FROM employees e
                INNER JOIN subordinates s ON s.employee_id = e.manager_id
            )
            SELECT * FROM subordinates
            """
        ]

        results = []
        for query in queries:
            result = benchmark_runner.run_select_benchmark(
                query=query,
                config=benchmark_config
            )
            results.append(result)

        # Analiz
        for result in results:
            assert result.avg_response_time < 1.0  # 1 saniye altı
            assert result.error_rate < 0.01        # %1'den az hata
            assert result.throughput > 100         # Saniyede 100+ sorgu

    def test_write_performance(self, benchmark_runner, benchmark_config):
        """INSERT/UPDATE/DELETE performansını test eder"""
        operations = [
            # INSERT
            """
            INSERT INTO users (name, email, created_at)
            VALUES ($1, $2, $3)
            """,
            
            # Bulk INSERT
            """
            INSERT INTO users (name, email, created_at)
            SELECT 
                'User ' || i,
                'user' || i || '@example.com',
                NOW()
            FROM generate_series(1, $1) i
            """,
            
            # UPDATE
            """
            UPDATE users 
            SET last_login = NOW()
            WHERE id = $1
            """,
            
            # DELETE
            "DELETE FROM users WHERE id = $1"
        ]

        for op in operations:
            result = benchmark_runner.run_write_benchmark(
                query=op,
                config=benchmark_config
            )
            
            assert result.avg_response_time < 0.5  # 500ms altı
            assert result.transactions_per_second > 50
            assert result.rollback_rate < 0.01

    def test_concurrent_performance(self, benchmark_runner, benchmark_config):
        """Eşzamanlı sorgu performansını test eder"""
        scenarios = [
            {
                'users': 100,
                'queries_per_user': 50,
                'query_mix': {
                    'SELECT': 0.7,
                    'INSERT': 0.1,
                    'UPDATE': 0.15,
                    'DELETE': 0.05
                }
            },
            {
                'users': 500,
                'queries_per_user': 20,
                'query_mix': {
                    'SELECT': 0.8,
                    'INSERT': 0.1,
                    'UPDATE': 0.1
                }
            }
        ]

        for scenario in scenarios:
            result = benchmark_runner.run_concurrent_benchmark(
                scenario=scenario,
                config=benchmark_config
            )
            
            assert result.max_concurrent_queries >= scenario['users']
            assert result.avg_response_time < 2.0  # 2 saniye altı
            assert result.error_rate < 0.05        # %5'den az hata