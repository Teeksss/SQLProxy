import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import styled from 'styled-components';
import { Parameter, TemplateDefinition } from './types';
import { executeParameterizedQuery } from './queryTemplatesSlice';

const TemplateForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const ParameterInput = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

interface Props {
  template: TemplateDefinition;
}

export const ParameterizedTemplate: React.FC<Props> = ({ template }) => {
  const dispatch = useDispatch();
  const [parameters, setParameters] = useState<Record<string, any>>({});
  
  const handleParameterChange = (param: Parameter, value: any) => {
    setParameters(prev => ({
      ...prev,
      [param.name]: value
    }));
  };
  
  const handleExecute = () => {
    // Replace parameters in query
    let finalQuery = template.query;
    Object.entries(parameters).forEach(([key, value]) => {
      finalQuery = finalQuery.replace(
        new RegExp(`\\$\\{${key}\\}`, 'g'),
        typeof value === 'string' ? `'${value}'` : value
      );
    });
    
    dispatch(executeParameterizedQuery({
      query: finalQuery,
      parameters
    }));
  };
  
  return (
    <TemplateForm onSubmit={e => {
      e.preventDefault();
      handleExecute();
    }}>
      {template.parameters.map(param => (
        <ParameterInput key={param.name}>
          <label htmlFor={param.name}>{param.label}</label>
          {param.type === 'select' ? (
            <select
              id={param.name}
              value={parameters[param.name] || ''}
              onChange={e => handleParameterChange(param, e.target.value)}
            >
              {param.options?.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={param.type}
              id={param.name}
              value={parameters[param.name] || ''}
              onChange={e => handleParameterChange(param, e.target.value)}
              required={param.required}
            />
          )}
        </ParameterInput>
      ))}
      <button type="submit">Execute Query</button>
    </TemplateForm>
  );
};