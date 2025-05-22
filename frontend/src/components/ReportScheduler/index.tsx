import React, { useState } from 'react';
import styled from 'styled-components';
import {
  ScheduleForm,
  RecipientList,
  DeliveryOptions
} from './components';
import { useReportScheduler } from '../../hooks/useReportScheduler';

const SchedulerContainer = styled.div`
  display: grid;
  gap: 1.5rem;
`;

const ScheduleGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
`;

export const ReportScheduler: React.FC<{
  reportId: string;
  initialSchedule?: any;
  onSave: (schedule: any) => void;
}> = ({ reportId, initialSchedule, onSave }) => {
  const [schedule, setSchedule] = useState(initialSchedule || {
    frequency: 'daily',
    time: '09:00',
    timezone: 'UTC',
    recipients: [],
    format: 'pdf',
    delivery: 'email'
  });
  
  const {
    validateSchedule,
    saveSchedule,
    testDelivery
  } = useReportScheduler();
  
  const handleSave = async () => {
    if (validateSchedule(schedule)) {
      await saveSchedule(reportId, schedule);
      onSave(schedule);
    }
  };
  
  return (
    <SchedulerContainer>
      <h3>Schedule Report</h3>
      
      <ScheduleGrid>
        <div>
          <h4>Timing</h4>
          <ScheduleForm
            value={schedule}
            onChange={setSchedule}
          />
        </div>
        
        <div>
          <h4>Recipients</h4>
          <RecipientList
            recipients={schedule.recipients}
            onUpdate={(recipients) => setSchedule({
              ...schedule,
              recipients
            })}
          />
        </div>
        
        <div>
          <h4>Delivery Options</h4>
          <DeliveryOptions
            options={schedule}
            onChange={(options) => setSchedule({
              ...schedule,
              ...options
            })}
          />
        </div>
      </ScheduleGrid>
      
      <div>
        <button onClick={handleSave}>Save Schedule</button>
        <button onClick={() => testDelivery(schedule)}>
          Test Delivery
        </button>
      </div>
    </SchedulerContainer>
  );
};