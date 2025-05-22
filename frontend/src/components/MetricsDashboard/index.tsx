import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import {
  SystemMetrics,
  QueryMetrics,
  AlertsPanel,
  ResourceUsage
} from './components';
import { useMetrics } from '../../hooks/useMetrics';

const DashboardContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
`;

const ChartContainer = styled.div`
  background: ${props => props.theme.colors.card};
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: ${props => props.theme.shadows.md};
`;

export const MetricsDashboard: React.FC = () => {
  const [timeframe, setTimeframe] = useState('1h');
  
  const {
    metrics,
    alerts,
    loading,
    error
  } = useMetrics(timeframe);
  
  // Real-time updates
  useEffect(() => {
    const socket = new WebSocket('ws://api/metrics');
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Update metrics in real-time
    };
    
    return () => socket.close();
  }, []);
  
  if (loading) return <Loading />;
  if (error) return <Error message={error} />;
  
  return (
    <DashboardContainer>
      <h2>System Metrics</h2>
      
      <TimeframeSelector
        value={timeframe}
        onChange={setTimeframe}
      />
      
      <MetricsGrid>
        <ChartContainer>
          <SystemMetrics
            data={metrics.system}
            type="cpu"
          />
        </ChartContainer>
        
        <ChartContainer>
          <SystemMetrics
            data={metrics.system}
            type="memory"
          />
        </ChartContainer>
        
        <ChartContainer>
          <QueryMetrics
            data={metrics.queries}
          />
        </ChartContainer>
        
        <ChartContainer>
          <ResourceUsage
            data={metrics.resources}
          />
        </ChartContainer>
      </MetricsGrid>
      
      <AlertsPanel
        alerts={alerts}
        onAcknowledge={handleAlertAcknowledge}
      />
    </DashboardContainer>
  );
};