# SQL Proxy - Dağıtım Kılavuzu

*Tarih: 2025-05-20 12:09:27 UTC*  
*Kullanıcı: Teeksss*

## Genel Bakış

Bu kılavuz, SQL Proxy'nin farklı ortamlarda dağıtımı için kapsamlı talimatlar içermektedir. SQL Proxy, Docker ve Kubernetes tabanlı dağıtımları desteklemekte, ayrıca manuel kurulum da mümkündür.

## İçindekiler

1. [Gereksinimler](#gereksinimler)
2. [Docker ile Dağıtım](#docker-ile-dağıtım)
3. [Kubernetes ile Dağıtım](#kubernetes-ile-dağıtım)
4. [Manuel Kurulum](#manuel-kurulum)
5. [Veritabanı Hazırlama](#veritabanı-hazırlama)
6. [Konfigürasyon](#konfigürasyon)
7. [SSL/TLS Yapılandırma](#ssltls-yapılandırma)
8. [Yüksek Erişilebilirlik Ayarları](#yüksek-erişilebilirlik-ayarları)
9. [Üretim Ortamı Kontrol Listesi](#üretim-ortamı-kontrol-listesi)
10. [Sorun Giderme](#sorun-giderme)

## Gereksinimler

### Minimum Sistem Gereksinimleri

- **CPU**: 2 çekirdek (üretim için 4+ önerilir)
- **RAM**: 4GB (üretim için 8GB+ önerilir)
- **Disk**: 20GB SSD (yedeklemeler için ek alan gerekebilir)
- **İşletim Sistemi**: Ubuntu 22.04 LTS, RHEL 8+, veya diğer modern Linux dağıtımları

### Yazılım Gereksinimleri

- Docker 20.10+ veya Kubernetes 1.23+
- PostgreSQL 14+ (meta-veritabanı için)
- Redis 6.2+
- Nginx 1.20+ (ön proxy için)

## Docker ile Dağıtım

### Docker Compose ile Hızlı Başlangıç

1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/example/sql-proxy.git
   cd sql-proxy