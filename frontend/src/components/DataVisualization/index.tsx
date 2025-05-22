import React, { useState } from 'react';
import styled from 'styled-components';
import {
  LineChart,
  BarChart,
  PieChart,
  HeatMap
} from './charts';
import { useVisualization } from '../../hooks/useVisualization';

const VisualizationContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
`;

export const DataVisualization: React.FC<{
  data: any;
  config: any;
}> = ({ data, config }) => {
  const [selectedView, setSelectedView] = useState('overview');
  
  const {
    processedData,
    chartOptions,
    loading
  } = useVisualization(data, config);
  
  return (
    <VisualizationContainer>
      <ViewSelector
        value={selectedView}
        onChange={setSelectedView}
      />
      
      <ChartGrid>
        <ChartContainer>
          <LineChart
            data={processedData.timeSeries}
            options={chartOptions.line}
          />
        </ChartContainer>
        
        <ChartContainer>
          <BarChart
            data={processedData.categorical}
            options={chartOptions.bar}
          />
        </ChartContainer>
        
        <ChartContainer>
          <PieChart
            data={processedData.distribution}
            options={chartOptions.pie}
          />
        </ChartContainer>
        
        <ChartContainer>
          <HeatMap
            data={processedData.correlation}
            options={chartOptions.heatmap}
          />
        </ChartContainer>
      </ChartGrid>
    </VisualizationContainer>
  );
};