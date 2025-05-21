import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  AlertTriangle,
  ArrowLeft,
  Database,
  Home,
  Search
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

const NotFound = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 px-4">
      <div className="text-center max-w-md">
        <div className="bg-red-100 p-3 rounded-full inline-flex items-center justify-center">
          <AlertTriangle className="h-8 w-8 text-red-600" />
        </div>
        
        <h1 className="mt-5 text-3xl font-bold text-gray-900">Sayfa Bulunamadı</h1>
        <p className="mt-3 text-gray-600">
          Aradığınız sayfaya erişilemiyor. Sayfa kaldırılmış, adı değişmiş veya geçici olarak kullanılamıyor olabilir.
        </p>
        
        <div className="mt-8 flex flex-col sm:flex-row justify-center space-y-3 sm:space-y-0 sm:space-x-3">
          <Button 
            variant="default" 
            onClick={() => navigate('/')}
            className="w-full sm:w-auto"
          >
            <Home className="h-4 w-4 mr-2" />
            Ana Sayfaya Git
          </Button>
          
          <Button 
            variant="outline" 
            onClick={() => navigate(-1)}
            className="w-full sm:w-auto"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Geri Dön
          </Button>
        </div>
        
        <div className="mt-10 border-t border-gray-200 pt-6">
          <div className="flex flex-col items-center">
            <Database className="h-5 w-5 text-blue-600 mb-2" />
            <p className="text-sm text-gray-500">
              SQL Proxy v1.0.1
            </p>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
              <Link to="/help" className="text-xs text-blue-600 hover:underline">Yardım</Link>
              <span className="text-xs text-gray-400">•</span>
              <Link to="/dashboard" className="text-xs text-blue-600 hover:underline">Dashboard</Link>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-8 text-xs text-gray-500">
        Son güncelleme: {new Date('2025-05-20 05:58:23').toLocaleString()} • Kullanıcı: Teeksss
      </div>
    </div>
  );
};

// Son güncelleme: 2025-05-20 05:58:23
// Güncelleyen: Teeksss

export default NotFound;