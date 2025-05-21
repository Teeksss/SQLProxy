# SQL Proxy Kullanıcı Kılavuzu

Bu dokümantasyon, SQL Proxy sisteminin kullanımı hakkında detaylı rehber sağlar.

*Son Güncelleme: 2025-05-16 13:22:27 UTC*  
*Düzenleyen: Teeksss*

## İçindekiler

- [Başlarken](#başlarken)
- [Sorgu Çalıştırma](#sorgu-çalıştırma)
- [Sorgu Geçmişi](#sorgu-geçmişi)
- [Sorgu Onaylama Süreci](#sorgu-onaylama-süreci)
- [Beyaz Liste Yönetimi](#beyaz-liste-yönetimi)
- [Sunucu Yönetimi](#sunucu-yönetimi)
- [Kullanıcı Rolleri](#kullanıcı-rolleri)
- [Denetim Logları](#denetim-logları)
- [PowerBI Entegrasyonu](#powerbi-entegrasyonu)
- [Sık Sorulan Sorular](#sık-sorulan-sorular)

## Başlarken

### Giriş Yapma

1. Web tarayıcınızda SQL Proxy uygulamasına gidin: `http://your-sql-proxy-server`
2. LDAP kullanıcı adınızı ve şifrenizi girin
3. "Giriş Yap" düğmesine tıklayın

![Giriş Ekranı](images/login_screen.png)

### Arayüz Tanıtımı

Giriş yaptıktan sonra, rolünüze bağlı olarak farklı bir arayüz görüntülenir:

- **Admin**: Tüm yönetim özellikleri ve panellere erişim
- **Analist**: Sorgu paneli ve geçmiş sorgulara erişim
- **Salt Okunur Kullanıcı**: Sadece onaylanmış sorguları çalıştırabilme

![Dashboard Ekranı](images/dashboard_screen.png)

## Sorgu Çalıştırma

### Sorgu Paneli Kullanımı

1. Sol menüden "Sorgu Paneli"ne tıklayın
2. Sunucu seçin dropdown menüsünden bir veritabanı sunucusu seçin
3. SQL Editor alanına sorgunuzu yazın
4. "Çalıştır" düğmesine tıklayın

![Sorgu Paneli](images/query_panel.png)

### Sorgu Sonuçları

Sorgu çalıştırıldıktan sonra, sonuç panelinde şunlar görüntülenir:

- Veri tablosu (sonuç setini gösterir)
- Etkilenen satır sayısı
- Çalışma süresi (milisaniye)
- Hata mesajları (varsa)

Sonuç verileri CSV olarak dışa aktarılabilir.

### SQL Yazım İpuçları

- **Filtreleme**: Her zaman WHERE koşullarını ekleyin
- **Sınırlama**: Büyük tablolarda LIMIT kullanın
- **İndeksleme**: İndekslenmiş alanlara göre filtreleme yapın
- **Birleştirme**: JOIN koşullarını doğru belirtin
- **Sorgu Performansı**: Karmaşık alt sorgulardan kaçının

## Sorgu Geçmişi

### Geçmiş Sorguları Görüntüleme

1. Sol menüden "Sorgu Geçmişi"ne tıklayın
2. Filtreleme seçeneklerini kullanarak belirli sorguları arayın
3. Bir sorguya tıklayarak detayları görüntüleyin

![Sorgu Geçmişi](images/query_history.png)

### Geçmiş Sorguları Yeniden Çalıştırma

1. Sorgu geçmişinden bir sorgu seçin
2. "Tekrar Çalıştır" düğmesine tıklayın
3. Sorgu, Sorgu Panelinde otomatik olarak yüklenir ve çalıştırılır

## Sorgu Onaylama Süreci

### Onay Gerektiren Sorgular

Aşağıdaki durumlarda sorgu onayı gereklidir:

- Daha önce çalıştırılmamış sorgular
- Yüksek riskli olarak değerlendirilen sorgular
- UPDATE veya DELETE işlemleri
- DDL işlemleri (CREATE, DROP, ALTER)

### Onay İş Akışı

1. Kullanıcı sorguyu çalıştırır
2. Sistem, sorgunun beyaz listede olup olmadığını kontrol eder
3. Beyaz listede değilse, "Onay Bekliyor" mesajı görüntülenir
4. Admin kullanıcıları "Sorgu Onayları" sayfasında bekleyen sorguları görür
5. Admin sorguyu onaylar veya reddeder
6. Kullanıcı, onaylanan sorguyu tekrar çalıştırabilir

![Onay Süreci](images/approval_workflow.png)

## Beyaz Liste Yönetimi

### Beyaz Listeyi Görüntüleme

1. Sol menüden "Beyaz Liste"ye tıklayın (sadece admin)
2. Filtreleme seçeneklerini kullanarak belirli sorguları arayın
3. Bir sorguya tıklayarak detayları görüntüleyin

![Beyaz Liste](images/whitelist.png)

### Yeni Beyaz Liste Kaydı Ekleme

1. "Yeni Sorgu Ekle" düğmesine tıklayın
2. SQL sorgusunu girin
3. Sorgu açıklaması ekleyin
4. PowerBI için özel olup olmadığını seçin
5. İzin verilen sunucuları belirtin
6. "Kaydet" düğmesine tıklayın

### Beyaz Liste Kaydını Düzenleme

1. Düzenlemek istediğiniz sorgu kaydının "Düzenle" düğmesine tıklayın
2. Gerekli değişiklikleri yapın
3. "Güncelle" düğmesine tıklayın

## Sunucu Yönetimi

### Sunucuları Görüntüleme

1. Sol menüden "Sunucular"a tıklayın (sadece admin)
2. Mevcut veritabanı sunucularının listesini görüntüleyin

![Sunucu Yönetimi](images/server_management.png)

### Yeni Sunucu Ekleme

1. "Yeni Sunucu Ekle" düğmesine tıklayın
2. Sunucu bilgilerini doldurun:
   - Sunucu Alias (benzersiz tanımlayıcı)
   - Açıklama
   - Sunucu Adresi
   - Port
   - Veritabanı Adı
   - İzin Verilen Roller
3. "Bağlantıyı Test Et" düğmesine tıklayın
4. Başarılı test sonrasında "Kaydet" düğmesine tıklayın

### Sunucu Düzenleme

1. Düzenlemek istediğiniz sunucunun "Düzenle" düğmesine tıklayın
2. Gerekli değişiklikleri yapın
3. "Güncelle" düğmesine tıklayın

## Kullanıcı Rolleri

### Mevcut Rolleri Görüntüleme

1. Sol menüden "Kullanıcı Rolleri"ne tıklayın (sadece admin)
2. Sistemdeki rolleri ve her role atanmış kullanıcıları görüntüleyin

![Kullanıcı Rolleri](images/user_roles.png)

### Rol İzinleri

Her rol için farklı izinler tanımlanabilir:

- **Sorgu Çalıştırma**: Sorguları çalıştırabilme
- **Kendi Sorgularını Yönetme**: Kullanıcının kendi sorgularını düzenleyebilmesi
- **Sorgu Onaylama**: Başkalarının sorgularını onaylayabilme
- **Beyaz Liste Yönetimi**: Beyaz listeyi düzenleyebilme
- **Sunucu Yönetimi**: Veritabanı sunucularını yapılandırabilme
- **Rol Yönetimi**: Kullanıcı rollerini yönetebilme
- **Rate Limit Yönetimi**: Rate limitleri yapılandırabilme
- **PowerBI API Kullanımı**: PowerBI API'lerini kullanabilme

### Kullanıcıları Rollere Atama

1. Bir rolü seçin
2. "Kullanıcılar" sekmesine tıklayın
3. "Kullanıcı Ekle" düğmesine tıklayın
4. LDAP kullanıcı adını girin veya listeden seçin
5. "Ekle" düğmesine tıklayın

## Denetim Logları

### Audit Logları Görüntüleme

1. Sol menüden "Audit Loglar"a tıklayın (sadece admin)
2. Filtreleme seçeneklerini kullanarak belirli logları arayın
3. Bir loga tıklayarak detayları görüntüleyin

![Audit Loglar](images/audit_logs.png)

### Log Filtreleme

Aşağıdaki kriterlere göre logları filtreleyebilirsiniz:

- Kullanıcı adı
- Sorgu tipi (SELECT, INSERT, UPDATE, vb.)
- Sunucu adı
- Tarih aralığı
- Durum (başarılı, hata, reddedildi)

### Log Dışa Aktarma

Logları CSV formatında dışa aktarmak için:

1. Filtreleme seçeneklerini kullanarak istediğiniz logları görüntüleyin
2. "CSV İndir" düğmesine tıklayın
3. Dosyayı bilgisayarınıza kaydedin

## Rate Limit Yönetimi

### Rate Limitleri Görüntüleme

1. Sol menüden "Rate Limitleri"ne tıklayın (sadece admin)
2. Mevcut rate limit kurallarını görüntüleyin

![Rate Limit Yönetimi](images/rate_limits.png)

### Yeni Rate Limit Kuralı Ekleme

1. "Yeni Kural Ekle" düğmesine tıklayın
2. Kural tipini seçin (rol, kullanıcı veya IP)
3. İlgili tanımlayıcıyı belirtin
4. Maksimum istek sayısını ve süre penceresini ayarlayın
5. "Ekle" düğmesine tıklayın

## PowerBI Entegrasyonu

### PowerBI Veri Kaynağı Oluşturma

1. PowerBI Desktop'ı açın
2. "Veri Al" > "Web" seçeneğini tıklayın
3. URL'yi şu formatta girin: