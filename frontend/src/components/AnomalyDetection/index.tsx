import React from 'react';
import styled from 'styled-components';
import {
  AnomalyChart,
  AlertsList,
  Thresholds
} from './components';
import { useAnomalyDetection } from '../../hooks/useAnomalyDetection';

const AnomalyContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const AnomalyGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 1.5rem;
`;

export const AnomalyDetection: React.FC = () => {
  const {
    anomalies,
    alerts,
    thresholds,
    updateThresholds,
    acknowledgeAlert
  } = useAnomalyDetection();
  
  return (
    <AnomalyContainer>
      <h3>Anomaly Detection</h3>
      
      <AnomalyGrid>
        <div>
          <AnomalyChart
            data={anomalies}
            thresholds={thresholds}
          />
        </div>
        
        <div>
          <Thresholds
            values={thresholds}
            onChange={updateThresholds}
          />
          
          <AlertsList
            alerts={alerts}
            onAcknowledge={acknowledgeAlert}
          />
        </div>
      </AnomalyGrid>
    </AnomalyContainer>
  );
};