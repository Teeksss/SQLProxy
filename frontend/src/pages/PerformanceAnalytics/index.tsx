import React, { useState } from 'react';
import styled from 'styled-components';
import {
  QueryPatterns,
  ResourceUsage,
  TimeDistribution,
  Recommendations
} from './components';
import { usePerformanceAnalytics } from '../../hooks/usePerformanceAnalytics';

const AnalyticsContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
`;

const MetricsPanel = styled.div`
  background: ${props => props.theme.colors.card};
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
`;

export const PerformanceAnalytics: React.FC = () => {
  const [timeframe, setTimeframe] = useState('7d');
  const {
    patterns,
    resourceMetrics,
    timeDistribution,
    recommendations,
    loading
  } = usePerformanceAnalytics(timeframe);
  
  return (
    <AnalyticsContainer>
      <h2>Performance Analytics</h2>
      
      <TimeframeSelector
        value={timeframe}
        onChange={setTimeframe}
      />
      
      <ChartGrid>
        <MetricsPanel>
          <h3>Query Patterns</h3>
          <QueryPatterns
            data={patterns}
            loading={loading}
          />
        </MetricsPanel>
        
        <MetricsPanel>
          <h3>Resource Usage</h3>
          <ResourceUsage
            data={resourceMetrics}
            loading={loading}
          />
        </MetricsPanel>
        
        <MetricsPanel>
          <h3>Time Distribution</h3>
          <TimeDistribution
            data={timeDistribution}
            loading={loading}
          />
        </MetricsPanel>
        
        <MetricsPanel>
          <h3>Recommendations</h3>
          <Recommendations
            items={recommendations}
            loading={loading}
          />
        </MetricsPanel>
      </ChartGrid>
    </AnalyticsContainer>
  );
};