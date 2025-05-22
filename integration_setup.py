import os
import shutil
from pathlib import Path
import yaml

def setup_integration():
    """Entegrasyon kurulumunu yapar"""
    
    # Dizin yapısını oluştur
    dirs = [
        'shared',
        'configs',
        'logs',
        'data'
    ]
    
    for dir in dirs:
        Path(dir).mkdir(parents=True, exist_ok=True)
    
    # Config dosyalarını kopyala
    copy_configs()
    
    # Docker compose dosyasını oluştur
    create_docker_compose()
    
    # Environment dosyalarını oluştur
    create_env_files()
    
    print("Entegrasyon kurulumu tamamlandı!")

def copy_configs():
    """Config dosyalarını kopyalar"""
    
    configs = {
        'SQLProxy/config.yaml': 'configs/sqlproxy_config.yaml',
        'MCP-SERVER/config.yaml': 'configs/mcp_config.yaml'
    }
    
    for src, dst in configs.items():
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Config kopyalandı: {dst}")

def create_env_files():
    """Environment dosyalarını oluşturur"""
    
    env_vars = {
        '.env': {
            'POSTGRES_PASSWORD': 'your_secure_password',
            'REDIS_PASSWORD': 'your_secure_password',
            'LOG_LEVEL': 'info'
        },
        'SQLProxy/.env': {
            'DB_HOST': 'postgres',
            'REDIS_HOST': 'redis'
        },
        'MCP-SERVER/.env': {
            'SQLPROXY_HOST': 'sqlproxy',
            'SQLPROXY_PORT': '5000'
        }
    }
    
    for file, vars in env_vars.items():
        with open(file, 'w') as f:
            for key, value in vars.items():
                f.write(f"{key}={value}\n")
        print(f"Environment dosyası oluşturuldu: {file}")

if __name__ == "__main__":
    setup_integration()