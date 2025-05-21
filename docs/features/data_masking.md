# Sorgu İçerik Maskeleme Özelliği

## Genel Bakış
Sorgu içerik maskeleme özelliği, hassas veri içeren kolonların (TCKN, kredi kartı numarası, maaş bilgileri vb.) API çıkışında otomatik olarak maskelenmesini sağlar. Bu özellik, veri güvenliği ve KVKK/GDPR gibi düzenlemelere uyumluluk açısından kritik öneme sahiptir.

## Özellik Detayları

### Maskeleme Kuralları
- **TCKN**: İlk 5 rakam gösterilir, kalan rakamlar '*' ile maskelenir (örn: 12345******)
- **Kredi Kartı**: İlk 6 ve son 4 rakam gösterilir, aradakiler '*' ile maskelenir (örn: 456789******1234)
- **Email**: @ işaretinden önceki ilk 2 karakter gösterilir, kalanı '*' ile maskelenir (örn: jo**@domain.com)
- **Telefon**: İlk 3 ve son 2 rakam gösterilir, aradakiler '*' ile maskelenir (örn: 532*****34)
- **Maaş/Finansal Veri**: Tam olarak maskelenir, '*****' gösterilir

### Konfigürasyon
- Maskeleme kuralları, sistem yapılandırma dosyasından düzenlenebilir
- Rol bazlı maskeleme豩iyetlendirme (bazı rollerin maskelenmemiş verileri görebilmesi)
- Kolon isimlerine göre otomatik tespit (örn: "tckn", "cc_number", "salary" vb.)

## Teknik Uygulama

### Backend Değişiklikleri
1. `app/proxy/sql_proxy.py`: Sorgu sonuçları işlenirken maskeleme katmanı eklenmesi
2. `app/config/masking_rules.py`: Maskeleme kurallarının tanımlanması
3. `app/models/whitelist.py`: Whitelist modelinde maskeleme tercihlerinin saklanması

### Frontend Değişiklikleri
1. `src/pages/Whitelist.jsx`: Beyaz liste formuna maskeleme seçenekleri eklenmesi
2. `src/pages/Settings.jsx`: Sistem geneli maskeleme kurallarının yönetimi
3. `src/components/DataTable.jsx`: Maskelenmiş verilerin görsel gösterimi

### API Değişiklikleri
Yeni API endpoint'leri:
- `GET /api/admin/masking-rules`: Mevcut maskeleme kurallarını listeler
- `POST /api/admin/masking-rules`: Yeni maskeleme kuralı ekler
- `PUT /api/admin/masking-rules/{rule_id}`: Mevcut maskeleme kuralını günceller
- `DELETE /api/admin/masking-rules/{rule_id}`: Maskeleme kuralını siler

## Uygulama Adımları

### 1. Faz - Temel Maskeleme Altyapısı (1 hafta)
- Backend maskeleme katmanı oluşturma
- Temel maskeleme kurallarını tanımlama
- SQL Parser'a maskeleme desteği ekleme

### 2. Faz - Rol Tabanlı Maskeleme (3 gün)
- Rol bazlı maskeleme kurallarını tanımlama
- Kullanıcının rolüne göre maskeleme kontrolü

### 3. Faz - Frontend Entegrasyonu (3 gün)
- Maskeleme yönetimi için kullanıcı arayüzü
- Sorgu önizlemede maskeleme gösterimi
- Beyaz liste formuna maskeleme seçenekleri eklenmesi

### 4. Faz - Test ve Dokümantasyon (1 gün)
- Otomasyon testleri
- Kullanıcı dokümantasyonu
- Performans testleri

## Diğer Notlar
- Maskeleme işlemi, veriyi veritabanında değiştirmez, sadece görüntüleme sırasında uygular
- İleride, farklı maskeleme türleri (hash, encryption, tokenization) eklenebilir
- Audit loglarında maskeleme kullanımı da kaydedilir