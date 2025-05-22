import React from 'react';
import styled from 'styled-components';
import {
  LineChart,
  AreaChart,
  BarChart
} from '../Charts';
import { useResourceMetrics } from '../../hooks/useResourceMetrics';

const GraphContainer = styled.div`
  display: grid;
  gap: 1.5rem;
`;

const GraphGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1rem;
`;

export const ResourceGraphs: React.FC = () => {
  const {
    cpuUsage,
    memoryUsage,
    diskIO,
    networkTraffic,
    timeRange,
    setTimeRange
  } = useResourceMetrics();
  
  const graphs = [
    {
      title: 'CPU Usage',
      type: 'line',
      data: cpuUsage,
      options: {
        yAxis: { max: 100, unit: '%' }
      }
    },
    {
      title: 'Memory Usage',
      type: 'area',
      data: memoryUsage,
      options: {
        yAxis: { unit: 'GB' }
      }
    },
    {
      title: 'Disk I/O',
      type: 'bar',
      data: diskIO,
      options: {
        yAxis: { unit: 'MB/s' }
      }
    },
    {
      title: 'Network Traffic',
      type: 'area',
      data: networkTraffic,
      options: {
        yAxis: { unit: 'Mbps' }
      }
    }
  ];
  
  return (
    <GraphContainer>
      <TimeRangeSelector
        value={timeRange}
        onChange={setTimeRange}
      />
      
      <GraphGrid>
        {graphs.map((graph, index) => (
          <div key={index}>
            {graph.type === 'line' && (
              <LineChart
                title={graph.title}
                data={graph.data}
                options={graph.options}
              />
            )}
            {graph.type === 'area' && (
              <AreaChart
                title={graph.title}
                data={graph.data}
                options={graph.options}
              />
            )}
            {graph.type === 'bar' && (
              <BarChart
                title={graph.title}
                data={graph.data}
                options={graph.options}
              />
            )}
          </div>
        ))}
      </GraphGrid>
    </GraphContainer>
  );
};