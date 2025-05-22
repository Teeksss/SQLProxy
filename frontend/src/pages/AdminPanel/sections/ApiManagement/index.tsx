import React, { useState } from 'react';
import styled from 'styled-components';
import {
  ApiKeyManager,
  RateLimits,
  ApiUsage,
  Documentation
} from './components';
import { useApiManagement } from '../../../../hooks/useApiManagement';

const ApiContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const ApiSection = styled.section`
  background: ${props => props.theme.colors.card};
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
`;

export const ApiManagement: React.FC = () => {
  const {
    apiKeys,
    rateLimits,
    usageStats,
    createApiKey,
    revokeApiKey,
    updateRateLimits
  } = useApiManagement();
  
  return (
    <ApiContainer>
      <h2>API Management</h2>
      
      <ApiSection>
        <h3>API Keys</h3>
        <ApiKeyManager
          keys={apiKeys}
          onCreate={createApiKey}
          onRevoke={revokeApiKey}
        />
      </ApiSection>
      
      <ApiSection>
        <h3>Rate Limits</h3>
        <RateLimits
          limits={rateLimits}
          onUpdate={updateRateLimits}
        />
      </ApiSection>
      
      <ApiSection>
        <h3>API Usage Analytics</h3>
        <ApiUsage stats={usageStats} />
      </ApiSection>
      
      <ApiSection>
        <h3>API Documentation</h3>
        <Documentation />
      </ApiSection>
    </ApiContainer>
  );
};