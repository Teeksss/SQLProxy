from typing import Dict
from pydantic import BaseSettings

class SQLProxyConfig(BaseSettings):
    host: str = "sqlproxy"
    port: int = 5000
    username: str
    password: str
    pool_size: int = 10
    timeout: int = 30
    
    class Config:
        env_prefix = "SQLPROXY_"

class DatabaseConfig(BaseSettings):
    sqlproxy: SQLProxyConfig
    max_connections: int = 100
    debug: bool = False
    
    class Config:
        env_prefix = "DB_"