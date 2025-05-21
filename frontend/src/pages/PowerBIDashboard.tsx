/**
 * PowerBI Dashboard Page
 * 
 * Main page for PowerBI integration features
 * 
 * Last updated: 2025-05-21 05:48:50
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Typography,
  Paper,
  Tabs,
  Tab,
  Divider,
  Card,
  CardContent,
  Alert,
  AlertTitle,
  Button
} from '@mui/material';
import { Helmet } from 'react-helmet-async';

import PowerBIReportsList from '../components/PowerBI/PowerBIReportsList';
import PowerBIWorkspaceManager from '../components/PowerBI/PowerBIWorkspaceManager';
import PowerBISettingsForm from '../components/PowerBI/PowerBISettingsForm';
import PageHeader from '../components/common/PageHeader';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`powerbi-tabpanel-${index}`}
      aria-labelledby={`powerbi-tab-${index}`}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
};

const PowerBIDashboard: React.FC = () => {
  const [tabIndex, setTabIndex] = useState(0);

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  return (
    <>
      <Helmet>
        <title>PowerBI Integration | SQL Proxy</title>
      </Helmet>

      <PageHeader title="PowerBI Integration" subtitle="Manage PowerBI reports, workspaces and integration settings" />

      <Container maxWidth="xl">
        <Box sx={{ mb: 2 }}>
          <Alert severity="info">
            <AlertTitle>Microsoft PowerBI Integration</AlertTitle>
            Create, manage and embed PowerBI reports using SQL Proxy. Connect your PowerBI workspaces
            to query data directly from your database servers.
          </Alert>
        </Box>

        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={tabIndex}
            onChange={handleTabChange}
            aria-label="powerbi tabs"
            sx={{ px: 2, pt: 1 }}
          >
            <Tab label="Reports" id="powerbi-tab-0" />
            <Tab label="Workspaces" id="powerbi-tab-1" />
            <Tab label="Settings" id="powerbi-tab-2" />
          </Tabs>
          <Divider />

          <TabPanel value={tabIndex} index={0}>
            <PowerBIReportsList />
          </TabPanel>

          <TabPanel value={tabIndex} index={1}>
            <PowerBIWorkspaceManager />
          </TabPanel>

          <TabPanel value={tabIndex} index={2}>
            <PowerBISettingsForm />
          </TabPanel>
        </Paper>
      </Container>
    </>
  );
};

export default PowerBIDashboard;

// Son güncelleme: 2025-05-21 05:48:50
// Güncelleyen: Teeksss