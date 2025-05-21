"""
SQL Parser Service for SQL Proxy

This service provides parsing and analysis of SQL queries, extracting
tables, columns, clauses, and other metadata.

Last updated: 2025-05-20 06:53:16
Updated by: Teeksss
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from sqlparse import parse as sqlparse_parse
from sqlparse import tokens as T
from sqlparse.sql import (
    Identifier, IdentifierList, Parenthesis, Where, Comparison,
    Function, Operation, Statement, TokenList
)

logger = logging.getLogger(__name__)

class SQLParser:
    """
    SQL Parser service for analyzing SQL queries
    
    Uses sqlparse and additional logic to extract query metadata.
    """
    
    def __init__(self):
        """Initialize the SQL parser service"""
        # Common SQL types for queries
        self.select_keywords = {'SELECT'}
        self.update_keywords = {'UPDATE'}
        self.insert_keywords = {'INSERT'}
        self.delete_keywords = {'DELETE'}
        self.create_keywords = {'CREATE'}
        self.drop_keywords = {'DROP'}
        self.alter_keywords = {'ALTER'}
        self.truncate_keywords = {'TRUNCATE'}
        
        # Join types
        self.join_keywords = {
            'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 
            'LEFT OUTER JOIN', 'RIGHT OUTER JOIN', 'FULL JOIN',
            'FULL OUTER JOIN', 'CROSS JOIN'
        }
        
        logger.info("SQL Parser service initialized")
    
    def parse_query(self, sql_query: str) -> Optional[Dict[str, Any]]:
        """
        Parse a SQL query and extract metadata
        
        Args:
            sql_query: SQL query string to parse
            
        Returns:
            Dictionary with query metadata or None if parsing fails
        """
        if not sql_query:
            return None
        
        try:
            # Parse the query using sqlparse
            parsed = sqlparse_parse(sql_query)
            
            if not parsed or not parsed[0].tokens:
                logger.warning("Failed to parse SQL query")
                return None
            
            # Get the first statement (we don't handle multiple statements)
            statement = parsed[0]
            
            # Basic query structure
            result = {
                "query_type": self._determine_query_type(statement),
                "tables": self._extract_tables(statement),
                "query_text": sql_query
            }
            
            # Add query-type specific metadata
            if result["query_type"] == "SELECT":
                result.update(self._process_select_query(statement))
            elif result["query_type"] == "UPDATE":
                result.update(self._process_update_query(statement))
            elif result["query_type"] == "INSERT":
                result.update(self._process_insert_query(statement))
            elif result["query_type"] == "DELETE":
                result.update(self._process_delete_query(statement))
            elif result["query_type"] in ["CREATE", "ALTER", "DROP"]:
                result.update(self._process_ddl_query(statement))
            
            return result
        except Exception as e:
            logger.error(f"Error parsing SQL query: {str(e)}")
            return {
                "query_type": "UNKNOWN",
                "error": str(e),
                "query_text": sql_query
            }
    
    def _determine_query_type(self, statement: Statement) -> str:
        """
        Determine the type of SQL query
        
        Args:
            statement: SQL statement to analyze
            
        Returns:
            Query type string (SELECT, UPDATE, INSERT, DELETE, etc.)
        """
        # Extract the first token that's not whitespace
        first_token = None
        for token in statement.tokens:
            if token.ttype != T.Whitespace:
                first_token = token
                break
        
        if not first_token:
            return "UNKNOWN"
        
        # Check the token value against known query types
        token_val = first_token.value.upper()
        
        if token_val in self.select_keywords:
            return "SELECT"
        elif token_val in self.update_keywords:
            return "UPDATE"
        elif token_val in self.insert_keywords:
            return "INSERT"
        elif token_val in self.delete_keywords:
            return "DELETE"
        elif token_val in self.create_keywords:
            return "CREATE"
        elif token_val in self.drop_keywords:
            return "DROP"
        elif token_val in self.alter_keywords:
            return "ALTER"
        elif token_val in self.truncate_keywords:
            return "TRUNCATE"
        else:
            return "UNKNOWN"
    
    def _extract_tables(self, statement: Statement) -> List[str]:
        """
        Extract table names from a SQL statement
        
        Args:
            statement: SQL statement to analyze
            
        Returns:
            List of table names
        """
        tables = []
        query_type = self._determine_query_type(statement)
        
        # Different table extraction based on query type
        if query_type == "SELECT":
            # For SELECT, tables are in FROM clause
            from_seen = False
            for token in statement.tokens:
                if token.ttype == T.Keyword and token.value.upper() == "FROM":
                    from_seen = True
                    continue
                
                if from_seen and token.ttype != T.Whitespace:
                    # If there are joins, process separately
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            if identifier.value.upper() not in self.join_keywords:
                                tables.append(self._clean_identifier(identifier.value))
                    else:
                        tables.append(self._clean_identifier(token.value))
                    break
            
            # Process JOIN clauses
            for token in statement.tokens:
                if isinstance(token, TokenList):
                    for sub_token in token.tokens:
                        join_match = re.match(r'(?i)(INNER |LEFT |RIGHT |FULL |CROSS )?JOIN\s+(\w+)', str(sub_token))
                        if join_match:
                            tables.append(join_match.group(2))
        
        elif query_type == "UPDATE":
            # For UPDATE, table is right after UPDATE keyword
            update_seen = False
            for token in statement.tokens:
                if token.ttype == T.Keyword and token.value.upper() == "UPDATE":
                    update_seen = True
                    continue
                
                if update_seen and token.ttype != T.Whitespace:
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            tables.append(self._clean_identifier(identifier.value))
                    else:
                        tables.append(self._clean_identifier(token.value))
                    break
        
        elif query_type == "DELETE":
            # For DELETE, check if there's a FROM clause
            from_seen = False
            for token in statement.tokens:
                if token.ttype == T.Keyword and token.value.upper() == "FROM":
                    from_seen = True
                    continue
                
                if from_seen and token.ttype != T.Whitespace:
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            tables.append(self._clean_identifier(identifier.value))
                    else:
                        tables.append(self._clean_identifier(token.value))
                    break
        
        elif query_type == "INSERT":
            # For INSERT, look for INTO and extract the table
            into_seen = False
            for token in statement.tokens:
                if token.ttype == T.Keyword and token.value.upper() == "INTO":
                    into_seen = True
                    continue
                
                if into_seen and token.ttype != T.Whitespace:
                    tables.append(self._clean_identifier(token.value))
                    break
        
        elif query_type in ["CREATE", "ALTER", "DROP", "TRUNCATE"]:
            # For DDL statements, look for TABLE keyword
            table_seen = False
            for token in statement.tokens:
                if token.ttype == T.Keyword and token.value.upper() == "TABLE":
                    table_seen = True
                    continue
                
                if table_seen and token.ttype != T.Whitespace:
                    tables.append(self._clean_identifier(token.value))
                    break
        
        # Return unique tables
        return list(set(tables))
    
    def _clean_identifier(self, identifier: str) -> str:
        """
        Clean a table or column identifier
        
        Args:
            identifier: Table or column identifier
            
        Returns:
            Cleaned identifier
        """
        # Remove schema prefixes
        if '.' in identifier:
            parts = identifier.split('.')
            identifier = parts[-1]
        
        # Remove aliases
        if ' AS ' in identifier.upper():
            identifier = identifier.split(' AS ')[0]
        elif ' ' in identifier:
            identifier = identifier.split(' ')[0]
        
        # Remove quotes
        identifier = identifier.strip('"\'`[]')
        
        return identifier
    
    def _process_select_query(self, statement: Statement) -> Dict[str, Any]:
        """
        Process a SELECT query and extract metadata
        
        Args:
            statement: SELECT SQL statement
            
        Returns:
            Dictionary with query metadata
        """
        result = {
            "columns": self._extract_select_columns(statement),
            "where": self._has_where_clause(statement),
            "joins": self._extract_joins(statement),
            "group_by": self._has_group_by(statement),
            "having": self._has_having(statement),
            "order_by": self._has_order_by(statement),
            "limit": self._extract_limit(statement)
        }
        
        return result
    
    def _process_update_query(self, statement: Statement) -> Dict[str, Any]:
        """
        Process an UPDATE query and extract metadata
        
        Args:
            statement: UPDATE SQL statement
            
        Returns:
            Dictionary with query metadata
        """
        # Extract columns being updated
        set_columns = []
        set_clause = False
        
        for token in statement.tokens:
            if token.ttype == T.Keyword and token.value.upper() == "SET":
                set_clause = True
                continue
            
            if set_clause and token.ttype != T.Whitespace:
                if isinstance(token, IdentifierList):
                    for item in token.get_identifiers():
                        if isinstance(item, Comparison):
                            set_columns.append(self._clean_identifier(item.left.value))
                elif isinstance(token, Comparison):
                    set_columns.append(self._clean_identifier(token.left.value))
                else:
                    # Handle complex cases with tokenization
                    assignments = str(token).split(',')
                    for assignment in assignments:
                        if '=' in assignment:
                            column = assignment.split('=')[0].strip()
                            set_columns.append(self._clean_identifier(column))
                break
        
        result = {
            "columns": set_columns,
            "where": self._has_where_clause(statement)
        }
        
        return result
    
    def _process_insert_query(self, statement: Statement) -> Dict[str, Any]:
        """
        Process an INSERT query and extract metadata
        
        Args:
            statement: INSERT SQL statement
            
        Returns:
            Dictionary with query metadata
        """
        # Extract columns being inserted
        columns = []
        column_list_seen = False
        values_seen = False
        
        for token in statement.tokens:
            # Check for explicit column list
            if isinstance(token, Parenthesis) and not values_seen:
                column_list_seen = True
                for item in token.tokens:
                    if isinstance(item, IdentifierList):
                        for ident in item.get_identifiers():
                            columns.append(self._clean_identifier(ident.value))
            
            # Check for VALUES keyword
            if token.ttype == T.Keyword and token.value.upper() == "VALUES":
                values_seen = True
            
            # If no explicit columns, check for SELECT or VALUES
            if values_seen and not column_list_seen:
                # Either it's specifying all columns or it's a SELECT subquery
                for inner_token in statement.tokens:
                    if inner_token.ttype == T.Keyword and inner_token.value.upper() == "SELECT":
                        # It's an INSERT ... SELECT query
                        columns = ["*"]  # Unable to determine exact columns
                        break
        
        result = {
            "columns": columns
        }
        
        return result
    
    def _process_delete_query(self, statement: Statement) -> Dict[str, Any]:
        """
        Process a DELETE query and extract metadata
        
        Args:
            statement: DELETE SQL statement
            
        Returns:
            Dictionary with query metadata
        """
        result = {
            "where": self._has_where_clause(statement)
        }
        
        return result
    
    def _process_ddl_query(self, statement: Statement) -> Dict[str, Any]:
        """
        Process a DDL query (CREATE, ALTER, DROP) and extract metadata
        
        Args:
            statement: DDL SQL statement
            
        Returns:
            Dictionary with query metadata
        """
        result = {}
        
        # Determine what type of object is being created/altered/dropped
        object_type = None
        for token in statement.tokens:
            if token.ttype == T.Keyword and token.value.upper() in ["TABLE", "INDEX", "VIEW", "PROCEDURE", "FUNCTION", "TRIGGER"]:
                object_type = token.value.upper()
                break
        
        result["object_type"] = object_type
        
        # For CREATE TABLE, try to extract columns
        if statement.get_type() == 'CREATE' and object_type == 'TABLE':
            columns = []
            for token in statement.tokens:
                if isinstance(token, Parenthesis):
                    for item in token.tokens:
                        if isinstance(item, Function) or isinstance(item, Identifier):
                            if not item.value.startswith('CONSTRAINT') and not item.value.startswith('PRIMARY KEY'):
                                # Extract column name
                                try:
                                    column_def = str(item).strip().split()[0]
                                    columns.append(self._clean_identifier(column_def))
                                except:
                                    pass
            
            result["columns"] = columns
        
        return result
    
    def _extract_select_columns(self, statement: Statement) -> List[str]:
        """
        Extract columns from a SELECT query
        
        Args:
            statement: SELECT SQL statement
            
        Returns:
            List of column names
        """
        columns = []
        select_seen = False
        from_seen = False
        
        for token in statement.tokens:
            # Skip until we find SELECT
            if token.ttype == T.Keyword.DML and token.value.upper() == "SELECT":
                select_seen = True
                continue
            
            # Stop when we reach FROM
            if token.ttype == T.Keyword and token.value.upper() == "FROM":
                from_seen = True
                break
            
            # Process columns between SELECT and FROM
            if select_seen and not from_seen and token.ttype != T.Whitespace:
                if token.value == '*':
                    columns.append('*')
                elif isinstance(token, IdentifierList):
                    for ident in token.get_identifiers():
                        if isinstance(ident, Function):
                            # For aggregates like COUNT(), SUM(), etc.
                            columns.append(str(ident))
                        else:
                            columns.append(self._clean_identifier(ident.value))
                elif isinstance(token, Identifier) or isinstance(token, Function):
                    columns.append(self._clean_identifier(token.value))
                else:
                    # Handle complex cases
                    col_text = token.value.strip()
                    if col_text and col_text != ',':
                        cols = col_text.split(',')
                        for col in cols:
                            col = col.strip()
                            if col:
                                columns.append(self._clean_identifier(col))
        
        return columns
    
    def _has_where_clause(self, statement: Statement) -> bool:
        """
        Check if a SQL statement has a WHERE clause
        
        Args:
            statement: SQL statement
            
        Returns:
            True if statement has a WHERE clause, False otherwise
        """
        for token in statement.tokens:
            if isinstance(token, Where):
                return True
        
        # Also check tokens directly for simple cases
        for i, token in enumerate(statement.tokens):
            if token.ttype == T.Keyword and token.value.upper() == "WHERE":
                return True
        
        return False
    
    def _extract_joins(self, statement: Statement) -> List[Dict[str, str]]:
        """
        Extract JOIN clauses from a SELECT query
        
        Args:
            statement: SELECT SQL statement
            
        Returns:
            List of dictionaries with join information
        """
        joins = []
        for token in statement.tokens:
            join_match = re.search(r'(?i)(INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+(\w+)(?:\s+AS\s+(\w+))?(?:\s+ON\s+(.+))?', str(token))
            if join_match:
                join_type = (join_match.group(1) or "").upper() + " JOIN" if join_match.group(1) else "JOIN"
                join_type = join_type.strip()
                
                table = join_match.group(2)
                alias = join_match.group(3)
                condition = join_match.group(4)
                
                joins.append({
                    "type": join_type,
                    "table": table,
                    "alias": alias,
                    "condition": condition
                })
        
        return joins
    
    def _has_group_by(self, statement: Statement) -> bool:
        """
        Check if a SELECT query has a GROUP BY clause
        
        Args:
            statement: SELECT SQL statement
            
        Returns:
            True if query has a GROUP BY clause, False otherwise
        """
        for i, token in enumerate(statement.tokens):
            if token.ttype == T.Keyword and token.value.upper() == "GROUP BY":
                return True
            elif token.ttype == T.Keyword and token.value.upper() == "GROUP" and i+1 < len(statement.tokens):
                next_token = statement.tokens[i+1]
                if next_token.ttype == T.Keyword and next_token.value.upper() == "BY":
                    return True
        
        return False
    
    def _has_having(self, statement: Statement) -> bool:
        """
        Check if a SELECT query has a HAVING clause
        
        Args:
            statement: SELECT SQL statement
            
        Returns:
            True if query has a HAVING clause, False otherwise
        """
        for token in statement.tokens:
            if token.ttype == T.Keyword and token.value.upper() == "HAVING":
                return True
        
        return False
    
    def _has_order_by(self, statement: Statement) -> bool:
        """
        Check if a SELECT query has an ORDER BY clause
        
        Args:
            statement: SELECT SQL statement
            
        Returns:
            True if query has an ORDER BY clause, False otherwise
        """
        for i, token in enumerate(statement.tokens):
            if token.ttype == T.Keyword and token.value.upper() == "ORDER BY":
                return True
            elif token.ttype == T.Keyword and token.value.upper() == "ORDER" and i+1 < len(statement.tokens):
                next_token = statement.tokens[i+1]
                if next_token.ttype == T.Keyword and next_token.value.upper() == "BY":
                    return True
        
        return False
    
    def _extract_limit(self, statement: Statement) -> Optional[int]:
        """
        Extract LIMIT value from a SELECT query
        
        Args:
            statement: SELECT SQL statement
            
        Returns:
            Limit value as integer or None if no LIMIT clause
        """
        limit_seen = False
        
        for token in statement.tokens:
            if token.ttype == T.Keyword and token.value.upper() == "LIMIT":
                limit_seen = True
                continue
            
            if limit_seen and token.ttype != T.Whitespace:
                try:
                    # Extract the limit value
                    if token.ttype == T.Literal.Number.Integer:
                        return int(token.value)
                    else:
                        # Handle cases where the number might be in a different token type
                        limit_str = token.value.split(',')[0].strip()
                        return int(limit_str)
                except (ValueError, TypeError):
                    return None
        
        return None

# Son güncelleme: 2025-05-20 06:53:16
# Güncelleyen: Teeksss