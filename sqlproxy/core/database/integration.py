from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

class DatabaseIntegration:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SQL query"""
        with self.session_scope() as session:
            result = session.execute(text(query), params or {})
            return [dict(row) for row in result]

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.session_scope() as session:
                session.execute(text('SELECT 1'))
            return True
        except Exception:
            return False

    def get_table_info(self, table_name: str) -> Dict:
        """Get table information"""
        with self.session_scope() as session:
            columns = session.execute(text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = :table
            """), {'table': table_name})
            
            return {
                'table_name': table_name,
                'columns': [dict(row) for row in columns]
            }