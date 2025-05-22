import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import { Provider } from 'react-redux';
import { store } from './store';
import { theme } from './theme';
import {
  Dashboard,
  QueryEditor,
  ServerManager,
  Analytics,
  Settings
} from './pages';
import { Layout } from './components/Layout';

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/query" element={<QueryEditor />} />
              <Route path="/servers" element={<ServerManager />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  );
};

export default App;