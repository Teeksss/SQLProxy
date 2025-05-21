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
import { 
  Table, 
  TableBody, 
  TableCaption, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  AlertTriangle, 
  Clock, 
  DatabaseZap,
  Eye, 
  HourglassIcon,
  Pencil, 
  Plus, 
  RefreshCw, 
  Save, 
  Search, 
  Shield, 
  Trash2, 
  Users,
  User
} from 'lucide-react';
import { 
  getTimeoutSettings, 
  updateRoleTimeout, 
  createCustomTimeout, 
  updateCustomTimeout, 
  deleteCustomTimeout,
  testQuery
} from '@/api/timeout';

// Custom timeout form
const TimeoutForm = ({ initialData = null, onSubmit, onCancel, isRole = false }) => {
  const [formData, setFormData] = useState({
    type: 'user',
    identifier: '',
    timeout_seconds: 60,
    description: '',
    is_active: true
  });
  
  const { toast } = useToast();
  
  useEffect(() => {
    if (initialData) {
      setFormData({
        ...initialData,
        type: initialData.type || 'user'
      });
    } else if (isRole) {
      setFormData({
        ...formData,
        type: 'role'
      });
    }
  }, [initialData, isRole]);
  
  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.identifier) {
      toast({
        title: "Hata",
        description: "Lütfen bir tanımlayıcı girin",
        variant: "destructive",
      });
      return;
    }
    
    if (!formData.timeout_seconds || formData.timeout_seconds <= 0) {
      toast({
        title: "Hata",
        description: "Zaman aşımı süresi pozitif bir sayı olmalıdır",
        variant: "destructive",
      });
      return;
    }
    
    onSubmit(formData);
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4 py-2">
        {!isRole && (
          <div className="space-y-2">
            <Label htmlFor="type">Kural Tipi</Label>
            <Select 
              value={formData.type}
              onValueChange={(value) => handleChange('type', value)}
              disabled={!!initialData}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user">
                  <div className="flex items-center">
                    <User className="h-4 w-4 mr-2" />
                    <span>Kullanıcı</span>
                  </div>
                </SelectItem>
                <SelectItem value="group">
                  <div className="flex items-center">
                    <Users className="h-4 w-4 mr-2" />
                    <span>Grup</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
        
        <div className="space-y-2">
          <Label htmlFor="identifier">
            {isRole ? 'Rol' : formData.type === 'user' ? 'Kullanıcı Adı' : 'Grup Adı'}
          </Label>
          <Input 
            id="identifier"
            value={formData.identifier}
            onChange={(e) => handleChange('identifier', e.target.value)}
            placeholder={
              isRole ? 'Rol adı' : 
              formData.type === 'user' ? 'Kullanıcı adı girin' : 
              'Grup adı girin'
            }
            disabled={!!initialData && isRole}
            required
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="timeout_seconds">Zaman Aşımı (saniye)</Label>
          <Input 
            id="timeout_seconds"
            type="number"
            value={formData.timeout_seconds}
            onChange={(e) => handleChange('timeout_seconds', parseInt(e.target.value) || 0)}
            min="1"
            max="3600"
            required
          />
          <div className="text-xs text-gray-500 flex justify-between">
            <span>Minimum: 1 saniye</span>
            <span>Maksimum: 3600 saniye (1 saat)</span>
          </div>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="description">Açıklama</Label>
          <Input 
            id="description"
            value={formData.description || ''}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Bu zaman aşımı ayarı için açıklama girin (opsiyonel)"
          />
        </div>
        
        {/* Conversion to human-readable time */}
        <div className="bg-blue-50 p-3 rounded-md">
          <div className="flex items-start">
            <HourglassIcon className="h-5 w-5 text-blue-500 mr-2 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-800">
                Zaman Aşımı: {formData.timeout_seconds} saniye
              </p>
              <p className="text-xs text-blue-700 mt-1">
                {Math.floor(formData.timeout_seconds / 60)} dakika {formData.timeout_seconds % 60} saniye
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <DialogFooter className="mt-6">
        <Button type="button" variant="outline" onClick={onCancel}>
          İptal
        </Button>
        <Button type="submit">
          {initialData ? 'Güncelle' : 'Oluştur'}
        </Button>
      </DialogFooter>
    </form>
  );
};

