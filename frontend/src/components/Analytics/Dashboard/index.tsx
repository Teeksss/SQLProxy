import React, { useState } from 'react';
import styled from 'styled-components';
import {
  PerformanceChart,
  ServerHealth,
  QueryMetrics,
  ResourceUsage,
  TrendAnalysis
} from './components';
import { useAnalytics } from '../../../hooks/useAnalytics';

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
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
`;

export const AnalyticsDashboard: React.FC = () => {
  const [timeframe, setTimeframe] = useState('24h');
  
  const {
    performance,
    health,
    queries,
    resources,
    trends,
    loading
  } = useAnalytics(timeframe);
  
  return (
    <DashboardContainer>
      <TimeframeSelector
        value={timeframe}
        onChange={setTimeframe}
      />
      
      <MetricsGrid>
        <ChartContainer>
          <PerformanceChart
            data={performance}
            loading={loading}
          />
        </ChartContainer>
        
        <ChartContainer>
          <ServerHealth
            data={health}
            loading={loading}
          />
        </ChartContainer>
        
        <ChartContainer>
          <QueryMetrics
            data={queries}
            loading={loading}
          />
        </ChartContainer>
        
        <ChartContainer>
          <ResourceUsage
            data={resources}
            loading={loading}
          />
        </ChartContainer>
      </MetricsGrid>
      
      <TrendAnalysis
        data={trends}
        loading={loading}
      />
    </DashboardContainer>
  );
};