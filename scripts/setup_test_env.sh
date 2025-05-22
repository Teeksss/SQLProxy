#!/bin/bash

# Exit on error 
set -e

echo "Setting up test environment..."

# Python ve pip'in kurulu olduğundan emin ol
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
fi

# Virtual environment oluştur
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Pip'i güncelle
echo "Upgrading pip..."
pip install --upgrade pip

# Test dependencies yükle
echo "Installing test dependencies..."
pip install pytest==7.4.0 \
            pytest-asyncio==0.21.1 \
            pytest-cov==4.1.0 \
            pytest-mock==3.11.1 \
            pytest-xdist==3.3.1

# Core dependencies yükle
echo "Installing core dependencies..."
pip install numpy==1.24.3 \
            pandas==2.0.3 \
            scipy==1.10.1 \
            fastapi==0.100.0 \
            uvicorn==0.22.0 \
            sqlalchemy==2.0.18 \
            psycopg2-binary==2.9.6 \
            redis==4.6.0 \
            pydantic==2.0.2

# Development dependencies yükle
echo "Installing development dependencies..."
pip install black==23.3.0 \
            flake8==6.0.0 \
            mypy==1.4.1 \
            pre-commit==3.3.3

# Proje paketini yükle
echo "Installing project package..."
pip install -e .

echo "Test environment setup complete!"