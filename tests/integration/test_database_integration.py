import pytest
from sqlproxy.core.database.integration import DatabaseIntegration

@pytest.fixture
def db_integration():
    return DatabaseIntegration(
        "postgresql://postgres:postgres@localhost:5432/test_db"
    )

def test_database_connection(db_integration):
    assert db_integration.test_connection()

def test_query_execution(db_integration):
    result = db_integration.execute_query("SELECT 1 as test")
    assert len(result) == 1
    assert result[0]['test'] == 1