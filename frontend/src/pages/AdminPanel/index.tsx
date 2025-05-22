import React from 'react';
import styled from 'styled-components';
import { Switch, Route, useRouteMatch } from 'react-router-dom';
import { 
  Dashboard,
  DatabaseSettings,
  QueryMonitor,
  LogViewer,
  UserManagement,
  SystemSettings
} from './sections';
import { Sidebar } from './components';

const AdminLayout = styled.div`
  display: grid;
  grid-template-columns: 250px 1fr;
  min-height: 100vh;
`;

const Content = styled.main`
  padding: 2rem;
  background: ${props => props.theme.colors.background};
`;

export const AdminPanel: React.FC = () => {
  const { path } = useRouteMatch();
  
  return (
    <AdminLayout>
      <Sidebar />
      <Content>
        <Switch>
          <Route exact path={path} component={Dashboard} />
          <Route path={`${path}/databases`} component={DatabaseSettings} />
          <Route path={`${path}/queries`} component={QueryMonitor} />
          <Route path={`${path}/logs`} component={LogViewer} />
          <Route path={`${path}/users`} component={UserManagement} />
          <Route path={`${path}/settings`} component={SystemSettings} />
        </Switch>
      </Content>
    </AdminLayout>
  );
};