#!/bin/bash

# Ana proje dizinini oluştur
mkdir -p sqlproxy/{core,utils,tests}

# Core modüllerini oluştur
mkdir -p sqlproxy/core/{database,query,analytics}
touch sqlproxy/core/__init__.py
touch sqlproxy/core/database/__init__.py
touch sqlproxy/core/query/__init__.py
touch sqlproxy/core/analytics/__init__.py

# Utils modüllerini oluştur
mkdir -p sqlproxy/utils/{performance,monitoring}
touch sqlproxy/utils/__init__.py
touch sqlproxy/utils/performance/__init__.py
touch sqlproxy/utils/monitoring/__init__.py

# Test dizinlerini oluştur
mkdir -p sqlproxy/tests/{unit,integration,performance}
touch sqlproxy/tests/__init__.py
touch sqlproxy/tests/conftest.py

# Requirements dosyalarını oluştur
cat << EOF > requirements.txt
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
fastapi>=0.68.0
uvicorn>=0.15.0
sqlalchemy>=1.4.0
psycopg2-binary>=2.9.0
redis>=4.0.0
pydantic>=1.8.0
EOF

cat << EOF > requirements-dev.txt
pytest>=7.0.0
pytest-asyncio>=0.18.0
pytest-cov>=2.12.0
pytest-mock>=3.6.0
pytest-benchmark>=3.4.0
pytest-profiling>=1.7.0
black>=22.3.0
flake8>=4.0.1
mypy>=0.910
pre-commit>=2.17.0
EOF

# Setup.py dosyasını oluştur
cat << EOF > setup.py
from setuptools import setup, find_packages

setup(
    name="sqlproxy",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    extras_require={
        'dev': [
            line.strip()
            for line in open("requirements-dev.txt")
            if line.strip() and not line.startswith("#")
        ]
    }
)
EOF

# Test konfigurasyon dosyasını oluştur
cat << EOF > sqlproxy/tests/conftest.py
import os
import sys
import pytest

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

@pytest.fixture(scope='session')
def test_env():
    """Test environment setup"""
    os.environ['TESTING'] = 'true'
    yield
    os.environ.pop('TESTING', None)
EOF