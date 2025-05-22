import React, { useState } from 'react';
import styled from 'styled-components';
import {
  PendingRequests,
  RequestDetails,
  ApprovalHistory,
  Statistics
} from './components';
import { useApprovals } from '../../hooks/useApprovals';

const DashboardContainer = styled.div`
  display: grid;
  gap: 2rem;
  grid-template-columns: 1fr 300px;
`;

const MainContent = styled.div`
  display: grid;
  gap: 2rem;
`;

export const ApprovalDashboard: React.FC = () => {
  const [selectedRequest, setSelectedRequest] = useState(null);
  
  const {
    pendingRequests,
    history,
    stats,
    approveRequest,
    rejectRequest
  } = useApprovals();
  
  return (
    <DashboardContainer>
      <MainContent>
        <h2>Query Approvals</h2>
        
        <PendingRequests
          requests={pendingRequests}
          onSelect={setSelectedRequest}
        />
        
        {selectedRequest && (
          <RequestDetails
            request={selectedRequest}
            onApprove={approveRequest}
            onReject={rejectRequest}
          />
        )}
        
        <ApprovalHistory history={history} />
      </MainContent>
      
      <aside>
        <Statistics stats={stats} />
      </aside>
    </DashboardContainer>
  );
};