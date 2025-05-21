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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { AlertCircle, CheckCircle, Clock, XCircle, RefreshCw, Info } from 'lucide-react';
import { getAllPendingQueries, approveQuery, rejectQuery } from '@/api/queries';
import CodeEditor from '@/components/CodeEditor';

// Parsing the SQL query to highlight tables, columns, etc.
const highlightSQLComponents = (sqlQuery) => {
  if (!sqlQuery) return [];
  
  // Very basic highlighting - in real app this would be more sophisticated
  const keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'UPDATE', 'INSERT', 'DELETE', 'GROUP BY', 'ORDER BY', 'HAVING'];
  let highlightedText = sqlQuery;
  
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
    highlightedText = highlightedText.replace(regex, `<span class="text-blue-500 font-bold">$&</span>`);
  });
  
  return { __html: highlightedText };
};

const getRiskBadge = (riskLevel) => {
  switch (riskLevel.toLowerCase()) {
    case 'high':
      return <Badge className="bg-red-500">Yüksek Risk</Badge>;
    case 'medium':
      return <Badge className="bg-yellow-500">Orta Risk</Badge>;
    case 'low':
      return <Badge className="bg-green-500">Düşük Risk</Badge>;
    default:
      return <Badge className="bg-gray-500">Bilinmeyen</Badge>;
  }
};

