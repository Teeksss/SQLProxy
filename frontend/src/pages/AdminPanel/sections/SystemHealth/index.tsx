import React from 'react';
import styled from 'styled-components';
import {
  HealthStatus,
  ServiceStatus,
  ErrorRates,
  Performance
} from './components';
import { useSystemHealth } from '../../../../hooks/useSystemHealth';

const HealthContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const HealthGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
`;

export const SystemHealth: React.FC = () => {
  const {
    healthStatus,
    services,
    errorRates,
    performance,
    refresh
  } = useSystemHealth();
  
  return (
    <HealthContainer>
      <h2>System Health</h2>
      
      <HealthGrid>
        <HealthStatus
          status={healthStatus}
          onRefresh={refresh}
        />
        
        <ServiceStatus
          services={services}
          onRefresh={refresh}
        />
        
        <ErrorRates
          data={errorRates}
          onRefresh={refresh}
        />
        
        <Performance
          data={performance}
          onRefresh={refresh}
        />
      </HealthGrid>
    </HealthContainer>
  );
};