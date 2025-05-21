import React from 'react';
import { Badge } from '@/components/ui/badge';
import { getUserInfo } from '@/utils/auth';
import { CURRENT_USER, CURRENT_DATETIME, ROLE_COLORS } from '@/utils/constants';

const UserInfo = () => {
  const userInfo = getUserInfo() || CURRENT_USER;
  
  // Kullanıcı rolüne göre badge rengi belirleme
  const getBadgeColor = () => {
    return ROLE_COLORS[userInfo?.role] || 'bg-gray-500';
  };
  
  return (
    <div className="flex items-center space-x-3">
      <div>
        <div className="font-medium text-sm">
          {userInfo?.displayName || userInfo?.username || 'Teeksss'}
        </div>
        <div className="text-xs text-gray-500">
          {CURRENT_DATETIME.toLocaleString()}
        </div>
      </div>
      
      <Badge className={getBadgeColor()}>
        {userInfo?.role || 'User'}
      </Badge>
      
      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
        {(userInfo?.displayName || userInfo?.username || 'T')[0].toUpperCase()}
      </div>
    </div>
  );
};

export default UserInfo;