const QueryApprovalCard = ({ query, onApprove, onReject, onRefresh }) => {
  const [powerbiOnly, setPowerbiOnly] = useState(false);
  const [serverRestrictions, setServerRestrictions] = useState([]);
  const [availableServers, setAvailableServers] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  useEffect(() => {
    // Fetch available servers
    // This would be a real API call in production
    setAvailableServers([
      { id: 'prod_finance', name: 'Finance Production' },
      { id: 'prod_hr', name: 'HR Production' },
      { id: 'prod_sales', name: 'Sales Production' },
      { id: 'reporting_dw', name: 'Reporting Data Warehouse' },
      { id: 'dev_sandbox', name: 'Development Sandbox' }
    ]);
    
    // Pre-select the target server if it exists
    if (query.target_server) {
      setServerRestrictions([query.target_server]);
    }
  }, [query]);
  
  const handleApprove = async () => {
    if (serverRestrictions.length === 0) {
      alert('Lütfen en az bir sunucu seçin');
      return;
    }
    
    setIsProcessing(true);
    try {
      await onApprove(query.id, {
        powerbiOnly,
        serverRestrictions
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleReject = async () => {
    setIsProcessing(true);
    try {
      await onReject(query.id);
    } finally {
      setIsProcessing(false);
    }
  };
  
  const toggleServer = (serverId) => {
    setServerRestrictions(prev => 
      prev.includes(serverId) 
        ? prev.filter(id => id !== serverId) 
        : [...prev, serverId]
    );
  };
  
  return (
    <Card className="mb-6 border-l-4 border-l-blue-500">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg">Sorgu #{query.id}</CardTitle>
            <CardDescription>
              Kullanıcı: <span className="font-medium">{query.username}</span> • 
              Sunucu: <span className="font-medium">{query.target_server}</span> •
              Gönderilme: <span className="font-medium">{new Date(query.created_at).toLocaleString()}</span>
            </CardDescription>
          </div>
          <div className="flex space-x-2">
            {getRiskBadge(query.analysis.risk_level)}
            <Badge className="bg-blue-500">{query.analysis.query_type.toUpperCase()}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="query">
          <TabsList>
            <TabsTrigger value="query">SQL Sorgusu</TabsTrigger>
            <TabsTrigger value="analysis">Analiz</TabsTrigger>
            <TabsTrigger value="permissions">İzinler</TabsTrigger>
          </TabsList>
          
          <TabsContent value="query">
            <div className="mt-2 mb-4">
              <CodeEditor
                value={query.sql_query}
                language="sql"
                readOnly={true}
                height="150px"
              />
            </div>
          </TabsContent>
          
          <TabsContent value="analysis">
            <div className="mt-4 space-y-4">
              <div>
                <h3 className="text-sm font-semibold mb-2">Tablolar</h3>
                <div className="flex flex-wrap gap-2">
                  {query.analysis.tables.map((table, i) => (
                    <Badge key={i} variant="outline" className="bg-gray-100">
                      {table}
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-semibold mb-2">Kolonlar</h3>
                <div className="flex flex-wrap gap-2">
                  {query.analysis.columns.map((column, i) => (
                    <Badge key={i} variant="outline" className="bg-gray-100">
                      {column}
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-semibold mb-2">Sorgu Özellikleri</h3>
                <div className="grid grid-cols-3 gap-2">
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${query.analysis.has_where ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="text-sm">WHERE koşulu</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${query.analysis.has_limit ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="text-sm">LIMIT koşulu</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${query.analysis.has_join ? 'bg-green-500' : 'bg-gray-500'}`}></div>
                    <span className="text-sm">JOIN içeriyor</span>
                  </div>
                </div>
              </div>
              
              {query.analysis.sensitive_operations.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-2 text-red-500">Hassas İşlemler</h3>
                  <ul className="list-disc pl-5 text-red-500">
                    {query.analysis.sensitive_operations.map((op, i) => (
                      <li key={i}>{op}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </TabsContent>
          
          <TabsContent value="permissions">
            <div className="mt-4 space-y-4">
              <div className="flex items-center space-x-2">
                <Switch 
                  id="powerbi-only" 
                  checked={powerbiOnly} 
                  onCheckedChange={setPowerbiOnly}
                />
                <Label htmlFor="powerbi-only">Sadece PowerBI</Label>
                <Info className="h-4 w-4 text-gray-400" title="Bu sorgu sadece PowerBI kullanıcıları tarafından çalıştırılabilir." />
              </div>
              
              <div>
                <h3 className="text-sm font-semibold mb-2">İzin Verilen Sunucular</h3>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {availableServers.map(server => (
                    <div 
                      key={server.id} 
                      className={`p-2 border rounded cursor-pointer flex items-center space-x-2
                        ${serverRestrictions.includes(server.id) ? 'bg-blue-50 border-blue-300' : 'bg-white'}
                      `}
                      onClick={() => toggleServer(server.id)}
                    >
                      <div className={`w-3 h-3 rounded-full ${serverRestrictions.includes(server.id) ? 'bg-blue-500' : 'bg-gray-200'}`}></div>
                      <span>{server.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          onClick={onRefresh}
          disabled={isProcessing}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Yenile
        </Button>
        <div className="space-x-2">
          <Button 
            variant="destructive" 
            onClick={handleReject}
            disabled={isProcessing}
          >
            <XCircle className="h-4 w-4 mr-2" />
            Reddet
          </Button>
          <Button 
            onClick={handleApprove}
            disabled={isProcessing || serverRestrictions.length === 0}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Onayla
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};

const QueryApprovalPage = () => {
  const [pendingQueries, setPendingQueries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();
  
  const fetchPendingQueries = async () => {
    setIsLoading(true);
    try {
      const data = await getAllPendingQueries();
      setPendingQueries(data);
    } catch (error) {
      console.error('Error fetching pending queries:', error);
      toast({
        title: "Hata",
        description: "Bekleyen sorgular yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchPendingQueries();
    
    // Poll for new queries every 30 seconds
    const interval = setInterval(fetchPendingQueries, 30000);
    return () => clearInterval(interval);
  }, []);
  
  const handleApprove = async (queryId, options) => {
    try {
      await approveQuery(queryId, options);
      toast({
        title: "Başarılı",
        description: "Sorgu başarıyla onaylandı.",
        variant: "default",
      });
      
      // Remove the approved query from the list
      setPendingQueries(prev => prev.filter(q => q.id !== queryId));
    } catch (error) {
      console.error('Error approving query:', error);
      toast({
        title: "Hata",
        description: "Sorgu onaylanırken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  const handleReject = async (queryId) => {
    try {
      await rejectQuery(queryId);
      toast({
        title: "Bilgi",
        description: "Sorgu reddedildi.",
        variant: "default",
      });
      
      // Remove the rejected query from the list
      setPendingQueries(prev => prev.filter(q => q.id !== queryId));
    } catch (error) {
      console.error('Error rejecting query:', error);
      toast({
        title: "Hata",
        description: "Sorgu reddedilirken bir hata oluştu.",
        variant: "destructive",
      });
    }
  };
  
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">Sorgu Onay Paneli</h1>
      
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
        </div>
      ) : pendingQueries.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-6">
            <Clock className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-600">Bekleyen sorgu yok</p>
            <p className="text-sm text-gray-500 mt-1">
              Tüm sorgular onaylandı. Yeni sorgular geldiğinde burada görünecek.
            </p>
            <Button variant="outline" onClick={fetchPendingQueries} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Yenile
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div>
          <div className="mb-4 flex justify-between items-center">
            <p className="text-sm text-gray-500">
              {pendingQueries.length} bekleyen sorgu bulundu
            </p>
            <Button variant="outline" size="sm" onClick={fetchPendingQueries}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Yenile
            </Button>
          </div>
          
          {pendingQueries.map(query => (
            <QueryApprovalCard
              key={query.id}
              query={query}
              onApprove={handleApprove}
              onReject={handleReject}
              onRefresh={fetchPendingQueries}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default QueryApprovalPage;