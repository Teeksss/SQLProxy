from typing import Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class TableSchema:
    name: str
    columns: List[Dict]
    constraints: List[Dict]
    indexes: List[Dict]

class SchemaValidator:
    def __init__(self):
        self.supported_types = {
            'INTEGER', 'BIGINT', 'SMALLINT',
            'VARCHAR', 'TEXT', 'CHAR',
            'DATE', 'TIMESTAMP', 'BOOLEAN',
            'DECIMAL', 'NUMERIC', 'FLOAT'
        }
        
    def validate_schema(self, schema: Dict) -> Dict:
        """Schema'yı validate eder ve kontrol raporu döndürür."""
        validation_report = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Tablo validasyonu
            for table_name, table_def in schema.items():
                table_report = self._validate_table(table_name, table_def)
                
                if table_report['errors']:
                    validation_report['is_valid'] = False
                    validation_report['errors'].extend(table_report['errors'])
                    
                validation_report['warnings'].extend(table_report['warnings'])
                
            # Referential integrity kontrolü
            ref_report = self._check_referential_integrity(schema)
            if ref_report['errors']:
                validation_report['is_valid'] = False
                validation_report['errors'].extend(ref_report['errors'])
                
            return validation_report
            
        except Exception as e:
            validation_report['is_valid'] = False
            validation_report['errors'].append(str(e))
            return validation_report
            
    def _validate_table(self, table_name: str, table_def: Dict) -> Dict:
        """Tablo tanımını validate eder."""
        report = {'errors': [], 'warnings': []}
        
        # Primary key kontrolü
        if not self._has_primary_key(table_def):
            report['warnings'].append(
                f"Table {table_name} has no primary key"
            )
            
        # Kolon tipleri kontrolü
        for column in table_def.get('columns', []):
            if not self._is_valid_column_type(column['type']):
                report['errors'].append(
                    f"Invalid column type {column['type']} in {table_name}.{column['name']}"
                )
                
        # Index kontrolü
        if indexes := table_def.get('indexes', []):
            for index in indexes:
                if not self._is_valid_index(index, table_def):
                    report['errors'].append(
                        f"Invalid index definition in table {table_name}"
                    )
                    
        return report
        
    def _check_referential_integrity(self, schema: Dict) -> Dict:
        """Referential integrity kontrolü yapar."""
        report = {'errors': [], 'warnings': []}
        
        for table_name, table_def in schema.items():
            for constraint in table_def.get('constraints', []):
                if constraint['type'] == 'FOREIGN KEY':
                    if not self._is_valid_foreign_key(constraint, schema):
                        report['errors'].append(
                            f"Invalid foreign key reference in {table_name}"
                        )
                        
        return report