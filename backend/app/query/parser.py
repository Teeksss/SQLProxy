import sqlparse
from typing import Dict, List, Tuple, Set, Optional
from sqlparse.sql import IdentifierList, Identifier, Where, Parenthesis, Function
from sqlparse.tokens import Keyword, DML, Name, Punctuation

class SQLAnalyzer:
    """Analyzes SQL queries to extract metadata and structural information."""
    
    def __init__(self):
        self.query_types = {
            'SELECT': 'read',
            'INSERT': 'write',
            'UPDATE': 'write',
            'DELETE': 'write',
            'CREATE': 'ddl',
            'DROP': 'ddl',
            'ALTER': 'ddl',
            'TRUNCATE': 'ddl',
            'EXEC': 'procedure',
            'EXECUTE': 'procedure',
        }
    
    def parse_query(self, sql: str) -> Dict:
        """
        Parse SQL query and extract metadata.
        
        Args:
            sql: SQL query string
            
        Returns:
            Dictionary with query metadata:
            {
                'query_type': str,
                'tables': List[str],
                'columns': List[str],
                'has_where': bool,
                'has_limit': bool,
                'has_join': bool,
                'join_info': List[Dict],
                'has_group_by': bool,
                'group_by_columns': List[str],
                'has_order_by': bool,
                'order_by_columns': List[str],
                'has_having': bool,
                'has_subquery': bool,
                'risk_level': str,
                'sensitive_operations': List[str]
            }
        """
        parsed = sqlparse.parse(sql)
        if not parsed:
            return {
                'query_type': 'unknown',
                'tables': [],
                'columns': [],
                'has_where': False,
                'has_limit': False,
                'has_join': False,
                'join_info': [],
                'has_group_by': False,
                'group_by_columns': [],
                'has_order_by': False,
                'order_by_columns': [],
                'has_having': False,
                'has_subquery': False,
                'risk_level': 'unknown',
                'sensitive_operations': []
            }
        
        stmt = parsed[0]
        
        # Extract query type
        query_type = self._extract_query_type(stmt)
        
        # Extract tables
        tables = self._extract_tables(stmt)
        
        # Extract columns
        columns = self._extract_columns(stmt)
        
        # Check for WHERE clause
        has_where = self._has_where(stmt)
        
        # Check for LIMIT/TOP
        has_limit = self._has_limit(stmt)
        
        # Check for JOIN
        has_join, join_info = self._extract_joins(stmt)
        
        # Check for GROUP BY
        has_group_by, group_by_columns = self._extract_group_by(stmt)
        
        # Check for ORDER BY
        has_order_by, order_by_columns = self._extract_order_by(stmt)
        
        # Check for HAVING
        has_having = self._has_having(stmt)
        
        # Check for subqueries
        has_subquery = self._has_subquery(stmt)
        
        # Determine risk level and sensitive operations
        risk_level, sensitive_operations = self._assess_risk(
            query_type, 
            has_where, 
            has_limit,
            has_join,
            has_group_by,
            has_subquery,
            sql.lower()
        )
        
        return {
            'query_type': query_type,
            'tables': list(tables),
            'columns': list(columns),
            'has_where': has_where,
            'has_limit': has_limit,
            'has_join': has_join,
            'join_info': join_info,
            'has_group_by': has_group_by,
            'group_by_columns': group_by_columns,
            'has_order_by': has_order_by,
            'order_by_columns': order_by_columns,
            'has_having': has_having,
            'has_subquery': has_subquery,
            'risk_level': risk_level,
            'sensitive_operations': sensitive_operations
        }
    
    def _extract_query_type(self, stmt) -> str:
        """Extract the type of SQL query (SELECT, INSERT, etc.)."""
        for token in stmt.tokens:
            if token.ttype is DML or token.ttype is Keyword:
                token_value = token.value.upper()
                if token_value in self.query_types:
                    return self.query_types[token_value]
        return 'unknown'
    
    def _extract_tables(self, stmt) -> Set[str]:
        """Extract table names from SQL query."""
        tables = set()
        
        # Handle different query types
        if stmt.get_type() == 'SELECT':
            from_seen = False
            for token in stmt.tokens:
                if from_seen:
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            tables.add(str(identifier).strip('`"[]').split(' ')[-1])
                    elif isinstance(token, Identifier):
                        tables.add(str(token).strip('`"[]').split(' ')[-1])
                    elif token.ttype is Keyword and token.value.upper() in ('JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN'):
                        # Extract table from JOIN clause
                        join_idx = stmt.tokens.index(token)
                        if join_idx + 1 < len(stmt.tokens):
                            join_table = stmt.tokens[join_idx + 1]
                            if isinstance(join_table, Identifier):
                                tables.add(str(join_table).strip('`"[]').split(' ')[-1])
                if token.ttype is Keyword and token.value.upper() == 'FROM':
                    from_seen = True
        
        # Handle INSERT statements
        elif stmt.get_type() == 'INSERT':
            into_seen = False
            for token in stmt.tokens:
                if into_seen and isinstance(token, Identifier):
                    tables.add(str(token).strip('`"[]'))
                    break
                if token.ttype is Keyword and token.value.upper() == 'INTO':
                    into_seen = True
        
        # Handle UPDATE statements
        elif stmt.get_type() == 'UPDATE':
            update_seen = False
            for token in stmt.tokens:
                if update_seen and isinstance(token, Identifier):
                    tables.add(str(token).strip('`"[]'))
                    break
                if token.ttype is Keyword and token.value.upper() == 'UPDATE':
                    update_seen = True
        
        # Basic handling for other query types
        else:
            # Simplified table extraction for other query types
            for token in stmt.tokens:
                if isinstance(token, Identifier):
                    tables.add(str(token).strip('`"[]').split(' ')[-1])
        
        return tables
    
    def _extract_columns(self, stmt) -> Set[str]:
        """Extract column names from SQL query."""
        columns = set()
        
        # For SELECT statements
        if stmt.get_type() == 'SELECT':
            # Find the columns in the SELECT clause
            select_seen = False
            from_seen = False
            for token in stmt.tokens:
                if token.ttype is Keyword and token.value.upper() == 'SELECT':
                    select_seen = True
                    continue
                if token.ttype is Keyword and token.value.upper() == 'FROM':
                    from_seen = True
                    break
                if select_seen and not from_seen:
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            col = str(identifier).strip('`"[]').split('.')[-1].split(' ')[-1]
                            if col != '*':
                                columns.add(col)
                    elif isinstance(token, Identifier):
                        col = str(token).strip('`"[]').split('.')[-1].split(' ')[-1]
                        if col != '*':
                            columns.add(col)
        
        # For UPDATE statements
        elif stmt.get_type() == 'UPDATE':
            set_seen = False
            where_seen = False
            for token in stmt.tokens:
                if token.ttype is Keyword and token.value.upper() == 'SET':
                    set_seen = True
                    continue
                if isinstance(token, Where):
                    where_seen = True
                    break
                if set_seen and not where_seen:
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            for id_token in identifier.tokens:
                                if isinstance(id_token, Identifier):
                                    columns.add(str(id_token).strip('`"[]'))
                    elif isinstance(token, Identifier):
                        columns.add(str(token).strip('`"[]'))
        
        return columns
    
    def _has_where(self, stmt) -> bool:
        """Check if SQL has a WHERE clause."""
        for token in stmt.tokens:
            if isinstance(token, Where):
                return True
        return False
    
    def _has_limit(self, stmt) -> bool:
        """Check if SQL has a LIMIT or TOP clause."""
        sql_lower = stmt.value.lower()
        return ' limit ' in sql_lower or ' top ' in sql_lower
    
    def _extract_joins(self, stmt) -> Tuple[bool, List[Dict]]:
        """
        Extract JOIN information from SQL query.
        
        Returns:
            Tuple of (has_join, join_info)
            join_info is a list of dictionaries with structure:
            {
                'type': str,  # JOIN, INNER JOIN, LEFT JOIN, etc.
                'table': str,
                'condition': str (if available)
            }
        """
        joins = []
        has_join = False
        sql_lower = stmt.value.lower()
        
        # Quick check for any join keywords
        join_keywords = ['join', 'inner join', 'left join', 'right join', 'full join', 'cross join']
        if not any(join_keyword in sql_lower for join_keyword in join_keywords):
            return False, []
        
        # Detailed analysis for join information
        join_seen = False
        join_type = None
        join_table = None
        on_clause = None
        
        for token in stmt.tokens:
            if token.ttype is Keyword and token.value.upper() in (
                'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'CROSS JOIN'
            ):
                # If we were processing a join, save it before starting new one
                if join_seen and join_table:
                    joins.append({
                        'type': join_type,
                        'table': join_table,
                        'condition': on_clause
                    })
                
                join_seen = True
                join_type = token.value.upper()
                join_table = None
                on_clause = None
                
            elif join_seen and join_type and not join_table and isinstance(token, Identifier):
                join_table = str(token).strip('`"[]')
                
            elif join_seen and join_table and token.ttype is Keyword and token.value.upper() == 'ON':
                # Find the ON condition
                on_idx = stmt.tokens.index(token)
                if on_idx + 1 < len(stmt.tokens):
                    on_token = stmt.tokens[on_idx + 1]
                    if isinstance(on_token, Parenthesis):
                        on_clause = str(on_token).strip('()')
        
        # Add the last join if processing one
        if join_seen and join_table:
            joins.append({
                'type': join_type,
                'table': join_table,
                'condition': on_clause
            })
        
        has_join = len(joins) > 0
        return has_join, joins
    
    def _extract_group_by(self, stmt) -> Tuple[bool, List[str]]:
        """
        Extract GROUP BY information from SQL query.
        
        Returns:
            Tuple of (has_group_by, group_by_columns)
        """
        group_by_columns = []
        sql_lower = stmt.value.lower()
        
        # Quick check for group by keyword
        if 'group by' not in sql_lower:
            return False, []
        
        # Detailed analysis for group by columns
        group_by_seen = False
        having_seen = False
        order_by_seen = False
        
        for token in stmt.tokens:
            if token.ttype is Keyword and token.value.upper() == 'GROUP BY':
                group_by_seen = True
                continue
                
            if token.ttype is Keyword and token.value.upper() in ('HAVING', 'ORDER BY'):
                if token.value.upper() == 'HAVING':
                    having_seen = True
                else:
                    order_by_seen = True
                break
                
            if group_by_seen and not having_seen and not order_by_seen:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        group_by_columns.append(str(identifier).strip('`"[]'))
                elif isinstance(token, Identifier):
                    group_by_columns.append(str(token).strip('`"[]'))
        
        has_group_by = len(group_by_columns) > 0
        return has_group_by, group_by_columns
    
    def _extract_order_by(self, stmt) -> Tuple[bool, List[str]]:
        """
        Extract ORDER BY information from SQL query.
        
        Returns:
            Tuple of (has_order_by, order_by_columns)
        """
        order_by_columns = []
        sql_lower = stmt.value.lower()
        
        # Quick check for order by keyword
        if 'order by' not in sql_lower:
            return False, []
        
        # Detailed analysis for order by columns
        order_by_seen = False
        limit_seen = False
        
        for token in stmt.tokens:
            if token.ttype is Keyword and token.value.upper() == 'ORDER BY':
                order_by_seen = True
                continue
                
            if token.ttype is Keyword and token.value.upper() in ('LIMIT', 'OFFSET'):
                limit_seen = True
                break
                
            if order_by_seen and not limit_seen:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        order_by_columns.append(str(identifier).strip('`"[]'))
                elif isinstance(token, Identifier):
                    order_by_columns.append(str(token).strip('`"[]'))
        
        has_order_by = len(order_by_columns) > 0
        return has_order_by, order_by_columns
    
    def _has_having(self, stmt) -> bool:
        """Check if SQL has a HAVING clause."""
        sql_lower = stmt.value.lower()
        return ' having ' in sql_lower
    
    def _has_subquery(self, stmt) -> bool:
        """Check if SQL has subqueries."""
        # Look for subquery patterns like (SELECT ...)
        sql_lower = stmt.value.lower()
        parenthesis_count = 0
        in_subquery = False
        
        for i, char in enumerate(sql_lower):
            if char == '(':
                parenthesis_count += 1
                # Check if this is the start of a subquery
                next_word = self._get_next_word(sql_lower[i+1:]).strip()
                if next_word.upper() in ('SELECT', 'WITH'):
                    in_subquery = True
                    return True
            elif char == ')':
                parenthesis_count -= 1
                
        # Also check for common table expressions (WITH ... AS)
        return ' with ' in sql_lower and ' as ' in sql_lower
    
    def _get_next_word(self, s: str) -> str:
        """Get the next word from a string, skipping whitespace."""
        word = ''
        for char in s:
            if char.isspace():
                if word:
                    break
            else:
                word += char
        return word
    
    def _assess_risk(
        self, 
        query_type: str, 
        has_where: bool, 
        has_limit: bool,
        has_join: bool,
        has_group_by: bool,
        has_subquery: bool,
        sql_lower: str
    ) -> Tuple[str, List[str]]:
        """
        Assess the risk level of a query.
        
        Returns:
            Tuple of (risk_level, sensitive_operations)
            
            risk_level can be:
            - 'high': Potentially dangerous operations
            - 'medium': Operations that may need review
            - 'low': Safe operations
            
            sensitive_operations is a list of strings describing risky operations
        """
        sensitive_operations = []
        
        # Check for potentially risky operations
        if 'drop ' in sql_lower:
            sensitive_operations.append('DROP operation detected')
        if 'truncate ' in sql_lower:
            sensitive_operations.append('TRUNCATE operation detected')
        if 'delete ' in sql_lower and not has_where:
            sensitive_operations.append('DELETE without WHERE clause')
        if 'update ' in sql_lower and not has_where:
            sensitive_operations.append('UPDATE without WHERE clause')
        if 'create ' in sql_lower:
            sensitive_operations.append('CREATE operation detected')
        if 'alter ' in sql_lower:
            sensitive_operations.append('ALTER operation detected')
        if 'exec ' in sql_lower or 'execute ' in sql_lower:
            sensitive_operations.append('Stored procedure execution')
        if 'sp_' in sql_lower or 'xp_' in sql_lower:
            sensitive_operations.append('System procedure call detected')
        
        # Check for common SQL injection patterns
        if "'" in sql_lower or ";" in sql_lower:
            if "'" in sql_lower:
                sensitive_operations.append('Contains single quotes')
            if ";" in sql_lower:
                sensitive_operations.append('Contains semicolons')
        
        # Assess overall risk level
        risk_level = 'low'
        if query_type in ('write', 'ddl', 'procedure'):
            risk_level = 'medium'
        
        if len(sensitive_operations) > 0:
            risk_level = 'high'
        
        return risk_level, sensitive_operations
    
    def format_join_info(self, join_info: List[Dict]) -> str:
        """
        Format join information for display.
        
        Args:
            join_info: List of join dictionaries from _extract_joins
            
        Returns:
            Formatted string describing the joins
        """
        if not join_info:
            return "No joins"
        
        join_strings = []
        for join in join_info:
            join_type = join['type'].replace('JOIN', 'join').title()
            join_str = f"{join_type} on {join['table']}"
            if join['condition']:
                join_str += f" where {join['condition']}"
            join_strings.append(join_str)
        
        return ", ".join(join_strings)
    
    def format_group_by_info(self, group_by_columns: List[str], has_having: bool) -> str:
        """
        Format GROUP BY information for display.
        
        Args:
            group_by_columns: List of columns in GROUP BY clause
            has_having: Whether a HAVING clause is present
            
        Returns:
            Formatted string describing the GROUP BY
        """
        if not group_by_columns:
            return "No grouping"
        
        group_str = f"Grouped by {', '.join(group_by_columns)}"
        if has_having:
            group_str += " with HAVING condition"
        
        return group_str
    
    def get_summary(self, sql: str) -> Dict:
        """
        Get a human-readable summary of the SQL query.
        
        Args:
            sql: SQL query string
            
        Returns:
            Dictionary with summary information
        """
        analysis = self.parse_query(sql)
        
        # Determine query description
        operation = "Unknown operation"
        if analysis['query_type'] == 'read':
            operation = "Selecting data"
            if analysis['has_join']:
                operation = "Selecting data with joins"
            if analysis['has_group_by']:
                operation = "Aggregating data"
        elif analysis['query_type'] == 'write':
            if 'insert' in sql.lower():
                operation = "Inserting data"
            elif 'update' in sql.lower():
                operation = "Updating data"
            elif 'delete' in sql.lower():
                operation = "Deleting data"
        elif analysis['query_type'] == 'ddl':
            operation = "Modifying database structure"
        elif analysis['query_type'] == 'procedure':
            operation = "Executing stored procedure"
        
        # Determine data scope
        scope = "Unknown scope"
        if analysis['tables']:
            if len(analysis['tables']) == 1:
                scope = f"From table {next(iter(analysis['tables']))}"
            else:
                scope = f"From tables {', '.join(analysis['tables'])}"
        
        # Format filtering info
        filtering = "No filtering"
        if analysis['has_where']:
            filtering = "With WHERE conditions"
        
        # Format join info
        joins = self.format_join_info(analysis['join_info'])
        
        # Format grouping info
        grouping = self.format_group_by_info(
            analysis['group_by_columns'], 
            analysis['has_having']
        )
        
        # Format ordering info
        ordering = "No specific ordering"
        if analysis['has_order_by']:
            ordering = f"Ordered by {', '.join(analysis['order_by_columns'])}"
        
        # Format limit info
        limiting = "No row limit"
        if analysis['has_limit']:
            limiting = "With row limit"
        
        return {
            'operation': operation,
            'scope': scope,
            'filtering': filtering,
            'joins': joins,
            'grouping': grouping,
            'ordering': ordering,
            'limiting': limiting,
            'risk_level': analysis['risk_level'],
            'sensitive_operations': analysis['sensitive_operations']
        }