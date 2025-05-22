from typing import Dict, List, Optional
import hashlib
from datetime import datetime
import yaml
from pathlib import Path

class SchemaManager:
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.migrations_path = Path('migrations')
        self.schema_version_table = '_schema_versions'
        
    def initialize(self):
        """Schema yönetim sistemini başlatır."""
        self._ensure_version_table()
        self._load_migrations()
        
    def create_migration(self, name: str, 
                        up_queries: List[str],
                        down_queries: List[str]) -> str:
        """Yeni migration oluşturur."""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        migration_id = f"{timestamp}_{name}"
        
        migration_content = {
            'id': migration_id,
            'name': name,
            'timestamp': timestamp,
            'up': up_queries,
            'down': down_queries
        }
        
        # Migration dosyasını kaydet
        migration_file = self.migrations_path / f"{migration_id}.yml"
        with open(migration_file, 'w') as f:
            yaml.dump(migration_content, f)
            
        return migration_id
        
    def migrate(self, target_version: str = None) -> Dict:
        """Belirtilen versiyona kadar migrate eder."""
        current_version = self._get_current_version()
        migrations = self._get_pending_migrations(current_version, target_version)
        
        results = {
            'applied': [],
            'errors': [],
            'start_version': current_version,
            'end_version': current_version
        }
        
        for migration in migrations:
            try:
                self._apply_migration(migration)
                results['applied'].append(migration['id'])
                results['end_version'] = migration['id']
            except Exception as e:
                results['errors'].append({
                    'migration': migration['id'],
                    'error': str(e)
                })
                break
                
        return results
        
    def rollback(self, steps: int = 1) -> Dict:
        """Belirtilen sayıda migration'ı geri alır."""
        current_version = self._get_current_version()
        migrations = self._get_applied_migrations()
        
        to_rollback = migrations[-steps:]
        results = {
            'rolledback': [],
            'errors': [],
            'start_version': current_version
        }
        
        for migration in reversed(to_rollback):
            try:
                self._rollback_migration(migration)
                results['rolledback'].append(migration['id'])
            except Exception as e:
                results['errors'].append({
                    'migration': migration['id'],
                    'error': str(e)
                })
                break
                
        results['end_version'] = self._get_current_version()
        return results