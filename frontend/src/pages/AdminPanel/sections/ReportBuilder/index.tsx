import React, { useState } from 'react';
import styled from 'styled-components';
import {
  ReportDesigner,
  DataSelector,
  VisualizationPicker,
  ScheduleManager
} from './components';
import { useReportBuilder } from '../../../../hooks/useReportBuilder';

const BuilderContainer = styled.div`
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;
`;

const DesignerPanel = styled.div`
  background: ${props => props.theme.colors.card};
  padding: 1.5rem;
  border-radius: 8px;
`;

const PreviewPanel = styled.div`
  background: ${props => props.theme.colors.card};
  padding: 1.5rem;
  border-radius: 8px;
`;

export const ReportBuilder: React.FC = () => {
  const [reportConfig, setReportConfig] = useState({
    name: '',
    description: '',
    dataSources: [],
    visualizations: [],
    schedule: null,
    recipients: []
  });
  
  const {
    availableDataSources,
    availableVisualizations,
    saveReport,
    previewReport,
    scheduleReport
  } = useReportBuilder();
  
  const handleSave = async () => {
    try {
      await saveReport(reportConfig);
      // Show success message
    } catch (error) {
      // Handle error
    }
  };
  
  return (
    <BuilderContainer>
      <DesignerPanel>
        <h2>Report Designer</h2>
        
        <ReportDesigner
          config={reportConfig}
          onChange={setReportConfig}
        />
        
        <DataSelector
          availableSources={availableDataSources}
          selectedSources={reportConfig.dataSources}
          onSelect={(sources) => setReportConfig({
            ...reportConfig,
            dataSources: sources
          })}
        />
        
        <VisualizationPicker
          available={availableVisualizations}
          selected={reportConfig.visualizations}
          onSelect={(visuals) => setReportConfig({
            ...reportConfig,
            visualizations: visuals
          })}
        />
        
        <ScheduleManager
          schedule={reportConfig.schedule}
          recipients={reportConfig.recipients}
          onChange={(schedule, recipients) => setReportConfig({
            ...reportConfig,
            schedule,
            recipients
          })}
        />
        
        <button onClick={handleSave}>Save Report</button>
      </DesignerPanel>
      
      <PreviewPanel>
        <h2>Report Preview</h2>
        <ReportPreview config={reportConfig} />
      </PreviewPanel>
    </BuilderContainer>
  );
};