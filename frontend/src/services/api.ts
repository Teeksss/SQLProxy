import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL
});

export const executeQuery = async (database: string, query: string) => {
  const response = await api.post('/query', { database, query });
  return response.data;
};

export const listDatabases = async () => {
  const response = await api.get('/databases');
  return response.data;
};

export const listTables = async (database: string) => {
  const response = await api.get(`/tables/${database}`);
  return response.data;
};