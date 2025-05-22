import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import {
  LineChart,
  PredictionBands,
  ConfidenceInterval
} from '../Charts';
import { usePredictionModel } from '../../hooks/usePredictionModel';

const PredictorContainer = styled.div`
  display: grid;
  gap: 1.5rem;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
`;

const MetricCard = styled.div`
  background: ${props => props.theme.colors.card};
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
`;

export const ResourcePredictor: React.FC<{
  historical: any[];
  onPredict: (predictions: any[]) => void;
}> = ({ historical, onPredict }) => {
  const {
    predictions,
    confidence,
    accuracy,
    trainModel,
    updatePredictions
  } = usePredictionModel();
  
  const metrics = [
    {
      label: 'Model Accuracy',
      value: `${(accuracy * 100).toFixed(2)}%`,
      trend: accuracy > 0.8 ? 'up' : 'down'
    },
    {
      label: 'Confidence Level',
      value: `${(confidence * 100).toFixed(2)}%`,
      trend: confidence > 0.7 ? 'up' : 'down'
    }
  ];
  
  return (
    <PredictorContainer>
      <h3>Resource Usage Predictions</h3>
      
      <MetricsGrid>
        {metrics.map((metric, index) => (
          <MetricCard key={index}>
            <h4>{metric.label}</h4>
            <div className={`trend-${metric.trend}`}>
              {metric.value}
            </div>
          </MetricCard>
        ))}
      </MetricsGrid>
      
      <div>
        <LineChart
          data={historical}
          predictions={predictions}
          showConfidenceBands={true}
        />
      </div>
      
      <PredictionControls
        onTrain={() => trainModel(historical)}
        onUpdate={updatePredictions}
      />
    </PredictorContainer>
  );
};