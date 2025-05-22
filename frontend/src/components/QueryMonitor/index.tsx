import React, { useState } from 'react';
import styled from 'styled-components';
import {
  QueryList,
  QueryDetails,
  PerformanceMetrics,
  PolicyStatus
} from './components';
import { useQueryMonitor } from '../../hooks/useQueryMonitor';

const MonitorContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
`;

const QueryPanel = styled.div`
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 1.5rem;
`;

export const QueryMonitor: React.FC = () => {
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [timeframe, setTimeframe] = useState('1h');
  
  const {
    queries,
    metrics,
    policies,
    loading
  } = useQueryMonitor(timeframe);
  
  return (
    <MonitorContainer>
      <h2>Query Monitor</h2>
      
      <TimeframeSelector
        value={timeframe}
        onChange={setTimeframe}
      />
      
      <MetricsGrid>
        <PerformanceMetrics
          data={metrics}
          loading={loading}
        />
        
        <PolicyStatus
          data={policies}
          loading={loading}
        />
      </MetricsGrid>
      
      <QueryPanel>
        <QueryList
          queries={queries}
          onSelect={setSelectedQuery}
        />
        
        {selectedQuery && (
          <QueryDetails
            query={selectedQuery}
            metrics={metrics}
            policies={policies}
          />
        )}
      </QueryPanel>
    </MonitorContainer>
  );
};