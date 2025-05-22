import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import styled from 'styled-components';
import { 
  selectTemplates, 
  addTemplate, 
  removeTemplate 
} from './queryTemplatesSlice';
import { Modal, Button, Input, TextArea } from '../../components/UI';

const TemplateContainer = styled.div`
  margin: 1rem 0;
`;

const TemplateCard = styled.div`
  padding: 1rem;
  margin: 0.5rem 0;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 4px;
  
  &:hover {
    background: ${props => props.theme.colors.backgroundHover};
  }
`;

export const QueryTemplates: React.FC = () => {
  const templates = useSelector(selectTemplates);
  const dispatch = useDispatch();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    description: '',
    query: ''
  });
  
  const handleSave = () => {
    dispatch(addTemplate(newTemplate));
    setIsModalOpen(false);
    setNewTemplate({ name: '', description: '', query: '' });
  };
  
  return (
    <TemplateContainer>
      <Button onClick={() => setIsModalOpen(true)}>
        Add Template
      </Button>
      
      {templates.map(template => (
        <TemplateCard key={template.id}>
          <h4>{template.name}</h4>
          <p>{template.description}</p>
          <Button onClick={() => handleUseTemplate(template.query)}>
            Use Template
          </Button>
        </TemplateCard>
      ))}
      
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Query Template"
      >
        <Input
          label="Name"
          value={newTemplate.name}
          onChange={e => setNewTemplate({
            ...newTemplate,
            name: e.target.value
          })}
        />
        <TextArea
          label="Description"
          value={newTemplate.description}
          onChange={e => setNewTemplate({
            ...newTemplate,
            description: e.target.value
          })}
        />
        <TextArea
          label="Query"
          value={newTemplate.query}
          onChange={e => setNewTemplate({
            ...newTemplate,
            query: e.target.value
          })}
        />
        <Button onClick={handleSave}>Save Template</Button>
      </Modal>
    </TemplateContainer>
  );
};