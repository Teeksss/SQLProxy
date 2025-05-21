import React, { useState, useEffect, useRef } from 'react';
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
  AlertCircle, 
  AlertTriangle, 
  ArrowRight, 
  Clock, 
  Code,
  Database, 
  Eye, 
  FileBadge, 
  FileDown, 
  Info, 
  PlayCircle, 
  RefreshCw, 
  Save, 
  Server, 
  Shield, 
  Sparkles
} from 'lucide-react';
import CodeMirror from '@uiw/react-codemirror';
import { sql } from '@codemirror/lang-sql';
import { vscodeDark } from '@uiw/codemirror-theme-vscode';
import { CSV } from 'csv-string';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { executeQuery, getServers } from '@/api/queries';
import { ROLE_COLORS, CURRENT_USER } from '@/utils/constants';

// Maskelenmiş veri gösterimi için özel hücre bileşeni
const MaskedDataCell = ({ value, isMasked }) => {
  if (!isMasked) {
    return <span>{value}</span>;
  }
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger className="cursor-help">
          <span className="bg-yellow-100 px-1.5 py-0.5 rounded text-yellow-800 font-mono">
            {value}
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-xs">Bu değer gizlilik nedeniyle maskelenmiştir</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// Sorgu çalıştırma zaman aşımı uyarısı bileşeni
const TimeoutWarning = ({ timeoutSeconds, elapsedSeconds, isVisible }) => {
  if (!isVisible) return null;
  
  const percentage = Math.min(100, (elapsedSeconds / timeoutSeconds) * 100);
  const isNearTimeout = percentage > 80;
  
  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <div className="flex items-center">
          <Clock className={`h-4 w-4 mr-1.5 ${isNearTimeout ? 'text-red-500' : 'text-amber-500'}`} />
          <span className={`text-sm font-medium ${isNearTimeout ? 'text-red-700' : 'text-amber-700'}`}>
            Sorgu çalışıyor: {Math.round(elapsedSeconds)} / {timeoutSeconds} saniye
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {isNearTimeout 
            ? 'Zaman aşımına yaklaşılıyor!' 
            : 'Sorgunuz çalıştırılıyor...'}
        </span>
      </div>
      <Progress value={percentage} className={isNearTimeout ? "bg-red-100" : "bg-amber-100"} 
        indicatorClassName={isNearTimeout ? "bg-red-500" : "bg-amber-500"} />
    </div>
  );
};

