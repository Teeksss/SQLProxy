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
import { 
  Table, 
  TableBody, 
  TableCaption, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  AlertCircle, 
  CheckCircle, 
  Eye, 
  Pencil,
  Plus, 
  RefreshCw, 
  Search, 
  Shield, 
  Trash2, 
  User, 
  Users
} from 'lucide-react';
import { CURRENT_USER, CURRENT_DATETIME, ROLE_COLORS } from '@/utils/constants';

// Mock API functions - replace with actual API calls in production
const getRoles = async () => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 500));
  
  return [
    { 
      id: 'admin', 
      name: 'Admin', 
      description: 'Tam yönetici erişimi',
      permissions: ['execute_query', 'approve_query', 'manage_whitelist', 'manage_roles', 'manage_servers', 'manage_rate_limits'],
      user_count: 3,
      created_at: '2025-01-15T09:00:00Z',
      is_system_role: true
    },
    { 
      id: 'analyst', 
      name: 'Analist', 
      description: 'Veri analisti kullanıcı rolü',
      permissions: ['execute_query', 'manage_own_queries'],
      user_count: 12,
      created_at: '2025-01-15T09:05:00Z',
      is_system_role: true
    },
    { 
      id: 'powerbi', 
      name: 'PowerBI', 
      description: 'PowerBI entegrasyonu için özel rol',
      permissions: ['execute_query', 'use_powerbi_api'],
      user_count: 8,
      created_at: '2025-01-15T09:10:00Z',
      is_system_role: true
    },
    { 
      id: 'readonly', 
      name: 'Salt Okunur', 
      description: 'Sadece veri okuma erişimi',
      permissions: ['execute_query'],
      user_count: 25,
      created_at: '2025-01-15T09:15:00Z',
      is_system_role: true
    },
    { 
      id: 'data_scientist', 
      name: 'Veri Bilimci', 
      description: 'ML ve model geliştirme ekibi',
      permissions: ['execute_query', 'manage_own_queries', 'use_powerbi_api'],
      user_count: 4,
      created_at: '2025-04-10T14:30:00Z',
      is_system_role: false
    }
  ];
};

const getUsersInRole = async (roleId) => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 800));
  
  // Return mock users for each role
  const usersByRole = {
    'admin': [
      { id: 'admin.user', name: 'Admin User', email: 'admin@example.com', last_login: '2025-05-16T12:15:22Z' },
      { id: 'Teeksss', name: 'Teeksss', email: 'teeksss@example.com', last_login: '2025-05-16T13:35:47Z' },
      { id: 'john.admin', name: 'John Admin', email: 'john.admin@example.com', last_login: '2025-05-15T17:30:00Z' }
    ],
    'analyst': [
      { id: 'jane.smith', name: 'Jane Smith', email: 'jane.smith@example.com', last_login: '2025-05-16T09:10:00Z' },
      { id: 'mike.analyst', name: 'Mike Analyst', email: 'mike@example.com', last_login: '2025-05-15T15:42:00Z' },
      { id: 'sarah.data', name: 'Sarah Data', email: 'sarah@example.com', last_login: '2025-05-14T11:20:00Z' },
      // More users would be here...
    ],
    'powerbi': [
      { id: 'powerbi.service', name: 'PowerBI Service', email: 'powerbi@example.com', last_login: '2025-05-16T10:05:00Z' },
      { id: 'david.reports', name: 'David Reports', email: 'david@example.com', last_login: '2025-05-15T14:30:00Z' },
      // More users would be here...
    ],
    'readonly': [
      { id: 'user1', name: 'Regular User 1', email: 'user1@example.com', last_login: '2025-05-16T08:15:00Z' },
      { id: 'user2', name: 'Regular User 2', email: 'user2@example.com', last_login: '2025-05-15T16:20:00Z' },
      // More users would be here...
    ],
    'data_scientist': [
      { id: 'ml.expert', name: 'ML Expert', email: 'ml@example.com', last_login: '2025-05-16T11:40:00Z' },
      { id: 'data.scientist', name: 'Data Scientist', email: 'data.scientist@example.com', last_login: '2025-05-15T13:25:00Z' },
      // More users would be here...
    ]
  };
  
  return usersByRole[roleId] || [];
};

const createRole = async (roleData) => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  return {
    id: roleData.id,
    name: roleData.name,
    description: roleData.description,
    permissions: roleData.permissions,
    user_count: 0,
    created_at: new Date().toISOString(),
    is_system_role: false
  };
};

