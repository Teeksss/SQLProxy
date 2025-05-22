import React, { useState } from 'react';
import styled from 'styled-components';
import {
  WorkloadPrediction,
  ResourcePlanning,
  PerformancePredictor,
  PredictionMetrics
} from './components';
import { usePredictiveAnalytics } from '../../hooks/usePredictiveAnalytics';

const AnalyticsContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const PredictionGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 1.5rem;
`;

export const PredictiveAnalytics: React.FC = () => {
  const [timeHorizon, setTimeHorizon] = useState(24); // hours
  
  const {
    workloadPredictions,
    resourcePlan,
    performancePredictions,
    metrics,
    loading
  } = usePredictiveAnalytics(timeHorizon);
  
  return (
    <AnalyticsContainer>
      <h2>Predictive Analytics</h2>
      
      <TimeHorizonSelector
        value={timeHorizon}
        onChange={setTimeHorizon}
      />
      
      <PredictionGrid>
        <WorkloadPrediction
          data={workloadPredictions}
          loading={loading}
        />
        
        <ResourcePlanning
          plan={resourcePlan}
          loading={loading}
        />
        
        <PerformancePredictor
          predictions={performancePredictions}
          loading={loading}
        />
        
        <PredictionMetrics
          metrics={metrics}
          loading={loading}
        />
      </PredictionGrid>
    </AnalyticsContainer>
  );
};