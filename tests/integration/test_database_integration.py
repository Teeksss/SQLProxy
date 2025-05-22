import pytest
import asyncio
from sqlproxy.database import Database
from sqlproxy.models import QueryRequest, DatabaseConfig

class TestDatabaseIntegration:
    @pytest.fixture(scope="class")
    async def database(self):
        # Setup
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )
        db = Database(config)
        await db.connect()
        
        # Setup test data
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(255)
            )
        """)
        
        yield db
        
        # Cleanup
        await db.execute("DROP TABLE IF EXISTS test_users")
        await db.disconnect()
        
    @pytest.mark.asyncio
    async def test_insert_and_select(self, database):
        # Arrange
        insert_query = """
            INSERT INTO test_users (name, email)
            VALUES ($1, $2)
            RETURNING id
        """
        
        # Act
        result = await database.execute(
            insert_query,
            ["Test User", "test@example.com"]
        )
        
        select_result = await database.execute(
            "SELECT * FROM test_users WHERE id = $1",
            [result[0]["id"]]
        )
        
        # Assert
        assert len(select_result) == 1
        assert select_result[0]["name"] == "Test User"
        
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, database):
        # Arrange
        async with database.transaction() as txn:
            # Act
            await txn.execute(
                "INSERT INTO test_users (name) VALUES ($1)",
                ["User 1"]
            )
            
            with pytest.raises(ValueError):
                await txn.execute("INVALID SQL")
                
        # Assert
        result = await database.execute(
            "SELECT * FROM test_users WHERE name = $1",
            ["User 1"]
        )
        assert len(result) == 0  # Should be rolled back