import boto3
import json
from datetime import datetime
from typing import Dict, List
import os

class BackupService:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket_name = os.getenv('BACKUP_BUCKET')
        
    def backup_database(self, database: str) -> Dict:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{database}_{timestamp}.sql"
        
        # Execute pg_dump
        os.system(f'pg_dump {database} > /tmp/{backup_file}')
        
        # Upload to S3
        self.s3.upload_file(
            f'/tmp/{backup_file}',
            self.bucket_name,
            f'backups/{backup_file}'
        )
        
        # Cleanup
        os.remove(f'/tmp/{backup_file}')
        
        return {
            'database': database,
            'backup_file': backup_file,
            'timestamp': timestamp
        }
        
    def list_backups(self, database: str) -> List[Dict]:
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=f'backups/{database}_'
        )
        
        return [
            {
                'filename': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified']
            }
            for obj in response.get('Contents', [])
        ]
        
    def restore_database(self, database: str, backup_file: str) -> Dict:
        # Download from S3
        local_file = f'/tmp/{backup_file}'
        self.s3.download_file(
            self.bucket_name,
            f'backups/{backup_file}',
            local_file
        )
        
        # Execute restore
        os.system(f'psql {database} < {local_file}')
        
        # Cleanup
        os.remove(local_file)
        
        return {
            'database': database,
            'restored_from': backup_file,
            'timestamp': datetime.utcnow().isoformat()
        }