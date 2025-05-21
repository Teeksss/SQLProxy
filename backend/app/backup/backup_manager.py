"""
Automated Backup and Restore Manager for SQL Proxy

This module provides automated backup and restore capabilities for
SQL Proxy system data and configurations.

Last updated: 2025-05-20 10:59:28
Updated by: Teeksss
"""

import logging
import os
import time
import json
import shutil
import tarfile
import tempfile
import sqlite3
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import threading
from pathlib import Path
import boto3
from google.cloud import storage
from azure.storage.blob import BlobServiceClient
import psycopg2
import mysql.connector

from app.core.config import settings
from app.db.session import engine

logger = logging.getLogger(__name__)

class BackupManager:
    """
    Backup manager for SQL Proxy
    
    Provides automated backup and restore capabilities for SQL Proxy
    system data and configurations.
    """
    
    def __init__(self):
        """Initialize the backup manager"""
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.retention_days = settings.BACKUP_RETENTION_DAYS
        self.backup_enabled = settings.BACKUP_ENABLED
        
        # Storage settings
        self.storage_type = settings.BACKUP_STORAGE_TYPE  # local, s3, gcs, azure
        self.storage_bucket = settings.BACKUP_STORAGE_BUCKET
        self.storage_prefix = settings.BACKUP_STORAGE_PREFIX
        
        # Init storage clients based on type
        self.s3_client = None
        self.gcs_client = None
        self.azure_client = None
        
        if self.storage_type == 's3':
            self._init_s3_client()
        elif self.storage_type == 'gcs':
            self._init_gcs_client()
        elif self.storage_type == 'azure':
            self._init_azure_client()
        
        # Backup lock to prevent concurrent backups
        self.backup_lock = threading.RLock()
        self.backup_in_progress = False
        
        # Monitoring
        self.last_backup_time = None
        self.last_backup_status = None
        self.last_backup_error = None
        self.backup_history = []
        
        logger.info("Backup manager initialized")
    
    def _init_s3_client(self):
        """Initialize S3 client for AWS storage"""
        try:
            # AWS credentials should be configured in environment or IAM role
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            logger.info("S3 client initialized")
        except Exception as e:
            logger.error(f"Error initializing S3 client: {str(e)}")
    
    def _init_gcs_client(self):
        """Initialize GCS client for Google Cloud Storage"""
        try:
            # GCP credentials should be configured in environment
            self.gcs_client = storage.Client()
            logger.info("GCS client initialized")
        except Exception as e:
            logger.error(f"Error initializing GCS client: {str(e)}")
    
    def _init_azure_client(self):
        """Initialize Azure Blob Storage client"""
        try:
            # Azure credentials should be configured in environment
            connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
            self.azure_client = BlobServiceClient.from_connection_string(connection_string)
            logger.info("Azure Blob Storage client initialized")
        except Exception as e:
            logger.error(f"Error initializing Azure Blob Storage client: {str(e)}")
    
    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a backup of SQL Proxy data
        
        Args:
            backup_name: Optional name for the backup
            
        Returns:
            Dictionary with backup result
        """
        if not self.backup_enabled:
            return {"error": "Backup is not enabled"}
        
        with self.backup_lock:
            if self.backup_in_progress:
                return {"error": "Backup already in progress"}
            
            self.backup_in_progress = True
        
        try:
            # Generate backup name if not provided
            if not backup_name:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_name = f"sqlproxy_backup_{timestamp}"
            
            logger.info(f"Starting backup: {backup_name}")
            start_time = time.time()
            
            # Create temporary directory for backup
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Backup database
                db_file = temp_path / "database.sql"
                self._backup_database(db_file)
                
                # Backup configuration
                config_dir = temp_path / "config"
                config_dir.mkdir()
                self._backup_configuration(config_dir)
                
                # Backup user files and custom data
                data_dir = temp_path / "data"
                data_dir.mkdir()
                self._backup_user_data(data_dir)
                
                # Create metadata file
                metadata = {
                    "backup_name": backup_name,
                    "backup_time": datetime.utcnow().isoformat(),
                    "version": settings.VERSION,
                    "description": "SQL Proxy backup",
                    "database_type": settings.DB_TYPE,
                    "backup_components": ["database", "config", "data"]
                }
                
                with open(temp_path / "metadata.json", "w") as f:
                    json.dump(metadata, f, indent=2)
                
                # Create archive
                backup_file = self.backup_dir / f"{backup_name}.tar.gz"
                with tarfile.open(backup_file, "w:gz") as tar:
                    tar.add(temp_dir, arcname="")
                
                # Upload to remote storage if configured
                remote_url = None
                if self.storage_type != "local":
                    remote_url = self._upload_backup(backup_file, backup_name)
                
                # Cleanup old backups
                self._cleanup_old_backups()
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Update monitoring info
            self.last_backup_time = datetime.utcnow()
            self.last_backup_status = "success"
            self.last_backup_error = None
            
            backup_info = {
                "name": backup_name,
                "time": self.last_backup_time.isoformat(),
                "status": "success",
                "duration": duration,
                "size": os.path.getsize(backup_file),
                "location": str(backup_file),
                "remote_url": remote_url
            }
            
            # Add to history (limit to 100 entries)
            self.backup_history.append(backup_info)
            if len(self.backup_history) > 100:
                self.backup_history = self.backup_history[-100:]
            
            logger.info(f"Backup completed: {backup_name} ({duration:.2f}s)")
            
            return {
                "status": "success",
                "backup_name": backup_name,
                "backup_file": str(backup_file),
                "duration": duration,
                "remote_url": remote_url
            }
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            
            # Update monitoring info
            self.last_backup_time = datetime.utcnow()
            self.last_backup_status = "failed"
            self.last_backup_error = str(e)
            
            backup_info = {
                "name": backup_name,
                "time": self.last_backup_time.isoformat(),
                "status": "failed",
                "error": str(e)
            }
            
            # Add to history (limit to 100 entries)
            self.backup_history.append(backup_info)
            if len(self.backup_history) > 100:
                self.backup_history = self.backup_history[-100:]
            
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            with self.backup_lock:
                self.backup_in_progress = False
    
    def restore_backup(
        self, 
        backup_file: str,
        components: List[str] = None
    ) -> Dict[str, Any]:
        """
        Restore a backup
        
        Args:
            backup_file: Path to backup file
            components: List of components to restore (None for all)
            
        Returns:
            Dictionary with restore result
        """
        if not components:
            components = ["database", "config", "data"]
        
        with self.backup_lock:
            if self.backup_in_progress:
                return {"error": "Backup in progress, cannot restore"}
            
            self.backup_in_progress = True
        
        try:
            logger.info(f"Starting restore from: {backup_file}")
            start_time = time.time()
            
            # Check if backup file exists
            backup_path = Path(backup_file)
            if not backup_path.exists():
                # Try downloading from remote storage
                if self.storage_type != "local" and '/' in backup_file:
                    backup_name = backup_file.split('/')[-1].replace('.tar.gz', '')
                    backup_path = self.backup_dir / f"{backup_name}.tar.gz"
                    self._download_backup(backup_file, backup_path)
                elif not backup_path.is_absolute():
                    backup_path = self.backup_dir / backup_file
            
            if not backup_path.exists():
                return {"error": f"Backup file not found: {backup_file}"}
            
            # Create temporary directory for restore
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract archive
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(path=temp_dir)
                
                # Check metadata
                metadata_file = temp_path / "metadata.json"
                if not metadata_file.exists():
                    return {"error": "Invalid backup: metadata.json not found"}
                
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                
                # Verify backup components
                available_components = metadata.get("backup_components", [])
                for component in components:
                    if component not in available_components:
                        return {"error": f"Component not available in backup: {component}"}
                
                # Restore components
                if "database" in components:
                    db_file = temp_path / "database.sql"
                    if db_file.exists():
                        self._restore_database(db_file)
                    else:
                        return {"error": "Database backup file not found"}
                
                if "config" in components:
                    config_dir = temp_path / "config"
                    if config_dir.exists():
                        self._restore_configuration(config_dir)
                    else:
                        return {"error": "Config backup directory not found"}
                
                if "data" in components:
                    data_dir = temp_path / "data"
                    if data_dir.exists():
                        self._restore_user_data(data_dir)
                    else:
                        return {"error": "Data backup directory not found"}
            
            # Calculate duration
            duration = time.time() - start_time
            
            logger.info(f"Restore completed from {backup_file} ({duration:.2f}s)")
            
            return {
                "status": "success",
                "backup_file": str(backup_path),
                "components": components,
                "duration": duration,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            with self.backup_lock:
                self.backup_in_progress = False
    
    def list_backups(self) -> Dict[str, Any]:
        """
        List available backups
        
        Returns:
            Dictionary with backup list
        """
        try:
            # List local backups
            local_backups = []
            for file in self.backup_dir.glob("*.tar.gz"):
                file_stat = file.stat()
                
                # Try to extract metadata from backup
                metadata = self._get_backup_metadata(file)
                
                backup_info = {
                    "name": file.stem,
                    "path": str(file),
                    "size": file_stat.st_size,
                    "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "metadata": metadata
                }
                
                local_backups.append(backup_info)
            
            # Sort by modified time (newest first)
            local_backups.sort(key=lambda x: x["modified_time"], reverse=True)
            
            # List remote backups if configured
            remote_backups = []
            if self.storage_type != "local":
                remote_backups = self._list_remote_backups()
            
            return {
                "local_backups": local_backups,
                "remote_backups": remote_backups,
                "backup_history": self.backup_history,
                "last_backup_time": self.last_backup_time.isoformat() if self.last_backup_time else None,
                "last_backup_status": self.last_backup_status,
                "last_backup_error": self.last_backup_error
            }
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        Delete a backup
        
        Args:
            backup_name: Name of backup to delete
            
        Returns:
            Dictionary with delete result
        """
        try:
            # Find local backup file
            backup_file = self.backup_dir / f"{backup_name}.tar.gz"
            
            if not backup_file.exists():
                # Check if it's a remote URL
                if '/' in backup_name or backup_name.startswith(('s3://', 'gs://', 'https://')):
                    # Delete from remote storage
                    self._delete_remote_backup(backup_name)
                    
                    return {
                        "status": "success",
                        "message": f"Remote backup deleted: {backup_name}"
                    }
                else:
                    return {"error": f"Backup not found: {backup_name}"}
            
            # Delete local backup
            backup_file.unlink()
            
            # Also delete from remote storage if configured
            if self.storage_type != "local":
                remote_path = f"{self.storage_prefix}/{backup_name}.tar.gz"
                self._delete_remote_backup(remote_path)
            
            logger.info(f"Backup deleted: {backup_name}")
            
            return {
                "status": "success",
                "message": f"Backup deleted: {backup_name}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting backup: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def schedule_backup(
        self,
        cron_expression: str,
        retention_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Schedule automated backups
        
        Args:
            cron_expression: Cron expression for schedule
            retention_days: Days to retain backups
            
        Returns:
            Dictionary with schedule result
        """
        try:
            # This would typically integrate with a job scheduler
            # For now, we'll just return the configuration
            
            if retention_days is not None:
                self.retention_days = retention_days
            
            return {
                "status": "success",
                "message": "Backup scheduled",
                "cron_expression": cron_expression,
                "retention_days": self.retention_days,
                "note": "Actual scheduling requires integration with a job scheduler"
            }
            
        except Exception as e:
            logger.error(f"Error scheduling backup: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _backup_database(self, backup_file: Path) -> None:
        """
        Backup database to file
        
        Args:
            backup_file: Path to backup file
        """
        # Determine database type and use appropriate method
        db_type = settings.DB_TYPE.lower()
        
        if db_type == "postgresql":
            self._backup_postgresql(backup_file)
        elif db_type == "mysql":
            self._backup_mysql(backup_file)
        elif db_type == "sqlite":
            self._backup_sqlite(backup_file)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _backup_postgresql(self, backup_file: Path) -> None:
        """
        Backup PostgreSQL database
        
        Args:
            backup_file: Path to backup file
        """
        # Get database connection info
        db_host = settings.DB_HOST
        db_port = settings.DB_PORT
        db_name = settings.DB_NAME
        db_user = settings.DB_USER
        db_password = settings.DB_PASSWORD
        
        # Set environment variable for password
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password
        
        # Execute pg_dump command
        cmd = [
            "pg_dump",
            "--host", db_host,
            "--port", str(db_port),
            "--username", db_user,
            "--format", "plain",
            "--no-owner",
            "--no-acl",
            "--file", str(backup_file),
            db_name
        ]
        
        subprocess.run(cmd, env=env, check=True)
    
    def _backup_mysql(self, backup_file: Path) -> None:
        """
        Backup MySQL database
        
        Args:
            backup_file: Path to backup file
        """
        # Get database connection info
        db_host = settings.DB_HOST
        db_port = settings.DB_PORT
        db_name = settings.DB_NAME
        db_user = settings.DB_USER
        db_password = settings.DB_PASSWORD
        
        # Execute mysqldump command
        cmd = [
            "mysqldump",
            "--host", db_host,
            "--port", str(db_port),
            "--user", db_user,
            f"--password={db_password}",
            "--single-transaction",
            "--routines",
            "--triggers",
            "--databases", db_name,
            "--result-file", str(backup_file)
        ]
        
        subprocess.run(cmd, check=True)
    
    def _backup_sqlite(self, backup_file: Path) -> None:
        """
        Backup SQLite database
        
        Args:
            backup_file: Path to backup file
        """
        # Get database file path
        db_path = settings.DB_PATH
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Backup database
        with open(backup_file, 'w') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        
        conn.close()
    
    def _backup_configuration(self, config_dir: Path) -> None:
        """
        Backup configuration files
        
        Args:
            config_dir: Directory to backup to
        """
        # Get config directory
        src_config_dir = Path(settings.CONFIG_DIR)
        
        if src_config_dir.exists():
            # Copy config files
            for file in src_config_dir.glob("**/*"):
                if file.is_file():
                    # Create relative path
                    rel_path = file.relative_to(src_config_dir)
                    dst_path = config_dir / rel_path
                    
                    # Create parent directories
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(file, dst_path)
    
    def _backup_user_data(self, data_dir: Path) -> None:
        """
        Backup user data files
        
        Args:
            data_dir: Directory to backup to
        """
        # Get data directory
        src_data_dir = Path(settings.DATA_DIR)
        
        if src_data_dir.exists():
            # Copy data files
            for file in src_data_dir.glob("**/*"):
                if file.is_file():
                    # Create relative path
                    rel_path = file.relative_to(src_data_dir)
                    dst_path = data_dir / rel_path
                    
                    # Create parent directories
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(file, dst_path)
    
    def _restore_database(self, backup_file: Path) -> None:
        """
        Restore database from backup
        
        Args:
            backup_file: Path to backup file
        """
        # Determine database type and use appropriate method
        db_type = settings.DB_TYPE.lower()
        
        if db_type == "postgresql":
            self._restore_postgresql(backup_file)
        elif db_type == "mysql":
            self._restore_mysql(backup_file)
        elif db_type == "sqlite":
            self._restore_sqlite(backup_file)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _restore_postgresql(self, backup_file: Path) -> None:
        """
        Restore PostgreSQL database
        
        Args:
            backup_file: Path to backup file
        """
        # Get database connection info
        db_host = settings.DB_HOST
        db_port = settings.DB_PORT
        db_name = settings.DB_NAME
        db_user = settings.DB_USER
        db_password = settings.DB_PASSWORD
        
        # Set environment variable for password
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password
        
        # Execute psql command to restore
        cmd = [
            "psql",
            "--host", db_host,
            "--port", str(db_port),
            "--username", db_user,
            "--dbname", db_name,
            "--file", str(backup_file)
        ]
        
        subprocess.run(cmd, env=env, check=True)
    
    def _restore_mysql(self, backup_file: Path) -> None:
        """
        Restore MySQL database
        
        Args:
            backup_file: Path to backup file
        """
        # Get database connection info
        db_host = settings.DB_HOST
        db_port = settings.DB_PORT
        db_name = settings.DB_NAME
        db_user = settings.DB_USER
        db_password = settings.DB_PASSWORD
        
        # Execute mysql command to restore
        cmd = [
            "mysql",
            "--host", db_host,
            "--port", str(db_port),
            "--user", db_user,
            f"--password={db_password}",
            "--database", db_name,
            "<", str(backup_file)
        ]
        
        # Use shell=True for redirection operator
        subprocess.run(" ".join(cmd), shell=True, check=True)
    
    def _restore_sqlite(self, backup_file: Path) -> None:
        """
        Restore SQLite database
        
        Args:
            backup_file: Path to backup file
        """
        # Get database file path
        db_path = settings.DB_PATH
        
        # Backup the current database file before replacing
        if os.path.exists(db_path):
            backup_path = f"{db_path}.bak.{int(time.time())}"
            shutil.copy2(db_path, backup_path)
            logger.info(f"Backed up existing database to {backup_path}")
        
        # Create new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute the SQL from backup file
        with open(backup_file, 'r') as f:
            script = f.read()
            cursor.executescript(script)
        
        conn.commit()
        conn.close()
    
    def _restore_configuration(self, config_dir: Path) -> None:
        """
        Restore configuration files
        
        Args:
            config_dir: Directory to restore from
        """
        # Get config directory
        dst_config_dir = Path(settings.CONFIG_DIR)
        
        # Create destination directory if it doesn't exist
        dst_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy config files
        for file in config_dir.glob("**/*"):
            if file.is_file():
                # Create relative path
                rel_path = file.relative_to(config_dir)
                dst_path = dst_config_dir / rel_path
                
                # Create parent directories
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(file, dst_path)
    
    def _restore_user_data(self, data_dir: Path) -> None:
        """
        Restore user data files
        
        Args:
            data_dir: Directory to restore from
        """
        # Get data directory
        dst_data_dir = Path(settings.DATA_DIR)
        
        # Create destination directory if it doesn't exist
        dst_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy data files
        for file in data_dir.glob("**/*"):
            if file.is_file():
                # Create relative path
                rel_path = file.relative_to(data_dir)
                dst_path = dst_data_dir / rel_path
                
                # Create parent directories
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(file, dst_path)
    
    def _upload_backup(self, backup_file: Path, backup_name: str) -> str:
        """
        Upload backup to remote storage
        
        Args:
            backup_file: Local path to backup file
            backup_name: Backup name
            
        Returns:
            URL of uploaded file
        """
        remote_path = f"{self.storage_prefix}/{backup_name}.tar.gz"
        
        if self.storage_type == 's3':
            return self._upload_to_s3(backup_file, remote_path)
        elif self.storage_type == 'gcs':
            return self._upload_to_gcs(backup_file, remote_path)
        elif self.storage_type == 'azure':
            return self._upload_to_azure(backup_file, remote_path)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def _upload_to_s3(self, backup_file: Path, remote_path: str) -> str:
        """
        Upload backup to S3
        
        Args:
            backup_file: Local path to backup file
            remote_path: Remote path
            
        Returns:
            S3 URL
        """
        if not self.s3_client:
            raise ValueError("S3 client not initialized")
        
        # Upload to S3
        self.s3_client.upload_file(
            str(backup_file),
            self.storage_bucket,
            remote_path
        )
        
        # Return S3 URL
        return f"s3://{self.storage_bucket}/{remote_path}"
    
    def _upload_to_gcs(self, backup_file: Path, remote_path: str) -> str:
        """
        Upload backup to Google Cloud Storage
        
        Args:
            backup_file: Local path to backup file
            remote_path: Remote path
            
        Returns:
            GCS URL
        """
        if not self.gcs_client:
            raise ValueError("GCS client not initialized")
        
        # Get bucket
        bucket = self.gcs_client.bucket(self.storage_bucket)
        
        # Upload to GCS
        blob = bucket.blob(remote_path)
        blob.upload_from_filename(str(backup_file))
        
        # Return GCS URL
        return f"gs://{self.storage_bucket}/{remote_path}"
    
    def _upload_to_azure(self, backup_file: Path, remote_path: str) -> str:
        """
        Upload backup to Azure Blob Storage
        
        Args:
            backup_file: Local path to backup file
            remote_path: Remote path
            
        Returns:
            Azure URL
        """
        if not self.azure_client:
            raise ValueError("Azure client not initialized")
        
        # Get container client
        container_client = self.azure_client.get_container_client(self.storage_bucket)
        
        # Upload to Azure
        with open(backup_file, "rb") as data:
            container_client.upload_blob(name=remote_path, data=data, overwrite=True)
        
        # Return Azure URL
        account_name = self.azure_client.account_name
        return f"https://{account_name}.blob.core.windows.net/{self.storage_bucket}/{remote_path}"
    
    def _download_backup(self, remote_url: str, local_path: Path) -> None:
        """
        Download backup from remote storage
        
        Args:
            remote_url: Remote URL
            local_path: Local path
        """
        if remote_url.startswith("s3://"):
            self._download_from_s3(remote_url, local_path)
        elif remote_url.startswith("gs://"):
            self._download_from_gcs(remote_url, local_path)
        elif "blob.core.windows.net" in remote_url:
            self._download_from_azure(remote_url, local_path)
        else:
            raise ValueError(f"Unsupported remote URL: {remote_url}")
    
    def _download_from_s3(self, remote_url: str, local_path: Path) -> None:
        """
        Download backup from S3
        
        Args:
            remote_url: S3 URL
            local_path: Local path
        """
        if not self.s3_client:
            raise ValueError("S3 client not initialized")
        
        # Parse S3 URL
        parts = remote_url.replace("s3://", "").split("/")
        bucket = parts[0]
        key = "/".join(parts[1:])
        
        # Download from S3
        self.s3_client.download_file(bucket, key, str(local_path))
    
    def _download_from_gcs(self, remote_url: str, local_path: Path) -> None:
        """
        Download backup from Google Cloud Storage
        
        Args:
            remote_url: GCS URL
            local_path: Local path
        """
        if not self.gcs_client:
            raise ValueError("GCS client not initialized")
        
        # Parse GCS URL
        parts = remote_url.replace("gs://", "").split("/")
        bucket_name = parts[0]
        blob_name = "/".join(parts[1:])
        
        # Download from GCS
        bucket = self.gcs_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(str(local_path))
    
    def _download_from_azure(self, remote_url: str, local_path: Path) -> None:
        """
        Download backup from Azure Blob Storage
        
        Args:
            remote_url: Azure URL
            local_path: Local path
        """
        if not self.azure_client:
            raise ValueError("Azure client not initialized")
        
        # Parse Azure URL
        parts = remote_url.split("/")
        container_name = parts[-2]
        blob_name = parts[-1]
        
        # Download from Azure
        container_client = self.azure_client.get_container_client(container_name)
        with open(local_path, "wb") as file:
            download = container_client.download_blob(blob_name)
            file.write(download.readall())
    
    def _list_remote_backups(self) -> List[Dict[str, Any]]:
        """
        List remote backups
        
        Returns:
            List of remote backups
        """
        if self.storage_type == 's3':
            return self._list_s3_backups()
        elif self.storage_type == 'gcs':
            return self._list_gcs_backups()
        elif self.storage_type == 'azure':
            return self._list_azure_backups()
        else:
            return []
    
    def _list_s3_backups(self) -> List[Dict[str, Any]]:
        """
        List backups in S3
        
        Returns:
            List of backups
        """
        if not self.s3_client:
            logger.warning("S3 client not initialized")
            return []
        
        try:
            # List objects in S3 bucket
            response = self.s3_client.list_objects_v2(
                Bucket=self.storage_bucket,
                Prefix=self.storage_prefix
            )
            
            backups = []
            
            for obj in response.get("Contents", []):
                if obj["Key"].endswith(".tar.gz"):
                    backup_name = obj["Key"].split("/")[-1].replace(".tar.gz", "")
                    
                    backup_info = {
                        "name": backup_name,
                        "path": f"s3://{self.storage_bucket}/{obj['Key']}",
                        "size": obj["Size"],
                        "modified_time": obj["LastModified"].isoformat(),
                        "storage_type": "s3"
                    }
                    
                    backups.append(backup_info)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing S3 backups: {str(e)}")
            return []
    
    def _list_gcs_backups(self) -> List[Dict[str, Any]]:
        """
        List backups in Google Cloud Storage
        
        Returns:
            List of backups
        """
        if not self.gcs_client:
            logger.warning("GCS client not initialized")
            return []
        
        try:
            # List objects in GCS bucket
            bucket = self.gcs_client.bucket(self.storage_bucket)
            blobs = bucket.list_blobs(prefix=self.storage_prefix)
            
            backups = []
            
            for blob in blobs:
                if blob.name.endswith(".tar.gz"):
                    backup_name = blob.name.split("/")[-1].replace(".tar.gz", "")
                    
                    backup_info = {
                        "name": backup_name,
                        "path": f"gs://{self.storage_bucket}/{blob.name}",
                        "size": blob.size,
                        "modified_time": blob.updated.isoformat(),
                        "storage_type": "gcs"
                    }
                    
                    backups.append(backup_info)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing GCS backups: {str(e)}")
            return []
    
    def _list_azure_backups(self) -> List[Dict[str, Any]]:
        """
        List backups in Azure Blob Storage
        
        Returns:
            List of backups
        """
        if not self.azure_client:
            logger.warning("Azure client not initialized")
            return []
        
        try:
            # List objects in Azure container
            container_client = self.azure_client.get_container_client(self.storage_bucket)
            blobs = container_client.list_blobs(name_starts_with=self.storage_prefix)
            
            backups = []
            
            for blob in blobs:
                if blob.name.endswith(".tar.gz"):
                    backup_name = blob.name.split("/")[-1].replace(".tar.gz", "")
                    
                    backup_info = {
                        "name": backup_name,
                        "path": f"https://{self.azure_client.account_name}.blob.core.windows.net/{self.storage_bucket}/{blob.name}",
                        "size": blob.size,
                        "modified_time": blob.last_modified.isoformat(),
                        "storage_type": "azure"
                    }
                    
                    backups.append(backup_info)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing Azure backups: {str(e)}")
            return []
    
    def _delete_remote_backup(self, remote_path: str) -> None:
        """
        Delete backup from remote storage
        
        Args:
            remote_path: Remote path or URL
        """
        try:
            if remote_path.startswith("s3://"):
                self._delete_from_s3(remote_path)
            elif remote_path.startswith("gs://"):
                self._delete_from_gcs(remote_path)
            elif "blob.core.windows.net" in remote_path:
                self._delete_from_azure(remote_path)
            else:
                # Assume it's just a path within the storage
                if self.storage_type == 's3':
                    self._delete_from_s3(f"s3://{self.storage_bucket}/{remote_path}")
                elif self.storage_type == 'gcs':
                    self._delete_from_gcs(f"gs://{self.storage_bucket}/{remote_path}")
                elif self.storage_type == 'azure':
                    account_name = self.azure_client.account_name
                    self._delete_from_azure(f"https://{account_name}.blob.core.windows.net/{self.storage_bucket}/{remote_path}")
        except Exception as e:
            logger.error(f"Error deleting remote backup: {str(e)}")
            raise
    
    def _delete_from_s3(self, remote_url: str) -> None:
        """
        Delete backup from S3
        
        Args:
            remote_url: S3 URL
        """
        if not self.s3_client:
            raise ValueError("S3 client not initialized")
        
        # Parse S3 URL
        parts = remote_url.replace("s3://", "").split("/")
        bucket = parts[0]
        key = "/".join(parts[1:])
        
        # Delete from S3
        self.s3_client.delete_object(
            Bucket=bucket,
            Key=key
        )
    
    def _delete_from_gcs(self, remote_url: str) -> None:
        """
        Delete backup from Google Cloud Storage
        
        Args:
            remote_url: GCS URL
        """
        if not self.gcs_client:
            raise ValueError("GCS client not initialized")
        
        # Parse GCS URL
        parts = remote_url.replace("gs://", "").split("/")
        bucket_name = parts[0]
        blob_name = "/".join(parts[1:])
        
        # Delete from GCS
        bucket = self.gcs_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
    
    def _delete_from_azure(self, remote_url: str) -> None:
        """
        Delete backup from Azure Blob Storage
        
        Args:
            remote_url: Azure URL
        """
        if not self.azure_client:
            raise ValueError("Azure client not initialized")
        
        # Parse Azure URL
        parts = remote_url.split("/")
        container_name = parts[-2]
        blob_name = parts[-1]
        
        # Delete from Azure
        container_client = self.azure_client.get_container_client(container_name)
        container_client.delete_blob(blob_name)
    
    def _get_backup_metadata(self, backup_file: Path) -> Dict[str, Any]:
        """
        Extract metadata from backup file
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            Metadata dictionary
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract metadata.json from the archive
                with tarfile.open(backup_file, "r:gz") as tar:
                    try:
                        metadata_file = tar.extractfile("metadata.json")
                        if metadata_file:
                            return json.load(metadata_file)
                    except (KeyError, tarfile.ReadError):
                        # Try extracting with a path prefix
                        for member in tar.getmembers():
                            if member.name.endswith("metadata.json"):
                                metadata_file = tar.extractfile(member)
                                if metadata_file:
                                    return json.load(metadata_file)
        except Exception as e:
            logger.warning(f"Error extracting metadata from {backup_file}: {str(e)}")
        
        # Return minimal metadata if extraction failed
        return {
            "backup_name": backup_file.stem,
            "description": "Unknown (metadata extraction failed)"
        }
    
    def _cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policy"""
        try:
            if self.retention_days <= 0:
                return
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            # Clean up local backups
            for file in self.backup_dir.glob("*.tar.gz"):
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if file_time < cutoff_date:
                    try:
                        file.unlink()
                        logger.info(f"Deleted old backup: {file}")
                    except Exception as e:
                        logger.error(f"Error deleting old backup {file}: {str(e)}")
            
            # Clean up remote backups
            if self.storage_type != "local":
                remote_backups = self._list_remote_backups()
                for backup in remote_backups:
                    modified_time = datetime.fromisoformat(backup["modified_time"])
                    if modified_time < cutoff_date:
                        try:
                            self._delete_remote_backup(backup["path"])
                            logger.info(f"Deleted old remote backup: {backup['path']}")
                        except Exception as e:
                            logger.error(f"Error deleting old remote backup {backup['path']}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")

# Create singleton instance
backup_manager = BackupManager()

# Son güncelleme: 2025-05-20 10:59:28
# Güncelleyen: Teeksss