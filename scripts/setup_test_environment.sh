#!/bin/bash

# Exit on error
set -e

echo "Setting up test environment for SQLProxy..."

# Python sürümünü kontrol et
python_version=$(python --version 2>&1)
echo "Using ${python_version}"

# pip'i güncelle
python -m pip install --upgrade pip
echo "pip version: $(pip --version)"

# Test bağımlılıklarını yükle
echo "Installing pytest and other test dependencies..."
pip install pytest pytest-cov pytest-asyncio pytest-mock numpy pandas scipy

# pytest'in doğru şekilde yüklendiğini doğrula
echo "Verifying pytest installation..."
pytest_path=$(which pytest || echo "NOT FOUND")
echo "pytest path: ${pytest_path}"

if [ "${pytest_path}" = "NOT FOUND" ]; then
    echo "Pytest was not installed correctly. Trying alternative installation..."
    python -m pip install pytest
    
    # PATH'e ~/.local/bin ekle (kullanıcı kurulumu yapıldıysa)
    export PATH=$PATH:~/.local/bin
    
    # Tekrar kontrol et
    pytest_path=$(which pytest || echo "STILL NOT FOUND")
    echo "pytest path (after fix): ${pytest_path}"
    
    if [ "${pytest_path}" = "STILL NOT FOUND" ]; then
        echo "Installing pytest directly to the current Python environment..."
        python -m pip install --force-reinstall pytest
        
        echo "Creating pytest executable link..."
        PYTHON_BIN_DIR=$(dirname $(which python))
        ln -sf ${PYTHON_BIN_DIR}/python -m pytest ${PYTHON_BIN_DIR}/pytest
        
        # Son kontrol
        pytest_path=$(which pytest || echo "INSTALLATION FAILED")
        echo "pytest path (final check): ${pytest_path}"
    fi
fi

# Yüklenen paketleri listele
echo "Installed packages:"
pip list

# Çalışma dizinini kontrol et
echo "Working directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "Test environment setup completed!"