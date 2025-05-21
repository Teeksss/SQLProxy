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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
  ChevronLeft, 
  ChevronRight,
  CheckCircle, 
  Download, 
  Eye, 
  Filter, 
  RefreshCw, 
  Search, 
  Server,
  Trash2,
  Edit,
  Plus,
  ListFilter
} from 'lucide-react';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  getWhitelistedQueries, 
  updateWhitelistedQuery, 
  deleteWhitelistedQuery 
} from '@/api/queries';
import CodeEditor from '@/components/CodeEditor';

const WhitelistPage = () => {
  const [queries, setQueries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [queryTypeFilter, setQueryTypeFilter] = useState('');
  const [availableServers, setAvailableServers] = useState([
    { id: 'prod_finance', name: 'Finance Production' },
    { id: 'prod_hr', name: 'HR Production' },
    { id: 'prod_sales', name: 'Sales Production' },
    { id: 'reporting_dw', name: 'Reporting Data Warehouse' },
    { id: 'dev_sandbox', name: 'Development Sandbox' }
  ]);
  const [editFormData, setEditFormData] = useState({
    description: '',
    powerbi_only: false,
    server_restrictions: []
  });
  const { toast } = useToast();
  
  const fetchQueries = async () => {
    setIsLoading(true);
    try {
      // Prepare filter parameters
      const params = {
        page,
        limit: pageSize,
        search: searchTerm || undefined,
        query_type: queryTypeFilter || undefined
      };
      
      const data = await getWhitelistedQueries(params);
      
      setQueries(data.queries);
      setTotalCount(data.total);
    } catch (error) {
      console.error('Error fetching whitelisted queries:', error);
      toast({
        title: "Hata",
        description: "Sorgu beyaz listesi yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchQueries();
  }, [page, pageSize]);
  
  const handleViewQuery = (query) => {
    setSelectedQuery(query);
    setIsViewDialogOpen(true);
  };
  
  const handleEditQuery = (query) => {
    setSelectedQuery(query);
    setEditFormData({
      description: query.description || '',
      powerbi_only: query.powerbi_only || false,
      server_restrictions: query.server_restrictions || []
    });
    setIsEditDialogOpen(true);
  };
  
  const handleDeleteQuery = async (queryId) => {
    if (!confirm('Bu sorguyu beyaz listeden kaldırmak istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
      return;
    }
    
    try {
      await deleteWhitelistedQuery(queryId);
      toast({
        title: "Başarılı",
        description: "Sorgu beyaz listeden kaldırıldı.",
        variant: "default",
      });
      
      // Refresh the list
      fetchQueries();
    } catch (error) {
      console.error('Error deleting whitelisted query:', error);
      toast({
        title: "Hata",
        description: "Sorgu silinirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleSubmitEdit = async () => {
    try {
      await updateWhitelistedQuery(selectedQuery.id, editFormData);
      toast({
        title: "Başarılı",
        description: "Sorgu bilgileri güncellendi.",
        variant: "default",
      });
      
      setIsEditDialogOpen(false);
      fetchQueries();
    } catch (error) {
      console.error('Error updating whitelisted query:', error);
      toast({
        title: "Hata",
        description: "Sorgu güncellenirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleSearch = () => {
    setPage(1); // Reset to first page when search changes
    fetchQueries();
  };
  
  const applyFilters = () => {
    setPage(1); // Reset to first page when filters change
    fetchQueries();
  };
  
  const resetFilters = () => {
    setSearchTerm('');
    setQueryTypeFilter('');
    setPage(1);
    fetchQueries();
  };
  
  const toggleServer = (serverId) => {
    setEditFormData(prev => {
      const current = [...prev.server_restrictions];
      
      if (current.includes(serverId)) {
        // Remove server
        return {
          ...prev,
          server_restrictions: current.filter(id => id !== serverId)
        };
      } else {
        // Add server
        return {
          ...prev,
          server_restrictions: [...current, serverId]
        };
      }
    });
  };
  
  const getQueryTypeBadge = (type) => {
    switch (type) {
      case 'read':
        return <Badge className="bg-green-500">SELECT</Badge>;
      case 'write':
        return <Badge className="bg-orange-500">WRITE</Badge>;
      case 'ddl':
        return <Badge className="bg-red-500">DDL</Badge>;
      case 'procedure':
        return <Badge className="bg-purple-500">PROC</Badge>;
      default:
        return <Badge className="bg-gray-500">{type}</Badge>;
    }
  };
  
  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('tr-TR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const totalPages = Math.ceil(totalCount / pageSize);
  
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">Sorgu Beyaz Listesi</h1>
      
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filtreler</CardTitle>
          <CardDescription>
            Beyaz listedeki sorguları filtrelemek için aşağıdaki kriterleri kullanın
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="search">Sorgu İçinde Ara</Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                <Input
                  id="search"
                  placeholder="SQL sorgusu için arama yapın..."
                  className="pl-8"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="query_type">Sorgu Tipi</Label>
              <Select
                value={queryTypeFilter}
                onValueChange={(value) => setQueryTypeFilter(value)}
              >
                <SelectTrigger id="query_type">
                  <SelectValue placeholder="Tip seçin" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tümü</SelectItem>
                  <SelectItem value="read">SELECT</SelectItem>
                  <SelectItem value="write">WRITE</SelectItem>
                  <SelectItem value="ddl">DDL</SelectItem>
                  <SelectItem value="procedure">PROCEDURE</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex justify-end mt-4 space-x-2">
            <Button variant="outline" onClick={resetFilters}>
              Filtreleri Temizle
            </Button>
            <Button onClick={applyFilters}>
              <Filter className="h-4 w-4 mr-2" />
              Filtrele
            </Button>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>İzin Verilen Sorgular</CardTitle>
              <CardDescription>
                Onaylanmış ve otomatik çalıştırılabilen SQL sorguları
              </CardDescription>
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm" onClick={fetchQueries}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Yenile
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                CSV İndir
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            </div>
          ) : queries.length === 0 ? (
            <div className="text-center py-8">
              <ListFilter className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">Beyaz listede sorgu bulunamadı.</p>
              <p className="text-sm text-gray-400">Sorguları görmek için farklı filtreler deneyebilirsiniz.</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Sorgu</TableHead>
                      <TableHead>Tip</TableHead>
                      <TableHead>Onaylayan</TableHead>
                      <TableHead>Tarih</TableHead>
                      <TableHead>Özellikler</TableHead>
                      <TableHead className="text-right">İşlemler</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {queries.map(query => (
                      <TableRow key={query.id}>
                        <TableCell className="font-medium">{query.id}</TableCell>
                        <TableCell className="max-w-md">
                          <div className="truncate text-sm">
                            {query.sql_query}
                          </div>
                        </TableCell>
                        <TableCell>
                          {getQueryTypeBadge(query.query_type)}
                        </TableCell>
                        <TableCell>
                          {query.approved_by}
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            {formatDateTime(query.approved_at)}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {query.powerbi_only && (
                              <Badge className="bg-purple-500">PowerBI</Badge>
                            )}
                            {query.server_restrictions && query.server_restrictions.length > 0 && (
                              <Badge variant="outline" className="bg-blue-50">
                                {query.server_restrictions.length} Sunucu
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end space-x-1">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleViewQuery(query)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleEditQuery(query)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleDeleteQuery(query.id)}
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
              
              <div className="flex items-center justify-between mt-4 text-sm">
                <div className="text-gray-500">
                  Toplam {totalCount} sorgu, sayfa {page}/{totalPages}
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(prev => Math.max(prev - 1, 1))}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  
                  <Select
                    value={pageSize.toString()}
                    onValueChange={(value) => {
                      setPageSize(Number(value));
                      setPage(1);
                    }}
                  >
                    <SelectTrigger className="w-16">
                      <SelectValue placeholder={pageSize} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10</SelectItem>
                      <SelectItem value="25">25</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={page === totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
      
      {/* View Query Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Sorgu Detayları</DialogTitle>
            <DialogDescription>
              Beyaz liste sorgu #{selectedQuery?.id} detaylı bilgileri
            </DialogDescription>
          </DialogHeader>
          
          {selectedQuery && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium mb-1">Sorgu Tipi</h4>
                  <div>{getQueryTypeBadge(selectedQuery.query_type)}</div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium mb-1">PowerBI Özel</h4>
                  <div>
                    {selectedQuery.powerbi_only ? (
                      <Badge className="bg-purple-500">Evet</Badge>
                    ) : (
                      <Badge variant="outline">Hayır</Badge>
                    )}
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium mb-1">Onaylayan</h4>
                  <div className="text-sm">{selectedQuery.approved_by}</div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium mb-1">Onay Tarihi</h4>
                  <div className="text-sm">{formatDateTime(selectedQuery.approved_at)}</div>
                </div>
              </div>
              
              <div>
                <h4 className="text-sm font-medium mb-1">Açıklama</h4>
                <div className="text-sm p-2 bg-gray-50 rounded-md min-h-8">
                  {selectedQuery.description || 'Açıklama yok'}
                </div>
              </div>
              
              <div>
                <h4 className="text-sm font-medium mb-1">İzin Verilen Sunucular</h4>
                <div className="flex flex-wrap gap-1">
                  {selectedQuery.server_restrictions && selectedQuery.server_restrictions.length > 0 ? (
                    selectedQuery.server_restrictions.map(server => (
                      <Badge key={server} variant="outline" className="bg-blue-50">
                        {server}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-sm text-gray-500">Tüm sunucularda çalışabilir</span>
                  )}
                </div>
              </div>
              
              <div>
                <h4 className="text-sm font-medium mb-1">SQL Sorgusu</h4>
                <CodeEditor 
                  value={selectedQuery.sql_query}
                  language="sql"
                  readOnly={true}
                  height="150px"
                />
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* Edit Query Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sorgu Düzenle</DialogTitle>
            <DialogDescription>
              Beyaz liste sorgu #{selectedQuery?.id} bilgilerini güncelleyin
            </DialogDescription>
          </DialogHeader>
          
          {selectedQuery && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="description">Açıklama</Label>
                <Input 
                  id="description"
                  value={editFormData.description}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Bu sorgunun amacı veya kullanımı hakkında açıklama"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch 
                  id="powerbi_only" 
                  checked={editFormData.powerbi_only}
                  onCheckedChange={(checked) => setEditFormData(prev => ({ ...prev, powerbi_only: checked }))}
                />
                <Label htmlFor="powerbi_only">Sadece PowerBI</Label>
              </div>
              
              <div className="space-y-2">
                <Label>İzin Verilen Sunucular</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {availableServers.map(server => (
                    <div 
                      key={server.id} 
                      className={`p-2 border rounded cursor-pointer flex items-center space-x-2
                        ${editFormData.server_restrictions.includes(server.id) ? 'bg-blue-50 border-blue-300' : 'bg-white'}
                      `}
                      onClick={() => toggleServer(server.id)}
                    >
                      <div className={`w-3 h-3 rounded-full ${editFormData.server_restrictions.includes(server.id) ? 'bg-blue-500' : 'bg-gray-200'}`}></div>
                      <span>{server.name}</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500">
                  Hiçbir sunucu seçilmezse, bu sorgu tüm sunucularda çalışabilir.
                </p>
              </div>
              
              <div className="pt-2">
                <h4 className="text-sm font-medium mb-1">SQL Sorgusu (Salt Okunur)</h4>
                <CodeEditor 
                  value={selectedQuery.sql_query}
                  language="sql"
                  readOnly={true}
                  height="100px"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Not: SQL sorgu metni güvenlik nedeniyle düzenlenemez. Değişiklik gerekiyorsa yeni sorgu onayı gerekir.
                </p>
              </div>
              
              <DialogFooter className="mt-4">
                <Button 
                  variant="outline" 
                  onClick={() => setIsEditDialogOpen(false)}
                >
                  İptal
                </Button>
                <Button onClick={handleSubmitEdit}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Kaydet
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default WhitelistPage;