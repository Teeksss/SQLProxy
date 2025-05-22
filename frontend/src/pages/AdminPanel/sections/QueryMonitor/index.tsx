import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  QueryList,
  QueryDetails,
  QueryAnalytics,
  QueryFilter
} from './components';
import { useQueryMonitor } from '../../../../hooks/useQueryMonitor';

const MonitorContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 1rem;
`;

const AnalyticsSection = styled.div`
  display: grid;
  gap: 1rem;
`;

export const QueryMonitor: React.FC = () => {
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [filters, setFilters] = useState({
    status: [],
    database: [],
    timeRange: '24h',
    search: ''
  });
  
  const {
    queries,
    analytics,
    isLoading,
    error
  } = useQueryMonitor(filters);
  
  return (
    <div>
      <h2>Query Monitor</h2>
      
      <QueryFilter
        filters={filters}
        onChange={setFilters}
      />
      
      <MonitorContainer>
        <div>
          <QueryList
            queries={queries}
            loading={isLoading}
            error={error}
            onSelect={setSelectedQuery}
            selected={selectedQuery}
          />
          
          {selectedQuery && (
            <QueryDetails query={selectedQuery} />
          )}
        </div>
        
        <AnalyticsSection>
          <QueryAnalytics
            data={analytics}
            loading={isLoading}
          />
        </AnalyticsSection>
      </MonitorContainer>
    </div>
  );
};