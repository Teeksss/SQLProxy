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
import { Checkbox } from '@/components/ui/checkbox';
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
  Table, 
  TableBody, 
  TableCaption, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  AlertCircle, 
  Database, 
  Plus, 
  RefreshCw, 
  Server, 
  Settings,
  Edit,
  Trash2
} from 'lucide-react';
import { 
  getServers, 
  createServer, 
  updateServer, 
  deleteServer, 
  testServerConnection 
} from '@/api/servers';

const ServerForm = ({ initialData = null, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    server_alias: '',
    description: '',
    server_host: '',
    server_port: 1433,
    database_name: '',
    is_active: true,
    allowed_roles: ['admin'],
    auto_approve_queries: false
  });
  
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const { toast } = useToast();
  
  // Available roles
  const availableRoles = [
    { id: 'admin', label: 'Admin' },
    { id: 'analyst', label: 'Analyst' },
    { id: 'powerbi', label: 'PowerBI' },
    { id: 'readonly', label: 'ReadOnly' }
  ];
  
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
  
  const handleRoleToggle = (role) => {
    setFormData(prev => {
      const currentRoles = [...prev.allowed_roles];
      
      if (currentRoles.includes(role)) {
        // Remove role
        return {
          ...prev,
          allowed_roles: currentRoles.filter(r => r !== role)
        };
      } else {
        // Add role
        return {
          ...prev,
          allowed_roles: [...currentRoles, role]
        };
      }
    });
  };
  
  const handleTestConnection = async () => {
    setIsTestingConnection(true);
    setTestResult(null);
    
    try {
      const result = await testServerConnection({
        host: formData.server_host,
        port: formData.server_port,
        database: formData.database_name
      });
      
      setTestResult({
        success: result.success,
        message: result.message
      });
      
      toast({
        title: result.success ? "Bağlantı Başarılı" : "Bağlantı Hatası",
        description: result.message,
        variant: result.success ? "default" : "destructive",
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: error.message || "Bağlantı testi sırasında bir hata oluştu."
      });
      
      toast({
        title: "Bağlantı Hatası",
        description: error.message || "Bağlantı testi sırasında bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsTestingConnection(false);
    }
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate required fields
    const requiredFields = ['server_alias', 'server_host', 'database_name'];
    const missingFields = requiredFields.filter(field => !formData[field]);
    
    if (missingFields.length > 0) {
      toast({
        title: "Eksik Bilgiler",
        description: "Lütfen tüm zorunlu alanları doldurun.",
        variant: "destructive",
      });
      return;
    }
    
    // At least admin role should be selected
    if (!formData.allowed_roles.includes('admin')) {
      toast({
        title: "Rol Hatası",
        description: "En az 'admin' rolü seçilmelidir.",
        variant: "destructive",
      });
      return;
    }
    
    onSubmit(formData);
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="server_alias" className="required">Sunucu Alias</Label>
          <Input 
            id="server_alias"
            value={formData.server_alias}
            onChange={(e) => handleChange('server_alias', e.target.value)}
            placeholder="prod_finance"
          />
          <p className="text-xs text-gray-500">
            Sistemde kullanılacak benzersiz tanımlayıcı
          </p>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="description">Açıklama</Label>
          <Input 
            id="description"
            value={formData.description || ''}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Finance Production Database"
          />
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="server_host" className="required">Sunucu Adresi</Label>
          <Input 
            id="server_host"
            value={formData.server_host}
            onChange={(e) => handleChange('server_host', e.target.value)}
            placeholder="db.example.com"
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="server_port" className="required">Port</Label>
          <Input 
            id="server_port"
            type="number"
            value={formData.server_port}
            onChange={(e) => handleChange('server_port', parseInt(e.target.value))}
            placeholder="1433"
          />
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="database_name" className="required">Veritabanı Adı</Label>
        <Input 
          id="database_name"
          value={formData.database_name}
          onChange={(e) => handleChange('database_name', e.target.value)}
          placeholder="finance_prod"
        />
      </div>
      
      <div className="space-y-2">
        <Label>İzin Verilen Roller</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {availableRoles.map(role => (
            <div key={role.id} className="flex items-center space-x-2">
              <Checkbox 
                id={`role-${role.id}`}
                checked={formData.allowed_roles.includes(role.id)}
                onCheckedChange={() => handleRoleToggle(role.id)}
                disabled={role.id === 'admin'} // Admin role always selected
              />
              <Label 
                htmlFor={`role-${role.id}`}
                className="text-sm font-normal"
              >
                {role.label}
              </Label>
            </div>
          ))}
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Checkbox 
            id="auto_approve_queries"
            checked={formData.auto_approve_queries}
            onCheckedChange={(checked) => handleChange('auto_approve_queries', checked)}
          />
          <Label htmlFor="auto_approve_queries" className="text-sm font-normal">
            Önceden onaylanmamış admin sorgularını otomatik onayla
          </Label>
        </div>
        <p className="text-xs text-red-500 ml-6">
          Güvenlik Uyarısı: Bu seçenek, admin kullanıcıların yeni sorgularını otomatik onaylayacaktır. Bu sadece geliştirme ve test ortamlarında önerilir.
        </p>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Checkbox 
            id="is_active"
            checked={formData.is_active}
            onCheckedChange={(checked) => handleChange('is_active', checked)}
          />
          <Label htmlFor="is_active" className="text-sm font-normal">
            Aktif
          </Label>
        </div>
        <p className="text-xs text-gray-500 ml-6">
          Pasif sunuculara bağlantı yapılamaz
        </p>
      </div>
      
      <div className="pt-2">
        <Button
          type="button"
          variant="outline"
          onClick={handleTestConnection}
          disabled={isTestingConnection}
        >
          {isTestingConnection ? (
            <>
              <div className="animate-spin mr-2 h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
              Test Ediliyor...
            </>
          ) : (
            <>
              <Database className="h-4 w-4 mr-2" />
              Bağlantıyı Test Et
            </>
          )}
        </Button>
        
        {testResult && (
          <div className={`mt-2 p-2 text-sm rounded-md ${
            testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {testResult.message}
          </div>
        )}
      </div>
      
      <DialogFooter className="pt-4">
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

const ServerManagementPage = () => {
  const [servers, setServers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [currentServer, setCurrentServer] = useState(null);
  const { toast } = useToast();
  
  const fetchServers = async () => {
    setIsLoading(true);
    try {
      const data = await getServers();
      setServers(data);
    } catch (error) {
      console.error('Error fetching servers:', error);
      toast({
        title: "Hata",
        description: "Sunucu listesi alınırken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchServers();
  }, []);
  
  const handleAddServer = () => {
    setCurrentServer(null);
    setIsDialogOpen(true);
  };
  
  const handleEditServer = (server) => {
    setCurrentServer(server);
    setIsDialogOpen(true);
  };
  
  const handleDeleteServer = async (serverId) => {
    if (!confirm('Bu sunucuyu silmek istediğinizden emin misiniz?')) {
      return;
    }
    
    try {
      await deleteServer(serverId);
      toast({
        title: "Başarılı",
        description: "Sunucu başarıyla silindi.",
        variant: "default",
      });
      
      // Refresh the list
      fetchServers();
    } catch (error) {
      console.error('Error deleting server:', error);
      toast({
        title: "Hata",
        description: error.message || "Sunucu silinirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleSubmitServer = async (formData) => {
    try {
      if (currentServer) {
        // Update existing server
        await updateServer(currentServer.id, formData);
        toast({
          title: "Başarılı",
          description: "Sunucu başarıyla güncellendi.",
          variant: "default",
        });
      } else {
        // Create new server
        await createServer(formData);
        toast({
          title: "Başarılı",
          description: "Sunucu başarıyla oluşturuldu.",
          variant: "default",
        });
      }
      
      // Close dialog and refresh list
      setIsDialogOpen(false);
      fetchServers();
    } catch (error) {
      console.error('Error saving server:', error);
      toast({
        title: "Hata",
        description: error.message || "Sunucu kaydedilirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Sunucu Yönetimi</h1>
        <Button onClick={handleAddServer}>
          <Plus className="h-4 w-4 mr-2" />
          Yeni Sunucu Ekle
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>SQL Sunucu Listesi</CardTitle>
          <CardDescription>
            Sisteme bağlanılacak sunucuları ve erişim izinlerini yönetin
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            </div>
          ) : servers.length === 0 ? (
            <div className="text-center py-8">
              <Server className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">Henüz tanımlanmış sunucu yok.</p>
              <Button variant="outline" onClick={handleAddServer} className="mt-4">
                <Plus className="h-4 w-4 mr-2" />
                Yeni Sunucu Ekle
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sunucu Alias</TableHead>
                  <TableHead>Açıklama</TableHead>
                  <TableHead>Bağlantı</TableHead>
                  <TableHead>İzinli Roller</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlemler</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {servers.map(server => (
                  <TableRow key={server.id}>
                    <TableCell className="font-medium">
                      {server.server_alias}
                    </TableCell>
                    <TableCell>
                      {server.description || '-'}
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div>{server.server_host}:{server.server_port}</div>
                        <div className="text-gray-500">{server.database_name}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {server.allowed_roles.map(role => (
                          <Badge key={role} variant="outline" className="text-xs">
                            {role}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      {server.is_active ? (
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
                          onClick={() => handleEditServer(server)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleDeleteServer(server.id)}
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
      
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {currentServer ? 'Sunucu Düzenle' : 'Yeni Sunucu Ekle'}
            </DialogTitle>
            <DialogDescription>
              {currentServer 
                ? 'Mevcut sunucuyu güncelleyin.' 
                : 'SQL Server sunucusu ekleyin ve izinleri yapılandırın.'}
            </DialogDescription>
          </DialogHeader>
          
          <ServerForm 
            initialData={currentServer}
            onSubmit={handleSubmitServer}
            onCancel={() => setIsDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ServerManagementPage;