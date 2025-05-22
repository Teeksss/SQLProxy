from typing import Dict, List, Any
import pandas as pd
import json
from datetime import datetime
from .models import ExportConfig, ExportFormat
from .generators import ReportGenerator

class ExportManager:
    def __init__(self):
        self.report_generator = ReportGenerator()
        self.supported_formats = {
            ExportFormat.CSV: self._export_csv,
            ExportFormat.JSON: self._export_json,
            ExportFormat.EXCEL: self._export_excel,
            ExportFormat.PDF: self._export_pdf
        }
        
    async def export_data(self, data: Any,
                         config: ExportConfig) -> Dict:
        """Veri export eder."""
        try:
            # Convert data to DataFrame
            df = self._to_dataframe(data)
            
            # Apply transformations
            if config.transformations:
                df = await self._apply_transformations(
                    df, config.transformations
                )
                
            # Generate export
            export_func = self.supported_formats[config.format]
            result = await export_func(df, config)
            
            return {
                'status': 'success',
                'data': result,
                'metadata': {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'format': config.format,
                    'timestamp': datetime.utcnow()
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def schedule_export(self, config: ExportConfig,
                            schedule: Dict) -> Dict:
        """Export schedule eder."""
        try:
            # Validate schedule
            if not self._validate_schedule(schedule):
                raise ValueError("Invalid schedule configuration")
                
            # Create schedule
            job_id = await self._create_schedule_job(
                config, schedule
            )
            
            return {
                'status': 'success',
                'job_id': job_id,
                'schedule': schedule
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def _export_csv(self, df: pd.DataFrame,
                         config: ExportConfig) -> str:
        """CSV export yapar."""
        return df.to_csv(
            index=config.include_index,
            encoding=config.encoding
        )
        
    async def _export_excel(self, df: pd.DataFrame,
                          config: ExportConfig) -> bytes:
        """Excel export yapar."""
        output = io.BytesIO()
        with pd.ExcelWriter(output) as writer:
            df.to_excel(
                writer,
                sheet_name=config.sheet_name,
                index=config.include_index
            )
        return output.getvalue()