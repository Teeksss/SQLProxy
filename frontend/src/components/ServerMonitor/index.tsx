import React, { useState } from 'react';
import styled from 'styled-components';
import {
  ServerList,
  ServerDetails,
  SessionManager,
  QueryAnalytics
} from './components';
import { useServerMonitor } from '../../hooks/useServerMonitor';

const MonitorContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const ServerGrid = styled.div`
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1.5rem;
`;

export const ServerMonitor: React.FC = () => {
  const [selectedServer, setSelectedServer] = useState(null);
  
  const {
    servers,
    sessions,
    analytics,
    loading
  } = useServerMonitor();
  
  return (
    <MonitorContainer>
      <h2>SQL Server Monitor</h2>
      
      <ServerGrid>
        <div>
          <ServerList
            servers={servers}
            onSelect={setSelectedServer}
          />
          
          <SessionManager
            sessions={sessions}
            selectedServer={selectedServer}
          />
        </div>
        
        <div>
          {selectedServer && (
            <ServerDetails
              server={selectedServer}
              loading={loading}
            />
          )}
          
          <QueryAnalytics
            data={analytics}
            server={selectedServer}
          />
        </div>
      </ServerGrid>
    </MonitorContainer>
  );
};