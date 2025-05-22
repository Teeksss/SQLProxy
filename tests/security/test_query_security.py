import pytest
from sqlproxy.security import SQLInjectionChecker
from sqlproxy.models import QueryRequest

class TestQuerySecurity:
    @pytest.fixture
    def security_checker(self):
        return SQLInjectionChecker()
        
    @pytest.mark.parametrize("query", [
        "SELECT * FROM users; DROP TABLE users;",
        "SELECT * FROM users WHERE id = 1 OR 1=1",
        "SELECT * FROM users UNION SELECT * FROM sensitive_data",
    ])
    def test_sql_injection_detection(self, security_checker, query):
        # Act & Assert
        with pytest.raises(SecurityError) as exc:
            security_checker.check(query)
        assert "Potential SQL injection detected" in str(exc.value)
        
    def test_parameterized_queries(self, security_checker):
        # Arrange
        query = "SELECT * FROM users WHERE id = $1"
        params = [1]
        
        # Act
        result = security_checker.check(query, params)
        
        # Assert
        assert result.is_safe == True
        
    @pytest.mark.parametrize("permission,expected", [
        ("read", True),
        ("write", False),
        ("admin", True),
    ])
    def test_permission_checks(self, permission, expected):
        # Arrange
        query = "SELECT * FROM sensitive_table"
        user = {"permissions": [permission]}
        
        # Act
        result = security_checker.check_permissions(
            query, user
        )
        
        # Assert
        assert result == expected