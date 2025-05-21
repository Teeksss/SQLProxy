import React, { useState } from 'react';
import { 
  Card, 
  CardContent,
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  AlertTriangle,
  BookOpen,
  ChevronRight,
  Database,
  FileText,
  HelpCircle,
  Info,
  MessageSquare,
  Search,
  Shield,
  Terminal,
  ThumbsUp,
  Timer,
  Video
} from 'lucide-react';
import SQLHighlight from '@/components/SQLHighlight';

const Help = () => {
  const [searchTerm, setSearchTerm] = useState('');
  
  // Örnek yardım içeriği kategorileri
  const categories = [
    {
      title: 'Başlangıç',
      icon: <Info className="h-5 w-5" />,
      questions: [
        {
          question: 'SQL Proxy nedir?',
          answer: (
            <div className="space-y-2">
              <p>SQL Proxy, kurumsal veri erişim yönetimi ve SQL sorgu güvenliği çözümüdür. Bu sistem, kurum içindeki veritabanlarına merkezi erişim kontrolü, sorgu onaylama, denetim logları ve rol tabanlı erişim kontrolleri sağlar.</p>
              
              <p>Temel özellikleri:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>LDAP entegrasyonu ile kurumsal kimlik doğrulama</li>
                <li>Rol tabanlı erişim kontrolü</li>
                <li>Sorgu onaylama ve beyaz liste yönetimi</li>
                <li>Denetim logları (audit trail)</li>
                <li>Veri maskeleme</li>
                <li>Sorgu zaman aşımı yönetimi</li>
              </ul>
            </div>
          )
        },
        {
          question: 'Nasıl başlarım?',
          answer: (
            <div className="space-y-2">
              <p>SQL Proxy'yi kullanmaya başlamak için:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Kurumsal (LDAP) kimlik bilgilerinizle giriş yapın</li>
                <li>Dashboard üzerinden SQL sorgu paneline erişin</li>
                <li>Sorgulamak istediğiniz sunucuyu seçin</li>
                <li>SQL sorgunuzu yazın ve "Çalıştır" butonuna tıklayın</li>
              </ol>
              
              <div className="bg-blue-50 p-3 rounded-md mt-2">
                <div className="flex">
                  <Info className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0" />
                  <p className="text-sm text-blue-700">
                    Bazı sorgular ilk kez çalıştırıldığında admin onayı gerektirebilir. Onay sonrası, aynı sorgu otomatik olarak çalışacaktır.
                  </p>
                </div>
              </div>
            </div>
          )
        },
        {
          question: 'Hangi rollar ve izinler mevcut?',
          answer: (
            <div className="space-y-3">
              <p>SQL Proxy'de kullanıcılar farklı roller üzerinden yetkilendirilir:</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="border rounded-md p-3">
                  <div className="flex items-center">
                    <Badge className="bg-blue-600 mr-2">admin</Badge>
                    <h4 className="font-medium">Yönetici</h4>
                  </div>
                  <p className="text-sm mt-1">Tüm özelliklere erişim, sorgular için otomatik onay, sistem ayarlarını yapılandırma</p>
                </div>
                
                <div className="border rounded-md p-3">
                  <div className="flex items-center">
                    <Badge className="bg-green-500 mr-2">analyst</Badge>
                    <h4 className="font-medium">Analist</h4>
                  </div>
                  <p className="text-sm mt-1">Veri analizi için özel izinler, kısmen yazma işlemleri</p>
                </div>
                
                <div className="border rounded-md p-3">
                  <div className="flex items-center">
                    <Badge className="bg-purple-500 mr-2">powerbi</Badge>
                    <h4 className="font-medium">PowerBI</h4>
                  </div>
                  <p className="text-sm mt-1">PowerBI entegrasyonu için özel izinler, otomatik sorgu çalıştırma</p>
                </div>
                
                <div className="border rounded-md p-3">
                  <div className="flex items-center">
                    <Badge className="bg-gray-500 mr-2">readonly</Badge>
                    <h4 className="font-medium">Salt Okunur</h4>
                  </div>
                  <p className="text-sm mt-1">Sadece SELECT sorgularını çalıştırma, sınırlı veri erişimi</p>
                </div>
              </div>
              
              <p className="text-sm text-gray-600">
                Rolünüz ve izinleriniz şirket LDAP dizini tarafından belirlenir. Değişiklik için IT departmanına başvurun.
              </p>
            </div>
          )
        }
      ]
    },
    {
      title: 'Sorgu Çalıştırma',
      icon: <Terminal className="h-5 w-5" />,
      questions: [
        {
          question: 'Hangi SQL sorguları çalıştırabilirim?',
          answer: (
            <div className="space-y-3">
              <p>Çalıştırabileceğiniz SQL sorguları rolünüze ve erişim izinlerinize bağlıdır:</p>
              
              <div className="space-y-2">
                <h4 className="font-medium">Genel Kurallar:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li><span className="font-medium">Admin:</span> Tüm SQL sorgu tiplerini çalıştırabilir (SELECT, INSERT, UPDATE, DELETE, CREATE, vb.)</li>
                  <li><span className="font-medium">Analyst:</span> SELECT sorguları ve bazı INSERT/UPDATE işlemleri (tabloya göre değişir)</li>
                  <li><span className="font-medium">PowerBI:</span> Önceden onaylanmış SELECT sorguları</li>
                  <li><span className="font-medium">Readonly:</span> Sadece SELECT sorguları</li>
                </ul>
              </div>
              
              <div className="bg-yellow-50 p-3 rounded-md">
                <div className="flex">
                  <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800">
                      Güvenlik Kısıtlamaları
                    </p>
                    <p className="text-sm text-yellow-700 mt-1">
                      WHERE koşulu olmayan veya çok fazla veri döndürebilecek sorgular sistem tarafından kısıtlanabilir. Sorgularınızı optimize edin ve WHERE koşulları ekleyin.
                    </p>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">Örnek Sorgu:</h4>
                <SQLHighlight code={`SELECT customer_id, first_name, last_name, email
FROM customers
WHERE region = 'Europe' 
  AND registration_date > '2025-01-01'
ORDER BY last_name
LIMIT 100;`} />
              </div>
            </div>
          )
        },
        {
          question: 'Sorgu onayı süreci nasıl işler?',
          answer: (
            <div className="space-y-3">
              <p>Beyaz listede olmayan sorgular ilk çalıştırıldığında onay sürecine girer:</p>
              
              <ol className="list-decimal list-inside space-y-1">
                <li>Sorgunuz sistem tarafından analiz edilir ve risk seviyesi belirlenir</li>
                <li>Admin kullanıcılarına onay için bildirim gönderilir</li>
                <li>Admin kullanıcılarından biri sorguyu inceleyip onaylayabilir veya reddedebilir</li>
                <li>Onay durumu size bildirilir (e-posta veya uygulama içi bildirim)</li>
                <li>Onaylanan sorgular beyaz listeye eklenebilir, böylece tekrar onay gerekmez</li>
              </ol>
              
              <div className="bg-blue-50 p-3 rounded-md">
                <div className="flex">
                  <Info className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-blue-800">İpucu</p>
                    <p className="text-sm text-blue-700">
                      Onay sürecini hızlandırmak için, sorgularınıza açıklayıcı bir yorum satırı ekleyin. Örneğin:
                      <code className="block bg-blue-100 p-2 rounded-sm mt-1 text-xs">
                        /* Avrupa'daki son 30 günlük yeni müşteriler - Aylık raporlama için */
                      </code>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )
        },
        {
          question: 'Zaman aşımı limitleri nelerdir?',
          answer: (
            <div className="space-y-3">
              <p>Uzun süren sorgular sistem performansını etkileyebilir. Bu nedenle, her rol için farklı zaman aşımı limitleri tanımlanmıştır:</p>
              
              <ul className="list-disc list-inside space-y-1">
                <li><span className="font-medium">Admin:</span> 5 dakika (300 saniye)</li>
                <li><span className="font-medium">Analyst:</span> 2 dakika (120 saniye)</li>
                <li><span className="font-medium">PowerBI:</span> 1 dakika (60 saniye)</li>
                <li><span className="font-medium">Readonly:</span> 30 saniye</li>
              </ul>
              
              <p>Sorgunuz bu süreleri aşarsa otomatik olarak iptal edilir ve hata mesajı alırsınız.</p>
              
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="flex">
                  <Timer className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium">Sorguları Optimize Etme</p>
                    <ul className="list-disc list-inside text-sm text-gray-600 mt-1 space-y-1">
                      <li>Sorgularınızda WHERE koşulları kullanın</li>
                      <li>LIMIT ile dönen satır sayısını sınırlayın</li>
                      <li>Sadece ihtiyacınız olan kolonları seçin (SELECT * kullanmaktan kaçının)</li>
                      <li>JOIN işlemlerini optimize edin</li>
                      <li>Büyük veri setleri için parçalı sorgular kullanın</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )
        }
      ]
    },
    {
      title: 'Veri Güvenliği',
      icon: <Shield className="h-5 w-5" />,
      questions: [
        {
          question: 'Veri maskeleme nasıl çalışır?',
          answer: (
            <div className="space-y-3">
              <p>Veri maskeleme, hassas verilerin (TCKN, kredi kartı, e-posta, vb.) sorgu sonuçlarında otomatik olarak maskelenmesini sağlar:</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="border rounded-md p-3">
                  <h4 className="font-medium">Tam Maskeleme</h4>
                  <p className="text-sm mt-1">Veri tamamen gizlenir</p>
                  <p className="text-sm italic mt-1">Örnek: <code>*****</code></p>
                </div>
                
                <div className="border rounded-md p-3">
                  <h4 className="font-medium">Kısmi Maskeleme</h4>
                  <p className="text-sm mt-1">Verinin bir kısmı gösterilir</p>
                  <p className="text-sm italic mt-1">Örnek: <code>12345******</code> veya <code>em**@example.com</code></p>
                </div>
              </div>
              
              <p>Maskeleme kuralları şu faktörlere göre belirlenir:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Kolon adları (örn: "tckn", "credit_card", "email", vb.)</li>
                <li>Tablo adları (örn: "customers", "employees")</li>
                <li>Kullanıcı rolü (admin kullanıcılar genellikle maskelenmemiş verileri görebilir)</li>
              </ul>
              
              <div className="bg-blue-50 p-3 rounded-md">
                <div className="flex">
                  <Info className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0" />
                  <p className="text-sm text-blue-700">
                    Maskelenmiş veriler sorgu sonuçlarında özel bir stil ile vurgulanır, böylece hangi verilerin maskelendiğini kolayca görebilirsiniz.
                  </p>
                </div>
              </div>
            </div>
          )
        },
        {
          question: 'Denetim kayıtları (audit log) neleri içerir?',
          answer: (
            <div className="space-y-3">
              <p>Sistem, tüm veritabanı erişimlerini ve sorguları kayıt altına alır. Bu kayıtlar şunları içerir:</p>
              
              <ul className="list-disc list-inside space-y-1">
                <li>Kullanıcı adı ve rolü</li>
                <li>İstemci IP adresi</li>
                <li>Çalıştırılan SQL sorgusu</li>
                <li>Hedef sunucu ve veritabanı</li>
                <li>Çalıştırma zamanı ve süresi</li>
                <li>Etkilenen satır sayısı</li>
                <li>Varsa hata mesajları</li>
                <li>Beyaz liste referansı (eğer mevcutsa)</li>
              </ul>
              
              <p>Denetim kayıtları şu amaçlarla kullanılır:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Güvenlik inceleme ve sorun giderme</li>
                <li>Veri erişimi takibi</li>
                <li>Performans izleme</li>
                <li>Düzenleme/mevzuat (compliance) uyumluluğu</li>
              </ul>
              
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="flex">
                  <FileText className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" />
                  <p className="text-sm text-gray-700">
                    Admin yetkisine sahip kullanıcılar, "Audit Loglar" sayfasından tüm denetim kayıtlarını görüntüleyebilir ve filtreleyebilir. Standart kullanıcılar ise sadece kendi sorgularının geçmişini "Sorgu Geçmişi" sayfasından görüntüleyebilir.
                  </p>
                </div>
              </div>
            </div>
          )
        }
      ]
    },
    {
      title: 'PowerBI Entegrasyonu',
      icon: <Database className="h-5 w-5" />,
      questions: [
        {
          question: 'PowerBI için SQL Proxy nasıl kullanılır?',
          answer: (
            <div className="space-y-3">
              <p>PowerBI ile SQL Proxy entegrasyonu, güvenli ve kontrollü veri erişimi sağlar:</p>
              
              <ol className="list-decimal list-inside space-y-2">
                <li>
                  <span className="font-medium">PowerBI Kullanıcısı Tanımlama:</span>
                  <p className="ml-6 text-sm">PowerBI servis hesabınız için özel bir kullanıcı tanımlanmalıdır (IT departmanı tarafından yapılır)</p>
                </li>
                
                <li>
                  <span className="font-medium">Onaylı Sorgular Oluşturma:</span>
                  <p className="ml-6 text-sm">SQL Proxy üzerinden raporlarınız için gerekli sorguları oluşturun ve onaylatın</p>
                </li>
                
                <li>
                  <span className="font-medium">API URL'leri Alma:</span>
                  <p className="ml-6 text-sm">Her onaylı sorgu için özel bir API endpoint'i oluşturulur (örn: <code>/api/powerbi/query/123</code>)</p>
                </li>
                
                <li>
                  <span className="font-medium">PowerBI'da Veri Kaynağı Ekleme:</span>
                  <p className="ml-6 text-sm">PowerBI Desktop'ta "Web" veri kaynağı kullanarak API URL'lerine bağlanın</p>
                </li>
              </ol>
              
              <div className="bg-blue-50 p-3 rounded-md">
                <div className="flex">
                  <Info className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-blue-800">API Kimlik Doğrulama</p>
                    <p className="text-sm text-blue-700 mt-1">
                      PowerBI entegrasyonu için OAuth2 token kimlik doğrulaması kullanılır. Oluşturulan API anahtarlarının güvenliğini sağlamak önemlidir. Anahtarlar düzenli olarak yenilenmelidir.
                    </p>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-1">Örnek PowerBI Sorgu URL'i</h4>
                <code className="block bg-gray-100 p-2 rounded-sm text-xs">
                  https://sql-proxy.sirketiniz.com/api/powerbi/query/456?server=reporting_dw
                </code>
              </div>
              
              <p className="text-sm">
                Detaylı talimatlar için IT departmanımızdan özel destek alabilirsiniz.
              </p>
            </div>
          )
        }
      ]
    }
  ];
  
  // Arama terimiyle filtreleme
  const filteredCategories = searchTerm
    ? categories.map(category => ({
        ...category,
        questions: category.questions.filter(q => 
          q.question.toLowerCase().includes(searchTerm.toLowerCase()) || 
          (typeof q.answer === 'string' && q.answer.toLowerCase().includes(searchTerm.toLowerCase()))
        )
      })).filter(category => category.questions.length > 0)
    : categories;
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Yardım ve Destek</h1>
      </div>
      
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center">
            <HelpCircle className="h-5 w-5 mr-2" />
            SQL Proxy Yardım Merkezi
          </CardTitle>
          <CardDescription>
            SQL Proxy sistemini nasıl kullanacağınıza dair bilgiler
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4 flex items-start">
              <Video className="h-6 w-6 text-blue-500 mr-3 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-medium text-blue-700">Eğitim Videoları</h3>
                <p className="text-sm text-blue-600 mt-1">
                  Temel kullanım ve ileri konular hakkında eğitim videoları
                </p>
                <Button size="sm" variant="link" className="px-0 mt-1 text-blue-600">
                  Videoları İzle <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
            
            <div className="bg-purple-50 rounded-lg p-4 flex items-start">
              <BookOpen className="h-6 w-6 text-purple-500 mr-3 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-medium text-purple-700">Dokümantasyon</h3>
                <p className="text-sm text-purple-600 mt-1">
                  Detaylı sistem dokümantasyonu ve API referansı
                </p>
                <Button size="sm" variant="link" className="px-0 mt-1 text-purple-600">
                  Dökümanlara Git <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
            
            <div className="bg-amber-50 rounded-lg p-4 flex items-start">
              <MessageSquare className="h-6 w-6 text-amber-500 mr-3 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-medium text-amber-700">Soru Sor</h3>
                <p className="text-sm text-amber-600 mt-1">
                  SQL Proxy ekibine doğrudan soru sorabilirsiniz
                </p>
                <Button size="sm" variant="link" className="px-0 mt-1 text-amber-600">
                  Yeni Soru Sor <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
            
            <div className="bg-green-50 rounded-lg p-4 flex items-start">
              <ThumbsUp className="h-6 w-6 text-green-500 mr-3 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-medium text-green-700">Öneriler</h3>
                <p className="text-sm text-green-600 mt-1">
                  SQL Proxy için özellik istekleri ve geliştirme önerileri
                </p>
                <Button size="sm" variant="link" className="px-0 mt-1 text-green-600">
                  Öneri Gönder <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          </div>
          
          <div className="relative mb-6">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Soru veya anahtar kelime ara..."
              className="pl-9"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          {filteredCategories.length === 0 ? (
            <div className="text-center py-12">
              <HelpCircle className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">Arama kriterine uygun sonuç bulunamadı.</p>
              <Button variant="outline" className="mt-4" onClick={() => setSearchTerm('')}>
                Aramayı Temizle
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              {filteredCategories.map((category, index) => (
                <div key={index}>
                  <h2 className="text-lg font-medium flex items-center mb-3">
                    {category.icon}
                    <span className="ml-2">{category.title}</span>
                  </h2>
                  
                  <Accordion type="single" collapsible className="mb-4">
                    {category.questions.map((item, qIndex) => (
                      <AccordionItem key={qIndex} value={`item-${index}-${qIndex}`}>
                        <AccordionTrigger className="hover:no-underline">
                          <span className="text-left">{item.question}</span>
                        </AccordionTrigger>
                        <AccordionContent>
                          <div className="pt-2 pb-1 text-gray-700">
                            {item.answer}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </div>
              ))}
            </div>
          )}
        </CardContent>
        <CardFooter className="border-t pt-4 flex justify-between">
          <div className="text-xs text-gray-500">
            Son güncelleme: {new Date('2025-05-20 05:33:12').toLocaleString()} • Kullanıcı: Teeksss
          </div>
          <div className="flex items-center text-sm text-gray-500">
            <HelpCircle className="h-4 w-4 mr-1.5" />
            <span>Daha fazla yardım için IT departmanıyla iletişime geçin</span>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

// Son güncelleme: 2025-05-20 05:33:12
// Güncelleyen: Teeksss

export default Help;