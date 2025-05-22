import React from 'react';
import styled from 'styled-components';
import { AlertConfig } from './AlertConfig';
import { NotificationList } from './NotificationList';
import { useAlerts } from '../../hooks/useAlerts';

const AlertContainer = styled.div`
  display: grid;
  gap: 1.5rem;
`;

const AlertHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const AlertGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
`;

export const AlertSystem: React.FC = () => {
  const {
    alerts,
    configs,
    notifications,
    createAlert,
    updateAlert,
    deleteAlert,
    markAsRead
  } = useAlerts();
  
  return (
    <AlertContainer>
      <AlertHeader>
        <h3>Alert Management</h3>
        <button onClick={() => {/* create new alert */}}>
          New Alert
        </button>
      </AlertHeader>
      
      <AlertGrid>
        <div>
          <h4>Alert Configurations</h4>
          <AlertConfig
            configs={configs}
            onCreate={createAlert}
            onUpdate={updateAlert}
            onDelete={deleteAlert}
          />
        </div>
        
        <div>
          <h4>Recent Notifications</h4>
          <NotificationList
            notifications={notifications}
            onMarkAsRead={markAsRead}
          />
        </div>
      </AlertGrid>
    </AlertContainer>
  );
};