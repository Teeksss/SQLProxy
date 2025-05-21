import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { AlertCircle, EyeIcon, CheckCircle, BellRing, BarChart, ServerIcon, UserCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { tr } from 'date-fns/locale';

/**
 * Component for displaying anomaly alerts
 * 
 * @param {Object} props Component props
 * @param {Object} props.anomaly Anomaly alert data
 * @param {Function} props.onAcknowledge Callback when user acknowledges the anomaly
 * @param {Function} props.onResolve Callback when user resolves the anomaly
 * @param {Function} props.onView Callback when user views the anomaly details
 * @returns {JSX.Element} Anomaly alert card component
 */
const AnomalyAlertCard = ({ 
  anomaly, 
  onAcknowledge,
  onResolve,
  onView
}) => {
  const [expanded, setExpanded] = useState(false);
  
  if (!anomaly) return null;
  
  // Get severity level badge
  const getSeverityBadge = () => {
    switch (anomaly.severity) {
      case 'critical':
        return <Badge className="bg-red-600 hover:bg-red-700">Kritik</Badge>;
      case 'high':
        return <Badge className="bg-orange-500 hover:bg-orange-600">Yüksek</Badge>;
      case 'medium':
        return <Badge className="bg-yellow-500 hover:bg-yellow-600">Orta</Badge>;
      case 'low':
        return <Badge className="bg-blue-500 hover:bg-blue-600">Düşük</Badge>;
      default:
        return <Badge>Bilinmeyen</Badge>;
    }
  };
  
  // Get anomaly type icon and description
  const getAnomalyTypeInfo = () => {
    switch (anomaly.anomaly_type) {
      case 'query_volume':
        return {
          icon: <BarChart className="h-4 w-4 mr-1" />,
          label: 'Sorgu Hacmi Anomalisi'
        };
      case 'error_rate':
        return {
          icon: <AlertCircle className="h-4 w-4 mr-1" />,
          label: 'Hata Oranı Anomalisi'
        };
      case 'slow_query':
        return {
          icon: <ServerIcon className="h-4 w-4 mr-1" />,
          label: 'Yavaş Sorgu Anomalisi'
        };
      case 'unusual_time':
        return {
          icon: <BellRing className="h-4 w-4 mr-1" />,
          label: 'Olağandışı Zaman Anomalisi'
        };
      default:
        return {
          icon: <AlertCircle className="h-4 w-4 mr-1" />,
          label: `Anomali: ${anomaly.anomaly_type}`
        };
    }
  };
  
  // Format anomaly details for display
  const formatAnomalyDetails = () => {
    if (!anomaly.details) return null;
    
    const details = anomaly.details;
    
    // Different formatting based on anomaly type
    switch (anomaly.anomaly_type) {
      case 'query_volume':
        return (
          <>
            <div className="grid grid-cols-2 gap-2 mb-2">
              <div className="text-sm font-medium">Mevcut Sayı:</div>
              <div className="text-sm">{details.current_count}</div>
              
              <div className="text-sm font-medium">Geçmiş Sayı:</div>
              <div className="text-sm">{details.historical_count}</div>
              
              <div className="text-sm font-medium">Oran:</div>
              <div className="text-sm">{(details.ratio).toFixed(2)}x</div>
              
              <div className="text-sm font-medium">Eşik:</div>
              <div className="text-sm">{details.threshold}x</div>
              
              <div className="text-sm font-medium">Zaman Aralığı:</div>
              <div className="text-sm">{details.window} saniye</div>
            </div>
          </>
        );
      
      case 'error_rate':
        return (
          <>
            <div className="grid grid-cols-2 gap-2 mb-2">
              <div className="text-sm font-medium">Hata Oranı:</div>
              <div className="text-sm">{(details.error_rate * 100).toFixed(2)}%</div>
              
              <div className="text-sm font-medium">Hata Sayısı:</div>
              <div className="text-sm">{details.error_queries} / {details.total_queries}</div>
              
              <div className="text-sm font-medium">Eşik:</div>
              <div className="text-sm">{(details.threshold * 100).toFixed(2)}%</div>
              
              <div className="text-sm font-medium">Zaman Aralığı:</div>
              <div className="text-sm">{details.window} saniye</div>
            </div>
          </>
        );
      
      case 'slow_query':
        return (
          <>
            <div className="grid grid-cols-2 gap-2 mb-2">
              <div className="text-sm font-medium">Sorgu Tipi:</div>
              <div className="text-sm">{details.query_type}</div>
              
              <div className="text-sm font-medium">Çalışma Süresi:</div>
              <div className="text-sm">{details.execution_time.toFixed(2)} ms</div>
              
              <div className="text-sm font-medium">Ortalama Süre:</div>
              <div className="text-sm">{details.avg_execution_time.toFixed(2)} ms</div>
              
              <div className="text-sm font-medium">Oran:</div>
              <div className="text-sm">{details.ratio.toFixed(2)}x</div>
            </div>
          </>
        );
      
      case 'unusual_time':
        return (
          <>
            <div className="grid grid-cols-2 gap-2 mb-2">
              <div className="text-sm font-medium">Erişim Saati:</div>
              <div className="text-sm">{details.hour}:00</div>
              
              <div className="text-sm font-medium">Olağandışılık:</div>
              <div className="text-sm">{(details.unusualness * 100).toFixed(2)}%</div>
              
              <div className="text-sm font-medium">Eşik:</div>
              <div className="text-sm">{(details.threshold * 100).toFixed(2)}%</div>
            </div>
          </>
        );
      
      default:
        return (
          <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40 mt-2">
            {JSON.stringify(details, null, 2)}
          </pre>
        );
    }
  };
  
  const anomalyTypeInfo = getAnomalyTypeInfo();
  const createdAt = new Date(anomaly.created_at);
  const timeAgo = formatDistanceToNow(createdAt, { addSuffix: true, locale: tr });
  
  return (
    <Card className={`mb-4 ${anomaly.status === 'open' ? 'border-orange-300' : 'border-gray-200'}`}>
      <CardHeader className={`pb-3 ${anomaly.status === 'open' ? 'bg-orange-50' : 'bg-gray-50'}`}>
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            {anomalyTypeInfo.icon}
            <CardTitle className="text-base">{anomalyTypeInfo.label}</CardTitle>
          </div>
          {getSeverityBadge()}
        </div>
        <CardDescription className="flex flex-wrap items-center gap-2 mt-1">
          <div className="flex items-center gap-1">
            <UserCircle className="h-3 w-3" />
            <span>{anomaly.username}</span>
          </div>
          <div className="flex items-center gap-1">
            <ServerIcon className="h-3 w-3" />
            <span>{anomaly.target_server}</span>
          </div>
          <div className="text-xs text-gray-500">
            {timeAgo}
          </div>
        </CardDescription>
      </CardHeader>
      
      <CardContent className="pt-3">
        <div className="mb-3">
          <Badge variant="outline" className={`
            ${anomaly.status === 'open' ? 'border-orange-300 text-orange-700' : ''}
            ${anomaly.status === 'acknowledged' ? 'border-blue-300 text-blue-700' : ''}
            ${anomaly.status === 'resolved' ? 'border-green-300 text-green-700' : ''}
            ${anomaly.status === 'false_positive' ? 'border-gray-300 text-gray-700' : ''}
          `}>
            {anomaly.status === 'open' && 'Açık'}
            {anomaly.status === 'acknowledged' && 'Bildirimi Alındı'}
            {anomaly.status === 'resolved' && 'Çözüldü'}
            {anomaly.status === 'false_positive' && 'Yanlış Uyarı'}
          </Badge>
        </div>
        
        {formatAnomalyDetails()}
        
        <Accordion type="single" collapsible className="mt-3">
          <AccordionItem value="details" className="border-b-0">
            <AccordionTrigger className="py-2 text-sm">Detaylı Bilgi</AccordionTrigger>
            <AccordionContent>
              <div className="text-xs space-y-1 text-gray-700">
                <div><strong>ID:</strong> {anomaly.id}</div>
                <div><strong>Sorgu ID:</strong> {anomaly.query_id}</div>
                <div><strong>Sorgu Hash:</strong> {anomaly.query_hash}</div>
                <div><strong>Oluşturulma:</strong> {createdAt.toLocaleString()}</div>
                <div><strong>Durum:</strong> {anomaly.status}</div>
                <div><strong>Kullanıcı Rolü:</strong> {anomaly.user_role}</div>
                <div><strong>IP Adresi:</strong> {anomaly.client_ip}</div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
      
      <CardFooter className="flex justify-between pt-3 border-t gap-2">
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => onView && onView(anomaly)}
        >
          <EyeIcon className="h-4 w-4 mr-1" />
          İncele
        </Button>
        
        {anomaly.status === 'open' && (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => onAcknowledge && onAcknowledge(anomaly.id)}
            className="border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100"
          >
            <CheckCircle className="h-4 w-4 mr-1" />
            Bildir
          </Button>
        )}
        
        {anomaly.status !== 'resolved' && anomaly.status !== 'false_positive' && (
          <Button 
            variant="default" 
            size="sm" 
            onClick={() => onResolve && onResolve(anomaly.id)}
          >
            <CheckCircle className="h-4 w-4 mr-1" />
            Çözüldü
          </Button>
        )}
      </CardFooter>
    </Card>
  );
};

// Son güncelleme: 2025-05-20 10:00:16
// Güncelleyen: Teeksss

export default AnomalyAlertCard;