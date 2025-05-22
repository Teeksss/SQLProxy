import React, { useState } from 'react';
import styled from 'styled-components';
import {
  ConditionBuilder,
  RuleEditor,
  ContextViewer,
  TimeWindowSelector
} from './components';
import { useDynamicPermissions } from '../../hooks/useDynamicPermissions';

const PermissionContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const EditorGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
`;

export const DynamicPermissions: React.FC = () => {
  const [selectedRule, setSelectedRule] = useState(null);
  
  const {
    rules,
    conditions,
    contexts,
    createRule,
    updateRule,
    deleteRule,
    testRule
  } = useDynamicPermissions();
  
  return (
    <PermissionContainer>
      <h2>Dynamic Permissions</h2>
      
      <EditorGrid>
        <div>
          <h3>Conditions</h3>
          <ConditionBuilder
            conditions={conditions}
            onSave={(condition) => {
              if (selectedRule) {
                updateRule({
                  ...selectedRule,
                  conditions: [...selectedRule.conditions, condition]
                });
              }
            }}
          />
          
          <TimeWindowSelector
            onChange={(window) => {
              if (selectedRule) {
                updateRule({
                  ...selectedRule,
                  timeWindow: window
                });
              }
            }}
          />
        </div>
        
        <div>
          <h3>Rules</h3>
          <RuleEditor
            rule={selectedRule}
            onSave={selectedRule ? updateRule : createRule}
            onTest={testRule}
          />
          
          <ContextViewer
            contexts={contexts}
            selectedRule={selectedRule}
          />
        </div>
      </EditorGrid>
    </PermissionContainer>
  );
};