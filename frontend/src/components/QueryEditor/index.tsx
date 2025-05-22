import React, { useState } from 'react';
import styled from 'styled-components';
import MonacoEditor from '@monaco-editor/react';
import {
  EditorToolbar,
  ResultsPanel,
  QueryHistory,
  ExecutionPlan
} from './components';
import { useQueryExecution } from '../../hooks/useQueryExecution';

const EditorContainer = styled.div`
  display: grid;
  grid-template-rows: auto 1fr auto;
  height: 100vh;
  gap: 1rem;
`;

const EditorGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 1rem;
`;

const EditorPanel = styled.div`
  display: grid;
  grid-template-rows: 1fr auto;
  gap: 1rem;
`;

export const QueryEditor: React.FC = () => {
  const [query, setQuery] = useState('');
  const [selectedServer, setSelectedServer] = useState(null);
  
  const {
    execute,
    results,
    loading,
    error
  } = useQueryExecution();
  
  const handleExecute = async () => {
    if (!selectedServer) {
      alert('Please select a server');
      return;
    }
    
    await execute({
      query,
      serverId: selectedServer.id
    });
  };
  
  return (
    <EditorContainer>
      <EditorToolbar
        onExecute={handleExecute}
        onSave={() => {/* save query */}}
        onFormat={() => {/* format query */}}
        loading={loading}
      />
      
      <EditorGrid>
        <EditorPanel>
          <MonacoEditor
            height="100%"
            language="sql"
            theme="vs-dark"
            value={query}
            onChange={setQuery}
            options={{
              minimap: { enabled: false },
              lineNumbers: 'on',
              folding: true,
              autoIndent: true
            }}
          />
          
          <ResultsPanel
            results={results}
            error={error}
            loading={loading}
          />
        </EditorPanel>
        
        <div>
          <QueryHistory
            onSelect={(savedQuery) => setQuery(savedQuery)}
          />
          
          <ExecutionPlan
            query={query}
            serverId={selectedServer?.id}
          />
        </div>
      </EditorGrid>
    </EditorContainer>
  );
};