const TimeoutSettings = () => {
  const [roleSettings, setRoleSettings] = useState([]);
  const [customSettings, setCustomSettings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRoleDialogOpen, setIsRoleDialogOpen] = useState(false);
  const [isCustomDialogOpen, setIsCustomDialogOpen] = useState(false);
  const [currentSetting, setCurrentSetting] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const { toast } = useToast();
  
  const fetchSettings = async () => {
    setIsLoading(true);
    try {
      const data = await getTimeoutSettings();
      setRoleSettings(data.role_settings);
      setCustomSettings(data.custom_settings);
    } catch (error) {
      console.error('Error fetching timeout settings:', error);
      toast({
        title: "Hata",
        description: "Zaman aşımı ayarları yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
      
      // Mock data
      setRoleSettings([
        { id: 1, role: 'admin', timeout_seconds: 300, description: 'Yöneticiler için zaman aşımı', is_system: true },
        { id: 2, role: 'analyst', timeout_seconds: 120, description: 'Analistler için zaman aşımı', is_system: true },
        { id: 3, role: 'powerbi', timeout_seconds: 60, description: 'PowerBI için zaman aşımı', is_system: true },
        { id: 4, role: 'readonly', timeout_seconds: 30, description: 'Salt okunur kullanıcılar için zaman aşımı', is_system: true }
      ]);
      
      setCustomSettings([
        { id: 101, type: 'user', identifier: 'data_scientist', timeout_seconds: 180, description: 'Veri bilimcisi için özel süre', is_active: true, created_at: '2025-05-15T10:30:00Z' },
        { id: 102, type: 'user', identifier: 'Teeksss', timeout_seconds: 600, description: 'Yazılım geliştirici için uzun süre', is_active: true, created_at: '2025-05-20T05:19:26Z' },
        { id: 103, type: 'group', identifier: 'finance_team', timeout_seconds: 240, description: 'Finans ekibi için özel süre', is_active: true, created_at: '2025-05-18T14:25:00Z' },
        { id: 104, type: 'user', identifier: 'test_user', timeout_seconds: 15, description: 'Test amaçlı kısa süre', is_active: false, created_at: '2025-05-16T09:45:00Z' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchSettings();
  }, []);
  
  const handleEditRole = (role) => {
    setCurrentSetting(role);
    setIsRoleDialogOpen(true);
  };
  
  const handleSubmitRoleTimeout = async (formData) => {
    try {
      await updateRoleTimeout(formData.role, formData.timeout_seconds);
      
      toast({
        title: "Başarılı",
        description: `${formData.role} rolü için zaman aşımı süresi güncellendi.`,
        variant: "default",
      });
      
      setIsRoleDialogOpen(false);
      fetchSettings();
    } catch (error) {
      console.error('Error updating role timeout:', error);
      toast({
        title: "Hata",
        description: "Rol zaman aşımı süresi güncellenirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleAddCustom = () => {
    setCurrentSetting(null);
    setIsCustomDialogOpen(true);
  };
  
  const handleEditCustom = (setting) => {
    setCurrentSetting(setting);
    setIsCustomDialogOpen(true);
  };
  
  const handleDeleteCustom = async (settingId) => {
    if (!confirm('Bu özel zaman aşımı ayarını silmek istediğinizden emin misiniz?')) {
      return;
    }
    
    try {
      await deleteCustomTimeout(settingId);
      
      toast({
        title: "Başarılı",
        description: "Özel zaman aşımı ayarı başarıyla silindi.",
        variant: "default",
      });
      
      fetchSettings();
    } catch (error) {
      console.error('Error deleting custom timeout:', error);
      toast({
        title: "Hata",
        description: "Özel zaman aşımı ayarı silinirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleSubmitCustomTimeout = async (formData) => {
    try {
      if (currentSetting) {
        // Update existing
        await updateCustomTimeout(currentSetting.id, formData);
        toast({
          title: "Başarılı",
          description: "Özel zaman aşımı ayarı güncellendi.",
          variant: "default",
        });
      } else {
        // Create new
        await createCustomTimeout(formData);
        toast({
          title: "Başarılı",
          description: "Yeni özel zaman aşımı ayarı oluşturuldu.",
          variant: "default",
        });
      }
      
      setIsCustomDialogOpen(false);
      fetchSettings();
    } catch (error) {
      console.error('Error saving custom timeout:', error);
      toast({
        title: "Hata",
        description: "Özel zaman aşımı ayarı kaydedilirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  // Filter custom settings based on search term
  const filteredCustomSettings = customSettings.filter(setting => 
    setting.identifier.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (setting.description && setting.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Sorgu Zaman Aşımı Ayarları</h1>
        <Button onClick={handleAddCustom}>
          <Plus className="h-4 w-4 mr-2" />
          Yeni Özel Zaman Aşımı
        </Button>
      </div>
      
      {/* Role Timeout Settings */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="h-5 w-5 mr-2" />
            Rol Bazlı Zaman Aşımı Süreleri
          </CardTitle>
          <CardDescription>
            Farklı kullanıcı rolleri için varsayılan sorgu zaman aşımı sürelerini yapılandırın
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm mb-4">
            <p>
              <strong>Sorgu zaman aşımı</strong>, bir SQL sorgusunun maksimum ne kadar süre çalışabileceğini belirler. 
              Bu süre aşıldığında, sorgu otomatik olarak iptal edilir. Uzun süren sorgular sistem performansını etkileyebilir.
            </p>
          </div>
          
          {isLoading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rol</TableHead>
                  <TableHead>Zaman Aşımı</TableHead>
                  <TableHead>Açıklama</TableHead>
                  <TableHead className="text-right">İşlemler</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roleSettings.map(role => (
                  <TableRow key={role.id}>
                    <TableCell>
                      <div className="flex items-center">
                        <Badge className="bg-blue-500 mr-2">{role.role}</Badge>
                        {role.is_system && (
                          <span className="text-xs text-gray-500">(Sistem)</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1.5">
                        <Clock className="h-4 w-4 text-gray-500" />
                        <span>{role.timeout_seconds} saniye</span>
                        <span className="text-xs text-gray-500">
                          ({Math.floor(role.timeout_seconds / 60)} dk {role.timeout_seconds % 60} sn)
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>{role.description}</TableCell>
                    <TableCell className="text-right">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleEditRole(role)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      
      {/* Custom Timeout Settings */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="flex items-center">
                <Clock className="h-5 w-5 mr-2" />
                Özel Zaman Aşımı Ayarları
              </CardTitle>
              <CardDescription>
                Belirli kullanıcılar veya gruplar için özel sorgu zaman aşımı süreleri tanımlayın
              </CardDescription>
            </div>
            <div className="flex space-x-2">
              <div className="relative w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Kullanıcı veya grup ara..."
                  className="pl-9"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <Button variant="outline" size="icon" onClick={fetchSettings}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            </div>
          ) : filteredCustomSettings.length === 0 ? (
            <div className="text-center py-8">
              <HourglassIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">
                {searchTerm ? "Arama kriterine uygun özel zaman aşımı ayarı bulunamadı." : "Henüz tanımlanmış özel zaman aşımı ayarı yok."}
              </p>
              <Button variant="outline" className="mt-4" onClick={handleAddCustom}>
                <Plus className="h-4 w-4 mr-2" />
                Yeni Özel Zaman Aşımı Oluştur
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tanımlayıcı</TableHead>
                  <TableHead>Tip</TableHead>
                  <TableHead>Zaman Aşımı</TableHead>
                  <TableHead>Açıklama</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlemler</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCustomSettings.map(setting => (
                  <TableRow key={setting.id}>
                    <TableCell className="font-medium">
                      {setting.identifier}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {setting.type === 'user' ? 'Kullanıcı' : 'Grup'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1.5">
                        <Clock className="h-4 w-4 text-gray-500" />
                        <span>{setting.timeout_seconds} saniye</span>
                        <span className="text-xs text-gray-500">
                          ({Math.floor(setting.timeout_seconds / 60)} dk {setting.timeout_seconds % 60} sn)
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {setting.description || '-'}
                    </TableCell>
                    <TableCell>
                      {setting.is_active ? (
                        <Badge className="bg-green-500">Aktif</Badge>
                      ) : (
                        <Badge variant="outline">Pasif</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end space-x-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleEditCustom(setting)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleDeleteCustom(setting.id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
        <CardFooter className="border-t pt-4 text-xs text-gray-500">
          Son güncelleme: {new Date('2025-05-20 05:19:26').toLocaleString()} • Kullanıcı: Teeksss
        </CardFooter>
      </Card>
      
      {/* Edit Role Timeout Dialog */}
      <Dialog open={isRoleDialogOpen} onOpenChange={setIsRoleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rol Zaman Aşımı Süresi Düzenle</DialogTitle>
            <DialogDescription>
              {currentSetting?.role} rolü için sorgu zaman aşımı süresini düzenleyin
            </DialogDescription>
          </DialogHeader>
          
          {currentSetting && (
            <TimeoutForm 
              initialData={{
                role: currentSetting.role,
                timeout_seconds: currentSetting.timeout_seconds,
                description: currentSetting.description,
                identifier: currentSetting.role
              }}
              onSubmit={handleSubmitRoleTimeout}
              onCancel={() => setIsRoleDialogOpen(false)}
              isRole={true}
            />
          )}
        </DialogContent>
      </Dialog>
      
      {/* Custom Timeout Dialog */}
      <Dialog open={isCustomDialogOpen} onOpenChange={setIsCustomDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {currentSetting ? 'Özel Zaman Aşımı Düzenle' : 'Yeni Özel Zaman Aşımı'}
            </DialogTitle>
            <DialogDescription>
              {currentSetting 
                ? 'Mevcut özel zaman aşımı süresini düzenleyin' 
                : 'Belirli bir kullanıcı veya grup için özel zaman aşımı süresi tanımlayın'}
            </DialogDescription>
          </DialogHeader>
          
          <TimeoutForm 
            initialData={currentSetting}
            onSubmit={handleSubmitCustomTimeout}
            onCancel={() => setIsCustomDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Son güncelleme: 2025-05-20 05:19:26
// Güncelleyen: Teeksss

export default TimeoutSettings;