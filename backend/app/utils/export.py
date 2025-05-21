"""
Export utilities for SQL Proxy

Provides functions for exporting data in various formats (CSV, Excel, JSON, Parquet).

Last updated: 2025-05-20 07:47:46
Updated by: Teeksss
"""

import logging
import json
import io
import csv
from typing import Dict, List, Any, Optional, Union, BinaryIO

logger = logging.getLogger(__name__)

def dataframe_to_csv(
    data: List[Dict[str, Any]], 
    columns: Optional[List[str]] = None,
    output_file: Optional[Union[str, BinaryIO]] = None,
    dialect: str = 'excel',
    delimiter: str = ',',
    quotechar: str = '"',
    include_header: bool = True
) -> Optional[str]:
    """
    Convert data to CSV format
    
    Args:
        data: List of dictionaries containing the data
        columns: List of column names to include (and their order)
        output_file: Optional file path or file-like object to write to
        dialect: CSV dialect to use
        delimiter: Field delimiter to use
        quotechar: Quote character to use
        include_header: Whether to include a header row
        
    Returns:
        CSV string if output_file is None, otherwise None
    """
    try:
        # If no columns specified, use keys from first row or empty list
        if not columns:
            columns = list(data[0].keys()) if data else []
        
        # Create output stream
        if output_file is None:
            output = io.StringIO()
            write_to_string = True
        elif isinstance(output_file, str):
            output = open(output_file, 'w', newline='')
            write_to_string = False
        else:
            # Assume it's a file-like object
            output = output_file
            write_to_string = False
        
        # Create CSV writer
        writer = csv.DictWriter(
            output,
            fieldnames=columns,
            dialect=dialect,
            delimiter=delimiter,
            quotechar=quotechar,
            quoting=csv.QUOTE_MINIMAL
        )
        
        # Write header
        if include_header:
            writer.writeheader()
        
        # Write data
        for row in data:
            writer.writerow({k: row.get(k, '') for k in columns})
        
        # Return or close
        if write_to_string:
            return output.getvalue()
        elif isinstance(output_file, str):
            output.close()
        
        return None
        
    except Exception as e:
        logger.error(f"Error converting data to CSV: {str(e)}")
        if isinstance(output_file, str) and 'output' in locals():
            try:
                output.close()
            except:
                pass
        return None

def dataframe_to_excel(
    data: List[Dict[str, Any]], 
    columns: Optional[List[str]] = None,
    output_file: Optional[Union[str, BinaryIO]] = None,
    sheet_name: str = 'Data',
    include_header: bool = True
) -> Optional[bytes]:
    """
    Convert data to Excel format
    
    Args:
        data: List of dictionaries containing the data
        columns: List of column names to include (and their order)
        output_file: Optional file path or file-like object to write to
        sheet_name: Name of the Excel sheet
        include_header: Whether to include a header row
        
    Returns:
        Excel bytes if output_file is None, otherwise None
    """
    try:
        # Import pandas here to avoid making it a hard dependency
        import pandas as pd
        
        # If no columns specified, use keys from first row or empty list
        if not columns:
            columns = list(data[0].keys()) if data else []
        
        # Convert to DataFrame with specified columns
        df = pd.DataFrame(data)[columns] if columns else pd.DataFrame(data)
        
        # Create output stream
        if output_file is None:
            output = io.BytesIO()
            write_to_bytes = True
        elif isinstance(output_file, str):
            output = output_file
            write_to_bytes = False
        else:
            # Assume it's a file-like object
            output = output_file
            write_to_bytes = False
        
        # Write to Excel
        writer = pd.ExcelWriter(output, engine='openpyxl')
        df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False,
            header=include_header
        )
        writer.save()
        
        # Return or close
        if write_to_bytes:
            output.seek(0)
            return output.read()
        
        return None
        
    except ImportError:
        logger.error("Pandas is required for Excel export")
        return None
    except Exception as e:
        logger.error(f"Error converting data to Excel: {str(e)}")
        return None

