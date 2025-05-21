"""
Format API endpoints for SQL Proxy

This module provides API endpoints for formatting query results
in different output formats like JSON, XML, CSV.

Last updated: 2025-05-20 11:32:47
Updated by: Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Response
from typing import Dict, List, Any, Optional, Union

from app.services.formatters import JSONFormatter, XMLFormatter, CSVFormatter
from app.auth.jwt import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/json")
async def format_json(
    result: Dict[str, Any] = Body(...),
    format_type: str = Body("standard"),
    pretty: bool = Body(False),
    indent: int = Body(2),
    null_value: Optional[str] = Body(None),
    include_metadata: bool = Body(True),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    Format query result as JSON
    
    Args:
        result: Query result to format
        format_type: Format type (standard, objects, table, key_value_pairs)
        pretty: Whether to format with indentation
        indent: Indentation level if pretty is True
        null_value: Custom value for SQL NULL values
        include_metadata: Whether to include metadata
        current_user: Current user (for authentication)
        
    Returns:
        Formatted JSON response
    """
    try:
        # Validate result structure
        if "columns" not in result or "data" not in result:
            raise HTTPException(status_code=400, detail="Invalid result format. Must contain 'columns' and 'data'.")
        
        # Format based on requested type
        if format_type == "standard":
            formatted = JSONFormatter.format_standard(
                result=result,
                pretty=pretty,
                indent=indent,
                null_value=null_value
            )
        elif format_type == "objects":
            formatted = JSONFormatter.format_objects(
                result=result,
                pretty=pretty,
                indent=indent,
                null_value=null_value,
                include_metadata=include_metadata
            )
        elif format_type == "table":
            formatted = JSONFormatter.format_table(
                result=result,
                pretty=pretty,
                indent=indent,
                null_value=null_value,
                include_metadata=include_metadata
            )
        elif format_type == "key_value_pairs":
            formatted = JSONFormatter.format_key_value_pairs(
                result=result,
                pretty=pretty,
                indent=indent,
                null_value=null_value,
                include_metadata=include_metadata
            )
        else:
            raise HTTPException(status_code=400, 
                             detail=f"Invalid format_type: {format_type}. Must be one of: standard, objects, table, key_value_pairs")
        
        return Response(
            content=formatted,
            media_type="application/json"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error formatting as JSON: {str(e)}")

@router.post("/xml")
async def format_xml(
    result: Dict[str, Any] = Body(...),
    format_type: str = Body("standard"),
    pretty: bool = Body(True),
    null_value: Optional[str] = Body(None),
    root_element: str = Body("result"),
    row_element: str = Body("row"),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    Format query result as XML
    
    Args:
        result: Query result to format
        format_type: Format type (standard, attributes)
        pretty: Whether to format with indentation
        null_value: Custom value for SQL NULL values
        root_element: Name of root XML element
        row_element: Name of row XML element
        current_user: Current user (for authentication)
        
    Returns:
        Formatted XML response
    """
    try:
        # Validate result structure
        if "columns" not in result or "data" not in result:
            raise HTTPException(status_code=400, detail="Invalid result format. Must contain 'columns' and 'data'.")
        
        # Format based on requested type
        if format_type == "standard":
            formatted = XMLFormatter.format_standard(
                result=result,
                pretty=pretty,
                null_value=null_value,
                root_element=root_element,
                row_element=row_element
            )
        elif format_type == "attributes":
            formatted = XMLFormatter.format_attributes(
                result=result,
                pretty=pretty,
                null_value=null_value,
                root_element=root_element,
                row_element=row_element
            )
        else:
            raise HTTPException(status_code=400, 
                             detail=f"Invalid format_type: {format_type}. Must be one of: standard, attributes")
        
        return Response(
            content=formatted,
            media_type="application/xml"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error formatting as XML: {str(e)}")

@router.post("/csv")
async def format_csv(
    result: Dict[str, Any] = Body(...),
    include_header: bool = Body(True),
    delimiter: str = Body(","),
    quotechar: str = Body('"'),
    null_value: str = Body(""),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    Format query result as CSV
    
    Args:
        result: Query result to format
        include_header: Whether to include column headers
        delimiter: CSV delimiter character
        quotechar: CSV quote character
        null_value: Value to use for SQL NULL values
        current_user: Current user (for authentication)
        
    Returns:
        Formatted CSV response
    """
    try:
        # Validate result structure
        if "columns" not in result or "data" not in result:
            raise HTTPException(status_code=400, detail="Invalid result format. Must contain 'columns' and 'data'.")
        
        # Validate delimiter and quotechar
        if len(delimiter) != 1:
            raise HTTPException(status_code=400, detail="Delimiter must be a single character")
        
        if len(quotechar) != 1:
            raise HTTPException(status_code=400, detail="Quotechar must be a single character")
        
        # Format as CSV
        formatted = CSVFormatter.format(
            result=result,
            include_header=include_header,
            delimiter=delimiter,
            quotechar=quotechar,
            null_value=null_value
        )
        
        return Response(
            content=formatted,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=query_result.csv"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error formatting as CSV: {str(e)}")

@router.post("/auto")
async def format_auto(
    result: Dict[str, Any] = Body(...),
    format: str = Body(...),
    options: Dict[str, Any] = Body({}),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    Format query result based on requested format
    
    Args:
        result: Query result to format
        format: Requested format (json, xml, csv)
        options: Format-specific options
        current_user: Current user (for authentication)
        
    Returns:
        Formatted response
    """
    # Validate format
    format_lower = format.lower()
    if format_lower not in ["json", "xml", "csv"]:
        raise HTTPException(status_code=400, 
                         detail=f"Invalid format: {format}. Must be one of: json, xml, csv")
    
    # Redirect to appropriate formatter
    if format_lower == "json":
        return await format_json(
            result=result,
            format_type=options.get("format_type", "standard"),
            pretty=options.get("pretty", False),
            indent=options.get("indent", 2),
            null_value=options.get("null_value"),
            include_metadata=options.get("include_metadata", True),
            current_user=current_user
        )
    elif format_lower == "xml":
        return await format_xml(
            result=result,
            format_type=options.get("format_type", "standard"),
            pretty=options.get("pretty", True),
            null_value=options.get("null_value"),
            root_element=options.get("root_element", "result"),
            row_element=options.get("row_element", "row"),
            current_user=current_user
        )
    else:  # csv
        return await format_csv(
            result=result,
            include_header=options.get("include_header", True),
            delimiter=options.get("delimiter", ","),
            quotechar=options.get("quotechar", '"'),
            null_value=options.get("null_value", ""),
            current_user=current_user
        )

# Son güncelleme: 2025-05-20 11:32:47
# Güncelleyen: Teeksss