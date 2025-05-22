from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class QueryCondition:
    column: str
    operator: str
    value: Any

@dataclass
class JoinClause:
    table: str
    type: str  # INNER, LEFT, RIGHT, FULL
    conditions: List[QueryCondition]

class QueryBuilder:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self._type = 'SELECT'
        self._tables = []
        self._columns = ['*']
        self._conditions = []
        self._joins = []
        self._group_by = []
        self._having = []
        self._order_by = []
        self._limit = None
        self._offset = None
        
    def select(self, *columns: str) -> 'QueryBuilder':
        self._type = 'SELECT'
        self._columns = list(columns) if columns else ['*']
        return self
        
    def from_table(self, table: str) -> 'QueryBuilder':
        self._tables.append(table)
        return self
        
    def where(self, condition: QueryCondition) -> 'QueryBuilder':
        self._conditions.append(condition)
        return self
        
    def join(self, join_clause: JoinClause) -> 'QueryBuilder':
        self._joins.append(join_clause)
        return self
        
    def group_by(self, *columns: str) -> 'QueryBuilder':
        self._group_by.extend(columns)
        return self
        
    def having(self, condition: QueryCondition) -> 'QueryBuilder':
        self._having.append(condition)
        return self
        
    def order_by(self, column: str, desc: bool = False) -> 'QueryBuilder':
        self._order_by.append((column, desc))
        return self
        
    def limit(self, limit: int) -> 'QueryBuilder':
        self._limit = limit
        return self
        
    def offset(self, offset: int) -> 'QueryBuilder':
        self._offset = offset
        return self
        
    def build(self) -> str:
        query_parts = []
        
        # SELECT
        columns = ', '.join(self._columns)
        query_parts.append(f"SELECT {columns}")
        
        # FROM
        tables = ', '.join(self._tables)
        query_parts.append(f"FROM {tables}")
        
        # JOINS
        if self._joins:
            for join in self._joins:
                conditions = ' AND '.join(
                    f"{c.column} {c.operator} {c.value}"
                    for c in join.conditions
                )
                query_parts.append(
                    f"{join.type} JOIN {join.table} ON {conditions}"
                )
                
        # WHERE
        if self._conditions:
            conditions = ' AND '.join(
                f"{c.column} {c.operator} {c.value}"
                for c in self._conditions
            )
            query_parts.append(f"WHERE {conditions}")
            
        # GROUP BY
        if self._group_by:
            columns = ', '.join(self._group_by)
            query_parts.append(f"GROUP BY {columns}")
            
        # HAVING
        if self._having:
            conditions = ' AND '.join(
                f"{c.column} {c.operator} {c.value}"
                for c in self._having
            )
            query_parts.append(f"HAVING {conditions}")
            
        # ORDER BY
        if self._order_by:
            order = ', '.join(
                f"{column} {'DESC' if desc else 'ASC'}"
                for column, desc in self._order_by
            )
            query_parts.append(f"ORDER BY {order}")
            
        # LIMIT & OFFSET
        if self._limit is not None:
            query_parts.append(f"LIMIT {self._limit}")
            
        if self._offset is not None:
            query_parts.append(f"OFFSET {self._offset}")
            
        return ' '.join(query_parts)