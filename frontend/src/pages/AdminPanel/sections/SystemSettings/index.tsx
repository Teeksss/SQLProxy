import React from 'react';
import styled from 'styled-components';
import { Tabs } from '../../../../components/UI';
import {
  GeneralSettings,
  SecuritySettings,
  CacheSettings,
  BackupSettings,
  MonitoringSettings
} from './sections';

const SettingsContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

export const SystemSettings: React.FC = () => {
  const tabs = [
    {
      key: 'general',
      title: 'General',
      content: <GeneralSettings />
    },
    {
      key: 'security',
      title: 'Security',
      content: <SecuritySettings />
    },
    {
      key: 'cache',
      title: 'Cache',
      content: <CacheSettings />
    },
    {
      key: 'backup',
      title: 'Backup',
      content: <BackupSettings />
    },
    {
      key: 'monitoring',
      title: 'Monitoring',
      content: <MonitoringSettings />
    }
  ];
  
  return (
    <SettingsContainer>
      <h2>System Settings</h2>
      
      <Tabs tabs={tabs} />
    </SettingsContainer>
  );
};