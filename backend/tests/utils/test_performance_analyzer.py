"""
Tests for Performance Analyzer

This module contains tests for the performance analyzer utilities.

Last updated: 2025-05-21 05:11:29
Updated by: Teeksss
"""

import unittest
import time
from unittest.mock import patch, MagicMock
import statistics
import threading

from app.utils.performance_analyzer import (
    measure_query_performance,
    measure_endpoint_performance,
    analyze_query_performance,
    get_performance_summary,
    export_performance_metrics,
    reset_performance_metrics
)
from app.core.config import settings

class TestPerformanceAnalyzer(unittest.TestCase):
    """Test cases for performance analyzer"""
    
    def setUp(self):
        """Set up test environment"""
        # Save current settings
        self.original_performance_enabled = settings.PERFORMANCE_MONITORING_ENABLED
        self.original_metrics_enabled = settings.METRICS_ENABLED
        self.original_slow_query_threshold = settings.SLOW_QUERY_THRESHOLD_MS
        self.original_slow_endpoint_threshold = settings.SLOW_ENDPOINT_THRESHOLD_MS
        
        # Enable performance monitoring for tests
        settings.PERFORMANCE_MONITORING_ENABLED = True
        settings.METRICS_ENABLED = False  # Disable Prometheus for tests
        settings.SLOW_QUERY_THRESHOLD_MS = 100
        settings.SLOW_ENDPOINT_THRESHOLD_MS = 100
        
        # Reset metrics before each test
        reset_performance_metrics()
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original settings
        settings.PERFORMANCE_MONITORING_ENABLED = self.original_performance_enabled
        settings.METRICS_ENABLED = self.original_metrics_enabled
        settings.SLOW_QUERY_THRESHOLD_MS = self.original_slow_query_threshold
        settings.SLOW_ENDPOINT_THRESHOLD_MS = self.original_slow_endpoint_threshold
    
    def test_measure_query_performance(self):
        """Test query performance measurement decorator"""
        @measure_query_performance(database="test_db", endpoint="test_endpoint")
        def sample_query():
            time.sleep(0.01)  # Simulate query execution
            return "result"
        
        # Execute the decorated function
        result = sample_query()
        
        # Verify the result
        self.assertEqual(result, "result")
        
        # Get performance summary
        summary = get_performance_summary()
        
        # Verify metrics were recorded
        self.assertIn("test_db", summary["queries"])
        self.assertIn("test_endpoint", summary["queries"]["test_db"]["endpoints"])
        self.assertEqual(summary["queries"]["test_db"]["count"], 1)
    
    def test_measure_endpoint_performance(self):
        """Test endpoint performance measurement decorator"""
        @measure_endpoint_performance(method="GET", endpoint="/test")
        def sample_endpoint():
            time.sleep(0.01)  # Simulate endpoint execution
            return {"status": "success"}
        
        # Execute the decorated function
        result = sample_endpoint()
        
        # Verify the result
        self.assertEqual(result, {"status": "success"})
        
        # Get performance summary
        summary = get_performance_summary()
        
        # Verify metrics were recorded
        self.assertIn("GET", summary["endpoints"])
        self.assertIn("/test", summary["endpoints"]["GET"]["endpoints"])
        self.assertEqual(summary["endpoints"]["GET"]["count"], 1)
    
    @patch("app.utils.performance_analyzer.engine")
    def test_analyze_query_performance(self, mock_engine):
        """Test query performance analysis"""
        # Mock SQLAlchemy connection and execution
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.begin.return_value.__enter__.return_value = MagicMock()
        
        # Mock execution results
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [{"plan": "Seq Scan on test_table"}]
        mock_connection.execute.return_value = mock_result
        
        # Mock engine dialect
        mock_engine.dialect.name = "postgresql"
        
        # Test the analyze function
        query = "SELECT * FROM test_table WHERE id = :id"
        params = {"id": 1}
        result = analyze_query_performance(query, params, iterations=2)
        
        # Verify the results
        self.assertIn("execution_times", result)
        self.assertIn("explain_plan", result)
        self.assertIn("suggestions", result)
        self.assertEqual(result["query"], query)
        self.assertEqual(result["parameters"], params)
        
        # Verify explain was called
        mock_connection.execute.assert_called()
    
    def test_get_performance_summary_empty(self):
        """Test getting performance summary with no data"""
        summary = get_performance_summary()
        
        self.assertIn("queries", summary)
        self.assertIn("endpoints", summary)
        self.assertEqual(len(summary["queries"]), 0)
        self.assertEqual(len(summary["endpoints"]), 0)
    
    def test_get_performance_summary_with_data(self):
        """Test getting performance summary with data"""
        # Add some test data
        @measure_query_performance(database="test_db", endpoint="test_endpoint")
        def test_query():
            time.sleep(0.01)
            return True
        
        @measure_endpoint_performance(method="GET", endpoint="/test")
        def test_endpoint():
            time.sleep(0.01)
            return True
        
        # Execute multiple times
        for _ in range(5):
            test_query()
            test_endpoint()
        
        # Get summary
        summary = get_performance_summary()
        
        # Verify summary data
        self.assertIn("test_db", summary["queries"])
        self.assertIn("GET", summary["endpoints"])
        self.assertEqual(summary["queries"]["test_db"]["count"], 5)
        self.assertEqual(summary["endpoints"]["GET"]["count"], 5)
    
    @patch("app.utils.performance_analyzer.open")
    @patch("app.utils.performance_analyzer.json.dump")
    @patch("app.utils.performance_analyzer.Path")
    def test_export_performance_metrics(self, mock_path, mock_json_dump, mock_open):
        """Test exporting performance metrics"""
        # Enable export
        settings.PERFORMANCE_METRICS_EXPORT_ENABLED = True
        settings.PERFORMANCE_METRICS_EXPORT_PATH = "test_path.json"
        
        # Add some test data
        @measure_query_performance(database="test_db", endpoint="test_endpoint")
        def test_query():
            return True
        
        test_query()
        
        # Export metrics
        export_performance_metrics()
        
        # Verify export was called
        mock_path.return_value.parent.mkdir.assert_called_once()
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()
    
    def test_reset_performance_metrics(self):
        """Test resetting performance metrics"""
        # Add some test data
        @measure_query_performance(database="test_db", endpoint="test_endpoint")
        def test_query():
            return True
        
        test_query()
        
        # Verify data exists
        summary_before = get_performance_summary()
        self.assertIn("test_db", summary_before["queries"])
        
        # Reset metrics
        reset_performance_metrics()
        
        # Verify data is cleared
        summary_after = get_performance_summary()
        self.assertEqual(len(summary_after["queries"]), 0)
    
    def test_thread_safety(self):
        """Test thread safety of performance metrics"""
        @measure_query_performance(database="test_db", endpoint="test_endpoint")
        def test_query():
            time.sleep(0.01)
            return True
        
        # Execute in multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=test_query)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all executions were recorded
        summary = get_performance_summary()
        self.assertEqual(summary["queries"]["test_db"]["count"], 10)

if __name__ == "__main__":
    unittest.main()

# Son güncelleme: 2025-05-21 05:11:29
# Güncelleyen: Teeksss