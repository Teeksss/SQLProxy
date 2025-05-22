from typing import Dict, Any, List
import csv
import json
import pandas as pd
from io import StringIO, BytesIO
import xlsxwriter

class DataTransferService:
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'excel', 'sql']
        
    def export_data(self, data: Dict[str, Any], format: str) -> BytesIO:
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}")
            
        if format == 'csv':
            return self._export_csv(data)
        elif format == 'json':
            return self._export_json(data)
        elif format == 'excel':
            return self._export_excel(data)
        elif format == 'sql':
            return self._export_sql(data)
            
    def import_data(self, file: BytesIO, format: str) -> Dict[str, Any]:
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}")
            
        if format == 'csv':
            return self._import_csv(file)
        elif format == 'json':
            return self._import_json(file)
        elif format == 'excel':
            return self._import_excel(file)
        elif format == 'sql':
            return self._import_sql(file)
            
    def _export_csv(self, data: Dict[str, Any]) -> BytesIO:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data['columns'])
        writer.writeheader()
        writer.writerows(data['rows'])
        return BytesIO(output.getvalue().encode())
        
    def _export_excel(self, data: Dict[str, Any]) -> BytesIO:
        output = BytesIO()
        df = pd.DataFrame(data['rows'], columns=data['columns'])
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Query Results', index=False)
        return output