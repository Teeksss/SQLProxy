import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import {
  LiveMetrics,
  QueryStream,
  AlertPanel
} from './components';
import { useRealTimeData } from '../../hooks/useRealTimeData';

const MonitorContainer = styled.div`
  display: grid;
  gap: 1rem;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
`;

interface RealTimeMetric {
  name: string;
  value: number;
  trend: 'up' | 'down' | 'stable';
  threshold?: number;
}

export const RealTimeMonitor: React.FC = () => {
  const {
    metrics,
    queries,
    alerts,
    isConnected
  } = useRealTimeData();
  
  return (
    <MonitorContainer>
      <h3>Real-time Analytics</h3>
      
      <ConnectionStatus connected={isConnected} />
      
      <MetricsGrid>
        <LiveMetrics
          metrics={metrics}
          refreshRate={1000}
        />
        
        <QueryStream
          queries={queries}
          maxItems={50}
        />
        
        <AlertPanel
          alerts={alerts}
          onAcknowledge={(id) => {/* handle alert */}}
        />
      </MetricsGrid>
    </MonitorContainer>
  );
};