def dataframe_to_json(
    data: List[Dict[str, Any]], 
    columns: Optional[List[str]] = None,
    output_file: Optional[Union[str, BinaryIO]] = None,
    orient: str = 'records',
    indent: int = 2,
    date_format: str = 'iso'
) -> Optional[str]:
    """
    Convert data to JSON format
    
    Args:
        data: List of dictionaries containing the data
        columns: List of column names to include
        output_file: Optional file path or file-like object to write to
        orient: JSON orientation ('records', 'split', etc.)
        indent: Indentation level
        date_format: Date format to use
        
    Returns:
        JSON string if output_file is None, otherwise None
    """
    try:
        # If columns specified, filter data
        if columns:
            filtered_data = []
            for row in data:
                filtered_row = {k: row.get(k) for k in columns if k in row}
                filtered_data.append(filtered_row)
            data = filtered_data
        
        # Convert to JSON
        if orient == 'records':
            # Default format - list of objects
            json_data = json.dumps(data, indent=indent, default=str)
        elif orient == 'split':
            # Split format - columns and data separately
            col_list = columns if columns else (list(data[0].keys()) if data else [])
            values = []
            for row in data:
                row_values = [row.get(col) for col in col_list]
                values.append(row_values)
            json_data = json.dumps({
                'columns': col_list,
                'data': values
            }, indent=indent, default=str)
        elif orient == 'table':
            # Table format - schema and data
            col_list = columns if columns else (list(data[0].keys()) if data else [])
            json_data = json.dumps({
                'schema': {
                    'fields': [{'name': col} for col in col_list]
                },
                'data': data
            }, indent=indent, default=str)
        else:
            # Default to records
            json_data = json.dumps(data, indent=indent, default=str)
        
        # Write to file if specified
        if output_file is not None:
            if isinstance(output_file, str):
                with open(output_file, 'w') as f:
                    f.write(json_data)
            else:
                # Assume it's a file-like object
                output_file.write(json_data.encode() if hasattr(output_file, 'write') else json_data)
            return None
        
        return json_data
        
    except Exception as e:
        logger.error(f"Error converting data to JSON: {str(e)}")
        return None

def dataframe_to_parquet(
    data: List[Dict[str, Any]], 
    columns: Optional[List[str]] = None,
    output_file: Optional[Union[str, BinaryIO]] = None,
    compression: str = 'snappy'
) -> Optional[bytes]:
    """
    Convert data to Parquet format
    
    Args:
        data: List of dictionaries containing the data
        columns: List of column names to include
        output_file: Optional file path or file-like object to write to
        compression: Compression algorithm to use
        
    Returns:
        Parquet bytes if output_file is None, otherwise None
    """
    try:
        # Import required libraries here to avoid making them hard dependencies
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
        
        # If no columns specified, use keys from first row or empty list
        if not columns:
            columns = list(data[0].keys()) if data else []
        
        # Convert to DataFrame with specified columns
        df = pd.DataFrame(data)[columns] if columns else pd.DataFrame(data)
        
        # Convert to PyArrow Table
        table = pa.Table.from_pandas(df)
        
        # Create output stream
        if output_file is None:
            output = io.BytesIO()
            write_to_bytes = True
        elif isinstance(output_file, str):
            output = output_file
            write_to_bytes = False
        else:
            # Assume it's a file-like object
            output = output_file
            write_to_bytes = False
        
        # Write to Parquet
        pq.write_table(
            table,
            output,
            compression=compression
        )
        
        # Return or close
        if write_to_bytes:
            output.seek(0)
            return output.read()
        
        return None
        
    except ImportError:
        logger.error("Pandas, PyArrow, and PyArrow Parquet are required for Parquet export")
        return None
    except Exception as e:
        logger.error(f"Error converting data to Parquet: {str(e)}")
        return None

def format_data_for_export(
    data: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Format query results for export
    
    Args:
        data: Query results from SQL Proxy
        
    Returns:
        Tuple of (formatted_data, columns)
    """
    try:
        if not data or 'data' not in data:
            return [], []
        
        # Get data and columns
        result_data = data.get('data', [])
        columns = data.get('columns', [])
        
        # If no explicit columns, try to extract from first row
        if not columns and result_data:
            columns = list(result_data[0].keys())
        
        return result_data, columns
    
    except Exception as e:
        logger.error(f"Error formatting data for export: {str(e)}")
        return [], []

# Son güncelleme: 2025-05-20 07:47:46
# Güncelleyen: Teeksss