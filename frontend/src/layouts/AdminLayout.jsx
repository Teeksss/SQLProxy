import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  BarChart3, 
  Clock, 
  Database, 
  EyeOff,
  Gauge,
  HelpCircle,
  HourglassIcon,
  List,
  LogOut, 
  Menu,
  Server,
  Settings, 
  Shield, 
  Users,
  X
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import NotificationCenter from '@/components/NotificationCenter';
import SearchBox from '@/components/SearchBox';
import { logout, getUserInfo } from '@/utils/auth';
import { CURRENT_USER, CURRENT_DATETIME, SYSTEM_VERSION } from '@/utils/constants';

const AdminLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();
  const userInfo = getUserInfo() || CURRENT_USER;
  
  const navItems = [
    {
      title: 'Sorgu Paneli',
      icon: <Database className="h-5 w-5" />,
      path: '/admin/dashboard',
      badge: null
    },
    {
      title: 'Sorgu Onayları',
      icon: <Shield className="h-5 w-5" />,
      path: '/admin/query-approval',
      badge: 3
    },
    {
      title: 'Beyaz Liste',
      icon: <List className="h-5 w-5" />,
      path: '/admin/whitelist',
      badge: null
    },
    {
      title: 'Sunucular',
      icon: <Server className="h-5 w-5" />,
      path: '/admin/servers',
      badge: null
    },
    {
      title: 'Kullanıcı Rolleri',
      icon: <Users className="h-5 w-5" />,
      path: '/admin/roles',
      badge: null
    },
    {
      title: 'Rate Limitleri',
      icon: <Gauge className="h-5 w-5" />,
      path: '/admin/rate-limits',
      badge: null
    },
    {
      title: 'Veri Maskeleme',
      icon: <EyeOff className="h-5 w-5" />,
      path: '/admin/masking',
      badge: null
    },
    {
      title: 'Zaman Aşımları',
      icon: <HourglassIcon className="h-5 w-5" />,
      path: '/admin/timeouts',
      badge: null
    },
    {
      title: 'Audit Loglar',
      icon: <Clock className="h-5 w-5" />,
      path: '/admin/audit-logs',
      badge: null
    },
    {
      title: 'İstatistikler',
      icon: <BarChart3 className="h-5 w-5" />,
      path: '/admin/statistics',
      badge: null
    },
    {
      title: 'Yardım',
      icon: <HelpCircle className="h-5 w-5" />,
      path: '/help',
      badge: null
    },
    {
      title: 'Ayarlar',
      icon: <Settings className="h-5 w-5" />,
      path: '/admin/settings',
      badge: null
    }
  ];
  
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center">
            <Button variant="ghost" size="icon" onClick={toggleSidebar} className="mr-2 lg:hidden">
              {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
            <Link to="/admin/dashboard" className="flex items-center">
              <Database className="h-6 w-6 text-blue-600 mr-2" />
              <span className="text-xl font-bold">SQL Proxy</span>
              <Badge className="ml-2 bg-blue-600">Admin</Badge>
            </Link>
          </div>
          
          <div className="flex items-center space-x-2">
            <SearchBox />
            
            <div className="hidden md:flex items-center">
              <NotificationCenter />
              
              <div className="text-sm text-right ml-2">
                <div className="font-medium">{userInfo.username}</div>
                <div className="text-xs text-gray-500">
                  {new Date('2025-05-20 05:50:02').toLocaleString()}
                </div>
              </div>
              <div className="ml-3 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                {userInfo.username[0].toUpperCase()}
              </div>
            </div>
            
            <Button variant="ghost" size="icon" onClick={handleLogout} title="Çıkış Yap">
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>
      
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside 
          className={`bg-slate-50 border-r border-gray-200 ${
            isSidebarOpen ? 'block' : 'hidden'
          } lg:block w-64 flex-shrink-0 overflow-y-auto`}
        >
          <nav className="p-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center px-3 py-2 rounded-md transition-colors ${
                  location.pathname === item.path
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <span className="mr-3">{item.icon}</span>
                <span>{item.title}</span>
                {item.badge && (
                  <Badge className="ml-auto bg-blue-600">{item.badge}</Badge>
                )}
              </Link>
            ))}
          </nav>
          
          <div className="p-4 border-t border-gray-200 mt-4">
            <div className="text-xs text-gray-500">
              SQL Proxy {SYSTEM_VERSION}
            </div>
            <div className="text-xs text-gray-400">
              {new Date('2025-05-20 05:50:02').toLocaleDateString()}
            </div>
          </div>
        </aside>
        
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-slate-50">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

// Son güncelleme: 2025-05-20 05:50:02
// Güncelleyen: Teeksss

export default AdminLayout;