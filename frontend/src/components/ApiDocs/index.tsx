import React from 'react';
import styled from 'styled-components';
import { Swagger } from './Swagger';
import { MarkdownViewer } from './MarkdownViewer';
import { CodeExamples } from './CodeExamples';
import { useApiDocs } from '../../hooks/useApiDocs';

const DocsContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const TabContent = styled.div`
  padding: 1rem;
  background: ${props => props.theme.colors.background};
  border-radius: 4px;
`;

export const ApiDocs: React.FC = () => {
  const {
    swagger,
    markdown,
    examples,
    loading
  } = useApiDocs();
  
  const tabs = [
    {
      label: 'API Reference',
      content: <Swagger spec={swagger} />
    },
    {
      label: 'Guides',
      content: <MarkdownViewer content={markdown} />
    },
    {
      label: 'Examples',
      content: <CodeExamples examples={examples} />
    }
  ];
  
  return (
    <DocsContainer>
      <h2>API Documentation</h2>
      
      {loading ? (
        <div>Loading documentation...</div>
      ) : (
        <Tabs tabs={tabs} />
      )}
    </DocsContainer>
  );
};