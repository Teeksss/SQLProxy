import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Bell, 
  CheckCircle, 
  Clock, 
  Info, 
  Shield, 
  Trash2, 
  X, 
  XCircle 
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { 
  getUserNotifications, 
  markNotificationAsRead, 
  markAllNotificationsAsRead,
  deleteNotification
} from '@/api/notifications';

// Format a date relative to now (e.g., "2 hours ago")
const formatRelativeTime = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);
  
  if (diffInSeconds < 60) {
    return `${diffInSeconds} saniye önce`;
  }
  
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} dakika önce`;
  }
  
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} saat önce`;
  }
  
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return `${diffInDays} gün önce`;
  }
  
  return date.toLocaleDateString();
};

// Get icon based on notification type
const getNotificationIcon = (type) => {
  switch (type) {
    case 'query_approval':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'query_rejection':
      return <XCircle className="h-5 w-5 text-red-500" />;
    case 'whitelist_add':
      return <Shield className="h-5 w-5 text-blue-500" />;
    case 'timeout':
      return <Clock className="h-5 w-5 text-amber-500" />;
    default:
      return <Info className="h-5 w-5 text-gray-500" />;
  }
};

const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  
  const fetchNotifications = async () => {
    setIsLoading(true);
    try {
      const data = await getUserNotifications({ unreadOnly: false, limit: 20 });
      setNotifications(data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      // Mock data for demo
      setNotifications([
        {
          id: 1,
          type: 'query_approval',
          title: 'Sorgunuz onaylandı',
          message: 'SELECT * FROM customers LIMIT 100 sorgunuz onaylandı',
          read: false,
          created_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 minutes ago
          action_url: '/history'
        },
        {
          id: 2,
          type: 'query_rejection',
          title: 'Sorgunuz reddedildi',
          message: 'DELETE FROM users sorgunuz güvenlik nedeniyle reddedildi',
          read: true,
          created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
          action_url: '/history'
        },
        {
          id: 3,
          type: 'whitelist_add',
          title: 'Sorgu beyaz listeye eklendi',
          message: 'Rapor sorgunuz otomatik onay listesine eklendi',
          read: false,
          created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
          action_url: '/dashboard'
        },
        {
          id: 4,
          type: 'system',
          title: 'Sistem bakımı',
          message: 'SQL Proxy 2 saat içinde bakım nedeniyle kısa süreliğine kesintiye uğrayacak',
          read: true,
          created_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), // 2 days ago
          action_url: null
        },
        {
          id: 5,
          type: 'timeout',
          title: 'Sorgu zaman aşımı',
          message: 'Uzun çalışan sorgunuz zaman aşımına uğradı',
          read: false,
          created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
          action_url: '/history'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Fetch notifications when popover opens
  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);
  
  const handleMarkAsRead = async (id) => {
    try {
      await markNotificationAsRead(id);
      setNotifications(prev => 
        prev.map(notif => 
          notif.id === id ? { ...notif, read: true } : notif
        )
      );
    } catch (error) {
      console.error('Error marking notification as read:', error);
      // For demo, update state directly
      setNotifications(prev => 
        prev.map(notif => 
          notif.id === id ? { ...notif, read: true } : notif
        )
      );
    }
  };
  
  const handleMarkAllAsRead = async () => {
    try {
      await markAllNotificationsAsRead();
      setNotifications(prev => 
        prev.map(notif => ({ ...notif, read: true }))
      );
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
      // For demo, update state directly
      setNotifications(prev => 
        prev.map(notif => ({ ...notif, read: true }))
      );
    }
  };
  
  const handleDeleteNotification = async (id, e) => {
    e.stopPropagation(); // Prevent clicking on the notification item
    
    try {
      await deleteNotification(id);
      setNotifications(prev => prev.filter(notif => notif.id !== id));
    } catch (error) {
      console.error('Error deleting notification:', error);
      // For demo, update state directly
      setNotifications(prev => prev.filter(notif => notif.id !== id));
    }
  };
  
  const handleNotificationClick = (notification) => {
    // Mark as read
    if (!notification.read) {
      handleMarkAsRead(notification.id);
    }
    
    // Navigate to target page if action URL exists
    if (notification.action_url) {
      navigate(notification.action_url);
    }
    
    // Close popover
    setIsOpen(false);
  };
  
  const unreadCount = notifications.filter(n => !n.read).length;
  
  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white">
              {unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-96 p-0">
        <div className="flex items-center justify-between border-b p-3">
          <h3 className="font-medium">Bildirimler</h3>
          {unreadCount > 0 && (
            <Button variant="ghost" size="sm" onClick={handleMarkAllAsRead}>
              Tümünü Okundu İşaretle
            </Button>
          )}
        </div>
        
        <div className="max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-700"></div>
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Bell className="h-10 w-10 text-gray-300 mb-2" />
              <p className="text-gray-500">Bildiriminiz bulunmuyor</p>
            </div>
          ) : (
            <div>
              {notifications.map(notification => (
                <div 
                  key={notification.id}
                  className={`
                    flex items-start p-3 border-b hover:bg-gray-50 cursor-pointer
                    ${notification.read ? 'bg-white' : 'bg-blue-50'}
                  `}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <div className="flex-shrink-0 mr-3">
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                      <p className={`text-sm font-medium ${notification.read ? '' : 'text-blue-600'}`}>
                        {notification.title}
                      </p>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-6 w-6 -mt-1 -mr-1"
                        onClick={(e) => handleDeleteNotification(notification.id, e)}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-gray-400" />
                      </Button>
                    </div>
                    <p className="text-xs text-gray-600 mt-0.5 line-clamp-2">
                      {notification.message}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatRelativeTime(notification.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="p-2 border-t text-center">
          <Button variant="ghost" size="sm" className="text-xs text-gray-500 w-full" onClick={() => setIsOpen(false)}>
            Kapat
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
};

// Son güncelleme: 2025-05-20 05:50:02
// Güncelleyen: Teeksss

export default NotificationCenter;