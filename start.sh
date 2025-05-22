#!/bin/bash

# Environment dosyalarını yükle
set -a
source .env
set +a

# Docker compose başlat
docker-compose up -d

# Servislerin hazır olmasını bekle
echo "Servisler başlatılıyor..."
sleep 10

# Sağlık kontrolü
curl -f http://localhost:5000/health || exit 1
curl -f http://localhost:8000/health || exit 1

echo "Tüm servisler hazır!"