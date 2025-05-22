import React, { useState } from 'react';
import styled from 'styled-components';
import {
  QueryAnalysis,
  ApprovalStatus,
  Comments
} from './components';
import { useQueryReview } from '../../hooks/useQueryReview';

const ReviewContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
`;

export const QueryReview: React.FC<{
  requestId: string;
  onApprove: (comments: string) => void;
  onReject: (comments: string) => void;
}> = ({ requestId, onApprove, onReject }) => {
  const [comments, setComments] = useState('');
  const { request, analysis, loading } = useQueryReview(requestId);
  
  if (loading) {
    return <div>Loading review details...</div>;
  }
  
  return (
    <ReviewContainer>
      <h2>Query Review</h2>
      
      <QueryAnalysis analysis={analysis} />
      
      <ApprovalStatus
        status={request.status}
        approvers={request.approvers}
        approvals={request.approvals}
      />
      
      <Comments
        value={comments}
        onChange={setComments}
      />
      
      <ActionButtons>
        <button
          onClick={() => onReject(comments)}
          className="danger"
        >
          Reject
        </button>
        
        <button
          onClick={() => onApprove(comments)}
          className="primary"
          disabled={!analysis.is_safe}
        >
          Approve
        </button>
      </ActionButtons>
    </ReviewContainer>
  );
};