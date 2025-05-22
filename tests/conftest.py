import pytest

def pytest_configure(config):
    """Test markerlarını tanımla"""
    config.addinivalue_line(
        "markers",
        "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", 
        "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers",
        "performance: Performance tests"
    )
    config.addinivalue_line(
        "markers",
        "benchmark: Benchmark tests"
    )
    config.addinivalue_line(
        "markers",
        "security: Security tests"
    )

@pytest.fixture(scope="session")
def test_categories():
    """Test kategorilerini tanımlar"""
    return {
        'unit': ['core', 'utils', 'security'],
        'integration': ['database', 'redis', 'api'],
        'performance': ['benchmarks', 'profiling', 'load'],
        'security': ['injection', 'authentication', 'authorization']
    }