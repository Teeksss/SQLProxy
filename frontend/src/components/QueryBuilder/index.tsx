import React, { useState } from 'react';
import styled from 'styled-components';
import {
  Conditions,
  JoinBuilder,
  ColumnSelector,
  SortingBuilder
} from './components';
import { useQueryBuilder } from '../../hooks/useQueryBuilder';

const BuilderContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const BuilderSection = styled.div`
  background: ${props => props.theme.colors.card};
  padding: 1.5rem;
  border-radius: 8px;
`;

interface BuilderState {
  tables: string[];
  columns: string[];
  conditions: any[];
  joins: any[];
  sorting: any[];
  grouping: any[];
}

export const QueryBuilder: React.FC = () => {
  const [state, setState] = useState<BuilderState>({
    tables: [],
    columns: [],
    conditions: [],
    joins: [],
    sorting: [],
    grouping: []
  });
  
  const { buildQuery, validateQuery } = useQueryBuilder();
  
  const handleBuild = async () => {
    const query = await buildQuery(state);
    const validation = await validateQuery(query);
    
    if (validation.isValid) {
      // Execute query
      await executeQuery(query);
    } else {
      // Show validation errors
      displayErrors(validation.errors);
    }
  };
  
  return (
    <BuilderContainer>
      <BuilderSection>
        <h3>Tables & Columns</h3>
        <TableSelector
          selected={state.tables}
          onChange={tables => setState({...state, tables})}
        />
        <ColumnSelector
          tables={state.tables}
          selected={state.columns}
          onChange={columns => setState({...state, columns})}
        />
      </BuilderSection>
      
      <BuilderSection>
        <h3>Conditions</h3>
        <Conditions
          columns={state.columns}
          conditions={state.conditions}
          onChange={conditions => setState({...state, conditions})}
        />
      </BuilderSection>
      
      <BuilderSection>
        <h3>Joins</h3>
        <JoinBuilder
          tables={state.tables}
          joins={state.joins}
          onChange={joins => setState({...state, joins})}
        />
      </BuilderSection>
      
      <BuilderSection>
        <h3>Sorting & Grouping</h3>
        <SortingBuilder
          columns={state.columns}
          sorting={state.sorting}
          grouping={state.grouping}
          onChange={({sorting, grouping}) => 
            setState({...state, sorting, grouping})}
        />
      </BuilderSection>
      
      <Button onClick={handleBuild}>
        Build & Execute Query
      </Button>
    </BuilderContainer>
  );
};