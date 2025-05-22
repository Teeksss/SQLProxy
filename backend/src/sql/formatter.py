from typing import Dict, List, Any
import pandas as pd
from datetime import datetime
import json

class ResultFormatter:
    def __init__(self):
        self.supported_formats = ['json', 'csv', 'excel', 'html']
        
    def format_result(self, data: Dict[str, List], 
                     format_type: str = 'json',
                     options: Dict = None) -> Any:
        """Query sonuçlarını istenen formata dönüştürür."""
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}")
            
        df = pd.DataFrame(data['rows'], columns=data['columns'])
        
        if format_type == 'json':
            return self._format_json(df, options)
        elif format_type == 'csv':
            return self._format_csv(df, options)
        elif format_type == 'excel':
            return self._format_excel(df, options)
        elif format_type == 'html':
            return self._format_html(df, options)
            
    def _format_json(self, df: pd.DataFrame, options: Dict = None) -> str:
        """JSON formatında sonuç döndürür."""
        opts = options or {}
        orient = opts.get('orient', 'records')
        date_format = opts.get('date_format', 'iso')
        
        return df.to_json(
            orient=orient,
            date_format=date_format
        )
        
    def _format_csv(self, df: pd.DataFrame, options: Dict = None) -> str:
        """CSV formatında sonuç döndürür."""
        opts = options or {}
        separator = opts.get('separator', ',')
        encoding = opts.get('encoding', 'utf-8')
        
        return df.to_csv(
            sep=separator,
            encoding=encoding,
            index=False
        )
        
    def _format_excel(self, df: pd.DataFrame, options: Dict = None) -> bytes:
        """Excel formatında sonuç döndürür."""
        opts = options or {}
        sheet_name = opts.get('sheet_name', 'Query Result')
        
        # Excel dosyası oluştur
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )
            
            # Formatlama
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Header formatı
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D9D9D9'
            })
            
            # Kolonları formatla
            for idx, col in enumerate(df.columns):
                worksheet.set_column(idx, idx, len(col) + 2)
                worksheet.write(0, idx, col, header_format)
                
        return output.getvalue()