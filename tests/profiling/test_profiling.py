import pytest
import cProfile
import pstats
import memory_profiler
import psutil
import io
from sqlproxy.core.profiler import QueryProfiler
from sqlproxy.models import ProfilingResult

class TestProfiling:
    @pytest.fixture
    def profiler(self):
        return QueryProfiler()

    def test_cpu_profiling(self, profiler):
        """CPU kullanımını profiler"""
        # Test query
        query = """
        SELECT 
            u.*, 
            COUNT(o.id) as order_count,
            SUM(o.total) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.created_at > $1
        GROUP BY u.id
        HAVING COUNT(o.id) > 5
        ORDER BY total_spent DESC
        LIMIT 100
        """

        # Profile CPU usage
        pr = cProfile.Profile()
        pr.enable()
        
        result = profiler.execute_query(query)
        
        pr.disable()
        s = io.StringIO()
        stats = pstats.Stats(pr, stream=s)
        stats.sort_stats('cumulative')
        stats.print_stats()

        # Analyze results
        profile_output = s.getvalue()
        assert 'execute_query' in profile_output
        
        # Check execution time
        total_time = stats.total_tt
        assert total_time < 1.0  # 1 saniye altı

    @pytest.mark.skip(reason="Heavy memory usage")
    def test_memory_profiling(self, profiler):
        """Memory kullanımını profiler"""
        @memory_profiler.profile
        def memory_intensive_query():
            # Large result set query
            query = """
            SELECT *
            FROM generate_series(1, 1000000) i
            CROSS JOIN generate_series(1, 10) j
            """
            return profiler.execute_query(query)

        # Execute and profile
        result = memory_intensive_query()
        
        # Get memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Assertions
        assert memory_info.rss < 1024 * 1024 * 1024  # 1GB altı
        assert len(result) > 0

    def test_io_profiling(self, profiler):
        """I/O operasyonlarını profiler"""
        # Prepare test data
        test_data = [
            {'id': i, 'data': 'x' * 1000}
            for i in range(10000)
        ]

        # Profile I/O operations
        io_stats = profiler.profile_io_operations(
            data=test_data,
            batch_size=1000
        )

        assert io_stats.disk_read_bytes < 1024 * 1024  # 1MB altı
        assert io_stats.disk_write_bytes < 1024 * 1024
        assert io_stats.avg_io_wait < 0.1  # 100ms altı

    def test_network_profiling(self, profiler):
        """Network operasyonlarını profiler"""
        # Test scenarios
        scenarios = [
            {
                'query': 'SELECT * FROM users LIMIT 1000',
                'expected_size': 1000
            },
            {
                'query': 'SELECT id FROM users LIMIT 10000',
                'expected_size': 10000
            }
        ]

        for scenario in scenarios:
            network_stats = profiler.profile_network(
                query=scenario['query']
            )

            assert network_stats.bytes_sent > 0
            assert network_stats.bytes_received > 0
            assert network_stats.latency < 0.1  # 100ms altı
            assert len(network_stats.connections) <= 10