const updateRole = async (roleId, roleData) => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  return {
    id: roleId,
    name: roleData.name,
    description: roleData.description,
    permissions: roleData.permissions,
    updated_at: new Date().toISOString()
  };
};

const deleteRole = async (roleId) => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 800));
  
  return { success: true };
};

const addUserToRole = async (roleId, userId) => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 600));
  
  return { success: true };
};

const removeUserFromRole = async (roleId, userId) => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 600));
  
  return { success: true };
};

// Available permissions in the system
const availablePermissions = [
  { id: 'execute_query', name: 'Sorgu Çalıştırma', description: 'Onaylanmış sorguları çalıştırabilir' },
  { id: 'manage_own_queries', name: 'Kendi Sorgularını Yönetme', description: 'Kendi oluşturduğu sorguları yönetebilir' },
  { id: 'approve_query', name: 'Sorgu Onaylama', description: 'Başkalarının sorgularını onaylayabilir' },
  { id: 'manage_whitelist', name: 'Beyaz Liste Yönetimi', description: 'Beyaz listeyi düzenleyebilir' },
  { id: 'manage_roles', name: 'Rol Yönetimi', description: 'Rolleri yönetebilir' },
  { id: 'manage_servers', name: 'Sunucu Yönetimi', description: 'Sunucuları yapılandırabilir' },
  { id: 'manage_rate_limits', name: 'Rate Limit Yönetimi', description: 'Rate limitleri yapılandırabilir' },
  { id: 'use_powerbi_api', name: 'PowerBI API Kullanımı', description: 'PowerBI API entegrasyonunu kullanabilir' },
  { id: 'view_audit_logs', name: 'Audit Log Görüntüleme', description: 'Audit logları görüntüleyebilir' }
];

