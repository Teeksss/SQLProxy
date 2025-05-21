"""
Backup Service for SQL Proxy

This module provides functionality for automated backups of
both database data and configuration.

Last updated: 2025-05-20 12:39:30
Updated by: Teeksss
"""

import os
import json
import logging
import tarfile
import shutil
import tempfile
import datetime
import subprocess
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

import boto3
from google.cloud import storage
from azure.storage.blob import BlobServiceClient
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url

from app.core.config import settings
from app.db.session import engine
from app.models.backup import BackupRecord, BackupStatus

logger = logging.getLogger(__name__)

class BackupService:
    """
    Service for creating and managing backups
    
    Provides functionality for both automated and manual backups,
    with support for local storage and cloud providers (S3, GCS, Azure).
    """
    
    def __init__(self):
        """Initialize backup service"""
        self.backup_path = Path(settings.BACKUP_STORAGE_PATH)
        self.backup_path.mkdir(parents=True, exist_ok=True)
        self.storage_type = settings.BACKUP_STORAGE_TYPE
        
        # Connect to database
        self.db_url = make_url(str(settings.DATABASE_URI))
        
        # Initialize cloud storage if needed
        if self.storage_type == "s3":
            self._init_s3()
        elif self.storage_type == "gcs":
            self._init_gcs()
        elif self.storage_type == "azure":
            self._init_azure()
            
        logger.info(f"Backup service initialized with storage type: {self.storage_type}")
    
    def _init_s3(self):
        """Initialize AWS S3 client"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION
        )
        self.s3_bucket = settings.S3_BUCKET
        
        # Check if bucket exists
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
        except Exception as e:
            logger.error(f"Error connecting to S3 bucket: {e}")
            raise
    
    def _init_gcs(self):
        """Initialize Google Cloud Storage client"""
        try:
            self.gcs_client = storage.Client()
            self.gcs_bucket = self.gcs_client.bucket(settings.GCS_BUCKET)
        except Exception as e:
            logger.error(f"Error connecting to GCS bucket: {e}")
            raise
    
    def _init_azure(self):
        """Initialize Azure Blob Storage client"""
        try:
            connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
            self.azure_client = BlobServiceClient.from_connection_string(connection_string)
            self.azure_container = settings.AZURE_CONTAINER
        except Exception as e:
            logger.error(f"Error connecting to Azure Blob Storage: {e}")
            raise
    
    async def create_backup(self, 
                          backup_type: str = "full", 
                          description: str = "Automated backup", 
                          include_queries: bool = True) -> Optional[BackupRecord]:
        """
        Create a new backup
        
        Args:
            backup_type: Type of backup ("full" or "incremental")
            description: Backup description
            include_queries: Whether to include saved queries
            
        Returns:
            Created backup record if successful, None otherwise
        """
        try:
            # Create a unique backup ID based on timestamp
            timestamp = datetime.datetime.utcnow()
            backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Create temporary directory for backup files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Back up database
                db_backup_path = await self._backup_database(temp_path, backup_type)
                
                # Back up configuration
                config_backup_path = await self._backup_configuration(temp_path, include_queries)
                
                # Create metadata file
                metadata = {
                    "backup_id": backup_id,
                    "timestamp": timestamp.isoformat(),
                    "backup_type": backup_type,
                    "description": description,
                    "database_version": engine.dialect.server_version_info,
                    "includes_queries": include_queries,
                    "sql_proxy_version": settings.VERSION
                }
                
                with open(temp_path / "metadata.json", "w") as f:
                    json.dump(metadata, f, indent=2)
                
                # Create archive
                backup_filename = f"{backup_id}.tar.gz"
                archive_path = self.backup_path / backup_filename
                
                with tarfile.open(archive_path, "w:gz") as tar:
                    for file_path in temp_path.glob("**/*"):
                        if file_path.is_file():
                            tar.add(file_path, arcname=file_path.relative_to(temp_path))
                
                # Upload to cloud storage if configured
                remote_path = await self._upload_backup(archive_path, backup_id)
                
                # Create backup record
                backup_record = await self._create_backup_record(
                    backup_id=backup_id,
                    filename=backup_filename,
                    backup_type=backup_type,
                    description=description,
                    size_bytes=archive_path.stat().st_size,
                    remote_path=remote_path,
                    metadata=metadata
                )
                
                # Clean up local file if using cloud storage
                if self.storage_type != "local":
                    archive_path.unlink()
                
                logger.info(f"Backup created successfully: {backup_id}")
                return backup_record
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return None
    
    async def _backup_database(self, temp_path: Path, backup_type: str) -> Path:
        """
        Back up the database
        
        Args:
            temp_path: Temporary directory path
            backup_type: Type of backup
            
        Returns:
            Path to the database backup file
        """
        db_backup_path = temp_path / "database"
        db_backup_path.mkdir(exist_ok=True)
        
        if self.db_url.drivername.startswith("postgresql"):
            return await self._backup_postgresql(db_backup_path, backup_type)
        elif self.db_url.drivername.startswith("mysql"):
            return await self._backup_mysql(db_backup_path, backup_type)
        elif self.db_url.drivername.startswith("sqlite"):
            return await self._backup_sqlite(db_backup_path, backup_type)
        else:
            logger.warning(f"Unsupported database type for backup: {self.db_url.drivername}")
            # Create a placeholder file
            with open(db_backup_path / "database_backup_not_supported.txt", "w") as f:
                f.write(f"Database backup not supported for {self.db_url.drivername}")
            return db_backup_path
    
    async def _backup_postgresql(self, backup_path: Path, backup_type: str) -> Path:
        """
        Back up PostgreSQL database
        
        Args:
            backup_path: Path to save the backup
            backup_type: Type of backup
            
        Returns:
            Path to the backup file
        """
        try:
            # Determine pg_dump command
            command = [
                "pg_dump",
                "-h", self.db_url.host or "localhost",
                "-p", str(self.db_url.port or 5432),
                "-U", self.db_url.username,
                "-d", self.db_url.database,
                "-F", "c",  # Custom format
                "-f", str(backup_path / "database.dump")
            ]
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_url.password or ""
            
            # Execute pg_dump
            result = subprocess.run(
                command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            return backup_path / "database.dump"
            
        except Exception as e:
            logger.error(f"Error backing up PostgreSQL database: {e}", exc_info=True)
            raise
    
    async def _backup_mysql(self, backup_path: Path, backup_type: str) -> Path:
        """
        Back up MySQL database
        
        Args:
            backup_path: Path to save the backup
            backup_type: Type of backup
            
        Returns:
            Path to the backup file
        """
        try:
            # Determine mysqldump command
            command = [
                "mysqldump",
                "-h", self.db_url.host or "localhost",
                "-P", str(self.db_url.port or 3306),
                "-u", self.db_url.username,
                "--single-transaction",
                "--routines",
                "--triggers",
                "--events",
                self.db_url.database
            ]
            
            # Set MYSQL_PWD environment variable
            env = os.environ.copy()
            env["MYSQL_PWD"] = self.db_url.password or ""
            
            # Execute mysqldump and save to file
            with open(backup_path / "database.sql", "w") as f:
                result = subprocess.run(
                    command,
                    env=env,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            if result.returncode != 0:
                logger.error(f"mysqldump failed: {result.stderr}")
                raise Exception(f"mysqldump failed: {result.stderr}")
            
            return backup_path / "database.sql"
            
        except Exception as e:
            logger.error(f"Error backing up MySQL database: {e}", exc_info=True)
            raise
    
    async def _backup_sqlite(self, backup_path: Path, backup_type: str) -> Path:
        """
        Back up SQLite database
        
        Args:
            backup_path: Path to save the backup
            backup_type: Type of backup
            
        Returns:
            Path to the backup file
        """
        try:
            # Extract database path from URL
            db_path = self.db_url.database
            
            # Simply copy the SQLite database file
            shutil.copy(db_path, backup_path / "database.sqlite")
            
            return backup_path / "database.sqlite"
            
        except Exception as e:
            logger.error(f"Error backing up SQLite database: {e}", exc_info=True)
            raise
    
    async def _backup_configuration(self, temp_path: Path, include_queries: bool) -> Path:
        """
        Back up configuration files
        
        Args:
            temp_path: Temporary directory path
            include_queries: Whether to include saved queries
            
        Returns:
            Path to the configuration backup directory
        """
        try:
            config_backup_path = temp_path / "config"
            config_backup_path.mkdir(exist_ok=True)
            
            # Copy configuration files
            config_dir = Path("config")
            if config_dir.exists():
                for file_path in config_dir.glob("**/*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(config_dir)
                        dest_path = config_backup_path / relative_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy(file_path, dest_path)
            
            # Export server configurations
            await self._export_server_configs(config_backup_path)
            
            # Export saved queries if requested
            if include_queries:
                await self._export_saved_queries(config_backup_path)
            
            return config_backup_path
            
        except Exception as e:
            logger.error(f"Error backing up configuration: {e}", exc_info=True)
            raise
    
    async def _export_server_configs(self, config_path: Path) -> None:
        """
        Export server configurations to JSON
        
        Args:
            config_path: Path to save the configurations
        """
        try:
            from app.db.session import get_db
            from app.models.server import ServerConfig
            
            db = next(get_db())
            servers = db.query(ServerConfig).all()
            
            server_configs = []
            for server in servers:
                # Convert server to dict, excluding sensitive information
                server_dict = {
                    "id": server.id,
                    "alias": server.alias,
                    "description": server.description,
                    "server_type": server.server_type,
                    "host": server.host,
                    "port": server.port,
                    "database": server.database,
                    "schema": server.schema,
                    "username": server.username,
                    # Skip password
                    "ssl_enabled": server.ssl_enabled,
                    "ca_cert": None,  # Skip certificates
                    "client_cert": None,
                    "client_key": None,
                    "environment": server.environment,
                    "is_active": server.is_active,
                    "created_at": server.created_at.isoformat() if server.created_at else None,
                    "updated_at": server.updated_at.isoformat() if server.updated_at else None
                }
                server_configs.append(server_dict)
            
            with open(config_path / "server_configs.json", "w") as f:
                json.dump(server_configs, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting server configurations: {e}", exc_info=True)
            raise
    
    async def _export_saved_queries(self, config_path: Path) -> None:
        """
        Export saved queries to JSON
        
        Args:
            config_path: Path to save the queries
        """
        try:
            from app.db.session import get_db
            from app.models.query import SavedQuery
            
            db = next(get_db())
            queries = db.query(SavedQuery).all()
            
            saved_queries = []
            for query in queries:
                query_dict = {
                    "id": query.id,
                    "name": query.name,
                    "description": query.description,
                    "query_text": query.query_text,
                    "server_id": query.server_id,
                    "is_public": query.is_public,
                    "user_id": query.user_id,
                    "parameters": query.parameters,
                    "tags": query.tags,
                    "created_at": query.created_at.isoformat() if query.created_at else None,
                    "updated_at": query.updated_at.isoformat() if query.updated_at else None
                }
                saved_queries.append(query_dict)
            
            with open(config_path / "saved_queries.json", "w") as f:
                json.dump(saved_queries, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting saved queries: {e}", exc_info=True)
            raise
    
    async def _upload_backup(self, backup_path: Path, backup_id: str) -> Optional[str]:
        """
        Upload backup to cloud storage
        
        Args:
            backup_path: Path to the backup file
            backup_id: Backup identifier
            
        Returns:
            Remote path where the backup was stored, or None for local storage
        """
        if self.storage_type == "local":
            return None
            
        try:
            if self.storage_type == "s3":
                return await self._upload_to_s3(backup_path, backup_id)
            elif self.storage_type == "gcs":
                return await self._upload_to_gcs(backup_path, backup_id)
            elif self.storage_type == "azure":
                return await self._upload_to_azure(backup_path, backup_id)
            else:
                logger.warning(f"Unsupported storage type: {self.storage_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading backup: {e}", exc_info=True)
            raise
    
    async def _upload_to_s3(self, backup_path: Path, backup_id: str) -> str:
        """
        Upload backup to AWS S3
        
        Args:
            backup_path: Path to the backup file
            backup_id: Backup identifier
            
        Returns:
            S3 path where the backup was stored
        """
        try:
            # Determine S3 key (path within bucket)
            s3_key = f"backups/{backup_id}/{backup_path.name}"
            
            # Upload file
            with open(backup_path, "rb") as f:
                self.s3_client.upload_fileobj(f, self.s3_bucket, s3_key)
            
            return f"s3://{self.s3_bucket}/{s3_key}"
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}", exc_info=True)
            raise
    
    async def _upload_to_gcs(self, backup_path: Path, backup_id: str) -> str:
        """
        Upload backup to Google Cloud Storage
        
        Args:
            backup_path: Path to the backup file
            backup_id: Backup identifier
            
        Returns:
            GCS path where the backup was stored
        """
        try:
            # Determine GCS blob name (path within bucket)
            blob_name = f"backups/{backup_id}/{backup_path.name}"
            
            # Upload file
            blob = self.gcs_bucket.blob(blob_name)
            blob.upload_from_filename(str(backup_path))
            
            return f"gs://{self.gcs_bucket.name}/{blob_name}"
            
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}", exc_info=True)
            raise
    
    async def _upload_to_azure(self, backup_path: Path, backup_id: str) -> str:
        """
        Upload backup to Azure Blob Storage
        
        Args:
            backup_path: Path to the backup file
            backup_id: Backup identifier
            
        Returns:
            Azure path where the backup was stored
        """
        try:
            # Determine blob name (path within container)
            blob_name = f"backups/{backup_id}/{backup_path.name}"
            
            # Upload file
            blob_client = self.azure_client.get_blob_client(
                container=self.azure_container,
                blob=blob_name
            )
            
            with open(backup_path, "rb") as f:
                blob_client.upload_blob(f)
            
            return f"azure://{self.azure_container}/{blob_name}"
            
        except Exception as e:
            logger.error(f"Error uploading to Azure: {e}", exc_info=True)
            raise
    
    async def _create_backup_record(self, 
                                   backup_id: str, 
                                   filename: str, 
                                   backup_type: str, 
                                   description: str, 
                                   size_bytes: int, 
                                   remote_path: Optional[str], 
                                   metadata: Dict[str, Any]) -> BackupRecord:
        """
        Create a backup record in the database
        
        Args:
            backup_id: Backup identifier
            filename: Backup filename
            backup_type: Type of backup
            description: Backup description
            size_bytes: Size of the backup in bytes
            remote_path: Remote storage path
            metadata: Backup metadata
            
        Returns:
            Created backup record
        """
        try:
            from app.db.session import get_db
            
            db = next(get_db())
            
            backup_record = BackupRecord(
                backup_id=backup_id,
                filename=filename,
                backup_type=backup_type,
                description=description,
                size_bytes=size_bytes,
                storage_type=self.storage_type,
                storage_path=remote_path or str(self.backup_path / filename),
                metadata=json.dumps(metadata),
                status=BackupStatus.COMPLETED.value,
                created_at=datetime.datetime.utcnow()
            )
            
            db.add(backup_record)
            db.commit()
            db.refresh(backup_record)
            
            return backup_record
            
        except Exception as e:
            logger.error(f"Error creating backup record: {e}", exc_info=True)
            raise
    
    async def list_backups(
        self, 
        limit: int = 100, 
        offset: int = 0, 
        backup_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[BackupRecord]:
        """
        List backup records
        
        Args:
            limit: Maximum number of records to return
            offset: Offset for pagination
            backup_type: Filter by backup type
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            
        Returns:
            List of backup records
        """
        try:
            from app.db.session import get_db
            from sqlalchemy import desc, asc
            
            db = next(get_db())
            
            # Build query
            query = db.query(BackupRecord)
            
            # Apply filters
            if backup_type:
                query = query.filter(BackupRecord.backup_type == backup_type)
            
            # Apply sorting
            if sort_order.lower() == "desc":
                query = query.order_by(desc(getattr(BackupRecord, sort_by)))
            else:
                query = query.order_by(asc(getattr(BackupRecord, sort_by)))
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}", exc_info=True)
            raise
    
    async def get_backup(self, backup_id: str) -> Optional[BackupRecord]:
        """
        Get a backup record by ID
        
        Args:
            backup_id: Backup identifier
            
        Returns:
            Backup record if found, None otherwise
        """
        try:
            from app.db.session import get_db
            
            db = next(get_db())
            
            return db.query(BackupRecord).filter(BackupRecord.backup_id == backup_id).first()
            
        except Exception as e:
            logger.error(f"Error getting backup: {e}", exc_info=True)
            raise
    
    async def restore_backup(self, backup_id: str) -> bool:
        """
        Restore a backup
        
        Args:
            backup_id: Backup identifier
            
        Returns:
            True if restored successfully, False otherwise
        """
        try:
            # Get backup record
            backup_record = await self.get_backup(backup_id)
            if not backup_record:
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            # Create temporary directory for restoration
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Download backup if needed
                backup_file = await self._download_backup(backup_record, temp_path)
                
                # Extract backup archive
                extract_path = temp_path / "extract"
                extract_path.mkdir(exist_ok=True)
                
                with tarfile.open(backup_file, "r:gz") as tar:
                    tar.extractall(path=extract_path)
                
                # Restore database
                await self._restore_database(extract_path / "database")
                
                # Restore configuration if needed
                # Note: Be careful with configuration restoration, as it might override current settings
                # await self._restore_configuration(extract_path / "config")
                
                logger.info(f"Backup restored successfully: {backup_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error restoring backup: {e}", exc_info=True)
            return False
    
    async def _download_backup(self, backup_record: BackupRecord, temp_path: Path) -> Path:
        """
        Download a backup file
        
        Args:
            backup_record: Backup record
            temp_path: Temporary directory path
            
        Returns:
            Path to the downloaded backup file
        """
        try:
            if backup_record.storage_type == "local":
                # For local storage, just copy the file
                local_path = Path(backup_record.storage_path)
                if not local_path.exists():
                    raise FileNotFoundError(f"Backup file not found: {local_path}")
                
                dest_path = temp_path / backup_record.filename
                shutil.copy(local_path, dest_path)
                return dest_path
                
            elif backup_record.storage_type == "s3":
                # Parse S3 path
                s3_path = backup_record.storage_path
                if not s3_path.startswith("s3://"):
                    raise ValueError(f"Invalid S3 path: {s3_path}")
                
                parts = s3_path[5:].split('/', 1)
                if len(parts) < 2:
                    raise ValueError(f"Invalid S3 path format: {s3_path}")
                
                bucket = parts[0]
                key = parts[1]
                
                # Download from S3
                dest_path = temp_path / backup_record.filename
                self.s3_client.download_file(bucket, key, str(dest_path))
                return dest_path
                
            elif backup_record.storage_type == "gcs":
                # Parse GCS path
                gcs_path = backup_record.storage_path
                if not gcs_path.startswith("gs://"):
                    raise ValueError(f"Invalid GCS path: {gcs_path}")
                
                parts = gcs_path[5:].split('/', 1)
                if len(parts) < 2:
                    raise ValueError(f"Invalid GCS path format: {gcs_path}")
                
                bucket_name = parts[0]
                blob_name = parts[1]
                
                # Download from GCS
                bucket = self.gcs_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                
                dest_path = temp_path / backup_record.filename
                blob.download_to_filename(str(dest_path))
                return dest_path
                
            elif backup_record.storage_type == "azure":
                # Parse Azure path
                azure_path = backup_record.storage_path
                if not azure_path.startswith("azure://"):
                    raise ValueError(f"Invalid Azure path: {azure_path}")
                
                parts = azure_path[9:].split('/', 1)
                if len(parts) < 2:
                    raise ValueError(f"Invalid Azure path format: {azure_path}")
                
                container_name = parts[0]
                blob_name = parts[1]
                
                # Download from Azure
                blob_client = self.azure_client.get_blob_client(
                    container=container_name,
                    blob=blob_name
                )
                
                dest_path = temp_path / backup_record.filename
                with open(dest_path, "wb") as f:
                    download_stream = blob_client.download_blob()
                    f.write(download_stream.readall())
                
                return dest_path
                
            else:
                raise ValueError(f"Unsupported storage type: {backup_record.storage_type}")
                
        except Exception as e:
            logger.error(f"Error downloading backup: {e}", exc_info=True)
            raise
    
    async def _restore_database(self, backup_path: Path) -> None:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to the database backup directory
        """
        try:
            if self.db_url.drivername.startswith("postgresql"):
                await self._restore_postgresql(backup_path)
            elif self.db_url.drivername.startswith("mysql"):
                await self._restore_mysql(backup_path)
            elif self.db_url.drivername.startswith("sqlite"):
                await self._restore_sqlite(backup_path)
            else:
                logger.warning(f"Unsupported database type for restore: {self.db_url.drivername}")
                
        except Exception as e:
            logger.error(f"Error restoring database: {e}", exc_info=True)
            raise
    
    async def _restore_postgresql(self, backup_path: Path) -> None:
        """
        Restore PostgreSQL database from backup
        
        Args:
            backup_path: Path to the database backup directory
        """
        try:
            dump_file = backup_path / "database.dump"
            if not dump_file.exists():
                raise FileNotFoundError(f"PostgreSQL dump file not found: {dump_file}")
            
            # Determine pg_restore command
            command = [
                "pg_restore",
                "-h", self.db_url.host or "localhost",
                "-p", str(self.db_url.port or 5432),
                "-U", self.db_url.username,
                "-d", self.db_url.database,
                "-c",  # Clean (drop) objects before recreating
                "-v",  # Verbose
                str(dump_file)
            ]
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_url.password or ""
            
            # Execute pg_restore
            result = subprocess.run(
                command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"pg_restore failed: {result.stderr}")
                raise Exception(f"pg_restore failed: {result.stderr}")
            
            logger.info("PostgreSQL database restored successfully")
            
        except Exception as e:
            logger.error(f"Error restoring PostgreSQL database: {e}", exc_info=True)
            raise
    
    async def _restore_mysql(self, backup_path: Path) -> None:
        """
        Restore MySQL database from backup
        
        Args:
            backup_path: Path to the database backup directory
        """
        try:
            dump_file = backup_path / "database.sql"
            if not dump_file.exists():
                raise FileNotFoundError(f"MySQL dump file not found: {dump_file}")
            
            # Determine mysql command
            command = [
                "mysql",
                "-h", self.db_url.host or "localhost",
                "-P", str(self.db_url.port or 3306),
                "-u", self.db_url.username,
                self.db_url.database
            ]
            
            # Set MYSQL_PWD environment variable
            env = os.environ.copy()
            env["MYSQL_PWD"] = self.db_url.password or ""
            
            # Execute mysql
            with open(dump_file, "r") as f:
                result = subprocess.run(
                    command,
                    env=env,
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            if result.returncode != 0:
                logger.error(f"mysql restore failed: {result.stderr}")
                raise Exception(f"mysql restore failed: {result.stderr}")
            
            logger.info("MySQL database restored successfully")
            
        except Exception as e:
            logger.error(f"Error restoring MySQL database: {e}", exc_info=True)
            raise
    
    async def _restore_sqlite(self, backup_path: Path) -> None:
        """
        Restore SQLite database from backup
        
        Args:
            backup_path: Path to the database backup directory
        """
        try:
            backup_file = backup_path / "database.sqlite"
            if not backup_file.exists():
                raise FileNotFoundError(f"SQLite backup file not found: {backup_file}")
            
            # Extract database path from URL
            db_path = self.db_url.database
            
            # Simply copy the SQLite database file, first backing up the existing one
            now = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            if Path(db_path).exists():
                shutil.copy(db_path, f"{db_path}.{now}.bak")
            
            shutil.copy(backup_file, db_path)
            
            logger.info("SQLite database restored successfully")
            
        except Exception as e:
            logger.error(f"Error restoring SQLite database: {e}", exc_info=True)
            raise
    
    async def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup
        
        Args:
            backup_id: Backup identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Get backup record
            backup_record = await self.get_backup(backup_id)
            if not backup_record:
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            # Delete the backup file
            await self._delete_backup_file(backup_record)
            
            # Delete the record
            from app.db.session import get_db
            
            db = next(get_db())
            db.delete(backup_record)
            db.commit()
            
            logger.info(f"Backup deleted successfully: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup: {e}", exc_info=True)
            return False
    
    async def _delete_backup_file(self, backup_record: BackupRecord) -> None:
        """
        Delete a backup file
        
        Args:
            backup_record: Backup record
        """
        try:
            if backup_record.storage_type == "local":
                # For local storage, just delete the file
                local_path = Path(backup_record.storage_path)
                if local_path.exists():
                    local_path.unlink()
                
            elif backup_record.storage_type == "s3":
                # Parse S3 path
                s3_path = backup_record.storage_path
                if not s3_path.startswith("s3://"):
                    raise ValueError(f"Invalid S3 path: {s3_path}")
                
                parts = s3_path[5:].split('/', 1)
                if len(parts) < 2:
                    raise ValueError(f"Invalid S3 path format: {s3_path}")
                
                bucket = parts[0]
                key = parts[1]
                
                # Delete from S3
                self.s3_client.delete_object(Bucket=bucket, Key=key)
                
            elif backup_record.storage_type == "gcs":
                # Parse GCS path
                gcs_path = backup_record.storage_path
                if not gcs_path.startswith("gs://"):
                    raise ValueError(f"Invalid GCS path: {gcs_path}")
                
                parts = gcs_path[5:].split('/', 1)
                if len(parts) < 2:
                    raise ValueError(f"Invalid GCS path format: {gcs_path}")
                
                bucket_name = parts[0]
                blob_name = parts[1]
                
                # Delete from GCS
                bucket = self.gcs_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.delete()
                
            elif backup_record.storage_type == "azure":
                # Parse Azure path
                azure_path = backup_record.storage_path
                if not azure_path.startswith("azure://"):
                    raise ValueError(f"Invalid Azure path: {azure_path}")
                
                parts = azure_path[9:].split('/', 1)
                if len(parts) < 2:
                    raise ValueError(f"Invalid Azure path format: {azure_path}")
                
                container_name = parts[0]
                blob_name = parts[1]
                
                # Delete from Azure
                blob_client = self.azure_client.get_blob_client(
                    container=container_name,
                    blob=blob_name
                )
                blob_client.delete_blob()
                
            else:
                raise ValueError(f"Unsupported storage type: {backup_record.storage_type}")
                
        except Exception as e:
            logger.error(f"Error deleting backup file: {e}", exc_info=True)
            raise

    async def cleanup_old_backups(self, retention_days: Optional[int] = None) -> int:
        """
        Clean up old backups beyond retention period
        
        Args:
            retention_days: Number of days to retain backups (default: from settings)
            
        Returns:
            Number of backups deleted
        """
        try:
            if retention_days is None:
                retention_days = settings.BACKUP_RETENTION_DAYS
            
            # Calculate cutoff date
            cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=retention_days)
            
            # Get backups older than cutoff date
            from app.db.session import get_db
            
            db = next(get_db())
            old_backups = db.query(BackupRecord).filter(BackupRecord.created_at < cutoff_date).all()
            
            deleted_count = 0
            for backup in old_backups:
                try:
                    # Delete the backup file
                    await self._delete_backup_file(backup)
                    
                    # Delete the record
                    db.delete(backup)
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error deleting old backup {backup.backup_id}: {e}")
                    continue
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}", exc_info=True)
            raise

# Initialize backup service
backup_service = BackupService()

# Son güncelleme: 2025-05-20 12:39:30
# Güncelleyen: Teeksss