#!/bin/bash

# Poetry kurulumu
curl -sSL https://install.python-poetry.org | python3 -

# Poetry konfigürasyonu
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# Bağımlılıkları yükle
poetry install

# Pre-commit hooks kurulumu
poetry run pre-commit install

# Test ortamını hazırla
poetry run pytest --setup-only

echo "Development ortamı hazır!"