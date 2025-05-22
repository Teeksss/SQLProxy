import React, { useState } from 'react';
import styled from 'styled-components';
import {
  ResourceUtilization,
  CostAnalysis,
  ScalingHistory,
  Recommendations
} from './components';
import { useCapacityDashboard } from '../../hooks/useCapacityDashboard';

const DashboardContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
`;

export const CapacityDashboard: React.FC = () => {
  const [timeframe, setTimeframe] = useState('24h');
  
  const {
    utilization,
    costs,
    scaling,
    recommendations,
    loading
  } = useCapacityDashboard(timeframe);
  
  return (
    <DashboardContainer>
      <h2>Capacity Management</h2>
      
      <TimeframeSelector
        value={timeframe}
        onChange={setTimeframe}
      />
      
      <MetricsGrid>
        <ResourceUtilization
          data={utilization}
          loading={loading}
        />
        
        <CostAnalysis
          data={costs}
          loading={loading}
        />
        
        <ScalingHistory
          data={scaling}
          loading={loading}
        />
        
        <Recommendations
          items={recommendations}
          loading={loading}
        />
      </MetricsGrid>
    </DashboardContainer>
  );
};