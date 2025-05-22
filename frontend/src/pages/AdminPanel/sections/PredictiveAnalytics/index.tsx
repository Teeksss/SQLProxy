import React from 'react';
import styled from 'styled-components';
import {
  ResourcePredictor,
  UsageForecaster,
  AnomalyDetector,
  CapacityPlanner
} from './components';
import { usePredictiveAnalytics } from '../../../../hooks/usePredictiveAnalytics';

const AnalyticsContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const AnalyticsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 1.5rem;
`;

export const PredictiveAnalytics: React.FC = () => {
  const {
    resourcePredictions,
    usageForecasts,
    anomalies,
    capacityPlans,
    updatePredictions,
    timeRange,
    setTimeRange
  } = usePredictiveAnalytics();
  
  return (
    <AnalyticsContainer>
      <h2>Predictive Analytics</h2>
      
      <TimeRangeSelector
        value={timeRange}
        onChange={setTimeRange}
      />
      
      <AnalyticsGrid>
        <ResourcePredictor
          predictions={resourcePredictions}
          onUpdate={updatePredictions}
        />
        
        <UsageForecaster
          forecasts={usageForecasts}
          onUpdate={updatePredictions}
        />
        
        <AnomalyDetector
          anomalies={anomalies}
          onUpdate={updatePredictions}
        />
        
        <CapacityPlanner
          plans={capacityPlans}
          onUpdate={updatePredictions}
        />
      </AnalyticsGrid>
    </AnalyticsContainer>
  );
};