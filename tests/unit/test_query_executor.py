import pytest
from unittest.mock import Mock, patch
from sqlproxy.core.query_executor import QueryExecutor
from sqlproxy.models import QueryRequest, QueryResponse

class TestQueryExecutor:
    @pytest.fixture
    def executor(self):
        return QueryExecutor()
        
    @pytest.fixture
    def mock_db(self):
        return Mock()
        
    def test_simple_select_query(self, executor, mock_db):
        # Arrange
        query = "SELECT * FROM users"
        request = QueryRequest(query=query)
        
        mock_db.execute.return_value = [
            {"id": 1, "name": "Test User"}
        ]
        
        # Act
        with patch('sqlproxy.core.query_executor.get_db', 
                  return_value=mock_db):
            result = executor.execute(request)
            
        # Assert
        assert result.success == True
        assert len(result.data) == 1
        assert result.data[0]["name"] == "Test User"
        
    def test_invalid_query_syntax(self, executor):
        # Arrange
        query = "SELEC * FROM users"  # Intentional typo
        request = QueryRequest(query=query)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc:
            executor.execute(request)
        assert "Invalid SQL syntax" in str(exc.value)
        
    @pytest.mark.parametrize("query,expected_tables", [
        ("SELECT * FROM users", ["users"]),
        ("SELECT * FROM users JOIN orders ON users.id = orders.user_id",
         ["users", "orders"]),
    ])
    def test_table_extraction(self, executor, query, expected_tables):
        # Arrange
        request = QueryRequest(query=query)
        
        # Act
        tables = executor._extract_tables(request)
        
        # Assert
        assert set(tables) == set(expected_tables)