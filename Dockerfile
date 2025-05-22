FROM python:3.10-slim AS builder

WORKDIR /app

# Poetry kurulumu
RUN pip install poetry==1.4.2

# Sadece pyproject.toml dosyasını kopyala (poetry.lock olmadan)
COPY pyproject.toml ./

# poetry.lock dosyasını oluştur
RUN poetry config virtualenvs.create false \
    && poetry lock --no-update \
    && poetry install --no-interaction --no-ansi

# Kaynak kodu kopyala
COPY sqlproxy/ sqlproxy/
COPY README.md ./

# Test dosyalarını kopyala (opsiyonel)
COPY tests/ tests/

# Uygulamayı kurmak için
RUN pip install -e .

# Üretim aşaması
FROM python:3.10-slim

WORKDIR /app

# Bağımlılıkları ve uygulamayı builder'dan kopyala
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /app/sqlproxy /app/sqlproxy

# Gerekli ortam değişkenlerini ayarla
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Sağlık kontrolü için
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Uygulamayı çalıştır
CMD ["python", "-m", "sqlproxy"]