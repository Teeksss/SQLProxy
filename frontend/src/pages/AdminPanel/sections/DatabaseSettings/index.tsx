import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useDispatch, useSelector } from 'react-redux';
import {
  Card,
  Button,
  Table,
  Modal,
  Form
} from '../../../../components/UI';
import { DatabaseForm } from './DatabaseForm';
import { ConnectionTest } from './ConnectionTest';
import { 
  addDatabase,
  updateDatabase,
  removeDatabase,
  testConnection
} from '../../../../store/slices/databaseSlice';

const DatabaseCard = styled(Card)`
  margin-bottom: 1rem;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.5rem;
`;

export const DatabaseSettings: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedDb, setSelectedDb] = useState(null);
  const dispatch = useDispatch();
  const databases = useSelector(state => state.databases.list);
  
  const handleSubmit = (values) => {
    if (selectedDb) {
      dispatch(updateDatabase(values));
    } else {
      dispatch(addDatabase(values));
    }
    setIsModalOpen(false);
  };
  
  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      sortable: true
    },
    {
      title: 'Type',
      dataIndex: 'type',
      filters: [
        { text: 'PostgreSQL', value: 'postgresql' },
        { text: 'MySQL', value: 'mysql' },
        { text: 'Oracle', value: 'oracle' }
      ]
    },
    {
      title: 'Host',
      dataIndex: 'host'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (status) => (
        <span className={`status-${status.toLowerCase()}`}>
          {status}
        </span>
      )
    },
    {
      title: 'Actions',
      render: (record) => (
        <ActionButtons>
          <Button 
            onClick={() => handleEdit(record)}
            variant="secondary"
          >
            Edit
          </Button>
          <Button 
            onClick={() => handleTest(record)}
            variant="info"
          >
            Test
          </Button>
          <Button 
            onClick={() => handleDelete(record)}
            variant="danger"
          >
            Delete
          </Button>
        </ActionButtons>
      )
    }
  ];
  
  return (
    <div>
      <h2>Database Management</h2>
      
      <Button 
        onClick={() => {
          setSelectedDb(null);
          setIsModalOpen(true);
        }}
      >
        Add Database
      </Button>
      
      <Table
        columns={columns}
        dataSource={databases}
        pagination={{
          pageSize: 10,
          total: databases.length
        }}
      />
      
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={selectedDb ? 'Edit Database' : 'Add Database'}
      >
        <DatabaseForm
          initialValues={selectedDb}
          onSubmit={handleSubmit}
        />
      </Modal>
    </div>
  );
};