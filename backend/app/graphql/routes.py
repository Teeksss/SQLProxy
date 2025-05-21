"""
GraphQL API routes for SQL Proxy

This module provides the GraphQL API endpoint for the SQL Proxy system.

Last updated: 2025-05-20 10:34:03
Updated by: Teeksss
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from graphql import GraphQLError

from app.db.session import db_session
from app.auth.jwt import get_current_user
from app.graphql.schema import schema
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/graphql")
async def graphql_endpoint(request: Request, current_user = Depends(get_current_user)):
    """
    GraphQL API endpoint
    
    This endpoint processes GraphQL queries and mutations.
    """
    try:
        # Parse request
        data = await request.json()
        query = data.get("query")
        variables = data.get("variables", {})
        operation_name = data.get("operationName")
        
        if not query:
            raise HTTPException(status_code=400, detail="No GraphQL query provided")
        
        # Set request context
        context = {
            "request": request,
            "auth_token": request.headers.get("Authorization"),
            "db_session": db_session,
            "current_user": current_user,
        }
        
        # Execute query
        result = schema.execute(
            query,
            variable_values=variables,
            context_value=context,
            operation_name=operation_name
        )
        
        # Handle errors
        if result.errors:
            errors = [
                {
                    "message": str(error),
                    "locations": [
                        {
                            "line": loc.line, 
                            "column": loc.column
                        } for loc in error.locations
                    ] if error.locations else None,
                    "path": error.path
                }
                for error in result.errors
            ]
            
            # Log errors
            for error in result.errors:
                if not isinstance(error, GraphQLError):
                    logger.error(f"GraphQL execution error: {str(error)}")
            
            return JSONResponse(
                status_code=200,  # GraphQL returns 200 even for errors
                content={"data": result.data, "errors": errors}
            )
        
        # Return successful result
        return JSONResponse(content={"data": result.data})
    
    except Exception as e:
        logger.exception(f"Error processing GraphQL request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"errors": [{"message": "Internal server error processing GraphQL request"}]}
        )

@router.get("/graphql/schema")
async def graphql_schema(current_user = Depends(get_current_user)):
    """
    Get GraphQL schema
    
    This endpoint returns the GraphQL schema in SDL format.
    Only available to admin users.
    """
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to access schema")
    
    try:
        from graphql import print_schema
        schema_str = print_schema(schema.graphql_schema)
        
        return Response(
            content=schema_str,
            media_type="text/plain"
        )
    except Exception as e:
        logger.exception(f"Error getting GraphQL schema: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating GraphQL schema")

# Son güncelleme: 2025-05-20 10:34:03
# Güncelleyen: Teeksss