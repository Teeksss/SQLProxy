import React, { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/use-toast';
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
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import {
  AlertCircle,
  Bell,
  BellOff,
  Check,
  Database,
  Key,
  Mail,
  Save,
  Settings as SettingsIcon,
  User,
  UserCog
} from 'lucide-react';
import { getUserPreferences, updateUserPreferences } from '@/api/users';
import { getNotificationSettings, updateNotificationSettings } from '@/api/notifications';
import { getUserInfo } from '@/utils/auth';

const Settings = () => {
  const [generalSettings, setGeneralSettings] = useState({
    theme: 'system',
    language: 'tr',
    dateFormat: 'DD.MM.YYYY',
    timeFormat: '24h'
  });
  
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    pushNotifications: true,
    notifyOnQueryApproval: true,
    notifyOnQueryRejection: true,
    notifyOnWhitelistChanges: false,
    dailyDigest: false
  });
  
  const [securitySettings, setSecuritySettings] = useState({
    twoFactorEnabled: false,
    sessionTimeout: 180,
    rememberDevices: true
  });
  
  const [userInfo, setUserInfo] = useState(getUserInfo() || {
    username: 'Teeksss',
    displayName: 'Teeksss',
    email: 'teeksss@example.com',
    role: 'admin'
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();
  
  // Fetch user settings
  useEffect(() => {
    const fetchSettings = async () => {
      setIsLoading(true);
      try {
        // Fetch user preferences
        const preferences = await getUserPreferences();
        setGeneralSettings(preferences.general || generalSettings);
        setSecuritySettings(preferences.security || securitySettings);
        
        // Fetch notification settings
        const notifications = await getNotificationSettings();
        setNotificationSettings(notifications || notificationSettings);
      } catch (error) {
        console.error('Error fetching user settings:', error);
        toast({
          title: "Hata",
          description: "Kullanıcı ayarları yüklenirken bir hata oluştu.",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchSettings();
  }, []);
  
  const handleSaveGeneralSettings = async () => {
    setIsSaving(true);
    try {
      await updateUserPreferences({
        general: generalSettings
      });
      
      toast({
        title: "Başarılı",
        description: "Genel ayarlar başarıyla güncellendi.",
        variant: "default",
      });
    } catch (error) {
      console.error('Error saving general settings:', error);
      toast({
        title: "Hata",
        description: "Genel ayarlar kaydedilirken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleSaveNotificationSettings = async () => {
    setIsSaving(true);
    try {
      await updateNotificationSettings(notificationSettings);
      
      toast({
        title: "Başarılı",
        description: "Bildirim ayarları başarıyla güncellendi.",
        variant: "default",
      });
    } catch (error) {
      console.error('Error saving notification settings:', error);
      toast({
        title: "Hata",
        description: "Bildirim ayarları kaydedilirken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleSaveSecuritySettings = async () => {
    setIsSaving(true);
    try {
      await updateUserPreferences({
        security: securitySettings
      });
      
      toast({
        title: "Başarılı",
        description: "Güvenlik ayarları başarıyla güncellendi.",
        variant: "default",
      });
    } catch (error) {
      console.error('Error saving security settings:', error);
      toast({
        title: "Hata",
        description: "Güvenlik ayarları kaydedilirken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Kullanıcı Ayarları</h1>
      </div>
      
      <Tabs defaultValue="general">
        <TabsList className="mb-4">
          <TabsTrigger value="general">
            <SettingsIcon className="h-4 w-4 mr-2" />
            Genel
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="h-4 w-4 mr-2" />
            Bildirimler
          </TabsTrigger>
          <TabsTrigger value="security">
            <Key className="h-4 w-4 mr-2" />
            Güvenlik
          </TabsTrigger>
          <TabsTrigger value="account">
            <User className="h-4 w-4 mr-2" />
            Hesap
          </TabsTrigger>
        </TabsList>
        
        {/* Kullanıcı Paneli */}
        <div className="mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-2xl font-bold">
                  {userInfo.displayName[0].toUpperCase()}
                </div>
                <div>
                  <h2 className="text-xl font-semibold">{userInfo.displayName}</h2>
                  <div className="flex items-center space-x-2 text-gray-500">
                    <Mail className="h-4 w-4" />
                    <span>{userInfo.email}</span>
                  </div>
                  <div className="flex items-center space-x-2 mt-1">
                    <Badge className="bg-blue-500">{userInfo.role}</Badge>
                    <span className="text-xs text-gray-500">Son giriş: {new Date('2025-05-20 05:33:12').toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Genel Ayarlar */}
        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle>Genel Ayarlar</CardTitle>
              <CardDescription>
                Arayüz ve erişim tercihlerinizi yapılandırın
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="theme">Tema</Label>
                <select 
                  id="theme" 
                  className="w-full p-2 border rounded-md"
                  value={generalSettings.theme}
                  onChange={(e) => setGeneralSettings({...generalSettings, theme: e.target.value})}
                  disabled={isLoading}
                >
                  <option value="light">Açık Tema</option>
                  <option value="dark">Koyu Tema</option>
                  <option value="system">Sistem Ayarlarını Kullan</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="language">Dil</Label>
                <select 
                  id="language" 
                  className="w-full p-2 border rounded-md"
                  value={generalSettings.language}
                  onChange={(e) => setGeneralSettings({...generalSettings, language: e.target.value})}
                  disabled={isLoading}
                >
                  <option value="tr">Türkçe</option>
                  <option value="en">English</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="dateFormat">Tarih Formatı</Label>
                <select 
                  id="dateFormat" 
                  className="w-full p-2 border rounded-md"
                  value={generalSettings.dateFormat}
                  onChange={(e) => setGeneralSettings({...generalSettings, dateFormat: e.target.value})}
                  disabled={isLoading}
                >
                  <option value="DD.MM.YYYY">31.12.2025 (DD.MM.YYYY)</option>
                  <option value="MM/DD/YYYY">12/31/2025 (MM/DD/YYYY)</option>
                  <option value="YYYY-MM-DD">2025-12-31 (YYYY-MM-DD)</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="timeFormat">Saat Formatı</Label>
                <select 
                  id="timeFormat" 
                  className="w-full p-2 border rounded-md"
                  value={generalSettings.timeFormat}
                  onChange={(e) => setGeneralSettings({...generalSettings, timeFormat: e.target.value})}
                  disabled={isLoading}
                >
                  <option value="24h">24 Saat (14:30)</option>
                  <option value="12h">12 Saat (2:30 PM)</option>
                </select>
              </div>
            </CardContent>
            <CardFooter className="border-t pt-4 flex justify-between">
              <div className="text-xs text-gray-500">
                Son güncelleme: {new Date('2025-05-20 05:33:12').toLocaleString()} • Kullanıcı: Teeksss
              </div>
              <Button onClick={handleSaveGeneralSettings} disabled={isSaving}>
                {isSaving ? (
                  <>
                    <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Kaydediliyor...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Kaydet
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        {/* Bildirim Ayarları */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Bildirim Ayarları</CardTitle>
              <CardDescription>
                Bildirim tercihlerinizi yapılandırın
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="emailNotifications">E-posta Bildirimleri</Label>
                    <p className="text-sm text-gray-500">
                      Önemli sistem olayları için e-posta bildirimleri alın
                    </p>
                  </div>
                  <Switch 
                    id="emailNotifications" 
                    checked={notificationSettings.emailNotifications}
                    onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, emailNotifications: checked})}
                    disabled={isLoading}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="pushNotifications">Anında Bildirimler</Label>
                    <p className="text-sm text-gray-500">
                      Tarayıcı bildirimleri ile anında haberdar olun
                    </p>
                  </div>
                  <Switch 
                    id="pushNotifications" 
                    checked={notificationSettings.pushNotifications}
                    onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, pushNotifications: checked})}
                    disabled={isLoading}
                  />
                </div>
                
                <div className="border-t pt-6 space-y-4">
                  <h3 className="font-medium">Bildirim Alınacak Olaylar</h3>
                  
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="notifyOnQueryApproval">Sorgu Onayları</Label>
                      <p className="text-sm text-gray-500">
                        Sorgularınız onaylandığında bildirim alın
                      </p>
                    </div>
                    <Switch 
                      id="notifyOnQueryApproval" 
                      checked={notificationSettings.notifyOnQueryApproval}
                      onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, notifyOnQueryApproval: checked})}
                      disabled={isLoading}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="notifyOnQueryRejection">Sorgu Redleri</Label>
                      <p className="text-sm text-gray-500">
                        Sorgularınız reddedildiğinde bildirim alın
                      </p>
                    </div>
                    <Switch 
                      id="notifyOnQueryRejection" 
                      checked={notificationSettings.notifyOnQueryRejection}
                      onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, notifyOnQueryRejection: checked})}
                      disabled={isLoading}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="notifyOnWhitelistChanges">Beyaz Liste Değişiklikleri</Label>
                      <p className="text-sm text-gray-500">
                        Beyaz liste değişikliklerinde bildirim alın
                      </p>
                    </div>
                    <Switch 
                      id="notifyOnWhitelistChanges" 
                      checked={notificationSettings.notifyOnWhitelistChanges}
                      onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, notifyOnWhitelistChanges: checked})}
                      disabled={isLoading}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="dailyDigest">Günlük Özet</Label>
                      <p className="text-sm text-gray-500">
                        Sorgu istatistiklerinizin günlük özetini alın
                      </p>
                    </div>
                    <Switch 
                      id="dailyDigest" 
                      checked={notificationSettings.dailyDigest}
                      onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, dailyDigest: checked})}
                      disabled={isLoading}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="border-t pt-4 flex justify-between">
              <div className="text-xs text-gray-500">
                Son güncelleme: {new Date('2025-05-20 05:33:12').toLocaleString()} • Kullanıcı: Teeksss
              </div>
              <Button onClick={handleSaveNotificationSettings} disabled={isSaving}>
                {isSaving ? (
                  <>
                    <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Kaydediliyor...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Kaydet
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        {/* Güvenlik Ayarları */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle>Güvenlik Ayarları</CardTitle>
              <CardDescription>
                Hesap güvenlik ayarlarınızı yapılandırın
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="twoFactorEnabled">İki Faktörlü Kimlik Doğrulama</Label>
                    <p className="text-sm text-gray-500">
                      Hesabınıza ekstra güvenlik katmanı ekleyin
                    </p>
                  </div>
                  <Switch 
                    id="twoFactorEnabled" 
                    checked={securitySettings.twoFactorEnabled}
                    onCheckedChange={(checked) => setSecuritySettings({...securitySettings, twoFactorEnabled: checked})}
                    disabled={isLoading}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="sessionTimeout">Oturum Zaman Aşımı (dakika)</Label>
                  <Input 
                    id="sessionTimeout" 
                    type="number"
                    min="15"
                    max="1440"
                    value={securitySettings.sessionTimeout}
                    onChange={(e) => setSecuritySettings({...securitySettings, sessionTimeout: parseInt(e.target.value) || 180})}
                    disabled={isLoading}
                  />
                  <p className="text-xs text-gray-500">
                    Hareketsizlik durumunda otomatik oturum kapatma süresi
                  </p>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="rememberDevices">Cihazları Hatırla</Label>
                    <p className="text-sm text-gray-500">
                      Güvenilir cihazlarda daha uzun oturum süresi
                    </p>
                  </div>
                  <Switch 
                    id="rememberDevices" 
                    checked={securitySettings.rememberDevices}
                    onCheckedChange={(checked) => setSecuritySettings({...securitySettings, rememberDevices: checked})}
                    disabled={isLoading}
                  />
                </div>
                
                <div className="border-t pt-6">
                  <Button variant="outline" className="w-full">
                    <Key className="h-4 w-4 mr-2" />
                    Şifre Değiştir
                  </Button>
                </div>
              </div>
            </CardContent>
            <CardFooter className="border-t pt-4 flex justify-between">
              <div className="text-xs text-gray-500">
                Son güncelleme: {new Date('2025-05-20 05:33:12').toLocaleString()} • Kullanıcı: Teeksss
              </div>
              <Button onClick={handleSaveSecuritySettings} disabled={isSaving}>
                {isSaving ? (
                  <>
                    <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Kaydediliyor...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Kaydet
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        {/* Hesap Ayarları */}
        <TabsContent value="account">
          <Card>
            <CardHeader>
              <CardTitle>Hesap Bilgileri</CardTitle>
              <CardDescription>
                LDAP hesap bilgileriniz
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="bg-blue-50 p-4 rounded-md">
                  <div className="flex">
                    <Info className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-blue-800">
                        LDAP Entegrasyonu
                      </p>
                      <p className="text-sm text-blue-700 mt-1">
                        Hesap bilgileriniz şirket LDAP dizininden alınmaktadır. Değişiklik için IT departmanına başvurun.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Kullanıcı Adı</Label>
                    <Input value={userInfo.username} disabled />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Rol</Label>
                    <Input value={userInfo.role} disabled />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Tam Ad</Label>
                    <Input value={userInfo.displayName} disabled />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>E-posta</Label>
                    <Input value={userInfo.email} disabled />
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <p className="text-sm text-gray-500">
                    <strong>Son giriş:</strong> {new Date('2025-05-20 05:33:12').toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-500">
                    <strong>Üyelik:</strong> 01.01.2023 tarihinden beri
                  </p>
                </div>
              </div>
            </CardContent>
            <CardFooter className="border-t pt-4 flex justify-between">
              <div className="text-xs text-gray-500">
                Son güncelleme: {new Date('2025-05-20 05:33:12').toLocaleString()} • Kullanıcı: Teeksss
              </div>
              <Button variant="outline" disabled>
                <UserCog className="h-4 w-4 mr-2" />
                IT'ye Değişiklik Talebi Gönder
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Son güncelleme: 2025-05-20 05:33:12
// Güncelleyen: Teeksss

export default Settings;