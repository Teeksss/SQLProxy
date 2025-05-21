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
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  AlertCircle, 
  CheckCircle, 
  Database, 
  Eye, 
  EyeOff, 
  FileBadge, 
  FileEdit, 
  Info, 
  Lock, 
  Pencil, 
  Plus, 
  RefreshCw, 
  Save, 
  Search, 
  Shield, 
  ShieldAlert, 
  Table2, 
  Trash2, 
  UserCog, 
  X
} from 'lucide-react';
import { 
  getMaskingRules,
  createMaskingRule,
  updateMaskingRule,
  deleteMaskingRule,
  testMaskingPattern
} from '@/api/masking';

// MaskingRule form component
const MaskingRuleForm = ({ initialData = null, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    table_pattern: '',
    column_mappings: {},
    is_active: true,
    roles_exempted: [],
    users_exempted: []
  });
  
  const [newColumnName, setNewColumnName] = useState('');
  const [newColumnType, setNewColumnType] = useState('full');
  const [testTableName, setTestTableName] = useState('');
  const [testResult, setTestResult] = useState(null);
  const { toast } = useToast();
  
  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    }
  }, [initialData]);
  
  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  const handleAddColumnMapping = () => {
    if (!newColumnName.trim()) {
      toast({
        title: "Hata",
        description: "Kolon adı boş olamaz.",
        variant: "destructive",
      });
      return;
    }
    
    setFormData(prev => ({
      ...prev,
      column_mappings: {
        ...prev.column_mappings,
        [newColumnName.trim().toLowerCase()]: newColumnType
      }
    }));
    
    setNewColumnName('');
    setNewColumnType('full');
  };
  
  const handleRemoveColumnMapping = (columnName) => {
    setFormData(prev => {
      const newMappings = { ...prev.column_mappings };
      delete newMappings[columnName];
      
      return {
        ...prev,
        column_mappings: newMappings
      };
    });
  };
  
  const handleTestPattern = async () => {
    if (!formData.table_pattern.trim() || !testTableName.trim()) {
      toast({
        title: "Hata",
        description: "Tablo kalıbı ve test edilecek tablo adı gereklidir.",
        variant: "destructive",
      });
      return;
    }
    
    try {
      const result = await testMaskingPattern(formData.table_pattern, testTableName);
      setTestResult(result);
      
      toast({
        title: result.matches ? "Eşleşti" : "Eşleşmedi",
        description: result.matches 
          ? `"${testTableName}" tablo adı, "${formData.table_pattern}" kalıbıyla eşleşiyor.` 
          : `"${testTableName}" tablo adı, "${formData.table_pattern}" kalıbıyla eşleşmiyor.`,
        variant: result.matches ? "default" : "destructive",
      });
    } catch (error) {
      toast({
        title: "Hata",
        description: "Kalıp testi yapılırken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.name || !formData.table_pattern) {
      toast({
        title: "Hata",
        description: "İsim ve tablo kalıbı zorunludur.",
        variant: "destructive",
      });
      return;
    }
    
    // Ensure at least one column mapping
    if (Object.keys(formData.column_mappings).length === 0) {
      toast({
        title: "Hata",
        description: "En az bir kolon eşleştirmesi eklemelisiniz.",
        variant: "destructive",
      });
      return;
    }
    
    onSubmit(formData);
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4 py-2">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name">Kural Adı</Label>
            <Input 
              id="name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="Kural adı"
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="is_active" className="flex items-center justify-between">
              <span>Aktif</span>
              {formData.is_active ? (
                <Badge className="bg-green-500">Aktif</Badge>
              ) : (
                <Badge variant="outline">Pasif</Badge>
              )}
            </Label>
            <div className="flex items-center space-x-2">
              <Switch 
                id="is_active" 
                checked={formData.is_active} 
                onCheckedChange={(checked) => handleChange('is_active', checked)}
              />
              <Label htmlFor="is_active">
                {formData.is_active ? 'Bu kural aktif olarak uygulanır' : 'Bu kural pasif durumdadır'}
              </Label>
            </div>
          </div>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="description">Açıklama</Label>
          <Input 
            id="description"
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Kural açıklaması (opsiyonel)"
          />
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <Label htmlFor="table_pattern">Tablo Kalıbı (Regex)</Label>
            <div className="flex items-center space-x-2">
              <Input
                placeholder="Test için tablo adı"
                value={testTableName}
                onChange={(e) => setTestTableName(e.target.value)}
                className="w-48"
              />
              <Button 
                type="button" 
                variant="outline" 
                size="sm"
                onClick={handleTestPattern}
                disabled={!formData.table_pattern || !testTableName}
              >
                Test Et
              </Button>
            </div>
          </div>
          <Input 
            id="table_pattern"
            value={formData.table_pattern}
            onChange={(e) => handleChange('table_pattern', e.target.value)}
            placeholder="^employees|hr_.*|staff$"
            required
          />
          <p className="text-xs text-gray-500">
            Regular expression formatında tablo ismi kalıbı. Eşleşen tablolarda maskeleme kuralı uygulanır.
          </p>
          
          {testResult && (
            <div className={`mt-2 text-sm p-2 rounded ${
              testResult.matches ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            }`}>
              {testResult.matches ? (
                <div className="flex items-center">
                  <CheckCircle className="h-4 w-4 mr-1.5" />
                  <span>Eşleşti! "{testTableName}" tablosu bu kalıpla eşleşiyor.</span>
                </div>
              ) : (
                <div className="flex items-center">
                  <X className="h-4 w-4 mr-1.5" />
                  <span>Eşleşmedi! "{testTableName}" tablosu bu kalıpla eşleşmiyor.</span>
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="space-y-2">
          <Label>Kolon Eşleştirmeleri</Label>
          <Card>
            <CardHeader className="py-2">
              <div className="flex items-end space-x-2">
                <div className="flex-1 space-y-1">
                  <Label htmlFor="new_column_name">Kolon Adı</Label>
                  <Input 
                    id="new_column_name"
                    value={newColumnName}
                    onChange={(e) => setNewColumnName(e.target.value)}
                    placeholder="salary, email, credit_card, vb."
                  />
                </div>
                <div className="w-40 space-y-1">
                  <Label htmlFor="new_column_type">Maskeleme Tipi</Label>
                  <Select 
                    value={newColumnType} 
                    onValueChange={setNewColumnType}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="full">Tamamen Maskele</SelectItem>
                      <SelectItem value="partial">Kısmen Maskele</SelectItem>
                      <SelectItem value="none">Maskeleme</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button 
                  type="button" 
                  onClick={handleAddColumnMapping}
                  disabled={!newColumnName.trim()}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Ekle
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {Object.keys(formData.column_mappings).length === 0 ? (
                <div className="text-center py-4 text-gray-500">
                  <Database className="h-8 w-8 mx-auto text-gray-300 mb-2" />
                  <p>Henüz kolon eşleştirmesi eklenmedi</p>
                  <p className="text-xs">Yukarıdaki formu kullanarak kolon eşleştirmeleri ekleyin</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Kolon Adı</TableHead>
                      <TableHead>Maskeleme Tipi</TableHead>
                      <TableHead className="w-16 text-right">İşlem</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(formData.column_mappings).map(([columnName, maskType]) => (
                      <TableRow key={columnName}>
                        <TableCell className="font-medium">{columnName}</TableCell>
                        <TableCell>
                          <Badge className={
                            maskType === 'full' ? 'bg-red-500' : 
                            maskType === 'partial' ? 'bg-amber-500' : 
                            'bg-green-500'
                          }>
                            {maskType === 'full' ? 'Tam Maskeleme' : 
                             maskType === 'partial' ? 'Kısmi Maskeleme' : 
                             'Maskeleme Yok'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button 
                            type="button" 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleRemoveColumnMapping(columnName)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
        
        <div className="space-y-2">
          <Label>İzinli Roller ve Kullanıcılar</Label>
          <Card>
            <CardContent className="pt-4">
              <div className="space-y-4">
                <div>
                  <Label>Muaf Tutulan Roller</Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    <Badge 
                      variant={formData.roles_exempted.includes('admin') ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => {
                        if (formData.roles_exempted.includes('admin')) {
                          handleChange('roles_exempted', formData.roles_exempted.filter(r => r !== 'admin'));
                        } else {
                          handleChange('roles_exempted', [...formData.roles_exempted, 'admin']);
                        }
                      }}
                    >
                      admin
                    </Badge>
                    <Badge 
                      variant={formData.roles_exempted.includes('analyst') ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => {
                        if (formData.roles_exempted.includes('analyst')) {
                          handleChange('roles_exempted', formData.roles_exempted.filter(r => r !== 'analyst'));
                        } else {
                          handleChange('roles_exempted', [...formData.roles_exempted, 'analyst']);
                        }
                      }}
                    >
                      analyst
                    </Badge>
                    <Badge 
                      variant={formData.roles_exempted.includes('powerbi') ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => {
                        if (formData.roles_exempted.includes('powerbi')) {
                          handleChange('roles_exempted', formData.roles_exempted.filter(r => r !== 'powerbi'));
                        } else {
                          handleChange('roles_exempted', [...formData.roles_exempted, 'powerbi']);
                        }
                      }}
                    >
                      powerbi
                    </Badge>
                    <Badge 
                      variant={formData.roles_exempted.includes('readonly') ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => {
                        if (formData.roles_exempted.includes('readonly')) {
                          handleChange('roles_exempted', formData.roles_exempted.filter(r => r !== 'readonly'));
                        } else {
                          handleChange('roles_exempted', [...formData.roles_exempted, 'readonly']);
                        }
                      }}
                    >
                      readonly
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Bu rollere sahip kullanıcılar maskeleme olmadan tüm verileri görebilir</p>
                </div>
              </div>
            </CardContent>
          </Card>
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

const MaskingSettings = () => {
  const [maskingRules, setMaskingRules] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [currentRule, setCurrentRule] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const { toast } = useToast();
  
  const fetchMaskingRules = async () => {
    setIsLoading(true);
    try {
      const data = await getMaskingRules();
      setMaskingRules(data);
    } catch (error) {
      console.error('Error fetching masking rules:', error);
      toast({
        title: "Hata",
        description: "Maskeleme kuralları yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
      
      // Mock data
      setMaskingRules([
        {
          id: 1,
          name: 'Kişisel Bilgi Maskeleme',
          description: 'Müşteri ve personel tablolarındaki kişisel veriler için maskeleme',
          table_pattern: '^customers|employees|users|staff$',
          column_mappings: {
            'tckn': 'full',
            'tc_kimlik_no': 'full',
            'email': 'partial',
            'phone': 'partial',
            'phone_number': 'partial',
            'gsm': 'partial',
            'credit_card': 'partial',
            'adres': 'partial',
            'address': 'partial'
          },
          is_active: true,
          roles_exempted: ['admin'],
          priority: 100,
          created_by: 'admin',
          created_at: '2025-05-01T09:00:00Z'
        },
        {
          id: 2,
          name: 'Finansal Veri Maskeleme',
          description: 'Finansal verilerin maskelenmesi',
          table_pattern: '^transactions|payments|salaries|invoices$',
          column_mappings: {
            'amount': 'full',
            'salary': 'full',
            'income': 'full',
            'balance': 'full',
            'account_no': 'partial',
            'iban': 'partial'
          },
          is_active: true,
          roles_exempted: ['admin', 'analyst'],
          priority: 80,
          created_by: 'admin',
          created_at: '2025-05-02T14:30:00Z'
        },
        {
          id: 3,
          name: 'Log Tablolarında IP Maskeleme',
          description: 'Log tablolarındaki IP adreslerinin kısmi maskelenmesi',
          table_pattern: '^.*_logs$|^logs_.*$|^activity$',
          column_mappings: {
            'ip': 'partial',
            'ip_address': 'partial',
            'client_ip': 'partial',
            'server_ip': 'none'
          },
          is_active: false,
          roles_exempted: ['admin'],
          priority: 60,
          created_by: 'Teeksss',
          created_at: '2025-05-16T13:48:26Z'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchMaskingRules();
  }, []);
  
  const handleAddRule = () => {
    setCurrentRule(null);
    setIsDialogOpen(true);
  };
  
  const handleEditRule = (rule) => {
    setCurrentRule(rule);
    setIsDialogOpen(true);
  };
  
  const handleDeleteRule = async (ruleId) => {
    if (!confirm('Bu maskeleme kuralını silmek istediğinizden emin misiniz?')) {
      return;
    }
    
    try {
      await deleteMaskingRule(ruleId);
      toast({
        title: "Başarılı",
        description: "Maskeleme kuralı başarıyla silindi.",
        variant: "default",
      });
      
      // Refresh the list
      fetchMaskingRules();
    } catch (error) {
      console.error('Error deleting masking rule:', error);
      toast({
        title: "Hata",
        description: "Maskeleme kuralı silinirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleSubmitRule = async (formData) => {
    try {
      if (currentRule) {
        // Update existing rule
        await updateMaskingRule(currentRule.id, formData);
        toast({
          title: "Başarılı",
          description: "Maskeleme kuralı başarıyla güncellendi.",
          variant: "default",
        });
      } else {
        // Create new rule
        await createMaskingRule(formData);
        toast({
          title: "Başarılı",
          description: "Maskeleme kuralı başarıyla oluşturuldu.",
          variant: "default",
        });
      }
      
      // Close dialog and refresh list
      setIsDialogOpen(false);
      fetchMaskingRules();
    } catch (error) {
      console.error('Error saving masking rule:', error);
      toast({
        title: "Hata",
        description: "Maskeleme kuralı kaydedilirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  // Filter rules based on search term
  const filteredRules = maskingRules.filter(rule => 
    rule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rule.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rule.table_pattern.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Veri Maskeleme Ayarları</h1>
        <Button onClick={handleAddRule}>
          <Plus className="h-4 w-4 mr-2" />
          Yeni Maskeleme Kuralı
        </Button>
      </div>
      
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <ShieldAlert className="h-5 w-5 mr-2" />
            Hassas Veri Maskeleme
          </CardTitle>
          <CardDescription>
            Veritabanı sorgu sonuçlarında hassas verilerin otomatik maskelenmesi için kuralları yönetin
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between items-center mb-4">
            <div className="text-sm">
              <p>
                <strong>Veri maskeleme özelliği</strong>, hassas verilerin (TCKN, kredi kartı, e-posta, vb.) 
                sorgu sonuçlarında otomatik olarak maskelenmesini sağlar. Maskeleme, kullanıcının rol ve yetkilerine göre uygulanır.
              </p>
              <ul className="list-disc list-inside mt-2 text-gray-600">
                <li>
                  <strong>Tam maskeleme</strong>: Veri tamamen gizlenir (örn: *****)
                </li>
                <li>
                  <strong>Kısmi maskeleme</strong>: Verinin bir kısmı gösterilir (örn: 12345******)
                </li>
                <li>
                  <strong>Maskeleme yok</strong>: Veri olduğu gibi gösterilir
                </li>
              </ul>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Maskeleme kuralı ara..."
                className="pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button variant="outline" onClick={fetchMaskingRules}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Yenile
            </Button>
          </div>
          
          {isLoading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            </div>
          ) : filteredRules.length === 0 ? (
            <div className="text-center py-8">
              <EyeOff className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">
                {searchTerm ? "Arama kriterine uygun maskeleme kuralı bulunamadı." : "Henüz tanımlanmış maskeleme kuralı yok."}
              </p>
              <Button variant="outline" className="mt-4" onClick={handleAddRule}>
                <Plus className="h-4 w-4 mr-2" />
                Yeni Maskeleme Kuralı Oluştur
              </Button>
            </div>
          ) : (
            <div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Kural</TableHead>
                    <TableHead>Tablo Kalıbı</TableHead>
                    <TableHead>Maskeli Kolonlar</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead className="text-right">İşlemler</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRules.map(rule => (
                    <TableRow key={rule.id}>
                      <TableCell>
                        <div className="font-medium">{rule.name}</div>
                        <div className="text-sm text-gray-500">{rule.description}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          Oluşturan: {rule.created_by}, {new Date(rule.created_at).toLocaleString()}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {rule.table_pattern}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(rule.column_mappings).slice(0, 3).map(([column, type]) => (
                            <Badge 
                              key={column}
                              className={
                                type === 'full' ? 'bg-red-500' : 
                                type === 'partial' ? 'bg-amber-500' : 
                                'bg-green-500'
                              }
                            >
                              {column}
                            </Badge>
                          ))}
                          {Object.keys(rule.column_mappings).length > 3 && (
                            <Badge variant="outline">
                              +{Object.keys(rule.column_mappings).length - 3} daha
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {rule.is_active ? (
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
                            onClick={() => handleEditRule(rule)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => handleDeleteRule(rule.id)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
        <CardFooter className="border-t pt-4 text-xs text-gray-500">
          Son güncelleme: {new Date('2025-05-16 13:48:26').toLocaleString()} • Kullanıcı: Teeksss
        </CardFooter>
      </Card>
      
      {/* Rule Form Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>
              {currentRule ? 'Maskeleme Kuralını Düzenle' : 'Yeni Maskeleme Kuralı Oluştur'}
            </DialogTitle>
            <DialogDescription>
              {currentRule 
                ? 'Mevcut maskeleme kuralını düzenleyin' 
                : 'Hassas verilerin otomatik maskelenmesi için yeni bir kural oluşturun'}
            </DialogDescription>
          </DialogHeader>
          
          <MaskingRuleForm 
            initialData={currentRule}
            onSubmit={handleSubmitRule}
            onCancel={() => setIsDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Son güncelleme: 2025-05-16 13:48:26
// Güncelleyen: Teeksss

export default MaskingSettings;