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
import { 
  ChevronLeft, 
  ChevronRight,
  Clock,
  Copy,
  Download,
  Eye,
  Filter,
  RefreshCw,
  Search,
  Server,
  PlayCircle
} from 'lucide-react';
import { 
  Table, 
  TableBody, 
  TableCaption, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { getUserQueryHistory } from '@/api/queries';
import CodeEditor from '@/components/CodeEditor';
import { useNavigate } from 'react-router-dom';

const HistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [serverFilter, setServerFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const { toast } = useToast();
  const navigate = useNavigate();
  
  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      // Mock data for demo
      const mockData = {
        total: 75,
        queries: Array.from({ length: 25 }, (_, i) => ({
          id: i + 1 + (page - 1) * pageSize,
          sql_query: i % 3 === 0 
            ? "SELECT * FROM customers WHERE region = 'EU' ORDER BY revenue DESC LIMIT 100" 
            : i % 3 === 1 
              ? "SELECT product_id, SUM(quantity) as total_quantity FROM orders GROUP BY product_id HAVING SUM(quantity) > 100" 
              : "SELECT e.employee_name, d.department_name FROM employees e JOIN departments d ON e.dept_id = d.id WHERE e.hire_date > '2024-01-01'",
          execution_status: i % 5 === 0 ? 'error' : i % 7 === 0 ? 'rejected' : 'success',
          target_server: i % 4 === 0 ? 'prod_finance' : i % 4 === 1 ? 'prod_sales' : i % 4 === 2 ? 'reporting_dw' : 'dev_sandbox',
          created_at: new Date(new Date('2025-05-16 12:55:49').getTime() - (i * 24 * 60 * 60 * 1000)).toISOString(),
          rows_affected: i % 5 === 0 ? null : Math.floor(Math.random() * 1000),
          execution_time_ms: i % 5 === 0 ? null : Math.floor(Math.random() * 1000 + 50),
          error_message: i % 5 === 0 
            ? "Error: Column 'unknown_column' does not exist" 
            : i % 7 === 0 
              ? "Query needs admin approval before execution" 
              : null
        }))
      };
      
      // Apply filters (in real app, these would be sent to the backend)
      let filteredQueries = [...mockData.queries];
      
      if (serverFilter) {
        filteredQueries = filteredQueries.filter(q => q.target_server === serverFilter);
      }
      
      if (statusFilter) {
        filteredQueries = filteredQueries.filter(q => q.execution_status === statusFilter);
      }
      
      setHistory(filteredQueries);
      setTotalCount(mockData.total);
    } catch (error) {
      console.error('Error fetching query history:', error);
      toast({
        title: "Hata",
        description: "Sorgu geçmişi yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchHistory();
  }, [page, pageSize]);
  
  const handleViewQuery = (query) => {
    setSelectedQuery(query);
    setIsViewDialogOpen(true);
  };
  
  const handleRerunQuery = (query) => {
    // Store the query in session storage
    sessionStorage.setItem('rerunQuery', JSON.stringify({
      sql: query.sql_query,
      server: query.target_server
    }));
    
    // Navigate to dashboard
    navigate('/dashboard');
  };
  
  const handleCopyQuery = (query) => {
    navigator.clipboard.writeText(query.sql_query).then(() => {
      toast({
        title: "Kopyalandı",
        description: "Sorgu metni panoya kopyalandı.",
        variant: "default",
      });
    });
  };
  
  const applyFilters = () => {
    setPage(1); // Reset to first page when filters change
    fetchHistory();
  };
  
  const resetFilters = () => {
    setServerFilter('');
    setStatusFilter('');
    setPage(1);
    fetchHistory();
  };
  
  const getStatusBadge = (status) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-500">Başarılı</Badge>;
      case 'error':
        return <Badge className="bg-red-500">Hata</Badge>;
      case 'rejected':
        return <Badge className="bg-orange-500">Reddedildi</Badge>;
      default:
        return <Badge className="bg-gray-500">{status}</Badge>;
    }
  };
  
  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('tr-TR');
  };
  
  const totalPages = Math.ceil(totalCount / pageSize);
  
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">Sorgu Geçmişi</h1>
      
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filtreler</CardTitle>
          <CardDescription>
            Geçmiş sorgularınızı filtrelemek için aşağıdaki kriterleri kullanın
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="server">Sunucu</Label>
              <Select
                value={serverFilter}
                onValueChange={setServerFilter}
              >
                <SelectTrigger id="server">
                  <SelectValue placeholder="Sunucu seçin" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tümü</SelectItem>
                  <SelectItem value="prod_finance">Finance Production</SelectItem>
                  <SelectItem value="prod_sales">Sales Production</SelectItem>
                  <SelectItem value="reporting_dw">Reporting Data Warehouse</SelectItem>
                  <SelectItem value="dev_sandbox">Development Sandbox</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="status">Durum</Label>
              <Select
                value={statusFilter}
                onValueChange={setStatusFilter}
              >
                <SelectTrigger id="status">
                  <SelectValue placeholder="Durum seçin" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tümü</SelectItem>
                  <SelectItem value="success">Başarılı</SelectItem>
                  <SelectItem value="error">Hata</SelectItem>
                  <SelectItem value="rejected">Reddedildi</SelectItem>
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
              <CardTitle>Sorgu Geçmişi</CardTitle>
              <CardDescription>
                Teeksss kullanıcısının önceden çalıştırdığı sorgular
              </CardDescription>
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm" onClick={fetchHistory}>
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
          ) : history.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">Henüz sorgu çalıştırmadınız.</p>
              <p className="text-sm text-gray-400">Sorgularınızı sorgu panelinden çalıştırabilirsiniz.</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Sorgu</TableHead>
                      <TableHead>Sunucu</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead>Tarih</TableHead>
                      <TableHead>Etkilenen</TableHead>
                      <TableHead className="text-right">İşlemler</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {history.map(query => (
                      <TableRow key={query.id}>
                        <TableCell className="max-w-md">
                          <div className="truncate text-sm">
                            {query.sql_query}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center">
                            <Server className="h-4 w-4 mr-1.5 text-gray-500" />
                            <span>{query.target_server}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(query.execution_status)}
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            {formatDateTime(query.created_at)}
                          </div>
                        </TableCell>
                        <TableCell>
                          {query.rows_affected !== null ? (
                            <span>{query.rows_affected} satır</span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end space-x-1">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleViewQuery(query)}
                              title="Detayları Görüntüle"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleCopyQuery(query)}
                              title="Sorguyu Kopyala"
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleRerunQuery(query)}
                              title="Tekrar Çalıştır"
                            >
                              <PlayCircle className="h-4 w-4" />
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
              {formatDateTime(selectedQuery?.created_at)} tarihinde çalıştırılan sorgu
            </DialogDescription>
          </DialogHeader>
          
          {selectedQuery && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium mb-1">Sunucu</h4>
                  <div className="flex items-center">
                    <Server className="h-4 w-4 mr-1.5 text-gray-500" />
                    <span>{selectedQuery.target_server}</span>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium mb-1">Durum</h4>
                  <div>{getStatusBadge(selectedQuery.execution_status)}</div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium mb-1">Çalışma Süresi</h4>
                  <div className="text-sm">
                    {selectedQuery.execution_time_ms ? `${selectedQuery.execution_time_ms} ms` : '-'}
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium mb-1">Etkilenen Satır</h4>
                  <div className="text-sm">
                    {selectedQuery.rows_affected !== null ? selectedQuery.rows_affected : '-'}
                  </div>
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
              
              {selectedQuery.error_message && (
                <div>
                  <h4 className="text-sm font-medium mb-1 text-red-500">Hata Mesajı</h4>
                  <div className="p-3 bg-red-50 rounded-md text-red-800 text-sm">
                    {selectedQuery.error_message}
                  </div>
                </div>
              )}
              
              <DialogFooter>
                <Button 
                  variant="outline"
                  onClick={() => handleCopyQuery(selectedQuery)}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Sorguyu Kopyala
                </Button>
                <Button
                  onClick={() => {
                    handleRerunQuery(selectedQuery);
                    setIsViewDialogOpen(false);
                  }}
                >
                  <PlayCircle className="h-4 w-4 mr-2" />
                  Tekrar Çalıştır
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HistoryPage;