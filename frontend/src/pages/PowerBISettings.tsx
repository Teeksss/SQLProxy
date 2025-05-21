/**
 * PowerBI Settings Page
 * 
 * Page for configuring PowerBI integration settings
 * 
 * Last updated: 2025-05-21 06:45:04
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import { Helmet } from 'react-helmet-async';

import PageHeader from '../components/common/PageHeader';
import PowerBICredentialsForm from '../components/PowerBI/PowerBICredentialsForm';
import PowerBIWorkspaceManager from '../components/PowerBI/PowerBIWorkspaceManager';
import DSNGeneratorForm from '../components/PowerBI/DSNGeneratorForm';

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
      id={`powerbi-settings-tabpanel-${index}`}
      aria-labelledby={`powerbi-settings-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
};

const PowerBISettings: React.FC = () => {
  const [tabIndex, setTabIndex] = useState(0);

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  return (
    <>
      <Helmet>
        <title>PowerBI Settings | SQL Proxy</title>
      </Helmet>

      <PageHeader
        title="PowerBI Settings"
        subtitle="Configure PowerBI integration settings"
      />

      <Container maxWidth="lg">
        <Paper variant="outlined">
          <Tabs
            value={tabIndex}
            onChange={handleTabChange}
            aria-label="powerbi settings tabs"
            sx={{ px: 2, pt: 1 }}
          >
            <Tab label="Credentials" id="powerbi-settings-tab-0" />
            <Tab label="Workspaces" id="powerbi-settings-tab-1" />
            <Tab label="DSN Configurations" id="powerbi-settings-tab-2" />
          </Tabs>
          <Divider />
          
          <TabPanel value={tabIndex} index={0}>
            <PowerBICredentialsForm />
          </TabPanel>
          
          <TabPanel value={tabIndex} index={1}>
            <PowerBIWorkspaceManager />
          </TabPanel>
          
          <TabPanel value={tabIndex} index={2}>
            <DSNGeneratorForm />
          </TabPanel>
        </Paper>
      </Container>
    </>
  );
};

export default PowerBISettings;

// Son güncelleme: 2025-05-21 06:45:04
// Güncelleyen: Teeksss