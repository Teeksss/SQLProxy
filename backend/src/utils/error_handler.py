from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from .logger import Logger

class ErrorHandler:
    def __init__(self):
        self.logger = Logger()
        
    async def handle_error(self, error: Exception,
                          context: Dict[str, Any] = None) -> Dict:
        """Hata yönetimi yapar."""
        try:
            # Log error
            await self.logger.error(
                str(error),
                context or {}
            )
            
            # Database errors
            if isinstance(error, SQLAlchemyError):
                return self._handle_db_error(error)
                
            # HTTP errors
            if isinstance(error, HTTPException):
                return self._handle_http_error(error)
                
            # Query errors
            if isinstance(error, QueryError):
                return self._handle_query_error(error)
                
            # Default error response
            return {
                'status': 'error',
                'message': str(error),
                'type': error.__class__.__name__
            }
            
        except Exception as e:
            # Fallback error handling
            return {
                'status': 'error',
                'message': 'Internal server error',
                'type': 'InternalError'
            }
            
    def _handle_db_error(self, error: SQLAlchemyError) -> Dict:
        """Database hatalarını yönetir."""
        return {
            'status': 'error',
            'type': 'DatabaseError',
            'message': str(error),
            'details': {
                'error_code': getattr(error, 'code', None),
                'constraint': getattr(error, 'constraint_name', None)
            }
        }
        
    def _handle_query_error(self, error: 'QueryError') -> Dict:
        """Query hatalarını yönetir."""
        return {
            'status': 'error',
            'type': 'QueryError',
            'message': error.message,
            'details': {
                'query': error.query,
                'position': error.position,
                'suggestion': error.suggestion
            }
        }