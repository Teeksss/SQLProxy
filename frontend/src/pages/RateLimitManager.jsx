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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
import { 
  AlertCircle, 
  CheckCircle, 
  Info, 
  Plus, 
  RefreshCw, 
  Trash2, 
  Edit,
  PlusCircle,
  Settings,
  Search,
  Users,
  User,
  Shield,
  Globe
} from 'lucide-react';
import { 
  getRateLimitRules, 
  createRateLimitRule, 
  updateRateLimitRule, 
  deleteRateLimitRule,
  getUsersList,
  getRolesList
} from '@/api/ratelimits';
import { CURRENT_USER, CURRENT_DATETIME } from '@/utils/constants';

// Kullanıcı Arama Bileşeni
const UserSearchInput = ({ value, onChange, options, isLoading }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [filteredOptions, setFilteredOptions] = useState([]);
  
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredOptions(options.slice(0, 10));
    } else {
      const filtered = options.filter(user => 
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
        user.id.toLowerCase().includes(searchTerm.toLowerCase())
      ).slice(0, 10);
      setFilteredOptions(filtered);
    }
  }, [searchTerm, options]);
  
  const handleSelect = (user) => {
    onChange(user.id);
    setIsDropdownOpen(false);
    setSearchTerm('');
  };
  
  return (
    <div className="relative">
      <div className="relative">
        <User className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
        <Input
          type="text"
          className="pl-9 pr-4"
          placeholder={isLoading ? "Kullanıcılar yükleniyor..." : "Kullanıcı adı veya ID ara..."}
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setIsDropdownOpen(true);
          }}
          onFocus={() => setIsDropdownOpen(true)}
        />
        {value && !searchTerm && (
          <div className="absolute right-2 top-2.5">
            <Badge variant="outline">
              {options.find(o => o.id === value)?.name || value}
            </Badge>
          </div>
        )}
      </div>
      {isDropdownOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md border border-gray-200 max-h-60 overflow-auto">
          {filteredOptions.length > 0 ? (
            <ul className="py-1">
              {filteredOptions.map(user => (
                <li 
                  key={user.id}
                  className={`px-3 py-2 hover:bg-gray-100 cursor-pointer flex items-center ${value === user.id ? 'bg-blue-50' : ''}`}
                  onClick={() => handleSelect(user)}
                >
                  <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs mr-2">
                    {user.name[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="font-medium">{user.name}</div>
                    <div className="text-xs text-gray-500">{user.id}</div>
                  </div>
                  {value === user.id && (
                    <CheckCircle className="h-4 w-4 text-green-500 ml-auto" />
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-3 py-2 text-gray-500 text-sm">
              Sonuç bulunamadı
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const RateLimitRuleForm = ({ 
  initialData = null, 
  onSubmit, 
  onCancel 
}) => {
  const [formData, setFormData] = useState({
    rule_type: 'role',
    identifier: '',
    max_requests: 60,
    window_seconds: 60,
    is_active: true,
    description: ''
  });
  
  const [roleOptions, setRoleOptions] = useState([]);
  const [userOptions, setUserOptions] = useState([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isLoadingRoles, setIsLoadingRoles] = useState(false);
  const { toast } = useToast();
  
  useEffect(() => {
    // If editing an existing rule, populate the form
    if (initialData) {
      setFormData(initialData);
    }
    
    // Fetch roles
    const fetchRoles = async () => {
      setIsLoadingRoles(true);
      try {
        const roles = await getRolesList();
        setRoleOptions(roles);
      } catch (error) {
        console.error('Error fetching roles:', error);
        setRoleOptions([
          { id: 'admin', name: 'Admin' },
          { id: 'analyst', name: 'Analyst' },
          { id: 'powerbi', name: 'PowerBI' },
          { id: 'readonly', name: 'ReadOnly' }
        ]);
      } finally {
        setIsLoadingRoles(false);
      }
    };
    
    // Fetch users
    const fetchUsers = async () => {
      setIsLoadingUsers(true);
      try {
        const users = await getUsersList();
        setUserOptions(users);
      } catch (error) {
        console.error('Error fetching users:', error);
        // Demo kullanıcıları
        setUserOptions([
          { id: 'john.doe', name: 'John Doe' },
          { id: 'jane.smith', name: 'Jane Smith' },
          { id: 'bob.johnson', name: 'Bob Johnson' },
          { id: 'alice.williams', name: 'Alice Williams' },
          { id: 'Teeksss', name: 'Teeksss' },
          { id: 'mike.brown', name: 'Mike Brown' },
          { id: 'sarah.davis', name: 'Sarah Davis' },
          { id: 'tom.wilson', name: 'Tom Wilson' },
          { id: 'emily.jones', name: 'Emily Jones' },
          { id: 'david.miller', name: 'David Miller' },
          { id: 'lisa.taylor', name: 'Lisa Taylor' },
          { id: 'james.anderson', name: 'James Anderson' },
          { id: 'patricia.thomas', name: 'Patricia Thomas' },
          { id: 'robert.jackson', name: 'Robert Jackson' },
          { id: 'jennifer.white', name: 'Jennifer White' }
        ]);
      } finally {
        setIsLoadingUsers(false);
      }
    };
    
    fetchRoles();
    fetchUsers();
  }, [initialData]);
  
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
        description: "Lütfen bir tanımlayıcı seçin",
        variant: "destructive",
      });
      return;
    }
    
    onSubmit(formData);
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="rule_type">Kural Tipi</Label>
        <Select 
          value={formData.rule_type}
          onValueChange={(value) => {
            handleChange('rule_type', value);
            handleChange('identifier', ''); // Reset identifier when type changes
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Kural tipi seçin" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="user">
              <div className="flex items-center">
                <User className="h-4 w-4 mr-2" />
                <span>Kullanıcı</span>
              </div>
            </SelectItem>
            <SelectItem value="role">
              <div className="flex items-center">
                <Shield className="h-4 w-4 mr-2" />
                <span>Rol</span>
              </div>
            </SelectItem>
            <SelectItem value="ip">
              <div className="flex items-center">
                <Globe className="h-4 w-4 mr-2" />
                <span>IP Adresi</span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="identifier">
          {formData.rule_type === 'user' 
            ? 'Kullanıcı' 
            : formData.rule_type === 'role' 
              ? 'Rol' 
              : 'IP Adresi'}
        </Label>
        
        {formData.rule_type === 'role' ? (
          <Select 
            value={formData.identifier}
            onValueChange={(value) => handleChange('identifier', value)}
            disabled={isLoadingRoles}
          >
            <SelectTrigger>
              <SelectValue placeholder={isLoadingRoles ? "Roller yükleniyor..." : "Rol seçin"} />
            </SelectTrigger>
            <SelectContent>
              {roleOptions.map(role => (
                <SelectItem key={role.id} value={role.id}>
                  <div className="flex items-center">
                    <Shield className="h-4 w-4 mr-2 text-blue-500" />
                    <span>{role.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : formData.rule_type === 'user' ? (
          <UserSearchInput
            value={formData.identifier}
            onChange={(value) => handleChange('identifier', value)}
            options={userOptions}
            isLoading={isLoadingUsers}
          />
        ) : (
          <div className="relative">
            <Globe className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
            <Input 
              type="text"
              value={formData.identifier}
              onChange={(e) => handleChange('identifier', e.target.value)}
              placeholder="IP adresi girin (örn: 192.168.1.1)"
              className="pl-9"
            />
          </div>
        )}
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="max_requests">Maksimum İstek</Label>
          <Input 
            type="number"
            value={formData.max_requests}
            onChange={(e) => handleChange('max_requests', parseInt(e.target.value))}
            min="1"
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="window_seconds">Süre (saniye)</Label>
          <Input 
            type="number"
            value={formData.window_seconds}
            onChange={(e) => handleChange('window_seconds', parseInt(e.target.value))}
            min="1"
          />
          <p className="text-xs text-gray-500">
            {formData.max_requests} istek / {formData.window_seconds} saniye
          </p>
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="description">Açıklama</Label>
        <Input 
          type="text"
          value={formData.description || ''}
          onChange={(e) => handleChange('description', e.target.value)}
          placeholder="Bu kural için açıklama girin (opsiyonel)"
        />
      </div>
      
      <div className="flex items-center space-x-2">
        <Switch 
          id="is_active" 
          checked={formData.is_active}
          onCheckedChange={(checked) => handleChange('is_active', checked)}
        />
        <Label htmlFor="is_active">Aktif</Label>
      </div>
      
      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          İptal
        </Button>
        <Button type="submit">
          {initialData ? 'Güncelle' : 'Ekle'}
        </Button>
      </DialogFooter>
    </form>
  );
};

const RateLimitManagerPage = () => {
  const [rateLimitRules, setRateLimitRules] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [currentRule, setCurrentRule] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const { toast } = useToast();
  
  const fetchRateLimitRules = async () => {
    setIsLoading(true);
    try {
      const data = await getRateLimitRules();
      setRateLimitRules(data);
    } catch (error) {
      console.error('Error fetching rate limit rules:', error);
      toast({
        title: "Hata",
        description: "Rate limit kuralları yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
      
      // Demo verileri
      setRateLimitRules([
        {
          id: 1,
          rule_type: 'role',
          identifier: 'admin',
          max_requests: 300,
          window_seconds: 60,
          is_active: true,
          description: 'Admin kullanıcılar için limit',
          created_at: '2025-05-16T13:31:40Z'
        },
        {
          id: 2,
          rule_type: 'role',
          identifier: 'analyst',
          max_requests: 100,
          window_seconds: 60,
          is_active: true,
          description: 'Analistler için limit',
          created_at: '2025-05-16T13:31:40Z'
        },
        {
          id: 3,
          rule_type: 'role',
          identifier: 'powerbi',
          max_requests: 200,
          window_seconds: 60,
          is_active: true,
          description: 'PowerBI kullanıcıları için limit',
          created_at: '2025-05-16T13:31:40Z'
        },
        {
          id: 4,
          rule_type: 'role',
          identifier: 'readonly',
          max_requests: 30,
          window_seconds: 60,
          is_active: true,
          description: 'Salt okunur kullanıcılar için limit',
          created_at: '2025-05-16T13:31:40Z'
        },
        {
          id: 5,
          rule_type: 'user',
          identifier: 'Teeksss',
          max_requests: 500,
          window_seconds: 60,
          is_active: true,
          description: 'Teeksss kullanıcısı için özel limit',
          created_at: '2025-05-16T13:31:40Z'
        },
        {
          id: 6,
          rule_type: 'ip',
          identifier: '192.168.1.10',
          max_requests: 50,
          window_seconds: 120,
          is_active: false,
          description: 'Test sunucusu için limit',
          created_at: '2025-05-16T13:31:40Z'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchRateLimitRules();
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
    if (!confirm('Bu kuralı silmek istediğinizden emin misiniz?')) {
      return;
    }
    
    try {
      await deleteRateLimitRule(ruleId);
      toast({
        title: "Başarılı",
        description: "Rate limit kuralı başarıyla silindi.",
        variant: "default",
      });
      
      // Refresh the list
      fetchRateLimitRules();
    } catch (error) {
      console.error('Error deleting rate limit rule:', error);
      toast({
        title: "Hata",
        description: "Rate limit kuralı silinirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleSubmitRule = async (formData) => {
    try {
      if (currentRule) {
        // Update existing rule
        await updateRateLimitRule(currentRule.id, formData);
        toast({
          title: "Başarılı",
          description: "Rate limit kuralı başarıyla güncellendi.",
          variant: "default",
        });
      } else {
        // Create new rule
        await createRateLimitRule(formData);
        toast({
          title: "Başarılı",
          description: "Rate limit kuralı başarıyla oluşturuldu.",
          variant: "default",
        });
      }
      
      // Close dialog and refresh list
      setIsDialogOpen(false);
      fetchRateLimitRules();
    } catch (error) {
      console.error('Error saving rate limit rule:', error);
      toast({
        title: "Hata",
        description: "Rate limit kuralı kaydedilirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const formatIdentifierName = (rule) => {
    switch (rule.rule_type) {
      case 'role':
        return `${rule.identifier} (Rol)`;
      case 'user':
        return `${rule.identifier} (Kullanıcı)`;
      case 'ip':
        return `${rule.identifier} (IP)`;
      default:
        return rule.identifier;
    }
  };
  
  // Filter rules based on search term and type
  const filteredRules = rateLimitRules.filter(rule => {
    const matchesSearch = searchTerm === '' || 
      rule.identifier.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (rule.description && rule.description.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesType = filterType === '' || rule.rule_type === filterType;
    
    return matchesSearch && matchesType;
  });
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Rate Limit Yönetimi</h1>
        <div className="text-sm text-gray-500">
          Son güncelleme: {new Date('2025-05-16 13:31:40').toLocaleString()}
        </div>
      </div>
      
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Filtreleme ve Arama</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Tanımlayıcı veya açıklama ara..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="w-full md:w-48">
              <Select 
                value={filterType}
                onValueChange={setFilterType}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tüm tipler" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tüm tipler</SelectItem>
                  <SelectItem value="user">Kullanıcı</SelectItem>
                  <SelectItem value="role">Rol</SelectItem>
                  <SelectItem value="ip">IP Adresi</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" onClick={fetchRateLimitRules}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Yenile
            </Button>
            <Button onClick={handleAddRule}>
              <Plus className="h-4 w-4 mr-2" />
              Yeni Kural Ekle
            </Button>
          </div>
        </CardContent>
      </Card>
      
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">Tüm Kurallar</TabsTrigger>
          <TabsTrigger value="role">Rol Bazlı</TabsTrigger>
          <TabsTrigger value="user">Kullanıcı Bazlı</TabsTrigger>
          <TabsTrigger value="ip">IP Bazlı</TabsTrigger>
        </TabsList>
        
        <TabsContent value="all">
          <Card>
            <CardHeader>
              <CardTitle>Tüm Rate Limit Kuralları</CardTitle>
              <CardDescription>
                Tüm kullanıcı, rol ve IP bazlı rate limit kurallarını görüntüleyin ve yönetin.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center items-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
                </div>
              ) : filteredRules.length === 0 ? (
                <div className="text-center py-8">
                  <Info className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-gray-500">
                    {searchTerm || filterType 
                      ? "Arama kriterlerine uygun kural bulunamadı." 
                      : "Henüz tanımlanmış rate limit kuralı yok."}
                  </p>
                  <Button variant="outline" onClick={handleAddRule} className="mt-4">
                    <Plus className="h-4 w-4 mr-2" />
                    Yeni Kural Ekle
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tanımlayıcı</TableHead>
                      <TableHead>Limit</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead>Açıklama</TableHead>
                      <TableHead>Oluşturulma</TableHead>
                      <TableHead className="text-right">İşlemler</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRules.map(rule => (
                      <TableRow key={rule.id}>
                        <TableCell className="font-medium">
                          <div className="flex items-center">
                            {rule.rule_type === 'user' && <User className="h-4 w-4 mr-2 text-blue-500" />}
                            {rule.rule_type === 'role' && <Shield className="h-4 w-4 mr-2 text-green-500" />}
                            {rule.rule_type === 'ip' && <Globe className="h-4 w-4 mr-2 text-amber-500" />}
                            {formatIdentifierName(rule)}
                          </div>
                        </TableCell>
                        <TableCell>
                          {rule.max_requests} istek / {rule.window_seconds} saniye
                        </TableCell>
                        <TableCell>
                          {rule.is_active ? (
                            <Badge className="bg-green-500">Aktif</Badge>
                          ) : (
                            <Badge variant="outline">Pasif</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {rule.description || '-'}
                        </TableCell>
                        <TableCell className="text-sm">
                          {new Date(rule.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end space-x-2">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleEditRule(rule)}
                            >
                              <Edit className="h-4 w-4" />
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
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="role">
          <Card>
            <CardHeader>
              <CardTitle>Rol Bazlı Rate Limit Kuralları</CardTitle>
              <CardDescription>
                Rol bazlı rate limit kurallarını görüntüleyin ve yönetin.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rol</TableHead>
                    <TableHead>Limit</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead>Açıklama</TableHead>
                    <TableHead>Oluşturulma</TableHead>
                    <TableHead className="text-right">İşlemler</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRules
                    .filter(rule => rule.rule_type === 'role')
                    .map(rule => (
                      <TableRow key={rule.id}>
                        <TableCell className="font-medium">
                          <div className="flex items-center">
                            <Shield className="h-4 w-4 mr-2 text-green-500" />
                            {rule.identifier}
                          </div>
                        </TableCell>
                        <TableCell>
                          {rule.max_requests} istek / {rule.window_seconds} saniye
                        </TableCell>
                        <TableCell>
                          {rule.is_active ? (
                            <Badge className="bg-green-500">Aktif</Badge>
                          ) : (
                            <Badge variant="outline">Pasif</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {rule.description || '-'}
                        </TableCell>
                        <TableCell className="text-sm">
                          {new Date(rule.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end space-x-2">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleEditRule(rule)}
                            >
                              <Edit className="h-4 w-4" />
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
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="user">
          <Card>
            <CardHeader>
              <CardTitle>Kullanıcı Bazlı Rate Limit Kuralları</CardTitle>
              <CardDescription>
                Kullanıcı bazlı rate limit kurallarını görüntüleyin ve yönetin.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Kullanıcı</TableHead>
                    <TableHead>Limit</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead>Açıklama</TableHead>
                    <TableHead>Oluşturulma</TableHead>
                    <TableHead className="text-right">İşlemler</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRules
                    .filter(rule => rule.rule_type === 'user')
                    .map(rule => (
                      <TableRow key={rule.id}>
                        <TableCell className="font-medium">
                          <div className="flex items-center">
                            <User className="h-4 w-4 mr-2 text-blue-500" />
                            {rule.identifier}
                            {rule.identifier === CURRENT_USER.username && (
                              <Badge className="ml-2 bg-blue-100 text-blue-800 text-xs">Siz</Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {rule.max_requests} istek / {rule.window_seconds} saniye
                        </TableCell>
                        <TableCell>
                          {rule.is_active ? (
                            <Badge className="bg-green-500">Aktif</Badge>
                          ) : (
                            <Badge variant="outline">Pasif</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {rule.description || '-'}
                        </TableCell>
                        <TableCell className="text-sm">
                          {new Date(rule.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end space-x-2">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleEditRule(rule)}
                            >
                              <Edit className="h-4 w-4" />
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
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="ip">
          <Card>
            <CardHeader>
              <CardTitle>IP Bazlı Rate Limit Kuralları</CardTitle>
              <CardDescription>
                IP bazlı rate limit kurallarını görüntüleyin ve yönetin.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>IP Adresi</TableHead>
                    <TableHead>Limit</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead>Açıklama</TableHead>
                    <TableHead>Oluşturulma</TableHead>
                    <TableHead className="text-right">İşlemler</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRules
                    .filter(rule => rule.rule_type === 'ip')
                    .map(rule => (
                      <TableRow key={rule.id}>
                        <TableCell className="font-medium">
                          <div className="flex items-center">
                            <Globe className="h-4 w-4 mr-2 text-amber-500" />
                            {rule.identifier}
                          </div>
                        </TableCell>
                        <TableCell>
                          {rule.max_requests} istek / {rule.window_seconds} saniye
                        </TableCell>
                        <TableCell>
                          {rule.is_active ? (
                            <Badge className="bg-green-500">Aktif</Badge>
                          ) : (
                            <Badge variant="outline">Pasif</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {rule.description || '-'}
                        </TableCell>
                        <TableCell className="text-sm">
                          {new Date(rule.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end space-x-2">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleEditRule(rule)}
                            >
                              <Edit className="h-4 w-4" />
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
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {currentRule ? 'Rate Limit Kuralını Düzenle' : 'Yeni Rate Limit Kuralı Ekle'}
            </DialogTitle>
            <DialogDescription>
              {currentRule 
                ? 'Mevcut rate limit kuralını güncelleyin.' 
                : 'Kullanıcı, rol veya IP bazlı yeni bir rate limit kuralı oluşturun.'}
            </DialogDescription>
          </DialogHeader>
          
          <RateLimitRuleForm 
            initialData={currentRule}
            onSubmit={handleSubmitRule}
            onCancel={() => setIsDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RateLimitManagerPage;