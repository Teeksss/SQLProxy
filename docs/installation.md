# SQL Proxy Kurulum Rehberi

Bu dokümantasyon, SQL Proxy sisteminin kurulumu ve yapılandırması için adım adım talimatlar içerir.

*Son Güncelleme: 2025-05-16 13:15:15 UTC*  
*Düzenleyen: Teeksss*

## İçindekiler

- [Gereksinimler](#gereksinimler)
- [Docker ile Kurulum](#docker-ile-kurulum)
- [Manuel Kurulum](#manuel-kurulum)
- [Yapılandırma](#yapılandırma)
- [Doğrulama](#doğrulama)
- [Sorun Giderme](#sorun-giderme)

## Gereksinimler

### Donanım Gereksinimleri
- **CPU**: En az 2 çekirdek
- **RAM**: En az 4GB
- **Disk**: En az 20GB boş alan

### Yazılım Gereksinimleri
- **İşletim Sistemi**: Ubuntu 22.04 LTS / Windows Server 2022 / macOS 13+
- **Python**: 3.9+
- **Node.js**: 16+
- **PostgreSQL**: 13+
- **Docker**: 20.10+ (Docker ile kurulum için)
- **Docker Compose**: 2.0+ (Docker ile kurulum için)

## Docker ile Kurulum

Docker kullanarak hızlı kurulum için aşağıdaki adımları izleyin:

1. Projeyi klonlayın:
   ```bash
   git clone https://github.com/yourcompany/sql-proxy.git
   cd sql-proxy