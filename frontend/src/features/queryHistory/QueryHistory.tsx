import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import styled from 'styled-components';
import { selectHistory, removeFromHistory } from './queryHistorySlice';
import { Button, List, ListItem } from '../../components/UI';

const HistoryContainer = styled.div`
  padding: 1rem;
  background: ${props => props.theme.colors.background};
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
`;

const HistoryItem = styled(ListItem)`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  
  &:hover {
    background: ${props => props.theme.colors.backgroundHover};
  }
`;

export const QueryHistory: React.FC = () => {
  const history = useSelector(selectHistory);
  const dispatch = useDispatch();
  
  const handleReuse = (query: string) => {
    // Set query in editor
  };
  
  const handleDelete = (id: string) => {
    dispatch(removeFromHistory(id));
  };
  
  return (
    <HistoryContainer>
      <h3>Query History</h3>
      <List>
        {history.map(item => (
          <HistoryItem key={item.id}>
            <div>
              <div>{item.query.substring(0, 50)}...</div>
              <small>{new Date(item.timestamp).toLocaleString()}</small>
            </div>
            <div>
              <Button onClick={() => handleReuse(item.query)}>Reuse</Button>
              <Button onClick={() => handleDelete(item.id)}>Delete</Button>
            </div>
          </HistoryItem>
        ))}
      </List>
    </HistoryContainer>
  );
};