"""
Server CRUD operations for SQL Proxy

This module provides CRUD operations for managing database server connections.

Last updated: 2025-05-21 06:51:05
Updated by: Teeksss
"""

from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.server import Server
from app.schemas.server import ServerCreate, ServerUpdate
from app.services.security_service import security_service
from app.services.vault_service import vault_service

class CRUDServer:
    # ... Mevcut fonksiyonlar ...
    
    async def create(
        self, 
        db: Session, 
        obj_in: ServerCreate, 
        user_id: int
    ) -> Server:
        """
        Create a new server
        
        Args:
            db: Database session
            obj_in: Server creation data
            user_id: User ID
            
        Returns:
            Created server
        """
        # Create a new server object
        server_data = obj_in.dict(exclude={"password"})
        db_obj = Server(**server_data, user_id=user_id)
        
        # Handle password securely based on configuration
        if obj_in.password:
            if obj_in.use_vault and vault_service.is_enabled():
                # Store password in Vault
                db_obj.use_vault = True
                db_obj.password = None  # Don't store in database
                
                # Add server to DB first to get the ID
                db.add(db_obj)
                db.flush()
                
                # Store credentials in Vault
                await vault_service.store_database_credentials(
                    server_id=db_obj.id,
                    credentials={
                        "username": obj_in.username,
                        "password": obj_in.password,
                        "host": obj_in.host,
                        "port": obj_in.port,
                        "database": obj_in.database
                    }
                )
            else:
                # Encrypt password if not using Vault
                db_obj.password = security_service.encrypt(obj_in.password)
                db_obj.is_encrypted = True
        
        # Save server in database
        if not db_obj.id:  # Only add if not already added
            db.add(db_obj)
        
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    async def update(
        self, 
        db: Session, 
        db_obj: Server, 
        obj_in: Union[ServerUpdate, Dict[str, Any]]
    ) -> Server:
        """
        Update a server
        
        Args:
            db: Database session
            db_obj: Existing server object
            obj_in: Server update data
            
        Returns:
            Updated server
        """
        # Update with provided fields
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        
        # Handle password updates securely
        password = update_data.pop("password", None)
        use_vault = update_data.get("use_vault", db_obj.use_vault)
        
        if password:
            if use_vault and vault_service.is_enabled():
                # Store password in Vault
                update_data["use_vault"] = True
                update_data["password"] = None  # Don't store in database
                update_data["is_encrypted"] = False
                
                # Store credentials in Vault
                await vault_service.store_database_credentials(
                    server_id=db_obj.id,
                    credentials={
                        "username": update_data.get("username", db_obj.username),
                        "password": password,
                        "host": update_data.get("host", db_obj.host),
                        "port": update_data.get("port", db_obj.port),
                        "database": update_data.get("database", db_obj.database)
                    }
                )
            else:
                # Encrypt password if not using Vault
                update_data["password"] = security_service.encrypt(password)
                update_data["is_encrypted"] = True
                update_data["use_vault"] = False
        elif "use_vault" in update_data and update_data["use_vault"] != db_obj.use_vault:
            # Handle switching between Vault and encrypted storage
            if update_data["use_vault"] and vault_service.is_enabled():
                # Moving from encrypted to Vault
                if db_obj.password and db_obj.is_encrypted:
                    # Decrypt current password
                    decrypted_password = security_service.decrypt(db_obj.password)
                    
                    # Store in Vault
                    await vault_service.store_database_credentials(
                        server_id=db_obj.id,
                        credentials={
                            "username": update_data.get("username", db_obj.username),
                            "password": decrypted_password,
                            "host": update_data.get("host", db_obj.host),
                            "port": update_data.get("port", db_obj.port),
                            "database": update_data.get("database", db_obj.database)
                        }
                    )
                    
                    # Clear password from database
                    update_data["password"] = None
                    update_data["is_encrypted"] = False
            else:
                # Moving from Vault to encrypted
                credentials = await vault_service.get_database_credentials(db_obj.id)
                if credentials and "password" in credentials:
                    # Encrypt password for database storage
                    update_data["password"] = security_service.encrypt(credentials["password"])
                    update_data["is_encrypted"] = True
        
        # Update server fields
        for field in update_data:
            if field != "password" or update_data[field] is not None:
                setattr(db_obj, field, update_data[field])
        
        # Set updated timestamp
        db_obj.updated_at = datetime.utcnow()
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    async def delete(self, db: Session, server_id: str) -> bool:
        """
        Delete a server
        
        Args:
            db: Database session
            server_id: Server ID
            
        Returns:
            Success status
        """
        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            return False
        
        # Delete credentials from Vault if using it
        if server.use_vault and vault_service.is_enabled():
            await vault_service.delete_secret(f"database/servers/{server.id}")
        
        # Delete from database
        db.delete(server)
        db.commit()
        
        return True
    
    async def get_password(self, db: Session, server: Server) -> Optional[str]:
        """
        Get server password securely
        
        Args:
            db: Database session
            server: Server object
            
        Returns:
            Decrypted password or None
        """
        if not server:
            return None
        
        # Get password from Vault if using it
        if server.use_vault and vault_service.is_enabled():
            credentials = await vault_service.get_database_credentials(server.id)
            if credentials and "password" in credentials:
                return credentials["password"]
            return None
        
        # Decrypt password from database
        if server.password and server.is_encrypted:
            return security_service.decrypt(server.password)
        
        # Return plaintext password (not recommended)
        return server.password

# Initialize CRUD operations
server = CRUDServer()

# Son güncelleme: 2025-05-21 06:51:05
# Güncelleyen: Teeksss