const Dashboard = () => {
  const [query, setQuery] = useState('SELECT * FROM customers WHERE region = \'EU\' LIMIT 10;');
  const [selectedServer, setSelectedServer] = useState('');
  const [servers, setServers] = useState([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState('csv');
  
  // Zaman aşımı izleme değişkenleri
  const [timeoutSeconds, setTimeoutSeconds] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isShowingTimeout, setIsShowingTimeout] = useState(false);
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);
  
  const { toast } = useToast();
  
  // Sunucuları yükleme
  useEffect(() => {
    const fetchServers = async () => {
      try {
        const data = await getServers();
        setServers(data);
        
        // Varsayılan sunucu seçimi
        if (data.length > 0 && !selectedServer) {
          setSelectedServer(data[0].server_alias);
        }
      } catch (error) {
        console.error('Error fetching servers:', error);
        toast({
          title: "Hata",
          description: "Sunucular yüklenirken bir hata oluştu.",
          variant: "destructive",
        });
        
        // Demo data
        const mockServers = [
          { 
            id: 1, 
            server_alias: 'prod_finance', 
            description: 'Finance Production Database',
            server_host: 'finance-db.example.com',
            allowed_roles: ['admin', 'analyst', 'powerbi']
          },
          { 
            id: 2, 
            server_alias: 'prod_hr', 
            description: 'HR Production Database',
            server_host: 'hr-db.example.com',
            allowed_roles: ['admin', 'hr_analyst']
          },
          { 
            id: 3, 
            server_alias: 'reporting_dw', 
            description: 'Reporting Data Warehouse',
            server_host: 'reporting-dw.example.com',
            allowed_roles: ['admin', 'analyst', 'powerbi', 'readonly']
          }
        ];
        
        setServers(mockServers);
        if (!selectedServer) {
          setSelectedServer(mockServers[0].server_alias);
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchServers();
  }, []);
  
  // Zaman aşımı izleme timer'ı
  useEffect(() => {
    if (isExecuting && timeoutSeconds > 0) {
      // Timer'ı başlat
      setIsShowingTimeout(true);
      startTimeRef.current = Date.now();
      
      // Her saniye elapsed time'ı güncelle
      timerRef.current = setInterval(() => {
        const elapsed = (Date.now() - startTimeRef.current) / 1000;
        setElapsedSeconds(elapsed);
      }, 1000);
      
      return () => {
        // Temizlik fonksiyonu
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        setIsShowingTimeout(false);
        setElapsedSeconds(0);
      };
    }
  }, [isExecuting, timeoutSeconds]);
  
  // Sorgu çalıştırma
  const handleExecuteQuery = async () => {
    if (!selectedServer) {
      toast({
        title: "Hata",
        description: "Lütfen bir sunucu seçin.",
        variant: "destructive",
      });
      return;
    }
    
    if (!query.trim()) {
      toast({
        title: "Hata",
        description: "Lütfen bir SQL sorgusu girin.",
        variant: "destructive",
      });
      return;
    }
    
    setIsExecuting(true);
    setError(null);
    setQueryResult(null);
    
    try {
      // Sorgu zaman aşımı değeri (rol bazlı)
      const roleTimeouts = {
        admin: 300,  // 5 dakika
        analyst: 120,  // 2 dakika
        powerbi: 60,  // 1 dakika
        readonly: 30   // 30 saniye
      };
      
      // Kullanıcının rolüne göre timeout değerini belirle
      setTimeoutSeconds(roleTimeouts[CURRENT_USER.role] || 60);
      
      const result = await executeQuery(selectedServer, query);
      setQueryResult(result);
      
      if (result.masked && result.masked_columns && result.masked_columns.length > 0) {
        toast({
          title: "Veri Maskeleme Uygulandı",
          description: `${result.masked_columns.length} sütundaki veriler güvenlik nedeniyle maskelenmiştir.`,
          variant: "default",
        });
      }
    } catch (error) {
      console.error('Query execution error:', error);
      
      if (error.response && error.response.status === 403) {
        // Onay gerektiren sorgu
        setError({
          type: 'approval',
          message: error.response.data.detail || 'Bu sorgu admin onayı gerektiriyor.'
        });
        
        toast({
          title: "Onay Gerekiyor",
          description: "Sorgunuz admin onayı için gönderildi. Onaylandıktan sonra tekrar çalıştırabilirsiniz.",
          variant: "default",
        });
      } else if (error.response && error.response.status === 429) {
        // Rate limit aşıldı
        setError({
          type: 'rate_limit',
          message: error.response.data.detail || 'Rate limit aşıldı. Lütfen daha sonra tekrar deneyin.'
        });
        
        toast({
          title: "Rate Limit Aşıldı",
          description: "Kısa süre içinde çok fazla sorgu çalıştırdınız. Lütfen bir süre bekleyin.",
          variant: "destructive",
        });
      } else if (error.message && error.message.includes('timeout')) {
        // Sorgu zaman aşımı
        setError({
          type: 'timeout',
          message: 'Sorgu zaman aşımına uğradı. Lütfen sorgunuzu optimize edin veya daha küçük sonuç setleri için filtreleme yapın.'
        });
        
        toast({
          title: "Zaman Aşımı",
          description: "Sorgunuz maksimum çalışma süresini aştı ve iptal edildi.",
          variant: "destructive",
        });
      } else {
        // Diğer hatalar
        setError({
          type: 'error',
          message: error.response?.data?.detail || error.message || 'Sorgu çalıştırılırken bir hata oluştu.'
        });
        
        toast({
          title: "Hata",
          description: "Sorgu çalıştırılırken bir hata oluştu.",
          variant: "destructive",
        });
      }
    } finally {
      setIsExecuting(false);
    }
  };
  
  // CSV olarak dışa aktarma
  const handleExportToCsv = () => {
    if (!queryResult || !queryResult.data || queryResult.data.length === 0) {
      toast({
        title: "Hata",
        description: "Dışa aktarılacak veri yok.",
        variant: "destructive",
      });
      return;
    }
    
    setIsExporting(true);
    
    try {
      const columns = queryResult.columns;
      const rows = queryResult.data.map(row => columns.map(col => row[col]));
      
      // CSV formatına çevir
      const csvContent = CSV.stringify([columns, ...rows]);
      
      // Download linki oluştur
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `query_result_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast({
        title: "Başarılı",
        description: "Sorgu sonuçları CSV olarak indirildi.",
        variant: "default",
      });
    } catch (error) {
      console.error('Error exporting to CSV:', error);
      toast({
        title: "Hata",
        description: "CSV dışa aktarılırken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  };
  
  // Sorgu değişikliği
  const handleQueryChange = React.useCallback((value) => {
    setQuery(value);
  }, []);
  
  // Sunucu değişikliği
  const handleServerChange = (value) => {
    setSelectedServer(value);
  };
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">SQL Sorgu Paneli</h1>
        <div className="flex items-center space-x-2">
          <Badge className={ROLE_COLORS[CURRENT_USER.role] || 'bg-gray-500'}>
            {CURRENT_USER.role.charAt(0).toUpperCase() + CURRENT_USER.role.slice(1)}
          </Badge>
        </div>
      </div>
      
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <div className="flex justify-between">
            <div>
              <CardTitle>SQL Sorgusu</CardTitle>
              <CardDescription>
                Çalıştırmak istediğiniz SQL sorgusunu yazın
              </CardDescription>
            </div>
            <div className="flex space-x-2">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="w-48">
                      <Select value={selectedServer} onValueChange={handleServerChange}>
                        <SelectTrigger className="w-full" disabled={isLoading || isExecuting}>
                          <SelectValue placeholder="Sunucu seçin" />
                        </SelectTrigger>
                        <SelectContent>
                          {servers.map(server => (
                            <SelectItem key={server.server_alias} value={server.server_alias}>
                              <div className="flex items-center">
                                <Server className="h-4 w-4 mr-2 text-gray-500" />
                                <div>
                                  <span>{server.server_alias}</span>
                                  {server.description && (
                                    <span className="text-xs text-gray-500 block">
                                      {server.description}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Sorgunun çalıştırılacağı veritabanı sunucusu</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              
              <Button 
                onClick={handleExecuteQuery} 
                disabled={isExecuting || isLoading || !selectedServer}
                className="whitespace-nowrap"
              >
                {isExecuting ? (
                  <>
                    <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Çalıştırılıyor...
                  </>
                ) : (
                  <>
                    <PlayCircle className="h-4 w-4 mr-2" />
                    Çalıştır
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Zaman aşımı uyarısı */}
          <TimeoutWarning 
            timeoutSeconds={timeoutSeconds} 
            elapsedSeconds={elapsedSeconds} 
            isVisible={isShowingTimeout} 
          />
          
          {/* SQL Editor */}
          <div className="border rounded-md">
            <CodeMirror
              value={query}
              height="200px"
              extensions={[sql()]}
              onChange={handleQueryChange}
              theme={vscodeDark}
              editable={!isExecuting}
              basicSetup={{
                lineNumbers: true,
                highlightActiveLineGutter: true,
                highlightSpecialChars: true,
                foldGutter: true,
                indentOnInput: true,
                syntaxHighlighting: true,
                bracketMatching: true,
                closeBrackets: true,
                autocompletion: true,
                rectangularSelection: true,
                crosshairCursor: true,
                highlightActiveLine: true,
                highlightSelectionMatches: true,
                closeBracketsKeymap: true,
                searchKeymap: true,
              }}
            />
          </div>
          
          {/* Hata mesajı */}
          {error && (
            <div className={`mt-4 p-3 rounded-md ${
              error.type === 'approval' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
              error.type === 'rate_limit' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
              'bg-red-50 text-red-700 border border-red-200'
            }`}>
              <div className="flex">
                {error.type === 'approval' ? (
                  <Shield className="h-5 w-5 mr-2 flex-shrink-0" />
                ) : error.type === 'rate_limit' ? (
                  <Clock className="h-5 w-5 mr-2 flex-shrink-0" />
                ) : error.type === 'timeout' ? (
                  <AlertTriangle className="h-5 w-5 mr-2 flex-shrink-0" />
                ) : (
                  <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
                )}
                <div>
                  <p className="font-medium">
                    {error.type === 'approval' ? 'Onay Gerekiyor' : 
                     error.type === 'rate_limit' ? 'Rate Limit Aşıldı' :
                     error.type === 'timeout' ? 'Sorgu Zaman Aşımı' : 'Sorgu Hatası'}
                  </p>
                  <p className="mt-1 text-sm">{error.message}</p>
                  
                  {error.type === 'approval' && (
                    <p className="mt-2 text-sm">
                      Yöneticiler sorgunuzu inceleyecek ve onaylarsa tekrar çalıştırabilirsiniz.
                    </p>
                  )}
                  
                  {error.type === 'timeout' && (
                    <div className="mt-2 text-sm">
                      <p>Öneriler:</p>
                      <ul className="list-disc list-inside mt-1">
                        <li>WHERE koşulları ekleyerek sonuç kümesini sınırlayın</li>
                        <li>LIMIT kullanarak dönüş satır sayısını azaltın</li>
                        <li>Sorgunuzu daha küçük parçalara bölün</li>
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Sorgu sonuçları */}
      {queryResult && queryResult.data && queryResult.data.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Sorgu Sonuçları</CardTitle>
                <CardDescription>
                  {queryResult.rowcount || queryResult.data.length} satır, {queryResult.execution_time_ms} ms'de çalıştırıldı
                </CardDescription>
              </div>
              <div className="flex space-x-2">
                <Button 
                  variant="outline" 
                  onClick={handleExportToCsv}
                  disabled={isExporting}
                >
                  {isExporting ? (
                    <>
                      <div className="animate-spin mr-2 h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                      İndiriliyor...
                    </>
                  ) : (
                    <>
                      <FileDown className="h-4 w-4 mr-2" />
                      CSV İndir
                    </>
                  )}
                </Button>
              </div>
            </div>
            
            {/* Maskeleme uyarısı */}
            {queryResult.masked && (
              <div className="flex items-start bg-yellow-50 border border-yellow-200 rounded-md p-2 mt-2">
                <FileBadge className="h-5 w-5 mr-2 text-yellow-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">
                    Veri Maskeleme Uygulandı
                  </p>
                  <p className="text-xs text-yellow-700 mt-1">
                    Yetkilerinize göre bazı hassas veriler maskelenmiştir. 
                    Maskelenen sütunlar: {queryResult.masked_columns.join(', ')}
                  </p>
                </div>
              </div>
            )}
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {queryResult.columns.map((column, index) => (
                      <TableHead key={index} className={
                        queryResult.masked_columns && queryResult.masked_columns.includes(column) 
                          ? "bg-yellow-50"
                          : ""
                      }>
                        {column}
                        {queryResult.masked_columns && queryResult.masked_columns.includes(column) && (
                          <span className="ml-1 text-yellow-500">
                            <FileBadge className="h-3 w-3 inline" />
                          </span>
                        )}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {queryResult.data.map((row, rowIndex) => (
                    <TableRow key={rowIndex}>
                      {queryResult.columns.map((column, colIndex) => (
                        <TableCell key={colIndex}>
                          <MaskedDataCell 
                            value={row[column] !== null ? row[column] : ''} 
                            isMasked={queryResult.masked_columns && queryResult.masked_columns.includes(column)}
                          />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
          <CardFooter className="border-t pt-3 text-xs text-gray-500">
            Son güncelleme: {new Date('2025-05-16 13:48:26').toLocaleString()} • Kullanıcı: Teeksss
          </CardFooter>
        </Card>
      )}
      
      {/* Sonuç yoksa */}
      {queryResult && queryResult.data && queryResult.data.length === 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Sorgu Sonuçları</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8">
              <Database className="h-12 w-12 text-gray-300" />
              <p className="mt-4 text-gray-500">Sorgu başarıyla çalıştırıldı, ancak sonuç döndürmedi.</p>
              <p className="text-sm text-gray-400 mt-1">
                Çalışma süresi: {queryResult.execution_time_ms} ms
              </p>
            </div>
          </CardContent>
          <CardFooter className="border-t pt-3 text-xs text-gray-500">
            Son güncelleme: {new Date('2025-05-16 13:48:26').toLocaleString()} • Kullanıcı: Teeksss
          </CardFooter>
        </Card>
      )}
    </div>
  );
};

// Son güncelleme: 2025-05-16 13:48:26
// Güncelleyen: Teeksss

export default Dashboard;