import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  BarChart3, 
  Database, 
  LogOut, 
  Settings, 
  Shield, 
  UserCog,
  Clock,
  List,
  Server,
  Gauge,
  Menu,
  X,
  HelpCircle
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { logout, getUserInfo, getUserRole } from '@/utils/auth';
import { CURRENT_USER, CURRENT_DATETIME, ROLE_COLORS } from '@/utils/constants';

const UserLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();
  const userInfo = getUserInfo() || CURRENT_USER;
  const userRole = getUserRole() || CURRENT_USER.role;
  
  const navItems = [
    {
      title: 'Sorgu Paneli',
      icon: <Database className="h-5 w-5" />,
      path: '/dashboard',
      badge: null
    },
    {
      title: 'Sorgu Geçmişi',
      icon: <Clock className="h-5 w-5" />,
      path: '/history',
      badge: null
    },
    {
      title: 'Yardım',
      icon: <HelpCircle className="h-5 w-5" />,
      path: '/help',
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
  
  const roleBadgeColor = ROLE_COLORS[userRole] || ROLE_COLORS.readonly;
  
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center">
            <Button variant="ghost" size="icon" onClick={toggleSidebar} className="mr-2 lg:hidden">
              {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
            <Link to="/dashboard" className="flex items-center">
              <Database className="h-6 w-6 text-blue-600 mr-2" />
              <span className="text-xl font-bold">SQL Proxy</span>
              <Badge className={`ml-2 ${roleBadgeColor}`}>
                {userRole.charAt(0).toUpperCase() + userRole.slice(1)}
              </Badge>
            </Link>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center">
              <div className="text-sm text-right">
                <div className="font-medium">{CURRENT_USER.username}</div>
                <div className="text-xs text-gray-500">
                  {new Date('2025-05-16 13:35:47').toLocaleString()}
                </div>
              </div>
              <div className="ml-3 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                {CURRENT_USER.username[0].toUpperCase()}
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
              Son güncelleme: {new Date('2025-05-16 13:35:47').toLocaleString()}
            </div>
            <div className="text-xs text-gray-400">
              Kullanıcı: Teeksss
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

export default UserLayout;