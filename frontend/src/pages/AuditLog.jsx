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
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import SQLHighlight from '@/components/SQLHighlight';
import { 
  Check, 
  CheckCircle, 
  Clock, 
  Database,
  Download,
  Eye, 
  FileDown, 
  Filter, 
  Info, 
  RefreshCw, 
  Search, 
  Server, 
  User, 
  X, 
  XCircle 
} from 'lucide-react';
import { format } from 'date-fns';
import { getAuditLogs, exportAuditLogs } from '@/api/audit';
import { CURRENT_USER, CURRENT_DATETIME, STATUS_COLORS } from '@/utils/constants';

// Query type badge component
const QueryTypeBadge = ({ type }) => {
  const colors = {
    'read': 'bg-green-500',
    'write': 'bg-orange-500',
    'ddl': 'bg-red-500',
    'procedure': 'bg-purple-500',
    'unknown': 'bg-gray-500'
  };
  
  const labels = {
    'read': 'SELECT',
    'write': 'WRITE',
    'ddl': 'DDL',
    'procedure': 'PROC',
    'unknown': 'UNKNOWN'
  };
  
  return (
    <Badge className={colors[type] || colors.unknown}>
      {labels[type] || labels.unknown}
    </Badge>
  );
};

// Status badge component
const StatusBadge = ({ status }) => {
  const colors = {
    'success': 'bg-green-500',
    'error': 'bg-red-500',
    'rejected': 'bg-orange-500',
    'pending': 'bg-yellow-500'
  };
  
  return (
    <Badge className={colors[status] || 'bg-gray-500'}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
};

// Date range picker component
const DateRangePicker = ({ startDate, endDate, onStartDateChange, onEndDateChange }) => {
  return (
    <div className="flex items-center space-x-2">
      <div className="grid gap-1.5">
        <Label htmlFor="from">Başlangıç</Label>
        <Popover>
          <PopoverTrigger asChild>
            <Button
              id="from"
              variant={"outline"}
              className={`w-[150px] justify-start text-left font-normal ${
                !startDate && "text-muted-foreground"
              }`}
            >
              <Calendar className="mr-2 h-4 w-4" />
              {startDate ? format(startDate, "dd.MM.yyyy") : "Bir tarih seçin"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar
              mode="single"
              selected={startDate}
              onSelect={onStartDateChange}
              initialFocus
            />
          </PopoverContent>
        </Popover>
      </div>
      
      <div className="grid gap-1.5">
        <Label htmlFor="to">Bitiş</Label>
        <Popover>
          <PopoverTrigger asChild>
            <Button
              id="to"
              variant={"outline"}
              className={`w-[150px] justify-start text-left font-normal ${
                !endDate && "text-muted-foreground"
              }`}
            >
              <Calendar className="mr-2 h-4 w-4" />
              {endDate ? format(endDate, "dd.MM.yyyy") : "Bir tarih seçin"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar
              mode="single"
              selected={endDate}
              onSelect={onEndDateChange}
              initialFocus
            />
          </PopoverContent>
        </Popover>
      </div>
    </div>
  );
};

// Log details dialog component
const LogDetailsDialog = ({ log, isOpen, onClose }) => {
  if (!log) return null;
  
  // Format execution time
  const formattedTime = log.execution_time_ms 
    ? `${log.execution_time_ms} ms (${(log.execution_time_ms / 1000).toFixed(2)} s)` 
    : 'N/A';
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <Clock className="h-5 w-5 mr-2" />
            Log #{log.id} Detayları
          </DialogTitle>
          <DialogDescription>
            Sorgu ve çalıştırma detaylarını görüntüleyin
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid grid-cols-2 gap-4 py-4">
          <div className="space-y-1">
            <Label>Kullanıcı</Label>
            <div className="flex items-center">
              <User className="h-4 w-4 text-gray-500 mr-2" />
              <span>
                {log.username} ({log.user_role})
              </span>
            </div>
          </div>
          
          <div className="space-y-1">
            <Label>IP Adresi</Label>
            <div className="text-sm">{log.client_ip || 'N/A'}</div>
          </div>
          
          <div className="space-y-1">
            <Label>Oluşturulma Zamanı</Label>
            <div className="text-sm">{new Date(log.created_at).toLocaleString()}</div>
          </div>
          
          <div className="space-y-1">
            <Label>Hedef Sunucu</Label>
            <div className="flex items-center">
              <Server className="h-4 w-4 text-gray-500 mr-2" />
              <span>{log.target_server}</span>
            </div>
          </div>
          
          <div className="space-y-1">
            <Label>Sorgu Tipi</Label>
            <div>
              <QueryTypeBadge type={log.query_type || 'unknown'} />
            </div>
          </div>
          
          <div className="space-y-1">
            <Label>Durum</Label>
            <div>
              <StatusBadge status={log.execution_status} />
            </div>
          </div>
          
          <div className="space-y-1">
            <Label>Çalışma Süresi</Label>
            <div className="text-sm">{formattedTime}</div>
          </div>
          
          <div className="space-y-1">
            <Label>Etkilenen Satır Sayısı</Label>
            <div className="text-sm">{log.rows_affected || 'N/A'}</div>
          </div>
        </div>
        
        <div className="space-y-2">
          <Label>SQL Sorgusu</Label>
          <SQLHighlight code={log.query_text} />
        </div>
        
        {log.error_message && (
          <div className="space-y-2 mt-4">
            <Label className="text-red-500">Hata Mesajı</Label>
            <div className="bg-red-50 p-3 rounded border border-red-200 text-red-700 text-sm">
              {log.error_message}
            </div>
          </div>
        )}
        
        {log.whitelist_id && (
          <div className="flex items-center text-sm text-gray-500 mt-2">
            <Info className="h-4 w-4 mr-1" />
            Bu sorgu whitelist'te bulunuyor (ID: {log.whitelist_id})
          </div>
        )}
        
        <DialogFooter>
          <Button onClick={onClose}>
            Kapat
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

const AuditLogPage = () => {
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState({
    username: '',
    server: '',
    status: '',
    query_type: '',
    startDate: null,
    endDate: null,
    page: 1,
    limit: 50
  });
  const [totalLogs, setTotalLogs] = useState(0);
  const [selectedLog, setSelectedLog] = useState(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const { toast } = useToast();
  
  // Fetch logs based on filters
  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      // Convert dates to ISO strings for API
      const apiFilters = {
        ...filters,
        startDate: filters.startDate ? filters.startDate.toISOString() : undefined,
        endDate: filters.endDate ? filters.endDate.toISOString() : undefined
      };
      
      const response = await getAuditLogs(apiFilters);
      setLogs(response.logs);
      setTotalLogs(response.total);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      toast({
        title: "Hata",
        description: "Audit loglar yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
      
      // Demo data
      const mockLogs = Array.from({ length: 50 }, (_, i) => ({
        id: 1000 + i,
        username: i % 5 === 0 ? 'Teeksss' : `user${i % 10}`,
        user_role: i % 5 === 0 ? 'admin' : (i % 3 === 0 ? 'analyst' : 'readonly'),
        client_ip: `192.168.1.${i % 255}`,
        query_text: `SELECT * FROM customers WHERE customer_id > ${i * 10} LIMIT 100`,
        query_hash: `hash${i}`,
        query_type: i % 4 === 0 ? 'write' : 'read',
        target_server: i % 3 === 0 ? 'prod_finance' : (i % 2 === 0 ? 'prod_hr' : 'reporting_dw'),
        execution_status: i % 7 === 0 ? 'error' : (i % 13 === 0 ? 'rejected' : 'success'),
        execution_time_ms: i * 50 + 20,
        rows_affected: i % 4 === 0 ? 0 : (i * 5 + 10),
        created_at: new Date(new Date('2025-05-16 13:40:50').getTime() - (i * 1000 * 60 * 10)).toISOString(),
        whitelist_id: i % 5 === 0 ? i + 100 : null,
        error_message: i % 7 === 0 ? 'ORA-00001: unique constraint violated' : null
      }));
      
      setLogs(mockLogs);
      setTotalLogs(500);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Initial load
  useEffect(() => {
    fetchLogs();
  }, [filters.page, filters.limit]);
  
  // Handle filter changes
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      // Reset to first page when filters change
      ...(key !== 'page' && key !== 'limit' ? { page: 1 } : {})
    }));
  };
  
  // Handle apply filters button
  const handleApplyFilters = () => {
    fetchLogs();
  };
  
  // Handle clear filters
  const handleClearFilters = () => {
    setFilters({
      username: '',
      server: '',
      status: '',
      query_type: '',
      startDate: null,
      endDate: null,
      page: 1,
      limit: 50
    });
    
    // Re-fetch with cleared filters
    setTimeout(() => {
      fetchLogs();
    }, 0);
  };
  
  // Handle log details view
  const handleViewLogDetails = (log) => {
    setSelectedLog(log);
    setIsDetailsOpen(true);
  };
  
  // Handle export to CSV
  const handleExportLogs = async () => {
    setIsExporting(true);
    try {
      // Convert dates to ISO strings for API
      const apiFilters = {
        ...filters,
        startDate: filters.startDate ? filters.startDate.toISOString() : undefined,
        endDate: filters.endDate ? filters.endDate.toISOString() : undefined,
        format: 'csv'
      };
      
      await exportAuditLogs(apiFilters);
      
      toast({
        title: "Başarılı",
        description: "Audit loglar CSV olarak indirildi.",
        variant: "default",
      });
    } catch (error) {
      console.error('Error exporting audit logs:', error);
      toast({
        title: "Hata",
        description: "Audit loglar export edilirken bir hata oluştu.",
        variant: "destructive",
      });
      
      // Demo CSV download
      const headers = [
        "ID", "User", "Role", "IP", "Query Type", "Server", 
        "Status", "Execution Time (ms)", "Rows", "Created At"
      ];
      
      const csvContent = [
        headers.join(','),
        ...logs.map(log => {
          return [
            log.id,
            log.username,
            log.user_role,
            log.client_ip,
            log.query_type,
            log.target_server,
            log.execution_status,
            log.execution_time_ms,
            log.rows_affected,
            new Date(log.created_at).toLocaleString()
          ].join(',');
        })
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_logs_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } finally {
      setIsExporting(false);
    }
  };
  
  // Handle pagination
  const handleNextPage = () => {
    if (filters.page * filters.limit < totalLogs) {
      handleFilterChange('page', filters.page + 1);
    }
  };
  
  const handlePrevPage = () => {
    if (filters.page > 1) {
      handleFilterChange('page', filters.page - 1);
    }
  };
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Audit Loglar</h1>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            onClick={handleExportLogs}
            disabled={isExporting}
          >
            {isExporting ? (
              <>
                <div className="animate-spin mr-2 h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                Export Ediliyor...
              </>
            ) : (
              <>
                <FileDown className="h-4 w-4 mr-2" />
                CSV Export
              </>
            )}
          </Button>
          <Button onClick={fetchLogs}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Yenile
          </Button>
        </div>
      </div>
      
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center">
            <Filter className="h-5 w-5 mr-2" />
            Filtreleme Seçenekleri
          </CardTitle>
          <CardDescription>
            Arama kriterlerinizi belirleyin
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="username">Kullanıcı</Label>
              <div className="relative">
                <User className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                <Input
                  id="username"
                  placeholder="Kullanıcı adı"
                  className="pl-9"
                  value={filters.username}
                  onChange={(e) => handleFilterChange('username', e.target.value)}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="server">Sunucu</Label>
              <Select 
                value={filters.server}
                onValueChange={(value) => handleFilterChange('server', value)}
              >
                <SelectTrigger id="server">
                  <SelectValue placeholder="Tüm sunucular" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tüm sunucular</SelectItem>
                  <SelectItem value="prod_finance">Finance Production</SelectItem>
                  <SelectItem value="prod_hr">HR Production</SelectItem>
                  <SelectItem value="prod_sales">Sales Production</SelectItem>
                  <SelectItem value="reporting_dw">Reporting DW</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="status">Durum</Label>
              <Select 
                value={filters.status}
                onValueChange={(value) => handleFilterChange('status', value)}
              >
                <SelectTrigger id="status">
                  <SelectValue placeholder="Tüm durumlar" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tüm durumlar</SelectItem>
                  <SelectItem value="success">Başarılı</SelectItem>
                  <SelectItem value="error">Hata</SelectItem>
                  <SelectItem value="rejected">Reddedildi</SelectItem>
                  <SelectItem value="pending">Beklemede</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="query_type">Sorgu Tipi</Label>
              <Select 
                value={filters.query_type}
                onValueChange={(value) => handleFilterChange('query_type', value)}
              >
                <SelectTrigger id="query_type">
                  <SelectValue placeholder="Tüm sorgu tipleri" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tüm sorgu tipleri</SelectItem>
                  <SelectItem value="read">SELECT</SelectItem>
                  <SelectItem value="write">WRITE</SelectItem>
                  <SelectItem value="ddl">DDL</SelectItem>
                  <SelectItem value="procedure">PROC</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2 md:col-span-2">
              <Label>Tarih Aralığı</Label>
              <DateRangePicker 
                startDate={filters.startDate}
                endDate={filters.endDate}
                onStartDateChange={(date) => handleFilterChange('startDate', date)}
                onEndDateChange={(date) => handleFilterChange('endDate', date)}
              />
            </div>
          </div>
          
          <div className="flex justify-between mt-4">
            <Button variant="outline" onClick={handleClearFilters}>
              <X className="h-4 w-4 mr-2" />
              Filtreleri Temizle
            </Button>
            
            <Button onClick={handleApplyFilters}>
              <Search className="h-4 w-4 mr-2" />
              Uygula
            </Button>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="pb-3">
          <CardTitle>Audit Log Kayıtları</CardTitle>
          <CardDescription>
            Toplamda {totalLogs} log kaydı bulundu, 
            şu anda {(filters.page - 1) * filters.limit + 1}-
            {Math.min(filters.page * filters.limit, totalLogs)} arası görüntüleniyor.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12">
              <Database className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">
                Belirtilen kriterlere uygun log kaydı bulunamadı.
              </p>
              <Button variant="outline" className="mt-4" onClick={handleClearFilters}>
                Filtreleri Temizle
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">ID</TableHead>
                    <TableHead>Kullanıcı</TableHead>
                    <TableHead>Sunucu</TableHead>
                    <TableHead>Sorgu Tipi</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead>Çalışma Süresi</TableHead>
                    <TableHead>Tarih</TableHead>
                    <TableHead className="text-right">İşlem</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map(log => (
                    <TableRow key={log.id}>
                      <TableCell className="font-medium">{log.id}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <span>{log.username}</span>
                          <Badge variant="outline" className="text-xs">
                            {log.user_role}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>{log.target_server}</TableCell>
                      <TableCell>
                        <QueryTypeBadge type={log.query_type} />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={log.execution_status} />
                      </TableCell>
                      <TableCell>
                        {log.execution_time_ms ? `${log.execution_time_ms} ms` : 'N/A'}
                      </TableCell>
                      <TableCell>
                        {new Date(log.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleViewLogDetails(log)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-between border-t pt-3">
          <div className="text-xs text-gray-500">
            Son güncelleme: {new Date('2025-05-16 13:40:50').toLocaleString()} • Kullanıcı: Teeksss
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrevPage}
              disabled={filters.page <= 1}
            >
              Önceki
            </Button>
            <span className="text-sm">
              Sayfa {filters.page} / {Math.ceil(totalLogs / filters.limit)}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleNextPage}
              disabled={filters.page * filters.limit >= totalLogs}
            >
              Sonraki
            </Button>
          </div>
        </CardFooter>
      </Card>
      
      {/* Log details dialog */}
      <LogDetailsDialog 
        log={selectedLog}
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
      />
    </div>
  );
};

// Son güncelleme: 2025-05-16 13:40:50
// Güncelleyen: Teeksss

export default AuditLogPage;