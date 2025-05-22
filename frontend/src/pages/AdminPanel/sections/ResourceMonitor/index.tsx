import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import {
  SystemMetrics,
  DatabaseMetrics,
  NetworkStats,
  AlertManager
} from './components';
import { useResourceMonitor } from '../../../../hooks/useResourceMonitor';

const MonitorGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
`;

const MetricCard = styled.div`
  background: ${props => props.theme.colors.card};
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
`;

const AlertSection = styled.div`
  grid-column: 1 / -1;
`;

export const ResourceMonitor: React.FC = () => {
  const {
    systemMetrics,
    databaseMetrics,
    networkStats,
    alerts,
    updateInterval,
    setUpdateInterval
  } = useResourceMonitor();
  
  return (
    <div>
      <h2>Resource Monitor</h2>
      
      <MonitorGrid>
        <MetricCard>
          <h3>System Performance</h3>
          <SystemMetrics
            data={systemMetrics}
            updateInterval={updateInterval}
            onIntervalChange={setUpdateInterval}
          />
        </MetricCard>
        
        <MetricCard>
          <h3>Database Performance</h3>
          <DatabaseMetrics
            data={databaseMetrics}
            updateInterval={updateInterval}
          />
        </MetricCard>
        
        <MetricCard>
          <h3>Network Statistics</h3>
          <NetworkStats
            data={networkStats}
            updateInterval={updateInterval}
          />
        </MetricCard>
        
        <AlertSection>
          <AlertManager
            alerts={alerts}
            onDismiss={(id) => {/* handle alert dismiss */}}
            onConfigure={() => {/* open alert config */}}
          />
        </AlertSection>
      </MonitorGrid>
    </div>
  );
};