const RoleForm = ({ initialData = null, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    description: '',
    permissions: ['execute_query'] // Default minimum permission
  });
  
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
  
  const handlePermissionToggle = (permissionId) => {
    setFormData(prev => {
      const currentPermissions = [...prev.permissions];
      
      if (currentPermissions.includes(permissionId)) {
        // Don't allow removing execute_query from system roles
        if (permissionId === 'execute_query' && initialData?.is_system_role) {
          return prev;
        }
        // Remove permission
        return {
          ...prev,
          permissions: currentPermissions.filter(id => id !== permissionId)
        };
      } else {
        // Add permission
        return {
          ...prev,
          permissions: [...currentPermissions, permissionId]
        };
      }
    });
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.id || !formData.name) {
      alert('Rol ID ve isim zorunludur');
      return;
    }
    
    onSubmit(formData);
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="id">Rol ID</Label>
          <Input 
            id="id"
            value={formData.id}
            onChange={(e) => handleChange('id', e.target.value)}
            placeholder="unique_role_id"
            disabled={initialData !== null} // Can't change ID for existing roles
            required
          />
          <p className="text-xs text-gray-500">
            Benzersiz rol tanımlayıcısı (değiştirilemez)
          </p>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="name">Rol Adı</Label>
          <Input 
            id="name"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder="Rol Adı"
            required
          />
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="description">Açıklama</Label>
        <Input 
          id="description"
          value={formData.description || ''}
          onChange={(e) => handleChange('description', e.target.value)}
          placeholder="Bu rolün amacını açıklayın"
        />
      </div>
      
      <div className="space-y-2">
        <Label className="text-base">İzinler</Label>
        <p className="text-sm text-gray-500 mb-2">
          Bu role verilecek izinleri seçin
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {availablePermissions.map(permission => (
            <div key={permission.id} className="flex items-start space-x-2">
              <Checkbox 
                id={`permission-${permission.id}`}
                checked={formData.permissions.includes(permission.id)}
                onCheckedChange={() => handlePermissionToggle(permission.id)}
                disabled={
                  permission.id === 'execute_query' && 
                  initialData?.is_system_role
                }
              />
              <div>
                <Label 
                  htmlFor={`permission-${permission.id}`}
                  className="text-sm font-medium"
                >
                  {permission.name}
                </Label>
                <p className="text-xs text-gray-500">{permission.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {initialData?.is_system_role && (
        <div className="bg-amber-50 p-3 rounded-md">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-amber-500 mr-2 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Sistem Rolü
              </p>
              <p className="text-xs text-amber-700 mt-1">
                Bu bir sistem rolüdür. Bazı izinler ve ayarlar değiştirilemez.
              </p>
            </div>
          </div>
        </div>
      )}
      
      <DialogFooter className="pt-2">
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

const RoleManagementPage = () => {
  const [roles, setRoles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRoleDialogOpen, setIsRoleDialogOpen] = useState(false);
  const [isUsersDialogOpen, setIsUsersDialogOpen] = useState(false);
  const [currentRole, setCurrentRole] = useState(null);
  const [usersInRole, setUsersInRole] = useState([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const { toast } = useToast();
  
  const fetchRoles = async () => {
    setIsLoading(true);
    try {
      const data = await getRoles();
      setRoles(data);
    } catch (error) {
      console.error('Error fetching roles:', error);
      toast({
        title: "Hata",
        description: "Roller yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchRoles();
  }, []);
  
  const handleAddRole = () => {
    setCurrentRole(null);
    setIsRoleDialogOpen(true);
  };
  
  const handleEditRole = (role) => {
    setCurrentRole(role);
    setIsRoleDialogOpen(true);
  };
  
  const handleViewUsers = async (role) => {
    setCurrentRole(role);
    setIsUsersDialogOpen(true);
    setIsLoadingUsers(true);
    
    try {
      const users = await getUsersInRole(role.id);
      setUsersInRole(users);
    } catch (error) {
      console.error('Error fetching users in role:', error);
      toast({
        title: "Hata",
        description: "Rol kullanıcıları yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
      setUsersInRole([]);
    } finally {
      setIsLoadingUsers(false);
    }
  };
  
  const handleDeleteRole = async (roleId) => {
    // Prevent deleting system roles
    const role = roles.find(r => r.id === roleId);
    if (role.is_system_role) {
      toast({
        title: "İzin Hatası",
        description: "Sistem rolleri silinemez.",
        variant: "destructive",
      });
      return;
    }
    
    if (!confirm(`"${role.name}" rolünü silmek istediğinizden emin misiniz?`)) {
      return;
    }
    
    try {
      await deleteRole(roleId);
      toast({
        title: "Başarılı",
        description: "Rol başarıyla silindi.",
        variant: "default",
      });
      
      // Refresh the list
      fetchRoles();
    } catch (error) {
      console.error('Error deleting role:', error);
      toast({
        title: "Hata",
        description: "Rol silinirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleSubmitRole = async (formData) => {
    try {
      if (currentRole) {
        // Update existing role
        await updateRole(currentRole.id, formData);
        toast({
          title: "Başarılı",
          description: "Rol başarıyla güncellendi.",
          variant: "default",
        });
      } else {
        // Create new role
        await createRole(formData);
        toast({
          title: "Başarılı",
          description: "Rol başarıyla oluşturuldu.",
          variant: "default",
        });
      }
      
      // Close dialog and refresh list
      setIsRoleDialogOpen(false);
      fetchRoles();
    } catch (error) {
      console.error('Error saving role:', error);
      toast({
        title: "Hata",
        description: "Rol kaydedilirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleRemoveUserFromRole = async (userId) => {
    if (!confirm(`Bu kullanıcıyı "${currentRole.name}" rolünden çıkarmak istediğinizden emin misiniz?`)) {
      return;
    }
    
    try {
      await removeUserFromRole(currentRole.id, userId);
      toast({
        title: "Başarılı",
        description: "Kullanıcı rolden çıkarıldı.",
        variant: "default",
      });
      
      // Update local list
      setUsersInRole(prev => prev.filter(user => user.id !== userId));
      
      // Refresh roles list for updated count
      fetchRoles();
    } catch (error) {
      console.error('Error removing user from role:', error);
      toast({
        title: "Hata",
        description: "Kullanıcı rolden çıkarılırken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  // Filter roles based on search term
  const filteredRoles = roles.filter(role => 
    role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    role.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (role.description && role.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Kullanıcı Rolleri Yönetimi</h1>
        <Button onClick={handleAddRole}>
          <Plus className="h-4 w-4 mr-2" />
          Yeni Rol Oluştur
        </Button>
      </div>
      
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle>Roller</CardTitle>
            <div className="flex items-center space-x-2">
              <div className="relative w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Rol ara..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Button variant="outline" size="sm" onClick={fetchRoles}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <CardDescription>
            Sistem ve özel rolleri yönetin
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            </div>
          ) : filteredRoles.length === 0 ? (
            <div className="text-center py-8">
              <Shield className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">
                {searchTerm ? "Arama kriterine uygun rol bulunamadı." : "Henüz tanımlanmış rol yok."}
              </p>
              {searchTerm && (
                <Button variant="outline" className="mt-2" onClick={() => setSearchTerm('')}>
                  Aramayı Temizle
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rol</TableHead>
                  <TableHead>İzinler</TableHead>
                  <TableHead>Kullanıcı Sayısı</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlemler</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRoles.map(role => (
                  <TableRow key={role.id}>
                    <TableCell>
                      <div className="font-medium">{role.name}</div>
                      <div className="text-sm text-gray-500">{role.id}</div>
                      {role.description && (
                        <div className="text-xs text-gray-500 mt-1">{role.description}</div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {role.permissions.map(perm => {
                          const permission = availablePermissions.find(p => p.id === perm);
                          return (
                            <Badge 
                              key={perm} 
                              variant="outline"
                              className="text-xs"
                              title={permission?.description || perm}
                            >
                              {permission?.name || perm}
                            </Badge>
                          );
                        })}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center">
                        <Users className="h-4 w-4 mr-1.5 text-gray-500" />
                        <span>{role.user_count}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {role.is_system_role ? (
                        <Badge className="bg-blue-500">Sistem Rolü</Badge>
                      ) : (
                        <Badge variant="outline">Özel Rol</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end space-x-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleViewUsers(role)}
                          title="Kullanıcıları Görüntüle"
                        >
                          <Users className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleEditRole(role)}
                          title="Düzenle"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleDeleteRole(role.id)}
                          title="Sil"
                          disabled={role.is_system_role}
                        >
                          <Trash2 className={`h-4 w-4 ${role.is_system_role ? 'text-gray-300' : 'text-red-500'}`} />
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
          Son güncelleme: {new Date('2025-05-16T13:35:47Z').toLocaleString()} • Kullanıcı: Teeksss
        </CardFooter>
      </Card>
      
      {/* Role Form Dialog */}
      <Dialog open={isRoleDialogOpen} onOpenChange={setIsRoleDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {currentRole ? 'Rolü Düzenle' : 'Yeni Rol Oluştur'}
            </DialogTitle>
            <DialogDescription>
              {currentRole 
                ? 'Mevcut rolü güncelleyin veya izinlerini değiştirin.' 
                : 'Özel bir rol oluşturun ve izinleri tanımlayın.'}
            </DialogDescription>
          </DialogHeader>
          
          <RoleForm 
            initialData={currentRole}
            onSubmit={handleSubmitRole}
            onCancel={() => setIsRoleDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
      
      {/* Users in Role Dialog */}
      <Dialog open={isUsersDialogOpen} onOpenChange={setIsUsersDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              {currentRole?.name} Rolündeki Kullanıcılar
            </DialogTitle>
            <DialogDescription>
              Bu role atanmış tüm kullanıcıları görüntüleyin ve yönetin
            </DialogDescription>
          </DialogHeader>
          
          {isLoadingUsers ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            </div>
          ) : usersInRole.length === 0 ? (
            <div className="text-center py-8">
              <User className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">Bu rolde henüz kullanıcı yok.</p>
            </div>
          ) : (
            <div className="overflow-y-auto max-h-96">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Kullanıcı</TableHead>
                    <TableHead>E-posta</TableHead>
                    <TableHead>Son Giriş</TableHead>
                    <TableHead className="text-right">İşlemler</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {usersInRole.map(user => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex items-center">
                          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium mr-3">
                            {user.name[0].toUpperCase()}
                          </div>
                          <div>
                            <div className="font-medium">{user.name}</div>
                            <div className="text-xs text-gray-500">{user.id}</div>
                          </div>
                          {user.id === CURRENT_USER.username && (
                            <Badge className="ml-2 bg-blue-100 text-blue-800 text-xs">Siz</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>{new Date(user.last_login).toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleRemoveUserFromRole(user.id)}
                          disabled={user.id === CURRENT_USER.username && currentRole.id === 'admin'}
                          title={
                            user.id === CURRENT_USER.username && currentRole.id === 'admin'
                              ? "Kendi admin rolünüzü kaldıramazsınız"
                              : "Rolden Çıkar"
                          }
                        >
                          <Trash2 className={`h-4 w-4 ${
                            user.id === CURRENT_USER.username && currentRole.id === 'admin'
                              ? 'text-gray-300'
                              : 'text-red-500'
                          }`} />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          
          <DialogFooter className="flex justify-between items-center">
            <div className="text-xs text-gray-500">
              Toplam: {usersInRole.length} kullanıcı
            </div>
            <Button onClick={() => setIsUsersDialogOpen(false)}>
              Kapat
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Son güncelleme: 2025-05-16 13:35:47
// Güncelleyen: Teeksss

export default RoleManagementPage;