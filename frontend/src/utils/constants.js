// Sistem genelinde kullanılacak sabitler

// Geçerli kullanıcı bilgileri
export const CURRENT_USER = {
  username: 'Teeksss',
  displayName: 'Teeksss',
  role: 'admin',
  email: 'teeksss@example.com'
};

// Geçerli tarih ve saat
export const CURRENT_DATETIME = new Date('2025-05-20 05:58:23');

// Sistem versiyonu
export const SYSTEM_VERSION = 'v1.0.1';

// API endpoint
export const API_BASE_URL = 'http://localhost:8000/api';

// Rol renkleri
export const ROLE_COLORS = {
  admin: 'bg-blue-600',
  analyst: 'bg-green-500',
  powerbi: 'bg-purple-500',
  readonly: 'bg-gray-500'
};

// Durum renkleri
export const STATUS_COLORS = {
  success: 'bg-green-500',
  error: 'bg-red-500',
  rejected: 'bg-orange-500',
  pending: 'bg-yellow-500'
};

// Sorgu tipleri
export const QUERY_TYPES = {
  read: { label: 'SELECT', color: 'bg-green-500' },
  write: { label: 'WRITE', color: 'bg-orange-500' },
  ddl: { label: 'DDL', color: 'bg-red-500' },
  procedure: { label: 'PROC', color: 'bg-purple-500' }
};

// Sunucu listesi
export const SERVERS = [
  { id: 'prod_finance', name: 'Finance Production' },
  { id: 'prod_hr', name: 'HR Production' },
  { id: 'prod_sales', name: 'Sales Production' },
  { id: 'reporting_dw', name: 'Reporting Data Warehouse' },
  { id: 'dev_sandbox', name: 'Development Sandbox' }
];

// Veri maskeleme tipleri
export const MASKING_TYPES = {
  full: { name: 'Tam Maskeleme', description: 'Veri tamamen maskelenir (*****)', color: 'bg-red-500' },
  partial: { name: 'Kısmi Maskeleme', description: 'Verinin bir kısmı gösterilir (12345***)', color: 'bg-amber-500' },
  none: { name: 'Maskeleme Yok', description: 'Veri olduğu gibi gösterilir', color: 'bg-green-500' }
};

// Sorgu önceliği bilgileri 
export const QUERY_TIMEOUTS = {
  admin: 300,    // 5 dakika - Yöneticiler
  analyst: 120,  // 2 dakika - Analistler
  powerbi: 60,   // 1 dakika - PowerBI kullanıcıları
  readonly: 30   // 30 saniye - Salt okunur kullanıcılar
};

// Bildirim türleri
export const NOTIFICATION_TYPES = {
  query_approval: { label: 'Sorgu Onayı', icon: 'shield', color: 'bg-blue-500' },
  query_rejection: { label: 'Sorgu Reddi', icon: 'x-circle', color: 'bg-red-500' },
  whitelist_add: { label: 'Beyaz Liste Ekleme', icon: 'check-circle', color: 'bg-green-500' },
  system: { label: 'Sistem Bildirimi', icon: 'info', color: 'bg-gray-500' },
  timeout: { label: 'Zaman Aşımı', icon: 'clock', color: 'bg-amber-500' }
};

// Sorgu öncelikleri
export const QUERY_PRIORITIES = {
  low: { label: 'Düşük', color: 'bg-blue-500', value: 1 },
  normal: { label: 'Normal', color: 'bg-green-500', value: 2 },
  high: { label: 'Yüksek', color: 'bg-amber-500', value: 3 },
  urgent: { label: 'Acil', color: 'bg-red-500', value: 4 }
};

// Dokümantasyon kategorileri
export const DOC_CATEGORIES = {
  getting_started: { label: 'Başlangıç', icon: 'play' },
  sql_basics: { label: 'SQL Temelleri', icon: 'database' },
  advanced_queries: { label: 'İleri SQL', icon: 'code' },
  admin_guides: { label: 'Yönetici Kılavuzları', icon: 'shield' },
  api_references: { label: 'API Referansları', icon: 'server' },
  faq: { label: 'Sık Sorulan Sorular', icon: 'help-circle' }
};

// Rapor türleri
export const REPORT_TYPES = {
  usage: { label: 'Kullanım Raporu', icon: 'bar-chart' },
  security: { label: 'Güvenlik Raporu', icon: 'shield' },
  performance: { label: 'Performans Raporu', icon: 'activity' },
  audit: { label: 'Denetim Raporu', icon: 'file-text' }
};

// Son güncelleme: 2025-05-20 05:58:23
// Güncelleyen: Teeksss