from sqlalchemy import create_engine, inspect
from typing import List, Dict

class DatabaseService:
    def __init__(self):
        self.engines = {}

    def get_tables(self, database: str) -> List[str]:
        engine = self.get_engine(database)
        inspector = inspect(engine)
        return inspector.get_table_names()

    def get_schema(self, database: str, table: str) -> List[Dict]:
        engine = self.get_engine(database)
        inspector = inspect(engine)
        return inspector.get_columns(table)