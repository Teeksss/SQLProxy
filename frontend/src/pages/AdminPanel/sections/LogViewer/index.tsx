import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import {
  LineChart,
  BarChart,
  PieChart
} from '../../../../components/Charts';
import { LogTable } from './LogTable';
import { LogFilter } from './LogFilter';
import { LogAnalytics } from './LogAnalytics';
import { useLogData } from '../../../../hooks/useLogData';

const LogViewerContainer = styled.div`
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;
`;

const ChartsGrid = styled.div`
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
`;

export const LogViewer: React.FC = () => {
  const [filters, setFilters] = useState({
    startDate: null,
    endDate: null,
    level: [],
    source: [],
    keyword: ''
  });
  
  const {
    logs,
    analytics,
    isLoading,
    error
  } = useLogData(filters);
  
  const charts = {
    errorRate: {
      title: 'Error Rate Over Time',
      data: analytics.errorRate,
      type: 'line'
    },
    logLevels: {
      title: 'Log Levels Distribution',
      data: analytics.logLevels,
      type: 'pie'
    },
    topErrors: {
      title: 'Top Error Types',
      data: analytics.topErrors,
      type: 'bar'
    }
  };
  
  return (
    <LogViewerContainer>
      <h2>Log Analysis</h2>
      
      <LogFilter
        filters={filters}
        onChange={setFilters}
      />
      
      <ChartsGrid>
        {Object.entries(charts).map(([key, chart]) => (
          <div key={key}>
            {chart.type === 'line' && (
              <LineChart
                title={chart.title}
                data={chart.data}
                loading={isLoading}
              />
            )}
            {chart.type === 'pie' && (
              <PieChart
                title={chart.title}
                data={chart.data}
                loading={isLoading}
              />
            )}
            {chart.type === 'bar' && (
              <BarChart
                title={chart.title}
                data={chart.data}
                loading={isLoading}
              />
            )}
          </div>
        ))}
      </ChartsGrid>
      
      <LogAnalytics analytics={analytics} />
      
      <LogTable
        logs={logs}
        loading={isLoading}
        error={error}
      />
    </LogViewerContainer>
  );
};