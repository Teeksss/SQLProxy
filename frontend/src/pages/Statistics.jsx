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
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  AlertTriangle,
  BarChart3,
  Calendar,
  Clock,
  Database,
  RefreshCw,
  Server,
  Users
} from 'lucide-react';
import { getStatistics } from '@/api/statistics';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const Statistics = () => {
  const [stats, setStats] = useState({
    loading: true,
    overview: {},
    queryTypes: [],
    timeDistribution: [],
    userActivity: [],
    serverUsage: [],
    errorRates: []
  });
  
  const [timeRange, setTimeRange] = useState('7d'); // 24h, 7d, 30d, 90d
  const { toast } = useToast();
  
  const fetchStatisticsData = async () => {
    setStats(prev => ({ ...prev, loading: true }));
    
    try {
      const data = await getStatistics(timeRange);
      setStats({
        loading: false,
        ...data
      });
    } catch (error) {
      console.error('Error fetching statistics:', error);
      toast({
        title: "Hata",
        description: "İstatistik verileri yüklenirken bir hata oluştu.",
        variant: "destructive",
      });
      
      // Mock data
      setStats({
        loading: false,
        overview: {
          totalQueries: 5248,
          successfulQueries: 4987,
          failedQueries: 261,
          averageExecutionTime: 245,
          uniqueUsers: 38
        },
        queryTypes: [
          { name: 'SELECT', value: 4123, percentage: 78.5 },
          { name: 'INSERT', value: 612, percentage: 11.7 },
          { name: 'UPDATE', value: 419, percentage: 8.0 },
          { name: 'DELETE', value: 69, percentage: 1.3 },
          { name: 'DDL', value: 25, percentage: 0.5 }
        ],
        timeDistribution: [
          { hour: '00', count: 42 },
          { hour: '01', count: 21 },
          { hour: '02', count: 15 },
          { hour: '03', count: 9 },
          { hour: '04', count: 12 },
          { hour: '05', count: 18 },
          { hour: '06', count: 32 },
          { hour: '07', count: 78 },
          { hour: '08', count: 198 },
          { hour: '09', count: 412 },
          { hour: '10', count: 489 },
          { hour: '11', count: 512 },
          { hour: '12', count: 398 },
          { hour: '13', count: 421 },
          { hour: '14', count: 521 },
          { hour: '15', count: 498 },
          { hour: '16', count: 479 },
          { hour: '17', count: 389 },
          { hour: '18', count: 294 },
          { hour: '19', count: 189 },
          { hour: '20', count: 132 },
          { hour: '21', count: 87 },
          { hour: '22', count: 64 },
          { hour: '23', count: 49 }
        ],
        userActivity: [
          { name: 'Teeksss', count: 512, percentage: 9.8 },
          { name: 'analyst1', count: 483, percentage: 9.2 },
          { name: 'data_scientist', count: 456, percentage: 8.7 },
          { name: 'powerbi_service', count: 421, percentage: 8.0 },
          { name: 'admin', count: 387, percentage: 7.4 }
        ],
        serverUsage: [
          { name: 'reporting_dw', count: 2142, percentage: 40.8 },
          { name: 'prod_finance', count: 1456, percentage: 27.7 },
          { name: 'prod_hr', count: 892, percentage: 17.0 },
          { name: 'prod_sales', count: 758, percentage: 14.5 }
        ],
        errorRates: [
          { date: '05/14', total: 712, errors: 32 },
          { date: '05/15', total: 689, errors: 29 },
          { date: '05/16', total: 745, errors: 41 },
          { date: '05/17', total: 780, errors: 38 },
          { date: '05/18', total: 794, errors: 35 },
          { date: '05/19', total: 801, errors: 46 },
          { date: '05/20', total: 727, errors: 40 }
        ]
      });
    }
  };
  
  useEffect(() => {
    fetchStatisticsData();
  }, [timeRange]);
  
  // Format for numbers
  const formatNumber = (num) => {
    return num.toLocaleString();
  };
  
  // Tooltip formatter for charts
  const tooltipFormatter = (value) => {
    return [formatNumber(value), 'Sorgu Sayısı'];
  };
  
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Sorgu İstatistikleri</h1>
        <div className="flex items-center space-x-2">
          <div className="bg-white border rounded-md p-1 flex">
            <Button 
              variant={timeRange === '24h' ? 'default' : 'ghost'} 
              size="sm"
              onClick={() => setTimeRange('24h')}
            >
              24 Saat
            </Button>
            <Button 
              variant={timeRange === '7d' ? 'default' : 'ghost'} 
              size="sm"
              onClick={() => setTimeRange('7d')}
            >
              7 Gün
            </Button>
            <Button 
              variant={timeRange === '30d' ? 'default' : 'ghost'} 
              size="sm"
              onClick={() => setTimeRange('30d')}
            >
              30 Gün
            </Button>
            <Button 
              variant={timeRange === '90d' ? 'default' : 'ghost'} 
              size="sm"
              onClick={() => setTimeRange('90d')}
            >
              90 Gün
            </Button>
          </div>
          <Button variant="outline" onClick={fetchStatisticsData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Yenile
          </Button>
        </div>
      </div>
      
      {/* Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-500">Toplam Sorgu</p>
                <h3 className="text-2xl font-bold mt-1">{formatNumber(stats.overview.totalQueries || 0)}</h3>
              </div>
              <div className="bg-blue-100 p-3 rounded-full">
                <Database className="h-5 w-5 text-blue-700" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-500">Başarılı Sorgu</p>
                <h3 className="text-2xl font-bold mt-1">{formatNumber(stats.overview.successfulQueries || 0)}</h3>
              </div>
              <div className="bg-green-100 p-3 rounded-full">
                <Badge className="bg-green-500">{stats.overview.successfulQueries ? Math.round((stats.overview.successfulQueries / stats.overview.totalQueries) * 100) : 0}%</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-500">Hatalı Sorgu</p>
                <h3 className="text-2xl font-bold mt-1">{formatNumber(stats.overview.failedQueries || 0)}</h3>
              </div>
              <div className="bg-red-100 p-3 rounded-full">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-500">Ort. Çalışma Süresi</p>
                <h3 className="text-2xl font-bold mt-1">{stats.overview.averageExecutionTime || 0} ms</h3>
              </div>
              <div className="bg-amber-100 p-3 rounded-full">
                <Clock className="h-5 w-5 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-500">Aktif Kullanıcı</p>
                <h3 className="text-2xl font-bold mt-1">{formatNumber(stats.overview.uniqueUsers || 0)}</h3>
              </div>
              <div className="bg-purple-100 p-3 rounded-full">
                <Users className="h-5 w-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Query Types Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Database className="h-5 w-5 mr-2" />
              Sorgu Tipleri Dağılımı
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
              </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={stats.queryTypes}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                    >
                      {stats.queryTypes.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value, name) => [formatNumber(value), name]} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Time Distribution Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Clock className="h-5 w-5 mr-2" />
              Saatlik Sorgu Dağılımı
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
              </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.timeDistribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip formatter={tooltipFormatter} />
                    <Bar dataKey="count" fill="#3b82f6" name="Sorgu Sayısı" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Top Users Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Users className="h-5 w-5 mr-2" />
              En Aktif Kullanıcılar
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
              </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={stats.userActivity}
                    layout="vertical"
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={80} />
                    <Tooltip formatter={tooltipFormatter} />
                    <Bar dataKey="count" fill="#8884d8" name="Sorgu Sayısı" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Server Usage Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Server className="h-5 w-5 mr-2" />
              Sunucu Kullanımı
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
              </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={stats.serverUsage}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                    >
                      {stats.serverUsage.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value, name) => [formatNumber(value), name]} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Error Rate Trend */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Günlük Hata Oranı Trendi
          </CardTitle>
        </CardHeader>
        <CardContent>
          {stats.loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            </div>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stats.errorRates}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value, name) => {
                    if (name === 'errorRate') {
                      return [`${value}%`, 'Hata Oranı'];
                    }
                    return [formatNumber(value), name === 'total' ? 'Toplam Sorgu' : 'Hatalı Sorgu'];
                  }} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="total" 
                    stroke="#3b82f6" 
                    name="Toplam Sorgu" 
                    strokeWidth={2}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="errors" 
                    stroke="#ef4444" 
                    name="Hatalı Sorgu" 
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey={(data) => ((data.errors / data.total) * 100).toFixed(1)}
                    stroke="#f59e0b"
                    name="Hata Oranı (%)"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
      
      <Card>
        <CardFooter className="border-t pt-4 flex justify-between">
          <div className="text-xs text-gray-500">
            Son güncelleme: {new Date('2025-05-20 05:40:32').toLocaleString()} • Kullanıcı: Teeksss
          </div>
          <div className="flex items-center space-x-1 text-xs text-gray-500">
            <Calendar className="h-3.5 w-3.5" />
            <span>{timeRange === '24h' ? 'Son 24 Saat' : timeRange === '7d' ? 'Son 7 Gün' : timeRange === '30d' ? 'Son 30 Gün' : 'Son 90 Gün'}</span>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

// Son güncelleme: 2025-05-20 05:40:32
// Güncelleyen: Teeksss

export default Statistics;